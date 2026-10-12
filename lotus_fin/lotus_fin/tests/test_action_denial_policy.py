"""F04: closed denial precedence at construction and final delivery."""

import uuid
import pytest
from pydantic import ValidationError
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome, SourceEvidence, ActionStatus as S, ActionReasonCode as R,
)
from lotus_fin.presentation.dto.action_outcome import ActionOutcomeDTO
from lotus_fin.presentation.response.action_response import ActionResponseBuilder as B


def outcome(status=S.OK, data=None):
    return ActionOutcome(
        status=status, reason_code=R.RESULTS_FOUND if status == S.OK else R.COVERAGE_INCOMPLETE,
        correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
        capability="invoice.search", context_version="ctx", data=data,
        source=SourceEvidence(mode="ERP_READ", product_ref="prod", site_ref="site",
            connection_ref="conn", connection_version="v1", observed_at="2026-10-12T00:00:00Z",
            timezone="Asia/Ho_Chi_Minh", coverage="PAGE_COMPLETE" if status == S.OK else "INCOMPLETE"),
        user_message="synthetic benign control",
    )


@pytest.mark.parametrize("reason", ["AUTH_REQUIRED", "CSRF_OR_ORIGIN_DENIED",
                                    "COMPANY_DENIED", "CAPABILITY_DENIED", "ACCESS_DENIED"])
@pytest.mark.parametrize("status", [S.OK, S.PARTIAL])
@pytest.mark.parametrize("shape", ["dict", "list"])
def test_all_closed_denials_rejected_at_both_boundaries(reason, status, shape):
    child = {"reason_code": reason, "is_success": True, "private": "DENIAL_CANARY"}
    data = {"result": child} if shape == "dict" else {"items": [child]}
    valid = outcome(status, {"items": []})
    assert B.serialize_response(valid)[0] == 200
    with pytest.raises(ValidationError, match="nested denial"):
        outcome(status, data)
    valid.data = data
    with pytest.raises(ValidationError, match="nested denial"):
        ActionOutcomeDTO.from_domain(valid)
    with pytest.raises(ValidationError, match="nested denial"):
        B.serialize_response(valid)


@pytest.mark.parametrize("status", [S.OK, S.PARTIAL])
def test_benign_approved_shapes_remain_success(status):
    value = outcome(status, {"items": [{"label": "safe", "docstatus": 1}], "has_more": False})
    http, _, body = B.serialize_response(value)
    assert http == 200 and body["status"] == status and body["data"]["items"][0]["label"] == "safe"


@pytest.mark.parametrize("data", [
    {"result": {"status": "UNKNOWN"}}, {"result": {"reason_code": "UNKNOWN"}},
    {"result": {"status": ["FORBIDDEN"]}}, {"items": ("unsupported",)},
    {"result": {"status": "OK", "reason_code": "SOURCE_FAILURE"}},
    {"result": {"value": float("nan")}},
])
def test_unsupported_nested_shapes_fail_closed(data):
    with pytest.raises(ValidationError, match="Unsupported nested outcome"):
        outcome(data=data)
    valid = outcome(data={"items": []})
    valid.data = data
    with pytest.raises(ValidationError, match="Unsupported nested outcome"):
        B.serialize_response(valid)


@pytest.mark.parametrize("wide", [False, True])
def test_nested_scan_is_bounded(wide):
    data = [None] * 4097 if wide else {}
    if not wide:
        for _ in range(17):
            data = {"nested": data}
    with pytest.raises(ValidationError, match="Unsupported nested outcome"):
        outcome(data=data)
