# TODO

## Session end (2026-05-12)

F01–F13 complete and committed on `main`. Suite green: api 31/31, web 6/6, mobile 2/2, packages 8/8.

## Resume here next session

**Heads-up before picking up F14:** the web/mobile UIs do not yet send auth tokens. After F13, the api requires bearer tokens for `/devices*` routes — so the web app's devices/attendance pages will currently fail in the browser even though their vitest tests pass (tests don't hit the real api).

Two options before continuing:
1. **Hot-patch web/mobile** to send a manual dev token (added to `.env.local`) — quick unblock for manual testing.
2. **F14 first** — implement mobile login + token storage and a matching web login flow. Cleaner but a larger feature.

## Up next

- F14 — Mobile login flow + auth context + SecureStore (and matching web login)
- F15 — ADMS push receiver
- F16 — WebSocket real-time feed
- F17 — Mobile real-time feed UI
- F18+ — see `tasks/all-features.md`

## Followups carried forward

- Migrate `next lint` → eslint CLI + flat config when bumping to Next 16
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`)
- Replace `Base.metadata.create_all` with Alembic migrations before prod
- Postgres-dialect path for the attendance dedup insert (currently `sqlite_insert.on_conflict_do_nothing` works on both via SQLAlchemy but a clean dialect switch is owed)
- Set `TIKKO_JWT_SECRET` properly in prod (currently default `change-me` triggers InsecureKeyLengthWarning under tests)

## Blocked

_(none)_
