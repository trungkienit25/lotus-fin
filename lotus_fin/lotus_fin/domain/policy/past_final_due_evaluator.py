"""Deterministic financial eligibility evaluator for PAST_FINAL_DUE_INVOICES.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §1, §3, §4, §5.
Rules:
- Submitted/approved lifecycle according to source contract.
- Not a return or credit document or write-off.
- Verified final due date strictly earlier than the server-observed site-local date.
- Current outstanding balance strictly greater than zero (using Decimal, never float).
- Correct party-account currency (no FX synthesis or cross-currency mixing).
- Within authorized source/tenant scope.
- Due today is NOT past-final-due.
- Never substitute zero or estimate balances.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import NamedTuple, Optional
import zoneinfo

from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation


class EligibilityDecision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    UNQUALIFIED = "UNQUALIFIED"


class EvaluationResult(NamedTuple):
    decision: EligibilityDecision
    reason: str
    overdue_days: Optional[int] = None
    outstanding_balance: Optional[Decimal] = None
    currency: Optional[str] = None


class PastFinalDueEvaluator:
    """Deterministic predicate engine for PAST_FINAL_DUE_INVOICES (Option B)."""

    APPROVED_LIFECYCLES = {"SUBMITTED", "APPROVED", "POSTED", "1"}

    @classmethod
    def get_site_local_date(cls, observed_at_utc_iso: str, site_timezone: str) -> date:
        """Determines the site-local calendar date at the instant of observation."""
        dt_utc = datetime.fromisoformat(observed_at_utc_iso.replace("Z", "+00:00"))
        tz = zoneinfo.ZoneInfo(site_timezone)
        dt_local = dt_utc.astimezone(tz)
        return dt_local.date()

    @classmethod
    def evaluate(
        cls,
        observation: AuthorizedOutstandingInvoiceObservation,
        authorized_tenant_id: str,
        authorized_company_id: str,
        expected_currency: Optional[str] = None,
    ) -> EvaluationResult:
        """Evaluates whether an observed invoice is strictly past final due."""

        # 1. Authority & Scope check
        if observation.tenant_id != authorized_tenant_id:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Tenant scope mismatch: {observation.tenant_id} != {authorized_tenant_id}"
            )

        if observation.company_id != authorized_company_id:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Company scope mismatch: {observation.company_id} != {authorized_company_id}"
            )

        # 2. Source completeness check
        if observation.source_completeness != "COMPLETE":
            return EvaluationResult(
                EligibilityDecision.UNQUALIFIED,
                f"Source record incomplete or not independently qualified: {observation.source_completeness}"
            )

        # 3. Document lifecycle check
        if observation.lifecycle_status.upper() not in cls.APPROVED_LIFECYCLES:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Document lifecycle '{observation.lifecycle_status}' is not submitted/approved."
            )

        # 4. Return, Credit note, Write-off exclusion
        if observation.is_return or observation.is_credit_note or observation.is_write_off:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                "Document is a return, credit note, or write-off."
            )

        # 5. Currency sanity: Party-account currency vs invoice currency
        if expected_currency and observation.party_account_currency != expected_currency:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Party-account currency {observation.party_account_currency} does not match filter {expected_currency}"
            )

        # 6. Outstanding residual balance check (strictly Decimal)
        balance = observation.outstanding_decimal
        if balance <= Decimal("0"):
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Current outstanding residual {balance} is not strictly positive."
            )

        # 7. Date calculation at site-local midnight
        site_local_date = cls.get_site_local_date(
            observation.observed_at_utc,
            observation.site_timezone
        )

        # Future-posted invoice check (trap detection)
        if observation.posting_date > site_local_date:
            return EvaluationResult(
                EligibilityDecision.UNQUALIFIED,
                f"Future-posted document: posting date {observation.posting_date} > site date {site_local_date}"
            )

        # Strict predicate: final_due_date < site_local_date
        # Due today is NOT past-final-due!
        if observation.final_due_date >= site_local_date:
            return EvaluationResult(
                EligibilityDecision.NOT_ELIGIBLE,
                f"Final due date {observation.final_due_date} is not earlier than site date {site_local_date}."
            )

        overdue_days = (site_local_date - observation.final_due_date).days

        return EvaluationResult(
            decision=EligibilityDecision.ELIGIBLE,
            reason="Verified submitted non-return invoice with positive residual past final due date.",
            overdue_days=overdue_days,
            outstanding_balance=balance,
            currency=observation.party_account_currency,
        )
