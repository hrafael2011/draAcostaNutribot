"""Simple circuit breaker middleware — trips on sustained 5xx errors."""
import logging
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Open the circuit when >50 5xx errors occur in a 60s window.

    While open, all requests get HTTP 503. Resets after 30s of no 5xx.
    """

    def __init__(self, app, threshold: int = 50, window_s: float = 60.0, cooldown_s: float = 30.0):
        super().__init__(app)
        self.threshold = threshold
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self._errors: deque[float] = deque()
        self._opened_at: float | None = None

    async def dispatch(self, request: Request, call_next):
        now = time.monotonic()

        # If circuit is open, check cooldown
        if self._opened_at is not None:
            if now - self._opened_at < self.cooldown_s:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Service temporarily unavailable — circuit breaker open"},
                )
            # Cooldown elapsed — half-open
            logger.info("Circuit breaker half-open, testing")
            self._opened_at = None

        # Prune old errors outside window
        cutoff = now - self.window_s
        while self._errors and self._errors[0] < cutoff:
            self._errors.popleft()

        response = await call_next(request)

        # Track 5xx
        if response.status_code >= 500:
            self._errors.append(now)
            if len(self._errors) >= self.threshold:
                self._opened_at = now
                logger.error(
                    "Circuit breaker OPEN — %d 5xx in %ds, blocking for %ds",
                    len(self._errors),
                    self.window_s,
                    self.cooldown_s,
                )

        return response
