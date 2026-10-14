"""Comprehensive tests for SearchOverdueInvoicesService and Providers (CORE, DEMO, NATIVE).

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §3, §4, §5.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest

from lotus_fin.application.service.search_overdue_invoices import SearchOverdueInvoicesService
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams
from lotus_fin.infrastructure.persistence.core_overdue_provider import CoreOverdueObservationProvider
from lotus_fin.infrastructure.persistence.demo_overdue_provider import DemoOverdueObservationProvider
from lotus_fin.infrastructure.persistence.native_overdue_adapter import NativeOverdueObservationAdapter
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


def make_context(
    site_id="site_demo",
    company_id="Lotus Demo Corp",
    observed_at="2026-10-13T12:00:00+00:00",
    timezone_str="Asia/Ho_Chi_Minh",
):
    return AuthorizedReadContext(
        actor_id="test_actor",
        auth_session_binding="sess_binding_123",
        site_id=site_id,
        product_id="lotus_app",
        connection_id="conn_1",
        connection_version="1.0.0",
        company_id=company_id,
        capability="invoice.search",
        projection_version="invoice.min.v1",
        context_version="ctx_v1",
        observed_at_utc=observed_at,
        timezone=timezone_str,
        deadline_at_utc=(datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat(),
        correlation_id="d0000000-0000-4000-8000-000000000001",
        request_id="e0000000-0000-4000-8000-000000000001",
        adapter_mode="DEMO_ISOLATED",
    )


def test_core_provider_unconfigured_fails_closed():
    """Core provider reports NOT_AVAILABLE and zero hallucinated records."""
    port = CoreOverdueObservationProvider(is_configured=False)
    svc = SearchOverdueInvoicesService(port=port, provider_mode="CORE")
    ctx = make_context()

    resp, src, status, reason = svc.execute(ctx)
    assert status == ActionStatus.NOT_AVAILABLE
    assert reason == ActionReasonCode.TARGET_UNQUALIFIED
    assert resp is None
    assert src is None


def test_native_provider_unapproved_fails_closed():
    """Native adapter reports NOT_AVAILABLE and blocks execution pending N0."""
    port = NativeOverdueObservationAdapter()
    svc = SearchOverdueInvoicesService(port=port, provider_mode="NATIVE")
    ctx = make_context()

    resp, src, status, reason = svc.execute(ctx)
    assert status == ActionStatus.NOT_AVAILABLE
    assert reason == ActionReasonCode.TARGET_UNQUALIFIED
    assert resp is None


def test_demo_provider_e2e_evaluation():
    """Demo provider returns qualified past-final-due items and filters out non-eligible records."""
    codec = ActionReferenceCodec(key_id="demo_k1", secret_key="demo_super_secret_signing_key_32bytes")
    port = DemoOverdueObservationProvider()
    svc = SearchOverdueInvoicesService(port=port, codec=codec, provider_mode="DEMO")
    ctx = make_context()

    resp, src, status, reason = svc.execute(ctx)

    assert status == ActionStatus.OK
    assert reason == ActionReasonCode.RESULTS_FOUND
    assert src is not None
    assert src.mode == "DEMO_ISOLATED"
    assert resp is not None
    assert resp.provider_mode == "DEMO"
    assert "DEMO_FICTIONAL_DATA" in resp.limitations

    # Expected: DEMO-INV-001 (15,000,000 VND) and DEMO-INV-002 (2,850,000.50 VND)
    # Excluded:
    # - DEMO-INV-003 (balance 0)
    # - DEMO-RET-004 (return doc)
    # - DEMO-INV-005 (due today Oct 13)
    assert len(resp.items) == 2
    item_ids = [item.invoice_id for item in resp.items]
    assert item_ids == ["DEMO-INV-001", "DEMO-INV-002"]

    # Verify signed references
    assert resp.items[0].selection_ref is not None
    assert resp.items[0].selection_ref.startswith("ref.v2.")
    assert resp.items[1].selection_ref is not None

    # Coverage verification
    assert resp.coverage.complete is True
    assert resp.coverage.scanned_rows == 5
    assert resp.coverage.returned_rows == 2


def test_cross_company_returns_empty_result_complete():
    """Searching for an unauthorized company returns complete empty result, no leakage."""
    port = DemoOverdueObservationProvider()
    svc = SearchOverdueInvoicesService(port=port, provider_mode="DEMO")
    ctx = make_context(company_id="Unauthorized Company Ltd")

    resp, src, status, reason = svc.execute(ctx)
    assert status == ActionStatus.OK
    assert reason == ActionReasonCode.EMPTY_RESULT
    assert resp is not None
    assert len(resp.items) == 0
    assert resp.coverage.returned_rows == 0
    assert resp.coverage.complete is True


def test_partial_coverage_strips_selection_references():
    """When scan is truncated or unqualified items exist, coverage is PARTIAL and references stripped."""
    codec = ActionReferenceCodec(key_id="demo_k1", secret_key="demo_super_secret_signing_key_32bytes")
    
    # Provider with one unqualified observation
    records = [
        AuthorizedOutstandingInvoiceObservation(
            invoice_id="INV-UNQUAL-01",
            tenant_id="site_demo",
            company_id="Lotus Demo Corp",
            source_system="DEMO_ISOLATED",
            document_version="v1",
            lifecycle_status="SUBMITTED",
            is_return=False,
            posting_date=date(2026, 9, 1),
            final_due_date=date(2026, 10, 1),
            party_account_currency="VND",
            invoice_currency="VND",
            outstanding_balance="1000.00",
            observed_at_utc="2026-10-13T12:00:00+00:00",
            site_timezone="Asia/Ho_Chi_Minh",
            source_completeness="PARTIAL",  # Unqualified!
            authorized_scope="site_demo:Lotus Demo Corp",
        ),
        AuthorizedOutstandingInvoiceObservation(
            invoice_id="INV-VALID-02",
            tenant_id="site_demo",
            company_id="Lotus Demo Corp",
            source_system="DEMO_ISOLATED",
            document_version="v2",
            lifecycle_status="SUBMITTED",
            is_return=False,
            posting_date=date(2026, 9, 1),
            final_due_date=date(2026, 10, 1),
            party_account_currency="VND",
            invoice_currency="VND",
            outstanding_balance="2000.00",
            observed_at_utc="2026-10-13T12:00:00+00:00",
            site_timezone="Asia/Ho_Chi_Minh",
            source_completeness="COMPLETE",
            authorized_scope="site_demo:Lotus Demo Corp",
        ),
    ]

    port = DemoOverdueObservationProvider(records=records)
    svc = SearchOverdueInvoicesService(port=port, codec=codec, provider_mode="DEMO")
    ctx = make_context()

    resp, src, status, reason = svc.execute(ctx)
    assert status == ActionStatus.PARTIAL
    assert reason == ActionReasonCode.COVERAGE_INCOMPLETE
    assert resp is not None
    assert resp.coverage.complete is False
    assert resp.coverage.missing_required_data is True
    assert len(resp.items) == 1
    # Crucial security invariant: references MUST be None under PARTIAL
    assert resp.items[0].selection_ref is None
