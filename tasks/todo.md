# TODO

## Session end (2026-05-14)

F01–F20 + F22 complete on `main`, plus a UI polish pass. Skipped F21 for now (templates need a join table; revisiting next).
- **api 75/75** · **web 16/16** · **shared-types 11/11** · **mobile 6/6** = 108 tests
- `all-features.md` F20 + F22 lines closed; F21 still open.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- F21 — Fingerprint template management + cross-device transfer (needs a new
  `employee_templates` join table; adds `ZKClient.get_user_template` +
  `save_user_template` + matching fakes; routes for pull + push between devices)
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
