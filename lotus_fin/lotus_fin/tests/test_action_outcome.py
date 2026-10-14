"""Tests for Action Outcome Domain Schema (Stage A).

Validates strict P1 contract, matrix, null data on failures, source evidence rules.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import pytest
from pydantic import ValidationError
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome,
    ActionReasonCode,
    ActionStatus,
    SourceEvidence,
    STATUS_REASON_MATRIX,
)


def valid_source(coverage="PAGE_COMPLETE") -> SourceEvidence:
    return SourceEvidence(
        mode="ERP_READ",
        verification="AUTHORIZED_READ",
        product_ref="prod_lotus_01",
        site_ref="site_erp_main",
        connection_ref="conn_direct",
        connection_version="v1.0",
        projection_version="invoice.min.v1",
        observed_at="2026-10-11T09:00:00Z",
        timezone="Asia/Ho_Chi_Minh",
        coverage=coverage,
        consistency="LIVE_KEYSET",
    )


def test_valid_ok_outcome():
    outcome = ActionOutcome(
        contract_version="p1.invoice.v1",
        status=ActionStatus.OK,
        reason_code=ActionReasonCode.RESULTS_FOUND,
        correlation_id="cid-12345",
        request_id="req-67890",
        capability="invoice.search",
        source=valid_source("PAGE_COMPLETE"),
        context_version="ctx-v1",
        data={"items": [{"invoice_id": "SINV-001"}]},
        user_message="Tìm thấy kết quả",
    )
    assert outcome.status == ActionStatus.OK
    assert outcome.data == {"items": [{"invoice_id": "SINV-001"}]}


def test_valid_partial_outcome():
    outcome = ActionOutcome(
        contract_version="p1.invoice.v1",
        status=ActionStatus.PARTIAL,
        reason_code=ActionReasonCode.COVERAGE_INCOMPLETE,
        correlation_id="cid-12345",
        request_id="req-67890",
        capability="invoice.search",
        source=valid_source("INCOMPLETE"),
        context_version="ctx-v1",
        data={"items": []},
        user_message="Dữ liệu một phần",
    )
    assert outcome.status == ActionStatus.PARTIAL
    assert outcome.source.coverage == "INCOMPLETE"


def test_partial_rejects_page_complete_coverage():
    with pytest.raises(ValidationError, match="PARTIAL status requires source coverage='INCOMPLETE'"):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.PARTIAL,
            reason_code=ActionReasonCode.COVERAGE_INCOMPLETE,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            source=valid_source("PAGE_COMPLETE"),
            context_version="ctx-v1",
            data={"items": []},
            user_message="Dữ liệu một phần",
        )


def test_ok_requires_source():
    with pytest.raises(ValidationError, match="OK status requires valid source evidence"):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.OK,
            reason_code=ActionReasonCode.RESULTS_FOUND,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            source=None,
            context_version="ctx-v1",
            data={"items": []},
            user_message="OK missing source",
        )


@pytest.mark.parametrize("status,reason", [
    (ActionStatus.FORBIDDEN, ActionReasonCode.AUTH_REQUIRED),
    (ActionStatus.SOURCE_ERROR, ActionReasonCode.SOURCE_FAILURE),
    (ActionStatus.TIMEOUT, ActionReasonCode.DEADLINE_EXCEEDED),
    (ActionStatus.NOT_AVAILABLE, ActionReasonCode.INVALID_REQUEST),
])
def test_failure_statuses_must_have_null_data(status, reason):
    with pytest.raises(ValidationError, match="Data must be null for status"):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=status,
            reason_code=reason,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            source=None,
            data={"leaked_data": "sensitive"},
            user_message="Failure with data",
        )


def test_failure_statuses_must_not_have_source():
    with pytest.raises(ValidationError, match="Source evidence must be null for failure status"):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.FORBIDDEN,
            reason_code=ActionReasonCode.ACCESS_DENIED,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            source=valid_source(),
            data=None,
            user_message="Forbidden with source",
        )


def test_incompatible_reason_code_rejected():
    with pytest.raises(ValidationError, match="is incompatible with status"):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.OK,
            reason_code=ActionReasonCode.ACCESS_DENIED,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            source=valid_source(),
            data={},
            user_message="Incompatible",
        )


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.NOT_AVAILABLE,
            reason_code=ActionReasonCode.INVALID_REQUEST,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            data=None,
            user_message="Invalid",
            extra_field="malicious_payload",
        )


def test_unknown_contract_version_rejected():
    with pytest.raises(ValidationError):
        ActionOutcome(
            contract_version="p2.invoice.v2",
            status=ActionStatus.NOT_AVAILABLE,
            reason_code=ActionReasonCode.INVALID_REQUEST,
            correlation_id="cid-12345",
            request_id="req-67890",
            capability="invoice.search",
            data=None,
            user_message="Bad version",
        )
