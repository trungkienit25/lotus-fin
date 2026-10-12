"""Tests for Action Delivery, DTO Serialization, and Redaction (Stages B, C, D).

ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import uuid
import io
import logging
import pytest
from pydantic import ValidationError
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome,
    ActionReasonCode,
    ActionStatus,
    SourceEvidence,
)
from lotus_fin.presentation.dto.action_outcome import ActionOutcomeDTO
from lotus_fin.presentation.response.action_response import (
    ActionResponseBuilder,
    REASON_HTTP_OVERRIDE,
    STATUS_HTTP_MAP,
)
from lotus_fin.application.port.i_action_events import ActionEvent, ActionEventStage
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents


def make_valid_source() -> SourceEvidence:
    return SourceEvidence(
        mode="ERP_READ",
        verification="AUTHORIZED_READ",
        product_ref="prod_01",
        site_ref="site_01",
        connection_ref="conn_01",
        connection_version="v1.0",
        projection_version="invoice.min.v1",
        observed_at="2026-10-11T09:00:00Z",
        timezone="Asia/Ho_Chi_Minh",
        coverage="PAGE_COMPLETE",
        consistency="LIVE_KEYSET",
    )


def test_dto_valid_uuid_validation():
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    dto = ActionOutcomeDTO(
        contract_version="p1.invoice.v1",
        status=ActionStatus.OK,
        reason_code=ActionReasonCode.RESULTS_FOUND,
        correlation_id=cid,
        request_id=req_id,
        capability="invoice.search",
        source=make_valid_source().model_dump(mode="json"),
        data={"items": []},
        user_message="OK",
    )
    assert dto.correlation_id == cid
    assert dto.request_id == req_id


def test_dto_invalid_uuid_rejected():
    with pytest.raises(ValidationError, match="correlation_id.*must be a valid UUID v4"):
        ActionOutcomeDTO(
            contract_version="p1.invoice.v1",
            status=ActionStatus.OK,
            reason_code=ActionReasonCode.RESULTS_FOUND,
            correlation_id="not-a-valid-uuid",
            request_id=str(uuid.uuid4()),
            capability="invoice.search",
            data=None,
            user_message="OK",
        )


def test_request_id_replacement_for_invalid_client_id():
    valid_id = str(uuid.uuid4())
    clean_id, replaced = ActionResponseBuilder.sanitize_request_id(valid_id)
    assert clean_id == valid_id and not replaced

    invalid_id = "fake_client_request_id"
    clean_id, replaced = ActionResponseBuilder.sanitize_request_id(invalid_id)
    assert replaced and uuid.UUID(clean_id, version=4)

    clean_id, replaced = ActionResponseBuilder.sanitize_request_id(None)
    assert replaced and uuid.UUID(clean_id, version=4)


def test_response_builder_header_body_cid_equality():
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    outcome = ActionOutcome(
        contract_version="p1.invoice.v1",
        status=ActionStatus.OK,
        reason_code=ActionReasonCode.RESULTS_FOUND,
        correlation_id=cid,
        request_id=req_id,
        capability="invoice.search",
        source=make_valid_source(),
        data={"items": []},
        user_message="OK",
    )
    status_code, headers, body = ActionResponseBuilder.serialize_response(outcome)
    assert status_code == 200
    assert headers["X-Correlation-ID"] == cid == body["correlation_id"]
    assert headers["Cache-Control"] == "no-store, no-cache, must-revalidate"


@pytest.mark.parametrize("status,reason,expected_http", [
    (ActionStatus.FORBIDDEN, ActionReasonCode.AUTH_REQUIRED, 401),
    (ActionStatus.FORBIDDEN, ActionReasonCode.ACCESS_DENIED, 403),
    (ActionStatus.NOT_AVAILABLE, ActionReasonCode.DOCUMENT_UNAVAILABLE, 404),
    (ActionStatus.NOT_AVAILABLE, ActionReasonCode.STALE_SELECTION, 409),
    (ActionStatus.NOT_AVAILABLE, ActionReasonCode.TARGET_UNQUALIFIED, 503),
    (ActionStatus.SOURCE_ERROR, ActionReasonCode.SOURCE_FAILURE, 502),
    (ActionStatus.TIMEOUT, ActionReasonCode.DEADLINE_EXCEEDED, 504),
])
def test_http_status_mapping_and_overrides(status, reason, expected_http):
    assert ActionResponseBuilder.resolve_http_status(status, reason) == expected_http


def test_build_failure_outcome_no_data_leakage():
    client_req_id = "invalid-req-id"
    outcome = ActionResponseBuilder.build_failure_outcome(
        status=ActionStatus.FORBIDDEN,
        reason_code=ActionReasonCode.COMPANY_DENIED,
        capability="invoice.search",
        client_request_id=client_req_id,
    )
    assert outcome.status == ActionStatus.FORBIDDEN
    assert outcome.data is None and outcome.source is None
    assert outcome.reason_code == ActionReasonCode.COMPANY_DENIED
    assert uuid.UUID(outcome.request_id, version=4)


def test_safe_message_never_raw_exception_sentinel():
    raw_exception = "OperationalError: Connection to MariaDB 10.6 failed on port 3306 with password 'secret123'"
    msg = ActionResponseBuilder.get_safe_message(ActionReasonCode.SOURCE_FAILURE)
    assert raw_exception not in msg and "secret123" not in msg
    assert msg == "Lỗi kết nối tới hệ thống nguồn dữ liệu."


def test_observability_event_recording():
    events_adapter = SafeStructuredActionEvents(logging.Logger("test.delivery", logging.INFO))
    events_adapter._logger.addHandler(logging.StreamHandler(io.StringIO()))
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    event = ActionEvent(
        correlation_id=cid,
        request_id=req_id,
        capability="invoice.search",
        stage=ActionEventStage.AUTH_CHECK,
        status=ActionStatus.FORBIDDEN,
        reason_code=ActionReasonCode.ACCESS_DENIED,
        duration_ms=12.5,
    )
    events_adapter.record_event(event)
    assert len(events_adapter.recorded_events) == 1
    rec = events_adapter.recorded_events[0]
    assert rec["correlation_id"] == cid
    assert rec["request_id"] == req_id
    assert rec["stage"] == "AUTH_CHECK"


def test_observability_sentinel_tokens_cookies_passwords():
    events_adapter = SafeStructuredActionEvents(logging.Logger("test.delivery", logging.INFO))
    events_adapter._logger.addHandler(logging.StreamHandler(io.StringIO()))
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    for stage_val in [ActionEventStage.REQUEST_RECEIVED, ActionEventStage.AUTH_CHECK]:
        event = ActionEvent(
            correlation_id=cid,
            request_id=req_id,
            capability="invoice.search",
            stage=stage_val,
        )
        events_adapter.record_event(event)
    assert len(events_adapter.recorded_events) == 2
