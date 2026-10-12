"""B03: identity is not Company authority; unavailable permission fails closed."""

import sys
import types
import uuid
import pytest
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.infrastructure.config.invoice_actions_config import ApprovedConnection, InvoiceActionsConfig
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer


def resolve():
    connection = ApprovedConnection(product_id="product", site_id="site", connection_id="conn",
                                    connection_version="v1", allowed_companies=["Company A"])
    config = InvoiceActionsConfig(signing_key_id="test-key", signing_secret="x" * 32,
                                  connections={"site": connection})
    auth = FrappeInvoiceAuthorizer(config, session_user="alice", session_id="sid", site_name="site")
    return auth.resolve_context("Company A", "invoice.context", str(uuid.uuid4()), str(uuid.uuid4()))


@pytest.mark.parametrize("mode", ["no_framework", "no_method", "not_callable", "throws"])
def test_missing_permission_seam_with_fixed_identity_denied(monkeypatch, mode):
    calls = []
    framework = types.ModuleType("frappe")

    def throwing(doctype, **kwargs):
        calls.append((doctype, kwargs))
        raise RuntimeError("PRIVATE_PERMISSION_CANARY")

    if mode == "not_callable":
        framework.has_permission = True
    elif mode == "throws":
        framework.has_permission = throwing
    # None explicitly marks an unavailable import, even if ERP is installed locally.
    monkeypatch.setitem(sys.modules, "frappe", None if mode == "no_framework" else framework)
    ctx, check = resolve()
    assert ctx is None and not check.is_authorized
    assert check.status == ActionStatus.NOT_AVAILABLE
    assert check.reason_code == ActionReasonCode.TARGET_UNQUALIFIED
    assert "PRIVATE_PERMISSION_CANARY" not in str(check)
    assert len(calls) == (1 if mode == "throws" else 0)
    if calls:
        assert calls == [("Company", dict(ptype="read", doc="Company A", user="alice"))]


@pytest.mark.parametrize("decision", [False, None, 1, "yes"])
def test_only_qualified_affirmative_company_actor_decision_grants_context(monkeypatch, decision):
    calls = []

    def permission(doctype, **kwargs):
        calls.append((doctype, kwargs))
        return decision

    monkeypatch.setitem(sys.modules, "frappe", types.SimpleNamespace(has_permission=permission))
    ctx, check = resolve()
    assert calls == [("Company", dict(ptype="read", doc="Company A", user="alice"))]
    assert ctx is None and not check.is_authorized
    assert check.status == ActionStatus.FORBIDDEN
    assert check.reason_code == ActionReasonCode.COMPANY_DENIED


def test_explicit_qualified_affirmative_permission_control(monkeypatch):
    calls = []

    def qualified(doctype, *, ptype, doc, user):
        calls.append((doctype, ptype, doc, user))
        return (doctype, ptype, doc, user) == ("Company", "read", "Company A", "alice")

    monkeypatch.setitem(sys.modules, "frappe", types.SimpleNamespace(has_permission=qualified))
    ctx, check = resolve()
    assert calls == [("Company", "read", "Company A", "alice")]
    assert ctx is not None and ctx.actor_id == "alice" and ctx.company_id == "Company A"
    assert check.is_authorized and check.reason_code == ActionReasonCode.CONTEXT_READY
