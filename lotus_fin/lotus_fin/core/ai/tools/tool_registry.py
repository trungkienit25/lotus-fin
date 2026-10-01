from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    """Tool metadata and execution spec conforming to OpenAI/Gemini function calling schema."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., Any]
    read_only: bool = True

    def to_schema(self) -> Dict[str, Any]:
        """Converts tool definition to standard JSON function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """
    Registry of verified, read-only tools available for AI agent execution.
    Enforces Zero DB Mutation: All registered tools must be read-only.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        read_only: bool = True
    ) -> None:
        if not read_only:
            raise ValueError(f"Agent tool '{name}' must be read-only. Write actions are prohibited.")
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            read_only=read_only
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        tool = self.get_tool(name)
        if not tool:
            raise KeyError(f"Tool '{name}' is not registered.")
        return tool.handler(**arguments)


# Global tool registry instance
tool_registry = ToolRegistry()
