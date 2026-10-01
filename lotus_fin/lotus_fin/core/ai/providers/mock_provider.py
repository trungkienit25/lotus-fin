from typing import Dict, List, Optional
from lotus_fin.core.ai.providers.base_provider import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for offline development and zero-cost unit testing.
    Never makes network calls.
    """

    def __init__(self, model_name: str = "mock", custom_response: Optional[str] = None):
        super().__init__(model_name=model_name, api_key="mock-key")
        self.custom_response = custom_response

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        content = self.custom_response or '{"status": "AVAILABLE", "facts": ["Mock metric verified"], "interpretations": [], "next_checks": []}'
        return LLMResponse(
            content=content,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(len(prompt) + len(content)) // 4,
            duration_ms=1.5,
            model=self.model_name,
            cost_usd=0.0,
            cost_vnd=0.0
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        combined = " ".join(m.get("content", "") for m in messages)
        return self.generate(combined, temperature=temperature, max_tokens=max_tokens)
