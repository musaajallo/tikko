# TODO

## Session end (2026-05-14)

F01–F20 complete on `main`, plus a UI polish pass. F20-sync ships device-side enrollment.
- **api 75/75** green (49/49 after F19; +16 F20 CRUD; +10 F20-sync)
- `all-features.md` F20 line is closed.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- F21 — Fingerprint template management + cross-device transfer
- F22 — Web admin: employee enrollment page
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
