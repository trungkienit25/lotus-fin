import test from "node:test";
import assert from "node:assert/strict";
import { createHttpTransport, createProductionTransport } from "../src/pages/copilot/actions/invoiceActionClient.ts";
import { createDemoInvoiceTransport } from "../src/pages/copilot/demo/demoInvoiceProvider.ts";
import { InvoiceActionController } from "../src/pages/copilot/actions/invoiceActionController.ts";
import { parseInvoiceIntent, validateSearchCriteria } from "../src/pages/copilot/actions/invoiceActionPresentation.ts";
import { parseInvoiceOutcome } from "../src/pages/copilot/actions/invoiceActionDecoders.ts";

const RID = "11111111-1111-4111-8111-111111111111";
const CID = "22222222-2222-4222-8222-222222222222";

test("CORE HTTP Transport: sends POST with JSON body and CSRF header to declared endpoints", async () => {
  const calls: { url: string; method?: string; headers?: Record<string, string>; body?: string }[] = [];
  const origFetch = globalThis.fetch;

  (globalThis as any).fetch = async (url: string, init?: RequestInit) => {
    calls.push({
      url,
      method: init?.method,
      headers: init?.headers as Record<string, string>,
      body: init?.body as string,
    });
    return {
      status: 503,
      headers: new Headers({ "x-correlation-id": CID }),
      json: async () => ({
        message: {
          contract_version: "p1.invoice.v1",
          status: "NOT_AVAILABLE",
          reason_code: "CAPABILITY_DISABLED",
          correlation_id: CID,
          request_id: RID,
          capability: "invoice.context",
          source: null,
          context_version: null,
          data: null,
          user_message: "disabled",
        },
      }),
    };
  };

  try {
    const transport = createHttpTransport({
      baseUrl: "http://127.0.0.1:8097",
      getCsrfToken: () => "test-csrf-token-123",
    });

    const res = await transport.post("invoice.context", {
      request_id: RID,
      company_candidate: "Lotus Corp",
    }, new AbortController().signal);

    assert.equal(res.status, 503);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "http://127.0.0.1:8097/api/method/lotus_fin.api.invoice_actions_api.get_context");
    assert.equal(calls[0].method, "POST");
    assert.equal(calls[0].headers?.["X-Frappe-CSRF-Token"], "test-csrf-token-123");
    assert.equal(calls[0].headers?.["Content-Type"], "application/json");
    const sentBody = JSON.parse(calls[0].body || "{}");
    assert.equal(sentBody.company_candidate, "Lotus Corp");
    assert.equal(sentBody.request_id, RID);
  } finally {
    globalThis.fetch = origFetch;
  }
});

test("CORE HTTP Transport: unauthenticated guest 403 maps to ACCESS_DENIED", async () => {
  const origFetch = globalThis.fetch;
  (globalThis as any).fetch = async () => {
    return {
      status: 403,
      headers: new Headers(),
      json: async () => ({
        message: {
          contract_version: "p1.invoice.v1",
          status: "FORBIDDEN",
          reason_code: "AUTH_REQUIRED",
          correlation_id: CID,
          request_id: RID,
          capability: "invoice.context",
          source: null,
          context_version: null,
          data: null,
          user_message: "forbidden",
        },
      }),
    };
  };

  try {
    const ctrl = new InvoiceActionController({
      transport: createHttpTransport({ getCsrfToken: () => "unit-token" }),
      newRequestId: () => RID,
      now: () => Date.now(),
    });
    await ctrl.loadContext("Lotus Corp");
    const s = ctrl.getState();
    assert.equal(s.context, null);
    assert.equal(s.notice?.kind, "denied");
    assert.equal(s.notice?.reason, "ACCESS_DENIED");
  } finally {
    globalThis.fetch = origFetch;
  }
});

test("CORE HTTP Transport: server 503 CAPABILITY_DISABLED produces truthful disabled notice without fabricated rows", async () => {
  const origFetch = globalThis.fetch;
  (globalThis as any).fetch = async () => {
    return {
      status: 503,
      headers: new Headers({ "x-correlation-id": CID }),
      json: async () => ({
        message: {
          contract_version: "p1.invoice.v1",
          status: "NOT_AVAILABLE",
          reason_code: "CAPABILITY_DISABLED",
          correlation_id: CID,
          request_id: RID,
          capability: "invoice.context",
          source: null,
          context_version: null,
          data: null,
          user_message: "disabled",
        },
      }),
    };
  };

  try {
    const ctrl = new InvoiceActionController({
      transport: createHttpTransport({ getCsrfToken: () => "unit-token" }),
      newRequestId: () => RID,
      now: () => Date.now(),
    });
    await ctrl.loadContext("Lotus Corp");
    const s = ctrl.getState();
    assert.equal(s.context, null);
    assert.equal(s.results, null);
    assert.equal(s.document, null);
    assert.equal(s.notice?.kind, "unavailable");
    assert.equal(s.notice?.reason, "DISABLED");
  } finally {
    globalThis.fetch = origFetch;
  }
});

test("DEMO profile: complete Search -> Select -> Open lifecycle with DEMO_ISOLATED source", async () => {
  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const ctrl = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => 0,
    allowDemoSource: true,
  });

  // 1. Load context
  await ctrl.loadContext("Lotus Synthetic Demo Ltd");
  const s1 = ctrl.getState();
  assert.ok(s1.context);
  assert.equal(s1.context.companyLabel, "Lotus Synthetic Demo Ltd (Demo Isolated)");
  assert.equal(s1.context.sourceMode, "DEMO_ISOLATED");

  // 2. Search
  await ctrl.search({ prefix: "DEMO-SINV-2026" });
  const s2 = ctrl.getState();
  assert.ok(s2.results);
  assert.equal(s2.results.kind, "results");
  assert.equal(s2.results.items.length, 3);
  assert.equal(s2.results.complete, true);
  assert.equal(s2.results.items[0].invoiceId, "DEMO-SINV-2026-001");
  assert.ok(s2.results.items[0].selectionRef);

  // 3. Open
  await ctrl.openInvoice("DEMO-SINV-2026-001");
  const s3 = ctrl.getState();
  assert.ok(s3.document);
  assert.equal(s3.document.kind, "document");
  assert.equal(s3.document.document.invoice_id, "DEMO-SINV-2026-001");
  assert.equal(s3.document.sourceMode, "DEMO_ISOLATED");
  assert.equal(s3.document.companyLabel, "Lotus Synthetic Demo Ltd (Demo Isolated)");
});

test("DEMO profile: PARTIAL scenario disables selection handles", async () => {
  const demoTransport = createDemoInvoiceTransport("PARTIAL");
  const ctrl = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => 0,
    allowDemoSource: true,
  });

  await ctrl.loadContext("Lotus Synthetic Demo Ltd");
  await ctrl.search({ prefix: "DEMO" });
  const s = ctrl.getState();
  assert.ok(s.results);
  assert.equal(s.results.kind, "results");
  assert.equal(s.results.complete, false);
  assert.equal(s.results.items[0].selectionRef, null);
  // Attempt open should be rejected safely
  await ctrl.openInvoice("DEMO-SINV-2026-001");
  assert.equal(ctrl.getState().document, null);
});

test("DEMO profile: EMPTY scenario produces clean empty result", async () => {
  const demoTransport = createDemoInvoiceTransport("EMPTY");
  const ctrl = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => 0,
    allowDemoSource: true,
  });

  await ctrl.loadContext("Lotus Synthetic Demo Ltd");
  await ctrl.search({ prefix: "DEMO" });
  const s = ctrl.getState();
  assert.ok(s.results);
  assert.equal(s.results.kind, "empty");
});

test("DEMO profile: FORBIDDEN scenario clears protected state to denied notice", async () => {
  const demoTransport = createDemoInvoiceTransport("FORBIDDEN");
  const ctrl = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => 0,
    allowDemoSource: true,
  });

  await ctrl.loadContext("Lotus Synthetic Demo Ltd");
  const s = ctrl.getState();
  assert.equal(s.context, null);
  assert.equal(s.notice?.kind, "denied");
  assert.equal(s.notice?.reason, "ACCESS_DENIED");
});

test("DEMO Isolation: attempted DEMO source in CORE profile without allowDemoSource fails closed", async () => {
  const demoTransport = createDemoInvoiceTransport("NORMAL");
  const ctrl = new InvoiceActionController({
    transport: demoTransport,
    newRequestId: () => RID,
    now: () => 0,
    allowDemoSource: false, // CORE profile: allowDemoSource is false!
  });

  await ctrl.loadContext("Lotus Synthetic Demo Ltd");
  const s = ctrl.getState();
  // Must fail closed because DEMO source is rejected when allowDemoSource is false
  assert.equal(s.context, null);
  assert.equal(s.notice?.kind, "unavailable");
  assert.equal(s.notice?.reason, "INVALID_RESPONSE");
});

test("Deterministic intent routing: invoice search, clarification, and unsupported", () => {
  // Supported valid search
  const res1 = parseInvoiceIntent("tìm hóa đơn SINV-2026");
  assert.equal(res1.kind, "search");
  if (res1.kind === "search") {
    assert.equal(res1.criteria.prefix, "SINV-2026");
  }

  // Ambiguous needs processing / overdue requires clarification
  const res2 = parseInvoiceIntent("tìm các hóa đơn quá hạn chưa thanh toán");
  assert.equal(res2.kind, "clarify");
  if (res2.kind === "clarify") {
    assert.ok(res2.questions[0].includes("not supported yet"));
  }

  // Search keyword without criteria asks for criteria clarification
  const res3 = parseInvoiceIntent("search invoice");
  assert.equal(res3.kind, "clarify");
  if (res3.kind === "clarify") {
    assert.ok(res3.questions[0].includes("Which invoices?"));
  }

  // Unrelated request is unsupported
  const res4 = parseInvoiceIntent("thời tiết hôm nay thế nào");
  assert.equal(res4.kind, "unsupported");
});
