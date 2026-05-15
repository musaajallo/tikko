# syntax=docker/dockerfile:1.7
#
# tikko-api image.
#
# Build context is the monorepo root so the COPY paths line up with the
# `apps/api/...` layout. Build with:
#   docker build -f apps/api/Dockerfile -t tikko-api .
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# `uv` is the Python toolchain the project uses for everything. The official
# image ships a single binary; copy it in rather than `pip install uv` to
# avoid Python-version coupling.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app/apps/api

# Lockfile-driven install. The two-step COPY keeps the dependency layer
# cached across source edits.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the project itself + alembic config so migrations can run from
# inside the container (`docker compose run api alembic upgrade head`).
COPY apps/api/src ./src
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic

RUN uv sync --frozen --no-dev

EXPOSE 8000

# Health probe target — see /health route in routes/health.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).status == 200 else 1)"

CMD ["uv", "run", "uvicorn", "tikko.main:app", "--host", "0.0.0.0", "--port", "8000"]
