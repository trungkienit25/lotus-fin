"""Shared typed-result trust checks; no ERP/framework/provider imports."""
from lotus_fin.domain.schema.action_outcome import (
    ActionStatus as S, ActionReasonCode as R, ActionOutcome, SourceEvidence, STATUS_REASON_MATRIX,
)
from lotus_fin.domain.model.invoice_read_budget import ReadBudgetExceeded


def failure(status=S.SOURCE_ERROR, reason=R.INVALID_PROVIDER_RESPONSE):
    return None, None, status, reason


def terminal(status, reason):
    if status == S.FORBIDDEN or reason in STATUS_REASON_MATRIX[S.FORBIDDEN]:
        return failure(S.FORBIDDEN, reason if reason in STATUS_REASON_MATRIX[S.FORBIDDEN] else R.ACCESS_DENIED)
    if type(status) is not S or type(reason) is not R or reason not in STATUS_REASON_MATRIX.get(status, []):
        return failure()
    if status not in (S.OK, S.PARTIAL):
        return failure(status, reason)
    return None


def validate_source(source, context):
    if type(source) is not SourceEvidence:
        raise ValueError("Missing typed source")
    source = SourceEvidence(**source.model_dump())
    expected = {"mode": context.adapter_mode, "product_ref": context.product_id,
        "site_ref": context.site_id, "connection_ref": context.connection_id,
        "connection_version": context.connection_version,
        "projection_version": context.projection_version, "timezone": context.timezone}
    if any(getattr(source, name) != value for name, value in expected.items()):
        raise ValueError("Source scope mismatch")
    return source


def exception_result(exc):
    if isinstance(exc, TimeoutError) or (isinstance(exc, ReadBudgetExceeded) and exc.axis == "deadline"):
        return failure(S.TIMEOUT, R.DEADLINE_EXCEEDED)
    if isinstance(exc, (ValueError, TypeError, ReadBudgetExceeded)):
        return failure()
    return failure(S.SOURCE_ERROR, R.SOURCE_FAILURE)


def response_bytes(context, data, source, status, reason):
    """Count full JSON envelope, conservatively reserving maximal UTF-8 message bytes."""
    value = ActionOutcome(status=status, reason_code=reason, capability=context.capability,
        correlation_id=context.correlation_id, request_id=context.request_id,
        context_version=context.context_version, source=source, data=data,
        user_message="\U0001f642" * 256)
    return len(value.model_dump_json().encode("utf-8"))
