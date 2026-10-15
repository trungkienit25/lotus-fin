import React, { useState, useEffect } from "react";
import type { L4ActionProposal, L4OperationRecord } from "../actions/l4MutationContracts";

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
      { field_name: "title", old_value: null, new_value: initialTitle, description: "Tên công việc theo dõi" },
      { field_name: "due_date", old_value: null, new_value: "2026-10-25", description: "Hạn xử lý (7 ngày)" },
      { field_name: "priority", old_value: null, new_value: "MEDIUM", description: "Mức ưu tiên mặc định" },
    ],
    expires_at_utc: new Date(Date.now() + 10 * 60 * 1000).toISOString(), // 10 minutes
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
        operation_id: `op-sim-${Date.now().toString(36).toUpperCase()}`,
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
    }, 600);
  };

  const handleCancel = () => {
    setStatus("CANCELLED");
  };

  if (status === "CANCELLED") {
    return (
      <div className="w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500 my-2">
        Đã hủy đề xuất tạo tác vụ: <span className="font-semibold text-slate-700">{proposal.preview_title}</span>.
      </div>
    );
  }

  if (status === "EXPIRED") {
    return (
      <div className="w-full rounded-2xl border border-rose-200 bg-rose-50/60 p-4 text-xs text-rose-700 my-2 space-y-1">
        <div className="font-bold">Đề xuất đã hết hạn</div>
        <div>Thời gian hiệu lực (10 phút) đã qua. Vui lòng yêu cầu lại để sinh đề xuất mới có giá trị.</div>
      </div>
    );
  }

  if (status === "SUCCEEDED" && operationRecord) {
    return (
      <div className="w-full rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3 my-2 animate-fadeIn">
        <div className="flex items-center justify-between border-b border-emerald-100 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="size-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">
              ✓
            </span>
            <h4 className="text-xs sm:text-sm font-bold text-emerald-950">
              Đã tạo tác vụ theo dõi (Mô phỏng thành công)
            </h4>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            DEMO RECEIPT
          </span>
        </div>

        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between py-1 border-b border-emerald-100/60">
            <span className="text-slate-500">Mã vận hành (Operation ID):</span>
            <span className="font-mono font-bold text-slate-800">{operationRecord.operation_id}</span>
          </div>
          <div className="flex justify-between py-1 border-b border-emerald-100/60">
            <span className="text-slate-500">Đối tượng liên kết:</span>
            <span className="font-mono text-slate-700">{operationRecord.target_entity}</span>
          </div>
          <div className="flex justify-between py-1 border-b border-emerald-100/60">
            <span className="text-slate-500">Nội dung công việc:</span>
            <span className="font-semibold text-slate-900">{proposal.preview_title}</span>
          </div>
          <div className="flex justify-between py-1">
            <span className="text-slate-500">Thời điểm ghi nhận:</span>
            <span className="text-slate-600">{new Date(operationRecord.completed_at_utc!).toLocaleTimeString()}</span>
          </div>
        </div>

        <div className="text-[10px] text-amber-700 bg-amber-50/80 p-2 rounded-xl border border-amber-200/60">
          Lưu ý an toàn: Tác vụ đã được ghi nhận trong phiên mô phỏng an toàn. Chưa tác động trực tiếp vào Task DocType trên máy chủ ERPNext.
        </div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl border border-blue-200 bg-white p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3.5 my-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
              Đề xuất tác vụ (L4 Proposal)
            </span>
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
              MÔ PHỎNG AN TOÀN
            </span>
          </div>
          <h4 className="text-xs sm:text-sm font-bold text-slate-900">
            {proposal.preview_title}
          </h4>
        </div>

        <div className="text-right text-[11px] text-slate-500">
          <div>Hết hạn sau: <span className="font-mono font-bold text-rose-600">{formatTimer(timeLeft)}</span></div>
          <div className="font-mono text-[9px] text-slate-400">ID: {proposal.proposal_id}</div>
        </div>
      </div>

      {/* Field Level Changes */}
      <div className="space-y-1.5">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Dữ liệu sẽ được thiết lập:
        </div>
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 divide-y divide-slate-100 text-xs overflow-hidden">
          {proposal.preview_diff.map((diff) => (
            <div key={diff.field_name} className="flex items-center justify-between p-2.5">
              <span className="text-slate-500 font-medium">{diff.description}</span>
              <span className="font-mono font-bold text-slate-800">{diff.new_value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Explicit User Confirmation Actions */}
      <div className="pt-2 flex items-center justify-between gap-3 border-t border-slate-100">
        <span className="text-[10px] text-slate-400 italic">
          Bấm xác nhận tường minh để thực thi
        </span>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={status === "SUBMITTING"}
            onClick={handleCancel}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            disabled={status === "SUBMITTING"}
            onClick={handleConfirm}
            className="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
          >
            {status === "SUBMITTING" ? (
              <>
                <span className="size-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Đang tạo...</span>
              </>
            ) : (
              <span>Xác nhận tạo việc</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
