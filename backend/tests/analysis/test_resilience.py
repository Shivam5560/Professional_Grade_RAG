"""Tests for CircuitBreaker and retry_with_backoff resilience."""

import time

import pytest

from app.analysis.resilience import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_callable()

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60)

        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert cb.state == CircuitState.OPEN

    def test_rejects_calls_when_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not be called")

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)

        # Should now be half-open and allow a trial call
        assert cb.is_callable()

        # Successful call should close the circuit
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    def test_reopens_after_half_open_failure(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        time.sleep(0.02)

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail again")))

        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=5)

        # Fail once
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        # Succeed
        cb.call(lambda: "ok")
        # Fail again — count should be 1, not 2
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        # Should still be CLOSED (only 1 consecutive failure after reset)
        assert cb.state == CircuitState.CLOSED

    def test_is_callable_returns_correctly(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
        assert cb.is_callable()

        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert not cb.is_callable()
