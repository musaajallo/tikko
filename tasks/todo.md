# TODO

## Session end (2026-05-14)

F01–F24 complete on `main`, plus a UI polish pass, a login error-UX patch, Alembic adoption, and TopBar consolidation.
- **api 129/129** · **web 16/16** · **shared-types 11/11** · **mobile 10/10** = 166 tests
- `all-features.md` F20 + F21 + F22 + F23 + F24 all closed.
- **Schema management: Alembic.** Two migrations: `8c51c515c891` (initial), `598bccf9f7db` (leave_requests). Live `tikko-dev.db` at head. New environments: `cd apps/api && uv run alembic upgrade head`. New model → just register in `tikko.models.__init__`; `alembic/env.py` picks it up via `import tikko.models`.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **F25** — Mobile manager view (team list + pending approvals UI). Lists `GET /leave-requests?status=pending` for admin/manager users; tap to approve/reject via `PATCH /leave-requests/:id/decision`. May want a web counterpart too (`/leave-requests` admin page) at some point.
- **F26** — Shift rules model + per-employee assignment. Unlocks the late/early/OT bits of F27 payroll calc.
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
