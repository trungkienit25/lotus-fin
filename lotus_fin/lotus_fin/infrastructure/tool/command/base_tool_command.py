from abc import ABC, abstractmethod
from typing import Any, Dict
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult


class IToolCommand(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Returns the JSON schema and description for this tool."""
        pass

    @abstractmethod
    def is_authorized(self, user: UserPrincipal) -> bool:
        """Validates if the user principal has permission to invoke this tool."""
        pass

    @abstractmethod
    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        """Executes deterministic domain business logic."""
        pass

