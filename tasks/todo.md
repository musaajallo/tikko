# TODO

## Session end (2026-05-14)

F01–F22 complete on `main` (F21 = pull half; push deferred to F21-push), plus a UI polish pass.
- **api 87/87** · **web 16/16** · **shared-types 11/11** · **mobile 8/8** = 122 tests
- Mobile suite is **flaky** — first jest run after a cold start sometimes fails with an `act(...)` warning on `Animated.View` from `TouchableOpacity` in `login.tsx`. Second run is reliably 8/8. Worth a small investigation when next touching mobile.
- `all-features.md` F20 + F22 lines closed; F21 stays open until F21-push lands.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next

- **F21-push** — `POST /employees/:id/templates/push {device_ids}` (reads stored
  templates from `employee_templates`, writes to target devices via
  `save_user_template`). Per-device + per-finger result envelope.
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
