"""
LLM Provider Factory.
Instantiates the configured ILLMProvider according to environment variables.
"""

import os
from typing import Optional

from lotus_fin.application.port.i_llm_provider import ILLMProvider
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.llm.adapter.openai_llm_adapter import OpenAILLMAdapter
from lotus_fin.infrastructure.llm.adapter.gemini_llm_adapter import GeminiLLMAdapter


class LLMProviderFactory:
    """Factory creating concrete ILLMProvider instances based on system configuration."""

    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> ILLMProvider:
        """
        Creates an ILLMProvider based on explicit parameters or environment variables.

        Environment Variables:
        - LOTUS_AI_PROVIDER: 'openai' | 'gemini' | 'mock' | 'deepseek' | 'vllm' | 'ollama'
        - LOTUS_AI_MODEL: model name (e.g. 'gpt-4o', 'gemini-1.5-flash', 'deepseek-chat')
        - LOTUS_AI_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY
        - LOTUS_AI_BASE_URL / OPENAI_BASE_URL
        """
        p_name = (
            provider_name
            or os.environ.get("LOTUS_AI_PROVIDER")
            or "mock"
        ).lower().strip()

        if p_name in ["openai", "chatgpt", "deepseek", "vllm", "ollama", "groq"]:
            return OpenAILLMAdapter(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
            )
        elif p_name in ["gemini", "google"]:
            return GeminiLLMAdapter(
                model_name=model_name,
                api_key=api_key,
            )
        else:
            return MockLLMAdapter()
