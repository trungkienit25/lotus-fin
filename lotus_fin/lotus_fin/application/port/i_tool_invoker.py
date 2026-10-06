from abc import ABC, abstractmethod
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult


class IToolInvoker(ABC):
    @abstractmethod
    def invoke(self, call: ToolCallRequest, user: UserPrincipal) -> ToolExecutionResult:
        """Executes a tool call request safely under user security context."""
        pass
