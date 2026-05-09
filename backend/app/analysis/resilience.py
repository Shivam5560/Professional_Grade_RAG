"""
Resilience patterns: circuit breaker and retry utilities.

The CircuitBreaker prevents cascading failures when the LLM provider is
unhealthy. After `failure_threshold` consecutive failures, the circuit
opens and all calls immediately fail without touching the downstream
service. After `recovery_timeout` seconds, a single trial call is
allowed (half-open); if it succeeds, the circuit closes.
"""

from __future__ import annotations

import threading
import time
from enum import Enum, auto
from typing import Callable

from app.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = auto()  # Normal operation
    OPEN = auto()  # Failing fast
    HALF_OPEN = auto()  # Testing recovery


class CircuitBreaker:
    """Stateful circuit breaker for external service calls."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    def call(self, fn: Callable, *args, **kwargs):
        """Execute a call through the circuit breaker. Raises CircuitBreakerOpenError if open."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.warning(
                        "CircuitBreaker '%s' entering HALF_OPEN — testing recovery",
                        self.name,
                    )
                else:
                    raise CircuitBreakerOpenError(
                        f"CircuitBreaker '{self.name}' is OPEN. "
                        f"Retry in {self._recovery_timeout - (time.monotonic() - self._last_failure_time):.0f}s"
                    )

        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.monotonic()
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.OPEN
                    logger.error("CircuitBreaker '%s' re-opened after trial failure", self.name)
                elif self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.error(
                        "CircuitBreaker '%s' OPEN after %d consecutive failures",
                        self.name,
                        self._failure_count,
                    )
            raise

        # Success
        with self._lock:
            was_open = self._state != CircuitState.CLOSED
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            if was_open:
                logger.log_operation("CircuitBreaker CLOSED", name=self.name, event="recovery")
        return result

    def is_callable(self) -> bool:
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                    return True
                return False
            return True  # HALF_OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""
    pass
