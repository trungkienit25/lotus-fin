import React from "react";
import type { DocumentVm } from "./invoiceActionPresentation.ts";
import { safeText } from "./invoiceActionPresentation.ts";

const STATUS_LABEL: Record<number, string> = { 0: "Draft", 1: "Submitted" };

/** Fixed read-only Lotus viewer (sales-invoice-minimal-v1): five contract fields + server company label. */
export const InvoiceReadView: React.FC<{ doc: DocumentVm }> = ({ doc }) => {
  const d = doc.document;
  return (
    <section data-testid="read-view" aria-label="Sales invoice (read-only)" className="border rounded-lg bg-white p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Sales invoice</h3>
        <span data-testid="readonly-badge" className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">Read-only</span>
      </header>
      {doc.sourceMode === "DEMO_ISOLATED" && (
        <div data-testid="demo-banner" role="note" className="text-xs p-2 rounded bg-purple-50 border border-purple-300 text-purple-800">
          Demo data from an isolated test source. Not an ERP record.
        </div>
      )}
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="text-gray-500">Invoice</dt><dd data-testid="f-invoice-id">{safeText(d.invoice_id)}</dd>
        <dt className="text-gray-500">Type</dt><dd data-testid="f-type">Sales</dd>
        <dt className="text-gray-500">Company</dt><dd data-testid="f-company">{safeText(doc.companyLabel)}</dd>
        <dt className="text-gray-500">Posting date</dt><dd data-testid="f-date">{safeText(d.posting_date, 10)}</dd>
        <dt className="text-gray-500">Status</dt><dd data-testid="f-status">{STATUS_LABEL[d.docstatus]}</dd>
        <dt className="text-gray-500">Version</dt><dd data-testid="f-version">{safeText(d.record_version, 64)}</dd>
      </dl>
      <footer className="text-xs text-gray-500 border-t pt-2" data-testid="trace">
        Request ID <span data-testid="trace-rid">{doc.requestId}</span> · Correlation ID{" "}
        <span data-testid="trace-cid">{doc.cid}</span> · Observed {safeText(doc.observedAt, 64)}
      </footer>
    </section>
  );
};
