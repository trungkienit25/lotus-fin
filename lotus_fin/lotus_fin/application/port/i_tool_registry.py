from abc import ABC, abstractmethod
from typing import List, Optional
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition


class IToolRegistry(ABC):
    @abstractmethod
    def get_available_tools(self, user: UserPrincipal) -> List[ToolDefinition]:
        """Returns tools the user is authorized to discover and invoke."""
        pass

    @abstractmethod
    def has_tool(self, name: str) -> bool:
        """Checks if tool name exists in registry."""
        pass

