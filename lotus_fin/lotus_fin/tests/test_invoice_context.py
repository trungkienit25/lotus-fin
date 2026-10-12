"""Tests for Authorized Read Context and Authorizer Adapter (Stages B1 & B2).

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §4.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import uuid
import sys
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.infrastructure.config.invoice_actions_config import (
    ApprovedConnection,
    InvoiceActionsConfig,
)
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService


def make_test_config() -> InvoiceActionsConfig:
    conn = ApprovedConnection(
        product_id="lotus_fin_v1",
        site_id="erp_site_main",
        connection_id="conn_primary",
        connection_version="v1.0",
        allowed_companies=["Cong ty TNHH Hoa Sen", "Lotus Corp"],
    )
    return InvoiceActionsConfig(
        enabled=True,
        signing_key_id="key_2026_01",
        signing_secret="super_secret_signing_key_minimum_32_bytes_long",
        connections={"erp_site_main": conn},
    )


def test_context_model_immutability():
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    ctx = AuthorizedReadContext(
        actor_id="user_test",
        auth_session_binding="sid_test",
        site_id="erp_site_main",
        product_id="lotus_fin_v1",
        connection_id="conn_primary",
        connection_version="v1.0",
        company_id="Lotus Corp",
        capability="invoice.context",
        context_version="ctx_123",
        observed_at_utc="2026-10-11T10:00:00Z",
        timezone="Asia/Ho_Chi_Minh",
        deadline_at_utc="2026-10-11T10:00:05Z",
        correlation_id=cid,
        request_id=req_id,
    )
    with pytest.raises(ValidationError):
        ctx.company_id = "Hacked Corp"  # frozen model


def test_authorizer_guest_user_denied():
    cfg = make_test_config()
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg, session_user="Guest", site_name="erp_site_main"
    )
    ctx, check = authorizer.resolve_context(
        candidate_company="Lotus Corp",
        capability="invoice.context",
        client_request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
    )
    assert ctx is None
    assert not check.is_authorized
    assert check.status == ActionStatus.FORBIDDEN
    assert check.reason_code == ActionReasonCode.AUTH_REQUIRED


def test_authorizer_unauthorized_company_denied():
    cfg = make_test_config()
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg, session_user="accountant@lotus.vn", session_id="sid_123", site_name="erp_site_main"
    )
    ctx, check = authorizer.resolve_context(
        candidate_company="Unauthorized Adversary Corp",
        capability="invoice.context",
        client_request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
    )
    assert ctx is None
    assert not check.is_authorized
    assert check.status == ActionStatus.FORBIDDEN
    assert check.reason_code == ActionReasonCode.COMPANY_DENIED


def test_authorizer_unqualified_target_site():
    cfg = make_test_config()
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg, session_user="accountant@lotus.vn", session_id="sid_123", site_name="unregistered_rogue_site"
    )
    ctx, check = authorizer.resolve_context(
        candidate_company="Lotus Corp",
        capability="invoice.context",
        client_request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
    )
    assert ctx is None
    assert check.status == ActionStatus.NOT_AVAILABLE
    assert check.reason_code == ActionReasonCode.TARGET_UNQUALIFIED


def test_authorizer_unapproved_capability_denied():
    cfg = make_test_config()
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg, session_user="accountant@lotus.vn", site_name="erp_site_main"
    )
    ctx, check = authorizer.resolve_context(
        candidate_company="Lotus Corp",
        capability="invoice.arbitrary_delete",
        client_request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
    )
    assert ctx is None
    assert check.status == ActionStatus.FORBIDDEN
    assert check.reason_code == ActionReasonCode.CAPABILITY_DENIED


def test_authorizer_valid_context_resolution(monkeypatch):
    monkeypatch.setitem(sys.modules, "frappe", SimpleNamespace(has_permission=lambda dt, **kw:
        (dt, kw) == ("Company", dict(ptype="read", doc="Lotus Corp", user="accountant@lotus.vn"))))
    cfg = make_test_config()
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg,
        session_user="accountant@lotus.vn",
        session_id="sid_valid_123",
        site_name="erp_site_main",
    )
    svc = ResolveReadContextService(authorizer)
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    ctx, check = svc.execute(
        candidate_company="Lotus Corp",
        capability="invoice.context",
        client_request_id=req_id,
        correlation_id=cid,
    )
    assert check.is_authorized
    assert check.status == ActionStatus.OK
    assert ctx is not None
    assert ctx.actor_id == "accountant@lotus.vn"
    assert ctx.company_id == "Lotus Corp"
    assert ctx.site_id == "erp_site_main"
    assert ctx.correlation_id == cid
    assert ctx.request_id == req_id
    assert ctx.context_version.startswith("ctx_")


def test_authorizer_exact_company_denial_and_outage_fail_closed():
    import sys, types
    cfg = make_test_config()
    fake_frappe = types.ModuleType("frappe")
    fake_frappe.session = types.SimpleNamespace(user="alice", sid="sid_123")
    fake_frappe.local = types.SimpleNamespace(site="erp_site_main")

    def scoped_perm(doctype, ptype="read", doc=None, user=None, **kw):
        return doc != "Lotus Corp"

    fake_frappe.has_permission = scoped_perm
    sys.modules["frappe"] = fake_frappe
    try:
        authorizer = FrappeInvoiceAuthorizer(config=cfg, site_name="erp_site_main")
        ctx, ch = authorizer.resolve_context(
            candidate_company="Lotus Corp",
            capability="invoice.context",
            client_request_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
        )
        assert ctx is None
        assert ch.status == ActionStatus.FORBIDDEN
        assert ch.reason_code == ActionReasonCode.COMPANY_DENIED

        def throwing_perm(*args, **kw):
            raise RuntimeError("PERMISSION_OUTAGE")

        fake_frappe.has_permission = throwing_perm
        ctx, ch = authorizer.resolve_context(
            candidate_company="Lotus Corp",
            capability="invoice.context",
            client_request_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
        )
        assert ctx is None
        assert ch.status == ActionStatus.NOT_AVAILABLE
        assert ch.reason_code == ActionReasonCode.TARGET_UNQUALIFIED
    finally:
        sys.modules.pop("frappe", None)

