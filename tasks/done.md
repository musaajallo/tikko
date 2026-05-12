# Done

## F01 — Monorepo skeleton ✓
- **Tests:** smoke check — `pnpm install` resolves the workspace (prettier + turbo installed)
- **Files changed:** 13 new (root configs + tasks/ folder)
- **Lines:** +~300
- **Complexity:** Low — pure tooling/configs, no logic
- **Notes:**
  - `just` skipped (not installed); root `pnpm` scripts orchestrate everything, calling `uv run` for Python tasks. Can swap to `just` later if desired.
  - Single-deployable contract documented in CLAUDE.md — no branching on `TIKKO_DEPLOY_MODE` in business logic.
  - All env vars use `TIKKO_*` prefix.
  - Git initialized on `main` with per-feature commit convention.

## F02 — CI workflow ✓
- **Tests:** smoke check — YAML parses; 5 jobs detected (workspace, api, web, mobile, packages)
- **Files changed:** 1 new (`.github/workflows/ci.yml`)
- **Lines:** +~115
- **Complexity:** Low — single workflow file
- **Notes:**
  - Each app-specific job is gated by `if: hashFiles(...)` so the workflow doesn't fail before F03/F04/F05 land.
  - Workspace job (install + prettier check) runs unconditionally.
  - Uses `pnpm/action-setup@v4`, `actions/setup-node@v4` w/ pnpm cache, `astral-sh/setup-uv@v6` for the Python api.
  - Concurrency group set to cancel superseded runs on the same ref.
