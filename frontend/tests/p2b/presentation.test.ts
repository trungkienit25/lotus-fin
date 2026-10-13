import test from "node:test";
import assert from "node:assert/strict";
import {
  parseInvoiceOutcome,
  validateSearchCriteria,
  parseInvoiceIntent,
  buildSearchPayload,
  safeText,
} from "../../src/pages/copilot/actions/invoiceActionPresentation.ts";
import {
  RID, CID, row, envelope, okSearch, partialSearch, okContext, okOpen, failure, searchData, source,
} from "./fixtures.ts";

const opts = (capability: string, extra: Record<string, unknown> = {}) =>
  ({ capability, requestId: RID, allowDemoSource: true, ...extra }) as never;

// ---------- UI1: outcome mapping ----------
test("context OK maps to context view model with server fields only", () => {
  const vm = parseInvoiceOutcome(okContext(), opts("invoice.context"));
  assert.equal(vm.kind, "context");
  if (vm.kind === "context") {
    assert.equal(vm.companyLabel, "Lotus Corp");
    assert.equal(vm.contextRef, "ref.v1.ctx.sig");
    assert.deepEqual(vm.defaults, { from: "2026-07-15", to: "2026-10-12" });
  }
});

test("context with server date defaults exposes them", () => {
  const vm = parseInvoiceOutcome(
    okContext({ default_posting_from: "2026-07-15", default_posting_to: "2026-10-12" }), opts("invoice.context"));
  assert.equal(vm.kind, "context");
  if (vm.kind === "context") assert.deepEqual(vm.defaults, { from: "2026-07-15", to: "2026-10-12" });
});

test("complete results with items map to results with selectable refs", () => {
  const vm = parseInvoiceOutcome(okSearch([row("A"), row("B")]), opts("invoice.search"));
  assert.equal(vm.kind, "results");
  if (vm.kind === "results") {
    assert.equal(vm.complete, true);
    assert.equal(vm.items.length, 2);
    assert.ok(vm.items.every((i) => i.selectionRef !== null));
    assert.equal(vm.cid, CID);
  }
});

test("single match still requires explicit selection", () => {
  const vm = parseInvoiceOutcome(okSearch([row("ONLY")]), opts("invoice.search"));
  assert.equal(vm.kind, "results");
  if (vm.kind === "results") assert.equal(vm.selectionRequired, true);
});

test("empty complete result maps to empty", () => {
  assert.equal(parseInvoiceOutcome(okSearch([]), opts("invoice.search")).kind, "empty");
});

test("PARTIAL results are never selectable", () => {
  const vm = parseInvoiceOutcome(partialSearch([row("A", null)]), opts("invoice.search"));
  assert.equal(vm.kind, "results");
  if (vm.kind === "results") {
    assert.equal(vm.complete, false);
    assert.ok(vm.items.every((i) => i.selectionRef === null));
  }
});

test("PARTIAL carrying a selection_ref fails closed", () => {
  const vm = parseInvoiceOutcome(partialSearch([row("A", "ref.v2.leak")]), opts("invoice.search"));
  assert.equal(vm.kind, "unavailable");
});

test("PARTIAL with zero items is not mapped to empty", () => {
  const vm = parseInvoiceOutcome(partialSearch([]), opts("invoice.search"));
  assert.notEqual(vm.kind, "empty");
  assert.equal(vm.kind, "results");
});

test("OK with row missing selection_ref fails closed", () => {
  assert.equal(parseInvoiceOutcome(okSearch([row("A", null)]), opts("invoice.search")).kind, "unavailable");
});

test("FORBIDDEN maps to denied and drops any payload", () => {
  const raw = envelope({ status: "FORBIDDEN", reason_code: "ACCESS_DENIED", data: searchData([row("A")]) });
  const vm = parseInvoiceOutcome(raw, opts("invoice.search"));
  assert.equal(vm.kind, "denied");
  assert.equal(JSON.stringify(vm).includes("rec_A"), false);
});

test("HTTP 401/403 is denial even with a success-looking body", () => {
  assert.equal(parseInvoiceOutcome(okSearch([row("A")]), opts("invoice.search", { httpStatus: 403 })).kind, "denied");
  assert.equal(parseInvoiceOutcome(okSearch([row("A")]), opts("invoice.search", { httpStatus: 401 })).kind, "denied");
});

test("stale/changed states map to expired", () => {
  for (const reason of ["CONTEXT_CHANGED", "STALE_SELECTION", "STALE_CURSOR", "CONTEXT_REQUIRED"]) {
    assert.equal(parseInvoiceOutcome(failure("NOT_AVAILABLE", reason), opts("invoice.search")).kind, "expired", reason);
  }
});

test("SOURCE_ERROR / TIMEOUT / NOT_AVAILABLE map to unavailable with reason", () => {
  const a = parseInvoiceOutcome(failure("SOURCE_ERROR", "SOURCE_FAILURE"), opts("invoice.search"));
  const b = parseInvoiceOutcome(failure("TIMEOUT", "DEADLINE_EXCEEDED"), opts("invoice.search"));
  const c = parseInvoiceOutcome(failure("NOT_AVAILABLE", "TARGET_UNQUALIFIED"), opts("invoice.search"));
  assert.deepEqual([a.kind, b.kind, c.kind], ["unavailable", "unavailable", "unavailable"]);
  assert.deepEqual(
    [a, b, c].map((v) => (v.kind === "unavailable" ? v.reason : "")),
    ["SOURCE_ERROR", "TIMEOUT", "NOT_AVAILABLE"],
  );
});

test("CAPABILITY_DISABLED maps to a distinct DISABLED state with no data", () => {
  const v = parseInvoiceOutcome(failure("NOT_AVAILABLE", "CAPABILITY_DISABLED"), opts("invoice.search"));
  assert.equal(v.kind, "unavailable");
  if (v.kind === "unavailable") assert.equal(v.reason, "DISABLED");
});

test("open OK maps to read-only document with exactly five fields", () => {
  const vm = parseInvoiceOutcome(okOpen("SINV-9"), opts("invoice.open"));
  assert.equal(vm.kind, "document");
  if (vm.kind === "document") {
    assert.deepEqual(Object.keys(vm.document).sort(),
      ["docstatus", "invoice_id", "invoice_type", "posting_date", "record_version"]);
    assert.equal(vm.companyLabel, "Lotus Corp");
  }
});

test("open document with extra financial field fails closed", () => {
  const raw = okOpen() as any;
  raw.data.document.grand_total = 100;
  assert.equal(parseInvoiceOutcome(raw, opts("invoice.open")).kind, "unavailable");
});

test("open navigation other than fixed descriptor fails closed (no arbitrary URL)", () => {
  const raw = okOpen() as any;
  raw.data.navigation = { kind: "URL", view: "https://evil.example/x" };
  assert.equal(parseInvoiceOutcome(raw, opts("invoice.open")).kind, "unavailable");
  const raw2 = okOpen() as any;
  raw2.data.navigation = { kind: "LOTUS_READ_VIEW", view: "sales-invoice-minimal-v1", href: "/app/sales-invoice/X" };
  assert.equal(parseInvoiceOutcome(raw2, opts("invoice.open")).kind, "unavailable");
});

// ---------- fail-closed envelope checks ----------
test("malformed and unknown outcomes fail closed", () => {
  const bad: unknown[] = [
    null, undefined, "ok", 42, [], {}, { message: null },
    envelope({ contract_version: "p9" }),
    envelope({ status: "SUCCESS" }),
    envelope({ status: "OK", reason_code: "ACCESS_DENIED", data: searchData([]) }),
    envelope({ extra_key: 1, data: searchData([]) }),
    envelope({ correlation_id: "not-a-uuid", data: searchData([]) }),
    envelope({ capability: "invoice.open", data: searchData([]) }),
    envelope({ request_id: "99999999-9999-4999-8999-999999999999", data: searchData([]) }),
    { message: { message: okSearch([]) } }, // double wrap
    okSearch([row("A"), row("A")]), // duplicate ids
    envelope({ data: searchData([row("A")], { total_count: 12 }) }), // total leak
    envelope({ data: searchData([row("A")], { returned_count: 5 }) }),
    envelope({ data: searchData([{ ...row("A"), grand_total: 5 }]) }),
    envelope({ data: searchData([row("A")]), source: source("INCOMPLETE") }),
    envelope({ data: searchData([row("A")]), source: { ...source(), mode: "NOPE" } }),
  ];
  for (const raw of bad) {
    const vm = parseInvoiceOutcome(raw, opts("invoice.search"));
    assert.equal(vm.kind, "unavailable", JSON.stringify(raw)?.slice(0, 80));
    if (vm.kind === "unavailable") assert.ok(["INVALID_RESPONSE", "NOT_AVAILABLE"].includes(vm.reason));
  }
});

test("single Frappe message wrapper is unwrapped exactly once", () => {
  assert.equal(parseInvoiceOutcome({ message: okSearch([row("A")]) }, opts("invoice.search")).kind, "results");
});

test("header CID must match body CID", () => {
  const ok = parseInvoiceOutcome(okSearch([]), opts("invoice.search", { cidHeader: CID }));
  assert.equal(ok.kind, "empty");
  const bad = parseInvoiceOutcome(okSearch([]), opts("invoice.search", { cidHeader: "33333333-3333-4333-8333-333333333333" }));
  assert.equal(bad.kind, "unavailable");
});

test("demo source is rejected unless explicitly allowed (production path)", () => {
  const vm = parseInvoiceOutcome(okSearch([row("A")]), { capability: "invoice.search", requestId: RID } as never);
  assert.equal(vm.kind, "unavailable");
});

test("server user_message is never surfaced; messages are fixed English", () => {
  const vm = parseInvoiceOutcome(failure("SOURCE_ERROR", "SOURCE_FAILURE"), opts("invoice.search"));
  assert.ok(vm.kind === "unavailable" && !vm.message.includes("server text"));
  assert.match(vm.kind === "unavailable" ? vm.message : "", /[A-Za-z]/);
});

// ---------- safe text ----------
test("safeText strips control chars and bounds length; never interprets HTML", () => {
  assert.equal(safeText("a\u0000b\u0007c"), "abc");
  assert.equal(safeText("<img src=x onerror=alert(1)>"), "<img src=x onerror=alert(1)>");
  assert.equal(safeText("x".repeat(500), 10).length, 10);
});

// ---------- UI2: criteria & clarification ----------
test("no criteria triggers clarification", () => {
  const r = validateSearchCriteria({});
  assert.equal(r.ok, false);
});

test("prefix-only criteria is valid and omits dates (server default window)", () => {
  const r = validateSearchCriteria({ prefix: "SINV-2026" });
  assert.equal(r.ok, true);
  if (r.ok) assert.deepEqual(r.filters, { invoice_name_prefix: "SINV-2026" });
});

test("one date without the other is rejected", () => {
  assert.equal(validateSearchCriteria({ prefix: "S", postingFrom: "2026-01-01" }).ok, false);
  assert.equal(validateSearchCriteria({ prefix: "S", postingTo: "2026-01-01" }).ok, false);
});

test("reversed, over-365-day and non-calendar dates are rejected", () => {
  assert.equal(validateSearchCriteria({ postingFrom: "2026-02-01", postingTo: "2026-01-01" }).ok, false);
  assert.equal(validateSearchCriteria({ postingFrom: "2025-01-01", postingTo: "2026-01-02" }).ok, false);
  assert.equal(validateSearchCriteria({ postingFrom: "2026-02-30", postingTo: "2026-03-01" }).ok, false);
  assert.equal(validateSearchCriteria({ postingFrom: "2025-10-13", postingTo: "2026-10-12" }).ok, true); // 365 days
});

test("empty/whitespace/control/oversized prefix rejected", () => {
  for (const p of ["", "   ", "A\u0000B", "A".repeat(129)]) {
    assert.equal(validateSearchCriteria({ prefix: p, docstatus: "BOTH" }).ok, false, JSON.stringify(p));
  }
});

test("docstatus must be one of the closed values", () => {
  assert.equal(validateSearchCriteria({ docstatus: "OVERDUE" as never }).ok, false);
  const r = validateSearchCriteria({ docstatus: "SUBMITTED" });
  assert.equal(r.ok, true);
  if (r.ok) assert.deepEqual(r.filters, { docstatus: "SUBMITTED" });
});

test("server defaults alone do not satisfy the clarification requirement", () => {
  assert.equal(validateSearchCriteria({}, { from: "2026-07-15", to: "2026-10-12" }).ok, false);
});

test("server date defaults fill both dates when other criteria exist", () => {
  const r = validateSearchCriteria({ prefix: "S" }, { from: "2026-07-15", to: "2026-10-12" });
  assert.equal(r.ok, true);
  if (r.ok) assert.deepEqual(r.filters,
    { invoice_name_prefix: "S", posting_from: "2026-07-15", posting_to: "2026-10-12" });
});

// ---------- intent ----------
test("overdue / needs-processing wording requires clarification, never assumed overdue", () => {
  for (const t of ["show overdue invoices", "invoices that need processing", "hóa đơn cần xử lý", "unpaid invoices"]) {
    const i = parseInvoiceIntent(t);
    assert.equal(i.kind, "clarify", t);
    if (i.kind === "clarify") assert.ok(i.questions.length > 0);
  }
});

test("supported search intent extracts prefix, status and ISO dates", () => {
  const i = parseInvoiceIntent("find submitted sales invoices SINV-2026 from 2026-07-01 to 2026-09-30");
  assert.equal(i.kind, "search");
  if (i.kind === "search") {
    assert.deepEqual(i.criteria,
      { prefix: "SINV-2026", docstatus: "SUBMITTED", postingFrom: "2026-07-01", postingTo: "2026-09-30" });
  }
});

test("search intent without criteria asks for clarification; unrelated text is unsupported", () => {
  assert.equal(parseInvoiceIntent("find sales invoices").kind, "clarify");
  assert.equal(parseInvoiceIntent("what is the weather").kind, "unsupported");
});

// ---------- payload ----------
test("search payload: required filters object, omitted page_size, no nulls, no overrides", () => {
  const p = buildSearchPayload({ requestId: RID, contextRef: "c", contextVersion: "v", filters: {} });
  assert.deepEqual(Object.keys(p).sort(),
    ["context_ref", "expected_context_version", "filters", "invoice_type", "request_id"]);
  assert.deepEqual(p.filters, {});
  assert.equal(JSON.stringify(p).includes("null"), false);
  const q = buildSearchPayload({ requestId: RID, contextRef: "c", contextVersion: "v", filters: {}, pageSize: 20 });
  assert.equal(q.page_size, 20);
  assert.throws(() => buildSearchPayload({ requestId: RID, contextRef: "c", contextVersion: "v", filters: {}, pageSize: null as never }));
  assert.throws(() => buildSearchPayload({ requestId: RID, contextRef: "c", contextVersion: "v", filters: {}, pageSize: 51 }));
});

// ---------- F01 / F02 / F03 security & contract regression tests ----------
test("F01: empty result requires selection_required === false, true fails closed", () => {
  const badEmpty = okSearch([]);
  (badEmpty.data as any).selection_required = true;
  assert.equal(parseInvoiceOutcome(badEmpty, opts("invoice.search")).kind, "unavailable");

  const validEmpty = okSearch([]);
  assert.equal(parseInvoiceOutcome(validEmpty, opts("invoice.search")).kind, "empty");
});

test("F01: partial with zero rows requires selection_required === false and maps to results with complete=false", () => {
  const validPartialEmpty = partialSearch([]);
  const vm = parseInvoiceOutcome(validPartialEmpty, opts("invoice.search"));
  assert.equal(vm.kind, "results");
  if (vm.kind === "results") {
    assert.equal(vm.complete, false);
    assert.equal(vm.items.length, 0);
    assert.equal(vm.selectionRequired, false);
  }

  const badPartialEmpty = partialSearch([]);
  (badPartialEmpty.data as any).selection_required = true;
  assert.equal(parseInvoiceOutcome(badPartialEmpty, opts("invoice.search")).kind, "unavailable");
});

test("F02: ContextData strictly requires all 7 fields", () => {
  const missingFrom = okContext();
  delete (missingFrom.data as any).default_posting_from;
  assert.equal(parseInvoiceOutcome(missingFrom, opts("invoice.context")).kind, "unavailable");

  const missingTo = okContext();
  delete (missingTo.data as any).default_posting_to;
  assert.equal(parseInvoiceOutcome(missingTo, opts("invoice.context")).kind, "unavailable");
});

test("F02: ContextData requires exact allowed_filters tuple", () => {
  const badFilters = okContext({ allowed_filters: ["arbitrary_sql"] });
  assert.equal(parseInvoiceOutcome(badFilters, opts("invoice.context")).kind, "unavailable");

  const wrongOrder = okContext({ allowed_filters: ["posting_date", "invoice_name_prefix", "docstatus"] });
  assert.equal(parseInvoiceOutcome(wrongOrder, opts("invoice.context")).kind, "unavailable");
});

test("F02: ContextData outer context_version must match inner context_version", () => {
  const mismatch = okContext();
  mismatch.context_version = "foreign-context";
  assert.equal(parseInvoiceOutcome(mismatch, opts("invoice.context")).kind, "unavailable");
});

test("F03: Search and Open enforce context_version and source anchor pinning", () => {
  const expectedCtx = parseInvoiceOutcome(okContext(), opts("invoice.context"));
  assert.equal(expectedCtx.kind, "context");
  if (expectedCtx.kind !== "context") return;

  // Search context_version mismatch
  const badSearchVer = okSearch([row("A")]);
  badSearchVer.context_version = "foreign-ver";
  assert.equal(parseInvoiceOutcome(badSearchVer, opts("invoice.search", { expectedContext: expectedCtx })).kind, "unavailable");

  // Search source anchor mismatch
  for (const axis of ["site_ref", "product_ref", "connection_ref", "connection_version"] as const) {
    const badSrc = okSearch([row("A")]);
    (badSrc.source as any)[axis] = "tampered";
    assert.equal(parseInvoiceOutcome(badSrc, opts("invoice.search", { expectedContext: expectedCtx })).kind, "unavailable", axis);
  }

  // Open company_label mismatch
  const badOpenCompany = okOpen("SINV-1");
  (badOpenCompany.data as any).company_label = "Other Company";
  assert.equal(parseInvoiceOutcome(badOpenCompany, opts("invoice.open", { expectedContext: expectedCtx })).kind, "unavailable");
});

