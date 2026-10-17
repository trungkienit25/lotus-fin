import logging
from typing import Any, Dict, Optional
from lotus_fin.application.port.i_tool_invoker import IToolInvoker
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.registry.tool_registry import ToolRegistry

_logger = logging.getLogger("lotus_fin.infrastructure.tool.invoker")


def _validate_schema(schema: Dict[str, Any], data: Any) -> Optional[str]:
    """Lightweight recursive schema validator enforcing types, required fields, and array constraints."""
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(data, dict):
            return "Expected object"
        for req in schema.get("required", []):
            if req not in data or data[req] is None:
                return f"Missing required parameter(s): {req}"
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop in data and data[prop] is not None:
                err = _validate_schema(prop_schema, data[prop])
                if err:
                    return err
    elif expected_type == "array":
        if not isinstance(data, list):
            return "Expected array"
        if "minItems" in schema and len(data) < schema["minItems"]:
            return f"Array violates minItems: {schema['minItems']}"
        items_schema = schema.get("items")
        if items_schema:
            for item in data:
                err = _validate_schema(items_schema, item)
                if err:
                    return err
    elif expected_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            return f"Expected integer, got {type(data).__name__}"
    elif expected_type == "string":
        if not isinstance(data, str):
            return f"Expected string, got {type(data).__name__}"
    elif expected_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            return f"Expected number, got {type(data).__name__}"
    elif expected_type == "boolean":
        if not isinstance(data, bool):
            return f"Expected boolean, got {type(data).__name__}"
    return None


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

        # Validate parameters against parameters_schema
        param_schema = getattr(tool.definition, "parameters_schema", None)
        if param_schema and isinstance(param_schema, dict):
            validation_error = _validate_schema(param_schema, call.arguments)
            if validation_error:
                _logger.warning("Tool %s schema violation: %s", call.tool_name, validation_error)
                return ToolExecutionResult(
                    tool_call_id=call.id,
                    tool_name=call.tool_name,
                    is_success=False,
                    error_message=validation_error
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
                error_message="Internal processing error occurred."
            )
