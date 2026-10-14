"""Comprehensive Unit and E2E Tests for L5 Action Workflows."""

import pytest
import time
from lotus_fin.domain.l5.models.contracts import (
    L5ActionFamily,
    L5AdapterCapabilityState,
    L5ApprovalLevel,
    L5PolicyDecision,
    L5ProposalState,
    L5RiskLevel,
)
from lotus_fin.domain.l5.models.proposals import L5TargetSpec
from lotus_fin.domain.l5.policy.engine import L5PolicyContext, L5PolicyEngine
from lotus_fin.domain.l5.service.workflow import L5WorkflowService


@pytest.fixture
def policy_engine():
    return L5PolicyEngine()


@pytest.fixture
def workflow_service(policy_engine):
    return L5WorkflowService(policy_engine=policy_engine, use_simulation=True)


# -------------------------------------------------------------
# Test Suite 1: L5 Policy Engine & Denial
# -------------------------------------------------------------
class TestL5PolicyEngine:
    def test_unknown_action_fails_closed(self, policy_engine):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        ctx = L5PolicyContext(
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            current_resource_version="v1",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("arbitrary.malicious.action", ctx)
        assert res.decision == L5PolicyDecision.DENIED
        assert res.reason_code == "UNKNOWN_ACTION_NAME"

    def test_payment_execution_permanently_blocked(self, policy_engine):
        target = L5TargetSpec(
            doctype="Payment Entry",
            doc_id="PE-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        ctx = L5PolicyContext(
            actor="treasurer@lotusfin.internal",
            actor_roles=["Treasurer"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            current_resource_version="v1",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("l5.pay.execute_wire_transfer.v1", ctx)
        assert res.decision == L5PolicyDecision.CAPABILITY_DISABLED
        assert res.reason_code == "CAPABILITY_DISABLED"

    def test_cross_tenant_company_mismatch_denied(self, policy_engine):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Foreign Corp",
        )
        ctx = L5PolicyContext(
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",  # Authorized for Lotus Corp, target is Foreign Corp
            target=target,
            current_resource_version="v1",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("l5.doc.submit_sales_invoice.v1", ctx)
        assert res.decision == L5PolicyDecision.DENIED
        assert res.reason_code == "COMPANY_MISMATCH"

    def test_insufficient_role_denied(self, policy_engine):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        ctx = L5PolicyContext(
            actor="guest_user",
            actor_roles=["Guest"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            current_resource_version="v1",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("l5.doc.submit_sales_invoice.v1", ctx)
        assert res.decision == L5PolicyDecision.DENIED
        assert res.reason_code == "INSUFFICIENT_ROLE"

    def test_stale_resource_version_denied(self, policy_engine):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1-stale",
            company="Lotus Corp",
        )
        ctx = L5PolicyContext(
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            current_resource_version="v2-latest",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("l5.doc.submit_sales_invoice.v1", ctx)
        assert res.decision == L5PolicyDecision.DENIED
        assert res.reason_code == "STALE_RESOURCE_VERSION"

    def test_email_domain_allowlist_enforced(self, policy_engine):
        target = L5TargetSpec(
            doctype="Customer",
            doc_id="CUST-001",
            resource_version="v1",
            company="Lotus Corp",
        )
        # Malicious non-allowlisted recipient
        ctx_bad = L5PolicyContext(
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts User"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            parameters={"recipient_email": "attacker@evil-domain.com"},
            current_resource_version="v1",
            current_docstatus=0,
        )
        res_bad = policy_engine.evaluate_intent("l5.comm.send_statement_email.v1", ctx_bad)
        assert res_bad.decision == L5PolicyDecision.DENIED
        assert res_bad.reason_code == "RECIPIENT_DOMAIN_DISALLOWED"

        # Allowlisted recipient
        ctx_good = L5PolicyContext(
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts User"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            parameters={"recipient_email": "client@clientcorp.com"},
            current_resource_version="v1",
            current_docstatus=0,
        )
        res_good = policy_engine.evaluate_intent("l5.comm.send_statement_email.v1", ctx_good)
        assert res_good.decision == L5PolicyDecision.PERMITTED

    def test_payment_request_amount_cap(self, policy_engine):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        ctx_excess = L5PolicyContext(
            actor="manager@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            tenant_id="t1",
            site="prod-site",
            authorized_company="Lotus Corp",
            target=target,
            parameters={"amount": 500000000.0, "currency": "VND"},  # 500M exceeds 100M cap
            current_resource_version="v1",
            current_docstatus=0,
        )
        res = policy_engine.evaluate_intent("l5.pay.request_disbursement.v1", ctx_excess)
        assert res.decision == L5PolicyDecision.DENIED
        assert res.reason_code == "AMOUNT_EXCEEDS_LIMIT"


# -------------------------------------------------------------
# Test Suite 2: Prepare -> Approve -> Execute Lifecycle
# -------------------------------------------------------------
class TestL5LifecycleAndSafety:
    def test_full_document_submit_simulation_success(self, workflow_service):
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        # 1. Prepare
        prep = workflow_service.prepare_proposal(
            action_name="l5.doc.submit_sales_invoice.v1",
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            site="prod-site",
            tenant_id="t1",
            authorized_company="Lotus Corp",
            target=target,
            parameters={},
            current_resource_version="v1",
            current_docstatus=0,
        )
        assert prep["status"] == "PROPOSAL_READY"
        proposal_id = prep["proposal_id"]
        challenge = prep["review_challenge"]

        # 2. Approve (requires Finance Officer gate)
        app = workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
            additional_approvals=[{"approver": "officer@lotusfin.internal", "role": "Finance Officer"}],
        )
        assert app["status"] == "APPROVED"

        # 3. Execute
        exec_res = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            idempotency_key="idemp-key-001",
            current_resource_version="v1",
            current_docstatus=0,
        )
        assert exec_res["status"] == "COMMITTED"
        assert exec_res["target_identity"] == "ACC-SINV-001"
        assert exec_res["receipt"]["new_docstatus"] == 1

        # Verify Audit Log
        events = [a.event_type for a in workflow_service.audit_log if a.proposal_id == proposal_id]
        assert "PROPOSAL_CREATED" in events
        assert "PROPOSAL_APPROVED" in events
        assert "OPERATION_RESERVED" in events
        assert "OPERATION_COMMITTED" in events

    def test_idempotency_replay_returns_cached_committed(self, workflow_service):
        target = L5TargetSpec(
            doctype="Customer",
            doc_id="CUST-001",
            resource_version="v1",
            company="Lotus Corp",
        )
        prep = workflow_service.prepare_proposal(
            action_name="l5.comm.send_statement_email.v1",
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts User"],
            session_id="sess-123",
            site="prod-site",
            tenant_id="t1",
            authorized_company="Lotus Corp",
            target=target,
            parameters={"recipient_email": "client@clientcorp.com"},
            current_resource_version="v1",
            current_docstatus=0,
        )
        proposal_id = prep["proposal_id"]
        challenge = prep["review_challenge"]

        workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
        )

        res1 = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts User"],
            session_id="sess-123",
            idempotency_key="idemp-email-001",
            current_resource_version="v1",
            current_docstatus=0,
        )
        assert res1["status"] == "COMMITTED"

        # Duplicate replay attempt
        res2 = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts User"],
            session_id="sess-123",
            idempotency_key="idemp-email-001",
            current_resource_version="v1",
            current_docstatus=0,
        )
        assert res2["status"] == "ALREADY_COMMITTED"
        assert res2["operation_id"] == res1["operation_id"]

    def test_dual_control_m_of_n_enforcement(self, workflow_service):
        # Cancel Sales Invoice requires DUAL_CONTROL_M_OF_N
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=2,
            resource_version="v1",
            company="Lotus Corp",
        )
        prep = workflow_service.prepare_proposal(
            action_name="l5.doc.cancel_sales_invoice.v1",
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            site="prod-site",
            tenant_id="t1",
            authorized_company="Lotus Corp",
            target=target,
            parameters={},
            current_resource_version="v1",
            current_docstatus=1,
        )
        proposal_id = prep["proposal_id"]
        challenge = prep["review_challenge"]

        # Attempt approval without 2nd approver
        gate_res = workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
            additional_approvals=[],  # Empty
        )
        assert gate_res["status"] == "APPROVAL_GATE_PENDING"
        assert gate_res["reason_code"] == "DUAL_CONTROL_REQUIRED"

        # Valid second approver
        valid_res = workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
            additional_approvals=[{"approver": "bob@lotusfin.internal", "role": "Accounts Manager"}],
        )
        assert valid_res["status"] == "APPROVED"

    def test_reauthorization_failure_before_commit(self, workflow_service):
        """TOCTOU defense: resource modified or role revoked after UI approval."""
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        prep = workflow_service.prepare_proposal(
            action_name="l5.doc.submit_sales_invoice.v1",
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            site="prod-site",
            tenant_id="t1",
            authorized_company="Lotus Corp",
            target=target,
            parameters={},
            current_resource_version="v1",
            current_docstatus=0,
        )
        proposal_id = prep["proposal_id"]
        challenge = prep["review_challenge"]

        workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
            additional_approvals=[{"approver": "officer@lotusfin.internal", "role": "Finance Officer"}],
        )

        # Execute with changed live resource version (concurrency edit)
        exec_res = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            idempotency_key="idemp-key-revoked",
            current_resource_version="v2-modified-concurrently",
            current_docstatus=0,
        )
        assert exec_res["status"] == "DENIED"
        assert exec_res["reason_code"] == "REAUTHORIZATION_FAILED"
        assert exec_res["sub_code"] == "STALE_RESOURCE_VERSION"

    def test_unknown_outcome_and_reconciliation(self, workflow_service):
        """Simulate ambiguous crash after possible commit and non-blind reconciliation."""
        target = L5TargetSpec(
            doctype="Sales Invoice",
            doc_id="ACC-SINV-001",
            expected_docstatus=1,
            resource_version="v1",
            company="Lotus Corp",
        )
        prep = workflow_service.prepare_proposal(
            action_name="l5.doc.submit_sales_invoice.v1",
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            site="prod-site",
            tenant_id="t1",
            authorized_company="Lotus Corp",
            target=target,
            parameters={},
            current_resource_version="v1",
            current_docstatus=0,
        )
        proposal_id = prep["proposal_id"]
        challenge = prep["review_challenge"]

        workflow_service.submit_ui_approval(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            review_challenge=challenge,
            additional_approvals=[{"approver": "officer@lotusfin.internal", "role": "Finance Officer"}],
        )

        # Inject simulated crash
        exec_res = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            idempotency_key="idemp-crash-001",
            current_resource_version="v1",
            current_docstatus=0,
            simulation_fault="CRASH_AFTER_POSSIBLE_COMMIT",
        )
        assert exec_res["status"] == "UNKNOWN_OUTCOME"
        operation_id = exec_res["operation_id"]

        # Attempting immediate blind execution retry is blocked
        retry_res = workflow_service.execute_proposal(
            proposal_id=proposal_id,
            actor="alice@lotusfin.internal",
            actor_roles=["Accounts Manager"],
            session_id="sess-123",
            idempotency_key="idemp-crash-001",
            current_resource_version="v1",
            current_docstatus=0,
        )
        assert retry_res["status"] == "UNKNOWN_OUTCOME"

        # Explicit non-blind operator reconciliation
        recon_res = workflow_service.reconcile_operation(
            operation_id=operation_id,
            actor="alice@lotusfin.internal",
            session_id="sess-123",
            verified_external_status="VERIFIED_COMMITTED",
        )
        assert recon_res["status"] == "RECONCILED"
        assert recon_res["resolved_state"] == "COMMITTED"
