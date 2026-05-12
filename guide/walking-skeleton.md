# Walking Skeleton — Manual Testing Guide

End-to-end exercise for the F01–F11 slice: register a device, poll it, view attendance.

## Prerequisites

- **Tools:** Node 20+, pnpm 10+, Python 3.12+, `uv`, Postgres 16+ (or stick with SQLite for first-run).
- **Tree:** This guide assumes the repo is at `/home/musaajallo/software_development/projects/web_apps/tikko`.
- **Env:** Copy `.env.example` to `.env` at the repo root. For the first-run SQLite path, override:
  ```
  TIKKO_DATABASE_URL=sqlite+aiosqlite:///./tikko-dev.db
  ```
  Leave the rest at defaults.

## 1. Install dependencies

```bash
cd tikko
pnpm install
cd apps/api && uv sync && cd ../..
```

Expected: pnpm completes, `apps/api/.venv/` exists, no errors.

## 2. Run the test suite

```bash
pnpm test:api                   # 15/15 pytest
pnpm --filter @tikko/web test   # 6/6 vitest
pnpm --filter @tikko/mobile test # 2/2 jest
pnpm -r --filter "./packages/*" run test  # 8/8 vitest
```

Expected: every command exits 0.

## 3. Start the API

```bash
cd apps/api
uv run fastapi dev src/tikko/main.py
```

Expected: server listens on `http://localhost:8000`, `GET /health` returns
```json
{ "status": "ok", "service": "tikko-api", "version": "0.0.0" }
```

The lifespan startup will call `Base.metadata.create_all` and create the `devices` and `attendance_logs` tables (in SQLite, the `tikko-dev.db` file will appear in `apps/api/`).

## 4. Start the web app

In a second terminal:

```bash
cd tikko
pnpm --filter @tikko/web dev
```

Expected: Next.js dev server on `http://localhost:3000`. Hot reload active.

## 4b. Create an admin user (one-time)

The `/devices*` endpoints are auth-gated as of F13. Register an admin once:

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"admin@tikko.local","password":"supersecret123","role":"admin"}' | jq .
```

## 5. Sign in through the web UI

1. Browse to `http://localhost:3000` → click **Sign in**.
2. Enter `admin@tikko.local` / `supersecret123`.
3. On success you land on `/devices`. The access token is stored in `localStorage` (`tikko.access_token`) and auto-attached to every API call.

## 5b. Register a device

1. From `/devices`, fill the form:
   - Name: `Front gate`
   - Host: the IP of an actual ZKTeco terminal on your LAN (or any IP — connection will fail but the row will save)
   - Port: `4370`
2. Click **Add device**. The list should refresh with the new row.

Expected: a row appears showing `Front gate`, `<host>:4370`, and the action buttons.

## 6. Test the connection

Click **Test connection** on the row.

- **If the IP is a real, reachable terminal:** the row shows `<device_name> (<serial>) firmware <version>` underneath. HTTP 200.
- **If the IP is unreachable:** the row shows a `connect timeout` (or similar) message. HTTP 503.

This exercises the F08 pyzk wrapper end-to-end.

## 7. Pull attendance

1. Click **View attendance →** on a device row.
2. On the attendance page, click **Poll now**.

- **Reachable terminal:** `Polled N records, M new` banner appears, table populates. Click Poll again and it should show `Polled N records, 0 new` — confirming dedup is working (the F09 unique constraint).
- **Unreachable:** error banner.

## 8. Confirm dedup via API

In a third terminal:

```bash
curl -s -X POST http://localhost:8000/devices | jq .   # list
DID=$(curl -s -X POST http://localhost:8000/devices \
  -H 'content-type: application/json' \
  -d '{"name":"curl-test","host":"127.0.0.1","port":4370}' | jq -r .id)
curl -s -X POST "http://localhost:8000/devices/$DID/poll" | jq .
curl -s "http://localhost:8000/devices/$DID/attendance?page=1&page_size=50" | jq .
```

Polls obviously fail (no real device on 127.0.0.1) but the 404/503 paths are exercised.

## Common Issues

| Issue | Likely cause | Fix |
|-------|--------------|-----|
| `pnpm install` hangs or 404s on `react-server-dom-webpack` | Slow PyPI/NPM mirror or transient registry | Re-run; the lockfile is already pinned, second pass is ~1 min |
| API starts but `/devices` returns 500 with "no such table" | Lifespan didn't run (e.g. mounted with `--no-lifespan`) | Restart with `uv run fastapi dev src/tikko/main.py` (default driver runs lifespan) |
| `Test connection` always 503 with "connect timeout" | Terminal not reachable on `4370` from the API host, or wrong IP | Verify with `ping <host>` and `nc -zv <host> 4370`; check firewall on the terminal |
| Repeated `Poll now` keeps showing `N new > 0` | The (device_id, device_user_id, punched_at) unique constraint isn't tripping — likely your terminal emits sub-second timestamps that vary between polls | Check the records via `/attendance` endpoint; the dedup key may need extension once we add the F18 background scheduler |
| Web shows "Failed to fetch" on the devices page | API not running on `localhost:8000` or `NEXT_PUBLIC_TIKKO_API_BASE_URL` mismatch | Confirm API is up; set the env var explicitly in `apps/web/.env.local` if pointing to a non-default URL |
