"""Read Authorizer Port and Result Models.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §4.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus


class AuthCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    is_authorized: bool = Field(...)
    status: ActionStatus = Field(...)
    reason_code: ActionReasonCode = Field(...)
    denial_message: Optional[str] = Field(default=None)


class IReadAuthorizerPort(ABC):
    """Port for server-side authorization check across principal, company, capability, and documents."""

    @abstractmethod
    def resolve_context(
        self,
        candidate_company: str,
        capability: str,
        client_request_id: str,
        correlation_id: str,
    ) -> tuple[Optional[AuthorizedReadContext], AuthCheckResult]:
        """Resolve server-owned context and verify principal/company/capability authority."""
        pass

    @abstractmethod
    def authorize_document_read(
        self,
        context: AuthorizedReadContext,
        invoice_id: str,
    ) -> AuthCheckResult:
        """Verify whether the current principal is authorized to read the specific document."""
        pass
