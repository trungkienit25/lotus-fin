import React from "react";
import { PastFinalDueResponseVm, PastFinalDueItemVm } from "./pastFinalDueTypes";

interface PastFinalDueViewProps {
  data: PastFinalDueResponseVm;
  onSelectInvoice?: (item: PastFinalDueItemVm) => void;
  onRefresh?: () => void;
}

export const PastFinalDueView: React.FC<PastFinalDueViewProps> = ({
  data,
  onSelectInvoice,
  onRefresh,
}) => {
  const isDemo = data.providerMode === "DEMO";
  const isCore = data.providerMode === "CORE";
  const isPartial = !data.coverage.complete;

  return (
    <div className="w-full space-y-4 font-sans text-slate-800" data-testid="past-final-due-container">
      {/* Header and Isolation Badges */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-white border border-slate-200/80 shadow-2xs">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Hóa đơn đã qua hạn cuối còn dư nợ (Past-Final-Due)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Ngày hạch toán hệ thống: <span className="font-mono font-medium text-slate-700">{data.siteLocalDate}</span> ({data.siteTimezone}) · Phạm vi: <span className="font-medium text-slate-700">{data.authorizedScope}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isDemo && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Dữ liệu kiểm thử
            </span>
          )}
          {isCore && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              ⚡ ERP Live
            </span>
          )}
          {isPartial && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
              Phạm vi một phần
            </span>
          )}
        </div>
      </div>

      {/* Limitations Warning */}
      {data.limitations && data.limitations.length > 0 && (
        <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200/80 text-amber-900 text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>{data.limitations.join(", ")}</span>
        </div>
      )}

      {/* Invoice Table */}
      {data.items.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-200 rounded-2xl bg-white">
          {isCore ? "Hiện tại chưa có hóa đơn quá hạn nào cần xử lý trong phạm vi đã chọn." : "Không tìm thấy hóa đơn quá hạn thỏa mãn điều kiện."}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-2xs">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] border-b border-slate-200/80 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-3 px-4">Mã Hóa đơn</th>
                <th className="py-3 px-4">Hạn chót thanh toán</th>
                <th className="py-3 px-4">Số ngày quá hạn</th>
                <th className="py-3 px-4 text-right">Dư nợ hiện tại</th>
                <th className="py-3 px-4">Đơn vị tiền tệ</th>
                <th className="py-3 px-4 text-center">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((item) => (
                <tr key={item.invoiceId} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{item.invoiceId}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{item.finalDueDate}</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      +{item.overdueDays} ngày
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                    {item.currentOutstandingDecimal}
                  </td>
                  <td className="py-3 px-4 text-slate-600 font-medium">{item.partyAccountCurrency}</td>
                  <td className="py-3 px-4 text-center">
                    <button
                      disabled={!item.selectionRef}
                      onClick={() => onSelectInvoice && onSelectInvoice(item)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-2xs ${
                        item.selectionRef
                          ? "bg-blue-600 text-white hover:bg-blue-700"
                          : "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                      }`}
                    >
                      {item.selectionRef ? "Xem chi tiết ↗" : "Chưa xác thực"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer & Freshness */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-400 px-1">
        <span>
          Đã quét: <strong className="text-slate-600">{data.coverage.scannedRows}</strong> · Trả về: <strong className="text-slate-600">{data.coverage.returnedRows}</strong> · Thời điểm đối soát: <span className="font-mono">{data.observedAtUtc}</span>
        </span>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-blue-600 hover:text-blue-700 font-semibold cursor-pointer self-start sm:self-auto"
          >
            Làm mới dữ liệu ↻
          </button>
        )}
      </div>
    </div>
  );
};
