import test from "node:test";
import assert from "node:assert/strict";
import { routeCopilotIntent } from "../src/pages/copilot/actions/copilotIntentRouter.ts";
import { sameActionScope } from "../src/pages/copilot/actions/copilotIntegrationClient.ts";
import { markSessionVerified, getSessionScopeSnapshot, markSessionRevoked } from "../src/providers/sessionScope.ts";
import { createCopilotMessageSender } from "../src/pages/copilot/components/copilotMessageSender.ts";

test("bounded intents choose review views without confirming", () => {
  const cases = [["Tìm hóa đơn INV", "L1"], ["Mở hóa đơn INV", "L2"], ["Soạn lời nhắc", "L3"],
    ["Tạo Task theo dõi", "L4"], ["Xác nhận tạo Task", "CONFIRM"], ["Gửi email", "L5"],
    ["Submit/Cancel", "L5"], ["Tìm hóa đơn đã quá hạn cuối", "V1"], ["Tạo cái đó", "CLARIFY"]];
  for (const [text, kind] of cases) assert.equal(routeCopilotIntent(text).kind, kind);
  assert.match(routeCopilotIntent("Xác nhận tạo Task").message!, /do not grant execution authority/i);
});

test("all protected feature responses fence actor, epoch and generation", async () => {
  await markSessionVerified("alice", "csrf-alice");
  const a = getSessionScopeSnapshot();
  assert.equal(sameActionScope(a, a), true);
  for (const changed of [{ ...a, actor: "bob" }, { ...a, sessionEpoch: "rotated" },
    { ...a, generation: a.generation + 1 }, { ...a, siteScope: "other" }]) assert.equal(sameActionScope(a, changed), false);
  markSessionRevoked();
  assert.equal(sameActionScope(a, getSessionScopeSnapshot()), false);
});

test("chat confirmation cannot execute and a profile change fences late replies", async () => {
  await markSessionVerified("alice", "csrf-alice");
  const features: string[] = []; const messages: unknown[] = [];
  let profile: "CORE" | "DEMO" = "DEMO";
  let resolve: (value: any) => void = () => {};
  let calls = 0;
  const sender = createCopilotMessageSender({ input: "", files: [], loading: false,
    scope: getSessionScopeSnapshot(), profile: "DEMO", currentProfile: () => profile,
    append: m => messages.push(m), clearInput: () => {}, selectMode: () => {}, selectFeature: f => features.push(f),
    sendRequest: () => { calls++; return new Promise(r => { resolve = r; }); } });
  await sender("Xác nhận tạo Task");
  assert.deepEqual(features, ["L4"]); assert.equal(calls, 0);
  const pending = sender("Financial snapshot");
  profile = "CORE";
  resolve({ userFacingText: "old fictional result", sourceLabel: "DEMO" });
  await pending;
  assert.equal(messages.length, 1); // Only the user's request survives; old result is discarded.
});
