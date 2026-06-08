---
phase: 06-ship
plan: 01
subsystem: packaging
tags: [build-system, hatchling, gitattributes, uv, windows]
requires: []
provides:
  - "fleet_analytics importable at runtime (editable install via hatchling)"
  - ".gitattributes pinning CSV to LF and Parquet to binary"
  - ".gitignore coverage for editable-install build artifacts"
affects:
  - pyproject.toml
  - .gitattributes
  - .gitignore
  - uv.lock
tech-stack:
  added:
    - "hatchling (PyPA-official build backend)"
  patterns:
    - "src-layout package made installable via [tool.hatch.build.targets.wheel] packages"
    - "eol=lf gitattribute to neutralize Windows CRLF diff churn on DuckDB CSV exports"
key-files:
  created:
    - .gitattributes
  modified:
    - pyproject.toml
    - .gitignore
    - uv.lock
decisions:
  - "Used hatchling (PyPA-official, RESEARCH-Approved) as the only added build dependency; no other third-party package introduced (T-6-SC mitigation)"
  - "Renormalized the 5 committed data/gold CSVs with `git add --renormalize` (no-op: blobs already LF) to clear a stale eol-comparison flag — no actual content churn"
metrics:
  duration: ~5m
  completed: 2026-06-06
  tasks: 3
  files: 4
---

# Phase 6 Plan 01: Packaging & Line-Ending Hygiene Summary

Made the `fleet_analytics` src-layout package importable at runtime by adding a hatchling `[build-system]` to `pyproject.toml`, and neutralized Windows CRLF diff churn on regenerated CSV outputs via a new `.gitattributes` — clearing two of the three foundational SHIP-01 blockers so Plan 02 can run `python -m fleet_analytics.pipeline` and Plan 03 can verify clean regeneration diffs.

## What Was Built

- **Runtime importability (Task 1):** Added `[build-system]` (`requires = ["hatchling"]`, `build-backend = "hatchling.build"`) and `[tool.hatch.build.targets.wheel]` with `packages = ["src/fleet_analytics"]`. `uv sync` now installs the local package editable into `.venv` (`+ fleet-analytics==0.1.0 (from file://...)`), and `uv run python -c "import fleet_analytics"` exits 0 — previously raised `ModuleNotFoundError` at runtime because pytest's `pythonpath=["src"]` only fixed collection, not runtime. All four pre-existing stanzas (`[project]`, dependency list, `[tool.pytest.ini_options]`, `[dependency-groups]`) left unchanged.
- **Line-ending + ignore hygiene (Task 2):** Created `.gitattributes` at repo root with exactly `*.csv eol=lf` and `*.parquet binary`. Extended `.gitignore` with a `# Build artifacts` section (`build/`, `*.egg-info/`, `dist/`). `git check-attr eol -- data/gold/dim_date.csv` reports `eol: lf`; `data/gold/` and `data/kpi/` remain tracked.
- **Non-breaking verification (Task 3):** `uv run pytest -q` → 76 passed, 0 failed (matches RESEARCH baseline). Working tree is fully clean with no CSV/Parquet content churn and no leaked build artifacts.

## How to Verify

```bash
uv run python -c "import fleet_analytics; print('ok')"   # -> ok
git check-attr eol -- data/gold/dim_date.csv              # -> eol: lf
uv run pytest -q                                          # -> 76 passed
git status --porcelain                                    # -> clean
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stale eol comparison flag on 5 committed data/gold CSVs**
- **Found during:** Task 3 (`git status --porcelain` showed dim_date.csv, dim_division.csv, dim_time.csv, fact_ferry.csv, fact_vehicle.csv as modified)
- **Issue:** After staging `.gitattributes` with `*.csv eol=lf`, git flagged the 5 already-committed CSVs as "modified". Inspection showed both the committed blob (`git show HEAD:...`) and the working-tree file were already LF (`cat -A` shows `$` with no `^M`); `git diff` produced zero content lines. This was git's stale eol-attribute comparison, not real churn.
- **Fix:** Ran `git add --renormalize` on exactly the 5 named CSVs (not a blanket `git add .`). Because the blobs were already LF, this was a no-op that cleared the false-modified status; working tree returned fully clean.
- **Files modified:** none (no-op renormalize; no new commit needed)
- **Commit:** n/a (verification-only task; no content change resulted)

## Authentication Gates

None.

## Threat Surface

No new security-relevant surface. Per the plan threat model: T-6-SC mitigated (only hatchling added — PyPA-official, RESEARCH-Approved; `uv.lock` pins all transitive deps; `uv sync` added no unexpected packages). No Python or SQL authored (config-only edits).

## Known Stubs

None.

## Commits

- `54bd52e` build(06-01): add hatchling build-system for runtime import
- `13d2086` chore(06-01): add .gitattributes and ignore build artifacts

## Self-Check: PASSED

- FOUND: pyproject.toml (`[build-system]` + `[tool.hatch.build.targets.wheel]`)
- FOUND: .gitattributes (`*.csv eol=lf`, `*.parquet binary`)
- FOUND: .gitignore (`build/`, `*.egg-info/`, `dist/`)
- FOUND commit: 54bd52e
- FOUND commit: 13d2086
- VERIFIED: `import fleet_analytics` exits 0; `git check-attr eol` -> lf; pytest 76 passed; working tree clean
