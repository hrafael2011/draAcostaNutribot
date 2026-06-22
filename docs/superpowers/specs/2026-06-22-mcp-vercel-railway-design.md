# MCP Server: Vercel + Railway — Spec

**Date:** 2026-06-22
**Status:** Designing
**Author:** hrafael2011

## Purpose

A single MCP server that exposes Vercel (REST API) and Railway (GraphQL API) operations as MCP tools for Claude Code, packaged as a Docker container.

## Motivation

- The user deploys multiple projects: backend to Railway, frontend to Vercel, and more coming.
- Currently, interacting with either platform requires switching between browser dashboards or running CLIs manually.
- An MCP server lets Claude manage deploys, logs, env vars, and config from within a conversation — faster feedback and fewer context switches.
- One server, one Docker image, one entry in `mcpServers` config — reusable across all projects.

## Architecture

### Approach: SDK-first (REST API wrapping)

Control total sobre cada endpoint expuesto. Sin dependencia de CLIs externos. HTTP directo con `httpx` + Pydantic schemas.

### Component Diagram

```
Claude Code
    │ STDIN (JSON-RPC)
    ▼
server.py  ──creates──►  mcp.Server
                              │
    ┌─────────────────────────┤
    │                         │
    ▼                         ▼
vercel/tools.py          railway/tools.py
    │                         │
    ▼                         ▼
vercel/client.py         railway/client.py
 (httpx → REST)          (httpx → GraphQL)
    │                         │
    ▼                         ▼
api.vercel.com           backboard.railway.app/graphql
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python + `mcp` SDK | Same stack as backend; official SDK well-maintained |
| One server, two platforms | Single entrypoint in Claude Code config |
| STDIO transport only | No network attack surface; MCP native transport |
| Tokens via env vars | 12-factor; no secrets in code or image |
| Pydantic schemas for all tool inputs/outputs | Validates before execution; Claude gets typed errors |
| No CLI dependency (`vercel`, `railway`) | Smaller Docker image; no subprocess parsing fragility |

## Project Structure

```
mcp-vercel-railway/               # Repositorio independiente (github.com/hrafael2011/mcp-vercel-railway)
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
├── .env.example
│
├── src/
│   ├── __init__.py
│   ├── server.py                # Entrypoint: creates mcp.Server, registers tools
│   ├── config.py                # Loads VERCEL_TOKEN, RAILWAY_TOKEN from env
│   │
│   ├── vercel/
│   │   ├── __init__.py
│   │   ├── client.py            # httpx async client for Vercel REST API
│   │   └── tools.py             # MCP tool definitions for Vercel
│   │
│   ├── railway/
│   │   ├── __init__.py
│   │   ├── client.py            # httpx async client for Railway GraphQL API
│   │   ├── schema.py            # GraphQL types and queries
│   │   └── tools.py             # MCP tool definitions for Railway
│   │
│   └── shared/
│       ├── __init__.py
│       ├── errors.py            # AuthError, NotFoundError, RateLimitError, PlatformError
│       └── models.py            # Shared Pydantic models
│
└── tests/
    ├── conftest.py
    ├── test_vercel_client.py
    ├── test_vercel_tools.py
    ├── test_railway_client.py
    └── test_railway_tools.py
```

## MCP Tools

### Railway (GraphQL API → `https://backboard.railway.app/graphql`)

| Tool | Description |
|------|-------------|
| `railway_list_projects` | List all projects accessible to the token |
| `railway_list_services` | List services within a project |
| `railway_list_deployments` | Deployment history for a service |
| `railway_get_deployment_logs` | Build/deploy logs for a specific deployment |
| `railway_get_variables` | Environment variables for a service or project |
| `railway_upsert_variable` | Create or update an environment variable |
| `railway_delete_variable` | Delete an environment variable |
| `railway_trigger_deploy` | Trigger a new deployment for a service |
| `railway_get_status` | Current status of a service (healthy, deploying, crashed) |

### Vercel (REST API → `https://api.vercel.com`)

| Tool | Description |
|------|-------------|
| `vercel_list_projects` | List all projects |
| `vercel_get_project` | Get project details |
| `vercel_list_deployments` | Deployment history for a project |
| `vercel_get_deployment` | Get deployment detail (status, logs, events) |
| `vercel_trigger_deploy` | Trigger deploy via deploy hook or API |
| `vercel_cancel_deployment` | Cancel an in-progress deployment |
| `vercel_list_env_vars` | Environment variables for a project |
| `vercel_upsert_env_var` | Create or update an environment variable |
| `vercel_delete_env_var` | Delete an environment variable |
| `vercel_list_domains` | Domains associated with a project |
| `vercel_add_domain` | Add a domain to a project |

### Tool Design Principles

- Each tool has a Pydantic model for inputs (validated by MCP SDK before execution).
- Each tool returns a typed Pydantic model (structured output Claude can reason about).
- Tool names are verb-noun (`list_projects`, `get_deployment_logs`), consistent across platforms.
- Tools that mutate (`upsert_variable`, `trigger_deploy`) include a `reason` parameter so Claude documents why the change was made.

## Error Handling

### Exception Hierarchy (`shared/errors.py`)

```
MCPServiceError (base)
├── AuthError            # 401 — "check YOUR_TOKEN"
├── NotFoundError        # 404 — "project X not found"
├── RateLimitError       # 429 — "retry in N seconds"
└── PlatformError        # 5xx — "Vercel/Railway internal error"
```

### Flow

1. `client.py` makes HTTP call → catches `httpx.HTTPStatusError` → raises typed `MCPServiceError`
2. `tools.py` calls client; doesn't catch — lets exceptions bubble
3. `server.py` middleware catches `MCPServiceError` → converts to structured MCP error response with actionable message
4. Unexpected exceptions (bugs in our code) → caught by fallback handler → generic "internal error" with traceback logged to stderr (not exposed to Claude)

### Retries

`client.py` uses `httpx.AsyncClient` with `transport=AsyncHTTPTransport(retries=3)` for transient network errors and 429 responses, with exponential backoff: 1s → 2s → 4s.

## Security

| Measure | Detail |
|---------|--------|
| **STDIO-only transport** | No HTTP listener, no ports exposed. Communication is stdin/stdout. Zero network attack surface. |
| **Tokens via env vars** | `VERCEL_TOKEN` and `RAILWAY_TOKEN` passed via `docker run -e`. Never in code, image, or logs. |
| **No secrets persistence** | Container is ephemeral (`--rm`). No filesystem writes beyond Python bytecode cache. |
| **User non-root** | `Dockerfile` creates `mcp` user; `USER mcp` before entrypoint. |
| **Minimal base image** | `python:3.12-slim`. No shells beyond what Python needs. |
| **HTTPS enforced** | `httpx` defaults `verify=True`. No option to disable. |
| **Token sanitization** | `config.py` overrides `__repr__` and `__str__` on token holders to prevent accidental logging. |
| **Rate limiting** | Internal backoff prevents hammering Vercel/Railway APIs. |

### What We Don't Do (and Why)

- **No HTTP MCP transport** — Adds attack surface. STDIO is simpler and sufficient for local Claude Code usage.
- **No secrets manager** — Overkill for single-user use case. Env vars are the standard.
- **No multi-tenancy** — One token per platform. If needed later, run multiple container instances with different env vars.

## Docker

### Dockerfile (Multi-Stage)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

RUN useradd --create-home --shell /bin/bash mcp && \
    chown -R mcp:mcp /app

COPY --from=builder /root/.local /home/mcp/.local
COPY src/ ./src/

ENV PATH="/home/mcp/.local/bin:${PATH}"
USER mcp
ENTRYPOINT ["python", "-m", "src.server"]
```

### Usage

```json
// ~/.claude/settings.json or project .claude/settings.local.json
{
  "mcpServers": {
    "vercel-railway": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "VERCEL_TOKEN",
        "-e", "RAILWAY_TOKEN",
        "mcp-vercel-railway:latest"
      ]
    }
  }
}
```

### Requirements (`requirements.txt`)

```
mcp>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## Testing Strategy

- **Unit tests** for `client.py` — mock `httpx` responses; verify correct URL construction, header injection, error mapping
- **Unit tests** for `tools.py` — mock client; verify tool schemas and input validation
- **Integration tests** — optional; require real tokens (marked with `@pytest.mark.integration`, skipped in CI by default)
- **No tests that call real Vercel/Railway APIs** unless explicitly opted in

## Repo Location

Repositorio independiente: `github.com/hrafael2011/mcp-vercel-railway`

- Publicado como imagen Docker en GitHub Container Registry (`ghcr.io/hrafael2011/mcp-vercel-railway:latest`)
- Se usa desde cualquier proyecto añadiéndolo al `settings.json`
- Desacoplado del ciclo de desarrollo de cualquier proyecto en particular
- Se comparte entre todos los proyectos del usuario
