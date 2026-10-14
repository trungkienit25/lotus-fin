import React from "react";
import type { InvoiceActionTransport } from "../actions/invoiceActionController";
import type { DemoScenario } from "../demo/demoInvoiceProvider";
import { InvoiceActionPanel } from "../actions/InvoiceActionPanel";
import type { AuthenticatedActionScope } from "../../../providers/sessionScope.ts";

interface InvoiceActionsTabViewProps {
  company: string;
  contextKey?: string;
  demoProfile: "CORE" | "DEMO";
  demoScenario: DemoScenario;
  onSetDemoProfile: (profile: "CORE" | "DEMO") => void;
  onSetDemoScenario: (scenario: DemoScenario) => void;
  activeInvoiceTransport: InvoiceActionTransport;
  scope?: AuthenticatedActionScope;
  onPrepareFollowup?: (invoiceId: string) => void;
}

export const InvoiceActionsTabView: React.FC<InvoiceActionsTabViewProps> = ({
  company,
  contextKey,
  demoProfile,
  demoScenario,
  onSetDemoProfile,
  onSetDemoScenario,
  activeInvoiceTransport,
  scope,
  onPrepareFollowup,
}) => {
  const scopeKey = `${scope?.actor ?? "anonymous"}:${scope?.sessionEpoch ?? ""}:${company || "lotus-fin"}:${contextKey || "default"}:${demoProfile}:${demoScenario}`;

  return (
    <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 max-w-4xl mx-auto w-full">
      {/* Profile Switcher Card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-gray-900">Sales Invoice Actions Profile</h2>
            <p className="text-xs text-gray-500">
              Select between Frappe Core HTTP transport and Isolated Synthetic Demo.
            </p>
          </div>
          <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-xl">
            <button
              type="button"
              aria-label="Select CORE profile"
              aria-pressed={demoProfile === "CORE"}
              onClick={() => onSetDemoProfile("CORE")}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                demoProfile === "CORE" ? "bg-white text-blue-700 shadow-xs" : "text-gray-500 hover:text-gray-900"
              }`}
            >
              CORE (Frappe HTTP)
            </button>
            <button
              type="button"
              aria-label="Select DEMO profile"
              aria-pressed={demoProfile === "DEMO"}
              onClick={() => onSetDemoProfile("DEMO")}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                demoProfile === "DEMO" ? "bg-amber-500 text-white shadow-xs" : "text-gray-500 hover:text-gray-900"
              }`}
            >
              DEMO (Synthetic)
            </button>
          </div>
        </div>

        {demoProfile === "CORE" ? (
          <div className="p-3 rounded-xl border border-blue-200 bg-blue-50/70 text-blue-900 text-xs flex items-start gap-2">
            <span className="text-base" aria-hidden="true">ℹ️</span>
            <div>
              <div className="font-semibold">CORE Production Transport Active</div>
              <div className="text-blue-700 mt-0.5">
                Connects directly to Frappe Core RPC endpoints (<code>/api/method/lotus_fin.api.invoice_actions_api.*</code>). Since native financial authority (N0) is blocked, queries truthfully return <code className="bg-blue-100 px-1 py-0.5 rounded">CAPABILITY_DISABLED</code> (503). Zero synthetic data leakage.
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="p-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 text-xs flex items-start gap-2">
              <span className="text-base" aria-hidden="true">⚠️</span>
              <div>
                <div className="font-semibold uppercase tracking-wide text-amber-800">
                  DEMO DATA (ISOLATED SYNTHETIC PROFILE)
                </div>
                <div className="text-amber-700 mt-0.5">
                  Fictional records strictly isolated from production. No production data or ERPNext dependencies. Bounded synthetic authority.
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-3">
              <label htmlFor="demo-scenario-select" className="text-xs font-bold text-gray-700 shrink-0">
                Test Scenario:
              </label>
              <select
                id="demo-scenario-select"
                aria-label="Test Scenario"
                value={demoScenario}
                onChange={(e) => onSetDemoScenario(e.target.value as DemoScenario)}
                className="text-xs font-semibold bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1 text-gray-800 focus:outline-hidden w-full sm:w-auto max-w-full"
              >
                <option value="NORMAL">NORMAL (Complete Search → Explicit Select → Open)</option>
                <option value="PARTIAL">PARTIAL (Partial results — Selection disabled)</option>
                <option value="EMPTY">EMPTY (Zero matching invoices)</option>
                <option value="FORBIDDEN">FORBIDDEN (403 Permission Denied)</option>
                <option value="EXPIRED">EXPIRED (Session / Context expired)</option>
                <option value="STALE">STALE (Version mismatch / Context changed)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Panel Component */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 sm:p-5 shadow-xs">
        <InvoiceActionPanel
          companyCandidate={company || "Lotus Fin Core"}
          scopeKey={scopeKey}
          transport={activeInvoiceTransport}
          allowDemoSource={demoProfile === "DEMO"}
          scope={scope}
          onPrepareFollowup={onPrepareFollowup}
        />
      </div>
    </div>
  );
};
