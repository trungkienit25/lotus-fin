"""
Google Gemini LLM Adapter (Gemini 1.5/2.0/2.5 Flash & Pro REST API).
Implements ILLMProvider with Function Declarations & Tool Calling.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from lotus_fin.application.port.i_llm_provider import ILLMProvider, LLMResponse
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition


class GeminiLLMAdapter(ILLMProvider):
    """
    Adapter communicating with Google Generative AI (Gemini) REST API.
    Zero external SDK dependency (pure urllib.request).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 45,
    ):
        self.model_name = (
            model_name
            or os.environ.get("GEMINI_MODEL")
            or os.environ.get("LOTUS_AI_MODEL")
            or os.environ.get("LOTUS_LLM_MODEL")
            or "gemini-flash-latest"
        )
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("LOTUS_AI_API_KEY")
            or os.environ.get("LOTUS_LLM_API_KEY")
            or ""
        )

        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None
    ) -> LLMResponse:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )

        contents = []
        system_instruction_text = None

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction_text = msg.content
                continue

            if msg.role == MessageRole.USER:
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content or ""}]
                })
            elif msg.role == MessageRole.ASSISTANT:
                parts = []
                if msg.content:
                    parts.append({"text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc.tool_name,
                                "args": tc.arguments,
                            }
                        })
                contents.append({
                    "role": "model",
                    "parts": parts or [{"text": ""}]
                })
            elif msg.role == MessageRole.TOOL:
                # Tool execution response
                contents.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.tool_call_id or "tool_response",
                            "response": {"output": msg.content or ""}
                        }
                    }]
                })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
            }
        }

        if system_instruction_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction_text}]
            }

        if tools and len(tools) > 0:
            function_declarations = []
            for t in tools:
                function_declarations.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters_schema,
                })
            payload["tools"] = [{"functionDeclarations": function_declarations}]

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw_body = resp.read().decode("utf-8")
                res_json = json.loads(raw_body)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"Gemini API Error {e.code}: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Gemini Network Error: {str(e)}")

        candidates = res_json.get("candidates", [])
        if not candidates:
            return LLMResponse(content="")

        content_parts = candidates[0].get("content", {}).get("parts", [])
        text_content_list = []
        parsed_tool_calls: Optional[List[ToolCallRequest]] = None

        for idx, part in enumerate(content_parts):
            if "text" in part:
                text_content_list.append(part["text"])
            elif "functionCall" in part:
                if parsed_tool_calls is None:
                    parsed_tool_calls = []
                fn_call = part["functionCall"]
                parsed_tool_calls.append(
                    ToolCallRequest(
                        id=f"gemini_call_{idx}",
                        tool_name=fn_call.get("name", ""),
                        arguments=fn_call.get("args", {})
                    )
                )

        return LLMResponse(
            content="\n".join(text_content_list),
            tool_calls=parsed_tool_calls,
        )

