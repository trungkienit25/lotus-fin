import React, { useState, useEffect } from "react";
import type { L4ActionProposal, L4OperationRecord } from "../actions/l4MutationContracts";
import { ModuleBadge } from "../components/ModuleBadge";

export interface L4ProposalChatCardProps {
  initialTitle?: string;
  targetEntity?: string;
  onSuccess?: (op: L4OperationRecord) => void;
}

export const L4ProposalChatCard: React.FC<L4ProposalChatCardProps> = ({
  initialTitle = "Theo dõi công nợ quá hạn SINV-2026-00088",
  targetEntity = "Sales Invoice/SINV-2026-00088",
  onSuccess,
}) => {
  const [proposal, setProposal] = useState<L4ActionProposal>({
    proposal_id: `prop-${Date.now().toString(36)}`,
    action_id: "lotus.task.create",
    target_entity: targetEntity,
    arguments: { title: initialTitle, due_date: "2026-10-25", priority: "MEDIUM" },
    canonical_args_digest: "sha256-mock-digest",
    actor_id: "user-admin",
    session_id: "sess-mock-01",
    tenant_id: "tenant-default",
    site_id: "site-lotus",
    source_version: "v1.0",
    policy_version: "p6-v1",
    issued_at_utc: new Date().toISOString(),
    preview_title: initialTitle,
    preview_diff: [
      { field_name: "Tên công việc", old_value: null, new_value: initialTitle, description: "Nhiệm vụ theo dõi công nợ đối soát" },
      { field_name: "Hạn chót xử lý", old_value: null, new_value: "2026-10-25", description: "Thời hạn quy chuẩn kế toán (7 ngày)" },
      { field_name: "Mức độ ưu tiên", old_value: null, new_value: "MEDIUM", description: "Mức ưu tiên đối chiếu định kỳ" },
    ],
    expires_at_utc: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
    confirmation_challenge: "chal-mock-998",
    simulated: true,
  });

  const [timeLeft, setTimeLeft] = useState<number>(600);
  const [status, setStatus] = useState<"IDLE" | "SUBMITTING" | "SUCCEEDED" | "CANCELLED" | "EXPIRED">("IDLE");
  const [operationRecord, setOperationRecord] = useState<L4OperationRecord | null>(null);

  useEffect(() => {
    if (status !== "IDLE") return;
    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.floor((new Date(proposal.expires_at_utc).getTime() - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining === 0) {
        setStatus("EXPIRED");
        clearInterval(interval);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [proposal.expires_at_utc, status]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const handleConfirm = () => {
    setStatus("SUBMITTING");
    setTimeout(() => {
      const op: L4OperationRecord = {
        operation_id: `OP-MUTATION-${Date.now().toString(36).toUpperCase()}`,
        proposal_id: proposal.proposal_id,
        action_id: proposal.action_id,
        target_entity: proposal.target_entity,
        actor_id: proposal.actor_id,
        tenant_id: proposal.tenant_id,
        site_id: proposal.site_id,
        session_id: proposal.session_id,
        state: "SUCCEEDED",
        canonical_args_digest: proposal.canonical_args_digest,
        challenge_used: true,
        created_at_utc: new Date().toISOString(),
        updated_at_utc: new Date().toISOString(),
        completed_at_utc: new Date().toISOString(),
        execution_attempts: 1,
        is_synthetic_demo: true,
      };
      setOperationRecord(op);
      setStatus("SUCCEEDED");
      onSuccess?.(op);
    }, 500);
  };

  const handleCancel = () => {
    setStatus("CANCELLED");
  };

  if (status === "CANCELLED") {
    return (
      <div className="w-full mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
        Đã hủy đề xuất tạo tác vụ: <span className="font-semibold text-slate-700">{proposal.preview_title}</span>.
      </div>
    );
  }

  if (status === "EXPIRED") {
    return (
      <div className="w-full mt-3 rounded-2xl border border-rose-200 bg-rose-50/60 p-4 text-xs text-rose-700 space-y-1">
        <div className="font-bold">Đề xuất đã hết hạn</div>
        <div>Thời gian hiệu lực (10 phút) đã qua. Vui lòng gửi lại yêu cầu để tạo đề xuất mới.</div>
      </div>
    );
  }

  if (status === "SUCCEEDED" && operationRecord) {
    return (
      <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 animate-fadeIn">
        {/* Banner Success */}
        <div className="p-4 sm:p-5 bg-gradient-to-r from-emerald-900 via-teal-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="size-8 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 flex items-center justify-center font-bold text-sm">
              ✓
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight text-white">
                  Đã tạo Đề xuất Tác vụ (Biên nhận Mô phỏng)
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                  SUCCEEDED
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Biên nhận đã được lưu vào nhật ký phiên an toàn
              </p>
            </div>
          </div>

          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-emerald-200 border border-white/20 backdrop-blur font-mono self-start sm:self-auto">
            {operationRecord.operation_id}
          </span>
        </div>

        <div className="p-4 sm:p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
              <span className="text-[11px] font-medium text-slate-400 block">Mã vận hành (Operation ID)</span>
              <span className="text-xs font-bold text-slate-900 font-mono block mt-0.5">{operationRecord.operation_id}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
              <span className="text-[11px] font-medium text-slate-400 block">Đối tượng chứng từ gắn kèm</span>
              <span className="text-xs font-bold text-slate-800 font-mono block mt-0.5">{operationRecord.target_entity}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60 sm:col-span-2">
              <span className="text-[11px] font-medium text-slate-400 block">Nội dung nhiệm vụ</span>
              <span className="text-xs font-bold text-slate-900 block mt-0.5">{proposal.preview_title}</span>
            </div>
          </div>

          {/* Safety footnote */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-slate-600 text-[11px] flex items-center justify-between">
            <span>✓ Trạng thái: Hoàn tất mô phỏng an toàn. Chưa ghi đè cơ sở dữ liệu thật.</span>
            <span className="font-mono text-slate-400">{new Date(operationRecord.completed_at_utc!).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Header Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-blue-900 via-indigo-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="financial_health" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Đề xuất Khởi tạo Tác vụ Theo dõi (L4)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                Awaiting Confirmation
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Kiểm tra thông tin chi tiết và xác nhận bằng nút bấm tường minh
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-slate-200 border border-white/20 backdrop-blur font-mono">
            Hết hạn sau: {formatTimer(timeLeft)}
          </span>
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Field Level Changes */}
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-700">
            Chi tiết các trường thông tin sẽ được thiết lập:
          </div>
          <div className="rounded-xl border border-slate-200/80 bg-white divide-y divide-slate-100 text-xs overflow-hidden">
            {proposal.preview_diff.map((diff) => (
              <div key={diff.field_name} className="flex items-center justify-between p-3 hover:bg-[#F9FBFC] transition-colors">
                <span className="text-slate-500 font-medium">{diff.field_name}</span>
                <span className="font-mono font-bold text-slate-900">{diff.new_value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Note */}
        <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/70 text-amber-900 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-amber-600 font-bold">ℹ</span>
            <span>Hệ thống chỉ thực thi khi bạn bấm nút xác nhận bên dưới. Tin nhắn chat không có quyền tự kích hoạt.</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
          <span className="text-[11px] text-slate-400">
            Yêu cầu xác nhận từ kế toán viên
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={status === "SUBMITTING"}
              onClick={handleCancel}
              className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-2xs transition-all cursor-pointer disabled:opacity-50"
            >
              Hủy bỏ
            </button>
            <button
              type="button"
              disabled={status === "SUBMITTING"}
              onClick={handleConfirm}
              className="px-4 py-2 rounded-xl text-white text-xs font-bold shadow-2xs transition-all cursor-pointer disabled:opacity-50 flex items-center gap-2 hover:opacity-95"
              style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
            >
              {status === "SUBMITTING" ? (
                <>
                  <span className="size-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang xử lý...</span>
                </>
              ) : (
                <span>✓ Xác nhận Tạo việc</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
