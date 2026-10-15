import React from "react";
import type { PastFinalDueItemVm } from "../actions/pastFinalDueTypes";
import { ModuleBadge } from "../components/ModuleBadge";

export interface V1PastDueChatCardProps {
  company?: string;
  onSelectInvoice?: (invId: string) => void;
}

const DEMO_OVERDUE_ITEMS: PastFinalDueItemVm[] = [
  {
    invoiceId: "SINV-2026-00088",
    finalDueDate: "2026-09-14",
    overdueDays: 32,
    currentOutstandingDecimal: "87,000",
    partyAccountCurrency: "VND",
    sourceModified: "2026-09-20",
    selectionRef: "ref-sinv-88",
  },
  {
    invoiceId: "SINV-2026-00045",
    finalDueDate: "2026-08-19",
    overdueDays: 58,
    currentOutstandingDecimal: "125,000",
    partyAccountCurrency: "VND",
    sourceModified: "2026-08-25",
    selectionRef: "ref-sinv-45",
  },
  {
    invoiceId: "SINV-2026-00031",
    finalDueDate: "2026-07-10",
    overdueDays: 98,
    currentOutstandingDecimal: "104,000",
    partyAccountCurrency: "VND",
    sourceModified: "2026-07-15",
    selectionRef: "ref-sinv-31",
  },
];

export const V1PastDueChatCard: React.FC<V1PastDueChatCardProps> = ({
  company = "Lotus-fin (Demo)",
  onSelectInvoice,
}) => {
  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-amber-950 via-rose-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="risk_signals" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Hóa đơn Quá hạn Cuối còn Dư nợ (Past-Final-Due)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                V1 Audit
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Phát hiện nợ quá hạn chót theo nguyên tắc thận trọng kế toán
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-amber-200 border border-white/20 backdrop-blur font-mono self-start sm:self-auto">
          Mốc chốt: 13/10/2026
        </span>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Overdue Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-200/80">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] border-b border-slate-200/80 text-[11px] font-bold text-slate-600">
                <th className="py-3 px-3.5">Mã Hóa đơn</th>
                <th className="py-3 px-3.5">Hạn chót thanh toán</th>
                <th className="py-3 px-3.5">Số ngày quá hạn</th>
                <th className="py-3 px-3.5 text-right">Dư nợ còn lại</th>
                <th className="py-3 px-3.5 text-center">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {DEMO_OVERDUE_ITEMS.map((item) => (
                <tr key={item.invoiceId} className="hover:bg-[#F9FBFC] transition-colors">
                  <td className="py-2.5 px-3.5 font-mono font-bold text-slate-900">{item.invoiceId}</td>
                  <td className="py-2.5 px-3.5 text-slate-600 font-mono">{item.finalDueDate}</td>
                  <td className="py-2.5 px-3.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        item.overdueDays > 60
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-amber-50 text-amber-800 border border-amber-200"
                      }`}
                    >
                      +{item.overdueDays} ngày
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
                      Tạo việc ↗
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Audit info */}
        <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
          <span>Ghi nhận 3 hóa đơn quá hạn thỏa mãn tiêu chí</span>
          <span className="font-mono text-slate-400">V1 Independent Evaluator</span>
        </div>
      </div>
    </div>
  );
};
