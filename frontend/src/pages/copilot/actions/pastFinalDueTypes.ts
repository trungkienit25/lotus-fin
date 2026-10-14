/**
 * Frontend typed contracts and definitions for PastFinalDue Invoices (Phase 7).
 * Decoupled from ERPNext. Shared Copilot shell files are untouched.
 */

export interface PastFinalDueScanCoverage {
  complete: boolean;
  fetchedRows: number;
  scannedRows: number;
  returnedRows: number;
  missingRequiredData: boolean;
  truncated: boolean;
  reason?: string | null;
}

export interface PastFinalDueItemVm {
  invoiceId: string;
  finalDueDate: string;
  currentOutstandingDecimal: string;
  partyAccountCurrency: string;
  sourceModified: string;
  selectionRef: string | null;
  overdueDays: number;
  evidenceRef?: string | null;
}

export interface PastFinalDueResponseVm {
  capability: "PAST_FINAL_DUE_INVOICES";
  contractVersion: "p6.overdue.v1";
  observedAtUtc: string;
  siteLocalDate: string;
  siteTimezone: string;
  authorizedScope: string;
  providerMode: "CORE" | "DEMO" | "NATIVE";
  items: PastFinalDueItemVm[];
  coverage: PastFinalDueScanCoverage;
  limitations: string[];
  nextCursor?: string | null;
}

export interface PastFinalDueFilterState {
  currency?: string;
  invoicePrefix?: string;
  minOverdueDays?: number;
}
