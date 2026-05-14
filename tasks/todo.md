# TODO

## Session end (2026-05-14)

F01–F30 complete on `main`. F28 shipped JSON+CSV (XLSX deferred); F30 shipped enroll+verify+admin-login (recovery codes deferred to F30-recovery).
- **api 190/190** · **web 20/20** · **shared-types 11/11** · **mobile 14/14** = 235 tests
- `all-features.md` F20–F30 all ticked.
- **Alembic migrations**: 4 total — `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules), `b2d4cc7dbe00` (user_totp).
- **Schema management: Alembic.** Three migrations: `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules). Live `tikko-dev.db` at head. New environments: `cd apps/api && uv run alembic upgrade head`. New model → register in `tikko.models.__init__`; `alembic/env.py` picks it up via `import tikko.models`.
- **Known migration gotcha**: when autogenerate emits a new FK inside `batch_alter_table` (SQLite path), hand-edit the file to name the constraint — autogen emits `create_foreign_key(None, ...)` and SQLite's batch mode rejects it. Hit once during F26, documented in the done.md entry.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **F31** — Deploy mode config (`TIKKO_DEPLOY_MODE=lan|cloud` drives bindings/TLS/defaults; env validation at boot). Last item on the all-features hardening track besides F32.
- **F32** — Docker Compose (LAN) + VPS deploy scripts/systemd units.
- **F30-recovery** (optional) — 10 single-use backup codes generated at enrollment; usable as `totp_code` during login; rotated by re-enrollment.
- **F28-xlsx** (optional) — `openpyxl` + `.xlsx` endpoint.

- **F28-xlsx** (optional) — adds `openpyxl` + an `.xlsx` endpoint. Skip until someone asks.
- **F30+** — TOTP for admin, deploy-mode env validation, docker compose. Hardening track.
- Carryover gaps: `/leave-requests` web page (mobile-only today), employee-facing leave list on mobile dashboard.
- Web counterpart for approvals — `/leave-requests` admin page (thin wrapper on the same endpoints; the mobile F25 screen is the only UI today).
- F22-edit (optional) — inline edit name + status on the row (PATCH `/employees/:id`)
- F22-delete-confirm (optional) — guard the row "Delete" with a confirm dialog
- Web UI for templates pull/push — there's no `/employees/:id/templates` page yet
- F22-edit (optional) — inline edit name + status on the row (PATCH `/employees/:id`)
- F22-delete-confirm (optional) — guard the row "Delete" with a confirm dialog
- F23+ — see `tasks/all-features.md` (mobile dashboard, leave, payroll, reports, hardening)

## Followups carried forward

- Backfill `tasks/done.md` entries for F15–F18 + UI polish (notes only live in commit messages right now)
- Migrate `next lint` → eslint CLI + flat config when bumping to Next 16
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`)
- Replace `Base.metadata.create_all` with Alembic migrations before prod
- Postgres-dialect path for the attendance dedup insert
- Set `TIKKO_JWT_SECRET` properly in prod (currently default `change-me` triggers InsecureKeyLengthWarning)
- Refresh-token rotation flow (refresh tokens are stored but never exchanged yet — access tokens just expire)

## Blocked

_(none)_
