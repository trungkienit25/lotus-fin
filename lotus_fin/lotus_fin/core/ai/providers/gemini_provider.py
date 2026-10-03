import json
import os
import time
from typing import Dict, List, Optional
import urllib.request
import urllib.error

from lotus_fin.core.ai.providers.base_provider import BaseLLMProvider, LLMResponse
from lotus_fin.core.ai.resilience.token_manager import token_manager


class GeminiProvider(BaseLLMProvider):
    """Provider for Google Gemini 1.5/2.5 Flash/Pro REST API."""

    def __init__(self, model_name: str = "gemini-flash-lite-latest", api_key: Optional[str] = None):
        if model_name in ["gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]:
            model_name = "gemini-flash-lite-latest"
        super().__init__(model_name=model_name, api_key=api_key or os.environ.get("GEMINI_API_KEY"))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key or ''}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_body = resp.read().decode("utf-8")
                res_json = json.loads(raw_body)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"Gemini API Error {e.code}: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Gemini Network Error: {str(e)}")

        duration_ms = round((time.time() - start) * 1000, 2)
        usage = res_json.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        total_tokens = usage.get("totalTokenCount", prompt_tokens + completion_tokens)

        cost = token_manager.calculate_cost(self.model_name, prompt_tokens, completion_tokens)
        candidates = res_json.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                content = parts[0].get("text", "")

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

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        combined = " ".join(m.get("content", "") for m in messages)
        return self.generate(combined, temperature=temperature, max_tokens=max_tokens)
