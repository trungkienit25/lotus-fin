/**
 * P2-B typed contracts and view models for Sales Invoice actions.
 */

export type InvoiceCapability = "invoice.context" | "invoice.search" | "invoice.open";
export type DocStatusFilter = "DRAFT" | "SUBMITTED" | "BOTH";

export interface SourceEvidence {
  sourceMode: string;
  observedAt: string;
  timezone: string;
  siteRef: string;
  productRef: string;
  connectionRef: string;
  connectionVersion: string;
}

export interface MetaVm extends SourceEvidence {
  cid: string;
  requestId: string;
}

export interface InvoiceRowVm {
  invoiceId: string;
  postingDate: string;
  docstatus: 0 | 1;
  recordVersion: string;
  selectionRef: string | null;
}

export interface ContextVm extends MetaVm {
  kind: "context";
  contextRef: string;
  contextVersion: string;
  companyLabel: string;
  expiresAt: string;
  defaults: { from: string; to: string } | null;
}

export interface ResultsVm extends MetaVm {
  kind: "results";
  items: InvoiceRowVm[];
  complete: boolean;
  hasMore: boolean | null;
  nextCursor: string | null;
  selectionRequired: boolean;
}

export interface EmptyVm extends MetaVm {
  kind: "empty";
}

export interface DocumentVm extends MetaVm {
  kind: "document";
  companyLabel: string;
  document: {
    invoice_type: "SALES";
    invoice_id: string;
    posting_date: string;
    docstatus: 0 | 1;
    record_version: string;
  };
}

export interface DeniedVm {
  kind: "denied";
  reason: string;
  message: string;
  cid: string | null;
}

export interface ExpiredVm {
  kind: "expired";
  reason: string;
  message: string;
  cid: string | null;
}

export interface UnavailableVm {
  kind: "unavailable";
  reason: string;
  message: string;
  cid: string | null;
}

export type InvoiceVm =
  | ContextVm
  | ResultsVm
  | EmptyVm
  | DocumentVm
  | DeniedVm
  | ExpiredVm
  | UnavailableVm;

export interface ParseOptions {
  capability: InvoiceCapability;
  requestId: string;
  httpStatus?: number;
  cidHeader?: unknown;
  /** Only isolated test/dev composition may set this. Production leaves it false. */
  allowDemoSource?: boolean;
  /** Expected active context for pinning context_version, company_label and source anchors */
  expectedContext?: ContextVm | null;
}

export const MESSAGES = {
  DENIED: "You do not have permission to view these invoices.",
  EXPIRED: "This search is no longer current. Start a new search to continue.",
  SOURCE_ERROR: "The invoice source could not be reached. Please try again.",
  TIMEOUT: "The request timed out. Please try again.",
  NOT_AVAILABLE: "Invoice lookup is not available right now.",
  DISABLED: "Invoice lookup is not enabled in this environment.",
  INVALID_RESPONSE: "The response could not be verified, so nothing is shown.",
  INVALID_REQUEST: "The search request was not accepted. Check the criteria and try again.",
} as const;

export interface SearchCriteriaInput {
  prefix?: string;
  postingFrom?: string;
  postingTo?: string;
  docstatus?: DocStatusFilter;
}

export interface SearchFilters {
  invoice_name_prefix?: string;
  posting_from?: string;
  posting_to?: string;
  docstatus?: DocStatusFilter;
}

export type CriteriaResult =
  | { ok: true; filters: SearchFilters }
  | { ok: false; questions: string[] };

export type IntentResult =
  | { kind: "search"; criteria: SearchCriteriaInput }
  | { kind: "clarify"; questions: string[] }
  | { kind: "unsupported" };
