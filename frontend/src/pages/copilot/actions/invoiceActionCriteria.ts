/**
 * Search criteria validation, intent parsing and payload builders for Sales Invoice actions.
 */
import type {
  CriteriaResult,
  IntentResult,
  SearchCriteriaInput,
  SearchFilters,
} from "./invoiceActionTypes.ts";
import { isCalendarDate, safeText } from "./invoiceActionDecoders.ts";

const dayNumber = (s: string) => Math.floor(Date.parse(s + "T00:00:00Z") / 86400000);

export function validateSearchCriteria(
  input: SearchCriteriaInput,
  defaults: { from: string; to: string } | null = null,
): CriteriaResult {
  const q: string[] = [];
  const f: SearchFilters = {};
  const nfc = typeof input.prefix === "string" ? input.prefix.normalize("NFC") : input.prefix;
  if (nfc !== undefined) {
    if (typeof nfc !== "string" || nfc.trim() === "" || nfc.length > 128 || safeText(nfc, 128) !== nfc) {
      q.push("Enter an invoice number prefix of 1 to 128 characters without control characters.");
    } else {
      f.invoice_name_prefix = nfc;
    }
  }
  if (input.docstatus !== undefined) {
    if (input.docstatus !== "DRAFT" && input.docstatus !== "SUBMITTED" && input.docstatus !== "BOTH") {
      q.push("Choose Draft, Submitted or Both for the invoice status.");
    } else {
      f.docstatus = input.docstatus;
    }
  }
  const hasFrom = input.postingFrom !== undefined && input.postingFrom !== "";
  const hasTo = input.postingTo !== undefined && input.postingTo !== "";
  if (hasFrom !== hasTo) {
    q.push("Provide both a start date and an end date, or neither.");
  } else if (hasFrom && hasTo) {
    if (!isCalendarDate(input.postingFrom) || !isCalendarDate(input.postingTo)) {
      q.push("Dates must be valid calendar dates (YYYY-MM-DD).");
    } else if (dayNumber(input.postingTo) < dayNumber(input.postingFrom)) {
      q.push("The end date must not be before the start date.");
    } else if (dayNumber(input.postingTo) - dayNumber(input.postingFrom) + 1 > 365) {
      q.push("The date range must not exceed 365 days.");
    } else {
      f.posting_from = input.postingFrom;
      f.posting_to = input.postingTo;
    }
  }
  if (q.length === 0 && Object.keys(f).length === 0) {
    q.push("Which invoices? Give an invoice number prefix, a date range, or a status (Draft, Submitted, Both).");
  }
  if (q.length > 0) return { ok: false, questions: q };
  if (defaults && f.posting_from === undefined) {
    f.posting_from = defaults.from;
    f.posting_to = defaults.to;
  }
  return { ok: true, filters: f };
}

const AMBIGUOUS = /(overdue|past due|unpaid|outstanding|needs? (to be )?process|need processing|cần xử lý|quá hạn|chưa thanh toán|chưa trả)/i;
const INVOICE_WORDS = /(invoice|hóa đơn|hoa don|sinv)/i;

export function parseInvoiceIntent(text: string): IntentResult {
  if (typeof text !== "string" || !INVOICE_WORDS.test(text)) return { kind: "unsupported" };
  if (AMBIGUOUS.test(text)) {
    return {
      kind: "clarify",
      questions: [
        "Overdue or payment status is not supported yet. Search by invoice number prefix, date range, or Draft/Submitted status instead.",
      ],
    };
  }
  const criteria: SearchCriteriaInput = {};
  const pre = text.match(/\b([A-Z]{2,}[A-Z0-9]*-[A-Z0-9-]*)/);
  if (pre) criteria.prefix = pre[1];
  if (/\bsubmitted\b/i.test(text)) criteria.docstatus = "SUBMITTED";
  else if (/\bdraft\b/i.test(text)) criteria.docstatus = "DRAFT";
  const dates = text.match(/\b\d{4}-\d{2}-\d{2}\b/g) ?? [];
  if (dates.length === 2) {
    criteria.postingFrom = dates[0];
    criteria.postingTo = dates[1];
  } else if (dates.length === 1) {
    criteria.postingFrom = dates[0];
  }
  if (Object.keys(criteria).length === 0) {
    return {
      kind: "clarify",
      questions: [
        "Which invoices? Give an invoice number prefix, a date range, or a status (Draft, Submitted, Both).",
      ],
    };
  }
  return { kind: "search", criteria };
}

export function buildContextPayload(a: { requestId: string; companyCandidate: string }) {
  return { request_id: a.requestId, company_candidate: a.companyCandidate };
}

export function buildSearchPayload(a: {
  requestId: string;
  contextRef: string;
  contextVersion: string;
  filters: SearchFilters;
  pageSize?: number;
}) {
  const p: Record<string, unknown> = {
    request_id: a.requestId,
    context_ref: a.contextRef,
    expected_context_version: a.contextVersion,
    invoice_type: "SALES",
    filters: { ...a.filters },
  };
  if (a.pageSize !== undefined) {
    if (!Number.isInteger(a.pageSize) || a.pageSize < 1 || a.pageSize > 50) {
      throw new Error("page_size out of range");
    }
    p.page_size = a.pageSize;
  }
  return p as {
    request_id: string;
    context_ref: string;
    expected_context_version: string;
    invoice_type: "SALES";
    filters: SearchFilters;
    page_size?: number;
  };
}

export function buildOpenPayload(a: {
  requestId: string;
  contextRef: string;
  contextVersion: string;
  selectionRef: string;
}) {
  return {
    request_id: a.requestId,
    context_ref: a.contextRef,
    expected_context_version: a.contextVersion,
    selection_ref: a.selectionRef,
  };
}
