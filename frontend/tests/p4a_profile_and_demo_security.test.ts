import test from "node:test";
import assert from "node:assert/strict";
import { createDemoInvoiceTransport } from "../src/pages/copilot/demo/demoInvoiceProvider.ts";
import { InvoiceActionController } from "../src/pages/copilot/actions/invoiceActionController.ts";
import type { InvoiceActionTransport, TransportResult } from "../src/pages/copilot/actions/invoiceActionController.ts";

const RID = "11111111-1111-4111-8111-111111111111";
const CID = "22222222-2222-4222-8222-222222222222";

// Mock Core transport that simulates Frappe Core RPC returning 503 CAPABILITY_DISABLED
function createMockCoreTransport(onPost?: (cap: string, payload: any) => void): InvoiceActionTransport {
  return {
    async post(capability: string, payload: unknown, signal: AbortSignal): Promise<TransportResult> {
      onPost?.(capability, payload);
      return {
        status: 503,
        data: {
          message: {
            contract_version: "p1.invoice.v1",
            status: "NOT_AVAILABLE",
            reason_code: "CAPABILITY_DISABLED",
            correlation_id: CID,
            request_id: (payload as any)?.request_id || RID,
            capability,
            source: null,
            context_version: null,
            data: null,
            user_message: "Native capability is disabled",
          },
        },
        headers: { "x-correlation-id": CID },
      };
    },
  };
}

// ============================================================================
// P2-04: DEMO SCOPE AND FORGERY PREVENTION TESTS
// ============================================================================

test("P2-04: forged context search is denied (non-200)", async () => {
  const transport = createDemoInvoiceTransport("NORMAL");
  const ctxRes = await transport.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  assert.equal(ctxRes.status, 200);

  const searchRes = await transport.post(
    "invoice.search",
    {
      request_id: RID,
      context_ref: "FORGED-CTX-REF",
      expected_context_version: "ctx_demo_2026_v1",
      filters: {},
    },
    new AbortController().signal
  );
  assert.notEqual(searchRes.status, 200);
});

test("P2-04: wrong context version search is denied (non-200)", async () => {
  const transport = createDemoInvoiceTransport("NORMAL");
  const ctxRes = await transport.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  const ctxRef = (ctxRes.data as any).message.data.context_ref;

  const searchRes = await transport.post(
    "invoice.search",
    {
      request_id: RID,
      context_ref: ctxRef,
      expected_context_version: "WRONG-VERSION",
      filters: {},
    },
    new AbortController().signal
  );
  assert.notEqual(searchRes.status, 200);
});

test("P2-04: forged selection open is denied (non-200)", async () => {
  const transport = createDemoInvoiceTransport("NORMAL");
  const ctxRes = await transport.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  const ctxRef = (ctxRes.data as any).message.data.context_ref;

  const openRes = await transport.post(
    "invoice.open",
    {
      request_id: RID,
      context_ref: ctxRef,
      selection_ref: "FORGED-SELECTION-REF",
      expected_context_version: "ctx_demo_2026_v1",
    },
    new AbortController().signal
  );
  assert.notEqual(openRes.status, 200);
});

test("P2-04: cross transport scope selection is denied (non-200)", async () => {
  const transportA = createDemoInvoiceTransport("NORMAL");
  const transportB = createDemoInvoiceTransport("NORMAL");

  const ctxResA = await transportA.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  const ctxRefA = (ctxResA.data as any).message.data.context_ref;

  const searchResA = await transportA.post(
    "invoice.search",
    {
      request_id: RID,
      context_ref: ctxRefA,
      expected_context_version: "ctx_demo_2026_v1",
      filters: {},
    },
    new AbortController().signal
  );
  assert.equal(searchResA.status, 200);
  const itemsA = (searchResA.data as any).message.data.items;
  const selRefA = itemsA[0].selection_ref;

  // Cross transport scope: transport B must deny
  const openResB = await transportB.post(
    "invoice.open",
    {
      request_id: RID,
      context_ref: ctxRefA,
      selection_ref: selRefA,
      expected_context_version: "ctx_demo_2026_v1",
    },
    new AbortController().signal
  );
  assert.notEqual(openResB.status, 200);
});

test("P2-04: PARTIAL scenario returns non-actionable selection refs", async () => {
  const transport = createDemoInvoiceTransport("PARTIAL");
  const ctxRes = await transport.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  const ctxRef = (ctxRes.data as any).message.data.context_ref;

  const searchRes = await transport.post(
    "invoice.search",
    {
      request_id: RID,
      context_ref: ctxRef,
      expected_context_version: "ctx_demo_2026_v1",
      filters: {},
    },
    new AbortController().signal
  );
  assert.equal(searchRes.status, 200);
  const data = (searchRes.data as any).message.data;
  assert.equal(data.page_complete, false);
  for (const item of data.items) {
    assert.equal(item.selection_ref, null);
  }
});

test("P2-04: STALE scenario returns 409 STALE_SELECTION on open", async () => {
  const transport = createDemoInvoiceTransport("STALE");
  const ctxRes = await transport.post(
    "invoice.context",
    { request_id: RID, company_candidate: "Scope A" },
    new AbortController().signal
  );
  const ctxRef = (ctxRes.data as any).message.data.context_ref;

  const openRes = await transport.post(
    "invoice.open",
    {
      request_id: RID,
      context_ref: ctxRef,
      selection_ref: "any-selection",
      expected_context_version: "ctx_demo_2026_v1",
    },
    new AbortController().signal
  );
  assert.equal(openRes.status, 409);
  assert.equal((openRes.data as any).message.reason_code, "STALE_SELECTION");
});

test("P2-04: FORBIDDEN scenario returns 403 on all capabilities", async () => {
  const transport = createDemoInvoiceTransport("FORBIDDEN");
  const ctxRes = await transport.post("invoice.context", { request_id: RID }, new AbortController().signal);
  assert.equal(ctxRes.status, 403);
  const searchRes = await transport.post("invoice.search", { request_id: RID }, new AbortController().signal);
  assert.equal(searchRes.status, 403);
  const openRes = await transport.post("invoice.open", { request_id: RID }, new AbortController().signal);
  assert.equal(openRes.status, 403);
});

// ============================================================================
// P1-01: PROFILE ISOLATION & CONTROLLER OWNERSHIP TESTS
// ============================================================================

test("P1-01: switching from DEMO to CORE clears protected state and enforces CORE transport", async () => {
  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const coreCalls: string[] = [];
  const coreTransport = createMockCoreTransport((cap) => coreCalls.push(cap));

  // 1. DEMO controller lifecycle
  const ctrlDemo = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => Date.now(),
    allowDemoSource: true,
  });
  ctrlDemo.setScope("lotus-fin:DEMO:NORMAL");

  await ctrlDemo.loadContext("Demo Company");
  assert.ok(ctrlDemo.getState().context);
  assert.equal(ctrlDemo.getState().context?.sourceMode, "DEMO_ISOLATED");

  await ctrlDemo.search({ prefix: "DEMO-SINV" });
  assert.ok(ctrlDemo.getState().results);
  assert.equal(ctrlDemo.getState().results?.items.length, 3);

  await ctrlDemo.openInvoice("DEMO-SINV-2026-002");
  assert.ok(ctrlDemo.getState().document);
  assert.equal(ctrlDemo.getState().document?.document.invoice_id, "DEMO-SINV-2026-002");

  // 2. User switches to CORE: old controller is disposed, new controller is created
  ctrlDemo.reset();
  const demoStateAfterReset = ctrlDemo.getState();
  assert.equal(demoStateAfterReset.context, null);
  assert.equal(demoStateAfterReset.results, null);
  assert.equal(demoStateAfterReset.document, null);
  assert.equal(demoStateAfterReset.selectedId, null);

  const ctrlCore = new InvoiceActionController({
    transport: coreTransport,
    newRequestId: () => RID,
    now: () => Date.now(),
    allowDemoSource: false, // CORE strictly forbids demo source!
  });
  ctrlCore.setScope("lotus-fin:CORE:NORMAL");

  // Verify CORE state is clean (ZERO demo records)
  const coreStateInitial = ctrlCore.getState();
  assert.equal(coreStateInitial.context, null);
  assert.equal(coreStateInitial.results, null);
  assert.equal(coreStateInitial.document, null);

  // When user searches in CORE, it calls CORE transport, returning disabled notice, never synthetic rows
  await ctrlCore.loadContext("Core Company");
  assert.equal(coreCalls.length, 1);
  assert.equal(coreCalls[0], "invoice.context");
  const coreState = ctrlCore.getState();
  assert.equal(coreState.context, null);
  assert.equal(coreState.results, null);
  assert.equal(coreState.document, null);
  assert.equal(coreState.notice?.kind, "unavailable");
  assert.equal(coreState.notice?.reason, "DISABLED");
});

test("P1-01: CORE controller rejects any DEMO source response even if transport leaked it", async () => {
  // If a buggy transport somehow returned DEMO_ISOLATED source to a CORE controller
  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const ctrlCore = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => Date.now(),
    allowDemoSource: false, // CORE: allowDemoSource is strictly false
  });
  ctrlCore.setScope("lotus-fin:CORE");

  await ctrlCore.loadContext("Any Company");
  const state = ctrlCore.getState();
  // Must fail closed with INVALID_RESPONSE notice, no context or results allowed
  assert.equal(state.context, null);
  assert.equal(state.results, null);
  assert.equal(state.notice?.kind, "unavailable");
  assert.equal(state.notice?.reason, "INVALID_RESPONSE");
});

test("P1-01: stale asynchronous response from old profile is aborted and cannot update state", async () => {
  let resolveDelayedCall: ((val: any) => void) | null = null;
  const delayedTransport: InvoiceActionTransport = {
    post(capability, payload, signal) {
      return new Promise((resolve) => {
        resolveDelayedCall = resolve;
        signal.addEventListener("abort", () => {
          resolve({ status: 0, data: null, aborted: true });
        });
      });
    },
  };

  const ctrl = new InvoiceActionController({
    transport: delayedTransport,
    newRequestId: () => RID,
    now: () => Date.now(),
    allowDemoSource: true,
  });
  ctrl.setScope("lotus-fin:DEMO:1");

  // Start in-flight request
  const loadPromise = ctrl.loadContext("Demo Company");
  assert.equal(ctrl.getState().busy, "context");

  // Switch profile / scope: reset() aborts and bumps generation
  ctrl.reset();
  assert.equal(ctrl.getState().busy, null);
  assert.equal(ctrl.getState().context, null);

  // Late response arrives from network after profile switch
  if (resolveDelayedCall) {
    (resolveDelayedCall as (v: any) => void)({
      status: 200,
      data: {
        message: {
          contract_version: "p1.invoice.v1",
          status: "OK",
          reason_code: "CONTEXT_READY",
          correlation_id: CID,
          request_id: RID,
          capability: "invoice.context",
          source: {
            mode: "DEMO_ISOLATED",
            verification: "AUTHORIZED_READ",
            product_ref: "lotus",
            site_ref: "site1",
            connection_ref: "conn1",
            connection_version: "1.0.0",
            projection_version: "invoice.min.v1",
            observed_at: "2026-10-12T00:00:00+00:00",
            timezone: "Asia/Ho_Chi_Minh",
            coverage: "PAGE_COMPLETE",
            consistency: "LIVE_KEYSET",
          },
          context_version: "ctx_demo_2026_v1",
          data: {
            context_ref: "stale.ref",
            context_version: "ctx_demo_2026_v1",
            company_label: "Stale Demo",
            allowed_filters: ["invoice_name_prefix", "posting_date", "docstatus"],
            default_posting_from: "2026-07-15",
            default_posting_to: "2026-10-12",
            expires_at: "2099-01-01T00:00:00Z",
          },
        },
      },
      headers: { "x-correlation-id": CID },
    });
  }
  await loadPromise;

  // Stale late response MUST NOT be admitted into state
  const state = ctrl.getState();
  assert.equal(state.context, null);
  assert.equal(state.busy, null);
});

test("P1-01: every DEMO scenario transitions cleanly without remount", async () => {
  for (const scenario of ["NORMAL", "PARTIAL", "EMPTY", "FORBIDDEN", "EXPIRED", "STALE"] as const) {
    const transport = createDemoInvoiceTransport(scenario);
    const ctrl = new InvoiceActionController({
      transport,
      newRequestId: () => RID,
      now: () => Date.now(),
      allowDemoSource: true,
    });
    ctrl.setScope(`lotus-fin:DEMO:${scenario}`);

    await ctrl.loadContext("Test Co");
    const s = ctrl.getState();
    if (scenario === "FORBIDDEN") {
      assert.equal(s.notice?.kind, "denied");
    } else {
      assert.ok(s.context);
    }
    // Clean reset between scenarios
    ctrl.reset();
    assert.equal(ctrl.getState().context, null);
  }
});
