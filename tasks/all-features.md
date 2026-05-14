# tikko — All Features

## Context

- **Test runners:**
  - api: `cd apps/api && uv run pytest` (single file: `uv run pytest <path>`)
  - web: `pnpm --filter @tikko/web test` (vitest)
  - mobile: `pnpm --filter @tikko/mobile test` (jest)
  - everything: `pnpm test`
- **Patterns to follow:**
  - Naming: Python `snake_case`; TS `camelCase` files, `PascalCase` components; DB `snake_case` plural tables
  - Errors: Python — domain exceptions in `tikko.errors`, `HTTPException` at routes; TS — typed Error subclasses
  - Logging: `structlog` (python), `console.*` until web/mobile logger lands; level from `TIKKO_LOG_LEVEL`
  - API shape: REST + JSON, raw payload on success, `{ "detail": "..." }` on error, `?page=&page_size=` pagination with `{ items, total }`
  - Validation: Pydantic at API boundary, Zod in web/mobile (from `packages/shared-types`)
- **Reference features:** none yet — greenfield. First few features will set patterns; later features must follow them.
- **Single-deployable contract:** never branch on `TIKKO_DEPLOY_MODE` in business logic. Deploy mode only configures bindings/TLS/defaults, not behavior.
- **TDD scope note:** F01 / F02 / F31 are tooling/infra features — "test" is a smoke check (install, recipe runs, workflow file validates), not a unit test. From F03 onward, real failing-test-first TDD applies.

## Features

### UI Polish

- [x] UI Polish — Tailwind v4 + shadcn/ui (Radix base) + emerald brand + app shell + sidebar nav + page rewrites for login, devices, attendance

### Bootstrap

- [x] F01 — Monorepo skeleton (pnpm workspaces, turbo, root scripts, .gitignore, .env.example, README, CLAUDE.md, git init)
- [x] F02 — CI workflow (GitHub Actions: lint + test + typecheck for api/web/mobile)
- [x] F03 — API skeleton (FastAPI + uv + pytest + `/health`, settings module reading `TIKKO_*`, ruff)
- [x] F04 — Web skeleton (Next.js + vitest + smoke test, eslint, tsconfig, base layout)
- [x] F05 — Mobile skeleton (Expo TS + jest + smoke test, eslint, tsconfig, base navigation)
- [x] F06 — Shared packages (`@tikko/shared-types` with Zod, `@tikko/api-client` with OpenAPI codegen pipeline)

### Walking skeleton: register device → poll → view

- [x] F07 — Device model + `POST /devices` + `GET /devices` (alembic migration, integration tests)
- [x] F08 — pyzk wrapper + `POST /devices/:id/test-connection` (mocked unit tests, real-device manual test)
- [x] F09 — AttendanceLog model + `POST /devices/:id/poll` (pulls via pyzk, dedups) + `GET /devices/:id/attendance`
- [x] F10 — Web `/devices` page (list + add form + test-connection button)
- [x] F11 — Web `/devices/:id/attendance` page (paginated list, manual poll button)

### Auth

- [x] F12 — User model + `POST /auth/register` + `POST /auth/login` + JWT issuance
- [x] F13 — Auth middleware + role guards (`admin`, `manager`, `employee`); apply to existing routes
- [x] F14 — Mobile login flow + auth context + token storage (SecureStore)

### Real-time + ADMS push protocol

- [x] F15 — ADMS push receiver (`POST /iclock/cdata`, `GET /iclock/getrequest`, device registration handshake)
- [x] F16 — WebSocket real-time feed (`/ws/attendance`) broadcasting new punches
- [x] F17 — Mobile real-time feed UI (subscribe + show punches as they arrive)

### Polling + dev ergonomics

- [x] F18 — Background scheduler (per-device poll interval, runs as worker process)
- [x] F19 — Mock device harness (in-process fake pyzk server for tests + local dev without hardware)

### Employee enrollment

- [x] F20 — Employee model + CRUD endpoints + sync to one or many devices
- [ ] F21 — Fingerprint template management + cross-device transfer
- [ ] F22 — Web admin: employee enrollment page (CRUD + which-devices-to-sync)

### Mobile UX + leave

- [ ] F23 — Mobile employee dashboard (own attendance, monthly summary)
- [ ] F24 — Leave request model + endpoints (submit, list-own, list-team, approve/reject)
- [ ] F25 — Mobile manager view (team list, pending approvals)

### Payroll + reports

- [ ] F26 — Shift rules model + per-employee assignment
- [ ] F27 — Payroll calc engine (late, early, OT — pure functions, well-tested)
- [ ] F28 — Report endpoints + CSV/XLSX export
- [ ] F29 — Web admin reports page (filters + export buttons)

### Hardening

- [ ] F30 — TOTP for admin role (enrollment, verification, recovery codes)
- [ ] F31 — Deploy mode config (`TIKKO_DEPLOY_MODE` switches binding, TLS, defaults; env validation at boot)
- [ ] F32 — Docker Compose (LAN) + VPS deploy scripts/systemd units
