import logging
from lotus_fin.application.port.i_tool_invoker import IToolInvoker
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.registry.tool_registry import ToolRegistry

_logger = logging.getLogger("lotus_fin.infrastructure.tool.invoker")


class ToolInvoker(IToolInvoker):
    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    def invoke(self, call: ToolCallRequest, user: UserPrincipal) -> ToolExecutionResult:
        tool = self._registry.get_tool(call.tool_name)
        if not tool:
            _logger.error("Tool not found: %s", call.tool_name)
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.tool_name,
                is_success=False,
                error_message=f"Tool '{call.tool_name}' is not registered."
            )

        if not tool.is_authorized(user):
            _logger.warning("Unauthorized tool invocation: %s by user %s", call.tool_name, user.user_id)
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.tool_name,
                is_success=False,
                error_message=f"User is not authorized to invoke tool '{call.tool_name}'."
            )

        try:
            result = tool.execute(call.arguments, user)
            # Ensure correlation id matches
            result.tool_call_id = call.id
            result.tool_name = call.tool_name
            return result
        except Exception as e:
            _logger.exception("Error executing tool %s: %s", call.tool_name, str(e))
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.tool_name,
                is_success=False,
                error_message=f"Internal execution error: {str(e)}"
            )
