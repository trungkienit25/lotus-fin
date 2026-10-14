"""Independent Security & Contract Regression Tests (N01-N12, A13-A16).

Validates F01-F04 counterexamples from independent Work review.
SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import io
import logging
import uuid
import pytest
from pydantic import ValidationError
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome,
    ActionReasonCode as R,
    ActionStatus as S,
    SourceEvidence,
)
from lotus_fin.presentation.dto.action_outcome import ActionOutcomeDTO
from lotus_fin.presentation.response.action_response import ActionResponseBuilder as B
from lotus_fin.application.port.i_action_events import (
    ActionEvent,
    ActionEventDeliveryError,
    ActionEventStage,
)
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents


def make_source(**changes):
    values = dict(
        mode="ERP_READ", product_ref="p", site_ref="s", connection_ref="c",
        connection_version="v1", observed_at="2026-10-11T09:00:00Z",
        timezone="Asia/Ho_Chi_Minh", coverage="PAGE_COMPLETE",
    )
    values.update(changes)
    return SourceEvidence(**values)


def make_outcome(**changes):
    values = dict(
        status=S.OK, reason_code=R.RESULTS_FOUND,
        correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
        capability="invoice.search", source=make_source(), context_version="ctx_p1a",
        data={"items": []}, user_message="Tìm thấy danh sách hóa đơn phù hợp.",
    )
    values.update(changes)
    return ActionOutcome(**values)


def test_n01_ok_with_incomplete_source_rejected():
    with pytest.raises(ValidationError, match="OK status requires source coverage='PAGE_COMPLETE'"):
        make_outcome(source=make_source(coverage="INCOMPLETE"))


def test_n02_invalid_observation_timestamp_or_timezone():
    with pytest.raises(ValidationError, match="observed_at.*must be a valid ISO 8601"):
        make_source(observed_at="not-a-date")
    with pytest.raises(ValidationError, match="timezone.*must be a valid IANA timezone"):
        make_source(timezone="invalid/timezone")


def test_n03_partial_carrying_selection_ref_rejected():
    with pytest.raises(ValidationError, match="PARTIAL outcome cannot issue selection_ref"):
        make_outcome(
            status=S.PARTIAL, reason_code=R.COVERAGE_INCOMPLETE,
            source=make_source(coverage="INCOMPLETE"),
            data={"items": [{"invoice_id": "SINV-001", "selection_ref": "ref-secret"}]},
        )


def test_n04_outer_ok_containing_nested_denial_rejected():
    with pytest.raises(ValidationError, match="OK outcome cannot contain recognized nested denial"):
        make_outcome(
            data={"nested": {"status": "FORBIDDEN", "reason_code": "ACCESS_DENIED", "canary": "CANARY_123"}}
        )


def test_n05_mutated_forbidden_data_null_at_delivery():
    o = make_outcome(status=S.FORBIDDEN, reason_code=R.ACCESS_DENIED, source=None, data=None)
    o.data = {"private": "P1A_CANARY_7428"}
    status_code, headers, body = B.serialize_response(o)
    assert status_code == 403 and body["data"] is None and body["source"] is None


def test_n06_arbitrary_user_message_replaced_with_safe_template():
    o = make_outcome(status=S.SOURCE_ERROR, reason_code=R.SOURCE_FAILURE, source=None, data=None)
    o.user_message = "OperationalError sid=P1A_CANARY_7428"
    status_code, headers, body = B.serialize_response(o)
    assert status_code == 502 and body["user_message"] == "Lỗi kết nối tới hệ thống nguồn dữ liệu."


def test_n07_direct_dto_rejects_unapproved_fields():
    with pytest.raises(ValidationError):
        ActionOutcomeDTO(
            contract_version="unapproved.v99", status=S.OK, reason_code=R.RESULTS_FOUND,
            correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
            capability="invoice.search", user_message="msg",
        )


def test_n08_n09_n10_event_privacy_and_closed_stage():
    for kw in [{"context_ref": "s=CANARY"}, {"actor_ref": "c@inv"}, {"stage": "ERR CANARY"}]:
        b = {"correlation_id": str(uuid.uuid4()), "request_id": str(uuid.uuid4()), "capability": "invoice.search", "stage": ActionEventStage.AUTH_CHECK}
        b.update(kw)
        with pytest.raises(ValidationError):
            ActionEvent(**b)  # type: ignore


def test_n11_event_validation_of_ids_capability_and_pair():
    for kw in [{"correlation_id": "bad"}, {"capability": "rpc"}, {"status": S.OK, "reason_code": R.ACCESS_DENIED}]:
        b = {"correlation_id": str(uuid.uuid4()), "request_id": str(uuid.uuid4()), "capability": "invoice.search", "stage": ActionEventStage.AUTH_CHECK}
        b.update(kw)
        with pytest.raises(ValidationError):
            ActionEvent(**b)  # type: ignore


def test_n12_audit_sink_failure_surfaced():
    class FailingLogger:
        def info(self, msg):
            raise OSError("Injected disk failure")

    adapter = SafeStructuredActionEvents(FailingLogger())
    ev = ActionEvent(
        correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
        capability="invoice.search", stage=ActionEventStage.AUTH_CHECK,
    )
    with pytest.raises(ActionEventDeliveryError):
        adapter.record_event(ev)
    assert len(adapter.recorded_events) == 0


def test_a13_mutated_source_revalidated_at_delivery():
    src = make_source()
    src.observed_at = "not-a-date"
    src.verification = "FORGED"  # type: ignore
    o = make_outcome(source=src)
    with pytest.raises(ValidationError):
        B.serialize_response(o)


def test_a14_partial_nested_denial_rejected():
    with pytest.raises(ValidationError, match="PARTIAL outcome cannot contain recognized nested denial"):
        make_outcome(
            status=S.PARTIAL, reason_code=R.COVERAGE_INCOMPLETE,
            source=make_source(coverage="INCOMPLETE"),
            data={"nested": {"status": "FORBIDDEN", "reason_code": "ACCESS_DENIED", "canary": "CANARY_14"}},
        )


def test_a15_ok_user_message_replaced_with_safe_template():
    o = make_outcome(status=S.OK, reason_code=R.RESULTS_FOUND, user_message="OperationalError sid=P1A_CANARY_A15")
    status_code, headers, body = B.serialize_response(o)
    assert status_code == 200 and body["user_message"] == "Tìm thấy danh sách hóa đơn phù hợp."


def test_a16_real_stream_handler_write_outage_surfaced():
    class BrokenStream:
        def write(self, message):
            raise OSError("SYNTHETIC_STREAM_OUTAGE")
        def flush(self):
            pass

    ev = ActionEvent(
        correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
        capability="invoice.context", stage=ActionEventStage.AUTH_CHECK,
    )

    # 1. Direct handler failure
    log = logging.Logger("test.a16.logger", logging.INFO)
    log.propagate = False
    log.addHandler(logging.StreamHandler(BrokenStream()))
    adapter = SafeStructuredActionEvents(log)
    with pytest.raises(ActionEventDeliveryError):
        adapter.record_event(ev)
    assert len(adapter.recorded_events) == 0

    # 2. Ancestor/root handler failure
    root = logging.getLogger()
    root_h = logging.StreamHandler(BrokenStream())
    root.addHandler(root_h)
    log_child = logging.getLogger("lotus_fin.actions.observability.test_child")
    log_child.setLevel(logging.INFO)
    log_child.propagate = True
    log_child.handlers = []
    adapter_child = SafeStructuredActionEvents(log_child)
    try:
        with pytest.raises(ActionEventDeliveryError):
            adapter_child.record_event(ev)
        assert len(adapter_child.recorded_events) == 0
    finally:
        root.removeHandler(root_h)

    # 3. Logger with no qualified sink
    log_no_sink = logging.Logger("test.no.sink", logging.INFO)
    log_no_sink.propagate = False
    adapter_no_sink = SafeStructuredActionEvents(log_no_sink)
    with pytest.raises(ActionEventDeliveryError):
        adapter_no_sink.record_event(ev)
    assert len(adapter_no_sink.recorded_events) == 0
