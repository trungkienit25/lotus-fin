"""
OpenAI & OpenAI-compatible LLM Adapter (supports OpenAI, vLLM, DeepSeek, Ollama, Groq, Together).
Implements ILLMProvider with native Function / Tool Calling.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from lotus_fin.application.port.i_llm_provider import ILLMProvider, LLMResponse
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition


class OpenAILLMAdapter(ILLMProvider):
    """
    Adapter communicating with OpenAI or any OpenAI-compatible API endpoint
    using standard HTTP/REST requests (zero third-party package requirement).
    Includes automatic multi-key rotation and error fallback (429 Quota/Rate Limit, 401/403, 5xx Server Error).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 45,
    ):
        self.model_name = (
            model_name
            or os.environ.get("OPENAI_MODEL")
            or os.environ.get("LOTUS_AI_MODEL")
            or os.environ.get("LOTUS_LLM_MODEL")
            or "gpt-4o-mini"
        )
        raw_key = (
            api_key
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("LOTUS_AI_API_KEY")
            or os.environ.get("LOTUS_LLM_API_KEY")
            or ""
        )
        # Parse comma-separated list of keys, stripping quotes and whitespaces
        self.api_keys: List[str] = [
            k.strip().strip('"').strip("'")
            for k in raw_key.replace("\n", ",").split(",")
            if k.strip().strip('"').strip("'")
        ]
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("LOTUS_AI_BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None
    ) -> LLMResponse:
        if not self.api_keys:
            raise ValueError("OPENAI_API_KEY (or LOTUS_AI_API_KEY / LOTUS_LLM_API_KEY) is not configured.")

        url = f"{self.base_url}/chat/completions"

        # Format messages for OpenAI
        formatted_messages = [msg.to_llm_dict() for msg in messages]

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": 0.1,
        }

        # Include tools if provided
        if tools and len(tools) > 0:
            payload["tools"] = [t.to_openai_dict() for t in tools]
            payload["tool_choice"] = "auto"

        data = json.dumps(payload).encode("utf-8")

        # Multi-key fallback execution loop
        last_exception = None
        for key_idx, current_key in enumerate(self.api_keys):
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {current_key}",
            }
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    raw_body = resp.read().decode("utf-8")
                    res_json = json.loads(raw_body)

                choices = res_json.get("choices", [])
                if not choices:
                    return LLMResponse(content="")

                choice_message = choices[0].get("message", {})
                content = choice_message.get("content") or ""

                # Parse tool calls if returned
                parsed_tool_calls: Optional[List[ToolCallRequest]] = None
                raw_tool_calls = choice_message.get("tool_calls")
                if raw_tool_calls and isinstance(raw_tool_calls, list):
                    parsed_tool_calls = []
                    for tc in raw_tool_calls:
                        tc_id = tc.get("id", "call_default")
                        fn_info = tc.get("function", {})
                        fn_name = fn_info.get("name", "")
                        raw_args = fn_info.get("arguments", "{}")

                        if isinstance(raw_args, str):
                            try:
                                args_dict = json.loads(raw_args)
                            except Exception:
                                args_dict = {"raw_input": raw_args}
                        elif isinstance(raw_args, dict):
                            args_dict = raw_args
                        else:
                            args_dict = {}

                        parsed_tool_calls.append(
                            ToolCallRequest(
                                id=tc_id,
                                tool_name=fn_name,
                                arguments=args_dict,
                            )
                        )

                return LLMResponse(
                    content=content,
                    tool_calls=parsed_tool_calls,
                )

            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8") if e.fp else str(e)
                last_exception = RuntimeError(f"OpenAI API Error {e.code} on key #{key_idx + 1}: {err_msg}")
                continue
            except Exception as e:
                last_exception = RuntimeError(f"OpenAI Network Error on key #{key_idx + 1}: {str(e)}")
                continue

        if last_exception:
            raise last_exception
        raise RuntimeError("All configured OpenAI API keys failed.")
