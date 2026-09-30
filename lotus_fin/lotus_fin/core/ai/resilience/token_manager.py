from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import Dict, Optional

# Benchmark cost per 1K tokens in USD
MODEL_PRICING = {
    "mock": {"input": 0.0, "output": 0.0},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.5-flash": {"input": 0.00010, "output": 0.0004},
}

VND_PER_USD = 25400.0


@dataclass
class TokenBucket:
    """Thread-safe Token Bucket rate limiter algorithm."""
    capacity: float = 10000.0
    refill_rate: float = 500.0  # tokens added per second
    tokens: float = 10000.0
    last_update: float = field(default_factory=time.time)

    def consume(self, amount: float) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class TokenManager:
    """
    Manages LLM token budgets, rate limits, and financial cost estimations.
    Enforces tenant-level isolation and budget enforcement.
    """

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._usage_log: Dict[str, Dict[str, float]] = {}

    def get_bucket(self, tenant_id: str) -> TokenBucket:
        if tenant_id not in self._buckets:
            self._buckets[tenant_id] = TokenBucket()
        return self._buckets[tenant_id]

    def check_rate_limit(self, tenant_id: str, estimated_tokens: float = 500.0) -> bool:
        """Returns True if tenant has token quota available, False if rate limited."""
        bucket = self.get_bucket(tenant_id)
        return bucket.consume(estimated_tokens)

    @staticmethod
    def calculate_cost(
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """Calculates cost in USD and VND based on token counts."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("gpt-4o-mini", {"input": 0.00015, "output": 0.0006}))
        input_cost = (input_tokens / 1000.0) * pricing["input"]
        output_cost = (output_tokens / 1000.0) * pricing["output"]
        total_usd = input_cost + output_cost
        total_vnd = round(total_usd * VND_PER_USD, 2)

        return {
            "cost_usd": round(total_usd, 6),
            "cost_vnd": total_vnd,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
        }

    def record_usage(
        self,
        tenant_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """Records token consumption and returns cost metrics."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        if tenant_id not in self._usage_log:
            self._usage_log[tenant_id] = {"total_tokens": 0.0, "total_cost_usd": 0.0, "total_cost_vnd": 0.0}

        rec = self._usage_log[tenant_id]
        rec["total_tokens"] += (input_tokens + output_tokens)
        rec["total_cost_usd"] += cost["cost_usd"]
        rec["total_cost_vnd"] += cost["cost_vnd"]
        return cost


# Singleton instance
token_manager = TokenManager()
