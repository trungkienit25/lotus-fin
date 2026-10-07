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

        # Validate required arguments against parameters_schema if available
        param_schema = getattr(tool.definition, "parameters_schema", None)
        if param_schema and isinstance(param_schema, dict):
            required_fields = param_schema.get("required", [])
            missing_fields = [f for f in required_fields if f not in call.arguments or call.arguments[f] is None]
            if missing_fields:
                _logger.warning("Tool %s missing required arguments: %s", call.tool_name, missing_fields)
                return ToolExecutionResult(
                    tool_call_id=call.id,
                    tool_name=call.tool_name,
                    is_success=False,
                    error_message=f"Missing required parameter(s): {', '.join(missing_fields)}"
                )

        try:
            result = tool.execute(call.arguments, user)
            # Ensure correlation id matches
            result.tool_call_id = call.id
            result.tool_name = call.tool_name
            return result
        except Exception as e:
            _logger.exception("Error executing tool %s: %s", call.tool_name, str(e))
            # Sanitize error message to prevent leaking internal traces to user
            clean_err = str(e).split("\n")[0] if str(e) else "Execution error"
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.tool_name,
                is_success=False,
                error_message=f"Execution error in {call.tool_name}: {clean_err}"
            )

