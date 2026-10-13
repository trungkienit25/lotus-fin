// Synthetic fixtures shaped like the P1 outcome envelope (p1.invoice.v1) + P2-A data.
// Test-only: never imported by production modules.
export const RID = "11111111-1111-4111-8111-111111111111";
export const CID = "22222222-2222-4222-8222-222222222222";

export function source(coverage: "PAGE_COMPLETE" | "INCOMPLETE" = "PAGE_COMPLETE", mode = "DEMO_ISOLATED") {
  return {
    mode,
    verification: "AUTHORIZED_READ",
    product_ref: "lotus",
    site_ref: "site1",
    connection_ref: "conn1",
    connection_version: "1.0.0",
    projection_version: "invoice.min.v1",
    observed_at: "2026-10-12T00:00:00+00:00",
    timezone: "Asia/Ho_Chi_Minh",
    coverage,
    consistency: "LIVE_KEYSET",
  };
}

export function row(id: string, ref: string | null = "ref.v2.sel." + id) {
  return {
    invoice_type: "SALES",
    invoice_id: id,
    posting_date: "2026-10-01",
    docstatus: 1,
    record_version: "rec_" + id,
    selection_ref: ref,
  };
}

export function envelope(over: Record<string, unknown>) {
  return {
    contract_version: "p1.invoice.v1",
    status: "OK",
    reason_code: "RESULTS_FOUND",
    correlation_id: CID,
    request_id: RID,
    capability: "invoice.search",
    source: source(),
    context_version: "ctx_abc",
    data: null,
    user_message: "server text that must never be rendered",
    ...over,
  };
}

export function searchData(items: unknown[], over: Record<string, unknown> = {}) {
  return {
    items,
    returned_count: items.length,
    total_count: null,
    page_complete: true,
    has_more: false,
    next_cursor: null,
    selection_required: items.length > 0,
    limitations: null,
    ...over,
  };
}

export function okSearch(items: unknown[]) {
  return envelope({ data: searchData(items), reason_code: items.length ? "RESULTS_FOUND" : "EMPTY_RESULT" });
}

export function partialSearch(items: unknown[]) {
  return envelope({
    status: "PARTIAL",
    reason_code: "COVERAGE_INCOMPLETE",
    source: source("INCOMPLETE"),
    data: searchData(items, {
      page_complete: false,
      has_more: null,
      selection_required: items.length > 0,
      limitations: ["COVERAGE_INCOMPLETE"],
    }),
  });
}

export function okContext(over: Record<string, unknown> = {}) {
  return envelope({
    capability: "invoice.context",
    reason_code: "CONTEXT_READY",
    context_version: "ctx_abc",
    data: {
      context_ref: "ref.v1.ctx.sig",
      context_version: "ctx_abc",
      company_label: "Lotus Corp",
      allowed_filters: ["invoice_name_prefix", "posting_date", "docstatus"],
      expires_at: "2099-01-01T00:00:00+00:00",
      default_posting_from: "2026-07-15",
      default_posting_to: "2026-10-12",
      ...over,
    },
  });
}

export function okOpen(id = "SINV-001") {
  return envelope({
    capability: "invoice.open",
    reason_code: "DOCUMENT_READY",
    data: {
      document: {
        invoice_type: "SALES",
        invoice_id: id,
        posting_date: "2026-10-01",
        docstatus: 1,
        record_version: "rec_" + id,
      },
      company_label: "Lotus Corp",
      navigation: { kind: "LOTUS_READ_VIEW", view: "sales-invoice-minimal-v1" },
    },
  });
}

export function failure(status: string, reason: string, capability = "invoice.search") {
  return envelope({ status, reason_code: reason, capability, source: null, data: null, context_version: null });
}
