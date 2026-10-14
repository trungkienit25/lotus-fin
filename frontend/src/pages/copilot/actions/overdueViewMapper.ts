import type { PastFinalDueResponseVm } from "./pastFinalDueTypes.ts";

export function mapOverdueView(d: any): PastFinalDueResponseVm {
  if (!d || d.capability !== "PAST_FINAL_DUE_INVOICES" || d.contract_version !== "p6.overdue.v1" ||
      d.provider_mode !== "DEMO" || !Array.isArray(d.items) || !d.coverage) throw new Error("Invalid overdue contract");
  return { capability: d.capability, contractVersion: d.contract_version, observedAtUtc: d.observed_at_utc,
    siteLocalDate: d.site_local_date, siteTimezone: d.site_timezone, authorizedScope: d.authorized_scope,
    providerMode: d.provider_mode, limitations: d.limitations, nextCursor: d.next_cursor,
    items: d.items.map((i: any) => ({ invoiceId: i.invoice_id, finalDueDate: i.final_due_date,
      currentOutstandingDecimal: i.current_outstanding_decimal, partyAccountCurrency: i.party_account_currency,
      sourceModified: i.source_modified, selectionRef: null, overdueDays: i.overdue_days, evidenceRef: i.evidence_ref })),
    coverage: { complete: d.coverage.complete, fetchedRows: d.coverage.fetched_rows, scannedRows: d.coverage.scanned_rows,
      returnedRows: d.coverage.returned_rows, missingRequiredData: d.coverage.missing_required_data,
      truncated: d.coverage.truncated, reason: d.coverage.reason } };
}
