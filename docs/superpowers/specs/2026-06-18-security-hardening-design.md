# Security Hardening — Post-OWASP Fixes

## Context

OWASP ASI + general security scan found 6 issues. This spec covers fixes in priority order.

## Changes

### 🔴 Issue 1: CORS Restriction (ALTA)

**File:** `backend/app/core/config.py`, `backend/.env.example`

**Problem:** `CORS_ORIGINS=*` with `allow_credentials=True` is unsafe in production.

**Fix:** Add startup validation — if `ENV=production` or Railway detected and `CORS_ORIGINS` is `*`, emit a `logger.warning`. Update `.env.example` comment.

### 🔴 Issue 2: npm HIGH vulnerability (ALTA)

**File:** `frontend/package.json` (auto-updated by npm)

**Problem:** vite <7.3.4 has Windows-only CVEs.

**Fix:** Run `npm audit fix`. Updates patch versions only. No breaking changes.

### 🟡 Issue 3: npm MODERATE vulnerabilities (MEDIA)

**Fix:** Same `npm audit fix` as Issue 2. Covers js-yaml, postcss, react-router.

### 🟡 Issue 4: Structured JSON Logging (MEDIA)

**Files:** `backend/app/core/logging_config.py` (new), `backend/app/main.py`, `backend/requirements.txt`

**Fix:**
- Add `python-json-logger` dependency
- Create `logging_config.py` — JSON format in production, text in dev
- Import and call in `main.py` startup

### 🟢 Issue 5: Circuit Breaker (BAJA)

**File:** `backend/app/core/circuit_breaker.py` (new), `backend/app/main.py`

**Fix:** Simple middleware — counts 5xx responses. If >50 in 60s window → return 503 for 30s. Logs events. No dependency needed.

### 🟢 Issue 6: pip-audit (BAJA)

**Fix:** `pip install pip-audit && pip-audit` — read-only scan, no code changes.

### Final: Re-scan

Run full OWASP ASI + secrets scan again to verify all issues resolved.

## Files affected

| File | Action |
|------|--------|
| `backend/app/core/config.py` | +5 lines CORS validation |
| `backend/.env.example` | Better CORS comment |
| `backend/app/core/logging_config.py` | New — ~30 lines |
| `backend/app/main.py` | +2 lines import logging config + circuit breaker |
| `backend/app/core/circuit_breaker.py` | New — ~40 lines |
| `backend/requirements.txt` | +python-json-logger |
| `frontend/package.json` | npm audit fix (auto) |
