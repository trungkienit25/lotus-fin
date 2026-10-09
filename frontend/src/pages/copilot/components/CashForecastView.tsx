import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";

interface CashForecastViewProps {
  company: string;
  onNavigateTab?: (tab: string) => void;
}

export const CashForecastView: React.FC<CashForecastViewProps> = ({
  company,
  onNavigateTab,
}) => {
  const { t } = useTranslation();
  const [asOfDate, setAsOfDate] = useState<string>("2026-09-26");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const fetchForecast = async () => {
    if (!company) return;
    setLoading(true);
    try {
      const res = await axios.post("/api/method/lotus_fin.api.ai_insights.get_ai002_cash_forecast", {
        company,
        financial_as_of: asOfDate,
      });

      const payload = res.data?.message || res.data;
      if (payload) {
        setData(payload);
      }
    } catch (err: any) {
      console.warn("Could not fetch real cash forecast:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, [company, asOfDate]);

  const formatVND = (val: any) => {
    if (val === null || val === undefined || val === "" || isNaN(Number(val))) return "-- VND";
    return Math.round(Number(val)).toLocaleString("vi-VN") + " VND";
  };

  const aggregateAmount = data?.opening_cash?.aggregate_amount !== undefined
    ? Number(data.opening_cash.aggregate_amount)
    : (typeof data?.opening_cash === "number" ? data.opening_cash : null);

  const accountList = data?.opening_cash?.accounts || data?.account_breakdown || [];
  const obligationsList = data?.obligations || [];
  const forecastPoints = data?.forecast_points || data?.daily_points || [];

  return (
    <div className="space-y-6">
      {/* 1. Header Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                Lotus Fin • Cash Forecast & Runway (AI002)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
                Tầm nhìn: 30 Ngày (Daily EOD)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 font-mono">
                {company}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="cash_forecast" size="md" />
              <h1 className="text-2xl font-bold tracking-tight">Dự báo Dòng tiền & Quỹ đạo Thanh khoản</h1>
            </div>
            <p className="text-sm text-slate-300 mt-1">
              Trích xuất số dư Sổ cái GL và lịch đáo hạn công nợ hợp đồng thực tế từ ERPNext của {company}.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-white/10 px-3 py-1.5 rounded-xl border border-white/20">
              <span className="text-slate-300">Tính đến ngày:</span>
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
                className="bg-transparent text-white font-mono focus:outline-hidden"
              />
            </div>

            <button
              onClick={() => fetchForecast()}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold border border-white/20 transition-all flex items-center gap-1.5 cursor-pointer backdrop-blur"
            >
              <svg className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{loading ? "Đang dự báo..." : "Cập nhật từ ERP"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Tier 1: Opening Cash & Bank Balances Verification */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ModuleBadge moduleId="financial_health" size="xs" />
              <span>Tier 1: Số dư Tiền mặt & Ngân hàng Đầu kỳ (Thực tế Sổ cái GL)</span>
            </h2>
            <p className="text-xs text-slate-500">Đối soát độc lập giữa Sổ cái General Ledger và Bảng cân đối thử</p>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            ✓ {data?.opening_cash?.reconciliation || "GL Reconciled"}
          </span>
        </div>

        {/* Total Aggregate Balance Box */}
        <div className={`p-5 rounded-2xl border mb-4 ${
          aggregateAmount !== null && aggregateAmount < 0
            ? "bg-rose-50/60 border-rose-200"
            : "bg-gradient-to-br from-slate-50 to-slate-100/80 border-slate-200/80"
        }`}>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Tổng số dư tiền khả dụng hợp nhất đầu kỳ
          </div>
          <div className={`text-3xl font-extrabold mt-1 tracking-tight font-mono ${
            aggregateAmount !== null && aggregateAmount < 0 ? "text-rose-700" : "text-slate-900"
          }`}>
            {formatVND(aggregateAmount)}
          </div>
        </div>

        {/* Account Breakdown Chips */}
        <div>
          <div className="text-xs font-semibold text-slate-600 mb-2">Chi tiết từng tài khoản tiền/ngân hàng thực tế:</div>
          <div className="flex flex-wrap gap-2.5">
            {accountList.length > 0 ? (
              accountList.map((acc: any, idx: number) => {
                const bal = acc.amount !== undefined ? Number(acc.amount) : Number(acc.balance);
                const isDeficit = acc.deficit || bal < 0;
                return (
                  <div
                    key={idx}
                    className={`px-3.5 py-2 rounded-xl border shadow-2xs flex items-center gap-3 text-xs ${
                      isDeficit ? "bg-rose-50/80 border-rose-200" : "bg-white border-slate-200"
                    }`}
                  >
                    <span className="text-slate-700 font-medium">{acc.account}</span>
                    <span className={`font-bold font-mono ${isDeficit ? "text-rose-600" : "text-blue-600"}`}>
                      {formatVND(bal)}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-xs text-slate-400">Không tìm thấy tài khoản tiền mặt/ngân hàng tương ứng.</div>
            )}
          </div>
        </div>
      </div>

      {/* 3. 30-Day Cash Trajectory Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>📈</span> Quỹ đạo Số dư Tiền mặt 30 Ngày (Daily EOD Trajectory)
            </h2>
            <p className="text-xs text-slate-500">Số dư cuối ngày được dự báo dựa trên các sự kiện kế toán đã hạch toán</p>
          </div>
          <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
            {forecastPoints.length > 0 ? `${forecastPoints.length} Mốc Dự báo` : "Deterministic Baseline"}
          </span>
        </div>

        <div className="overflow-x-auto max-h-[380px] border border-slate-100 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-slate-600 z-10 font-semibold">
              <tr>
                <th className="py-2.5 px-3">Ngày</th>
                <th className="py-2.5 px-3">Số dư Cuối ngày (EOD Cash)</th>
                <th className="py-2.5 px-3">Sự kiện / Giao dịch chính</th>
                <th className="py-2.5 px-3 text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {forecastPoints.length > 0 ? (
                forecastPoints.map((pt: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-800">{pt.date}</td>
                    <td className="py-2.5 px-3 font-bold font-mono text-slate-900">{formatVND(pt.eod_balance || pt.amount)}</td>
                    <td className="py-2.5 px-3 text-slate-600">{pt.event_desc || "Duy trì số dư định kỳ"}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          pt.status === "HEALTHY"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : pt.status === "WARNING"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-rose-50 text-rose-700 border border-rose-200"
                        }`}
                      >
                        {pt.status === "HEALTHY" ? "An toàn" : pt.status === "WARNING" ? "Cảnh báo" : "Thiếu hụt"}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    <div>
                      {data?.reason_code === "NO_CONFIRMED_SETTLEMENT_EVENTS"
                        ? "Không có sự kiện thanh toán tiền mặt được xác nhận trong 30 ngày tới (NO_CONFIRMED_SETTLEMENT_EVENTS)."
                        : "Chưa có bút toán thanh toán tương lai được phê duyệt."}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      Các hóa đơn mua/bán hàng bên dưới phản ánh nghĩa vụ theo ngày đáo hạn hợp đồng.
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Tier 2: Contractual Obligations (AR / AP Due Dates) */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>📑</span> Tier 2: Nghĩa vụ Hợp đồng Thực tế (Lịch đáo hạn AR / AP từ ERP)
            </h2>
            <p className="text-xs text-slate-500">Các hóa đơn Bán hàng (Sales Invoices) & Mua hàng (Purchase Invoices) đã hạch toán</p>
          </div>
          <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full">
            {obligationsList.length} Chứng từ
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-100 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3 text-center">Loại</th>
                <th className="py-2.5 px-3">Đối tác / Mã băm</th>
                <th className="py-2.5 px-3">Ngày đến hạn</th>
                <th className="py-2.5 px-3">Số tiền còn lại</th>
                <th className="py-2.5 px-3">Chứng từ gốc</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {obligationsList.length > 0 ? (
                obligationsList.map((ob: any, idx: number) => {
                  const amt = ob.remaining_amount !== undefined ? Number(ob.remaining_amount) : Number(ob.amount);
                  const isAR = ob.type === "AR";
                  return (
                    <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            isAR
                              ? "bg-blue-50 text-blue-700 border border-blue-200"
                              : "bg-purple-50 text-purple-700 border border-purple-200"
                          }`}
                        >
                          {isAR ? "Thu (AR)" : "Chi (AP)"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-800">
                        {ob.party || ob.party_hash || ob.party_type || "Đối tác"}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-600">{ob.due_date}</td>
                      <td className={`py-2.5 px-3 font-mono font-bold ${isAR ? "text-emerald-600" : "text-rose-600"}`}>
                        {isAR ? "+" : "-"}{formatVND(amt)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-500">
                        {ob.source_ref || ob.voucher_no || "--"}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400">
                    Không có khoản công nợ AR/AP chưa thanh toán.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Limitations & Assumptions Banner */}
      {data?.limitations && data.limitations.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
          <div className="font-bold text-slate-800 flex items-center gap-1.5">
            <span>⚠️</span> Giới hạn & Giả định Phương pháp Kế toán (AI-F002):
          </div>
          <ul className="list-disc list-inside space-y-1 text-slate-600">
            {data.limitations.map((lim: string, i: number) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CashForecastView;
