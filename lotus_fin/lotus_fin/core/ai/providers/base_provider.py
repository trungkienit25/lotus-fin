from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Standardized response container for all LLM providers."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_ms: float
    model: str
    cost_usd: float = 0.0
    cost_vnd: float = 0.0
    raw_response: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "cost_usd": self.cost_usd,
            "cost_vnd": self.cost_vnd,
        }


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers (Mock, OpenAI, Gemini, Anthropic)."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Executes a single prompt generation request."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Executes a multi-turn chat completion request."""
        pass
