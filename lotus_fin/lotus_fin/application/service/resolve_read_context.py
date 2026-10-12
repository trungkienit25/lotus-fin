"""Resolve Read Context Application Service.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §4.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Optional, Tuple
from lotus_fin.application.port.i_read_authorizer import AuthCheckResult, IReadAuthorizerPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext


class ResolveReadContextService:
    """Application use case for resolving and verifying authorized read context."""

    def __init__(self, authorizer: IReadAuthorizerPort) -> None:
        self._authorizer = authorizer

    def execute(
        self,
        candidate_company: str,
        capability: str,
        client_request_id: str,
        correlation_id: str,
    ) -> Tuple[Optional[AuthorizedReadContext], AuthCheckResult]:
        if not candidate_company or not isinstance(candidate_company, str):
            from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.NOT_AVAILABLE,
                reason_code=ActionReasonCode.CONTEXT_REQUIRED,
                denial_message="Yêu cầu cung cấp tên công ty hợp lệ.",
            )

        return self._authorizer.resolve_context(
            candidate_company=candidate_company.strip(),
            capability=capability,
            client_request_id=client_request_id,
            correlation_id=correlation_id,
        )
