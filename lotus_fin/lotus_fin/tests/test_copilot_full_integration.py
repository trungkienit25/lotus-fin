"""Integration tests exercise real module composition, never native qualification."""
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError
from lotus_fin.api.copilot_integration_api import IntegrationRequest
from lotus_fin.application.service.copilot_integration import CopilotIntegrationService
from lotus_fin.infrastructure.persistence.copilot_demo_store import CopilotDemoStore
from lotus_fin.domain.schema.l4_action_catalog import L4OperationState


@pytest.fixture
def service(tmp_path):
    return CopilotIntegrationService(CopilotDemoStore(tmp_path / "demo.sqlite3"))


def call(service, action, payload=None, *, actor="alice", session="session-a", profile="DEMO", enabled=True, roles=None, name=None):
    return service.dispatch(actor, roles if roles is not None else ["Accounts User"], session,
                            "isolated-site", enabled, {"profile": profile, "action": action,
                            "payload": payload or {}, "action_name": name})


def propose(service):
    status, result = call(service, "l4_propose", {"request_id": "test-request", "action_id": "lotus.task.create",
        "arguments": {"title": "Follow-up", "description": "User reviewed local L3 text", "due_date": "2026-10-20"}})
    assert status == 200, result
    assert result["proposal"]["simulated"] is True
    assert result["proposal"]["session_id"] == "server-bound"
    return result["proposal"]


def confirmation(proposal):
    return {"request_id": "confirm-request", "proposal_id": proposal["proposal_id"],
            "confirmation_challenge": proposal["confirmation_challenge"]}


def test_l3_to_l4_confirm_persists_and_is_idempotent(service):
    proposal = propose(service)
    status, first = call(service, "l4_confirm", confirmation(proposal))
    assert status == 200
    assert first["operation"]["is_synthetic_demo"] is True
    assert first["state"] == L4OperationState.SUCCEEDED
    # A fresh composition reads durable simulation state instead of a process singleton.
    fresh = CopilotIntegrationService(CopilotDemoStore(service.store.path))
    _, replay = call(fresh, "l4_confirm", confirmation(proposal))
    assert replay["operation"]["operation_id"] == first["operation"]["operation_id"]
    assert replay["operation"]["execution_attempts"] == 1


@pytest.mark.parametrize("change", [{"actor": "bob"}, {"session": "rotated"}, {"roles": []}])
def test_old_proposal_cannot_cross_scope_or_revoked_permissions(service, change):
    proposal = propose(service)
    _, result = call(service, "l4_confirm", confirmation(proposal), **change)
    assert not result["success"]
    assert result["operation"] is None


@pytest.mark.parametrize("profile,enabled,expected", [("CORE", True, 503), ("CORE", False, 503), ("DEMO", False, 403)])
@pytest.mark.parametrize("action", ["past_final_due", "l4_propose", "l4_confirm", "l5_review"])
def test_core_demo_isolation_and_disabled_source(service, profile, enabled, expected, action):
    status, result = call(service, action, profile=profile, enabled=enabled)
    assert status == expected
    assert "operation" not in result and "data" not in result
    assert not service.store.path.exists()


def test_v1_actual_evaluator_fixed_gold(service):
    status, result = call(service, "past_final_due")
    assert status == 200
    data = result["data"]
    assert data["provider_mode"] == "DEMO"
    assert [(i["invoice_id"], i["overdue_days"]) for i in data["items"]] == [("DEMO-INV-001", 12), ("DEMO-INV-002", 8)]
    assert all(i["selection_ref"] is None for i in data["items"])
    assert data["coverage"]["complete"] is True


@pytest.mark.parametrize("name,reason", [("l5.doc.submit_sales_invoice.v1", "APPROVAL_PROVIDER_UNAVAILABLE"),
    ("l5.pay.execute_wire_transfer.v1", "CAPABILITY_DISABLED"),
    ("l5.comm.send_statement_email.v1", "RECIPIENT_DOMAIN_DISALLOWED"), ("unknown", "UNKNOWN_ACTION_NAME")])
def test_l5_policy_review_denies_side_effects(service, name, reason):
    _, result = call(service, "l5_review", name=name)
    assert result["status"] == "DENIED" and result["reason_code"] == reason
    assert "review_challenge" not in result


def test_cancel_and_expired_proposal(service):
    proposal = propose(service)
    call(service, "l4_cancel", {"request_id": "cancel", "proposal_id": proposal["proposal_id"]})
    _, result = call(service, "l4_confirm", confirmation(proposal))
    assert not result["success"]
    other = propose(service)
    with service.store.transaction("isolated-site:alice:session-a:DEMO", "test-expire") as (ledger, _):
        ledger._proposals[other["proposal_id"]].expires_at_utc = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    _, expired = call(service, "l4_confirm", confirmation(other))
    assert expired["state"] == L4OperationState.EXPIRED


def test_failed_audit_rolls_back_before_simulation(service):
    propose(service)
    with sqlite3.connect(service.store.path) as conn:
        conn.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'audit unavailable'); END")
    with pytest.raises(sqlite3.IntegrityError):
        call(service, "l4_propose", {})
    with sqlite3.connect(service.store.path) as conn:
        assert conn.execute("SELECT count(*) FROM audit").fetchone()[0] == 1


def test_concurrent_confirmation_single_receipt(service):
    proposal = propose(service)
    results = []
    threads = [threading.Thread(target=lambda: results.append(call(service, "l4_confirm", confirmation(proposal)))) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(results) == 4
    assert len({r[1]["operation"]["operation_id"] for r in results}) == 1
    assert all(r[1]["operation"]["execution_attempts"] == 1 for r in results)


def test_unknown_outcome_reconciles_without_reexecution(service):
    proposal = propose(service)
    from lotus_fin.application.service.l4_mutation_service import L4MutationService
    from lotus_fin.domain.model.user_context import UserPrincipal
    principal = UserPrincipal(user_id="alice", roles=["Accounts User"], company="Lotus Demo Corp")
    with service.store.transaction("isolated-site:alice:session-a:DEMO", "timeout-fixture") as (ledger, adapter):
        adapter.set_simulate_timeout(True)
        state, operation, _ = L4MutationService(ledger, adapter).confirm_action(principal, "session-a", proposal["proposal_id"], proposal["confirmation_challenge"])
        assert state == L4OperationState.UNKNOWN_OUTCOME
    _, result = call(service, "l4_reconcile", {"request_id": "reconcile", "operation_id": operation.operation_id})
    assert result["state"] == L4OperationState.SUCCEEDED
    assert result["operation"]["execution_attempts"] == 1


def test_client_cannot_supply_authority_or_execution_adapter():
    for field in ("actor", "session", "company", "adapter", "simulated"):
        with pytest.raises(ValidationError):
            IntegrationRequest.model_validate({"profile": "DEMO", "action": "l4_propose", field: "attacker"})
