import React from "react";
import {
  L4ActionProposal,
  L4OperationRecord,
  L4OperationState,
  L4ProposalReviewProps,
  L4ExecutionStatusProps,
} from "./l4MutationContracts";

/**
 * Standalone L4 Proposal Review and Confirmation Card.
 * Renders human-readable proposal, canonical field-level diffs,
 * expiration warning, and explicit one-use confirmation button.
 */
export const L4ProposalReviewCard: React.FC<L4ProposalReviewProps> = ({
  proposal,
  isSubmitting,
  onConfirm,
  onCancel,
}) => {
  const isExpired = new Date(proposal.expires_at_utc).getTime() <= Date.now();

  return (
    <div className="rounded-lg border border-blue-200 bg-white p-5 shadow-sm dark:border-blue-900/50 dark:bg-gray-900">
      <div className="mb-3 flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
        <div>
          <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 dark:bg-blue-950 dark:text-blue-300">
            L4 Proposed Action
          </span>
          {proposal.simulated && (
            <span className="ml-2 inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-950 dark:text-amber-300">
              SYNTHETIC DEMO
            </span>
          )}
          <h4 className="mt-1 text-base font-semibold text-gray-900 dark:text-gray-100">
            {proposal.preview_title}
          </h4>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>Expires: {new Date(proposal.expires_at_utc).toLocaleTimeString()}</div>
          <div className="font-mono text-[10px] text-gray-400">ID: {proposal.proposal_id.slice(0, 12)}...</div>
        </div>
      </div>

      <div className="mb-4">
        <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
          Field-Level Changes
        </h5>
        <div className="divide-y divide-gray-100 rounded border border-gray-200 bg-gray-50/50 text-sm dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-950/40">
          {proposal.preview_diff.map((diff) => (
            <div key={diff.field_name} className="flex items-start justify-between p-2.5">
              <div className="w-1/3 font-medium text-gray-700 dark:text-gray-300">
                {diff.field_name}
              </div>
              <div className="w-2/3">
                <div className="font-mono text-xs text-gray-900 dark:text-gray-100">
                  {diff.new_value}
                </div>
                <div className="text-[11px] text-gray-500">{diff.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {isExpired ? (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          This proposal has expired. Please re-initiate the action to generate a fresh proposal.
        </div>
      ) : (
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => onCancel(proposal)}
            className="rounded-md border border-gray-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => onConfirm(proposal)}
            className="rounded-md bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? "Confirming..." : "Confirm & Execute"}
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * Standalone L4 Execution and Reconciliation Status Panel.
 * Handles progress, terminal success, failed attempts and UNKNOWN_OUTCOME states.
 */
export const L4ExecutionStatusPanel: React.FC<L4ExecutionStatusProps> = ({
  operation,
  state,
  errorMessage,
  onReconcile,
  onDismiss,
}) => {
  return (
    <div className="mt-3 rounded-lg border border-gray-200 bg-white p-4 text-sm shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-2">
        <span className="font-medium text-gray-900 dark:text-gray-100">Execution Status</span>
        <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold ${
          state === "SUCCEEDED" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" :
          state === "UNKNOWN_OUTCOME" ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" :
          state === "FAILED" || state === "REJECTED" ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" :
          "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
        }`}>
          {operation?.is_synthetic_demo && state === "SUCCEEDED" ? "SIMULATED_SUCCEEDED" : state}
        </span>
      </div>

      {operation?.is_synthetic_demo && (
        <div className="mb-2 text-xs font-semibold text-amber-600 dark:text-amber-400">
          [SYNTHETIC DEMO RECORD - VISIBLY ISOLATED]
        </div>
      )}

      {operation && (
        <div className="space-y-1 py-1 font-mono text-xs text-gray-600 dark:text-gray-400">
          <div>Operation: {operation.operation_id}</div>
          <div>Entity: {operation.target_entity}</div>
          {operation.completed_at_utc && (
            <div>{operation.is_synthetic_demo ? "Simulated receipt" : "Completed"}: {new Date(operation.completed_at_utc).toLocaleTimeString()}</div>
          )}
        </div>
      )}

      {errorMessage && (
        <div className="mt-2 rounded bg-red-50 p-2 text-xs text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {errorMessage}
        </div>
      )}

      {state === "UNKNOWN_OUTCOME" && (
        <div className="mt-3 rounded-md bg-amber-50 p-3 text-xs text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          <p className="font-semibold">Ambiguous State Detected</p>
          <p className="mt-1">
            Network response was lost during execution. The system must inspect and reconcile before any retry.
          </p>
          {onReconcile && operation && (
            <button
              type="button"
              onClick={() => onReconcile(operation.operation_id)}
              className="mt-2 rounded bg-amber-600 px-3 py-1 text-xs font-medium text-white hover:bg-amber-500"
            >
              Inspect & Reconcile Outcome
            </button>
          )}
        </div>
      )}

      {onDismiss && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
