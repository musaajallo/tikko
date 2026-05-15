# tikko — deploy notes

Two supported deploys: **LAN** (single host on an office network) and
**cloud** (VPS with TLS, public DNS, possibly behind a CDN). Same image,
different orchestration.

## LAN (Docker Compose)

```bash
cp .env.example .env
# Edit .env — at minimum set TIKKO_JWT_SECRET (openssl rand -hex 32).
docker compose -f docker-compose.lan.yml --env-file .env up -d --build
docker compose -f docker-compose.lan.yml run --rm api uv run alembic upgrade head
```

- Postgres data persists in the `tikko-postgres` named volume.
- The api binds to `0.0.0.0:8000` so ZKTeco devices on the LAN can push to
  `/iclock/cdata`. Postgres binds to `127.0.0.1:5432` only — clients reach
  the DB through the api.
- The web app baked-in `NEXT_PUBLIC_TIKKO_API_BASE_URL` defaults to
  `http://localhost:8000`. Set it to the LAN-reachable api URL for the
  build (`http://192.168.x.x:8000`) so other machines on the network
  can use it.

## Cloud (VPS without Docker)

`deploy/systemd/` has sample units for running the api + web directly under
systemd. Both expect:

- Source at `/opt/tikko`, checked out from git.
- Python 3.12 + `uv`, Node 20 + `pnpm`.
- Environment files at `/etc/tikko/api.env` and `/etc/tikko/web.env`
  (root-owned, mode 640).
- Postgres reachable on localhost (or external — see
  `TIKKO_DATABASE_URL`).
- A reverse proxy (nginx / caddy) terminating TLS and routing to
  `127.0.0.1:8000` (api) and `127.0.0.1:3000` (web).

Bootstrap:

```bash
sudo cp deploy/systemd/tikko-api.service /etc/systemd/system/
sudo cp deploy/systemd/tikko-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tikko-api tikko-web
```

The api unit runs `alembic upgrade head` on every start as `ExecStartPre`,
so deploys are "git pull && systemctl restart tikko-api". The web unit
expects the build output (`.next/standalone`) already present — wire that
into your CI or a separate build step.

## Cloud-mode env validation

`TIKKO_DEPLOY_MODE=cloud` triggers `Settings.validate_for_deployment()`
at startup. It refuses to boot if any of these still hold their defaults:

- `TIKKO_JWT_SECRET == "change-me"`
- `TIKKO_DATABASE_URL` points at SQLite
- `TIKKO_CORS_ORIGINS == ["http://localhost:3000"]`

Set all three (and any other prod-only values) before flipping the mode.
