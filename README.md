# tikko

Custom ZKTeco attendance terminal management platform. Single deployable that runs the same on a LAN server or a VPS — connection details are environment-driven.

## What it does

- Manages ZKTeco fingerprint terminals (K40, K50, MB360, iClock series, etc.)
- Pulls attendance logs via the ZK binary protocol on port 4370 (`pyzk`)
- Receives push events via the ADMS protocol (`/iclock/cdata`, `/iclock/getrequest`)
- Real-time attendance feed over WebSocket
- Employee + fingerprint template management with transfer between devices
- Payroll-style reports (shifts, late/early/OT) with CSV/XLSX export
- Web admin dashboard + role-based mobile app (employee/manager/admin)

## Repo layout

```
tikko/
├─ apps/
│  ├─ api/              FastAPI + pyzk + workers      (Python, uv)
│  ├─ web/              Next.js admin dashboard       (TypeScript)
│  └─ mobile/           Expo / React Native           (TypeScript)
├─ packages/
│  ├─ api-client/       Generated TS client from OpenAPI
│  └─ shared-types/     Zod schemas + shared constants
├─ infra/
│  ├─ docker/           Dockerfiles + docker-compose (LAN install)
│  └─ deploy/           VPS deploy scripts + systemd units
├─ tasks/               Feature plan + progress log
└─ .github/workflows/   CI
```

## Prerequisites

- Node 20+ and pnpm 10+ (`corepack enable` or `fnm`/`nvm`)
- Python 3.13+ and `uv`
- Postgres 16+

## Quickstart

```bash
cp .env.example .env
pnpm install
cd apps/api && uv sync && cd ../..

pnpm dev
```

## Deployment modes

Set `TIKKO_DEPLOY_MODE` in `.env`:

- `lan` — server lives on the office LAN, devices are on private IPs, the ADMS push endpoint binds to the internal interface, TLS optional
- `cloud` — server on a VPS, devices push over the internet or VPN, push endpoint internet-facing, TLS required

Same code, same image, different env.

## Development workflow

This project is built feature-by-feature using a TDD workflow. The full plan lives in [`tasks/all-features.md`](tasks/all-features.md) and progress is logged in [`tasks/done.md`](tasks/done.md).
