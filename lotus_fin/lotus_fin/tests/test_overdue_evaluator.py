"""Comprehensive test suite for Phase 1 & 2 Deterministic Predicate and Financial Boundaries.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §1, §2, §4, §5.
"""

from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError

from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.policy.past_final_due_evaluator import EligibilityDecision, PastFinalDueEvaluator


def make_test_observation(
    invoice_id="INV-001",
    tenant_id="tenant_alpha",
    company_id="Company Alpha",
    lifecycle_status="SUBMITTED",
    is_return=False,
    is_credit_note=False,
    is_write_off=False,
    posting_date=date(2026, 9, 1),
    final_due_date=date(2026, 10, 1),
    party_account_currency="VND",
    invoice_currency="VND",
    outstanding_balance="1000000.00",
    observed_at_utc="2026-10-13T12:00:00+00:00",
    site_timezone="Asia/Ho_Chi_Minh",
    source_completeness="COMPLETE",
):
    return AuthorizedOutstandingInvoiceObservation(
        invoice_id=invoice_id,
        tenant_id=tenant_id,
        company_id=company_id,
        source_system="TEST_SYS",
        document_version="ver_1",
        lifecycle_status=lifecycle_status,
        is_return=is_return,
        is_credit_note=is_credit_note,
        is_write_off=is_write_off,
        posting_date=posting_date,
        final_due_date=final_due_date,
        party_account_currency=party_account_currency,
        invoice_currency=invoice_currency,
        outstanding_balance=outstanding_balance,
        observed_at_utc=observed_at_utc,
        site_timezone=site_timezone,
        source_completeness=source_completeness,
        authorized_scope=f"{tenant_id}:{company_id}",
    )


def test_positive_eligible_case():
    obs = make_test_observation()
    res = PastFinalDueEvaluator.evaluate(
        obs, authorized_tenant_id="tenant_alpha", authorized_company_id="Company Alpha"
    )
    assert res.decision == EligibilityDecision.ELIGIBLE
    assert res.outstanding_balance == Decimal("1000000.00")
    assert res.overdue_days == 12  # Oct 13 - Oct 1 = 12 days


def test_due_date_boundaries():
    # Observed instant is Oct 13, 2026 12:00 UTC (19:00 Saigon -> Oct 13 local date)
    
    # 1. Due yesterday (Oct 12) -> ELIGIBLE
    obs_yesterday = make_test_observation(final_due_date=date(2026, 10, 12))
    res = PastFinalDueEvaluator.evaluate(obs_yesterday, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.ELIGIBLE
    assert res.overdue_days == 1

    # 2. Due TODAY (Oct 13) -> NOT_ELIGIBLE (Due today is not past final due!)
    obs_today = make_test_observation(final_due_date=date(2026, 10, 13))
    res = PastFinalDueEvaluator.evaluate(obs_today, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "not earlier than site date" in res.reason

    # 3. Due tomorrow (Oct 14) -> NOT_ELIGIBLE
    obs_tomorrow = make_test_observation(final_due_date=date(2026, 10, 14))
    res = PastFinalDueEvaluator.evaluate(obs_tomorrow, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE


def test_site_timezone_and_local_midnight():
    # Observed at 2026-10-12T18:00:00Z
    # In UTC, date is Oct 12.
    # In Asia/Ho_Chi_Minh (+7), time is 2026-10-13 01:00 AM -> date is Oct 13!
    obs_hcm = make_test_observation(
        final_due_date=date(2026, 10, 12),
        observed_at_utc="2026-10-12T18:00:00+00:00",
        site_timezone="Asia/Ho_Chi_Minh",
    )
    res_hcm = PastFinalDueEvaluator.evaluate(obs_hcm, "tenant_alpha", "Company Alpha")
    # Due Oct 12 vs site local date Oct 13 -> strictly past due!
    assert res_hcm.decision == EligibilityDecision.ELIGIBLE

    # In UTC (Europe/London or UTC), date is Oct 12.
    # Due Oct 12 vs site local date Oct 12 -> Due TODAY -> NOT_ELIGIBLE!
    obs_utc = make_test_observation(
        final_due_date=date(2026, 10, 12),
        observed_at_utc="2026-10-12T18:00:00+00:00",
        site_timezone="UTC",
    )
    res_utc = PastFinalDueEvaluator.evaluate(obs_utc, "tenant_alpha", "Company Alpha")
    assert res_utc.decision == EligibilityDecision.NOT_ELIGIBLE


def test_outstanding_residual_boundaries():
    # 1. Zero residual -> Settled -> NOT_ELIGIBLE
    obs_zero = make_test_observation(outstanding_balance="0.00")
    res = PastFinalDueEvaluator.evaluate(obs_zero, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "not strictly positive" in res.reason

    # 2. Negative residual -> Credit/Overpaid -> NOT_ELIGIBLE (never substitute zero or treat as payable)
    obs_neg = make_test_observation(outstanding_balance="-1500.00")
    res = PastFinalDueEvaluator.evaluate(obs_neg, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "not strictly positive" in res.reason

    # 3. Partial payment positive residual -> ELIGIBLE
    obs_partial = make_test_observation(outstanding_balance="250.75")
    res = PastFinalDueEvaluator.evaluate(obs_partial, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.ELIGIBLE
    assert res.outstanding_balance == Decimal("250.75")


def test_return_credit_and_write_off_exclusion():
    # Return document
    obs_ret = make_test_observation(is_return=True)
    res = PastFinalDueEvaluator.evaluate(obs_ret, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "return" in res.reason

    # Credit note
    obs_cn = make_test_observation(is_credit_note=True)
    res = PastFinalDueEvaluator.evaluate(obs_cn, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE

    # Write-off
    obs_wo = make_test_observation(is_write_off=True)
    res = PastFinalDueEvaluator.evaluate(obs_wo, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE


def test_lifecycle_status_filtering():
    # Draft -> NOT_ELIGIBLE
    obs_draft = make_test_observation(lifecycle_status="DRAFT")
    res = PastFinalDueEvaluator.evaluate(obs_draft, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "not submitted/approved" in res.reason

    # Cancelled -> NOT_ELIGIBLE
    obs_canc = make_test_observation(lifecycle_status="CANCELLED")
    res = PastFinalDueEvaluator.evaluate(obs_canc, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.NOT_ELIGIBLE


def test_tenant_and_company_isolation():
    obs = make_test_observation(tenant_id="tenant_alpha", company_id="Company Alpha")

    # Wrong tenant
    res_tenant = PastFinalDueEvaluator.evaluate(obs, "tenant_beta", "Company Alpha")
    assert res_tenant.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "Tenant scope mismatch" in res_tenant.reason

    # Wrong company
    res_comp = PastFinalDueEvaluator.evaluate(obs, "tenant_alpha", "Company Beta")
    assert res_comp.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "Company scope mismatch" in res_comp.reason


def test_currency_filtering():
    obs = make_test_observation(party_account_currency="USD", invoice_currency="USD")
    # Filter matches
    res_match = PastFinalDueEvaluator.evaluate(obs, "tenant_alpha", "Company Alpha", expected_currency="USD")
    assert res_match.decision == EligibilityDecision.ELIGIBLE

    # Filter mismatch
    res_mismatch = PastFinalDueEvaluator.evaluate(obs, "tenant_alpha", "Company Alpha", expected_currency="VND")
    assert res_mismatch.decision == EligibilityDecision.NOT_ELIGIBLE
    assert "does not match filter" in res_mismatch.reason


def test_future_posted_document_trap():
    # Posting date is in the future relative to site date
    obs_future = make_test_observation(posting_date=date(2026, 10, 20), final_due_date=date(2026, 10, 1))
    res = PastFinalDueEvaluator.evaluate(obs_future, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.UNQUALIFIED
    assert "Future-posted document" in res.reason


def test_unqualified_or_incomplete_data():
    obs_incomplete = make_test_observation(source_completeness="PARTIAL")
    res = PastFinalDueEvaluator.evaluate(obs_incomplete, "tenant_alpha", "Company Alpha")
    assert res.decision == EligibilityDecision.UNQUALIFIED


def test_nonfinite_or_invalid_decimal_rejection():
    with pytest.raises(ValidationError):
        make_test_observation(outstanding_balance="NaN")
    with pytest.raises(ValidationError):
        make_test_observation(outstanding_balance="Infinity")
    with pytest.raises(ValidationError):
        make_test_observation(outstanding_balance="invalid_str")
