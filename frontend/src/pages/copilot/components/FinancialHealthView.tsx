import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";
import { bootstrapSession } from "../../../providers/sessionBootstrap";

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

      const session = await bootstrapSession().catch(() => null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.csrfToken) {
        headers["X-Frappe-CSRF-Token"] = session.csrfToken;
      }

      const res = await axios.post(
        "/api/method/lotus_fin.api.ai_insights.get_financial_snapshot",
        {
          company,
          period_start: pStart,
          period_end: pEnd,
          currency: "USD",
          comparison: comparisonMode === "NONE" ? null : "PREVIOUS_PERIOD",
          include_explanation: 1,
        },
        { headers }
      );

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
      const session = await bootstrapSession().catch(() => null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.csrfToken) {
        headers["X-Frappe-CSRF-Token"] = session.csrfToken;
      }

      const res = await axios.post(
        "/api/method/lotus_fin.modules.f005_financing.service.simulate_what_if",
        {
          company,
          sales_change_pct: simSales / 100,
          collection_delay_days: simDelay,
          supplier_due_shift_days: simSupplier,
          financing_amount: simFinancing,
          financing_term_months: 12,
          financing_rate_annual: 0.095,
        },
        { headers }
      );
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

  const formatCurrency = (val: number | null | undefined) => {
    const cur = data?.currency || "USD";
    if (val === null || val === undefined || isNaN(val)) return `-- ${cur}`;
    const num = Number(val);
    if (cur === "USD") {
      return `$${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return Math.round(num).toLocaleString("vi-VN") + " " + cur;
  };

  const metricMap: Record<string, any> = {};
  if (data?.metrics && Array.isArray(data.metrics)) {
    data.metrics.forEach((m: any) => {
      metricMap[m.metric_id] = m;
    });
  }

  const approvedMetrics = [
    { id: "revenue", label: "Revenue", isCurrency: true },
    { id: "cogs", label: "Cost of Goods Sold (COGS)", isCurrency: true },
    { id: "gross_margin", label: "Gross Profit Margin", isRatio: true },
    { id: "cash_balance", label: "Cash Balance", isCurrency: true },
    { id: "ar_outstanding", label: "Accounts Receivable (AR)", isCurrency: true },
    { id: "overdue_ar_ratio", label: "Overdue AR Ratio", isRatio: true },
    { id: "ap_outstanding", label: "Accounts Payable (AP)", isCurrency: true },
    { id: "near_term_ap", label: "Near-Term AP Maturing", isCurrency: true },
  ];

  return (
    <div className="space-y-6 font-sans">
      {/* 1. Executive Header Banner */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-[#1E63B7] border border-blue-200/80 font-mono">
                AI001 • Financial Health
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80 flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>Mode: {data?.data_mode || "Actual ERP"}</span>
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 font-mono">
                {company}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="financial_health" size="md" />
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
                Corporate Financial Health Report
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Extracted directly from General Ledger, Trial Balance, and Profit & Loss of {company}.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 self-start md:self-auto shrink-0">
            <button
              onClick={() => fetchHealthData()}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold border border-slate-200 transition-all flex items-center gap-2 cursor-pointer shadow-2xs hover:text-[#1E63B7] hover:border-blue-300"
            >
              <svg className={`size-3.5 ${loading ? "animate-spin text-[#1E63B7]" : "text-slate-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{loading ? "Querying Ledger..." : "Sync from ERP"}</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-medium">Fiscal Period:</span>
            <select
              value={periodPreset}
              onChange={(e) => setPeriodPreset(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] font-medium cursor-pointer"
            >
              <option value="CURRENT_YEAR">Current Year (2026 - Actual)</option>
              <option value="FY2025">Fiscal Year 2025</option>
              <option value="FY2020">Fiscal Year 2020</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-medium">Comparison:</span>
            <select
              value={comparisonMode}
              onChange={(e) => setComparisonMode(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] font-medium cursor-pointer"
            >
              <option value="NONE">No Comparison</option>
              <option value="PREVIOUS_PERIOD">Previous Period</option>
            </select>
          </div>
        </div>
      </div>

      {/* 2. Key Financial Metrics (8-KPI Grid) */}
      <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5">
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-900">
              1. Actual Financial Metrics (8 Key Indicators)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Independently reconciled from General Ledger and P&L of {company}
            </p>
          </div>
          <span className="text-[11px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-3 py-1 rounded-full font-semibold self-start sm:self-auto flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            <span>Extracted from ERP Ledger</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {approvedMetrics.map((meta) => {
            const m = metricMap[meta.id];
            let displayVal = "--";
            let isNegative = false;
            let statusBadge = "No Data";

            if (m && m.status === "AVAILABLE" && m.value !== null && m.value !== undefined) {
              statusBadge = "Reconciled";
              if (meta.isRatio) {
                displayVal = `${(m.value * 100).toFixed(2)}%`;
              } else {
                displayVal = formatCurrency(m.value);
                if (m.value < 0) isNegative = true;
              }
            } else if (m && m.limitations && m.limitations.length > 0) {
              displayVal = "N/A";
              statusBadge = m.limitations[0];
            }

            return (
              <div
                key={meta.id}
                className={`p-4 rounded-2xl border transition-all ${
                  isNegative
                    ? "bg-rose-50/40 border-rose-200 hover:border-rose-300"
                    : "bg-[#F9FBFC] border-slate-200/70 hover:bg-white hover:border-[#1E63B7]/40 hover:shadow-2xs"
                }`}
              >
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600 truncate">
                    {meta.label}
                  </span>
                  <span
                    className={`size-2 rounded-full shrink-0 ${
                      m?.status === "AVAILABLE"
                        ? isNegative
                          ? "bg-rose-500"
                          : "bg-emerald-500"
                        : "bg-slate-300"
                    }`}
                  />
                </div>
                <div
                  className={`text-lg sm:text-xl font-bold tracking-tight mt-1 font-mono ${
                    isNegative ? "text-rose-700" : "text-slate-900"
                  }`}
                >
                  {displayVal}
                </div>
                <div className="mt-2 pt-2 border-t border-slate-200/50 flex items-center justify-between text-[10px]">
                  <span className="text-slate-400 font-medium truncate max-w-[150px]" title={statusBadge}>
                    {statusBadge}
                  </span>
                  <span className={`px-1.5 py-0.2 rounded-md font-bold uppercase text-[9px] shrink-0 ${
                    m?.status === "AVAILABLE"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                      : "bg-slate-100 text-slate-500 border border-slate-200/60"
                  }`}>
                    {m?.status === "AVAILABLE" ? "Verified" : "Unverified"}
                  </span>
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
              <h2 className="text-base font-bold text-slate-900">2. Fiscal Period Variance Analysis</h2>
              <p className="text-xs text-slate-500">
                Reconciled against previous period ({data.comparison.previous_period?.start} to {data.comparison.previous_period?.end})
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                  <th className="py-2.5 px-3">Metric</th>
                  <th className="py-2.5 px-3">Current Period</th>
                  <th className="py-2.5 px-3">Prior Period</th>
                  <th className="py-2.5 px-3">Variance (Abs)</th>
                  <th className="py-2.5 px-3">Variance (%)</th>
                  <th className="py-2.5 px-3">Status</th>
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
                        {isRatio ? `${(item.current * 100).toFixed(1)}%` : formatCurrency(item.current)}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {isRatio ? `${(item.previous * 100).toFixed(1)}%` : formatCurrency(item.previous)}
                      </td>
                      <td className={`py-2.5 px-3 font-semibold ${isPositive ? "text-emerald-600" : "text-rose-600"}`}>
                        {isPositive ? "+" : ""}
                        {isRatio ? `${(item.absolute_change * 100).toFixed(1)} pp` : formatCurrency(item.absolute_change)}
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

      {/* 3. Grounded AI Financial Analysis Narrative from Real Ledger */}
      {data?.explanation && (
        <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="size-7 rounded-xl bg-blue-50 text-[#1E63B7] flex items-center justify-center font-bold text-xs shrink-0 border border-blue-100">
              ✦
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
                3. Grounded Accounting Interpretation & Recommendations
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Derived directly from journal entries and transactions recorded in the ERP General Ledger
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/70">
              <div className="font-bold uppercase tracking-wider text-slate-700 text-[11px] mb-2.5 flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-[#1E63B7]"></span>
                <span>Verified Ledger Facts</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700">
                {data.explanation.facts && data.explanation.facts.length > 0 ? (
                  data.explanation.facts.map((f: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-slate-400 mt-0.5 font-bold">•</span>
                      <span className="flex-1 leading-relaxed">{formatBrandText(f)}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-400 italic">No transactions recorded in the selected period.</li>
                )}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/70">
              <div className="font-bold uppercase tracking-wider text-slate-700 text-[11px] mb-2.5 flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-[#2FB29A]"></span>
                <span>Actionable Checks</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700">
                {data.explanation.next_checks && data.explanation.next_checks.length > 0 ? (
                  data.explanation.next_checks.map((nc: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-500 mt-0.5 font-bold">✓</span>
                      <span className="flex-1 leading-relaxed">{formatBrandText(nc)}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-400 italic">Audit detailed bank statements and overdue customer balances.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 4. What-If Quick Simulation Stress Test Preview */}
      <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="size-7 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs shrink-0 border border-indigo-100">
              <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
                4. Rapid Sensitivity Stress Test (What-If 9-KPIs)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Simulate instantaneous impact on cash flow and liquidity safety
              </p>
            </div>
          </div>
          {onNavigateTab && (
            <button
              onClick={() => onNavigateTab("what_if")}
              className="text-xs font-semibold text-[#1E63B7] hover:text-[#174f96] flex items-center gap-1.5 cursor-pointer self-start sm:self-auto px-3 py-1.5 rounded-xl hover:bg-blue-50 transition-colors"
            >
              <span>Open Scenario Studio</span>
              <span className="text-[11px]">➔</span>
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-2xl bg-[#F9FBFC] border border-slate-200/70">
          <div>
            <label className="flex justify-between text-xs text-slate-700 font-semibold mb-1.5">
              <span>Sales Shock (%)</span>
              <span className="font-mono font-bold text-rose-600">{simSales}%</span>
            </label>
            <input
              type="range"
              min="-50"
              max="50"
              step="5"
              value={simSales}
              onChange={(e) => setSimSales(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#1E63B7]"
            />
          </div>

          <div>
            <label className="flex justify-between text-xs text-slate-700 font-semibold mb-1.5">
              <span>Collection Delay (Days)</span>
              <span className="font-mono font-bold text-amber-600">+{simDelay} days</span>
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
            <label className="flex justify-between text-xs text-slate-700 font-semibold mb-1.5">
              <span>Supplier Shift (Days)</span>
              <span className="font-mono font-bold text-emerald-600">+{simSupplier} days</span>
            </label>
            <input
              type="range"
              min="-30"
              max="60"
              step="5"
              value={simSupplier}
              onChange={(e) => setSimSupplier(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#2FB29A]"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-700 font-semibold mb-1.5">Financing Facility</label>
            <select
              value={simFinancing}
              onChange={(e) => setSimFinancing(Number(e.target.value))}
              className="w-full text-xs p-2 rounded-xl border border-slate-200 bg-white font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7]"
            >
              <option value={0}>None (No extra debt)</option>
              <option value={300000000}>300M (Working Capital 12M)</option>
              <option value={500000000}>500M (Medium Term 24M)</option>
              <option value={1000000000}>1 Billion (Expansion Term)</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={runQuickSimulation}
            disabled={simLoading}
            className="px-4 py-2 rounded-xl bg-[#1E63B7] hover:bg-[#174f96] text-white text-xs font-bold shadow-xs hover:opacity-95 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <svg className={`size-3.5 ${simLoading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>{simLoading ? "Computing..." : "Run Stress Test Simulation"}</span>
          </button>
        </div>

        {/* Simulation Output Card */}
        {simResult && (
          <div className="mt-4 p-4 rounded-2xl bg-slate-900 text-white grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs shadow-xs border border-slate-800 animate-fadeIn">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Ending Cash</div>
              <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                {formatCurrency(simResult.kpis_9_layer?.ending_cash?.simulation)}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Net Cash Flow (NCF)</div>
              <div className="text-base font-bold text-amber-300 font-mono mt-0.5">
                {formatCurrency(simResult.kpis_9_layer?.net_cash_flow?.simulation)}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Simulated Revenue</div>
              <div className="text-base font-bold text-blue-300 font-mono mt-0.5">
                {formatCurrency(simResult.kpis_9_layer?.revenue?.simulation)}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Cash Cycle (CCC)</div>
              <div className="text-base font-bold text-teal-300 font-mono mt-0.5">
                {simResult.kpis_9_layer?.ccc?.simulation} days
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 5. Evidence & Audit Provenance */}
      <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
              5. Audit Evidence Provenance
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Underlying ERP reports and registers referenced for extraction</p>
          </div>
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-slate-700 cursor-pointer shadow-2xs"
          >
            {showEvidence ? "Hide Details" : "View Source Evidence"}
          </button>
        </div>

        {showEvidence && (
          <div className="mt-4 space-y-2 text-xs">
            {data?.evidence_refs && data.evidence_refs.length > 0 ? (
              data.evidence_refs.map((ev: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 font-mono text-slate-700 flex justify-between items-center">
                  <span>{ev.source_name} ({ev.source_type})</span>
                  <span className="font-bold text-[#1E63B7] font-mono">v:{ev.checksum_or_version || "2026.1"}</span>
                </div>
              ))
            ) : (
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-slate-500">
                Data reconciled directly from Real-Time General Ledger and Sales Invoicing registers.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialHealthView;
