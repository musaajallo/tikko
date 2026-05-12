"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from tikko import __version__

app = FastAPI(title="tikko-api", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tikko-api", "version": __version__}
