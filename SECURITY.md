# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Active development |
| < 1.0   | ❌ Pre-release (no longer supported) |

## Reporting a Vulnerability

This project handles **clinical and personal health data**. We take security seriously.

**Do not** open a public GitHub issue to report a vulnerability. Instead, send an email to:

📧 **hendrick@example.com** (replace with the maintainer's actual email)

Please include:
- A description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if available)

You will receive a response within **72 hours** with an assessment and remediation timeline.

## What to Expect

1. **Acknowledgment** — we confirm receipt within 3 business days
2. **Assessment** — we evaluate severity and impact
3. **Fix** — a patch is developed and tested
4. **Release** — a security patch is published
5. **Disclosure** — after the fix is released, we may publish an advisory

## Scope

This policy covers all components in this repository:
- Backend API (FastAPI/Python)
- Frontend web application (React/TypeScript)
- Database schema and migrations
- Deployment configurations (Railway, Vercel, Docker)
- Telegram bot integration

## Clinical Data Note

This application processes **health-related personal data**. If you discover a vulnerability that could lead to unauthorized access to patient data, please flag it as **CRITICAL** in your report.

## Security Features

The project implements the following security measures:
- JWT-based authentication with bcrypt password hashing
- 3-tier RBAC (super_admin, admin, doctor)
- Rate limiting on authentication endpoints
- Circuit breaker for external API calls
- Soft delete with audit trail for clinical data
- Strict CORS configuration
- Force password change on first login
- Production registration lock (single-tenant)
