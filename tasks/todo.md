# TODO

## Session end (2026-05-14)

F01–F23 complete on `main`, plus a UI polish pass and a login error-UX patch.
- **api 108/108** · **web 16/16** · **shared-types 11/11** · **mobile 10/10** = 145 tests
- Mobile flakiness from F22 era didn't reproduce in F23-mobile runs (2/2 clean). Keep an eye on it.
- `all-features.md` F20 + F21 + F22 + F23 closed.
- Dev SQLite: had to manually `ALTER TABLE users ADD COLUMN employee_id` for F23-link. Alembic followup is now load-bearing — next schema change in a fresh dev env will hit the same trap.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **Alembic migrations** — replace `Base.metadata.create_all` (load-bearing followup now; next schema change in a fresh dev env will trip the same ALTER trap we just hit twice).
- **F24** — Leave request model + endpoints (submit, list-own, list-team, approve/reject)
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
