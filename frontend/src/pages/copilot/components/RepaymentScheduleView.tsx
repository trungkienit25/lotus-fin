import React, { useState, useEffect } from "react";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";

interface RepaymentScheduleViewProps {
  company: string;
  onNavigateTab?: (tab: string) => void;
}

export const RepaymentScheduleView: React.FC<RepaymentScheduleViewProps> = ({
  company,
  onNavigateTab,
}) => {
  const { t } = useTranslation();
  const [principal, setPrincipal] = useState<number>(1000000000);
  const [baseRate, setBaseRate] = useState<number>(8.5);
  const [termMonths, setTermMonths] = useState<number>(12);
  const [method, setMethod] = useState<"EQUAL_INSTALLMENT" | "EQUAL_PRINCIPAL">("EQUAL_INSTALLMENT");
  const [shockBps, setShockBps] = useState<number>(0);

  const [scheduleRows, setScheduleRows] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>({
    firstPeriodPayment: 0,
    totalInterest: 0,
    totalPayment: 0,
    effectiveRate: 0,
  });

  const formatVND = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(val)) return "-- VND";
    return Math.round(Number(val)).toLocaleString("vi-VN") + " VND";
  };

  const calculateSchedule = () => {
    const effectiveAnnualRate = (baseRate + shockBps / 100) / 100;
    const monthlyRate = effectiveAnnualRate / 12;
    const rows = [];

    let balance = principal;
    let sumInterest = 0;
    let sumPrincipal = 0;

    if (method === "EQUAL_INSTALLMENT") {
      // PMT Formula: P * r * (1+r)^n / ((1+r)^n - 1)
      const pmt =
        monthlyRate > 0
          ? (principal * (monthlyRate * Math.pow(1 + monthlyRate, termMonths))) /
            (Math.pow(1 + monthlyRate, termMonths) - 1)
          : principal / termMonths;

      for (let m = 1; m <= termMonths; m++) {
        const interest = balance * monthlyRate;
        const princ = Math.min(balance, pmt - interest);
        const ending = Math.max(0, balance - princ);

        rows.push({
          period: m,
          beginning: balance,
          principal: princ,
          interest: interest,
          total: princ + interest,
          ending: ending,
        });

        sumInterest += interest;
        sumPrincipal += princ;
        balance = ending;
      }
    } else {
      // Equal Principal Formula: Fixed Principal + Declining Interest
      const fixedPrincipal = principal / termMonths;

      for (let m = 1; m <= termMonths; m++) {
        const interest = balance * monthlyRate;
        const ending = Math.max(0, balance - fixedPrincipal);

        rows.push({
          period: m,
          beginning: balance,
          principal: fixedPrincipal,
          interest: interest,
          total: fixedPrincipal + interest,
          ending: ending,
        });

        sumInterest += interest;
        sumPrincipal += fixedPrincipal;
        balance = ending;
      }
    }

    setScheduleRows(rows);
    setMetrics({
      firstPeriodPayment: rows[0]?.total || 0,
      totalInterest: sumInterest,
      totalPayment: principal + sumInterest,
      effectiveRate: (baseRate + shockBps / 100).toFixed(2),
    });
  };

  useEffect(() => {
    calculateSchedule();
  }, [principal, baseRate, termMonths, method, shockBps]);

  return (
    <div className="space-y-6">
      {/* 1. Header Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                Lotus Fin • Debt Repayment Engine (AI006)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-400/30">
                Amortization & Stress Engine
              </span>
            </div>
            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="repayment_schedule" size="md" />
              <h1 className="text-2xl font-bold tracking-tight">Debt Repayment Simulation & Interest Rate Stress Test</h1>
            </div>
            <p className="text-sm text-slate-300 mt-1">
              Generate periodic principal and interest amortization schedules (Fixed PMT vs. Equal Principal) and assess cash flow sensitivity under market interest rate shocks (+bps).
            </p>
          </div>
        </div>
      </div>

      {/* 2. Simulation Parameters Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <ModuleBadge moduleId="repayment_schedule" size="xs" />
          <span>Loan Parameters & Rate Shock Assumptions (+bps)</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Principal Amount (VND)</label>
            <input
              type="number"
              value={principal}
              step={50000000}
              onChange={(e) => setPrincipal(Number(e.target.value))}
              className="w-full text-xs p-2 rounded-xl border border-slate-300 bg-white font-mono font-bold text-slate-800"
            />
            <div className="text-[11px] text-blue-600 font-medium mt-1">{formatVND(principal)}</div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Base Interest Rate (%/Year)</label>
            <input
              type="number"
              value={baseRate}
              step={0.1}
              onChange={(e) => setBaseRate(Number(e.target.value))}
              className="w-full text-xs p-2 rounded-xl border border-slate-300 bg-white font-mono text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Term (Months)</label>
            <input
              type="number"
              value={termMonths}
              min={1}
              max={120}
              onChange={(e) => setTermMonths(Number(e.target.value))}
              className="w-full text-xs p-2 rounded-xl border border-slate-300 bg-white font-mono text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Repayment Method</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as any)}
              className="w-full text-xs p-2 rounded-xl border border-slate-300 bg-white"
            >
              <option value="EQUAL_INSTALLMENT">Fixed Annuity / PMT (Principal + Interest)</option>
              <option value="EQUAL_PRINCIPAL">Equal Principal (Declining Balance)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-rose-600 mb-1">Rate Shock (+bps)</label>
            <select
              value={shockBps}
              onChange={(e) => setShockBps(Number(e.target.value))}
              className="w-full text-xs p-2 rounded-xl border border-rose-300 bg-rose-50/50 font-bold text-rose-700"
            >
              <option value={0}>0 bps (Baseline)</option>
              <option value={100}>+100 bps (+1.0%/year)</option>
              <option value={200}>+200 bps (+2.0%/year)</option>
              <option value={300}>+300 bps (+3.0%/year)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. 4 Core Metrics Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">First Period Payment Obligation</div>
          <div className="text-xl font-extrabold text-blue-600 mt-1">{formatVND(metrics.firstPeriodPayment)}</div>
          <div className="text-[11px] text-slate-400 mt-1">Includes Principal + Interest</div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Total Interest Payable</div>
          <div className="text-xl font-extrabold text-rose-600 mt-1">{formatVND(metrics.totalInterest)}</div>
          <div className="text-[11px] text-slate-400 mt-1">Over full {termMonths}-month tenure</div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Total Cash Outflow</div>
          <div className="text-xl font-extrabold text-slate-900 mt-1">{formatVND(metrics.totalPayment)}</div>
          <div className="text-[11px] text-slate-400 mt-1">Principal + Total Interest</div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Effective Post-Shock Rate</div>
          <div className="text-xl font-extrabold text-purple-600 mt-1">{metrics.effectiveRate}% / year</div>
          <div className="text-[11px] text-slate-400 mt-1">Reflects +{shockBps} bps</div>
        </div>
      </div>

      {/* 4. Full Amortization Schedule Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Periodic Amortization Schedule</h2>
            <p className="text-xs text-slate-500">
              Detailed breakdown of principal, interest, and ending balance per monthly period
            </p>
          </div>
          <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
            {scheduleRows.length} Payment Periods
          </span>
        </div>

        <div className="overflow-x-auto max-h-[420px] border border-slate-100 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-slate-600 z-10 font-semibold">
              <tr>
                <th className="py-2.5 px-3 text-center">Period</th>
                <th className="py-2.5 px-3">Beginning Balance</th>
                <th className="py-2.5 px-3">Principal Paid</th>
                <th className="py-2.5 px-3">Interest Incurred</th>
                <th className="py-2.5 px-3">Total Installment</th>
                <th className="py-2.5 px-3">Ending Balance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scheduleRows.map((r) => (
                <tr key={r.period} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2.5 px-3 text-center font-bold text-slate-700 font-mono">M{r.period}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-600">{formatVND(r.beginning)}</td>
                  <td className="py-2.5 px-3 font-mono font-semibold text-blue-600">{formatVND(r.principal)}</td>
                  <td className="py-2.5 px-3 font-mono font-semibold text-rose-600">{formatVND(r.interest)}</td>
                  <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{formatVND(r.total)}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-700">{formatVND(r.ending)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default RepaymentScheduleView;

