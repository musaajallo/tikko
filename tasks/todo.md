# TODO

## Session end (2026-05-14)

**F01–F32 complete on `main` — every roadmap feature shipped.** Plus a profile page, real settings page, employee leave list on mobile, web leave-requests page, web templates page, TOTP recovery codes, XLSX export, Remember-me persistence, edit-employee dialog, delete-confirm dialog.
- **api 218/218** · **web 33/33** · **shared-types 11/11** · **mobile 15/15** = 277 tests
- `all-features.md` F01–F32 all ticked. No roadmap items left.
- **Alembic migrations**: 4 total — `8c51c515c891` (initial), `598bccf9f7db` (leave_requests), `2823730c4ea4` (shift_rules), `b2d4cc7dbe00` (user_totp).
- **Cloud mode is now enforced at boot**: lifespan calls `Settings.validate_for_deployment()`; misconfigured cloud deploys (default jwt secret, sqlite DB, default localhost CORS) fail fast with a combined error listing every issue.
- **Known migration gotcha**: when autogenerate emits a new FK inside `batch_alter_table` (SQLite path), hand-edit the file to name the constraint — autogen emits `create_foreign_key(None, ...)` and SQLite's batch mode rejects it. Hit once during F26, documented in the done.md entry.

The walking skeleton is now usable in a real browser end-to-end, with ADMS push protocol,
WebSocket real-time feed, mobile real-time UI, a per-device background poller, and an
in-process pyzk harness for tests + hardware-free dev.

## Resume here next session

## Up next — roadmap

_All roadmap features shipped — nothing pending._

## Optional features

_All optional UI gaps and follow-ups from the prior list are also shipped (F30-recovery, F28-xlsx, web leave-requests, web templates, employee leave on mobile, F22-edit, F22-delete-confirm)._

## Followups (not features)

- Backfill `tasks/done.md` entries for F15–F18 + UI polish (notes only live in commit messages right now).
- Migrate `next lint` → ESLint CLI + flat config when bumping to Next 16.
- `pnpm.overrides` to align `@types/react` (currently band-aided with `{children as any}` in `app/layout.tsx`).
- Postgres-dialect path for the attendance dedup insert (currently SQLite-flavoured `ON CONFLICT`).
- Set `TIKKO_JWT_SECRET` properly in prod (F31 now refuses to boot in cloud mode with the default — but no real secret is set yet).
- Refresh-token rotation flow — refresh tokens are issued but never exchanged.
- Mobile suite flake — first jest run after a cold start sometimes fails with an `act(...)` warning on `Animated.View` from `TouchableOpacity` in `login.tsx`. Second run is reliably green.
- TOTP `secret_b32` is stored plaintext — encryption-at-rest needs a KMS / wrapper-key story.

## Blocked

_(none)_
