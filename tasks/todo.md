# TODO

## Session end (2026-05-12)

F01–F14 complete and committed on `main`. Suite green:
- api 31/31 · web 11/11 · mobile 6/6 · packages 8/8 = **56 tests**

The walking skeleton is now usable in a real browser end-to-end:
**home → /login → /devices (add, test connection) → /devices/:id/attendance (poll, view).**

## Resume here next session

## Up next

- F15 — ADMS push receiver (`/iclock/cdata`, `/iclock/getrequest`) so push-firmware devices can stream events without polling
- F16 — WebSocket real-time feed (`/ws/attendance`)
- F17 — Mobile real-time feed UI
- F18 — Background scheduler (per-device poll interval)
- F19 — Mock device harness (fake pyzk server for tests + hardware-free dev)
- F20+ — see `tasks/all-features.md` (employee enrollment, payroll, reports, hardening)

## Followups carried forward

- Migrate `next lint` → eslint CLI + flat config when bumping to Next 16
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`)
- Replace `Base.metadata.create_all` with Alembic migrations before prod
- Postgres-dialect path for the attendance dedup insert
- Set `TIKKO_JWT_SECRET` properly in prod (currently default `change-me` triggers InsecureKeyLengthWarning)
- Refresh-token rotation flow (refresh tokens are stored but never exchanged yet — access tokens just expire)

## Blocked

_(none)_
