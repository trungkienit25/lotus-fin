import React, { useEffect, useState } from "react";
import type { PastFinalDueItemVm } from "../actions/pastFinalDueTypes";
import { ModuleBadge } from "../components/ModuleBadge";
import { bootstrapSession } from "../../../providers/sessionBootstrap";

export interface V1PastDueChatCardProps {
  company?: string;
  onSelectInvoice?: (invId: string) => void;
}

export const V1PastDueChatCard: React.FC<V1PastDueChatCardProps> = ({
  company = "Lotus-fin (Demo)",
  onSelectInvoice,
}) => {
  const [items, setItems] = useState<PastFinalDueItemVm[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [sourceLabel, setSourceLabel] = useState<string>("Connecting to ERP...");
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchOverdue() {
      try {
        setFetchError(null);
        const session = await bootstrapSession().catch(() => null);
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (session?.csrfToken) {
          headers["X-Frappe-CSRF-Token"] = session.csrfToken;
        }

        const res = await fetch("/api/method/lotus_fin.api.copilot_api.get_real_overdue_invoices", {
          method: "POST",
          headers,
          credentials: "same-origin",
          body: JSON.stringify({ company }),
        });

        if (res.ok) {
          const wire = await res.json();
          const data = wire.message;
          if (data && data.items && isMounted) {
            setItems(data.items);
            setSourceLabel(data.source || "ERPNext Live Database");
            setLoading(false);
            return;
          }
        }
        throw new Error("Unable to retrieve overdue invoice records from ERP server.");
      } catch (err: any) {
        console.warn("Failed to fetch real overdue invoices:", err);
        if (isMounted) {
          setItems([]);
          setFetchError("AI service / ERP database encountered a connection error. Could not retrieve overdue invoices.");
          setSourceLabel("Connection Disrupted");
          setLoading(false);
        }
      }
    }

    fetchOverdue();
    return () => { isMounted = false; };
  }, [company]);
  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-amber-950 via-rose-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="risk_signals" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Past Final Due Invoices Requiring Follow-Up
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                Receivables Audit
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Identified overdue debts per accounting prudence principles
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-amber-200 border border-white/20 backdrop-blur font-mono self-start sm:self-auto">
          As of: 2026-10-13
        </span>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Overdue Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-200/80">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] border-b border-slate-200/80 text-[11px] font-bold text-slate-600">
                <th className="py-3 px-3.5">Invoice ID</th>
                <th className="py-3 px-3.5">Due Date</th>
                <th className="py-3 px-3.5">Days Overdue</th>
                <th className="py-3 px-3.5 text-right">Outstanding Balance</th>
                <th className="py-3 px-3.5 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400 font-sans">
                    <span className="inline-block animate-pulse">Loading verified invoice data from ERPNext...</span>
                  </td>
                </tr>
              ) : fetchError ? (
                <tr>
                  <td colSpan={5} className="py-6 px-4 text-center text-rose-700 bg-rose-50/50 text-xs font-sans">
                    ⚠️ {fetchError}
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400 font-sans">
                    No overdue invoices found at this time.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.invoiceId} className="hover:bg-[#F9FBFC] transition-colors">
                    <td className="py-2.5 px-3.5 font-mono font-bold text-slate-900">
                      <div>{item.invoiceId}</div>
                      {item.customerName && <div className="text-[10px] font-sans text-slate-500 font-normal">{item.customerName}</div>}
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-600 font-mono">{item.finalDueDate}</td>
                    <td className="py-2.5 px-3.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          item.overdueDays > 60
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-amber-50 text-amber-800 border border-amber-200"
                        }`}
                      >
                        +{item.overdueDays} days
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-right font-mono font-bold text-slate-900">
                      {item.currentOutstandingDecimal} <span className="text-[10px] text-slate-400 font-normal">{item.partyAccountCurrency}</span>
                    </td>
                    <td className="py-2.5 px-3.5 text-center">
                      <button
                        onClick={() => onSelectInvoice?.(item.invoiceId)}
                        className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:border-[#1E63B7] text-[#1E63B7] text-xs font-bold shadow-2xs transition-all cursor-pointer hover:bg-blue-50/50"
                      >
                        Create Task ↗
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Audit info */}
        <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
          <span>Found {items.length} overdue invoices</span>
          <span className="font-mono text-slate-500 font-medium">{sourceLabel}</span>
        </div>
      </div>
    </div>
  );
};
