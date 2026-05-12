# tikko-api

FastAPI service for tikko. Manages ZKTeco terminals via the binary protocol on port 4370 (`pyzk`) and the ADMS push protocol over HTTP.

## Run

```bash
uv sync
uv run fastapi dev src/tikko/main.py
```

## Test

```bash
uv run pytest
```
