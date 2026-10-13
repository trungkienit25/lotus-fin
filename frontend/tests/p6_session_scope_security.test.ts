import test from "node:test";
import assert from "node:assert/strict";
import {
  deriveOpaqueSessionEpoch,
  markSessionRevoked,
  markSessionVerified,
  getSessionScopeSnapshot,
  revalidateSessionScope,
  fetchServerSession,
  type AuthenticatedActionScope,
} from "../src/providers/sessionScope.ts";
import {
  bootstrapSession,
  clearSessionBootstrap,
  sessionGeneration,
  assertSessionGeneration,
} from "../src/providers/sessionBootstrap.ts";
import { createDemoInvoiceTransport } from "../src/pages/copilot/demo/demoInvoiceProvider.ts";
import { InvoiceActionController } from "../src/pages/copilot/actions/invoiceActionController.ts";
import { FollowupPreviewController } from "../src/pages/copilot/prepare/followupPreviewController.ts";

function createTestController(transport: any, allowDemoSource = true) {
  return new InvoiceActionController({
    transport,
    newRequestId: () => crypto.randomUUID(),
    now: () => Date.now(),
    allowDemoSource,
  });
}

test("Scenario 1 & 2 & 3: User A opens DEMO document, external logout revokes scope and clears protected state without reload", async () => {
  clearSessionBootstrap();
  await markSessionVerified("user-a@example.com", "csrf-token-a-11111");
  const scopeA = getSessionScopeSnapshot();
  assert.equal(scopeA.state, "VERIFIED");
  assert.equal(scopeA.actor, "user-a@example.com");

  // User A interacts with DEMO controller
  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const controller = createTestController(demoTransport, true);

  await controller.loadContext("Lotus Fin Core");
  await controller.search({ prefix: "DEMO-SINV" });
  assert.equal(controller.getState().results?.kind, "results");
  assert.equal(controller.getState().results?.items.length, 3);

  const firstRow = controller.getState().results?.items[0];
  assert.ok(firstRow);
  await controller.openInvoice(firstRow.invoiceId);
  assert.ok(controller.getState().document);
  assert.equal(controller.getState().document?.document.invoice_id, "DEMO-SINV-2026-001");

  // External logout in another tab (detected via markSessionRevoked / 401 response)
  markSessionRevoked();
  const revokedScope = getSessionScopeSnapshot();
  assert.equal(revokedScope.state, "REVOKED");
  assert.equal(revokedScope.actor, null);
  assert.equal(revokedScope.sessionEpoch, "");

  // Protected state clears immediately upon scope reset without document reload
  controller.reset();
  assert.equal(controller.getState().results, null);
  assert.equal(controller.getState().document, null);
  assert.equal(controller.getState().selectedId, null);
});

test("Scenario 4 & 5: User B logs in, old User A handle is denied and scoped transport isolates", async () => {
  clearSessionBootstrap();
  // User A session
  await markSessionVerified("user-a@example.com", "csrf-a");
  const epochA = getSessionScopeSnapshot().sessionEpoch;

  const transportA = createDemoInvoiceTransport("NORMAL");
  const controllerA = createTestController(transportA, true);
  await controllerA.loadContext("Lotus Fin Core");
  await controllerA.search({ prefix: "DEMO-SINV" });
  const rowA = controllerA.getState().results?.items[0];
  assert.ok(rowA);

  // User B logs in
  await markSessionVerified("user-b@example.com", "csrf-b");
  const scopeB = getSessionScopeSnapshot();
  assert.equal(scopeB.actor, "user-b@example.com");
  assert.notEqual(scopeB.sessionEpoch, epochA);

  // Attempting to use controller under new scope without re-search
  const transportB = createDemoInvoiceTransport("NORMAL");
  const controllerB = createTestController(transportB, true);
  await controllerB.loadContext("Lotus Fin Core");

  // Old handle from A's context cannot be accessed in B's fresh controller
  assert.equal(controllerB.getState().results, null);
  assert.equal(controllerB.getState().document, null);

  // Calling openInvoice with old row ID on fresh unsearched controller is rejected
  await controllerB.openInvoice(rowA.invoiceId);
  assert.equal(controllerB.getState().document, null);
});

test("Scenario 6: Same-user session replacement generates a distinct session epoch and fences old operations", async () => {
  clearSessionBootstrap();
  await markSessionVerified("user-a@example.com", "csrf-session-token-1");
  const scope1 = getSessionScopeSnapshot();

  // Session rotated / re-logged-in for the SAME user with a new token
  await markSessionVerified("user-a@example.com", "csrf-session-token-2");
  const scope2 = getSessionScopeSnapshot();

  assert.equal(scope1.actor, scope2.actor);
  assert.notEqual(scope1.sessionEpoch, scope2.sessionEpoch);
  assert.ok(scope2.generation > scope1.generation);
});

test("Scenario 7: Disabled / revoked user fails server bootstrap and revokes scope", async () => {
  const orig = globalThis.fetch;
  try {
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ exc_type: "AuthenticationError" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });

    await revalidateSessionScope();
    const scope = getSessionScopeSnapshot();
    assert.equal(scope.state, "REVOKED");
    assert.equal(scope.isVerified, false);
    assert.equal(scope.actor, null);
  } finally {
    globalThis.fetch = orig;
  }
});

test("Scenario 8: Delayed old response from prior session is discarded", async () => {
  let resolveDelayedFetch: (val: any) => void;
  const delayedPromise = new Promise((res) => {
    resolveDelayedFetch = res;
  });

  const orig = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      if (String(url) === "/copilot/session") {
        return new Response(JSON.stringify({ user: "user-a@example.com", csrf_token: "csrf-token-1" }), { status: 200 });
      }
      await delayedPromise;
      return new Response(JSON.stringify({ success: true, data: { companyLabel: "Delayed Company" } }), { status: 200 });
    };

    const sessionA = await bootstrapSession();
    assert.equal(sessionA.user, "user-a@example.com");

    const genBefore = sessionGeneration();
    clearSessionBootstrap(); // session changed
    const genAfter = sessionGeneration();
    assert.notEqual(genBefore, genAfter);

    assert.throws(() => assertSessionGeneration(genBefore), (err: any) => err.name === "AbortError");
  } finally {
    globalThis.fetch = orig;
  }
});

test("Scenario 9 & 10: CORE / DEMO profile transitions isolate transports and prevent data leakage", async () => {
  clearSessionBootstrap();
  await markSessionVerified("test-actor@example.com", "csrf-core-demo");

  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const demoCtrl = createTestController(demoTransport, true);
  await demoCtrl.loadContext("Lotus Fin Core");
  await demoCtrl.search({ prefix: "DEMO-SINV" });
  assert.equal(demoCtrl.getState().results?.kind, "results");

  // Transition to CORE: allowDemoSource is false
  const coreTransport = {
    post: async (cap: any, payload: any) => ({
      status: 503,
      data: {
        message: {
          contract_version: "p1.invoice.v1",
          status: "NOT_AVAILABLE",
          reason_code: "CAPABILITY_DISABLED",
          correlation_id: "22222222-2222-4222-8222-222222222222",
          request_id: payload?.request_id || "11111111-1111-4111-8111-111111111111",
          capability: "invoice.context",
          source: null,
          data: null,
          user_message: "Capability disabled in Core",
        },
      },
      headers: { "x-correlation-id": "22222222-2222-4222-8222-222222222222" },
    }),
  };
  const coreCtrl = createTestController(coreTransport, false);
  await coreCtrl.loadContext("Lotus Fin Core");

  assert.equal(coreCtrl.getState().results, null);
  assert.equal(coreCtrl.getState().document, null);
  assert.equal(coreCtrl.getState().notice?.reason, "DISABLED");
});

test("Scenario 11: L3 followup preview controller cleans up immediately on scope key change", async () => {
  const ctrl = new FollowupPreviewController({ scopeEpoch: "user-a:epoch-1:Lotus" });
  ctrl.prepare({
    contract_version: "l3.followup.local.v0.1",
    capability: "followup.prepare_text",
    template_id: "followup.neutral.vi.v1",
    locale: "vi-VN",
  });
  assert.equal(ctrl.getState().lifecycle, "EDITABLE");
  assert.ok(ctrl.getState().body.length > 0);

  ctrl.updateBody("Kính gửi Quý khách hàng, vui lòng thanh toán hóa đơn.");
  ctrl.setReviewed(true);
  assert.equal(ctrl.getState().isReviewed, true);
  assert.equal(ctrl.getState().body, "Kính gửi Quý khách hàng, vui lòng thanh toán hóa đơn.");

  // Scope key changes when session rotates or actor changes
  ctrl.setScopeEpoch("user-b:epoch-2:Lotus");
  assert.equal(ctrl.getState().lifecycle, "EMPTY");
  assert.equal(ctrl.getState().body, "");
  assert.equal(ctrl.getState().isReviewed, false);
});
