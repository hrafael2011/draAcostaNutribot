# AGENTS.md

## Project identity

Project name: `diet_telegram_agent`

Purpose:
System for a nutrition practice where the doctor manages patients from a web admin panel and operates a Telegram assistant to review patient data, generate diets, revise drafts, and approve final plans.

Core stack:

- Backend: FastAPI, SQLAlchemy async, PostgreSQL, Alembic
- Frontend: React, Vite, TypeScript
- Channel assistant: Telegram bot for the doctor
- AI usage: diet generation and some intent support

## Current product direction

The product is being shaped around a healthcare-safe workflow.

Priority areas:

1. Safe Telegram navigation
2. Draft-based diet review before approval
3. Low-friction UX for the doctor
4. Auditability and version discipline
5. Prevention of duplicate or stale Telegram actions

## Important architecture facts

1. Telegram flows are stateful and use `ConversationState`.
2. Diet generation creates drafts that can later be approved.
3. Approved diets should be treated as final clinical output.
4. Telegram callback safety is critical because duplicate clicks can create inconsistent clinical actions.
5. The backend is the real source of truth; Telegram UI alone is not sufficient for protection.
6. The product is not multitenant for now: account creation must be controlled, not public.

## Docker/runtime notes

Current local container behavior:

1. `backend` is built into the image from `backend/Dockerfile`.
2. There is no backend source bind mount in `docker-compose.yml`.
3. Backend changes require rebuild/recreate of the backend container to take effect.
4. `ngrok` is used for Telegram webhook exposure.
5. Current backend host mapping is `127.0.0.1:8020 -> 8000`.

## Deployment environments

Vercel project:

- `dra-acosta-nutribot`

Environment routing:

1. Vercel `Production` must use Railway `production`.
2. Vercel `Preview` for branch `dev` must use Railway `Staging-dev`.
3. Vercel `Development` must use Railway `Staging-dev` unless explicitly testing against local backend.
4. Do not point Vercel preview/development to Railway production.
5. Do not point production UI to staging APIs.

Current frontend API variables:

1. Vercel `Production`: `VITE_API_BASE_URL=https://diet-backend-production-9360.up.railway.app/api`
2. Vercel `Preview (dev)`: `VITE_API_BASE_URL=https://diet-backend-staging-dev.up.railway.app/api`
3. Vercel `Development`: `VITE_API_BASE_URL=https://diet-backend-staging-dev.up.railway.app/api`

## Recent work already completed

Telegram anti-duplication work has been started and partially implemented.

Implemented direction:

1. Critical Telegram callbacks now use stronger backend guards.
2. Active message validation by `message_id` was introduced for critical actions.
3. Diet approval, discard, confirm, quick adjust, and preview safety were reinforced.
4. Wizard inline steps were also extended to use current-message validation.
5. Focused automated tests were added and updated for these protections.

Important:

- If new Telegram UX work is done, preserve and extend these anti-duplication protections rather than replacing them with UI-only logic.

## Telegram UX strategy reference

There is a dedicated design reference file:

- `TELEGRAM_UX_NAVIGATION_PLAN.md`

That document is the source of truth for:

1. wizard navigation model
2. back/refresh/cancel strategy
3. button behavior
4. draft preview redesign
5. meal editing recovery plan
6. healthcare-safe approval lifecycle

When working on Telegram UX, read that file first.

## Product decisions to preserve

1. The doctor must always know the current flow and step.
2. Navigation must be recoverable; old Telegram messages must not control the active state.
3. Draft review must happen before approval.
4. Meal editing should happen on drafts, not on approved diets.
5. Any post-approval change should create a new draft/version, not mutate approved output directly.

## Preferred UX direction

Recommended Telegram interaction model:

1. Controlled wizard navigation
2. Visual blocking/replacement of processed buttons instead of silent disappearance
3. Persistent navigation actions such as:
   - back
   - refresh current step
   - cancel flow
4. Full 7-day draft review before approval
5. Meal-level editing in pending drafts

## Clinical safety rules

1. Do not weaken approval boundaries.
2. Do not allow stale callbacks to mutate final clinical state.
3. Keep auditability in mind whenever manual edits are introduced.
4. If a change affects diet editing or approval, think in terms of versioning.
5. Prioritize consistency and traceability over clever UI shortcuts.

## Account and access model

1. Public doctor registration must stay disabled in production.
2. Accounts are controlled by an internal administrator, not by an open signup screen.
3. Users have a `role` such as `admin` or `doctor`.
4. Temporary passwords must set `must_change_password = true`.
5. A user with `must_change_password = true` may only change their password; clinical/admin routes must remain blocked.
6. The administrator may create/reset doctor access, but must not know the doctor's final private password.
7. Admin recovery should happen through a controlled internal script or operational process, not through a public recovery button in this MVP.

Operational bootstrap:

- Use `backend/scripts/bootstrap_admin.py` to create or reset the internal admin account.

## Working conventions for future sections

When switching topics in this repo:

1. Re-read `AGENTS.md`
2. Re-read `TELEGRAM_UX_NAVIGATION_PLAN.md` if the topic touches Telegram UX
3. Preserve the healthcare-first decision model
4. Avoid broad refactors unless they directly support the active objective
5. Treat this file as stable context memory for the project

## Recommended future memory additions

This file should be updated when major decisions are made in these areas:

1. Telegram navigation model
2. Diet preview UX
3. Meal editing workflow
4. Approval/versioning rules
5. Deployment/runtime behavior
