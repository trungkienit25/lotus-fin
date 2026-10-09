import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";

interface FinancialHealthViewProps {
  company: string;
  onNavigateTab?: (tab: string) => void;
}

export const FinancialHealthView: React.FC<FinancialHealthViewProps> = ({
  company,
  onNavigateTab,
}) => {
  const { t } = useTranslation();
  const [periodPreset, setPeriodPreset] = useState<string>("CURRENT_YEAR");
  const [comparisonMode, setComparisonMode] = useState<string>("NONE");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  // What-If Simulation preview state inside Health view
  const [simSales, setSimSales] = useState<number>(-15);
  const [simDelay, setSimDelay] = useState<number>(15);
  const [simSupplier, setSimSupplier] = useState<number>(0);
  const [simFinancing, setSimFinancing] = useState<number>(300000000);
  const [simResult, setSimResult] = useState<any>(null);
  const [simLoading, setSimLoading] = useState(false);

  const fetchHealthData = async () => {
    if (!company) return;
    setLoading(true);
    try {
      const curYear = "2026";
      const pStart = periodPreset === "FY2020" ? "2020-01-01" : periodPreset === "FY2025" ? "2025-01-01" : `${curYear}-01-01`;
      const pEnd = periodPreset === "FY2020" ? "2020-12-31" : periodPreset === "FY2025" ? "2025-12-31" : `${curYear}-12-31`;

      const res = await axios.post("/api/method/lotus_fin.api.ai_insights.get_financial_snapshot", {
        company,
        period_start: pStart,
        period_end: pEnd,
        currency: "VND",
        comparison: comparisonMode === "NONE" ? null : "PREVIOUS_PERIOD",
        include_explanation: 1,
      });

      const payload = res.data?.message || res.data;
      if (payload && (payload.metrics || payload.status)) {
        setData(payload);
      }
    } catch (err: any) {
      console.warn("Could not fetch real snapshot, verifying response:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
  }, [company, periodPreset, comparisonMode]);

  const runQuickSimulation = async () => {
    setSimLoading(true);
    try {
      const res = await axios.post("/api/method/lotus_fin.modules.f005_financing.service.simulate_what_if", {
        company,
        sales_change_pct: simSales / 100,
        collection_delay_days: simDelay,
        supplier_due_shift_days: simSupplier,
        financing_amount: simFinancing,
        financing_term_months: 12,
        financing_rate_annual: 0.095,
      });
      const resMsg = res.data?.message || res.data;
      if (resMsg?.kpis_9_layer) {
        setSimResult(resMsg);
      }
    } catch (e) {
      console.warn("Simulation call error:", e);
    } finally {
      setSimLoading(false);
    }
  };

  const formatVND = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(val)) return "-- VND";
    return Math.round(Number(val)).toLocaleString("vi-VN") + " VND";
  };

  const metricMap: Record<string, any> = {};
  if (data?.metrics && Array.isArray(data.metrics)) {
    data.metrics.forEach((m: any) => {
      metricMap[m.metric_id] = m;
    });
  }

  const approvedMetrics = [
    { id: "revenue", label: "Doanh thu (Revenue)", isCurrency: true },
    { id: "cogs", label: "Giá vốn (COGS)", isCurrency: true },
    { id: "gross_margin", label: "Biên lợi nhuận gộp", isRatio: true },
    { id: "cash_balance", label: "Số dư tiền mặt", isCurrency: true },
    { id: "ar_outstanding", label: "Công nợ phải thu (AR)", isCurrency: true },
    { id: "overdue_ar_ratio", label: "Tỷ lệ nợ quá hạn", isRatio: true },
    { id: "ap_outstanding", label: "Công nợ phải trả (AP)", isCurrency: true },
    { id: "near_term_ap", label: "AP ngắn hạn đáo hạn", isCurrency: true },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                Lotus Fin • AI-F001
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                Chế độ Dữ liệu: {data?.data_mode || "Actual ERP"}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 font-mono">
                {company}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="financial_health" size="md" />
              <h1 className="text-2xl font-bold tracking-tight">Báo cáo Sức khỏe Tài chính Doanh nghiệp</h1>
            </div>
            <p className="text-sm text-slate-300 mt-1">
              Trích xuất trực tiếp từ Sổ cái General Ledger, Bảng cân đối thử và Báo cáo Kết quả Kinh doanh thực tế của {company}.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => fetchHealthData()}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-medium border border-white/20 transition-all flex items-center gap-1.5 backdrop-blur cursor-pointer"
            >
              <svg className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{loading ? "Đang truy vấn sổ cái..." : "Cập nhật từ ERP"}</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-5 pt-4 border-t border-white/10 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">Kỳ kế toán:</span>
            <select
              value={periodPreset}
              onChange={(e) => setPeriodPreset(e.target.value)}
              className="bg-white/10 border border-white/20 text-white rounded-lg px-2.5 py-1 text-xs focus:outline-hidden focus:ring-1 focus:ring-blue-400"
            >
              <option value="CURRENT_YEAR" className="text-slate-800">Năm hiện tại (2026 - Actual)</option>
              <option value="FY2025" className="text-slate-800">Năm tài chính 2025</option>
              <option value="FY2020" className="text-slate-800">Năm tài chính 2020</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">So sánh:</span>
            <select
              value={comparisonMode}
              onChange={(e) => setComparisonMode(e.target.value)}
              className="bg-white/10 border border-white/20 text-white rounded-lg px-2.5 py-1 text-xs focus:outline-hidden focus:ring-1 focus:ring-blue-400"
            >
              <option value="NONE" className="text-slate-800">Không so sánh</option>
              <option value="PREVIOUS_PERIOD" className="text-slate-800">Kỳ liền trước (Previous Period)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 2. Key Financial Metrics (8-KPI Grid) */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">1. Chỉ số Tài chính Thực tế (8 Cột mốc Kế toán)</h2>
            <p className="text-xs text-slate-500">Đối soát độc lập trực tiếp từ Sổ cái General Ledger và P&L của {company}</p>
          </div>
          <span className="text-xs font-mono text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full font-semibold">
            ✓ Trích xuất từ Sổ cái ERP
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {approvedMetrics.map((meta) => {
            const m = metricMap[meta.id];
            let displayVal = "--";
            let isNegative = false;
            let statusBadge = "Chưa có dữ liệu";

            if (m && m.status === "AVAILABLE" && m.value !== null && m.value !== undefined) {
              statusBadge = "Đã đối soát";
              if (meta.isRatio) {
                displayVal = `${(m.value * 100).toFixed(2)}%`;
              } else {
                displayVal = formatVND(m.value);
                if (m.value < 0) isNegative = true;
              }
            } else if (m && m.limitations && m.limitations.length > 0) {
              displayVal = "N/A";
              statusBadge = m.limitations[0];
            }

            return (
              <div
                key={meta.id}
                className={`p-4 rounded-xl border transition-all ${
                  isNegative
                    ? "bg-rose-50/50 border-rose-200"
                    : "bg-[#F9FBFC] border-slate-100 hover:border-blue-200"
                }`}
              >
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                  <span className="font-medium text-slate-700">{meta.label}</span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      m?.status === "AVAILABLE" ? (isNegative ? "bg-rose-500" : "bg-emerald-500") : "bg-slate-300"
                    }`}
                  ></span>
                </div>
                <div
                  className={`text-lg font-bold tracking-tight mt-1 font-mono ${
                    isNegative ? "text-rose-700" : "text-slate-900"
                  }`}
                >
                  {displayVal}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 truncate" title={statusBadge}>
                  {statusBadge}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Period Comparison Table */}
      {data?.comparison && data.comparison.status === "AVAILABLE" && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">2. So sánh Biến động Kỳ Kế toán</h2>
              <p className="text-xs text-slate-500">
                Đối chiếu với kỳ trước ({data.comparison.previous_period?.start} đến {data.comparison.previous_period?.end})
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                  <th className="py-2.5 px-3">Chỉ số</th>
                  <th className="py-2.5 px-3">Kỳ hiện tại</th>
                  <th className="py-2.5 px-3">Kỳ trước</th>
                  <th className="py-2.5 px-3">Biến động (Số tuyệt đối)</th>
                  <th className="py-2.5 px-3">Tăng/Giảm (%)</th>
                  <th className="py-2.5 px-3">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Object.entries(data.comparison.metrics || {}).map(([key, item]: [string, any]) => {
                  const meta = approvedMetrics.find((m) => m.id === key);
                  if (!meta) return null;
                  const isRatio = meta.isRatio;
                  const isPositive = (item.absolute_change || 0) >= 0;

                  return (
                    <tr key={key} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{meta.label}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-700">
                        {isRatio ? `${(item.current * 100).toFixed(1)}%` : formatVND(item.current)}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {isRatio ? `${(item.previous * 100).toFixed(1)}%` : formatVND(item.previous)}
                      </td>
                      <td className={`py-2.5 px-3 font-semibold ${isPositive ? "text-emerald-600" : "text-rose-600"}`}>
                        {isPositive ? "+" : ""}
                        {isRatio ? `${(item.absolute_change * 100).toFixed(1)} pp` : formatVND(item.absolute_change)}
                      </td>
                      <td className={`py-2.5 px-3 font-semibold ${isPositive ? "text-emerald-600" : "text-rose-600"}`}>
                        {isPositive ? "▲ +" : "▼ "}
                        {(item.relative_change * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Grounded AI Financial Analysis Narrative from Real Ledger */}
      {data?.explanation && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">🤖</span>
            <div>
              <h2 className="text-base font-bold text-slate-900">3. Diễn giải & Khuyến nghị Kế toán Thực tế</h2>
              <p className="text-xs text-slate-500">Diễn giải có căn cứ trực tiếp từ các sự kiện đã hạch toán</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100">
              <div className="font-semibold text-blue-900 text-xs mb-2 flex items-center gap-1.5">
                <span>📊</span> Sự thật Sổ cái (Verified Facts)
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                {data.explanation.facts && data.explanation.facts.length > 0 ? (
                  data.explanation.facts.map((f: string, i: number) => (
                    <li key={i}>{formatBrandText(f)}</li>
                  ))
                ) : (
                  <li>Chưa có số liệu phát sinh trong kỳ được chọn.</li>
                )}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-100">
              <div className="font-semibold text-emerald-900 text-xs mb-2 flex items-center gap-1.5">
                <span>💡</span> Phân tích Hành động Tiếp theo (Actionable Checks)
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700 list-disc list-inside">
                {data.explanation.next_checks && data.explanation.next_checks.length > 0 ? (
                  data.explanation.next_checks.map((nc: string, i: number) => (
                    <li key={i}>{formatBrandText(nc)}</li>
                  ))
                ) : (
                  <li>Kiểm tra chi tiết sổ phụ ngân hàng và công nợ quá hạn.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 5. What-If Quick Simulation Stress Test Preview */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">🔮</span>
            <div>
              <h2 className="text-base font-bold text-slate-900">4. Thử nghiệm Nhanh Kịch bản Nhạy cảm (What-If 9-KPIs)</h2>
              <p className="text-xs text-slate-500">Mô phỏng tác động tức thời đến dòng tiền và an toàn thanh khoản</p>
            </div>
          </div>
          {onNavigateTab && (
            <button
              onClick={() => onNavigateTab("what_if")}
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 cursor-pointer"
            >
              Mở Studio Chuyên sâu ➔
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div>
            <label className="flex justify-between text-xs text-slate-700 font-medium mb-1">
              <span>Sốc Doanh thu (%)</span>
              <span className="font-bold text-rose-600">{simSales}%</span>
            </label>
            <input
              type="range"
              min="-50"
              max="50"
              step="5"
              value={simSales}
              onChange={(e) => setSimSales(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <label className="flex justify-between text-xs text-slate-700 font-medium mb-1">
              <span>Chậm thu nợ (Ngày)</span>
              <span className="font-bold text-amber-600">+{simDelay} ngày</span>
            </label>
            <input
              type="range"
              min="0"
              max="60"
              step="5"
              value={simDelay}
              onChange={(e) => setSimDelay(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
          </div>

          <div>
            <label className="flex justify-between text-xs text-slate-700 font-medium mb-1">
              <span>Giãn nợ NCC (Ngày)</span>
              <span className="font-bold text-emerald-600">+{simSupplier} ngày</span>
            </label>
            <input
              type="range"
              min="-30"
              max="60"
              step="5"
              value={simSupplier}
              onChange={(e) => setSimSupplier(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-700 font-medium mb-1">Gói tín dụng bổ sung</label>
            <select
              value={simFinancing}
              onChange={(e) => setSimFinancing(Number(e.target.value))}
              className="w-full text-xs p-1.5 rounded-lg border border-slate-300 bg-white"
            >
              <option value={0}>Không vay thêm</option>
              <option value={300000000}>300M (Vốn LĐ 12T)</option>
              <option value={500000000}>500M (Trung hạn 24T)</option>
              <option value={1000000000}>1 Tỷ (Mở rộng quy mô)</option>
            </select>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <button
            onClick={runQuickSimulation}
            disabled={simLoading}
            className="px-4 py-2 rounded-xl text-white text-xs font-semibold shadow-xs hover:opacity-95 transition-all flex items-center gap-1.5 cursor-pointer"
            style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
          >
            🚀 {simLoading ? "Đang tính toán..." : "Chạy Thử nghiệm Stress Test"}
          </button>
        </div>

        {/* Simulation Output Card */}
        {simResult && (
          <div className="mt-4 p-4 rounded-xl bg-slate-900 text-white grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <div className="text-slate-400">Tiền mặt cuối kỳ:</div>
              <div className="text-base font-bold text-emerald-400 font-mono">
                {formatVND(simResult.kpis_9_layer?.ending_cash?.simulation)}
              </div>
            </div>
            <div>
              <div className="text-slate-400">Dòng tiền thuần (NCF):</div>
              <div className="text-base font-bold text-amber-300 font-mono">
                {formatVND(simResult.kpis_9_layer?.net_cash_flow?.simulation)}
              </div>
            </div>
            <div>
              <div className="text-slate-400">Doanh thu sau sốc:</div>
              <div className="text-base font-bold text-blue-300 font-mono">
                {formatVND(simResult.kpis_9_layer?.revenue?.simulation)}
              </div>
            </div>
            <div>
              <div className="text-slate-400">Chu kỳ tiền mặt (CCC):</div>
              <div className="text-base font-bold text-purple-300 font-mono">
                {simResult.kpis_9_layer?.ccc?.simulation} ngày
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 6. Evidence & Audit Provenance */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">5. Truy vết Bằng chứng Kế toán Thực tế (Evidence Provenance)</h2>
            <p className="text-xs text-slate-500">Các nguồn báo cáo ERP được truy xuất để trích xuất số liệu</p>
          </div>
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors text-slate-700 cursor-pointer"
          >
            {showEvidence ? "Ẩn chi tiết" : "Xem nguồn báo cáo"}
          </button>
        </div>

        {showEvidence && (
          <div className="mt-4 space-y-2 text-xs">
            {data?.evidence_refs && data.evidence_refs.length > 0 ? (
              data.evidence_refs.map((ev: any, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-100 font-mono text-slate-700 flex justify-between">
                  <span>{ev.source_name} ({ev.source_type})</span>
                  <span className="font-bold text-blue-600 font-mono">v:{ev.checksum_or_version || "2026.1"}</span>
                </div>
              ))
            ) : (
              <div className="p-3 rounded-lg bg-slate-50 text-slate-500">
                Dữ liệu được truy xuất trực tiếp từ các bảng Sổ cái `tabGL Entry` và `tabSales Invoice`.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialHealthView;
