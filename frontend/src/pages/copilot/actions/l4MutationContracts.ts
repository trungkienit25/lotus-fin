// L4 Confirmed Mutation Engine - Frontend Type Contracts and Standalone Module
// SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE
// Pure, standalone UI contract independent of ERPNext

export type L4ActionId = "lotus.task.create" | "lotus.note.create" | "lotus.draft_record.prepare";

export type L4OperationState =
  | "PROPOSED"
  | "AWAITING_CONFIRMATION"
  | "REJECTED"
  | "EXPIRED"
  | "CONFIRMED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED"
  | "UNKNOWN_OUTCOME"
  | "RECONCILING";

export interface L4FieldDiff {
  field_name: string;
  old_value: string | null;
  new_value: string;
  description: string;
}

export interface L4ActionProposal {
  proposal_id: string;
  action_id: L4ActionId;
  target_entity: string;
  arguments: Record<string, unknown>;
  canonical_args_digest: string;
  actor_id: string;
  session_id: string;
  tenant_id: string;
  site_id: string;
  source_version: string;
  policy_version: string;
  issued_at_utc: string;
  expires_at_utc: string;
  confirmation_challenge: string;
  preview_title: string;
  preview_diff: L4FieldDiff[];
  simulated: boolean;
}

export interface L4OperationRecord {
  operation_id: string;
  proposal_id: string;
  action_id: L4ActionId;
  target_entity: string;
  actor_id: string;
  tenant_id: string;
  site_id: string;
  session_id: string;
  state: L4OperationState;
  canonical_args_digest: string;
  challenge_used: boolean;
  created_at_utc: string;
  updated_at_utc: string;
  confirmed_at_utc?: string;
  completed_at_utc?: string;
  execution_attempts: number;
  result_data?: Record<string, unknown>;
  error_code?: string;
  error_message?: string;
  is_synthetic_demo: boolean;
  reconciliation_notes?: string;
}

export interface L4ProposalReviewProps {
  proposal: L4ActionProposal;
  isSubmitting: boolean;
  onConfirm: (proposal: L4ActionProposal) => void;
  onCancel: (proposal: L4ActionProposal) => void;
}

export interface L4ExecutionStatusProps {
  operation: L4OperationRecord | null;
  state: L4OperationState;
  errorMessage?: string;
  onReconcile?: (operationId: string) => void;
  onDismiss?: () => void;
}
