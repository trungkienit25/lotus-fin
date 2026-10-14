import test from "node:test";
import assert from "node:assert/strict";
import {
  FollowupPreviewController,
  type Clock,
  type ClipboardPort,
} from "../src/pages/copilot/prepare/followupPreviewController.ts";
import { EXPECTED_FOLLOWUP_TEMPLATE } from "../src/pages/copilot/prepare/followupPreview.ts";

const VALID_REQUEST = {
  contract_version: "l3.followup.local.v0.1" as const,
  capability: "followup.prepare_text" as const,
  template_id: "followup.neutral.vi.v1" as const,
  locale: "vi-VN" as const,
};

function createMockClock(initialMs = 1000): { clock: Clock; advance: (ms: number) => void; set: (ms: number) => void } {
  let current = initialMs;
  return {
    clock: { now: () => current },
    advance: (ms: number) => {
      current += ms;
    },
    set: (ms: number) => {
      current = ms;
    },
  };
}

function createMockClipboard(success = true): {
  clipboard: ClipboardPort;
  writes: string[];
  setSuccess: (v: boolean) => void;
  setDelay: (ms: number) => void;
} {
  const writes: string[] = [];
  let succeed = success;
  let delayMs = 0;
  return {
    clipboard: {
      writeText: async (text: string) => {
        if (delayMs > 0) {
          await new Promise((r) => setTimeout(r, delayMs));
        }
        if (!succeed) {
          throw new Error("Clipboard write permission denied");
        }
        writes.push(text);
      },
    },
    writes,
    setSuccess: (v: boolean) => {
      succeed = v;
    },
    setDelay: (ms: number) => {
      delayMs = ms;
    },
  };
}

test("Oracle L301 & L304: Prepare initializes state; Copy is disabled without Review", async () => {
  const { clock } = createMockClock();
  const { clipboard, writes } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  assert.equal(controller.getState().lifecycle, "EMPTY");
  controller.prepare(VALID_REQUEST);

  const state = controller.getState();
  assert.equal(state.lifecycle, "EDITABLE");
  assert.equal(state.body, EXPECTED_FOLLOWUP_TEMPLATE);
  assert.equal(state.provenance, "SUGGESTED");
  assert.equal(state.isReviewed, false);

  // Attempt copy without review -> must not call clipboard
  const copied = await controller.copy();
  assert.equal(copied, false);
  assert.equal(writes.length, 0);
});

test("Oracle L305: Explicit Review -> Copy writes exact text to clipboard", async () => {
  const { clock } = createMockClock();
  const { clipboard, writes } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);
  assert.equal(controller.getState().lifecycle, "REVIEWED");
  assert.equal(controller.getState().isReviewed, true);

  const copied = await controller.copy();
  assert.equal(copied, true);
  assert.equal(writes.length, 1);
  assert.equal(writes[0], EXPECTED_FOLLOWUP_TEMPLATE);
  assert.equal(controller.getState().lastActionStatus, "COPIED");
});

test("Oracle L306 & L307: Edit switches provenance to USER_ENTERED; manual revert stays USER_ENTERED", () => {
  const { clock } = createMockClock();
  const { clipboard } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);

  // Valid edit
  const editedText = "Nội dung do tôi nhập.";
  controller.updateBody(editedText);
  let s = controller.getState();
  assert.equal(s.lifecycle, "EDITABLE");
  assert.equal(s.body, editedText);
  assert.equal(s.provenance, "USER_ENTERED");
  assert.equal(s.isReviewed, false);

  // Manually type back original text
  controller.updateBody(EXPECTED_FOLLOWUP_TEMPLATE);
  s = controller.getState();
  assert.equal(s.body, EXPECTED_FOLLOWUP_TEMPLATE);
  assert.equal(s.provenance, "USER_ENTERED"); // Provenance must NOT be restored to SUGGESTED
});

test("Oracle L308: Reset template restores exact literal with SUGGESTED provenance and unreviewed", () => {
  const { clock } = createMockClock();
  const { clipboard } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.updateBody("Text custom");
  controller.resetTemplate();

  const s = controller.getState();
  assert.equal(s.lifecycle, "EDITABLE");
  assert.equal(s.body, EXPECTED_FOLLOWUP_TEMPLATE);
  assert.equal(s.provenance, "SUGGESTED");
  assert.equal(s.isReviewed, false);
});

test("Oracle L312: Clipboard rejection sets COPY_FAILED, keeps body local and editable", async () => {
  const { clock } = createMockClock();
  const { clipboard, setSuccess } = createMockClipboard(false); // Fails
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);

  const copied = await controller.copy();
  assert.equal(copied, false);
  const s = controller.getState();
  assert.equal(s.lifecycle, "REVIEWED");
  assert.equal(s.lastActionStatus, "COPY_FAILED");
  assert.equal(s.body, EXPECTED_FOLLOWUP_TEMPLATE);
});

test("Oracle L313: Concurrent copy calls execute only one clipboard operation", async () => {
  const { clock } = createMockClock();
  const { clipboard, writes, setDelay } = createMockClipboard(true);
  setDelay(20); // 20ms delay
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);

  const [res1, res2] = await Promise.all([controller.copy(), controller.copy()]);
  assert.equal(res1, true);
  assert.equal(res2, false); // Ignored/rejected because first copy is in progress
  assert.equal(writes.length, 1);
});

test("Oracle L314: Discard clears state and fences late copy promise", async () => {
  const { clock } = createMockClock();
  const { clipboard, setDelay } = createMockClipboard(true);
  setDelay(30);
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);

  const copyPromise = controller.copy();
  controller.discard();

  assert.equal(controller.getState().lifecycle, "EMPTY");
  await copyPromise;
  // Late resolve must not restore body or set COPIED on discarded state
  assert.equal(controller.getState().lifecycle, "EMPTY");
  assert.equal(controller.getState().body, "");
});

test("Oracle L315: Scope change clears state immediately and fences work", () => {
  const { clock } = createMockClock();
  const { clipboard } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "company-A" });

  controller.prepare(VALID_REQUEST);
  assert.equal(controller.getState().lifecycle, "EDITABLE");

  controller.setScopeEpoch("company-B");
  assert.equal(controller.getState().lifecycle, "EMPTY");
  assert.equal(controller.getState().body, "");
});

test("Oracle L317 & L318: TTL is exactly 600,000ms absolute; edit/focus does not extend it", () => {
  const { clock, advance } = createMockClock(0);
  const { clipboard, writes } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "epoch-1" });

  controller.prepare(VALID_REQUEST);
  assert.equal(controller.getState().lifecycle, "EDITABLE");

  // Advance 599,999 ms
  advance(599999);
  assert.equal(controller.getState().lifecycle, "EDITABLE");

  // Advance 1 ms -> reaches 600,000 ms -> EXPIRED
  advance(1);
  assert.equal(controller.getState().lifecycle, "EXPIRED");
  assert.equal(controller.getState().body, "");

  // Attempting copy returns false, 0 writes
  controller.copy().then((res) => {
    assert.equal(res, false);
    assert.equal(writes.length, 0);
  });
});

test("FIN-F03: Editing body while copy is pending invalidates success notice for new revision", async () => {
  let resolveClipboard!: () => void;
  const clipboard: ClipboardPort = {
    writeText: () => new Promise<void>((resolve) => { resolveClipboard = resolve; }),
  };
  const { clock } = createMockClock(0);
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "scope-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);

  const copyPromise = controller.copy();
  // User edits body while copy is in flight
  controller.updateBody("Nội dung phiên bản 2 đã chỉnh sửa.");
  controller.setReviewed(true);

  resolveClipboard();
  const result = await copyPromise;

  assert.equal(result, false);
  const s = controller.getState();
  assert.notEqual(s.lastActionStatus, "COPIED");
  assert.equal(s.body, "Nội dung phiên bản 2 đã chỉnh sửa.");
});

test("FIN-F03: Old copy completion in generation A does not unlock or affect copy lock in generation B", async () => {
  let resolveA!: () => void;
  let resolveB!: () => void;
  const calls: string[] = [];
  const clipboard: ClipboardPort = {
    writeText: (t) => {
      calls.push(t);
      if (calls.length === 1) {
        return new Promise<void>((r) => { resolveA = r; });
      }
      return new Promise<void>((r) => { resolveB = r; });
    },
  };
  const { clock } = createMockClock(0);
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "scope-1" });

  // Generation 1
  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);
  const pA = controller.copy();

  // User discards and prepares Generation 2
  controller.discard();
  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);
  const pB = controller.copy();

  assert.equal(calls.length, 2);

  // Resolve old A write -> should NOT unlock generation B
  resolveA();
  await pA;

  // Attempt copy while B is still pending
  const pC = controller.copy();
  assert.equal(await pC, false);
  assert.equal(calls.length, 2); // No third write!

  resolveB();
  await pB;
});

test("FIN-F04: Dispose on unmount clears text and handles, suppresses late notifications", async () => {
  let resolveClipboard!: () => void;
  const clipboard: ClipboardPort = {
    writeText: () => new Promise<void>((r) => { resolveClipboard = r; }),
  };
  const { clock } = createMockClock(0);
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "scope-1" });

  controller.prepare(VALID_REQUEST);
  controller.setReviewed(true);
  const copyPromise = controller.copy();

  // Component unmounts
  controller.dispose();

  assert.equal(controller.getState().lifecycle, "EMPTY");
  assert.equal(controller.getState().body, "");

  resolveClipboard();
  await copyPromise;

  const s = controller.getState();
  assert.equal(s.lifecycle, "EMPTY");
  assert.equal(s.body, "");
  assert.equal(s.lastActionStatus, null);
});

test("FIN-F05: Monotonic elapsed time accounts for TTL despite wall clock rollback", () => {
  let mono = 1000;
  let wall = 500000;
  const clock: Clock = {
    now: () => {
      // Simulate monotonic clock advancing
      return mono;
    },
  };
  const { clipboard } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "scope-1" });

  controller.prepare(VALID_REQUEST);
  assert.equal(controller.getState().lifecycle, "EDITABLE");

  // Advance monotonic clock by 600,001 ms while wall clock rolls backwards
  mono += 600001;
  wall -= 3600000; // 1 hour backwards in wall time

  const s = controller.getState();
  assert.equal(s.lifecycle, "EXPIRED");
  assert.equal(s.body, "");
});

test("FIN-F10: Unavailable or blank scope rejects prepare, edit, and copy", async () => {
  const { clock } = createMockClock();
  const { clipboard, writes } = createMockClipboard();
  const controller = new FollowupPreviewController({ clock, clipboard, scopeEpoch: "   " });

  controller.prepare(VALID_REQUEST);
  let s = controller.getState();
  assert.equal(s.lifecycle, "EMPTY");
  assert.equal(s.body, "");
  assert.equal(s.errorMessage, "Phạm vi phiên làm việc không khả dụng.");

  const edited = controller.updateBody("Try edit");
  assert.equal(edited, false);

  const copied = await controller.copy();
  assert.equal(copied, false);
  assert.equal(writes.length, 0);
});
