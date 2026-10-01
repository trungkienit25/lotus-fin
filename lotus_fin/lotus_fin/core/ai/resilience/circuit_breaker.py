from enum import Enum
import time
from typing import Any, Callable, Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while circuit is open."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern protecting upstream LLM and third-party APIs from cascading failure.
    Transitions:
    - CLOSED -> OPEN after `failure_threshold` consecutive failures.
    - OPEN -> HALF_OPEN after `recovery_timeout` seconds.
    - HALF_OPEN -> CLOSED on successful execution; OPEN on failure.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN allows single probe

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def execute(
        self,
        func: Callable[..., Any],
        fallback_func: Optional[Callable[..., Any]] = None,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Executes func with circuit breaker protection, executing fallback_func on failure."""
        if not self.can_execute():
            if fallback_func is not None:
                return fallback_func(*args, **kwargs)
            raise CircuitBreakerOpenException("Circuit breaker is currently OPEN.")

        try:
            res = func(*args, **kwargs)
            self.record_success()
            return res
        except Exception as e:
            self.record_failure()
            if fallback_func is not None:
                return fallback_func(*args, **kwargs)
            raise e
