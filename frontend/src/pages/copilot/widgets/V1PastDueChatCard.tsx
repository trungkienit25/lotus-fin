import React from "react";
import type { PastFinalDueItemVm } from "../actions/pastFinalDueTypes";

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
    <div className="w-full rounded-2xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3.5 my-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="size-7 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-xs shadow-2xs">
            ⏳
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
              Hóa đơn đã qua hạn cuối còn dư nợ (V1 Past Final Due)
            </h4>
            <div className="text-[11px] text-slate-400">
              Công ty: <span className="font-semibold text-slate-700">{company}</span> · Mốc chốt: 13/10/2026
            </div>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60">
          DỮ LIỆU DEMO CỐ ĐỊNH
        </span>
      </div>

      {/* Table of overdue invoices */}
      <div className="overflow-x-auto rounded-xl border border-slate-200/80">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-bold text-slate-500">
              <th className="py-2.5 px-3">Mã hóa đơn</th>
              <th className="py-2.5 px-3">Hạn cuối</th>
              <th className="py-2.5 px-3">Quá hạn</th>
              <th className="py-2.5 px-3 text-right">Dư nợ còn lại</th>
              <th className="py-2.5 px-3 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {DEMO_OVERDUE_ITEMS.map((item) => (
              <tr key={item.invoiceId} className="hover:bg-slate-50/60 transition-colors">
                <td className="py-2 px-3 font-mono font-bold text-slate-900">{item.invoiceId}</td>
                <td className="py-2 px-3 text-slate-600">{item.finalDueDate}</td>
                <td className="py-2 px-3">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      item.overdueDays > 60
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-amber-50 text-amber-800 border border-amber-200"
                    }`}
                  >
                    +{item.overdueDays} ngày
                  </span>
                </td>
                <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                  {item.currentOutstandingDecimal} <span className="text-[10px] text-slate-400 font-normal">{item.partyAccountCurrency}</span>
                </td>
                <td className="py-2 px-3 text-center">
                  <button
                    onClick={() => onSelectInvoice?.(item.invoiceId)}
                    className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                  >
                    Chuẩn bị việc
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-[10px] text-slate-400 border-t border-slate-100 pt-2 flex items-center justify-between">
        <span>Ghi nhận 3 hóa đơn quá hạn thỏa mãn tiêu chí</span>
        <span>Mô phỏng độc lập</span>
      </div>
    </div>
  );
};
