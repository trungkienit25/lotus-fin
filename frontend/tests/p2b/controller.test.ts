import test from "node:test";
import assert from "node:assert/strict";
import { InvoiceActionController } from "../../src/pages/copilot/actions/invoiceActionController.ts";
import { row, okContext, okSearch, partialSearch, okOpen, failure, envelope, searchData, source } from "./fixtures.ts";

type Call = { capability: string; payload: any; signal: AbortSignal; resolve: (r: any) => void; reject: (e: unknown) => void };

function harness(opts: { now?: () => number } = {}) {
  const calls: Call[] = [];
  let n = 0;
  const transport = {
    post: (capability: string, payload: any, signal: AbortSignal) =>
      new Promise<any>((resolve, reject) => { calls.push({ capability, payload, signal, resolve, reject }); }),
  };
  const ctrl = new InvoiceActionController({
    transport,
    newRequestId: () => `00000000-0000-4000-8000-${String(++n).padStart(12, "0")}`,
    now: opts.now ?? (() => Date.parse("2026-10-12T00:00:00Z")),
    allowDemoSource: true,
  });
  // Reply to the most recent call with an envelope whose request_id matches what was sent.
  const reply = (c: Call, body: any, status = 200) =>
    c.resolve({ status, data: { message: { ...body, request_id: c.payload.request_id } } });
  const flush = () => new Promise((r) => setImmediate(r));
  return { ctrl, calls, reply, flush };
}

async function ready(h: ReturnType<typeof harness>, items = [row("A"), row("B")]) {
  const p1 = h.ctrl.loadContext("Lotus Corp");
  h.reply(h.calls[0], okContext());
  await p1;
  const p2 = h.ctrl.search({ prefix: "SINV" });
  h.reply(h.calls[1], okSearch(items));
  await p2;
}

test("happy path: context -> search -> explicit select -> read-only document", async () => {
  const h = harness();
  await ready(h);
  assert.equal(h.ctrl.getState().results?.kind, "results");
  assert.equal(h.calls.length, 2, "no automatic open after search");
  const p = h.ctrl.openInvoice("B");
  const open = h.calls[2];
  assert.equal(open.capability, "invoice.open");
  assert.equal(open.payload.selection_ref, "ref.v2.sel.B");
  assert.equal(open.payload.context_ref, "ref.v1.ctx.sig");
  assert.equal(open.payload.expected_context_version, "ctx_abc");
  h.reply(open, okOpen("B"));
  await p;
  assert.equal(h.ctrl.getState().document?.document.invoice_id, "B");
  const ids = h.calls.map((c) => c.payload.request_id);
  assert.equal(new Set(ids).size, ids.length, "request_id is unique per operation");
});

test("a single match is never opened automatically", async () => {
  const h = harness();
  await ready(h, [row("ONLY")]);
  await h.flush();
  assert.equal(h.calls.length, 2);
  assert.equal(h.ctrl.getState().selectedId, null);
});

test("search without a context performs no request", async () => {
  const h = harness();
  await h.ctrl.search({ prefix: "SINV" });
  assert.equal(h.calls.length, 0);
  assert.equal(h.ctrl.getState().notice?.kind, "expired");
});

test("invalid criteria set clarification and perform no request", async () => {
  const h = harness();
  const p = h.ctrl.loadContext("Lotus Corp"); h.reply(h.calls[0], okContext()); await p;
  await h.ctrl.search({});
  assert.equal(h.calls.length, 1);
  assert.ok((h.ctrl.getState().clarification ?? []).length > 0);
});

test("out-of-order search: only the latest response updates state", async () => {
  const h = harness();
  const p0 = h.ctrl.loadContext("Lotus Corp"); h.reply(h.calls[0], okContext()); await p0;
  const a = h.ctrl.search({ prefix: "AAA" });
  const b = h.ctrl.search({ prefix: "BBB" });
  assert.equal(h.calls[1].signal.aborted, true, "previous request aborted");
  h.reply(h.calls[2], okSearch([row("NEW")])); await b;
  h.reply(h.calls[1], okSearch([row("OLD")])); await a;
  const r = h.ctrl.getState().results;
  assert.ok(r && r.kind === "results" && r.items[0].invoiceId === "NEW");
});

test("stale open response after selecting another invoice is ignored", async () => {
  const h = harness();
  await ready(h);
  const x = h.ctrl.openInvoice("A");
  const y = h.ctrl.openInvoice("B");
  h.reply(h.calls[3], okOpen("B")); await y;
  h.reply(h.calls[2], okOpen("A")); await x;
  assert.equal(h.ctrl.getState().document?.document.invoice_id, "B");
  assert.equal(h.ctrl.getState().selectedId, "B");
});

test("scope switch (company/context/actor) clears state and discards late responses", async () => {
  const h = harness();
  h.ctrl.setScope("company-a|ctx-1");
  const p0 = h.ctrl.loadContext("A"); h.reply(h.calls[0], okContext()); await p0;
  const s = h.ctrl.search({ prefix: "SINV" });
  h.ctrl.setScope("company-b|ctx-1");
  assert.equal(h.calls[1].signal.aborted, true);
  assert.equal(h.ctrl.getState().context, null);
  h.reply(h.calls[1], okSearch([row("LEAK")])); await s;
  assert.equal(h.ctrl.getState().results, null);
  assert.equal(h.ctrl.getState().busy, null);
});

test("setScope with the same key does not reset", async () => {
  const h = harness();
  h.ctrl.setScope("k"); await ready(h);
  h.ctrl.setScope("k");
  assert.equal(h.ctrl.getState().results?.kind, "results");
});

test("reset/logout clears protected state and fences in-flight work", async () => {
  const h = harness();
  await ready(h);
  const p = h.ctrl.openInvoice("A");
  h.ctrl.reset();
  h.reply(h.calls[2], okOpen("A")); await p;
  const s = h.ctrl.getState();
  assert.deepEqual([s.context, s.results, s.document, s.selectedId, s.notice, s.busy], [null, null, null, null, null, null]);
});

test("FORBIDDEN on open clears results, document, selection and context", async () => {
  const h = harness();
  await ready(h);
  const p = h.ctrl.openInvoice("A");
  h.reply(h.calls[2], failure("FORBIDDEN", "ACCESS_DENIED", "invoice.open")); await p;
  const s = h.ctrl.getState();
  assert.equal(s.notice?.kind, "denied");
  assert.deepEqual([s.context, s.results, s.document, s.selectedId], [null, null, null, null]);
});

test("HTTP 403 with a success-looking body is treated as denial", async () => {
  const h = harness();
  await ready(h);
  const p = h.ctrl.openInvoice("A");
  h.reply(h.calls[2], okOpen("A"), 403); await p;
  assert.equal(h.ctrl.getState().notice?.kind, "denied");
  assert.equal(h.ctrl.getState().document, null);
});

test("expired/changed context on open clears actionable controls", async () => {
  const h = harness();
  await ready(h);
  const p = h.ctrl.openInvoice("A");
  h.reply(h.calls[2], failure("NOT_AVAILABLE", "STALE_SELECTION", "invoice.open")); await p;
  const s = h.ctrl.getState();
  assert.equal(s.notice?.kind, "expired");
  assert.deepEqual([s.context, s.results, s.document], [null, null, null]);
});

test("client-side expiry blocks open without a request", async () => {
  let t = Date.parse("2026-10-12T00:00:00Z");
  const h = harness({ now: () => t });
  const p0 = h.ctrl.loadContext("Lotus Corp");
  h.reply(h.calls[0], okContext({ expires_at: "2026-10-12T00:05:00+00:00" })); await p0;
  const s = h.ctrl.search({ prefix: "SINV" }); h.reply(h.calls[1], okSearch([row("A")])); await s;
  t = Date.parse("2026-10-12T00:05:00Z"); // equality counts as expired
  await h.ctrl.openInvoice("A");
  assert.equal(h.calls.length, 2);
  assert.equal(h.ctrl.getState().notice?.kind, "expired");
  assert.equal(h.ctrl.getState().results, null);
});

test("PARTIAL results expose no selectable ref and open is refused without a request", async () => {
  const h = harness();
  const p0 = h.ctrl.loadContext("Lotus Corp"); h.reply(h.calls[0], okContext()); await p0;
  const s = h.ctrl.search({ prefix: "SINV" }); h.reply(h.calls[1], partialSearch([row("A", null)])); await s;
  await h.ctrl.openInvoice("A");
  assert.equal(h.calls.length, 2);
  assert.equal(h.ctrl.getState().document, null);
});

test("opening an invoice that is not in the current results is refused", async () => {
  const h = harness();
  await ready(h);
  await h.ctrl.openInvoice("NOT-LISTED");
  assert.equal(h.calls.length, 2);
});

test("opened document that differs from the selected row fails closed", async () => {
  const h = harness();
  await ready(h);
  const p = h.ctrl.openInvoice("A");
  h.reply(h.calls[2], okOpen("DIFFERENT")); await p;
  assert.equal(h.ctrl.getState().document, null);
  assert.equal(h.ctrl.getState().notice?.kind, "unavailable");
});

test("malformed search response shows nothing selectable", async () => {
  const h = harness();
  const p0 = h.ctrl.loadContext("Lotus Corp"); h.reply(h.calls[0], okContext()); await p0;
  const s = h.ctrl.search({ prefix: "SINV" });
  h.reply(h.calls[1], envelope({ data: searchData([row("A")], { total_count: 99 }) })); await s;
  assert.equal(h.ctrl.getState().results, null);
  assert.equal(h.ctrl.getState().notice?.kind, "unavailable");
});

test("replayed response with another request_id is rejected", async () => {
  const h = harness();
  const p = h.ctrl.loadContext("Lotus Corp");
  h.calls[0].resolve({ status: 200, data: { message: { ...okContext(), request_id: "99999999-9999-4999-8999-999999999999" } } });
  await p;
  assert.equal(h.ctrl.getState().context, null);
  assert.equal(h.ctrl.getState().notice?.kind, "unavailable");
});

test("transport failure maps to SOURCE_ERROR, timeout code to TIMEOUT, abort is silent", async () => {
  const h = harness();
  const a = h.ctrl.loadContext("X"); h.calls[0].reject(Object.assign(new Error("net"), { code: "ERR_NETWORK" })); await a;
  assert.equal((h.ctrl.getState().notice as any)?.reason, "SOURCE_ERROR");
  const b = h.ctrl.loadContext("X"); h.calls[1].reject(Object.assign(new Error("t"), { code: "ECONNABORTED" })); await b;
  assert.equal((h.ctrl.getState().notice as any)?.reason, "TIMEOUT");
  const c = h.ctrl.loadContext("X"); h.ctrl.reset();
  h.calls[2].reject(Object.assign(new Error("aborted"), { name: "AbortError" })); await c;
  assert.equal(h.ctrl.getState().notice, null);
});

test("controller never writes protected values to console", async () => {
  const seen: string[] = [];
  const orig = { log: console.log, warn: console.warn, error: console.error, info: console.info, debug: console.debug };
  for (const k of Object.keys(orig) as (keyof typeof orig)[]) console[k] = (...a: unknown[]) => { seen.push(String(a)); };
  try {
    const h = harness(); await ready(h);
    const p = h.ctrl.openInvoice("A"); h.reply(h.calls[2], failure("FORBIDDEN", "ACCESS_DENIED", "invoice.open")); await p;
  } finally { Object.assign(console, orig); }
  assert.deepEqual(seen, []);
});

test("subscribers are notified and unsubscribed listeners are not", async () => {
  const h = harness();
  let n = 0; const off = h.ctrl.subscribe(() => { n++; });
  const p = h.ctrl.loadContext("X"); h.reply(h.calls[0], okContext()); await p;
  assert.ok(n >= 2); const seen = n; off();
  h.ctrl.reset(); assert.equal(n, seen);
});
