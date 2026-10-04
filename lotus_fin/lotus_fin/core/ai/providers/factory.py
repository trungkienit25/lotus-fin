import os
from typing import Optional
from lotus_fin.core.ai.providers.base_provider import BaseLLMProvider
from lotus_fin.core.ai.providers.mock_provider import MockLLMProvider
from lotus_fin.core.ai.providers.openai_provider import OpenAIProvider
from lotus_fin.core.ai.providers.gemini_provider import GeminiProvider


class ProviderFactory:
    """Factory creating LLM provider instances based on system configuration."""

    @staticmethod
    def get_provider(
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> BaseLLMProvider:
        p_name = (provider_name or os.environ.get("LOTUS_AI_PROVIDER", "mock")).lower().strip()

        if p_name in ["mock", "test", "offline"]:
            return MockLLMProvider(model_name=model_name or "mock")
        elif p_name in ["openai", "chatgpt"]:
            return OpenAIProvider(model_name=model_name or "gpt-4o-mini")
        elif p_name in ["gemini", "google"]:
            return GeminiProvider(model_name=model_name or "gemini-1.5-flash")
        else:
            # Fallback to mock provider for unknown names
            return MockLLMProvider(model_name=model_name or "mock")
