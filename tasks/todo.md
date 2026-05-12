# TODO

## F03 — API skeleton (next)

Steps:
1. `cd apps/api` and `uv init --package tikko-api`
2. Add deps: fastapi, uvicorn[standard], pydantic, pydantic-settings, sqlalchemy[asyncio], alembic, psycopg[binary], structlog, pyzk
3. Dev deps: pytest, pytest-asyncio, httpx, ruff, mypy
4. Project layout: `src/tikko/{__init__,main,settings,logging,errors}.py`, `tests/test_health.py`
5. **Write failing test first** — `tests/test_health.py` asserts `GET /health` returns `{"status": "ok"}`
6. Implement minimal `main.py` with the route until test passes
7. Add `ruff.toml` (or pyproject section) and confirm `uv run ruff check .` passes

## Up next

- F04 — Web skeleton
- F05 — Mobile skeleton

## Blocked

_(none)_
