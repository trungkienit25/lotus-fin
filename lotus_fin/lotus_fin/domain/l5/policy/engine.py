"""L5 Server-Side Policy Engine - Lotus Fin P6-2."""

import time
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from lotus_fin.domain.l5.models.contracts import (
    L5ActionFamily,
    L5ApprovalLevel,
    L5PolicyDecision,
    L5PolicyEvaluationResult,
    L5RiskLevel,
)
from lotus_fin.domain.l5.models.proposals import L5TargetSpec


class L5ActionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action_name: str
    family: L5ActionFamily
    description: str
    risk_level: L5RiskLevel
    required_approval_level: L5ApprovalLevel
    required_roles: List[str]
    allowed_source_doctypes: List[str]
    allowed_transitions: Dict[str, List[int]]  # doctype -> list of allowed next docstatus
    max_amount: Optional[float] = None
    allowed_currencies: Optional[List[str]] = None
    recipient_domain_allowlist: Optional[List[str]] = None
    autonomous_permitted: bool = False
    is_reversible: bool = False


class L5PolicyContext(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    actor: str
    actor_roles: List[str]
    tenant_id: str
    site: str
    authorized_company: str
    target: L5TargetSpec
    parameters: Dict[str, Any] = Field(default_factory=dict)
    current_resource_version: str
    current_docstatus: int


# Default explicit catalog of allowlisted L5 actions
L5_ACTION_CATALOG: Dict[str, L5ActionDefinition] = {
    "l5.doc.submit_sales_invoice.v1": L5ActionDefinition(
        action_name="l5.doc.submit_sales_invoice.v1",
        family=L5ActionFamily.DOCUMENT_SUBMIT,
        description="Submit an approved draft Sales Invoice into submitted status.",
        risk_level=L5RiskLevel.HIGH,
        required_approval_level=L5ApprovalLevel.FINANCE_OFFICER_GATE,
        required_roles=["Accounts User", "Accounts Manager"],
        allowed_source_doctypes=["Sales Invoice"],
        allowed_transitions={"Sales Invoice": [1]},  # 0 (draft) -> 1 (submitted)
        is_reversible=False,
    ),
    "l5.doc.cancel_sales_invoice.v1": L5ActionDefinition(
        action_name="l5.doc.cancel_sales_invoice.v1",
        family=L5ActionFamily.DOCUMENT_CANCEL,
        description="Cancel a submitted Sales Invoice.",
        risk_level=L5RiskLevel.CRITICAL,
        required_approval_level=L5ApprovalLevel.DUAL_CONTROL_M_OF_N,
        required_roles=["Accounts Manager"],
        allowed_source_doctypes=["Sales Invoice"],
        allowed_transitions={"Sales Invoice": [2]},  # 1 (submitted) -> 2 (cancelled)
        is_reversible=False,
    ),
    "l5.comm.send_statement_email.v1": L5ActionDefinition(
        action_name="l5.comm.send_statement_email.v1",
        family=L5ActionFamily.EXTERNAL_EMAIL_SEND,
        description="Send customer account statement email to allowlisted domain.",
        risk_level=L5RiskLevel.MEDIUM,
        required_approval_level=L5ApprovalLevel.SINGLE_USER_CONFIRM,
        required_roles=["Accounts User", "Accounts Manager"],
        allowed_source_doctypes=["Customer", "Sales Invoice"],
        allowed_transitions={},
        recipient_domain_allowlist=["lotusfin.internal", "clientcorp.com", "verified-domain.com"],
        is_reversible=False,
    ),
    "l5.pay.request_disbursement.v1": L5ActionDefinition(
        action_name="l5.pay.request_disbursement.v1",
        family=L5ActionFamily.PAYMENT_REQUEST,
        description="Generate a strictly typed Payment Request proposal (NOT execution).",
        risk_level=L5RiskLevel.HIGH,
        required_approval_level=L5ApprovalLevel.FINANCE_OFFICER_GATE,
        required_roles=["Accounts Manager", "Treasurer"],
        allowed_source_doctypes=["Payment Request", "Sales Invoice"],
        allowed_transitions={"Payment Request": [0, 1]},
        max_amount=100000000.0,  # 100M VND cap for request
        allowed_currencies=["VND", "USD"],
        is_reversible=False,
    ),
    "l5.pay.execute_wire_transfer.v1": L5ActionDefinition(
        action_name="l5.pay.execute_wire_transfer.v1",
        family=L5ActionFamily.PAYMENT_EXECUTION,
        description="Actual wire transfer disbursement to banking rail.",
        risk_level=L5RiskLevel.CRITICAL,
        required_approval_level=L5ApprovalLevel.BLOCKED_DISALLOWED,  # DISALLOWED IN MVP
        required_roles=["Treasurer"],
        allowed_source_doctypes=["Payment Entry"],
        allowed_transitions={"Payment Entry": [1]},
        max_amount=0.0,
        allowed_currencies=["VND"],
        is_reversible=False,
    ),
    "l5.sched.autonomous_reconciliation.v1": L5ActionDefinition(
        action_name="l5.sched.autonomous_reconciliation.v1",
        family=L5ActionFamily.SCHEDULED_AUTONOMOUS_ACTION,
        description="Autonomous background job for scheduled reconciliation.",
        risk_level=L5RiskLevel.CRITICAL,
        required_approval_level=L5ApprovalLevel.BLOCKED_DISALLOWED,  # DISALLOWED IN MVP
        required_roles=["System Manager"],
        allowed_source_doctypes=["Bank Account"],
        allowed_transitions={},
        autonomous_permitted=False,
        is_reversible=False,
    ),
}


class L5PolicyEngine:
    """Server-side policy evaluation engine enforcing fail-closed security invariants."""

    def __init__(self, catalog: Optional[Dict[str, L5ActionDefinition]] = None):
        self.catalog = catalog or L5_ACTION_CATALOG

    def evaluate_intent(self, action_name: str, context: L5PolicyContext) -> L5PolicyEvaluationResult:
        # Rule 1: Unknown action fails closed
        if action_name not in self.catalog:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.DENIED,
                reason_code="UNKNOWN_ACTION_NAME",
                risk_level=L5RiskLevel.CRITICAL,
                required_approval_level=L5ApprovalLevel.BLOCKED_DISALLOWED,
                details={"error": f"Action {action_name} is not registered in L5 allowlisted catalog"},
            )

        action_def = self.catalog[action_name]

        # Rule 2: Unapproved candidate execution blocks (PAYMENT_EXECUTION and SCHEDULED autonomous are blocked)
        if action_def.required_approval_level == L5ApprovalLevel.BLOCKED_DISALLOWED:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.CAPABILITY_DISABLED,
                reason_code="CAPABILITY_DISABLED",
                risk_level=action_def.risk_level,
                required_approval_level=action_def.required_approval_level,
                details={"error": f"Action {action_name} is disabled by platform policy in this candidate release."},
            )

        # Rule 3: Tenant / Company scoping check
        if context.authorized_company != context.target.company:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.DENIED,
                reason_code="COMPANY_MISMATCH",
                risk_level=action_def.risk_level,
                required_approval_level=action_def.required_approval_level,
                details={
                    "error": f"Authorized company {context.authorized_company} does not match target company {context.target.company}"
                },
            )

        # Rule 4: Role permission check
        has_role = any(role in action_def.required_roles for role in context.actor_roles)
        if not has_role:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.DENIED,
                reason_code="INSUFFICIENT_ROLE",
                risk_level=action_def.risk_level,
                required_approval_level=action_def.required_approval_level,
                details={
                    "error": f"Actor {context.actor} lacks required role for {action_name}. Required one of: {action_def.required_roles}"
                },
            )

        # Rule 5: Allowed target DocType check
        if context.target.doctype not in action_def.allowed_source_doctypes:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.DENIED,
                reason_code="TARGET_DOCTYPE_DISALLOWED",
                risk_level=action_def.risk_level,
                required_approval_level=action_def.required_approval_level,
                details={
                    "error": f"DocType {context.target.doctype} not allowed for {action_name}. Allowed: {action_def.allowed_source_doctypes}"
                },
            )

        # Rule 6: Resource version freshness check
        if context.current_resource_version != context.target.resource_version:
            return L5PolicyEvaluationResult(
                decision=L5PolicyDecision.DENIED,
                reason_code="STALE_RESOURCE_VERSION",
                risk_level=action_def.risk_level,
                required_approval_level=action_def.required_approval_level,
                details={
                    "error": f"Target version {context.target.resource_version} differs from live {context.current_resource_version}"
                },
            )

        # Rule 7: Allowed state transition
        if context.target.doctype in action_def.allowed_transitions:
            allowed_next = action_def.allowed_transitions[context.target.doctype]
            if context.target.expected_docstatus not in allowed_next:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="INVALID_STATE_TRANSITION",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={
                        "error": f"Expected docstatus {context.target.expected_docstatus} not allowed for transition from {context.current_docstatus}"
                    },
                )

        # Rule 8: Recipient domain allowlist for email send
        if action_def.family == L5ActionFamily.EXTERNAL_EMAIL_SEND:
            recipient = context.parameters.get("recipient_email", "")
            if not recipient or "@" not in recipient:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="INVALID_RECIPIENT_EMAIL",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={"error": "Valid recipient_email parameter is required"},
                )
            domain = recipient.split("@")[-1].lower()
            if action_def.recipient_domain_allowlist and domain not in action_def.recipient_domain_allowlist:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="RECIPIENT_DOMAIN_DISALLOWED",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={"error": f"Recipient domain '{domain}' is not in policy allowlist"},
                )

        # Rule 9: Amount / currency limits for payment request
        if action_def.family == L5ActionFamily.PAYMENT_REQUEST:
            amount = context.parameters.get("amount")
            currency = context.parameters.get("currency")
            if amount is None or amount <= 0:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="INVALID_AMOUNT",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={"error": "Positive amount required for payment request"},
                )
            if action_def.max_amount is not None and amount > action_def.max_amount:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="AMOUNT_EXCEEDS_LIMIT",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={"error": f"Amount {amount} exceeds max allowed {action_def.max_amount}"},
                )
            if action_def.allowed_currencies and currency not in action_def.allowed_currencies:
                return L5PolicyEvaluationResult(
                    decision=L5PolicyDecision.DENIED,
                    reason_code="CURRENCY_DISALLOWED",
                    risk_level=action_def.risk_level,
                    required_approval_level=action_def.required_approval_level,
                    details={"error": f"Currency {currency} not in allowed currencies: {action_def.allowed_currencies}"},
                )

        # Policy passed: requires human confirmation according to required_approval_level
        return L5PolicyEvaluationResult(
            decision=L5PolicyDecision.PERMITTED,
            reason_code="POLICY_ALLOW",
            risk_level=action_def.risk_level,
            required_approval_level=action_def.required_approval_level,
            details={"action_name": action_name, "family": action_def.family.value},
        )
