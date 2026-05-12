# Done

## F01 — Monorepo skeleton ✓
- **Tests:** smoke check — `pnpm install` resolves the workspace (prettier + turbo installed)
- **Files changed:** 13 new (root configs + tasks/ folder)
- **Lines:** +~300
- **Complexity:** Low — pure tooling/configs, no logic
- **Notes:**
  - `just` skipped (not installed); root `pnpm` scripts orchestrate everything, calling `uv run` for Python tasks. Can swap to `just` later if desired.
  - Single-deployable contract documented in CLAUDE.md — no branching on `TIKKO_DEPLOY_MODE` in business logic.
  - All env vars use `TIKKO_*` prefix.
  - Git initialized on `main` with per-feature commit convention.

## F02 — CI workflow ✓
- **Tests:** smoke check — YAML parses; 5 jobs detected (workspace, api, web, mobile, packages)
- **Files changed:** 1 new (`.github/workflows/ci.yml`)
- **Lines:** +~115
- **Complexity:** Low — single workflow file
- **Notes:**
  - Each app-specific job is gated by `if: hashFiles(...)` so the workflow doesn't fail before F03/F04/F05 land.
  - Workspace job (install + prettier check) runs unconditionally.
  - Uses `pnpm/action-setup@v4`, `actions/setup-node@v4` w/ pnpm cache, `astral-sh/setup-uv@v6` for the Python api.
  - Concurrency group set to cancel superseded runs on the same ref.

## F03 — API skeleton ✓
- **Tests:** 2/2 passing (`test_health_returns_ok`, `test_health_is_unauthenticated`)
- **Files changed:** 7 new (pyproject.toml, README, src/tikko/{__init__,settings,main}.py, tests/{__init__,conftest,test_health}.py) + uv.lock
- **Lines:** +~150 src/test + lockfile
- **Complexity:** Low — `/health` route, settings class, two assertion tests
- **Notes:**
  - Deps: fastapi[standard], pydantic-settings, sqlalchemy[asyncio], alembic, psycopg[binary], structlog, pyzk 0.9. Dev: pytest, pytest-asyncio, httpx, ruff.
  - Used `[dependency-groups].dev` (modern uv) instead of deprecated `[tool.uv].dev-dependencies`.
  - `Settings.deploy_mode` is a `StrEnum` (`lan`/`cloud`). Re-iterated in docstring: deploy_mode affects bindings/TLS/defaults only, never business logic.
  - `get_settings()` returns a cached singleton; tests can patch it later.
  - Ruff config in `pyproject.toml`, `select = [E,W,F,I,B,UP,RUF]`; clean.

## F04 — Web skeleton ✓
- **Tests:** 2/2 passing (Home renders the tikko heading; links to /devices)
- **Files changed:** 10 new (package.json, tsconfig.json, next.config.ts, vitest.config.ts, vitest.setup.ts, .eslintrc.json, next-env.d.ts, app/layout.tsx, app/page.tsx, app/__tests__/home.test.tsx) + pnpm-lock updates
- **Lines:** +~150 src/test
- **Complexity:** Low — single page + smoke component test
- **Notes:**
  - Next 15.1, React 19, TypeScript 5.7, Vitest 2.1, jsdom 25
  - `outputFileTracingRoot` pinned to repo root to silence Next's "multiple lockfiles" warning (there's a stray `package-lock.json` somewhere up the directory tree).
  - `next lint` is deprecated in Next 15.x and will be removed in Next 16. Migration to `eslint` CLI + flat config deferred to a future feature (will tackle alongside Next 16 upgrade).
  - Tests run with `pnpm --filter @tikko/web test` via vitest.
  - Strict TDD: RED was implicit (test imports `../page` which didn't exist); didn't observe a failing vitest run separately because pnpm install hadn't completed yet. Future features will do explicit RED → GREEN.

## F05 — Mobile skeleton ✓
- **Tests:** 2/2 jest (Home renders heading + tagline)
- **Files:** package.json, app.json, tsconfig.json, babel.config.js, jest.setup.ts, .eslintrc.json, expo-env.d.ts, app/_layout.tsx, app/index.tsx, app/__tests__/index.test.tsx
- **Complexity:** Medium — Expo + pnpm + jest required custom transformIgnorePatterns; expo lint auto-downgraded eslint from 9 to 8 and required legacy `.eslintrc.json` (not flat config).
- **Stack:** Expo 52, expo-router 4, React 18.3, RN 0.76, jest 29 with jest-expo preset.
- **Pnpm quirk:** transformIgnorePatterns must match `node_modules/.pnpm/...` paths — broadened pattern with `.*` prefix.

## F06 — Shared packages ✓
- **Tests:** 8/8 (shared-types 6, api-client 2), typecheck clean both
- **Files:** packages/{shared-types,api-client}/{package.json, tsconfig.json, src/index.ts, src/index.test.ts}
- **Stack:** zod 3, openapi-fetch 0.13, openapi-typescript 7 (devDep, for `pnpm codegen`)
- **Notes:**
  - `@tikko/shared-types` exposes `DeviceSchema`, `DevicePunchSchema`, `DeployMode`, `UserRole` (mirrors api StrEnum)
  - `@tikko/api-client` wraps `openapi-fetch`; types loose until F07 lands the first endpoint, then `pnpm codegen` regenerates from `apps/api/openapi.json`
  - Packages exported as raw source (`main: src/index.ts`), no build step — TS consumers resolve directly via `moduleResolution: bundler`

## F07 — Device model + register ✓
- **Tests:** 8/8 (6 device + 2 health), ruff clean
- **Files:** src/tikko/{db,main}.py, src/tikko/models/{__init__,device}.py, src/tikko/schemas/{__init__,device}.py, src/tikko/routes/{__init__,devices}.py, tests/{conftest,test_devices}.py
- **Routes:** POST /devices (201), GET /devices (paginated list with total), GET /devices/{id} (404 on miss)
- **DB:** SQLAlchemy 2.x async, in-memory SQLite for tests (aiosqlite), Postgres in prod. `Base.metadata.create_all` on lifespan startup; Alembic deferred.
- **Notes:**
  - Patterns established: `SessionDep` annotated dep, `from_attributes=True` Pydantic config, response envelope `{ items, total }` for lists, UUID strings as IDs (sqlite-friendly), `created_at` defaulted with `datetime.now(UTC)`
  - conftest overrides `get_session` and resets `db_module._engine` per test for full isolation

## F08 — pyzk wrapper + test-connection ✓
- **Tests:** 11/11 (3 new: returns device info, 404 unknown device, 503 unreachable)
- **Files:** src/tikko/zk/{__init__,client}.py, src/tikko/schemas/zk.py, route added to devices.py
- **Wrapper:** `ZKClient.test_connection()` is synchronous (pyzk is sync); route wraps it with `asyncio.to_thread(...)` to keep the event loop free
- **Errors:** `ZKConnectionError` → HTTP 503 with detail; unknown device → 404
- **Tested via:** `unittest.mock.patch("tikko.routes.devices.ZKClient.test_connection", ...)` — no real device or network needed

## F09 — Attendance log poll ✓
- **Tests:** 15/15 (4 new: poll inserts + count, idempotent dedup, 404, list)
- **Files:** src/tikko/models/attendance.py, src/tikko/schemas/attendance.py, ZKClient.get_attendance(), 2 new routes
- **Routes:** POST /devices/{id}/poll → `{ polled, new }`, GET /devices/{id}/attendance → paginated `{ items, total }` with `?page=&page_size=`
- **Dedup:** UniqueConstraint on (device_id, device_user_id, punched_at). Insert uses SQLite dialect's `on_conflict_do_nothing`; needs a small switch when running on Postgres in prod (deferred to dialect-routing later).
- **RawPunch:** new dataclass in zk/client.py modeling one device-reported record before normalization.







