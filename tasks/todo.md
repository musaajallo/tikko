# TODO

## Session end (2026-05-14)

F01–F19 complete on `main`, plus a UI polish pass and **F20 employee CRUD** (sync deferred).
- **api 65/65** green (49/49 after F19; +16 from F20 CRUD)
- `all-features.md` F20 stays open until F20-sync lands.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **F20-sync** — `POST /employees/:id/sync` + `ZKClient.set_user` + `FakeConnection.set_user`
  (drives the F19 harness end-to-end in tests; closes the `all-features.md` F20 line)
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
