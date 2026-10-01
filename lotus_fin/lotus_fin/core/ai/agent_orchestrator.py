"""
Lotus Fin - AI Agent Orchestrator.

Orchestrates multi-turn or single-turn interactions between LLMs and domain plugins.
Connects the Plugin Registry, Resilience layer, and Grounding Guard.
"""

from decimal import Decimal
import json
import logging
from typing import Any, Dict, List, Optional


from lotus_fin.core.ai.providers.factory import ProviderFactory
from lotus_fin.core.ai.resilience.circuit_breaker import CircuitBreaker
from lotus_fin.core.ai.resilience.token_manager import TokenManager
from lotus_fin.core.domain.calculators.grounding_guard import GroundingGuard
from lotus_fin.core.plugin.registry import plugin_registry

_logger = logging.getLogger("lotus_fin.core.ai.agent_orchestrator")


class AgentOrchestrator:
    """
    Agent Orchestrator interacting with domain modules purely via Plugin Interface.
    Enforces Grounding Guard and Zero DB Mutation.
    """

    def __init__(
        self,
        provider_name: str = "mock",
        model: Optional[str] = None,
        token_manager: Optional[TokenManager] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.provider = ProviderFactory.get_provider(provider_name, model_name=model)
        self.token_manager = token_manager or TokenManager()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.guard = GroundingGuard()


    def run_grounded_task(
        self,
        company: str,
        user_prompt: str,
        active_plugins: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes an AI task:
        1. Gathers deterministic grounding facts from plugins.
        2. Exports read-only tools from plugins.
        3. Invokes resilient LLM provider.
        4. Validates grounding against hallucinations.
        """
        # 1. Gather Grounding Context
        grounding_data = plugin_registry.gather_grounding_context(
            company=company,
            plugin_ids=active_plugins,
            **kwargs
        )

        # 2. Check Circuit Breaker
        if not self.circuit_breaker.can_execute():
            return {
                "status": "UNAVAILABLE",
                "reason": "AI Circuit breaker is OPEN. Fallback activated.",
                "data": grounding_data
            }

        # 3. Check Token Budget
        allowed = self.token_manager.check_rate_limit("default", estimated_tokens=500.0)
        if not allowed:
            return {
                "status": "UNAVAILABLE",
                "reason": "Rate limit / token budget exhausted.",
                "data": grounding_data
            }


        # 4. Build System Context
        system_instruction = (
            "You are Lotus Fin SME Financial AI Copilot. "
            "You must ONLY make statements grounded in the verified numbers provided. "
            "Never guarantee future profits or fabricate financial metrics."
        )

        try:
            response = self.provider.generate(
                prompt=f"Context: {json.dumps(grounding_data, default=str)}\n\nQuery: {user_prompt}",
                system_prompt=system_instruction
            )
            self.circuit_breaker.record_success()

            # 5. Extract ground facts for hallucination check
            ground_numbers = set(self._extract_numbers_from_dict(grounding_data))
            is_valid, errors = self.guard.verify(
                prose_blocks=[response.content],
                allowed_numbers=ground_numbers
            )


            return {
                "status": "AVAILABLE" if is_valid else "UNAVAILABLE",
                "content": response.content if is_valid else f"Ungrounded claims rejected: {errors}",
                "model": response.model,
                "total_tokens": response.total_tokens,
                "latency_ms": response.duration_ms,
                "grounding_valid": is_valid
            }


        except Exception as e:
            self.circuit_breaker.record_failure()
            _logger.error(f"Agent Orchestrator execution failed: {e}")
            return {
                "status": "UNAVAILABLE",
                "reason": str(e),
                "data": grounding_data
            }

    def _extract_numbers_from_dict(self, data: Any) -> List[Decimal]:
        nums = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    try:
                        nums.append(Decimal(str(v)))
                    except Exception:
                        pass
                elif isinstance(v, (dict, list)):
                    nums.extend(self._extract_numbers_from_dict(v))
        elif isinstance(data, list):
            for item in data:
                nums.extend(self._extract_numbers_from_dict(item))
        return nums

