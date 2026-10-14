/**
 * Shared types, constants, and envelopes for the Synthetic Demo Provider.
 * Strictly fictional records isolated from production and ERPNext.
 * Complies with ADR001 (< 200 lines).
 */

export type DemoScenario = "NORMAL" | "PARTIAL" | "EMPTY" | "EXPIRED" | "FORBIDDEN" | "STALE";

export interface DemoInvoiceRow {
  invoice_type: "SALES";
  invoice_id: string;
  posting_date: string;
  docstatus: 0 | 1;
  record_version: string;
  selection_ref: string | null;
}

export const DEMO_CONTEXT_VERSION = "ctx_demo_2026_v1";
export const DEMO_COMPANY_LABEL = "Lotus Synthetic Demo Ltd (Demo Isolated)";

export const DEMO_RECORDS: readonly DemoInvoiceRow[] = [
  {
    invoice_type: "SALES",
    invoice_id: "DEMO-SINV-2026-001",
    posting_date: "2026-09-15",
    docstatus: 1,
    record_version: "rec_demo_001",
    selection_ref: "ref.v2.sel.DEMO-SINV-2026-001",
  },
  {
    invoice_type: "SALES",
    invoice_id: "DEMO-SINV-2026-002",
    posting_date: "2026-09-28",
    docstatus: 0,
    record_version: "rec_demo_002",
    selection_ref: "ref.v2.sel.DEMO-SINV-2026-002",
  },
  {
    invoice_type: "SALES",
    invoice_id: "DEMO-SINV-2026-003",
    posting_date: "2026-10-05",
    docstatus: 1,
    record_version: "rec_demo_003",
    selection_ref: "ref.v2.sel.DEMO-SINV-2026-003",
  },
];

export function uuid4(): string {
  return typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : "00000000-0000-4000-8000-000000000000";
}

export function demoSource(coverage: "PAGE_COMPLETE" | "INCOMPLETE" = "PAGE_COMPLETE") {
  return {
    mode: "DEMO_ISOLATED" as const,
    verification: "AUTHORIZED_READ" as const,
    product_ref: "lotus-demo",
    site_ref: "demo-site-01",
    connection_ref: "demo-conn-01",
    connection_version: "1.0.0",
    projection_version: "invoice.min.v1",
    observed_at: "2026-10-12T00:00:00+00:00",
    timezone: "Asia/Ho_Chi_Minh",
    coverage,
    consistency: "LIVE_KEYSET" as const,
  };
}
