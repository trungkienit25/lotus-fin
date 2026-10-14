import threading
import time
import unittest
from datetime import datetime, timezone, timedelta
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.l4_action_catalog import (
    L4ActionId,
    L4OperationState,
    L4TargetEntity,
)
from lotus_fin.domain.model.l4_operation_record import compute_canonical_digest
from lotus_fin.infrastructure.persistence.l4_mutation_adapters import (
    InMemoryL4OperationLedger,
    IsolatedTestLotusActionWritePort,
    ProductionLotusActionWritePort,
)
from lotus_fin.application.service.l4_mutation_service import L4MutationService
from lotus_fin.presentation.controller.l4_mutation_controller import L4MutationController


class TestL4MutationEngineSecurity(unittest.TestCase):
    def setUp(self):
        self.valid_principal = UserPrincipal(
            user_id="alice@lotusfin.vn",
            company="Lotus SME Co",
            roles=["Accounts User"],
            as_of_date="2026-10-13",
        )
        self.manager_principal = UserPrincipal(
            user_id="boss@lotusfin.vn",
            company="Lotus SME Co",
            roles=["System Manager"],
            as_of_date="2026-10-13",
        )
        self.guest_principal = UserPrincipal(
            user_id="Guest",
            company="Lotus SME Co",
            roles=["Guest"],
            as_of_date="2026-10-13",
        )
        self.other_tenant_principal = UserPrincipal(
            user_id="eve@competitor.com",
            company="Competitor Corp",
            roles=["Accounts User"],
            as_of_date="2026-10-13",
        )
        self.ledger = InMemoryL4OperationLedger()
        self.test_adapter = IsolatedTestLotusActionWritePort()
        self.service = L4MutationService(
            ledger=self.ledger,
            write_adapter=self.test_adapter,
            proposal_ttl_seconds=10,
        )
        self.controller = L4MutationController(self.service)
        self.session_id = "sess_secure_123"
        self.site_id = "site_alpha.localhost"

    def test_e2e_successful_proposal_and_confirmation(self):
        """End-to-End valid proposal and one-use confirmation for Lotus Note."""
        args = {"title": "Call Client", "content": "Follow-up on overdue invoice note", "category": "FOLLOWUP"}
        ok, proposal, err = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
            is_simulated=True,
        )
        self.assertTrue(ok)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.target_entity, L4TargetEntity.LOTUS_NOTE)
        self.assertTrue(proposal.verify_integrity())

        # Confirm action
        state, op, err = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
            claimed_args=args,
        )
        self.assertEqual(state, L4OperationState.SUCCEEDED)
        self.assertIsNotNone(op)
        self.assertIsNotNone(op.result_data)
        self.assertTrue(op.result_data.get("is_synthetic_demo"))

    def test_missing_rights_denial(self):
        """Action requires manager role; regular user denied."""
        args = {"record_type": "draft_payment", "payload_summary": "Prepare payment draft"}
        ok, proposal, err = self.service.propose_action(
            principal=self.valid_principal,  # only Accounts User, needs Manager
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.DRAFT_RECORD_PREPARE,
            arguments=args,
        )
        self.assertFalse(ok)
        self.assertIn("Missing required roles", err)

    def test_guest_user_denial(self):
        """Guest user cannot propose actions."""
        args = {"title": "Test", "content": "Guest test", "category": "GENERAL"}
        ok, proposal, err = self.service.propose_action(
            principal=self.guest_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertFalse(ok)
        self.assertIn("Guest", err)

    def test_tampered_or_altered_args_denial(self):
        """Altering arguments in confirmation challenge results in rejection."""
        args = {"title": "Pay Bill", "description": "Pay bill task", "due_date": "2026-10-20", "priority": "HIGH"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.TASK_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        # Alter arguments during confirmation
        altered = dict(args)
        altered["priority"] = "URGENT"

        state, op, err = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
            claimed_args=altered,
        )
        self.assertEqual(state, L4OperationState.REJECTED)
        self.assertIn("Altered arguments", err)

    def test_different_actor_and_tenant_denial(self):
        """Confirmation by a different user/tenant must deny."""
        args = {"title": "Note A", "content": "Secret note", "category": "GENERAL"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        # Different tenant attempts confirmation
        state, op, err = self.service.confirm_action(
            principal=self.other_tenant_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.REJECTED)
        self.assertIn("Actor mismatch", err)

    def test_different_session_denial(self):
        """Confirmation with stolen token from a different session ID must deny."""
        args = {"title": "Note S", "content": "Session note", "category": "GENERAL"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        state, op, err = self.service.confirm_action(
            principal=self.valid_principal,
            session_id="different_session_999",
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.REJECTED)
        self.assertIn("Session binding mismatch", err)

    def test_expired_proposal_denial(self):
        """Expired proposals cannot be confirmed."""
        short_service = L4MutationService(
            ledger=self.ledger,
            write_adapter=self.test_adapter,
            proposal_ttl_seconds=-1,  # immediate expiry
        )
        args = {"title": "Quick", "content": "Expire quickly", "category": "GENERAL"}
        ok, proposal, _ = short_service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        state, op, err = short_service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.EXPIRED)
        self.assertIn("expired", err.lower())

    def test_double_click_challenge_reuse_protection(self):
        """Reusing challenge on second confirmation is rejected or returns idempotent state."""
        args = {"title": "Task 1", "description": "Single task", "due_date": "2026-10-30", "priority": "LOW"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.TASK_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        # Click 1
        s1, op1, _ = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(s1, L4OperationState.SUCCEEDED)

        # Click 2 (re-submission returns existing idempotent operation)
        s2, op2, _ = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(s2, L4OperationState.SUCCEEDED)
        self.assertEqual(op1.operation_id, op2.operation_id)

    def test_concurrent_double_worker_race(self):
        """Two concurrent threads confirming same proposal atomically allow only one execution."""
        args = {"title": "Race Note", "content": "Concurrency test", "category": "AUDIT"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        results = []

        def worker():
            st, op, err = self.service.confirm_action(
                principal=self.valid_principal,
                session_id=self.session_id,
                proposal_id=proposal.proposal_id,
                challenge=proposal.confirmation_challenge,
            )
            results.append((st, op))

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(results), 2)
        # Both outcomes must yield SUCCEEDED with identical operation ID (idempotent result)
        self.assertEqual(results[0][0], L4OperationState.SUCCEEDED)
        self.assertEqual(results[1][0], L4OperationState.SUCCEEDED)
        self.assertEqual(results[0][1].operation_id, results[1][1].operation_id)
        # Target store should contain exactly 1 created record
        target_recs = [k for k in self.test_adapter._store if results[0][1].operation_id in k]
        self.assertEqual(len(target_recs), 1)

    def test_unknown_outcome_and_reconciliation(self):
        """Network timeout during commit leads to UNKNOWN_OUTCOME and reconciles successfully."""
        args = {"title": "Timeout Note", "content": "Ambiguous outcome", "category": "GENERAL"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        # Trigger timeout simulation in adapter
        self.test_adapter.set_simulate_timeout(True)

        state, op, err = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.UNKNOWN_OUTCOME)
        self.assertIn("ambiguous", err.lower())

        # Safe reconciliation
        rec_state, rec_op, notes = self.service.reconcile_operation(
            principal=self.valid_principal,
            operation_id=op.operation_id,
        )
        self.assertEqual(rec_state, L4OperationState.SUCCEEDED)
        self.assertIn("Reconciled: Found synthetic record", notes)

    def test_production_write_port_fail_closed(self):
        """Production write port is fail-closed, blocking unapproved business mutation."""
        prod_service = L4MutationService(
            ledger=self.ledger,
            write_adapter=ProductionLotusActionWritePort(),
        )
        args = {"title": "Prod Task", "description": "Must fail closed", "due_date": "2026-11-01", "priority": "HIGH"}
        ok, proposal, _ = prod_service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.TASK_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        state, op, err = prod_service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.FAILED)
        self.assertIn("Production Lotus write port is disabled", err)

    def test_cancellation_flow(self):
        """Pending proposal can be cleanly cancelled by user."""
        args = {"title": "Discard", "content": "Never mind", "category": "GENERAL"}
        ok, proposal, _ = self.service.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            action_id=L4ActionId.NOTE_CREATE,
            arguments=args,
        )
        self.assertTrue(ok)

        cancelled, err = self.service.cancel_pending_proposal(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
        )
        self.assertTrue(cancelled)

        # Trying to confirm cancelled proposal fails
        state, op, err = self.service.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            proposal_id=proposal.proposal_id,
            challenge=proposal.confirmation_challenge,
        )
        self.assertEqual(state, L4OperationState.REJECTED)

    def test_controller_endpoints_and_serialization(self):
        """Presentation controller handles serialization and status codes accurately."""
        body = {
            "request_id": "req_101",
            "action_id": "lotus.note.create",
            "arguments": {"title": "Ctrl Note", "content": "Body", "category": "GENERAL"},
            "simulated": True,
        }
        status, resp = self.controller.propose_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            site_id=self.site_id,
            raw_body=body,
        )
        self.assertEqual(status, 200)
        self.assertTrue(resp["success"])
        proposal = resp["proposal"]

        # Confirm via controller
        confirm_body = {
            "request_id": "req_102",
            "proposal_id": proposal["proposal_id"],
            "confirmation_challenge": proposal["confirmation_challenge"],
            "claimed_arguments": {"title": "Ctrl Note", "content": "Body", "category": "GENERAL"},
        }
        c_status, c_resp = self.controller.confirm_action(
            principal=self.valid_principal,
            session_id=self.session_id,
            raw_body=confirm_body,
        )
        self.assertEqual(c_status, 200)
        self.assertTrue(c_resp["success"])
        self.assertEqual(c_resp["state"], "SUCCEEDED")
