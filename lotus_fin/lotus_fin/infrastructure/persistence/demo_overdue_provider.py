"""Demo Provider for overdue invoice observations.

Fixed fictional invoice observations clearly labeled DEMO DATA.
Deterministic financial oracle; isolated from production keys/state.
SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §5.
"""

from datetime import date
from typing import List, Optional, Tuple

from lotus_fin.application.port.i_overdue_observation_port import IAuthorizedOverdueObservationPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams


class DemoOverdueObservationProvider(IAuthorizedOverdueObservationPort):
    """Isolated Demo Provider serving fixed fictional records for simulated E2E."""

    def __init__(self, records: Optional[List[AuthorizedOutstandingInvoiceObservation]] = None) -> None:
        self.records = records if records is not None else self._default_demo_records()

    def _default_demo_records(self) -> List[AuthorizedOutstandingInvoiceObservation]:
        """Provides verified standard demo invoices."""
        return [
            AuthorizedOutstandingInvoiceObservation(
                invoice_id="DEMO-INV-001",
                tenant_id="site_demo",
                company_id="Lotus Demo Corp",
                source_system="DEMO_ISOLATED",
                document_version="v_demo_1",
                lifecycle_status="SUBMITTED",
                is_return=False,
                is_credit_note=False,
                is_write_off=False,
                posting_date=date(2026, 9, 1),
                final_due_date=date(2026, 10, 1),  # Past due relative to Oct 13, 2026
                party_account_currency="VND",
                invoice_currency="VND",
                outstanding_balance="15000000.00",
                currency_precision=2,
                observed_at_utc="2026-10-13T12:00:00+00:00",
                site_timezone="Asia/Ho_Chi_Minh",
                source_completeness="COMPLETE",
                authorized_scope="site_demo:Lotus Demo Corp",
                provenance_hash="demo_hash_001",
            ),
            AuthorizedOutstandingInvoiceObservation(
                invoice_id="DEMO-INV-002",
                tenant_id="site_demo",
                company_id="Lotus Demo Corp",
                source_system="DEMO_ISOLATED",
                document_version="v_demo_2",
                lifecycle_status="SUBMITTED",
                is_return=False,
                is_credit_note=False,
                is_write_off=False,
                posting_date=date(2026, 9, 15),
                final_due_date=date(2026, 10, 5),  # Past due relative to Oct 13, 2026
                party_account_currency="VND",
                invoice_currency="VND",
                outstanding_balance="2850000.50",
                currency_precision=2,
                observed_at_utc="2026-10-13T12:00:00+00:00",
                site_timezone="Asia/Ho_Chi_Minh",
                source_completeness="COMPLETE",
                authorized_scope="site_demo:Lotus Demo Corp",
                provenance_hash="demo_hash_002",
            ),
            # Settled invoice - balance 0 (should be excluded by predicate)
            AuthorizedOutstandingInvoiceObservation(
                invoice_id="DEMO-INV-003",
                tenant_id="site_demo",
                company_id="Lotus Demo Corp",
                source_system="DEMO_ISOLATED",
                document_version="v_demo_3",
                lifecycle_status="SUBMITTED",
                is_return=False,
                is_credit_note=False,
                is_write_off=False,
                posting_date=date(2026, 9, 1),
                final_due_date=date(2026, 9, 20),
                party_account_currency="VND",
                invoice_currency="VND",
                outstanding_balance="0.00",
                currency_precision=2,
                observed_at_utc="2026-10-13T12:00:00+00:00",
                site_timezone="Asia/Ho_Chi_Minh",
                source_completeness="COMPLETE",
                authorized_scope="site_demo:Lotus Demo Corp",
                provenance_hash="demo_hash_003",
            ),
            # Return document (should be excluded by predicate)
            AuthorizedOutstandingInvoiceObservation(
                invoice_id="DEMO-RET-004",
                tenant_id="site_demo",
                company_id="Lotus Demo Corp",
                source_system="DEMO_ISOLATED",
                document_version="v_demo_4",
                lifecycle_status="SUBMITTED",
                is_return=True,
                is_credit_note=False,
                is_write_off=False,
                posting_date=date(2026, 10, 1),
                final_due_date=date(2026, 10, 10),
                party_account_currency="VND",
                invoice_currency="VND",
                outstanding_balance="500000.00",
                currency_precision=2,
                observed_at_utc="2026-10-13T12:00:00+00:00",
                site_timezone="Asia/Ho_Chi_Minh",
                source_completeness="COMPLETE",
                authorized_scope="site_demo:Lotus Demo Corp",
                provenance_hash="demo_hash_004",
            ),
            # Due today / future (should be excluded by predicate)
            AuthorizedOutstandingInvoiceObservation(
                invoice_id="DEMO-INV-005",
                tenant_id="site_demo",
                company_id="Lotus Demo Corp",
                source_system="DEMO_ISOLATED",
                document_version="v_demo_5",
                lifecycle_status="SUBMITTED",
                is_return=False,
                is_credit_note=False,
                is_write_off=False,
                posting_date=date(2026, 10, 1),
                final_due_date=date(2026, 10, 13),  # Due TODAY in Asia/Ho_Chi_Minh
                party_account_currency="VND",
                invoice_currency="VND",
                outstanding_balance="7200000.00",
                currency_precision=2,
                observed_at_utc="2026-10-13T12:00:00+00:00",
                site_timezone="Asia/Ho_Chi_Minh",
                source_completeness="COMPLETE",
                authorized_scope="site_demo:Lotus Demo Corp",
                provenance_hash="demo_hash_005",
            ),
        ]

    def scan_invoice_observations(
        self,
        context: AuthorizedReadContext,
        filters: PastFinalDueFilterParams,
        max_scan_limit: int = 250,
        cursor: Optional[str] = None,
    ) -> Tuple[
        List[AuthorizedOutstandingInvoiceObservation],
        Optional[SourceEvidence],
        bool,
        ActionStatus,
        ActionReasonCode,
        Optional[str],
    ]:
        # Filter strictly by context tenant/company
        matching = [
            r for r in self.records
            if r.tenant_id == context.site_id and r.company_id == context.company_id
        ]

        is_truncated = len(matching) > max_scan_limit
        selected_records = matching[:max_scan_limit]

        source = SourceEvidence(
            mode="DEMO_ISOLATED",
            verification="AUTHORIZED_READ",
            product_ref=context.product_id,
            site_ref=context.site_id,
            connection_ref="demo_conn",
            connection_version="demo.v1",
            projection_version="invoice.min.v1",
            observed_at=context.observed_at_utc,
            timezone=context.timezone,
            coverage="PAGE_COMPLETE" if not is_truncated else "INCOMPLETE",
            consistency="LIVE_KEYSET",
        )

        return (
            selected_records,
            source,
            is_truncated,
            ActionStatus.OK,
            ActionReasonCode.RESULTS_FOUND if selected_records else ActionReasonCode.EMPTY_RESULT,
            None,
        )
