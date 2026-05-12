# tikko — project conventions

## Stack

- **apps/api** — FastAPI + SQLAlchemy 2.x + Alembic + pyzk + pytest, managed by `uv`
- **apps/web** — Next.js App Router + TypeScript + vitest
- **apps/mobile** — Expo + React Native + TypeScript + jest
- **packages/api-client** — generated TS client (from `apps/api`'s OpenAPI schema)
- **packages/shared-types** — Zod schemas + shared enums/constants

## Single-deployable contract

There is ONE build of this app. Deployment differences are environment-driven, never code branches per environment.

- `TIKKO_DEPLOY_MODE=lan|cloud` switches: which interfaces the ADMS push endpoint binds to, whether TLS is required, default CORS, default poll intervals
- All device connection info is per-row in the `devices` table, not in env
- Never write `if mode == "lan"` branches in business logic — that's a sign the abstraction is wrong

## Test commands

- **api:** `cd apps/api && uv run pytest` (single file: `uv run pytest path/to/test_x.py`)
- **web:** `pnpm --filter @tikko/web test` (single file: `pnpm --filter @tikko/web test path/to/x.test.ts`)
- **mobile:** `pnpm --filter @tikko/mobile test`
- **everything:** `pnpm test` (runs turbo across web/mobile + pytest on api)

## Naming

- Python: `snake_case` for files, functions, vars; `PascalCase` for classes
- TS: `camelCase` for files matching their default export; `PascalCase` for React components
- DB: `snake_case` tables and columns; tables are **plural** (`devices`, `attendance_logs`)
- API routes: kebab/lowercase, plural resources (`/devices`, `/attendance-logs`)
- Env: `TIKKO_*` prefix for everything

## API shape

- REST with JSON
- Response envelope: raw object/array on success; `{ "detail": "..." }` on error (FastAPI default)
- Pagination: `?page=1&page_size=50`, response includes `total` + `items`
- Timestamps: ISO 8601 UTC, suffix `_at`

## Errors

- Python: raise `HTTPException` at route layer; raise domain exceptions from `tikko.errors` deeper in
- TS: throw `Error` subclasses; centralized error boundary in web; toast on mobile

## Logging

- Python: structlog (configured in `apps/api/tikko/logging.py`)
- Level from `TIKKO_LOG_LEVEL`
- Log: incoming requests at info, errors at error with stack, device protocol events at debug

## Validation

- API input: Pydantic models at the route boundary
- DB: SQLAlchemy types + Alembic-managed constraints
- Web/mobile: Zod schemas from `packages/shared-types`

## Git workflow

- Per-feature commits directly on `main`
- Commit format: `F0X: <short description>` (e.g. `F01: monorepo skeleton`)
- One commit per feature when it moves to `done.md`
- The implementation guide gets its own commit at the end

**No `Co-Authored-By:` or `Generated with Claude Code` trailers/footers in commit messages or PR bodies.** (Inherited from user-global CLAUDE.md.)

## Working with features

- `tasks/all-features.md` — full feature list (source of truth)
- `tasks/todo.md` — current feature in progress + blocked features
- `tasks/done.md` — completed features with metadata
- TDD: failing test first, minimal implementation, then green
- 15-minute debug cap → mark blocked, move on
