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
  return (
    <div className="flex-1 overflow-y-auto min-w-0 p-4 sm:p-6 space-y-5 font-sans" data-testid="integrated-capabilities">
      {/* Banner */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Impact Audit & Policy Safety Gate</span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
              {feature} Engine
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {profile === "DEMO"
              ? "Safe simulation testing mode — isolated from production ledger"
              : "Dual-control compliance — enterprise accounting policy adherence"}
          </p>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 font-mono self-start sm:self-auto">
          {profile === "DEMO" ? "Simulation" : "ERP Live"}
        </span>
      </div>

      {feature === "L4" && (
        <div className="space-y-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
          <div>
            <h3 className="text-sm font-bold text-slate-800">Initialize Receivables Follow-up Task</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Standard workflow: Prepare Content → Preview Mutations → Dual Authorization.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Task Title
              </label>
              <input
                aria-label="Task title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={140}
                className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all"
                placeholder="e.g. Follow up on overdue receivables..."
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Description & Context
              </label>
              <textarea
                aria-label="Task description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={2000}
                rows={3}
                className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all resize-none"
                placeholder="Detailed follow-up instructions..."
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Due Date
              </label>
              <input
                aria-label="Task due date"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all"
              />
            </div>

            <div className="pt-2 flex items-center justify-end">
              <button
                disabled={busy || !description || !dueDate}
                onClick={() =>
                  void run("l4_propose", {
                    action_id: "lotus.task.create",
                    arguments: { title, description, due_date: dueDate, priority: "MEDIUM" },
                  })
                }
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-2xs"
              >
                {busy ? "Processing..." : "Generate Task Proposal"}
              </button>
            </div>
          </div>

          {proposal && (
            <div className="pt-3 border-t border-slate-100">
              <L4ProposalReviewCard
                proposal={proposal}
                isSubmitting={busy}
                onConfirm={(p) =>
                  void run("l4_confirm", {
                    proposal_id: p.proposal_id,
                    confirmation_challenge: p.confirmation_challenge,
                  })
                }
                onCancel={(p) => void run("l4_cancel", { proposal_id: p.proposal_id })}
              />
            </div>
          )}

          {operation && (
            <div className="space-y-3 pt-3 border-t border-slate-100">
              <L4ExecutionStatusPanel
                operation={operation}
                state={operation.state}
                onReconcile={(id) => void run("l4_reconcile", { operation_id: id })}
              />
              <button
                disabled={busy}
                onClick={() => void run("l4_status", { operation_id: operation.operation_id })}
                className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition-all cursor-pointer"
              >
                Làm mới trạng thái
              </button>
            </div>
          )}
        </div>
      )}

      {feature === "L5" && (
        <div className="space-y-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
          <div>
            <h3 className="text-sm font-bold text-slate-800">High-Impact Control Gateway (L5 Dual-Control Gate)</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Risk assessment and policy validation. Actions with irreversible financial impact (fund disbursement, document cancellation) require multi-tier authorization.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Target High-Impact Action
              </label>
              <select
                aria-label="High impact action"
                value={actionName}
                onChange={(e) => {
                  setActionName(e.target.value);
                  setPolicy(null);
                }}
                className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all cursor-pointer"
              >
                <option value="l5.doc.submit_sales_invoice.v1">Submit Sales Invoice (Formal Ledger Booking)</option>
                <option value="l5.doc.cancel_sales_invoice.v1">Cancel Sales Invoice (Reversal)</option>
                <option value="l5.comm.send_statement_email.v1">Transmit Statement of Accounts via Email</option>
                <option value="l5.pay.execute_wire_transfer.v1">Execute Bank Wire Transfer</option>
                <option value="l5.sched.autonomous_reconciliation.v1">Trigger Automated General Ledger Reconciliation</option>
              </select>
            </div>

            <div className="pt-2 flex items-center justify-end">
              <button
                disabled={busy}
                onClick={() => void run("l5_review")}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-2xs"
              >
                {busy ? "Evaluating..." : "Review Policy Rules"}
              </button>
            </div>
          </div>

          {policy && (
            <div className="pt-3 border-t border-slate-100">
              <L5ActionPreviewPanel
                proposal={policy}
                executionResult={null}
                isExecuting={false}
                onConfirm={() => {}}
                onCancel={() => setPolicy(null)}
              />
            </div>
          )}
        </div>
      )}

      {feature === "V1" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              disabled={busy}
              onClick={() => void run("past_final_due")}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-2xs"
            >
              {busy ? "Searching..." : "Find Past-Final-Due Invoices"}
            </button>
          </div>
          {overdue && <PastFinalDueView data={overdue} onRefresh={() => void run("past_final_due")} />}
        </div>
      )}

      {busy && (
        <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs flex items-center gap-2">
          <div className="size-2 rounded-full bg-blue-600 animate-ping"></div>
          <span>Verifying compliance policy and reconciling records...</span>
        </div>
      )}

      {notice && (
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs break-words">
          {notice}
        </div>
      )}
    </div>
  );
}
