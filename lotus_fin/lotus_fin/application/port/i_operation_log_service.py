# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from lotus_fin.domain.model.operation_log import SandboxOperationLogEntry
from lotus_fin.domain.model.user_context import UserPrincipal


class IOperationLogService(ABC):
    """
    Application Port for logging and retrieving AI Sandbox operations.
    """
    @abstractmethod
    def log_operation(
        self,
        session_id: str,
        user: UserPrincipal,
        prompt: str,
        reply: str,
        tool_called: Optional[str] = None,
        tool_inputs: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        latency_ms: int = 0,
        status: str = "SUCCESS",
        llm_provider: str = "unknown",
        model_name: Optional[str] = None,
    ) -> SandboxOperationLogEntry:
        """Create and persist an audit trace for an AI action."""
        pass

    @abstractmethod
    def get_recent_logs(
        self,
        company: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs formatted for presentation."""
        pass

    @abstractmethod
    def clear_logs(self, company: Optional[str] = None) -> None:
        """Clear audit logs for clean testing/demo setup."""
        pass

