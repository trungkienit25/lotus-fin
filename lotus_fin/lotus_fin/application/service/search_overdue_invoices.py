"""Application Service for Searching Overdue Invoices (PastFinalDue).

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §3, §4, §5.
"""

from datetime import date
from typing import List, Optional, Tuple

from lotus_fin.application.port.i_overdue_observation_port import IAuthorizedOverdueObservationPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.policy.past_final_due_evaluator import EligibilityDecision, PastFinalDueEvaluator
from lotus_fin.domain.schema.action_outcome import ActionOutcome, ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.overdue_invoice_read import (
    OverdueScanCoverage,
    PastFinalDueFilterParams,
    PastFinalDueInvoiceItem,
    PastFinalDueResponseData,
)
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


class SearchOverdueInvoicesService:
    """Orchestrates deterministic predicate evaluation over typed observation ports."""

    def __init__(
        self,
        port: IAuthorizedOverdueObservationPort,
        codec: Optional[ActionReferenceCodec] = None,
        provider_mode: str = "CORE",
    ) -> None:
        self.port = port
        self.codec = codec
        self.provider_mode = provider_mode

    def execute(
        self,
        context: AuthorizedReadContext,
        filters: Optional[PastFinalDueFilterParams] = None,
        page_size: int = 50,
        max_scan_limit: int = 250,
        cursor: Optional[str] = None,
    ) -> Tuple[Optional[PastFinalDueResponseData], Optional[SourceEvidence], ActionStatus, ActionReasonCode]:
        filters = filters or PastFinalDueFilterParams()

        # Step 1: Scan candidates from authorized port
        observations, source_evidence, is_truncated, status, reason, next_cursor = (
            self.port.scan_invoice_observations(
                context=context,
                filters=filters,
                max_scan_limit=max_scan_limit,
                cursor=cursor,
            )
        )

        if status != ActionStatus.OK and status != ActionStatus.PARTIAL:
            return None, None, status, reason

        site_local_date = PastFinalDueEvaluator.get_site_local_date(
            context.observed_at_utc,
            context.timezone,
        )

        eligible_items: List[PastFinalDueInvoiceItem] = []
        missing_data_encountered = False

        # Step 2: Evaluate each candidate through deterministic predicate
        for obs in observations:
            eval_res = PastFinalDueEvaluator.evaluate(
                observation=obs,
                authorized_tenant_id=context.site_id,
                authorized_company_id=context.company_id,
                expected_currency=filters.party_account_currency,
            )

            if eval_res.decision == EligibilityDecision.UNQUALIFIED:
                missing_data_encountered = True
                continue

            if eval_res.decision == EligibilityDecision.ELIGIBLE:
                # Apply optional min_overdue_days filter
                if filters.min_overdue_days and eval_res.overdue_days < filters.min_overdue_days:
                    continue

                # Apply prefix filter if requested
                if filters.invoice_id_prefix and not obs.invoice_id.startswith(filters.invoice_id_prefix):
                    continue

                # Sign selection reference if codec is available and complete coverage
                selection_ref = None
                if self.codec and not missing_data_encountered and not is_truncated:
                    selection_ref = self.codec.sign_selection_v2(
                        context=context,
                        doc_id=obs.invoice_id,
                        record_version=obs.document_version,
                    )

                item = PastFinalDueInvoiceItem(
                    invoice_id=obs.invoice_id,
                    final_due_date=obs.final_due_date,
                    current_outstanding_decimal=str(eval_res.outstanding_balance),
                    party_account_currency=eval_res.currency,
                    source_modified=obs.document_version,
                    selection_ref=selection_ref,
                    overdue_days=eval_res.overdue_days,
                    evidence_ref=obs.provenance_hash or f"src:{obs.source_system}:{obs.invoice_id}",
                )
                eligible_items.append(item)

        # Truncate to requested page_size
        returned_items = eligible_items[:page_size]
        limitations: List[str] = []

        is_complete = not is_truncated and not missing_data_encountered and (status == ActionStatus.OK)

        if is_truncated:
            limitations.append("SCAN_WINDOW_TRUNCATED")
        if missing_data_encountered:
            limitations.append("UNQUALIFIED_DATA_EXCLUDED")
        if self.provider_mode == "DEMO":
            limitations.append("DEMO_FICTIONAL_DATA")

        # Determine final status
        final_status = ActionStatus.OK if is_complete else ActionStatus.PARTIAL
        final_reason = (
            ActionReasonCode.RESULTS_FOUND
            if (returned_items and is_complete)
            else (
                ActionReasonCode.EMPTY_RESULT
                if (not returned_items and is_complete)
                else ActionReasonCode.COVERAGE_INCOMPLETE
            )
        )

        # If PARTIAL coverage, clear selection refs to uphold security invariant
        if final_status == ActionStatus.PARTIAL:
            returned_items = [
                item.model_copy(update={"selection_ref": None}) for item in returned_items
            ]

        # Update source evidence coverage
        if source_evidence:
            source_evidence = source_evidence.model_copy(
                update={"coverage": "PAGE_COMPLETE" if is_complete else "INCOMPLETE"}
            )

        coverage = OverdueScanCoverage(
            complete=is_complete,
            fetched_rows=len(observations),
            scanned_rows=len(observations),
            returned_rows=len(returned_items),
            missing_required_data=missing_data_encountered,
            truncated=is_truncated,
            reason="; ".join(limitations) if limitations else None,
        )

        response_data = PastFinalDueResponseData(
            capability="PAST_FINAL_DUE_INVOICES",
            contract_version="p6.overdue.v1",
            observed_at_utc=context.observed_at_utc,
            site_local_date=site_local_date,
            site_timezone=context.timezone,
            authorized_scope=f"{context.site_id}:{context.company_id}",
            provider_mode=self.provider_mode,
            items=returned_items,
            coverage=coverage,
            limitations=limitations,
            next_cursor=next_cursor,
        )

        return response_data, source_evidence, final_status, final_reason
