import json
import os
import time
from typing import Dict, List, Optional
import urllib.request
import urllib.error

from lotus_fin.core.ai.providers.base_provider import BaseLLMProvider, LLMResponse
from lotus_fin.core.ai.resilience.token_manager import token_manager


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI and OpenAI-compatible API endpoints (e.g. vLLM, DeepSeek)."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        super().__init__(model_name=model_name, api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or ''}"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_body = resp.read().decode("utf-8")
                res_json = json.loads(raw_body)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"OpenAI API Error {e.code}: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"OpenAI Network Error: {str(e)}")

        duration_ms = round((time.time() - start) * 1000, 2)
        usage = res_json.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        cost = token_manager.calculate_cost(self.model_name, prompt_tokens, completion_tokens)
        content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            model=self.model_name,
            cost_usd=cost["cost_usd"],
            cost_vnd=cost["cost_vnd"],
            raw_response=res_json
        )
