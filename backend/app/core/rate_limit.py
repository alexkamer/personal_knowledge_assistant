"""
Rate limiting middleware for API endpoints.

Implements token bucket algorithm for rate limiting requests to prevent abuse.
"""
import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        now = time.time()
        elapsed = now - self.last_update

        # Refill tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.

    Limits requests per IP address to prevent abuse.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # Tokens per second
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.burst_size, self.refill_rate)
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with rate limiting.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        bucket = self.buckets[client_ip]
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": int((1.0 / self.refill_rate) - bucket.tokens),
                },
            )

        # Process request
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Args:
            request: HTTP request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "default": {"requests_per_minute": 60, "burst_size": 100},
    "chat": {"requests_per_minute": 30, "burst_size": 50},  # More strict for LLM calls
    "search": {"requests_per_minute": 60, "burst_size": 100},
    "upload": {"requests_per_minute": 10, "burst_size": 20},  # Very strict for uploads
}


def get_rate_limit_config(endpoint: str) -> dict:
    """
    Get rate limit configuration for endpoint.

    Args:
        endpoint: Endpoint name

    Returns:
        Rate limit configuration dict
    """
    return RATE_LIMITS.get(endpoint, RATE_LIMITS["default"])
