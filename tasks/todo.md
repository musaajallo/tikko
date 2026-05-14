# TODO

## Session end (2026-05-14)

F01–F31 complete on `main`.
- **api 197/197** · **web 20/20** · **shared-types 11/11** · **mobile 14/14** = 242 tests
- `all-features.md` F20–F31 all ticked. Only F32 (Docker Compose + VPS deploy) remains.
- **Alembic migrations**: 4 total — `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules), `b2d4cc7dbe00` (user_totp).
- **Cloud mode is now enforced at boot**: lifespan calls `Settings.validate_for_deployment()`; misconfigured cloud deploys (default jwt secret, sqlite DB, default localhost CORS) fail fast with a combined error listing every issue.
- **Known migration gotcha**: when autogenerate emits a new FK inside `batch_alter_table` (SQLite path), hand-edit the file to name the constraint — autogen emits `create_foreign_key(None, ...)` and SQLite's batch mode rejects it. Hit once during F26, documented in the done.md entry.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## In progress

- **User profile page** (`/profile`)
  - Backend: new `POST /auth/change-password { current_password, new_password }` (401 on wrong current, 422 too-short new).
  - Frontend: Account card (email/role/linked employee/created), Change password form, Two-factor section (Enable dialog with QR + secret + verify code; Disable dialog with password re-auth).
  - TopBar avatar dropdown gets a Profile link.
  - QR rendered client-side via `qrcode` npm package — small and well-maintained.
- **Settings page** (`/settings`) — second commit, after profile.
  - Backend: `GET /users` (admin) + `PATCH /users/:user_id/role` (admin).
  - Frontend: Users section (list + edit role) + Shift rules section (full CRUD over F26 endpoints). Drop SOON badge in nav.

## Up next — roadmap

- **F32** — Docker Compose (LAN) + VPS deploy scripts/systemd units. Last item on `all-features.md`.

## Optional features

UI gaps in shipped backend features:

- **Settings page** — `/settings` is still a `ComingSoon` placeholder; nav still carries a SOON badge. No spec yet. Candidates for content: user/role management (admin can edit roles), org settings (tz, working week), maybe surface shift rules here too. Decision needed: scope it.
- **User profile** — no `/profile` route; the avatar dropdown only has "Sign out". User can't see/edit their account, change password, or enroll/disable TOTP from the UI. The backend is in place (`/auth/me`, `/auth/totp/*`); this is pure frontend.
- **Web `/leave-requests` admin page** — only the mobile F25 screen exists; managers approving from the browser have no UI today.
- **Web `/employees/:id/templates` page** — no UI for the F21 pull/push backend.
- **Employee-facing leave list on the mobile dashboard** — the dashboard shows attendance KPIs but not the user's own leave requests.

Smaller follow-ups to shipped features:

- **F22-edit** — inline edit employee name + status from the row (PATCH `/employees/:id`).
- **F22-delete-confirm** — confirm dialog before the row "Delete" actually deletes.
- **F30-recovery** — TOTP backup codes (10 single-use codes generated at `/verify`, usable as `totp_code` during login, rotated by re-enrollment).
- **F28-xlsx** — `openpyxl` + `.xlsx` endpoint that mirrors the CSV export.

## Followups (not features)

- Backfill `tasks/done.md` entries for F15–F18 + UI polish (notes only live in commit messages right now).
- Migrate `next lint` → ESLint CLI + flat config when bumping to Next 16.
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`).
- Postgres-dialect path for the attendance dedup insert (currently SQLite-flavoured `ON CONFLICT`).
- Set `TIKKO_JWT_SECRET` properly in prod (F31 now refuses to boot in cloud mode with the default — but no real secret is set yet).
- Refresh-token rotation flow — refresh tokens are issued but never exchanged.
- Mobile suite flake — first jest run after a cold start sometimes fails with an `act(...)` warning on `Animated.View` from `TouchableOpacity` in `login.tsx`. Second run is reliably green.
- TOTP `secret_b32` is stored plaintext — encryption-at-rest needs a KMS / wrapper-key story.

## Blocked

_(none)_
