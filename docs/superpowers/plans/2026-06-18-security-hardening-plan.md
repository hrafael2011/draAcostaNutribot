# Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 security issues found in OWASP ASI + general security scan, then re-scan to verify.

**Architecture:** Six independent fixes across backend and frontend — CORS validation warning, npm patch updates, JSON logging formatter, circuit breaker middleware, pip-audit install, and final re-scan. No breaking changes.

**Tech Stack:** Python 3.12 / FastAPI / Starlette middleware, Node.js / npm, python-json-logger

---

### Task 1: CORS — Add production validation warning

**Files:**
- Modify: `backend/app/core/config.py:62-66`

- [ ] **Step 1: Add CORS production warning to config.py**

In the `normalize_values` validator, after the existing JWT_SECRET check, add a CORS warning:

```python
# backend/app/core/config.py — inside normalize_values() validator, after line 73
        if self.is_production and self.CORS_ORIGINS.strip() == "*":
            import logging
            logging.getLogger(__name__).warning(
                "CORS_ORIGINS='*' in production — restrict to specific origins via CORS_ORIGINS env var"
            )
```

The complete updated `normalize_values` method becomes:

```python
    @model_validator(mode="after")
    def normalize_values(self) -> "Settings":
        self.ENV = (self.ENV or "development").strip().lower()
        self.CORS_ORIGINS = (self.CORS_ORIGINS or "*").strip() or "*"
        self.DATABASE_URL = normalize_async_database_url(self.DATABASE_URL)
        if self.is_production and self.JWT_SECRET == "change-me":
            raise ValueError("JWT_SECRET must be configured in production")
        if self.is_production and self.CORS_ORIGINS.strip() == "*":
            import logging
            logging.getLogger(__name__).warning(
                "CORS_ORIGINS='*' in production — restrict to specific origins via CORS_ORIGINS env var"
            )
        return self
```

- [ ] **Step 2: Update .env.example CORS comment**

Replace the CORS line in `backend/.env.example`:

```
# CORS: comma-separated origins, or * for any (dev only)
# CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

With:

```
# CORS: comma-separated origins. * only for local dev. In production set your actual frontend domain:
# CORS_ORIGINS=https://tudominio.com
```

- [ ] **Step 3: Verify config loads without error**

Run:
```bash
cd backend && ENV=development python -c "from app.core.config import settings; print('CORS:', settings.CORS_ORIGINS)"
```
Expected: `CORS: *` (no crash)

Run:
```bash
cd backend && ENV=production CORS_ORIGINS=https://example.com JWT_SECRET=test-secret-12345678 python -c "from app.core.config import settings; print('OK')" 2>&1
```
Expected: `OK` (no warning, valid origin set)

Run (should warn):
```bash
cd backend && ENV=production JWT_SECRET=test-secret-12345678 python -c "from app.core.config import settings" 2>&1
```
Expected: Warning about CORS_ORIGINS=*

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/config.py backend/.env.example
git commit -m "security: add CORS production warning when origins set to *"
```

---

### Task 2: npm audit fix — Patch vulnerable dependencies

**Files:**
- Modify: `frontend/package.json`, `frontend/package-lock.json` (auto-updated)

- [ ] **Step 1: Run npm audit fix**

```bash
cd frontend && npm audit fix
```

- [ ] **Step 2: Verify no regressions — TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Verify vulnerabilities resolved**

```bash
cd frontend && npm audit --audit-level=high
```
Expected: 0 high-severity vulnerabilities

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "security: npm audit fix — patch vite, react-router, js-yaml, postcss"
```

---

### Task 3: JSON Structured Logging

**Files:**
- Create: `backend/app/core/logging_config.py`
- Modify: `backend/app/main.py:19-23`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add python-json-logger dependency**

Add to `backend/requirements.txt` after line 10 (`python-dotenv>=1.0.1`):

```
python-json-logger>=3.3.0
```

- [ ] **Step 2: Create logging_config.py**

Create `backend/app/core/logging_config.py`:

```python
"""Structured JSON logging for production, plain text for development."""
import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(is_production: bool) -> None:
    root = logging.getLogger()
    # Remove any existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if is_production:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(levelname)-8s %(name)-24s %(message)s",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quieter client libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

- [ ] **Step 3: Wire logging_config into main.py**

Replace lines 17-27 in `backend/app/main.py`:

```python
# Remove this block (lines 17-27):
logger = logging.getLogger(__name__)

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

# Quieter client libraries; app loggers still emit ERROR/WARNING as needed.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
```

With:

```python
from app.core.logging_config import setup_logging

setup_logging(settings.is_production)
logger = logging.getLogger(__name__)
```

- [ ] **Step 4: Install dependency and test**

Run:
```bash
cd backend && pip install python-json-logger && python -c "
from app.core.config import settings
from app.core.logging_config import setup_logging
import logging
setup_logging(False)
logging.getLogger('test').info('hello dev')
print('--- dev format OK ---')
setup_logging(True)
logging.getLogger('test').info('hello prod')
print('--- json format OK ---')
"
```
Expected: Dev format shows plain text, prod format shows JSON line.

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/core/logging_config.py backend/app/main.py
git commit -m "security: add JSON structured logging for production"
```

---

### Task 4: Circuit Breaker Middleware

**Files:**
- Create: `backend/app/core/circuit_breaker.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create circuit_breaker.py**

Create `backend/app/core/circuit_breaker.py`:

```python
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
```

- [ ] **Step 2: Add to main.py middleware stack**

Add the import after line 9 in `backend/app/main.py`:

```python
from app.core.circuit_breaker import CircuitBreakerMiddleware
```

Add the middleware after the CORS middleware (after line 43):

```python
# Circuit breaker — trips on sustained 5xx errors
app.add_middleware(CircuitBreakerMiddleware)
```

- [ ] **Step 3: Verify circuit breaker imports**

Run:
```bash
cd backend && python -c "from app.core.circuit_breaker import CircuitBreakerMiddleware; print('import OK')"
```
Expected: `import OK`

- [ ] **Step 4: Verify app still loads with middleware**

Run:
```bash
cd backend && ENV=development python -c "from app.main import app; print('app loaded OK')"
```
Expected: `app loaded OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/circuit_breaker.py backend/app/main.py
git commit -m "security: add circuit breaker middleware for sustained 5xx errors"
```

---

### Task 5: pip-audit — Install and scan Python dependencies

**Files:** None modified (read-only tool)

- [ ] **Step 1: Install pip-audit**

```bash
pip install pip-audit
```

- [ ] **Step 2: Run pip-audit**

```bash
cd backend && pip-audit
```
Note: Vulnerabilities found should be reported. If any CRITICAL/HIGH, flag them explicitly.

- [ ] **Step 3: Document results (no commit needed for tool-only change)**

Record output for final report.

---

### Task 6: Run backend tests — Verify no regressions

**Files:** None modified

- [ ] **Step 1: Run unit tests**

```bash
cd backend && python -m pytest tests/test_diet_eligibility.py tests/test_nutrition_engine.py tests/test_nutrition_integration.py tests/test_nutrition_contract.py tests/test_diet_duration.py tests/test_diet_export_pdf.py tests/test_config.py -v
```
Expected: 32 passed

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

---

### Task 7: Final OWASP + Secrets Re-scan

**Files:** None modified

- [ ] **Step 1: Re-run secrets scan**

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent && \
  echo "=== Secrets in HEAD ===" && \
  git ls-tree -r HEAD --name-only | grep -iE "\.env$|\.pem$|\.key$|credentials\.json|\.p12$|secret" || echo "None in HEAD" && \
  echo "=== Unsafe execution patterns ===" && \
  grep -rn "eval(\|exec(\|subprocess\.run.*shell=True\|os\.system(" --include="*.py" backend/app/ || echo "None found" && \
  echo "=== Hardcoded secrets ===" && \
  grep -rn "password\s*=\s*['\"]\w\|secret\s*=\s*['\"]\w\|api_key\s*=\s*['\"]\w" --include="*.py" backend/app/ | grep -v "test_\|example\|#" || echo "None found"
```

- [ ] **Step 2: Verify npm audit clean**

```bash
cd frontend && npm audit --audit-level=high
```
Expected: 0 high vulnerabilities

- [ ] **Step 3: Verify CORS in production warns**

```bash
cd backend && ENV=production JWT_SECRET=test-secret-12345678 python -c "from app.core.config import settings" 2>&1 | grep -i "cors"
```
Expected: Warning message about CORS_ORIGINS

- [ ] **Step 4: Compile final report**

Document before/after comparison using the findings from the initial OWASP scan vs. post-fix state.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "security: final OWASP re-scan — all issues resolved"
```
