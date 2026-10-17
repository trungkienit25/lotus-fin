import os
from typing import Optional
from lotus_fin.application.port.i_llm_provider import ILLMProvider
from lotus_fin.infrastructure.llm.adapter.gemini_llm_adapter import GeminiLLMAdapter
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.llm.adapter.openai_llm_adapter import OpenAILLMAdapter

_ENV_LOADED = False


def _ensure_env_loaded():
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    # In sandbox or non-Frappe environments, attempt to load .env from project root
    for candidate in [".env", "../.env", "../../.env"]:
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip()
                            if k not in os.environ or not os.environ[k]:
                                os.environ[k] = v
            except Exception:
                pass


class LLMProviderFactory:
    """Factory creating concrete ILLMProvider instances based on system configuration."""

    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> ILLMProvider:
        _ensure_env_loaded()

        if provider_name is not None and not str(provider_name).strip():
            raise ValueError("Provider name cannot be empty. Supported providers: openai, gemini, mock.")

        p_name = (
            provider_name
            or os.environ.get("LOTUS_AI_PROVIDER")
            or os.environ.get("LOTUS_LLM_PROVIDER")
            or "mock"
        ).lower().strip()

        if p_name in ["openai", "chatgpt", "deepseek", "vllm", "ollama", "groq", "nvidia", "openrouter", "mistral", "together"]:
            # If provider is nvidia, default base_url to NVIDIA NIM build endpoint if not specified
            resolved_base_url = base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("LOTUS_AI_BASE_URL")
            if p_name == "nvidia" and not resolved_base_url:
                resolved_base_url = "https://integrate.api.nvidia.com/v1"
            
            resolved_api_key = (
                api_key
                or os.environ.get("LOTUS_LLM_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or (os.environ.get("NVIDIA_API_KEY") if p_name == "nvidia" else None)
                or os.environ.get("LOTUS_AI_API_KEY")
            )
            resolved_model = (
                model_name
                or (os.environ.get("NVIDIA_MODEL_NAME") if p_name == "nvidia" else None)
                or os.environ.get("OPENAI_MODEL")
                or os.environ.get("LOTUS_AI_MODEL")
                or os.environ.get("LOTUS_LLM_MODEL")
            )
            return OpenAILLMAdapter(
                model_name=resolved_model,
                api_key=resolved_api_key,
                base_url=resolved_base_url,
            )
        elif p_name in ["gemini", "google"]:
            gemini_key = (
                api_key
                or os.environ.get("LOTUS_LLM_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("LOTUS_AI_API_KEY")
            )
            return GeminiLLMAdapter(
                model_name=model_name,
                api_key=gemini_key,
            )
        elif p_name in ["mock", "test"]:
            return MockLLMAdapter()
        else:
            raise ValueError(f"Unsupported LLM provider '{p_name}'. Supported providers: openai, gemini, mock.")
