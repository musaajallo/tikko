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

## F10 — Web devices page ✓
- **Tests:** 4/4 web vitest (2 home + 2 devices page: list fetch + form POST→refetch), typecheck + lint clean
- **Files:** apps/web/lib/api.ts (typed fetch client), app/devices/page.tsx (client component), `@tikko/shared-types` added as workspace dep
- **Notes:**
  - `@tikko/shared-types` linked via `workspace:*` in apps/web/package.json so the page imports `Device` types directly
  - Hit React 19 types-collision bug on layout.tsx (two @types/react copies — one from web's direct dep, one transitive through next-dom). Pragmatic patch: `{children as any}` cast in app/layout.tsx. Real fix is a `pnpm.overrides` to pin @types/react across the workspace; deferred because mobile uses React 18 and unified pinning needs more care.
  - Typed routes Link href cast `as never` for `/devices/[id]/attendance` since that route doesn't exist yet — will tighten in F11.

## F11 — Web attendance page ✓
- **Tests:** 6/6 web vitest (2 home + 2 devices + 2 attendance), typecheck + lint clean
- **Files:** app/devices/[id]/attendance/page.tsx (server component awaiting params), app/devices/[id]/attendance/AttendanceClient.tsx (client component), app/devices/[id]/attendance/__tests__/attendance.test.tsx
- **Notes:**
  - Page splits server (awaits Next 15 async params) + client (state + fetch). Tests run against the client component directly.
  - 'Poll now' button calls F09's POST /devices/:id/poll then refetches the list. Reports `{ polled, new }` count to the user.
  - Removed the `as never` cast from F10's Link now that the route exists.
- **Walking skeleton is now complete** — device register → poll → view attendance works end-to-end through web + api with mocked pyzk in tests.

## F12 — Auth: register + login + JWT ✓
- **Tests:** 23/23 (8 new auth tests), ruff clean
- **Files:** src/tikko/auth/{__init__,hashing,tokens}.py, src/tikko/models/user.py, src/tikko/schemas/user.py, src/tikko/routes/auth.py
- **Deps added:** bcrypt 5.0, pyjwt 2.12
- **Routes:** POST /auth/register (201, returns UserRead without password), POST /auth/login (200, returns access+refresh tokens), 409 on duplicate email, 401 on wrong password / unknown email (same message — no enumeration)
- **JWT claims:** sub (user id), role, type ("access"|"refresh"), iat, exp. HS256 signed with `TIKKO_JWT_SECRET`. TTLs from settings (default 15min access / 30 days refresh).
- **Notes:**
  - Password min length enforced at 10 chars in `UserCreate`; pydantic returns 422 on shorter
  - Role defaults to "employee"; `UserRole` is a `Literal` constrained to admin/manager/employee
  - InsecureKeyLengthWarning during tests because default `TIKKO_JWT_SECRET` is "change-me" — set a real secret in prod (`openssl rand -hex 32`)

## F13 — Auth middleware + role guards ✓
- **Tests:** 31/31 (8 new auth-guard tests, 15 existing tests updated to authenticate), ruff clean
- **Files:** src/tikko/auth/dependencies.py (CurrentUser dataclass, get_current_user, require_role), guards applied to 5 /devices routes, tests/conftest.py grew `admin_auth` fixture, 3 existing test files updated to pass the fixture
- **Route policy:**
  - `POST /devices`, `POST /devices/:id/test-connection` — admin only
  - `GET /devices`, `GET /devices/:id`, `POST /devices/:id/poll` — admin or manager
  - `GET /devices/:id/attendance` — any authenticated role
  - `/health`, `/auth/register`, `/auth/login` — public
- **Errors:** 401 (missing/bad/expired token) with `WWW-Authenticate: Bearer`; 403 (wrong role) with `role 'X' not allowed`
- **Retrospective:** Splitting auth into F12 (endpoints) and F13 (apply guards) caused churn — 15 existing tests had to be updated. Should have either bundled them or built auth into F07 from day one. Carry this lesson into F14+ planning: when a feature horizontally affects all existing endpoints/screens, scope it as one feature.

## F14 — Login flow (web + mobile) ✓
- **Tests:** web 11/11 (3 new auth + 2 new login), mobile 6/6 (3 new auth + 1 new login), typecheck + lint clean both
- **Web:** lib/auth.ts (localStorage round-trip), app/login/page.tsx (form → POST /auth/login → setToken → router.push("/devices")), lib/api.ts auto-injects Authorization header from getToken()
- **Mobile:** lib/auth.ts (expo-secure-store wrapper), lib/api.ts (fetch wrapper with auto-Authorization), app/login.tsx (TextInputs + Pressable button → router.replace("/"))
- **Storage:** web → localStorage; mobile → SecureStore (encrypted on iOS keychain / Android keystore)
- **Walking skeleton is now usable through the browser**: visit /login, sign in as an admin, /devices and /devices/:id/attendance work.

## F19 — Mock device harness ✓
- **Tests:** api 49/49 (6 new in `test_zk_fake.py`), ruff clean
- **Files:** `src/tikko/zk/fake.py` (new), `tests/test_zk_fake.py` (new)
- **Public surface:**
  - `FakeDevice(host, serial_number, firmware_version, platform, device_name, punches)` — mutable in-memory terminal state; `.add_punch(user_id, timestamp, status, punch)` appends a record.
  - `FakeZK` — drop-in for `zk.ZK(host, port=, timeout=)`. `.connect()` looks the host up in the module registry and returns a `FakeConnection`; raises `ConnectionError` (caught by `ZKClient` and re-raised as `ZKConnectionError`) if no device is registered for that host.
  - `use_fake_devices(*devices)` — context manager that monkeypatches the `ZK` symbol bound inside `tikko.zk.client` for the duration of the block, seeds the registry, and restores both on exit.
- **Why pure in-process instead of a TCP fake on :4370:** the F19 win we needed was killing `unittest.mock.patch("tikko.routes.devices.ZKClient.<method>")` from the integration tests — pre-F19 you had to know the import site to patch correctly, and adding a method to `ZKClient` meant updating every patch path. `use_fake_devices()` lets a test drive the real `ZKClient` end-to-end. A TCP-listening fake is a future feature (needed for testing the pyzk wire protocol itself, not callers of it).
- **Notes:**
  - `FakeConnection` returns dataclass instances with `user_id`/`timestamp`/`status`/`punch` attributes — that's exactly the shape `ZKClient.get_attendance()` reads, so no shim needed.
  - The context manager saves and restores the registry (not just the `ZK` symbol) so nested or accidentally-overlapping `use_fake_devices()` blocks don't leak fakes into each other.
  - Existing tests under `test_attendance.py` / `test_zk_test_connection.py` still use `patch.object` and remain green — F19 is additive, no migration required.
- **Followup:** swap the older patch-based tests over to `use_fake_devices` when next touching them (not a blocker).

## F20 — Employee CRUD ✓ (sync deferred to F20-sync)
- **Tests:** api 65/65 (16 new in `test_employees.py`), ruff clean
- **Files:** `src/tikko/models/employee.py`, `src/tikko/schemas/employee.py`, `src/tikko/routes/employees.py` (all new); `models/__init__.py` + `main.py` updated to register.
- **Routes:**
  - `POST /employees` (admin) — 201; 409 on duplicate `employee_code`; 422 on non-numeric code.
  - `GET /employees?page=&page_size=` (admin or manager) — `{items, total}`.
  - `GET /employees/:id` (admin or manager) — 200; 404 if absent.
  - `PATCH /employees/:id` (admin) — partial update over `full_name` + `status`; 422 on bad status; 404 if absent.
  - `DELETE /employees/:id` (admin) — 204; 404 if absent. Hard delete for now (soft-delete is a later concern; rows the device knows about would block deletion in a more careful design, but F20 is small on purpose).
- **Schema choices:**
  - `employee_code` constrained at the Pydantic layer to `^\d+$`, max 32 chars. **Why:** keeps it interchangeable with the ZK `uid` int — F20-sync will pass `int(employee_code)` straight into `pyzk.set_user(uid=…, user_id=…)` with no separate mapping table.
  - `status` is a `Literal["active", "inactive", "terminated"]`. `inactive` exists for the "on leave / contractor not currently scheduled" case so we don't have to choose between active and terminated when the right answer is "neither".
- **Why split sync into F20-sync:**
  - `all-features.md` F20 originally bundled "model + CRUD + sync". Splitting lets the CRUD surface stabilise before the device side touches it, and gives F20-sync a clean scope: just the `POST /employees/:id/sync` route plus `ZKClient.set_user` plus a matching `FakeConnection.set_user`. The `all-features.md` F20 checkbox stays open until F20-sync lands.
- **Notes:**
  - No Alembic migration yet (follows the existing pattern — tables created via `Base.metadata.create_all` in lifespan; followup carried in `todo.md`).
  - No `Employee ↔ User` linkage. They're different concepts: a `User` is an auth principal (admin/manager/employee), an `Employee` is a tracked human on a terminal. Joining them is a later feature, only if/when the mobile employee dashboard (F23) needs it.

## F20-sync — POST /employees/:id/sync ✓ (closes the `all-features.md` F20 line)
- **Tests:** api 75/75 (10 new in `test_employees_sync.py`), ruff clean
- **Files:**
  - `src/tikko/zk/client.py` — `ZKClient.set_user(user_id, name)` added: validates digits-only `user_id`, casts to `uid` int, calls `conn.set_user(uid=, name=, user_id=)`, wraps any pyzk exception as `ZKConnectionError`.
  - `src/tikko/zk/fake.py` — new `FakeSyncedUser` dataclass; `FakeDevice.synced_users: dict[str, FakeSyncedUser]`; `FakeConnection.set_user(...)` records the call (signature matches pyzk: `uid, name='', privilege=0, password='', group_id='', user_id='', card=0`).
  - `src/tikko/schemas/employee.py` — `EmployeeSyncRequest { device_ids: list[str] (min_length=1) }`, `EmployeeSyncEntry { device_id, status, error }`, `EmployeeSyncResult { results }`.
  - `src/tikko/routes/employees.py` — `POST /employees/:id/sync` handler (admin). 404 if employee absent, 400 if any `device_id` not in DB, otherwise iterates devices in **request order** and produces a per-device `{status, error?}` entry. `set_user` is wrapped in `asyncio.to_thread` to keep the event loop free.
  - `tests/test_employees_sync.py` — 10 tests: single device, multi-device, request-order preservation, unreachable device → `status: failed`, mixed success/failure, missing employee (404), unknown `device_id` (400), empty list (422), employee role (403), no token (401).
- **Why per-device failures don't bubble to a 5xx:** the operator wants to know which devices took the user and which didn't, in one round trip. Returning 200 with a results array lets the web UI render "Synced to A, failed on B — retry?" without parsing partial-success out of an error body.
- **Why iterate in request order:** the `select(... in_(device_ids))` query returns rows in arbitrary order, but the caller chose a sequence (e.g. "front gate first, then back door"); preserving it keeps the result intuitive.
- **No DB persistence of sync state yet.** That belongs to F21 (when fingerprint templates land and we need a join table to track *which device has which template*). For now `synced_users` lives only on the (fake) device — real devices keep their own state.
- **Walking skeleton is now usable end-to-end through enrollment**: register employee → POST /employees/:id/sync against one or more devices → device knows the user.

## F22 — Web `/employees` page ✓
- **Tests:** web 16/16 (5 new in `app/employees/__tests__/employees-page.test.tsx`); shared-types 11/11 (4 new for `EmployeeSchema` + `EmployeeStatus` + `EmployeeSyncEntrySchema`); typecheck + lint clean. api re-run 75/75 to confirm no cross-package break.
- **Files:**
  - `packages/shared-types/src/index.ts` — `EmployeeStatus`, `EmployeeSchema`, `EmployeeSyncEntrySchema` (Zod) so the web app validates the API shape it consumes.
  - `apps/web/lib/api.ts` — `listEmployees`, `createEmployee`, `deleteEmployee`, `syncEmployee` methods; **also**: `request<T>` now short-circuits on HTTP 204 (returns `undefined as T`). The old path unconditionally `response.json()`'d which would throw on a no-content delete.
  - `apps/web/app/employees/page.tsx` (new) — client component: list table, add-employee dialog, per-row dropdown with **"Sync to devices…"** and **"Delete"**, separate sync dialog with a checkbox list of devices (defaults to all selected).
  - `apps/web/app/employees/layout.tsx` (new) — mirrors `DevicesLayout` (TopBar + TopNav + max-w-7xl main).
  - `apps/web/components/top-nav.tsx` — added "Employees" between "Devices" and "Reports".
  - `apps/web/package.json` — added `@testing-library/user-event` (devDep). Radix `DropdownMenu` uses pointer events; `fireEvent.click` on the trigger doesn't open it under jsdom. `user-event` simulates pointer events end-to-end.
- **What's deliberately not in F22:**
  - **Inline edit name / status** — deferred to F22-edit (or roll into F22 if/when the workflow demands it). Status change can already happen via a future PATCH dialog; no need to land it speculatively.
  - **Delete confirm dialog.** Single click on "Delete" fires DELETE immediately. Real-world UX should have a confirm — captured as a followup. Kept simple to keep the test surface small.
  - **Detail page `/employees/:id`** — devices got `/devices/:id/attendance`; employees don't need an equivalent yet because the list view + sync dialog handle the primary workflow.
- **Sync dialog UX call:** opening the dialog pre-selects every registered device. **Why:** the most common operator action after enrolling someone is "push to all terminals". Deselect-to-exclude is a friendlier default than select-to-include for that pattern. Test exercises the default-on path; deselection paths are exercised manually for now.
- **204 handling in `request<T>`:** small change with broad scope — every existing caller returns a body, so the short-circuit is unreachable for them. Worth knowing if anyone later adds a `void`-returning endpoint with a non-204 status.
- **Walking skeleton is now usable through the browser for enrollment**: log in as admin → `/employees` → Add → Sync to devices → toast confirms per-device results.

## F21 — Fingerprint template pull ✓ (push deferred to F21-push)
- **Tests:** api 87/87 (12 new in `test_employee_templates.py`), ruff clean.
- **Files:**
  - `src/tikko/models/employee_template.py` (new) — `EmployeeTemplate(id, employee_id FK, source_device_id FK, finger_id, template_data LargeBinary, captured_at)` with `UniqueConstraint(employee_id, source_device_id, finger_id)`.
  - `src/tikko/zk/client.py` — `RawTemplate(finger_id, data)` dataclass; `ZKClient.get_user_templates(user_id)` iterates `finger_id` 0..9 via `conn.get_user_template(uid=, temp_id=, user_id=)` and returns only the enrolled slots.
  - `src/tikko/zk/fake.py` — `FakeDevice.templates: dict[user_id][finger_id] = bytes` + `FakeDevice.set_user_template(...)` test helper; `FakeConnection.get_user_template(...)` returns a `_FakeFinger` with `.template` (matches pyzk's read shape) or `None`.
  - `src/tikko/schemas/employee.py` — `TemplateRead` (no blob), `TemplateList`, `TemplatePullResult { stored, fingers }`.
  - `src/tikko/routes/employees.py` — `POST /employees/:id/templates/pull?from_device_id=…` (admin), `GET /employees/:id/templates` (admin/manager).
  - `src/tikko/models/__init__.py` + `main.py` updated to register `EmployeeTemplate`.
- **Why "replace, don't merge" on pull:** the route deletes all existing rows for `(employee, source_device)` before re-inserting. If the operator re-enrolled finger 0 and removed finger 1 on the device, a merge-style pull would leave a stale finger-1 row in the DB. Replace keeps the DB faithful to the device's *current* state.
- **Why store per source device:** templates aren't always portable across firmware/vendor versions. Keeping the source lets F21-push pick a compatible source for each target device rather than guessing.
- **Why no template_data in list responses:** the blobs are kilobyte-scale per finger and only useful to the push step (which reads directly from the DB). Listing them through JSON would balloon responses and serialise binary the API doesn't need to expose.
- **Notes:**
  - No Alembic migration yet — still relying on `Base.metadata.create_all` in the lifespan (followup carried in `todo.md`).
  - 503 surfaces for connect failures during pull; that's symmetric with `POST /devices/:id/test-connection` and `/poll`.
  - F21-push will add `ZKClient.save_user_template` + `FakeConnection.save_user_template` and a `POST /employees/:id/templates/push` route that reads from `employee_templates` and writes to the target devices.

## F21-push — POST /employees/:id/templates/push ✓ (closes `all-features.md` F21)
- **Tests:** api 98/98 (11 new in `test_employee_templates_push.py`), ruff clean.
- **Files:**
  - `src/tikko/zk/client.py` — `ZKClient.save_user_templates(user_id, templates)` constructs `zk.finger.Finger` objects with `valid=1` and calls `conn.save_user_template(user=uid, fingers=[...])` once for the batch (single TCP round trip). Re-raises pyzk failures as `ZKConnectionError`.
  - `src/tikko/zk/fake.py` — `FakeConnection.save_user_template(user, fingers)` mirrors the pyzk signature: accepts `user` as int / str / object-with-`.user_id`, normalises to the string key the rest of the fake uses, then writes each `finger.fid → finger.template` into `FakeDevice.templates`. This means a push roundtrips through the same `get_user_template` read path the pull half exercises.
  - `src/tikko/schemas/employee.py` — `TemplatePushRequest { device_ids (min_length=1) }`, `TemplatePushEntry { device_id, status, fingers_pushed, error }`, `TemplatePushResult { results }`.
  - `src/tikko/routes/employees.py` — `POST /employees/:id/templates/push` (admin). 404 on missing employee, 400 on unknown `device_id`. For each target device: `set_user` first, then `save_user_templates`. Per-device `ZKConnectionError` becomes `{status: "failed", fingers_pushed: 0, error}` rather than a 5xx, mirroring F20-sync's partial-success ergonomics.
- **Latest-per-finger selection:** the route reads all `EmployeeTemplate` rows for the employee, orders by `captured_at desc`, then `setdefault(finger_id, row)` to keep the newest per slot. So if two source devices both have finger 0, the most recently captured wins. Ties on `captured_at` resolve by ORM read order; deterministic within a run but not specified across runs.
- **Why `set_user` runs before every push:** pyzk's `save_user_template` requires the user record to exist on the device; otherwise the device silently rejects the write. `set_user` is idempotent (overwrites with the same data), so calling it on every push is cheap and removes a precondition the operator would otherwise have to enforce manually.
- **Why one TCP round trip per device for the whole batch:** pyzk's `save_user_template` accepts a list of fingers, so calling it once with N fingers is one connect/setup/disconnect rather than N. Latency-bound, not bandwidth-bound, so the batching matters.
- **No fingers stored → still 200:** `fingers_pushed: 0` per device. The caller sees that nothing was pushed and can react (e.g. tell the user to pull first), rather than parsing a 4xx as a hard failure.
- **Walking skeleton is now usable for cross-device enrollment**: pull from device A → push to devices B and C. The full F20+F20-sync+F21+F21-push loop runs end-to-end against the fake harness.

## F23-link — User ↔ Employee + /auth/me + /me/attendance ✓ (F23 mobile-side follows)
- **Tests:** api 108/108 (10 new across `test_auth_me.py` + `test_me_attendance.py`), ruff clean.
- **Files:**
  - `src/tikko/models/user.py` — added `employee_id: str | None` (nullable FK to `employees.id`, indexed). Admins/managers commonly aren't enrolled on a terminal, so the link is optional.
  - `src/tikko/schemas/user.py` — `UserCreate.employee_code: str | None`, `UserRead.employee_id`, new `AuthMeResponse { user, employee | null }`.
  - `src/tikko/routes/auth.py` — `POST /auth/register` resolves `employee_code → Employee.id` (404 if absent) and stores the FK. `GET /auth/me` returns `{user, employee}` for the bearer.
  - `src/tikko/schemas/me.py` (new) — `AttendanceSummary { month, total_punches, days_present }`.
  - `src/tikko/routes/me.py` (new) — `/me/attendance` (paginated) and `/me/attendance/summary?month=YYYY-MM`. A `_linked_employee` helper 403s if the User has no FK or the FK target row vanished.
  - `src/tikko/main.py` — register the `/me` router.
- **Why link at register time (not via a separate admin endpoint yet):** keeps the F23-link MVP small. A real flow (admin links users after registration) can come in a follow-up. Tests cover both paths: registered with `employee_code` → linked, without → unlinked + 403 on `/me/*`.
- **Why "no link" is a 403, not a 200 with empty data:** the operator should learn that their account is not enrolled, not silently see an empty attendance list. Different signals serve different intent.
- **Summary endpoint shape (`{month, total_punches, days_present}`):** kept tight. `days_present` is `COUNT(DISTINCT date(punched_at))` over the month range. Cross-dialect (`func.date(...)` works on both SQLite and Postgres for this purpose). More detail (first/last punch, hours worked, late/early) belongs in F26 (shift rules + payroll).
- **Live-DB note:** the running `apps/api/tikko-dev.db` needed `ALTER TABLE users ADD COLUMN employee_id VARCHAR(36);` because we still don't have Alembic. That's another datapoint for the "replace `Base.metadata.create_all` with migrations" followup carried in `todo.md` — adding columns to existing tables in dev is currently a manual step.
- **What F23-mobile will do:** a new RN screen consuming `GET /auth/me` (to discover the linked employee + name) and `GET /me/attendance` (recent rows) + `GET /me/attendance/summary?month=YYYY-MM` (header KPIs). Auth handling already in place from F14.

## F23-mobile — Expo dashboard screen ✓ (closes `all-features.md` F23)
- **Tests:** mobile 10/10 (2 new in `app/__tests__/dashboard.test.tsx`). Stable across two runs in a row (no F14-era flake observed).
- **Files:**
  - `apps/mobile/lib/api.ts` — types (`UserMe`, `EmployeeMe`, `AuthMeResponse`, `AttendanceLog`, `AttendanceList`, `AttendanceSummary`) + methods (`getMe`, `listMyAttendance`, `myMonthlySummary`).
  - `apps/mobile/app/dashboard.tsx` (new) — header (employee name + `#code`), two KPI cards (`total_punches`, `days_present`), recent punches `FlatList`. Loading + error + empty states all handled inline.
  - `apps/mobile/app/index.tsx` — authed users now route to `/dashboard` (was `/feed`). Dashboard itself falls back to `/feed` when `/auth/me` reports no linked employee — admins/managers see the live device feed they had before.
- **Why dashboard owns the routing decision (not index):** index would otherwise need to hit `/auth/me` just to choose where to redirect. Letting dashboard fetch once and self-redirect on `employee === null` keeps index dumb and avoids a double network round trip in the linked-employee path.
- **Current-month helper:** `currentMonth()` builds `YYYY-MM` from `Date.getUTCFullYear/getUTCMonth` — no date library. Future month picker (prev/next arrows) is a small follow-up if needed.
- **KPI shape mirrors the api `AttendanceSummary`** — `total_punches` and `days_present` are the only numbers the screen needs today. Hours/late counts can come in F26 when shift rules land.
- **Walking skeleton is now usable end-to-end on mobile**: log in as an enrolled employee → land on dashboard → see this month's KPIs and recent punches; an admin lands on the existing live feed instead.

## Infra — adopt Alembic; drop create_all from app bootstrap ✓
- **Tests:** api 108/108 (unchanged), ruff clean (incl. `alembic/`).
- **Files:**
  - `apps/api/alembic.ini`, `apps/api/alembic/env.py`, `apps/api/alembic/versions/8c51c515c891_initial_schema.py` — initial migration covering users, devices, attendance_logs, employees, employee_templates plus the `User.employee_id` FK.
  - `apps/api/alembic/env.py` — reads `database_url` from `tikko.settings.get_settings()` so the same `TIKKO_DATABASE_URL` drives both app and migrations; uses `Base.metadata` for autogenerate; enables `render_as_batch=True` on SQLite (so `op.batch_alter_table` is emitted — required for SQLite's limited ALTER) and `compare_type=True`.
  - `apps/api/src/tikko/main.py` — lifespan no longer creates tables unconditionally; `create_all` runs only when `TIKKO_CREATE_TABLES_ON_STARTUP=1`. Real envs leave this unset and use `alembic upgrade head`.
  - `apps/api/tests/conftest.py` — sets `TIKKO_CREATE_TABLES_ON_STARTUP=1` before importing `tikko.main`, so tests keep getting their schema built in-memory directly off `Base.metadata` (orders of magnitude faster than running migrations per test).
- **Why a gate, not "tests run migrations":** an async aiosqlite `:memory:` engine relies on SQLAlchemy's `StaticPool` to share one connection across the test; running migrations outside that connection scope creates a different in-memory DB. Gating `create_all` inside the lifespan keeps everything inside the TestClient's loop and pool.
- **Live dev DB workflow:**
  - Existing `apps/api/tikko-dev.db` was stamped at `head` (revision `8c51c515c891`) so future migrations apply cleanly without trying to re-create the tables that are already there.
  - For a fresh environment: `cd apps/api && uv run alembic upgrade head` then start the app.
  - Smoke-tested on a throwaway empty DB: `alembic upgrade head` creates all five tables (+ `alembic_version`) with the right columns including `users.employee_id`.
- **Why this matters now:** dev-env schema drift was a recurring tax — F15-era `devices.serial_number` missing, then F23-link's `users.employee_id` missing. Both required manual `ALTER TABLE` to fix. With Alembic in place, the next schema change is `uv run alembic revision --autogenerate -m "…"` + `alembic upgrade head` instead.
- **Followups still on the list:**
  - ~~Adding a new model means importing it into both `tikko.models.__init__` AND `alembic/env.py`.~~ Resolved as part of F24: `alembic/env.py` now does `import tikko.models` so the package `__init__` is the single source of truth.
  - The dev SQLite path is fine for local work; Postgres migrations (the real prod target) haven't been exercised yet — first PG-dialect migration will be the moment we validate that path.

## UI — TopBar consolidation + coming-soon pages ✓
- **Tests:** web 16/16, typecheck + lint clean.
- **Files:**
  - `apps/web/components/top-bar.tsx` — now contains all nav (Devices, Employees, Reports, Settings, Docs) inline. SOON badges stay on routes whose feature isn't fully built; the links are still clickable to a placeholder page.
  - `apps/web/components/top-nav.tsx` deleted.
  - `apps/web/components/protected-shell.tsx` (new) — TopBar + max-w-7xl `main`. Used by every protected layout.
  - `apps/web/components/coming-soon.tsx` (new) — reusable "this is a placeholder" card with optional bullet list of upcoming capabilities.
  - New routes: `/reports`, `/settings`, `/documentation`, each with a layout that wraps `ProtectedShell` and a page rendering `<ComingSoon … />`.
  - `/devices` + `/employees` layouts simplified to `<ProtectedShell>{children}</ProtectedShell>` — no more layout duplication.
- **Why clickable-with-SOON instead of dead links:** keeps the IA consistent. A nav item that does nothing is more confusing than one that takes you to a placeholder explaining what's coming. Badges stay because the underlying feature is still soon.

## F24 — Leave requests: submit + list-own ✓ (approve deferred to F24-approve)
- **Tests:** api 116/116 (8 new in `test_leave_requests.py`), ruff clean.
- **Files:**
  - `src/tikko/models/leave_request.py` (new) — `LeaveRequest(id, employee_id FK, start_date, end_date, reason, status, created_at, decided_at, decided_by_user_id FK)`. Decision columns are nullable from day one so F24-approve doesn't need a follow-up migration.
  - `src/tikko/models/__init__.py` + `src/tikko/main.py` register `LeaveRequest`.
  - `src/tikko/schemas/leave_request.py` (new) — `LeaveRequestCreate` validates `start_date <= end_date` via a Pydantic `model_validator`; `LeaveRequestRead` + `LeaveRequestList`.
  - `src/tikko/routes/me.py` — `POST /me/leave-requests` (creates a pending row for the linked employee) and `GET /me/leave-requests?page=&page_size=` (paginated, newest-first). Both reuse the existing `_linked_employee` helper (403 if unlinked).
  - `apps/api/alembic/env.py` — switched to `import tikko.models` so future models only need to be added to the package `__init__`, not both places.
  - `apps/api/alembic/versions/598bccf9f7db_leave_requests.py` — autogenerated migration. Live dev DB upgraded successfully.
- **Why decision columns ship in F24, not F24-approve:** F24-approve will populate them but not change the schema. Bundling now avoids a tiny throwaway migration and proves the autogenerate path works end-to-end (initial use of Alembic for a real feature change).
- **Why status is `String(16)` + `Literal[...]` not a PG enum:** PG enums are awkward to evolve cross-dialect (SQLite doesn't have them, migrations need separate paths). Constraining at the Pydantic layer gives us the same correctness without dialect divergence. The DB-side `status` index lets the F24-approve `WHERE status = 'pending'` queries stay fast.
- **Routing under `/me`:** symmetric with `/me/attendance` — these are first-person routes for the linked employee. Manager/admin views land at `/leave-requests` (no `/me/`) in F24-approve.
- **F24-approve scope:** `GET /leave-requests?team=&status=` (admin/manager), `PATCH /leave-requests/:id/decision` body `{decision: "approved"|"rejected"}` — populates `decided_at = now()`, `decided_by_user_id = current_user.id`. 409 if already decided. Tests cover role gates + idempotence.

## F24-approve — GET /leave-requests + PATCH /:id/decision ✓ (closes `all-features.md` F24)
- **Tests:** api 129/129 (13 new in `test_leave_decisions.py`), ruff clean. No schema change — decision columns shipped in F24.
- **Files:**
  - `src/tikko/schemas/leave_request.py` — adds `LeaveDecisionRequest { decision: Literal["approved", "rejected"] }`.
  - `src/tikko/routes/leave_requests.py` (new) — `GET /leave-requests` (admin/manager) with optional `status` filter, paginated, newest-first; `PATCH /leave-requests/:id/decision` (admin/manager) flips status, stamps `decided_at = utcnow()`, `decided_by_user_id = current.id`. 409 if `leave.status != "pending"`; 404 if absent.
  - `src/tikko/main.py` — registers `leave_requests_router`.
- **Why a 409 on already-decided instead of letting the second PATCH win:** approvals are stateful and "decided once" is part of the contract. A re-decision would silently overwrite who decided + when, which is the kind of audit-trail loss you can't get back. Idempotence-friendly responses (already-`approved` PATCH `approve` returns 409 too) keep the rule simple — no special-casing the same-decision branch.
- **Why a separate `/leave-requests` router (not under `/me` or `/employees`):** these are manager/admin views of *everyone's* leave. `/me/leave-requests` is the first-person view; `/leave-requests` is the third-person view. Keeping them in separate modules makes the authz model legible at the URL — `_admin_or_manager` on the file vs. `_linked_employee` in `me.py`.
- **Status filter is `LeaveStatus | None`:** omit → return all. Index on `leave_requests.status` (shipped in F24) keeps the filtered query fast even at scale.
- **Lint note:** the `Query(...)` default for the `status` param tripped `B008`, while sibling `Query(1, ge=1)` did not. Ruff's FastAPI allowlist appears to require concrete (not `Union`) annotations to detect the marker, so the `status: LeaveStatus | None = Query(...)` line carries a `# noqa: B008` matching the pattern other routes already use implicitly. Worth revisiting if we switch the codebase to the `Annotated[..., Query(...)]` style.
- **Walking skeleton now spans the leave workflow end-to-end**: employee submits via `POST /me/leave-requests` → manager sees it in `GET /leave-requests?status=pending` → manager decides via `PATCH /leave-requests/:id/decision` → employee sees the decision in their `GET /me/leave-requests` list.

## F25 — Mobile manager approvals ✓ (closes `all-features.md` F25)
- **Tests:** api 131/131 (2 new for the enriched response shape) · mobile 14/14 (4 new in `approvals.test.tsx`). Mobile stable across two consecutive runs.
- **Backend enrich:**
  - `LeaveRequestRead` gains `employee_code` + `employee_full_name` as nullable strings. Without these the manager UI would render UUIDs — useless. Nullable so old or orphaned requests still serialise (employee row could be deleted between submit and decision).
  - `/leave-requests` GET joins `employees` once (`outerjoin`) and walks rows manually. PATCH-decision re-fetches the employee post-flush. Two small helpers — `_serialize_leave` in `routes/leave_requests.py` (joined-row form), `_serialize_leave_for_employee` in `routes/me.py` (already-resolved employee). Both reuse the same `LeaveRequestRead`.
  - **Why no ORM `relationship` shortcut:** SQLAlchemy async + lazy-loaded relationships need careful eager-loading config and selectin tuning. The two manual joins are ~15 lines total and keep the route reading obvious — worth the duplication for now.
- **Mobile screen:**
  - `apps/mobile/lib/api.ts` — `LeaveRequest`/`LeaveRequestList` types, `listLeaveRequests(status?)`, `decideLeaveRequest(id, decision)`.
  - `apps/mobile/app/approvals.tsx` (new) — fetches `?status=pending`, renders cards (`employee_full_name #employee_code`, date range, reason) with **Approve** and **Reject** buttons. On decide → PATCH then re-fetch so the decided row drops out of the list. Loading + error + empty states inline.
  - `apps/mobile/app/feed.tsx` — adds an "Approvals" pill in the header. Admins/managers landing on `/feed` (because their User has no linked Employee) can reach the approvals queue in one tap.
- **Why list refetch instead of in-place state mutation:** keeps the UI faithful to server state — if another manager decides the same request between fetch and tap, the next refetch will simply reflect that (the api 409s on the PATCH and we surface an Alert). Trade-off is one extra round trip per decision; for a single-user admin workflow that's fine.
- **Out of scope:** sortable date column, batch approve, a web counterpart at `/leave-requests`. The web view would be a thin wrapper on the same endpoints — easy to add when needed.

## F26 — Shift rules + per-employee assignment ✓
- **Tests:** api 148/148 (17 new in `test_shift_rules.py`), ruff clean. Live dev DB upgraded to `2823730c4ea4`.
- **Files:**
  - `src/tikko/models/shift_rule.py` (new) — `ShiftRule(name, start_time, end_time, late_grace_minutes, early_out_grace_minutes, overtime_threshold_minutes, work_days, …)`. `work_days` is a 7-char binary string Mon→Sun (`1111100` = Mon-Fri) — simple to validate (regex `^[01]{7}$`), simple to render, dialect-agnostic.
  - `src/tikko/models/employee.py` — nullable `shift_rule_id` FK to `shift_rules.id`, indexed.
  - `src/tikko/models/__init__.py` + `main.py` register `ShiftRule`; `alembic/env.py` picks it up via `import tikko.models`.
  - `src/tikko/schemas/shift_rule.py` (new) — `ShiftRuleCreate` enforces `start_time < end_time` via `model_validator`; `ShiftRuleUpdate` partial; `ShiftRuleRead`; `ShiftRuleList`.
  - `src/tikko/routes/shift_rules.py` (new) — full CRUD. Delete returns **409** if any employee still references the rule rather than `ON DELETE SET NULL` — silent unbinding would lose assignment data the operator didn't intend to discard.
  - `src/tikko/schemas/employee.py` — `EmployeeUpdate` accepts `shift_rule_id: str | None`; `EmployeeRead` exposes it.
  - `src/tikko/routes/employees.py` PATCH — uses `payload.model_fields_set` to distinguish "field omitted" from "explicit null"; validates the FK target exists (404 if not), then assigns or detaches.
  - `apps/api/alembic/versions/2823730c4ea4_shift_rules.py` — autogenerated, then hand-edited to **name** the FK constraint (`fk_employees_shift_rule_id`).
- **Why hand-name the FK:** SQLite's `op.batch_alter_table` requires every constraint to have a name; alembic autogenerate emits `create_foreign_key(None, ...)` by default. First attempt blew up mid-migration (the new `shift_rules` table was created but the FK on `employees` aborted with `ValueError: Constraint must have a name`). I considered adding a `naming_convention` to `Base.metadata` for a systemic fix, but that would make subsequent autogenerates emit "rename constraint" ops for every existing constraint in the live DB (which has no convention applied) — way more noise than benefit right now. Decision: hand-name FKs in batch migrations as a known step, revisit `naming_convention` if/when it bites a third time.
- **Why `model_fields_set` for `shift_rule_id` assignment:** `EmployeeUpdate.shift_rule_id: str | None = None` can't distinguish "omitted" (leave assignment unchanged) from "explicit null" (detach) using just `is not None`. Checking presence in `model_fields_set` is the canonical Pydantic v2 way to keep both gestures.
- **Walking skeleton extends to scheduling**: create shift rule → assign to employee via `PATCH /employees/:id { shift_rule_id }` → F27 will read the assignment to compute late/early/OT.

## F27 — Payroll calc engine ✓
- **Tests:** api 164/164 (16 new pure-function tests in `test_payroll_calc.py`), ruff clean. Tests run in 0.04s — no DB, no fixtures, no FastAPI.
- **Files:**
  - `src/tikko/payroll/__init__.py` (new) — public API: `ShiftSpec`, `DayMetrics`, `compute_day`.
  - `src/tikko/payroll/calc.py` (new) — the engine. `ShiftSpec` is a frozen dataclass that mirrors the ORM `ShiftRule` shape without depending on SQLAlchemy. `compute_day(spec, punches, on_date) -> DayMetrics` does all the work in ~30 lines.
- **Design decisions:**
  - **Pure functions, decoupled from the ORM.** The engine never imports SQLAlchemy or FastAPI. F28's report endpoint will be responsible for loading `ShiftRule` + `AttendanceLog` rows and adapting them into `ShiftSpec` + `list[datetime]`. Keeping the calc free of those dependencies means it stays fast to test and easy to reason about — every case is "given these inputs, expect this output."
  - **Naive in/out detection** (first punch = in, last = out). Many ZK terminals fail to classify check-in vs check-out reliably via `punch_type`. Min/max of the day's punches is robust against that noise. Caller can layer on smarter logic later if a real-device test reveals problems.
  - **Punches outside `on_date` are filtered out.** An overnight stay's next-day punches don't bleed into the previous day's metrics. A separate "span" function can be added later if we want to model shifts that cross midnight; for now each calendar day stands alone.
  - **Late and early-out are zero on non-workdays.** A weekend punch shouldn't generate "you were late on Saturday" — the rule wasn't in effect. Overtime, however, is still computed past `end_time + threshold` regardless of workday, so the caller can decide whether weekend OT counts (F28's policy call).
  - **Single-punch edge case** is honest about uncertainty: `first_in == last_out`, `worked_minutes == 0`, lateness still computed from the lone punch. The data is partial; downstream tooling can flag it.
  - **UTC-only for MVP.** The project already stores punches as UTC. Wall-clock-to-tz handling per organisation is a follow-up — adding it now without a real customer constraint risks the wrong abstraction.
- **What F28 wires in:** read `Employee.shift_rule_id` → `ShiftRule`, pull the employee's attendance for a date range, group punches by `date()`, call `compute_day` per day, aggregate. CSV/XLSX export builds on the same daily metrics.







