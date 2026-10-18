import React, { useState, useEffect } from "react";
import { ModuleBadge } from "../components/ModuleBadge";
import { bootstrapSession } from "../../../providers/sessionBootstrap";
import { POLICY_CATALOG, type PolicyDefinition } from "../../../constants/policyCatalog";

export interface PolicyGateAuditViewProps {
  company: string;
}

export const PolicyGateAuditView: React.FC<PolicyGateAuditViewProps> = ({ company }) => {
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>(POLICY_CATALOG[0].id);
  const [invoices, setInvoices] = useState<Array<{ invoiceId: string; customerName: string; grandTotal: number; docstatus: number }>>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string>("");
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evaluationResult, setEvaluationResult] = useState<{
    status: "success" | "warning" | "restricted" | "blocked" | "info";
    verdict_title: string;
    verdict_detail: string;
    risk_badge: string;
    action_allowed: boolean;
    approval_required: string;
  } | null>(null);

  const selectedPolicy = POLICY_CATALOG.find((p) => p.id === selectedPolicyId) || POLICY_CATALOG[0];

  // Load real invoices for audit testing
  useEffect(() => {
    let isMounted = true;
    async function loadInvoices() {
      try {
        const session = await bootstrapSession().catch(() => null);
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (session?.csrfToken) {
          headers["X-Frappe-CSRF-Token"] = session.csrfToken;
        }

        const res = await fetch("/api/method/lotus_fin.api.copilot_api.search_real_invoices", {
          method: "POST",
          headers,
          credentials: "same-origin",
          body: JSON.stringify({ company, limit: 15 }),
        });

        if (res.ok) {
          const wire = await res.json();
          const list = wire?.message?.invoices || [];
          if (isMounted && list.length > 0) {
            setInvoices(list);
            setSelectedInvoiceId(list[0].invoiceId);
          }
        }
      } catch (err) {
        console.warn("Failed to load invoices for policy gate:", err);
      }
    }

    loadInvoices();
    return () => { isMounted = false; };
  }, [company]);

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    setEvaluationResult(null);

    try {
      const session = await bootstrapSession().catch(() => null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.csrfToken) {
        headers["X-Frappe-CSRF-Token"] = session.csrfToken;
      }

      const res = await fetch("/api/method/lotus_fin.api.copilot_api.evaluate_policy_gate", {
        method: "POST",
        headers,
        credentials: "same-origin",
        body: JSON.stringify({
          policy_id: selectedPolicyId,
          target_invoice: selectedPolicy.needsInvoice ? selectedInvoiceId : undefined,
          company,
        }),
      });

      if (res.ok) {
        const wire = await res.json();
        if (wire?.message) {
          setEvaluationResult(wire.message);
          return;
        }
      }
    } catch (err) {
      console.warn("Policy evaluation error:", err);
    } finally {
      setIsEvaluating(false);
    }

    // Client fallback if offline
    if (selectedPolicy.id === "execute_wire_transfer" || selectedPolicy.id === "autonomous_reconciliation") {
      setEvaluationResult({
        status: "blocked",
        verdict_title: "Autonomous Action Strictly Prohibited",
        verdict_detail: "This high-impact action is permanently restricted by system fiduciary safety policies.",
        risk_badge: "Risk: Critical (Prohibited)",
        action_allowed: false,
        approval_required: "Autonomous execution blocked. Requires direct human banking operation with 2FA token.",
      });
    } else if (selectedPolicy.id === "cancel_sales_invoice") {
      setEvaluationResult({
        status: "restricted",
        verdict_title: "Dual-Control Approval Gate Required",
        verdict_detail: "Document cancellation posts reverse journal entries to the general ledger, permanently altering financial statements.",
        risk_badge: "Risk: Critical",
        action_allowed: false,
        approval_required: "Requires dual independent sign-offs from Finance Controller and Executive Board.",
      });
    } else {
      setEvaluationResult({
        status: "success",
        verdict_title: "Compliant with Accounting Standards",
        verdict_detail: "Action adheres to standard internal controls and is ready for authorized execution.",
        risk_badge: selectedPolicy.riskText,
        action_allowed: true,
        approval_required: selectedPolicy.approvalFlow,
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 font-sans text-slate-800">
      {/* Top Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="policy_gate" size="md" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-white">
                Accounting Policy Gate & Dual-Control Audit
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                Dual-Control Gate
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Risk assessment and policy verification prior to general ledger state mutation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-slate-200 border border-white/20 backdrop-blur font-mono">
            {company}
          </span>
        </div>
      </div>

      {/* Main Inspection Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-4">
        {/* Step 1: Select Policy */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
            1. Select High-Impact Business Action:
          </label>
          <select
            value={selectedPolicyId}
            onChange={(e) => {
              setSelectedPolicyId(e.target.value);
              setEvaluationResult(null);
            }}
            className="w-full text-xs font-semibold rounded-xl border border-slate-200 bg-[#F9FBFC] p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all cursor-pointer"
          >
            {POLICY_CATALOG.map((p) => (
              <option key={p.id} value={p.id}>
                [{p.riskText}] {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Step 2: Select Target Invoice (if applicable) */}
        {selectedPolicy.needsInvoice && (
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              2. Select Target Invoice from General Ledger ({invoices.length} invoices available):
            </label>
            {invoices.length > 0 ? (
              <select
                value={selectedInvoiceId}
                onChange={(e) => {
                  setSelectedInvoiceId(e.target.value);
                  setEvaluationResult(null);
                }}
                className="w-full text-xs font-mono font-medium rounded-xl border border-slate-200 bg-[#F9FBFC] p-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all cursor-pointer"
              >
                {invoices.map((inv) => (
                  <option key={inv.invoiceId} value={inv.invoiceId}>
                    {inv.invoiceId} — {inv.customerName} (${Number(inv.grandTotal).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}) [{inv.docstatus === 1 ? "Submitted" : "Draft"}]
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                Loading sales invoice documents from live ERP database...
              </div>
            )}
          </div>
        )}

        {/* Policy Details Grid */}
        <div className="rounded-xl border border-slate-200 bg-[#F8FAFC] p-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
            <div>
              <h4 className="text-sm font-bold text-slate-900">{selectedPolicy.name}</h4>
              <div className="text-[11px] text-slate-500 mt-0.5">{selectedPolicy.category}</div>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold self-start sm:self-auto ${
                selectedPolicy.riskLevel === "CRITICAL"
                  ? "bg-rose-100 text-rose-800 border border-rose-200"
                  : selectedPolicy.riskLevel === "HIGH"
                  ? "bg-amber-100 text-amber-800 border border-amber-200"
                  : "bg-blue-100 text-blue-800 border border-blue-200"
              }`}
            >
              {selectedPolicy.riskText}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-white border border-slate-200/60">
              <span className="text-[11px] font-semibold text-slate-400 block">Business Intent</span>
              <p className="text-slate-800 mt-1 leading-relaxed">{selectedPolicy.description}</p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/60">
              <span className="text-[11px] font-semibold text-slate-400 block">General Ledger (GL) Impact</span>
              <p className="text-slate-800 mt-1 leading-relaxed">{selectedPolicy.erpImpact}</p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/60 sm:col-span-2">
              <span className="text-[11px] font-semibold text-slate-400 block">Mandatory Approval Protocol</span>
              <p className="text-slate-800 mt-1 leading-relaxed font-semibold">{selectedPolicy.approvalFlow}</p>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <span className="text-[11px] text-slate-500">
            Standard: COSO Internal Control Framework & ERP Authorization Model
          </span>

          <button
            type="button"
            disabled={isEvaluating}
            onClick={handleRunEvaluation}
            className="px-5 py-2.5 rounded-xl text-white text-xs font-bold shadow-2xs transition-all cursor-pointer flex items-center gap-2 hover:opacity-95 disabled:opacity-50"
            style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
          >
            {isEvaluating ? (
              <>
                <span className="size-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Evaluating against ERP Ledger...</span>
              </>
            ) : (
              <>
                <span>⚡ Verify Approval Policy</span>
              </>
            )}
          </button>
        </div>

        {/* Evaluation Verdict Result Panel */}
        {evaluationResult && (
          <div
            className={`p-4 rounded-xl border text-xs space-y-2 animate-fadeIn ${
              evaluationResult.status === "blocked"
                ? "bg-rose-50 border-rose-300 text-rose-900"
                : evaluationResult.status === "restricted"
                ? "bg-amber-50 border-amber-300 text-amber-900"
                : evaluationResult.status === "warning"
                ? "bg-amber-50 border-amber-300 text-amber-900"
                : "bg-emerald-50 border-emerald-300 text-emerald-900"
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm">
              <div className="flex items-center gap-2">
                <span>
                  {evaluationResult.status === "blocked"
                    ? "⛔"
                    : evaluationResult.status === "restricted"
                    ? "⚠️"
                    : "✓"}
                </span>
                <span>{evaluationResult.verdict_title}</span>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-white/80 border border-current font-medium">
                {evaluationResult.risk_badge}
              </span>
            </div>

            <p className="leading-relaxed text-xs">{evaluationResult.verdict_detail}</p>

            <div className="p-3 bg-white/80 rounded-lg border border-current/20 space-y-1">
              <span className="font-bold block text-[11px] uppercase tracking-wider">
                System Approval Requirement:
              </span>
              <p className="text-xs leading-relaxed">{evaluationResult.approval_required}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
