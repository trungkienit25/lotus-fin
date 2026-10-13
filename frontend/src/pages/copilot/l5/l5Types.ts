/**
 * L5 Action Types and Interfaces - Lotus Fin P6-2
 */

export type L5ActionFamily =
  | "DOCUMENT_SUBMIT"
  | "DOCUMENT_CANCEL"
  | "EXTERNAL_EMAIL_SEND"
  | "PAYMENT_REQUEST"
  | "PAYMENT_EXECUTION"
  | "SCHEDULED_AUTONOMOUS_ACTION";

export type L5RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type L5ApprovalLevel =
  | "SINGLE_USER_CONFIRM"
  | "DUAL_CONTROL_M_OF_N"
  | "FINANCE_OFFICER_GATE"
  | "BOARD_OR_EXECUTIVE_GATE"
  | "BLOCKED_DISALLOWED";

export type L5ProposalState =
  | "DRAFT_PROPOSED"
  | "APPROVAL_PENDING"
  | "APPROVED"
  | "APPROVAL_RESERVED"
  | "EXECUTING"
  | "COMMITTED"
  | "FAILED_ROLLED_BACK"
  | "UNKNOWN_OUTCOME"
  | "RECONCILED"
  | "REJECTED"
  | "EXPIRED"
  | "REVOKED";

export interface L5TargetSpec {
  doctype: string;
  doc_id: string;
  expected_docstatus?: number;
  resource_version: string;
  company: string;
}

export interface L5ProposalPreview {
  status: "PROPOSAL_READY" | "DENIED";
  proposal_id?: string;
  action_name?: string;
  family?: L5ActionFamily;
  risk_level?: L5RiskLevel;
  required_approval_level?: L5ApprovalLevel;
  consequence_description?: string;
  is_reversible?: boolean;
  review_challenge?: string;
  target?: L5TargetSpec;
  expires_in_seconds?: number;
  reason_code?: string;
  details?: Record<string, unknown>;
}

export interface L5ExecutionResult {
  status: "COMMITTED" | "UNKNOWN_OUTCOME" | "FAILED" | "ALREADY_COMMITTED" | "DENIED";
  operation_id?: string;
  target_identity?: string;
  receipt?: Record<string, unknown>;
  reason_code?: string;
  message?: string;
  reconciliation_required?: boolean;
}
