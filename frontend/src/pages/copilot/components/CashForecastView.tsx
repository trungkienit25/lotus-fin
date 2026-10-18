import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";
import { bootstrapSession } from "../../../providers/sessionBootstrap";

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
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  const fetchForecast = async () => {
    if (!company) return;
    setLoading(true);
    setError(null);
    try {
      const session = await bootstrapSession().catch(() => null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.csrfToken) {
        headers["X-Frappe-CSRF-Token"] = session.csrfToken;
      }

      const res = await axios.post(
        "/api/method/lotus_fin.api.ai_insights.get_ai002_cash_forecast",
        {
          company,
          financial_as_of: asOfDate,
        },
        { headers }
      );

      const payload = res.data?.message || res.data;
      if (payload) {
        setData(payload);
      }
    } catch (err: any) {
      console.warn("Could not fetch real cash forecast:", err);
      const msg = err?.response?.data?.exception || err?.response?.data?._server_messages || err?.message || "Failed to fetch cash forecast";
      setError(typeof msg === "string" ? msg : "Failed to fetch cash forecast");
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchForecast();
  }, [company, asOfDate]);

  const formatCurrency = (val: any) => {
    const cur = data?.currency || "USD";
    if (val === null || val === undefined || val === "" || isNaN(Number(val))) return `-- ${cur}`;
    const num = Number(val);
    if (cur === "USD") {
      return `$${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return Math.round(num).toLocaleString("vi-VN") + " " + cur;
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
                Horizon: 30-Day (Daily EOD)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 font-mono">
                {company}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="cash_forecast" size="md" />
              <h1 className="text-2xl font-bold tracking-tight">Cash Flow Forecast & Liquidity Trajectory</h1>
            </div>
            <p className="text-sm text-slate-300 mt-1">
              Extracted from General Ledger cash balances and contractual receivables/payables schedule of {company}.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs bg-white/10 px-3 py-1.5 rounded-xl border border-white/20">
              <span className="text-slate-300">As-of Date:</span>
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
              <span>{loading ? "Forecasting..." : "Refresh from ERP"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && !data && (
        <div className="bg-white rounded-2xl p-12 border border-slate-200/80 shadow-xs flex flex-col items-center justify-center text-slate-500">
          <svg className="w-8 h-8 animate-spin text-blue-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <p className="text-sm font-medium">Extracting opening cash balances and contractual obligations from General Ledger...</p>
        </div>
      )}

      {/* Error Alert */}
      {error && !loading && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <span>⚠️</span>
            <span>Failed to fetch cash forecast: {error}</span>
          </div>
          <button
            onClick={() => fetchForecast()}
            className="px-3 py-1 bg-rose-600 text-white text-xs font-semibold rounded-lg hover:bg-rose-700 transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* 2. Tier 1: Opening Cash & Bank Balances Verification */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ModuleBadge moduleId="financial_health" size="xs" />
              <span>Tier 1: Opening Cash & Bank Balances (Actual GL Ledger)</span>
            </h2>
            <p className="text-xs text-slate-500">Independent reconciliation between General Ledger and Trial Balance</p>
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
            Total Consolidated Opening Available Cash
          </div>
          <div className={`text-3xl font-extrabold mt-1 tracking-tight font-mono ${
            aggregateAmount !== null && aggregateAmount < 0 ? "text-rose-700" : "text-slate-900"
          }`}>
            {formatCurrency(aggregateAmount)}
          </div>
        </div>

        {/* Account Breakdown Chips */}
        <div>
          <div className="text-xs font-semibold text-slate-600 mb-2">Detailed cash & bank account breakdown:</div>
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
                      {formatCurrency(bal)}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-xs text-slate-400">No matching cash/bank accounts identified.</div>
            )}
          </div>
        </div>
      </div>

      {/* 3. 30-Day Cash Trajectory Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>📈</span> 30-Day Cash Trajectory (Daily EOD Trajectory)
            </h2>
            <p className="text-xs text-slate-500">Projected end-of-day cash balance driven by confirmed accounting transactions</p>
          </div>
          <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
            {forecastPoints.length > 0 ? `${forecastPoints.length} Daily Intervals` : "Deterministic Baseline"}
          </span>
        </div>

        <div className="overflow-x-auto max-h-[380px] border border-slate-100 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-slate-600 z-10 font-semibold">
              <tr>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">EOD Cash Balance</th>
                <th className="py-2.5 px-3">Key Drivers & Events</th>
                <th className="py-2.5 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {forecastPoints.length > 0 ? (
                forecastPoints.map((pt: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-800">{pt.date}</td>
                    <td className="py-2.5 px-3 font-bold font-mono text-slate-900">{formatCurrency(pt.eod_balance || pt.amount)}</td>
                    <td className="py-2.5 px-3 text-slate-600">{pt.event_desc || "Conserved baseline balance"}</td>
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
                        {pt.status === "HEALTHY" ? "Healthy" : pt.status === "WARNING" ? "Warning" : "Deficit"}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-400">
                    <div>
                      {data?.reason_code === "NO_CONFIRMED_SETTLEMENT_EVENTS"
                        ? "No confirmed cash settlement events recorded within the next 30 days (NO_CONFIRMED_SETTLEMENT_EVENTS)."
                        : "No future cash disbursement vouchers approved."}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      Purchasing and sales invoices below reflect contractual due dates.
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
              <span>📑</span> Tier 2: Actual Contractual Obligations (AR / AP Due Schedule from ERP)
            </h2>
            <p className="text-xs text-slate-500">Booked Sales Invoices & Purchase Invoices</p>
          </div>
          <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full">
            {obligationsList.length} Documents
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-100 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-2.5 px-3 text-center">Type</th>
                <th className="py-2.5 px-3">Counterparty / Hash</th>
                <th className="py-2.5 px-3">Due Date</th>
                <th className="py-2.5 px-3">Remaining Balance</th>
                <th className="py-2.5 px-3">Voucher Reference</th>
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
                          {isAR ? "Inflow (AR)" : "Outflow (AP)"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-800">
                        {ob.party || ob.party_hash || ob.party_type || "Counterparty"}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-600">{ob.due_date}</td>
                      <td className={`py-2.5 px-3 font-mono font-bold ${isAR ? "text-emerald-600" : "text-rose-600"}`}>
                        {isAR ? "+" : "-"}{formatCurrency(amt)}
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
                    No unsettled AR/AP obligations.
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
            <span>⚠️</span> Accounting Methodology Limitations & Assumptions (AI-F002):
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
