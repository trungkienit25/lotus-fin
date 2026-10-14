import React from "react";
import type { EmptyVm, ResultsVm } from "./invoiceActionPresentation.ts";
import { safeText } from "./invoiceActionPresentation.ts";

export interface InvoiceSearchResultsProps {
  results: ResultsVm | EmptyVm;
  selectedId: string | null;
  busy: boolean;
  onOpen: (invoiceId: string) => void;
}

const STATUS_LABEL: Record<number, string> = { 0: "Draft", 1: "Submitted" };

/** Identity-only rows (no amounts). Even a single match requires an explicit click. */
export const InvoiceSearchResults: React.FC<InvoiceSearchResultsProps> = ({ results, selectedId, busy, onOpen }) => {
  if (results.kind === "empty") {
    return (
      <div data-testid="results-empty" className="text-sm text-gray-600 p-3 border rounded-lg bg-gray-50">
        No invoices matched these criteria in the checked range. This does not mean none exist outside it.
      </div>
    );
  }
  const selectable = results.complete;
  return (
    <div data-testid="results" className="space-y-2">
      {!selectable && (
        <div data-testid="results-partial" role="status" className="text-sm p-3 border border-amber-300 bg-amber-50 rounded-lg">
          Results are incomplete, so selection is disabled. Narrow your criteria and search again.
        </div>
      )}
      <ul className="divide-y border rounded-lg bg-white">
        {results.items.map((item) => (
          <li key={item.invoiceId} data-testid="result-row" data-invoice-id={safeText(item.invoiceId)}
            className="flex items-center justify-between gap-3 p-3 text-sm">
            <div>
              <div className="font-medium text-gray-900">{safeText(item.invoiceId)}</div>
              <div className="text-xs text-gray-500">
                {safeText(item.postingDate, 10)} · {STATUS_LABEL[item.docstatus]}
              </div>
            </div>
            {selectable && item.selectionRef !== null ? (
              <button type="button" data-testid="open-btn" disabled={busy}
                aria-pressed={selectedId === item.invoiceId}
                onClick={() => onOpen(item.invoiceId)}
                className="px-3 py-1 rounded border border-blue-600 text-blue-700 disabled:opacity-50">
                {selectedId === item.invoiceId ? "Selected" : "Open read-only"}
              </button>
            ) : (
              <span className="text-xs text-gray-400">Not selectable</span>
            )}
          </li>
        ))}
      </ul>
      <div className="text-xs text-gray-500" data-testid="results-meta">
        Showing {results.items.length} {results.items.length === 1 ? "invoice" : "invoices"} from this page only.
        {results.complete && results.hasMore ? " More results exist; refine your criteria to narrow them." : ""}
      </div>
    </div>
  );
};
