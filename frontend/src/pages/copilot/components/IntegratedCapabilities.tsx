import React, { useEffect, useRef, useState } from "react";
import { callIntegration } from "../actions/copilotIntegrationClient.ts";
import { L4ProposalReviewCard, L4ExecutionStatusPanel } from "../actions/L4MutationPanel.tsx";
import { L5ActionPreviewPanel } from "../l5/L5ActionPreviewPanel.tsx";
import { PastFinalDueView } from "../actions/PastFinalDueView.tsx";
import { mapOverdueView } from "../actions/overdueViewMapper.ts";
import type { L4ActionProposal, L4OperationRecord } from "../actions/l4MutationContracts.ts";
import type { L5ProposalPreview } from "../l5/l5Types.ts";
import type { PastFinalDueResponseVm } from "../actions/pastFinalDueTypes.ts";

export function IntegratedCapabilities({ profile, feature, draft = "" }: {
  profile: "CORE" | "DEMO"; feature: "L4" | "L5" | "V1"; draft?: string;
}) {
  const [proposal, setProposal] = useState<L4ActionProposal | null>(null);
  const [operation, setOperation] = useState<L4OperationRecord | null>(null);
  const [policy, setPolicy] = useState<L5ProposalPreview | null>(null);
  const [overdue, setOverdue] = useState<PastFinalDueResponseVm | null>(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("Theo dõi hóa đơn");
  const [description, setDescription] = useState(draft);
  const [dueDate, setDueDate] = useState("");
  const [actionName, setActionName] = useState("l5.doc.submit_sales_invoice.v1");
  const alive = useRef(true);
  const lock = useRef(false);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  async function run(action: string, payload: Record<string, unknown> = {}) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setNotice("");
    try {
      const result = await callIntegration(profile, action, { request_id: crypto.randomUUID(), ...payload }, action === "l5_review" ? actionName : undefined);
      if (!alive.current) return;
      const d = result.data;
      setNotice(d.error_message || d.message || d.reason_code || d.source_label || "");
      if (d.proposal) setProposal(d.proposal);
      if (d.operation) { setOperation(d.operation); setProposal(null); }
      if (action === "l4_cancel" && d.success) setProposal(null);
      if (action === "l5_review" && result.status === 200) setPolicy(d);
      if (action === "past_final_due" && d.data) setOverdue(mapOverdueView(d.data));
    } catch { if (alive.current) { setProposal(null); setNotice("UNAVAILABLE — xác minh phiên, kết nối hoặc nguồn thất bại. Không xác nhận thành công."); } }
    finally { lock.current = false; if (alive.current) setBusy(false); }
  }
  return <div className="flex-1 overflow-y-auto min-w-0 p-3 space-y-3" data-testid="integrated-capabilities">
    <p className="text-sm font-semibold">{feature} · {profile === "DEMO" ? "DEMO_ONLY — dữ liệu giả, thao tác mô phỏng" : "AWAITING_DATA — N0 BLOCKED"}</p>
    {feature === "L4" && <>
      <p className="text-xs">Chuẩn bị → xem đề xuất → xác nhận riêng → theo dõi biên nhận mô phỏng. Không tạo Task thật.</p>
      <label className="block text-sm">Tiêu đề Task<input aria-label="Task title" value={title} onChange={e => setTitle(e.target.value)} maxLength={140} className="w-full border p-2" /></label>
      <label className="block text-sm">Nội dung<textarea aria-label="Task description" value={description} onChange={e => setDescription(e.target.value)} maxLength={2000} className="w-full border p-2" /></label>
      <label className="block text-sm">Ngày theo dõi<input aria-label="Task due date" type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="w-full border p-2" /></label>
      <button disabled={busy || !description || !dueDate} onClick={() => void run("l4_propose", { action_id: "lotus.task.create", arguments: { title, description, due_date: dueDate, priority: "MEDIUM" } })} className="border rounded p-2">Xem đề xuất Task</button>
      {proposal && <L4ProposalReviewCard proposal={proposal} isSubmitting={busy} onConfirm={p => void run("l4_confirm", { proposal_id: p.proposal_id, confirmation_challenge: p.confirmation_challenge })} onCancel={p => void run("l4_cancel", { proposal_id: p.proposal_id })} />}
      {operation && <L4ExecutionStatusPanel operation={operation} state={operation.state} onReconcile={id => void run("l4_reconcile", { operation_id: id })} />}
      {operation && <button disabled={busy} onClick={() => void run("l4_status", { operation_id: operation.operation_id })}>Làm mới trạng thái mô phỏng</button>}
    </>}
    {feature === "L5" && <>
      <p className="text-xs">Đánh giá tác động và trạng thái phê duyệt. Email, submit, cancel, payment và scheduler đều không thực thi.</p>
      <select aria-label="High impact action" value={actionName} onChange={e => { setActionName(e.target.value); setPolicy(null); }} className="w-full border p-2">
        <option value="l5.doc.submit_sales_invoice.v1">Submit hóa đơn</option><option value="l5.doc.cancel_sales_invoice.v1">Cancel hóa đơn</option>
        <option value="l5.comm.send_statement_email.v1">Gửi email</option><option value="l5.pay.execute_wire_transfer.v1">Thanh toán</option>
        <option value="l5.sched.autonomous_reconciliation.v1">Scheduler</option>
      </select>
      <button disabled={busy} onClick={() => void run("l5_review")} className="border rounded p-2">Xem chính sách L5</button>
      {policy && <L5ActionPreviewPanel proposal={policy} executionResult={null} isExecuting={false} onConfirm={() => {}} onCancel={() => setPolicy(null)} />}
    </>}
    {feature === "V1" && <><button disabled={busy} onClick={() => void run("past_final_due")} className="border rounded p-2">Tìm hóa đơn đã quá hạn cuối</button>
      {overdue && <PastFinalDueView data={overdue} onRefresh={() => void run("past_final_due")} />}</>}
    {busy && <p role="status">Đang xác minh…</p>}{notice && <p role="status" className="text-sm break-words">{notice}</p>}
  </div>;
}
