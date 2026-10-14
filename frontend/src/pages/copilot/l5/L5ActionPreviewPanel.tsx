import React from "react";
import type { L5ProposalPreview, L5ExecutionResult } from "./l5Types.ts";

export interface L5ActionPreviewPanelProps {
  proposal: L5ProposalPreview | null;
  executionResult: L5ExecutionResult | null;
  isExecuting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  onReconcile?: () => void;
}

export const L5ActionPreviewPanel: React.FC<L5ActionPreviewPanelProps> = ({
  proposal,
  executionResult,
  isExecuting,
  onConfirm,
  onCancel,
  onReconcile,
}) => {
  if (!proposal) {
    return (
      <div className="p-4 border rounded-md bg-gray-50 text-gray-500 text-sm">
        No active L5 action proposed.
      </div>
    );
  }

  if (proposal.status === "DENIED") {
    return (
      <div className="p-4 border border-red-300 rounded-md bg-red-50 text-red-700 text-sm space-y-2">
        <div className="font-semibold text-base">L5 Action Blocked by Policy</div>
        <div>{proposal.action_name} · Risk: {proposal.risk_level} · Gate: {proposal.required_approval_level}</div>
        <p>{proposal.consequence_description}</p>
        <p>Side effects DISABLED · DEMO fictional policy review</p>
        <div>Reason: <code className="bg-red-100 px-1 py-0.5 rounded">{proposal.reason_code}</code></div>
        {proposal.details && (
          <div className="text-xs text-red-600 bg-white p-2 rounded border border-red-200">
            {JSON.stringify(proposal.details)}
          </div>
        )}
      </div>
    );
  }

  const isCritical = proposal.risk_level === "CRITICAL" || proposal.risk_level === "HIGH";

  return (
    <div className="p-4 border rounded-lg bg-white shadow-sm space-y-4">
      {/* Risk Badge & Action Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
            L5 High-Impact Action Proposal
          </span>
          <h3 className="text-base font-semibold text-gray-900">{proposal.action_name}</h3>
        </div>
        <div className="flex gap-2">
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              isCritical ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"
            }`}
          >
            Risk: {proposal.risk_level}
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
            Gate: {proposal.required_approval_level}
          </span>
        </div>
      </div>

      {/* Target and Consequence Box */}
      <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-amber-900 space-y-2">
        <div className="font-medium text-amber-950">Irreversible Consequence Notice:</div>
        <p className="text-xs">{proposal.consequence_description}</p>
        <div className="text-xs font-mono bg-white p-2 rounded border border-amber-200 text-gray-800">
          <div>DocType: {proposal.target?.doctype}</div>
          <div>Target ID: {proposal.target?.doc_id}</div>
          <div>Company: {proposal.target?.company}</div>
          <div>Version: {proposal.target?.resource_version}</div>
        </div>
      </div>

      {/* Execution Outcome / UNKNOWN_OUTCOME handling */}
      {executionResult && (
        <div
          className={`p-3 rounded border text-sm ${
            executionResult.status === "COMMITTED"
              ? "bg-green-50 border-green-300 text-green-800"
              : executionResult.status === "UNKNOWN_OUTCOME"
              ? "bg-purple-50 border-purple-300 text-purple-900"
              : "bg-red-50 border-red-300 text-red-800"
          }`}
        >
          <div className="font-semibold">Execution Status: {executionResult.status}</div>
          {executionResult.operation_id && (
            <div className="text-xs font-mono">Operation ID: {executionResult.operation_id}</div>
          )}
          {executionResult.message && <div className="text-xs mt-1">{executionResult.message}</div>}
          {executionResult.status === "UNKNOWN_OUTCOME" && (
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={onReconcile}
                className="px-3 py-1 bg-purple-700 text-white rounded text-xs font-semibold hover:bg-purple-800"
              >
                Reconcile Operation Status
              </button>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {!executionResult && (
        <div className="flex justify-end gap-3 pt-2 border-t">
          <button
            type="button"
            disabled={isExecuting}
            onClick={onCancel}
            className="px-3 py-1.5 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded font-medium"
          >
            Cancel Proposal
          </button>
          <button
            type="button"
            disabled={isExecuting}
            onClick={onConfirm}
            className={`px-4 py-1.5 text-sm text-white rounded font-medium ${
              isCritical ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {isExecuting ? "Executing..." : "Confirm & Execute Action"}
          </button>
        </div>
      )}
    </div>
  );
};
