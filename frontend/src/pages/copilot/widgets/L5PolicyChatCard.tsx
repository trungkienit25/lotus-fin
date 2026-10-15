import React from "react";
import type { L5ProposalPreview } from "../l5/l5Types";

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
    <div className="w-full rounded-2xl border border-rose-200 bg-rose-50/40 p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3 my-2">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rose-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="size-7 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs shadow-2xs">
            🛡️
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-rose-950 leading-tight">
              Bị từ chối bởi Chính sách An toàn (L5 Policy Gate)
            </h4>
            <div className="text-[11px] text-rose-700/80 font-mono mt-0.5">
              Hành động: {actionName}
            </div>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
          CHẶN THỰC THI (BLOCKED)
        </span>
      </div>

      <div className="space-y-1.5 text-xs text-rose-900">
        <div className="font-semibold text-rose-950">Giải thích từ Hệ thống Kiểm soát:</div>
        <p className="leading-relaxed bg-white/70 p-3 rounded-xl border border-rose-200/60 text-slate-800">
          {consequenceText}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-rose-600 border-t border-rose-100 pt-2 font-mono">
        <span>Lý do kiểm toán: {reasonCode}</span>
        <span className="bg-rose-100 px-2 py-0.5 rounded text-rose-800 font-bold">Dual-Control Required</span>
      </div>
    </div>
  );
};
