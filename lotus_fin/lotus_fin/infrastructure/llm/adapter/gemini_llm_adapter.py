import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from lotus_fin.application.port.i_llm_provider import ILLMProvider, LLMResponse
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition

_logger = logging.getLogger("lotus_fin.infrastructure.llm.gemini")


class GeminiLLMAdapter(ILLMProvider):
    """
    Adapter communicating with Google Generative AI (Gemini) REST API.
    Zero external SDK dependency (pure urllib.request).
    Includes automatic multi-key rotation and error fallback (429 Quota Exceeded, 403 Forbidden, 5xx Server Error).
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
            or "gemini-1.5-flash"
        )
        raw_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
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
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None
    ) -> LLMResponse:
        if not self.api_keys:
            raise ValueError("GEMINI_API_KEY (or LOTUS_AI_API_KEY / LOTUS_LLM_API_KEY) is not configured.")

        contents: List[Dict[str, Any]] = []
        system_instruction_text = None

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction_text = msg.content
            elif msg.role == MessageRole.USER:
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
                        call_obj = {
                            "name": tc.tool_name,
                            "args": tc.arguments,
                        }
                        p_dict: Dict[str, Any] = {"functionCall": call_obj}
                        ts = getattr(tc, "thought_signature", None)
                        if ts:
                            p_dict["thought_signature"] = ts
                        parts.append(p_dict)
                contents.append({
                    "role": "model",
                    "parts": parts or [{"text": ""}]
                })
            elif msg.role == MessageRole.TOOL:
                # In Gemini generateContent API, functionResponse parts are sent under role 'user'
                contents.append({
                    "role": "user",
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

        # Multi-key fallback execution loop
        last_exception = None
        for key_idx, current_key in enumerate(self.api_keys):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={current_key}"
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
                        ts = part.get("thought_signature") or part.get("thoughtSignature")
                        parsed_tool_calls.append(
                            ToolCallRequest(
                                id=f"gemini_call_{idx}",
                                tool_name=fn_call.get("name", ""),
                                arguments=fn_call.get("args", {}),
                                thought_signature=ts
                            )
                        )

                return LLMResponse(
                    content="\n".join(text_content_list),
                    tool_calls=parsed_tool_calls,
                )

            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8") if e.fp else str(e)
                last_exception = RuntimeError(f"Gemini API Error {e.code} on key #{key_idx + 1}: {err_msg}")
                _logger.warning("Gemini API key #%d failed with code %d. Attempting fallback to next key...", key_idx + 1, e.code)
                continue
            except Exception as e:
                last_exception = RuntimeError(f"Gemini Network Error on key #{key_idx + 1}: {str(e)}")
                _logger.warning("Gemini network error on key #%d: %s. Attempting fallback...", key_idx + 1, str(e))
                continue

        if last_exception:
            raise last_exception
        raise RuntimeError("All configured Gemini API keys failed.")
