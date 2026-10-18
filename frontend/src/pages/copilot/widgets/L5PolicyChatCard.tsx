import React from "react";
import { ModuleBadge } from "../components/ModuleBadge";

export interface L5PolicyChatCardProps {
  actionName?: string;
  reasonCode?: string;
  consequenceText?: string;
}

export const L5PolicyChatCard: React.FC<L5PolicyChatCardProps> = ({
  actionName = "Cancel Document / Automated Direct Payment",
  reasonCode = "POLICY_SAFETY_GATE_L5_BLOCKED",
  consequenceText = "This operation permanently affects the accounting general ledger and bank balances. It strictly requires dual authorization and direct execution in the authorized accounting module.",
}) => {
  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-rose-950 via-slate-900 to-indigo-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="risk_signals" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Blocked by Dual-Control Security Policy (L5 Gate)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-400/30">
                BLOCKED
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Actions with permanent financial impact are automatically blocked
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-rose-200 border border-white/20 backdrop-blur font-mono self-start sm:self-auto">
          Dual-Control Required
        </span>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        <div className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200/70 text-rose-950 space-y-1.5 text-xs">
          <div className="font-bold flex items-center gap-1.5">
            <span>🛡️</span>
            <span>Requested Action: {actionName}</span>
          </div>
          <p className="leading-relaxed text-slate-700">
            {consequenceText}
          </p>
        </div>

        <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 font-mono">
          <span>Audit Reason: {reasonCode}</span>
          <span>Side effects disabled</span>
        </div>
      </div>
    </div>
  );
};
