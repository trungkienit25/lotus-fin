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
      <div data-testid="results-empty" className="text-xs text-slate-600 p-4 border border-slate-200/80 rounded-xl bg-[#F9FBFC] text-center font-sans">
        No sales invoices matched the search criteria within the verified scope.
      </div>
    );
  }
  const selectable = results.complete;
  return (
    <div data-testid="results" className="space-y-3 font-sans">
      {!selectable && (
        <div data-testid="results-partial" role="status" className="text-xs p-3.5 border border-amber-200 bg-amber-50 rounded-xl text-amber-900 flex items-center gap-2">
          <span>⚠️</span>
          <span>Partial results returned due to query boundary limits. Selection is temporarily locked; please narrow criteria and retry.</span>
        </div>
      )}
      <ul className="divide-y divide-slate-100 border border-slate-200/80 rounded-2xl bg-white overflow-hidden shadow-2xs">
        {results.items.map((item) => {
          const isSelected = selectedId === item.invoiceId;
          const isSubmitted = item.docstatus === 1;
          return (
            <li
              key={item.invoiceId}
              data-testid="result-row"
              data-invoice-id={safeText(item.invoiceId)}
              className={`flex items-center justify-between gap-3 p-3.5 text-xs transition-colors ${
                isSelected ? "bg-blue-50/50" : "hover:bg-slate-50/70"
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="size-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 text-xs shrink-0 font-mono">
                  🧾
                </div>
                <div className="min-w-0">
                  <div className="font-mono font-bold text-slate-900 tracking-tight">
                    {safeText(item.invoiceId)}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                    <span>Date: {safeText(item.postingDate, 10)}</span>
                    <span>•</span>
                    <span className={`font-semibold ${isSubmitted ? "text-emerald-700" : "text-amber-700"}`}>
                      {STATUS_LABEL[item.docstatus]}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                {selectable && item.selectionRef !== null ? (
                  <button
                    type="button"
                    data-testid="open-btn"
                    disabled={busy}
                    aria-pressed={isSelected}
                    onClick={() => onOpen(item.invoiceId)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-2xs flex items-center gap-1 ${
                      isSelected
                        ? "bg-blue-600 text-white hover:bg-blue-700"
                        : "border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300"
                    } disabled:opacity-50`}
                  >
                    <span>{isSelected ? "Đang chọn" : "Mở xem"}</span>
                    <span>↗</span>
                  </button>
                ) : (
                  <span className="text-[11px] text-slate-400 font-medium">Không thể chọn</span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <div className="text-[11px] text-slate-400 flex items-center justify-between px-1" data-testid="results-meta">
        <span>Hiển thị {results.items.length} {results.items.length === 1 ? "hóa đơn" : "hóa đơn"} trong trang này.</span>
        {results.complete && results.hasMore && (
          <span className="text-blue-600">Còn kết quả khác; hãy lọc chi tiết hơn để thu hẹp.</span>
        )}
      </div>
    </div>
  );
};

