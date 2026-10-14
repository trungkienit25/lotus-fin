import type { ContextVm, DocumentVm, EmptyVm, MetaVm, ResultsVm } from "./invoiceActionTypes.ts";
import {
  bad,
  dayNumber,
  DOC_KEYS,
  hasOnly,
  isCalendarDate,
  isCanonicalUtc,
  isObj,
  parseCore,
  parseRow,
  safeText,
  str,
} from "./invoiceActionDecoderHelpers.ts";

const SEARCH_KEYS = [
  "items", "returned_count", "total_count", "page_complete", "has_more", "next_cursor",
  "selection_required", "limitations",
];

export function parseSearchData(d: unknown, status: "OK" | "PARTIAL", reason: string, meta: MetaVm): ResultsVm | EmptyVm {
  if (!isObj(d) || !hasOnly(d, SEARCH_KEYS, ["items", "returned_count", "total_count", "page_complete", "selection_required"])) return bad();
  if (!Array.isArray(d.items) || d.items.length > 50 || d.returned_count !== d.items.length) return bad();
  if (d.total_count !== null) return bad();
  if (typeof d.page_complete !== "boolean" || typeof d.selection_required !== "boolean") return bad();

  const items = d.items.map(parseRow);
  if (new Set(items.map((i) => i.invoiceId)).size !== items.length) return bad();

  const hasMore = d.has_more;
  const nextCursor = d.next_cursor;
  if (d.limitations != null && (!Array.isArray(d.limitations)
    || !d.limitations.every((l) => l === "COVERAGE_INCOMPLETE" || l === "LIVE_WINDOW"))) return bad();

  // F01 rule: backend selection_required must be false when 0 rows, true when rows > 0
  const expectedSelectionRequired = items.length > 0;
  if (d.selection_required !== expectedSelectionRequired) return bad();

  if (status === "PARTIAL") {
    if (reason !== "COVERAGE_INCOMPLETE" || d.page_complete !== false || hasMore !== null || nextCursor !== null) return bad();
    if (items.some((i) => i.selectionRef !== null)) return bad();
    return { ...meta, kind: "results", items, complete: false, hasMore: null, nextCursor: null, selectionRequired: false };
  }

  // status === "OK"
  if (d.page_complete !== true) return bad();
  if (typeof hasMore !== "boolean") return bad();
  if (hasMore) {
    if (!str(nextCursor, 2048)) return bad();
  } else {
    if (nextCursor !== null) return bad();
  }

  if (items.length === 0) {
    if (reason !== "EMPTY_RESULT" || hasMore !== false || nextCursor !== null) return bad();
    return { ...meta, kind: "empty" };
  }
  if (reason !== "RESULTS_FOUND" || items.some((i) => i.selectionRef === null)) return bad();
  return { ...meta, kind: "results", items, complete: true, hasMore, nextCursor, selectionRequired: true };
}

export function parseOpenData(d: unknown, meta: MetaVm, expectedContext?: ContextVm | null): DocumentVm {
  if (!isObj(d) || !hasOnly(d, ["document", "company_label", "navigation"])) return bad();
  const doc = parseCore(d.document, DOC_KEYS, DOC_KEYS);
  const nav = d.navigation;
  if (!isObj(nav) || !hasOnly(nav, ["kind", "view"]) || nav.kind !== "LOTUS_READ_VIEW"
    || nav.view !== "sales-invoice-minimal-v1") return bad();
  if (!str(d.company_label, 128)) return bad();

  // F03 pin: company_label must match expected active context
  if (expectedContext && d.company_label !== expectedContext.companyLabel) return bad();

  return {
    ...meta,
    kind: "document",
    companyLabel: safeText(d.company_label),
    document: {
      invoice_type: "SALES",
      invoice_id: doc.invoice_id,
      posting_date: doc.posting_date,
      docstatus: doc.docstatus,
      record_version: doc.record_version,
    },
  };
}

const CONTEXT_KEYS = [
  "context_ref", "context_version", "company_label", "allowed_filters", "expires_at",
  "default_posting_from", "default_posting_to",
] as const;

export function parseContextData(d: unknown, meta: MetaVm, outerContextVersion?: string | null): ContextVm {
  // F02 rule: all 7 keys strictly required
  if (!isObj(d) || !hasOnly(d, CONTEXT_KEYS, CONTEXT_KEYS)) return bad();
  if (!str(d.context_ref, 2048) || !str(d.context_version, 128) || !str(d.company_label, 128)
    || !isCanonicalUtc(d.expires_at)) return bad();

  // F02 rule: outer context_version must match inner context_version
  if (outerContextVersion !== d.context_version) return bad();

  // F02 rule: allowed_filters must be exact tuple: ["invoice_name_prefix", "posting_date", "docstatus"]
  if (!Array.isArray(d.allowed_filters) || d.allowed_filters.length !== 3
    || d.allowed_filters[0] !== "invoice_name_prefix"
    || d.allowed_filters[1] !== "posting_date"
    || d.allowed_filters[2] !== "docstatus") return bad();

  // F02 rule: default_posting_from & default_posting_to are strictly required
  const f = d.default_posting_from;
  const t = d.default_posting_to;
  if (!isCalendarDate(f) || !isCalendarDate(t) || dayNumber(t) < dayNumber(f) || dayNumber(t) - dayNumber(f) + 1 > 365) return bad();

  return {
    ...meta,
    kind: "context",
    contextRef: d.context_ref,
    contextVersion: d.context_version,
    companyLabel: safeText(d.company_label),
    expiresAt: d.expires_at,
    defaults: { from: f, to: t },
  };
}
