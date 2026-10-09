import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "../../../i18n";
import { formatBrandText } from "../../../utils/brand";
import { ModuleBadge } from "./ModuleBadge";

interface RiskSignalViewProps {
  company: string;
  onNavigateTab?: (tab: string) => void;
}

export const RiskSignalView: React.FC<RiskSignalViewProps> = ({
  company,
  onNavigateTab,
}) => {
  const { t } = useTranslation();
  const [signalId, setSignalId] = useState<string>("AR_OVERDUE_SPIKE");
  const [asOfDate, setAsOfDate] = useState<string>("2026-09-26");
  const [includeExplanation, setIncludeExplanation] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const evaluateSignal = async () => {
    if (!company) return;
    setLoading(true);
    try {
      const res = await axios.post("/api/method/lotus_fin.api.ai_insights.get_risk_signal", {
        company,
        signal_id: signalId,
        as_of_date: asOfDate,
        include_explanation: includeExplanation ? 1 : 0,
      });

      const payload = res.data?.message || res.data;
      if (payload) {
        setResult(payload);
      }
    } catch (err: any) {
      console.warn("Could not evaluate risk signal:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    evaluateSignal();
  }, [company, signalId, asOfDate]);

  const formatVND = (val: any) => {
    if (val === null || val === undefined || isNaN(Number(val))) return "-- VND";
    return Math.round(Number(val)).toLocaleString("vi-VN") + " VND";
  };

  const observedVal = result?.observed?.value !== undefined
    ? `${(Number(result.observed.value) * 100).toFixed(1)}%`
    : "--";
  const baselineVal = result?.baseline?.value !== undefined
    ? `${(Number(result.baseline.value) * 100).toFixed(1)}%`
    : "--";
  const deltaVal = result?.delta_pp !== undefined ? `${result.delta_pp} pp` : "0.00 pp";

  return (
    <div className="space-y-6">
      {/* 1. Header Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                Lotus Fin • Risk Signal Agent (AI003)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                Standard Contract V2.2
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 font-mono">
                {company}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <ModuleBadge moduleId="risk_signals" size="md" />
              <h1 className="text-2xl font-bold tracking-tight">Đánh giá Tín hiệu Rủi ro & Bất thường Thực tế</h1>
            </div>
            <p className="text-sm text-slate-300 mt-1">
              Phát hiện tự động rủi ro nợ quá hạn đột biến (AR Overdue Spike) và áp lực dồn tích hạn nợ nhà cung cấp (AP Due Cluster) từ dữ liệu kế toán {company}.
            </p>
          </div>

          <button
            onClick={() => evaluateSignal()}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold border border-white/20 transition-all flex items-center gap-1.5 cursor-pointer backdrop-blur"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>{loading ? "Đang đánh giá..." : "Đánh giá Tín hiệu"}</span>
          </button>
        </div>

        {/* Filter Controls */}
        <div className="mt-5 pt-4 border-t border-white/10 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">Tín hiệu kiểm tra:</span>
            <select
              value={signalId}
              onChange={(e) => setSignalId(e.target.value)}
              className="bg-white/10 border border-white/20 text-white rounded-lg px-2.5 py-1 text-xs focus:outline-hidden"
            >
              <option value="AR_OVERDUE_SPIKE" className="text-slate-800">
                AR Overdue Spike (Nợ phải thu quá hạn tăng cao)
              </option>
              <option value="AP_DUE_CLUSTER" className="text-slate-800">
                AP Due Cluster (Áp lực đáo hạn chi trả dồn tích)
              </option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-300 font-medium">Ngày chốt sổ:</span>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="bg-white/10 border border-white/20 text-white rounded-lg px-2 py-1 text-xs font-mono"
            />
          </div>
        </div>
      </div>

      {/* 2. Verdict Glossary Bar */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs flex flex-wrap items-center gap-3 text-xs">
        <span className="font-semibold text-slate-700 flex items-center gap-1">
          <span>📖</span> Thang đo mức độ nghiêm trọng:
        </span>
        <span className="px-2.5 py-1 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          BENIGN: An toàn (Dưới ngưỡng cảnh báo)
        </span>
        <span className="px-2.5 py-1 rounded-full font-medium bg-amber-50 text-amber-700 border border-amber-200">
          WATCH: Cần theo dõi sát
        </span>
        <span className="px-2.5 py-1 rounded-full font-medium bg-rose-50 text-rose-700 border border-rose-200">
          HIGH: Rủi ro cao cần xử lý ngay
        </span>
      </div>

      {/* 3. Result & Verdict Panel */}
      {result && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-6">
          {/* Header Status Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  result.severity === "HIGH"
                    ? "bg-rose-50 text-rose-700 border border-rose-300"
                    : result.severity === "WATCH" || result.finding === "TRIGGERED"
                    ? "bg-amber-50 text-amber-700 border border-amber-300"
                    : "bg-emerald-50 text-emerald-700 border border-emerald-300"
                }`}
              >
                {result.severity === "HIGH"
                  ? "🚨 SEVERITY: HIGH (RỦI RO CAO)"
                  : result.severity === "WATCH" || result.finding === "TRIGGERED"
                  ? "⚠️ SEVERITY: WATCH (THEO DÕI)"
                  : "🛡️ BENIGN: AN TOÀN TRONG NGƯỠNG"}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                Signal: {result.signal_id || signalId}
              </span>
            </div>
            <span className="text-xs text-slate-400 font-mono">Cutoff: {result.as_of_date || asOfDate}</span>
          </div>

          {/* Root Cause & Finding Rationale */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <span>🔍</span> Kết luận Đánh giá Thực tế:
            </div>
            <p className="text-sm text-slate-800 font-medium">
              {formatBrandText(result.explanation?.text || result.reason_text || "Đánh giá định lượng hoàn tất theo quy chuẩn chính sách.")}
            </p>
          </div>

          {/* Observed Metric Details */}
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
              📊 Chi tiết Chỉ số Đo lường Thực tế từ Sổ cái:
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3.5 rounded-xl border border-slate-100 bg-[#F9FBFC]">
                <div className="text-xs text-slate-500">Tỷ lệ quan sát hiện tại</div>
                <div className="text-lg font-bold text-slate-900 mt-1 font-mono">{observedVal}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Tổng AR: {formatVND(result?.observed?.supporting_amount)}
                </div>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-100 bg-[#F9FBFC]">
                <div className="text-xs text-slate-500">Tỷ lệ cơ sở (Baseline {result.baseline?.cutoff || ""})</div>
                <div className="text-lg font-bold text-slate-700 mt-1 font-mono">{baselineVal}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Tổng AR cơ sở: {formatVND(result?.baseline?.denominator)}
                </div>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-100 bg-[#F9FBFC]">
                <div className="text-xs text-slate-500">Độ lệch (Δ pp)</div>
                <div className={`text-lg font-bold mt-1 font-mono ${deltaVal.startsWith("+") && deltaVal !== "+0.00 pp" ? "text-rose-600" : "text-emerald-600"}`}>
                  {deltaVal}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Ngưỡng cảnh báo: {result?.rule?.threshold || "5.0"} pp
                </div>
              </div>
            </div>
          </div>

          {/* AI Narrative & Recommendations */}
          {result.next_check_actions && result.next_check_actions.length > 0 && (
            <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 space-y-2 text-xs">
              <div className="font-bold text-indigo-950 flex items-center gap-1.5">
                <span>🎯</span> Khuyến nghị Hành động Tiếp theo (Actionable Review):
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-700 pt-1">
                {result.next_check_actions.map((act: string, i: number) => (
                  <li key={i}>{formatBrandText(act)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskSignalView;
