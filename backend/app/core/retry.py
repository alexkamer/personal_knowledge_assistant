"""
Retry logic with exponential backoff for resilient API calls.

Provides decorators and utilities for retrying failed operations with configurable
backoff strategies and circuit breaker pattern.
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Optional, Type, Tuple

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker for {service_name} is open")


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures.

    Prevents cascading failures by stopping requests after failure threshold.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "default",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            name: Identifier for this circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: Attempting recovery (half-open)")
                self.state = "half_open"
            else:
                logger.warning(f"Circuit breaker {self.name}: OPEN - rejecting request")
                raise CircuitBreakerOpen(self.name)

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                logger.info(f"Circuit breaker {self.name}: Recovery successful (closed)")
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self):
        """Record a failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker {self.name}: OPENING (failures: {self.failure_count})"
            )
            self.state = "open"

    def reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
):
    """
    Decorator to retry function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        circuit_breaker: Optional circuit breaker to use

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Check circuit breaker if provided
                    if circuit_breaker and circuit_breaker.state == "open":
                        raise CircuitBreakerOpen(circuit_breaker.name)

                    # Attempt function call
                    result = await func(*args, **kwargs)

                    # Reset circuit breaker on success
                    if circuit_breaker and attempt > 0:
                        circuit_breaker.reset()

                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )

                    return result

                except exceptions as e:
                    last_exception = e

                    # Record failure in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        break

                    # Log retry
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Wait with exponential backoff
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            # Raise last exception if all retries failed
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Check circuit breaker if provided
                    if circuit_breaker and circuit_breaker.state == "open":
                        raise CircuitBreakerOpen(circuit_breaker.name)

                    # Attempt function call
                    result = func(*args, **kwargs)

                    # Reset circuit breaker on success
                    if circuit_breaker and attempt > 0:
                        circuit_breaker.reset()

                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )

                    return result

                except exceptions as e:
                    last_exception = e

                    # Record failure in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        break

                    # Log retry
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Wait with exponential backoff
                    time.sleep(delay)
                    delay *= backoff_factor

            # Raise last exception if all retries failed
            raise last_exception

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global circuit breakers for different services
ollama_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="ollama"
)

embedding_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    name="embedding"
)

vector_db_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=45,
    name="vector_db"
)
