"""F01: fresh resolver pipeline and scope revocation, with offline Company seam."""
import sys
from types import SimpleNamespace
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from lotus_fin.infrastructure.config.invoice_actions_config import ApprovedConnection, InvoiceActionsConfig
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters, InvoiceReadRow, InvoiceReadPage, InvoiceReadDocument
from lotus_fin.domain.schema.action_outcome import SourceEvidence, ActionStatus as S, ActionReasonCode as R

RID = "b1234567-89ab-4cde-8fab-0123456789ab"
CID = "c1234567-89ab-4cde-8fab-0123456789ab"


@pytest.fixture
def family(monkeypatch):
    calls = []
    framework = SimpleNamespace(session=SimpleNamespace(user="actor@example.invalid", sid="sid"),
        local=SimpleNamespace(site="site"), get_system_settings=lambda key: "Asia/Ho_Chi_Minh")
    def permission(doctype, **kw):
        calls.append((doctype, kw))
        return doctype == "Company" and kw == dict(ptype="read", doc="Company A", user=framework.session.user)
    framework.has_permission = permission
    monkeypatch.setitem(sys.modules, "frappe", framework)
    conn = ApprovedConnection(product_id="product", site_id="site", connection_id="conn",
        connection_version="policy-1", allowed_companies=["Company A", "Company B"])
    config = InvoiceActionsConfig(enabled=True, signing_key_id="key", signing_secret="x" * 32,
        connections={"site": conn})
    return framework, config, calls


def resolve(config, capability):
    ctx, check = ResolveReadContextService(FrappeInvoiceAuthorizer(config)).execute("Company A", capability, RID, CID)
    assert check.is_authorized and ctx is not None
    return ctx


def evidence(ctx):
    return SourceEvidence(mode="ERP_READ", product_ref=ctx.product_id, site_ref=ctx.site_id,
        connection_ref=ctx.connection_id, connection_version=ctx.connection_version,
        projection_version=ctx.projection_version, observed_at=ctx.observed_at_utc,
        timezone=ctx.timezone, coverage="PAGE_COMPLETE")


class ReadPort:
    def __init__(self):
        self.search_calls = self.open_calls = 0
        self.denied = False

    def search_invoices(self, *, context, **kwargs):
        self.search_calls += 1
        day = datetime.fromisoformat(context.observed_at_utc).astimezone(ZoneInfo(context.timezone)).date()
        row = InvoiceReadRow(invoice_id="INV-001", posting_date=day, docstatus=1, record_version="version-1")
        return InvoiceReadPage(items=[row], returned_count=1, page_complete=True, has_more=False), evidence(context), S.OK, R.RESULTS_FOUND

    def open_invoice(self, *, context, doc_id, **kwargs):
        self.open_calls += 1
        if self.denied:
            return None, None, S.FORBIDDEN, R.ACCESS_DENIED
        day = datetime.fromisoformat(context.observed_at_utc).astimezone(ZoneInfo(context.timezone)).date()
        doc = InvoiceReadDocument(invoice_id=doc_id, company_label=context.company_id,
            posting_date=day, docstatus=1, record_version="version-1")
        return doc, evidence(context), S.OK, R.DOCUMENT_READY


def selection(config):
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    port = ReadPort()
    ctx = resolve(config, "invoice.search")
    page, _, status, reason = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    assert (status, reason) == (S.OK, R.RESULTS_FOUND)
    return codec, port, page.items[0].selection_ref


def test_fresh_get_context_search_open_pipeline(family):
    _, config, calls = family
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    context = resolve(config, "invoice.context")
    context_ref = codec.sign_reference("invoice.context", context)
    search = resolve(config, "invoice.search")
    assert codec.verify_reference(context_ref, "invoice.context", search) == (True, None)
    codec, port, token = selection(config)
    opened = resolve(config, "invoice.open")
    assert context.context_version == search.context_version == opened.context_version
    assert OpenAuthorizedInvoiceService(port, codec).execute(opened, token)[2:] == (S.OK, R.DOCUMENT_READY)
    assert port.search_calls == port.open_calls == 1
    assert len(calls) == 4


@pytest.mark.parametrize("capability", ["invoice.context", "invoice.search", "invoice.open"])
def test_each_capability_is_independently_denied(family, capability):
    _, config, _ = family
    config = config.model_copy(update={"allowed_capabilities": [c for c in config.allowed_capabilities if c != capability]})
    ctx, check = ResolveReadContextService(FrappeInvoiceAuthorizer(config)).execute("Company A", capability, RID, CID)
    assert ctx is None and check.reason_code == R.CAPABILITY_DENIED


@pytest.mark.parametrize("axis", ["actor", "session", "site", "company", "product_id", "site_id",
    "connection_id", "connection_version", "deadline_ms", "reference_ttl_seconds", "signing_key_id", "signing_secret", "allowed_capabilities"])
def test_real_scope_or_policy_change_invalidates_selection(family, axis):
    framework, config, _ = family
    codec, port, token = selection(config)
    if axis in ("actor", "session"):
        setattr(framework.session, "user" if axis == "actor" else "sid", "changed")
    elif axis in ("site", "company", "product_id", "site_id", "connection_id", "connection_version"):
        conn = config.connections["site"]
        changes = {"allowed_companies": ["Company B"]} if axis == "company" else ({axis: "changed"} if axis != "site" else {})
        new_site = "changed" if axis == "site" else "site"
        framework.local.site = new_site
        config = config.model_copy(update={"connections": {new_site: conn.model_copy(update=changes)}})
    else:
        change = {"deadline_ms": 6000, "reference_ttl_seconds": 600, "signing_key_id": "new-key",
            "signing_secret": "y" * 32, "allowed_capabilities": ["invoice.context", "invoice.open"]}[axis]
        config = config.model_copy(update={axis: change})
    ctx, check = ResolveReadContextService(FrappeInvoiceAuthorizer(config)).execute("Company A", "invoice.open", RID, CID)
    if ctx is not None:
        assert OpenAuthorizedInvoiceService(port, codec).execute(ctx, token) == (None, None, S.FORBIDDEN, R.ACCESS_DENIED)
    else:
        assert not check.is_authorized
    assert port.open_calls == 0


def test_tampering_wrong_capability_and_replay_reauthorize(family):
    _, config, _ = family
    codec, port, token = selection(config)
    service = OpenAuthorizedInvoiceService(port, codec)
    assert service.execute(resolve(config, "invoice.search"), token)[2:] == (S.FORBIDDEN, R.CAPABILITY_DENIED)
    assert service.execute(resolve(config, "invoice.open"), token[:-1])[2:] == (S.FORBIDDEN, R.ACCESS_DENIED)
    for _ in range(2):
        assert service.execute(resolve(config, "invoice.open"), token)[2:] == (S.OK, R.DOCUMENT_READY)
    port.denied = True
    assert service.execute(resolve(config, "invoice.open"), token) == (None, None, S.FORBIDDEN, R.ACCESS_DENIED)
    assert port.open_calls == 3
