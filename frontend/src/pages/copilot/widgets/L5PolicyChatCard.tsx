import React from "react";
import { ModuleBadge } from "../components/ModuleBadge";

export interface L5PolicyChatCardProps {
  actionName?: string;
  reasonCode?: string;
  consequenceText?: string;
}

export const L5PolicyChatCard: React.FC<L5PolicyChatCardProps> = ({
  actionName = "Hủy bỏ chứng từ / Gửi thanh toán tự động",
  reasonCode = "POLICY_SAFETY_GATE_L5_BLOCKED",
  consequenceText = "Thao tác có tác động vĩnh viễn tới sổ cái kế toán và tài khoản ngân hàng. Cần phê duyệt kép và thực hiện trực tiếp trên giao diện kế toán được phân quyền.",
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
                Bị từ chối bởi Chính sách Kiểm soát Kép (L5 Gate)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-400/30">
                BLOCKED
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Hành động có tác động tài chính vĩnh viễn bị chặn tự động
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
            <span>Hành động yêu cầu: {actionName}</span>
          </div>
          <p className="leading-relaxed text-slate-700">
            {consequenceText}
          </p>
        </div>

        <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 font-mono">
          <span>Lý do kiểm toán: {reasonCode}</span>
          <span>Side effects disabled</span>
        </div>
      </div>
    </div>
  );
};
