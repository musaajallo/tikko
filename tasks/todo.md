# TODO

## Session end (2026-05-14)

F01–F28 complete on `main` (F28 = JSON + CSV; XLSX deferred). Plus the usual: UI polish, login error UX, Alembic adoption, TopBar consolidation.
- **api 178/178** · **web 16/16** · **shared-types 11/11** · **mobile 14/14** = 219 tests
- `all-features.md` F20 + F21 + F22 + F23 + F24 + F25 + F26 + F27 + F28 all closed (F28 ticked with a note that XLSX is deferred).
- **Schema management: Alembic.** Three migrations: `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules). Live `tikko-dev.db` at head. New environments: `cd apps/api && uv run alembic upgrade head`. New model → register in `tikko.models.__init__`; `alembic/env.py` picks it up via `import tikko.models`.
- **Known migration gotcha**: when autogenerate emits a new FK inside `batch_alter_table` (SQLite path), hand-edit the file to name the constraint — autogen emits `create_foreign_key(None, ...)` and SQLite's batch mode rejects it. Hit once during F26, documented in the done.md entry.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **F29** — Web admin reports page (filters + export buttons). Consumes F28: employee + month filters, table rendering of daily metrics, "Download CSV" button.
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
