"""Safe Response Builder and Serialization for Action Outcomes.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import uuid
from typing import Any, Dict, Optional, Tuple
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome,
    ActionReasonCode,
    ActionStatus,
    SourceEvidence,
    STATUS_REASON_MATRIX,
)
from lotus_fin.presentation.dto.action_outcome import (
    ActionOutcomeDTO,
    is_valid_uuid_v4,
)

STATUS_HTTP_MAP: Dict[ActionStatus, int] = {
    ActionStatus.OK: 200,
    ActionStatus.PARTIAL: 200,
    ActionStatus.FORBIDDEN: 403,
    ActionStatus.SOURCE_ERROR: 502,
    ActionStatus.TIMEOUT: 504,
    ActionStatus.NOT_AVAILABLE: 422,
}

REASON_HTTP_OVERRIDE: Dict[ActionReasonCode, int] = {
    ActionReasonCode.AUTH_REQUIRED: 401,
    ActionReasonCode.CSRF_OR_ORIGIN_DENIED: 403,
    ActionReasonCode.COMPANY_DENIED: 403,
    ActionReasonCode.CAPABILITY_DENIED: 403,
    ActionReasonCode.ACCESS_DENIED: 403,
    ActionReasonCode.CONTEXT_REQUIRED: 422,
    ActionReasonCode.INVALID_REQUEST: 422,
    ActionReasonCode.CONTEXT_CHANGED: 409,
    ActionReasonCode.STALE_SELECTION: 409,
    ActionReasonCode.STALE_CURSOR: 409,
    ActionReasonCode.DOCUMENT_UNAVAILABLE: 404,
    ActionReasonCode.PROJECTION_UNAVAILABLE: 422,
    ActionReasonCode.TARGET_UNQUALIFIED: 503,
    ActionReasonCode.CAPABILITY_DISABLED: 503,
    ActionReasonCode.UNSUPPORTED_INTENT: 422,
    ActionReasonCode.INVALID_OUTCOME: 422,
    ActionReasonCode.SOURCE_FAILURE: 502,
    ActionReasonCode.INVALID_PROVIDER_RESPONSE: 502,
    ActionReasonCode.DEADLINE_EXCEEDED: 504,
}

SAFE_MESSAGE_TEMPLATES: Dict[ActionReasonCode, str] = {
    ActionReasonCode.RESULTS_FOUND: "Tìm thấy danh sách hóa đơn phù hợp.",
    ActionReasonCode.EMPTY_RESULT: "Không tìm thấy hóa đơn nào trong phạm vi tìm kiếm.",
    ActionReasonCode.DOCUMENT_READY: "Hóa đơn đã sẵn sàng để xem.",
    ActionReasonCode.CONTEXT_READY: "Ngữ cảnh truy vấn hợp lệ.",
    ActionReasonCode.COVERAGE_INCOMPLETE: "Dữ liệu trả về chưa đầy đủ do giới hạn nguồn.",
    ActionReasonCode.AUTH_REQUIRED: "Yêu cầu đăng nhập để thực hiện tác vụ.",
    ActionReasonCode.CSRF_OR_ORIGIN_DENIED: "Yêu cầu bị từ chối do nguồn gốc không hợp lệ.",
    ActionReasonCode.COMPANY_DENIED: "Không có quyền truy cập vào công ty được chỉ định.",
    ActionReasonCode.CAPABILITY_DENIED: "Không có quyền thực hiện chức năng này.",
    ActionReasonCode.ACCESS_DENIED: "Quyền truy cập bị từ chối.",
    ActionReasonCode.SOURCE_FAILURE: "Lỗi kết nối tới hệ thống nguồn dữ liệu.",
    ActionReasonCode.INVALID_PROVIDER_RESPONSE: "Hệ thống nguồn phản hồi không hợp lệ.",
    ActionReasonCode.DEADLINE_EXCEEDED: "Quá thời gian xử lý yêu cầu.",
    ActionReasonCode.INVALID_REQUEST: "Yêu cầu không hợp lệ hoặc sai định dạng.",
    ActionReasonCode.CONTEXT_REQUIRED: "Cần chọn và xác thực ngữ cảnh công ty trước.",
    ActionReasonCode.CONTEXT_CHANGED: "Ngữ cảnh đã thay đổi, vui lòng thử lại.",
    ActionReasonCode.STALE_SELECTION: "Lựa chọn đã cũ hoặc tài liệu đã được cập nhật.",
    ActionReasonCode.STALE_CURSOR: "Con trỏ phân trang không còn hợp lệ.",
    ActionReasonCode.DOCUMENT_UNAVAILABLE: "Hóa đơn không tồn tại hoặc không thể truy cập.",
    ActionReasonCode.PROJECTION_UNAVAILABLE: "Trường dữ liệu yêu cầu không khả dụng.",
    ActionReasonCode.TARGET_UNQUALIFIED: "Mục tiêu kết nối chưa đủ điều kiện hoạt động.",
    ActionReasonCode.CAPABILITY_DISABLED: "Chức năng hiện đang tạm khóa.",
    ActionReasonCode.UNSUPPORTED_INTENT: "Yêu cầu chưa được hỗ trợ, vui lòng làm rõ tiêu chí.",
    ActionReasonCode.INVALID_OUTCOME: "Kết quả xử lý không hợp lệ.",
}


class ActionResponseBuilder:
    @staticmethod
    def resolve_http_status(status: ActionStatus, reason_code: ActionReasonCode) -> int:
        return REASON_HTTP_OVERRIDE.get(reason_code, STATUS_HTTP_MAP.get(status, 500))

    @staticmethod
    def get_safe_message(reason_code: ActionReasonCode) -> str:
        return SAFE_MESSAGE_TEMPLATES.get(
            reason_code, "Yêu cầu không thể hoàn thành. Vui lòng thử lại."
        )

    @staticmethod
    def sanitize_request_id(client_request_id: Optional[str]) -> Tuple[str, bool]:
        if client_request_id and is_valid_uuid_v4(client_request_id):
            return client_request_id, False
        return str(uuid.uuid4()), True

    @classmethod
    def build_failure_outcome(
        cls,
        status: ActionStatus,
        reason_code: ActionReasonCode,
        capability: str,
        client_request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        context_version: Optional[str] = None,
    ) -> ActionOutcome:
        cid = correlation_id if (correlation_id and is_valid_uuid_v4(correlation_id)) else str(uuid.uuid4())
        req_id, was_replaced = cls.sanitize_request_id(client_request_id)
        if client_request_id is not None and was_replaced and status == ActionStatus.NOT_AVAILABLE:
            reason_code = ActionReasonCode.INVALID_REQUEST

        return ActionOutcome(
            contract_version="p1.invoice.v1",
            status=status,
            reason_code=reason_code,
            correlation_id=cid,
            request_id=req_id,
            capability=capability,  # type: ignore
            source=None,
            context_version=context_version,
            data=None,
            user_message=cls.get_safe_message(reason_code),
        )

    @classmethod
    def serialize_response(
        cls, outcome: ActionOutcome
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        # Enforce approved safe message template for EVERY outcome
        outcome.user_message = cls.get_safe_message(outcome.reason_code)

        # Fail-closed sanitize: if failure status, enforce null data & null source
        if outcome.status in {
            ActionStatus.FORBIDDEN, ActionStatus.SOURCE_ERROR,
            ActionStatus.TIMEOUT, ActionStatus.NOT_AVAILABLE,
        }:
            outcome.data = None
            outcome.source = None
        else:
            # OK/PARTIAL: re-verify full SourceEvidence invariants
            if outcome.source is None:
                raise ValueError(f"{outcome.status} status requires valid source evidence.")
            SourceEvidence(**outcome.source.model_dump())

        # Validate through DTO
        dto = ActionOutcomeDTO.from_domain(outcome)
        body = dto.model_dump(mode="json")
        http_status = cls.resolve_http_status(dto.status, dto.reason_code)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "X-Correlation-ID": dto.correlation_id,
            "X-Content-Type-Options": "nosniff",
        }
        return http_status, headers, body
