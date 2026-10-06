import logging
from typing import Dict, List, Optional
from lotus_fin.application.port.i_tool_registry import IToolRegistry
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand

_logger = logging.getLogger("lotus_fin.infrastructure.tool.registry")


class ToolRegistry(IToolRegistry):
    def __init__(self):
        self._tools: Dict[str, IToolCommand] = {}

    def register(self, tool: IToolCommand) -> None:
        name = tool.definition.name
        if name in self._tools:
            _logger.warning("Overwriting tool registration for '%s'", name)
        self._tools[name] = tool
        _logger.debug("Registered tool: %s", name)

    def get_tool(self, name: str) -> Optional[IToolCommand]:
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_available_tools(self, user: UserPrincipal) -> List[ToolDefinition]:
        return [
            tool.definition
            for tool in self._tools.values()
            if tool.is_authorized(user)
        ]
