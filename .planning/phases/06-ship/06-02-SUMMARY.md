---
phase: 06-ship
plan: 02
subsystem: orchestration
tags: [pipeline, orchestrator, entry-point, smoke-test, ship-01]
requires:
  - "fleet_analytics importable at runtime (06-01 hatchling build-system)"
  - ".gitattributes pinning CSV to LF (06-01)"
provides:
  - "one-command full-chain orchestrator: uv run python -m fleet_analytics.pipeline"
  - "integration smoke test proving the orchestrator writes all Gold Parquet + the KPI snapshot"
affects:
  - src/fleet_analytics/pipeline.py
  - tests/test_pipeline.py
tech-stack:
  added: []
  patterns:
    - "orchestrator = flat sequence of existing (con)-signature builders on ONE in-memory DuckDB connection"
    - "main() idiom: duckdb.connect() -> try body -> finally close -> __main__ guard (copied from class_target.py / kpis.py)"
    - "single fast integration smoke test asserts file existence only; deep fidelity stays in test_export/test_kpis/test_join_integrity"
key-files:
  created:
    - src/fleet_analytics/pipeline.py
    - tests/test_pipeline.py
  modified: []
decisions:
  - "pipeline.py is pure wiring — zero new SQL and zero f-string interpolation (verified: grep for f-strings returns no matches), preserving the T-6-01 security invariant"
  - "Did NOT commit any data/gold or data/kpi files: the orchestrator's regeneration is content-identical (git diff --ignore-cr-at-eol is empty); the residual git 'modified' status is pre-existing CRLF-vs-eol=lf blob drift inherited from the worktree base, a Plan-01 line-ending-hygiene concern out of scope for this orchestration plan"
metrics:
  duration: ~12m
  completed: 2026-06-06
  tasks: 3
  files: 2
---

# Phase 6 Plan 02: One-Command Pipeline Orchestrator Summary

Created `src/fleet_analytics/pipeline.py` — the single one-command orchestrator that runs the entire data pipeline end-to-end (ingest → transform → model → export → class_target build+write → kpis build → kpi snapshot) on one in-memory DuckDB connection — plus `tests/test_pipeline.py`, a fast integration smoke test proving it writes all 6 Gold Parquet files and the committed KPI snapshot. This satisfies SHIP-01 Success Criterion 1 ("the full pipeline runs as a single one-command invocation").

## What Was Built

- **Full-chain orchestrator (Task 1):** `src/fleet_analytics/pipeline.py` defines `def main()` that opens `duckdb.connect()` (in-memory), then in a `try` block calls — in exact dependency order on ONE shared connection — `ingest.ingest_bronze`, `transform.build_all`, `model.build_all`, `export.write_gold`, `class_target.build_class_target`, `class_target.write_class_target`, `kpis.build_all`, `kpis.write_kpi_snapshot`, and closes the connection in `finally`. An `if __name__ == "__main__": main()` guard enables `uv run python -m fleet_analytics.pipeline` (exits 0). It is pure wiring: it imports the sibling builder modules and authors NO SQL string and NO f-string interpolation of its own (T-6-01 — verified by grep returning no f-string matches). It does not re-read Gold from Parquet mid-run; `kpis.load_gold_views` is idempotent and reuses the in-memory Gold tables (RESEARCH Anti-Pattern avoided).
- **Integration smoke test (Task 2):** `tests/test_pipeline.py::test_pipeline_runs_and_writes_gold` invokes the real `pipeline.main()`, then loops over `config.GOLD_TABLES + ["dim_class_target"]` asserting each `.parquet` exists in `config.GOLD_DIR`, and asserts `config.KPI_DIR / "kpi_values.json"` exists. It deliberately does NOT duplicate the pooled-mean / COVID-dip / 7229-max / 209-null / 2080-6 join-integrity asserts — those remain in `test_export.py` / `test_kpis.py` / `test_join_integrity.py`.
- **Suite + reproducibility confirmation (Task 3):** `uv run pytest -q` → **77 passed, 0 failed** (prior 76 + the new smoke test). A fresh `uv run python -m fleet_analytics.pipeline` produces **content-identical** Gold/KPI output: `git diff --ignore-cr-at-eol -- data/gold/ data/kpi/` is empty, proving deterministic regeneration. See Deviations for the residual line-ending bookkeeping note.

## How to Verify

```bash
uv sync                                              # editable-install the local package
uv run python -m fleet_analytics.pipeline            # -> exits 0; writes 6 Gold Parquet + kpi_values.json
uv run pytest -q                                     # -> 77 passed
uv run pytest tests/test_pipeline.py -q              # -> 1 passed (the smoke test)
git diff --ignore-cr-at-eol -- data/gold/ data/kpi/  # -> empty (regeneration is byte-identical content)
```

## Deviations from Plan

### Deferred / Documented (Task 3 acceptance nuance)

**1. [Documented - eol blob drift] data/gold + data/kpi CSVs show `M` under `git status`, but regeneration is content-identical**
- **Found during:** Task 3 (`git status --porcelain` after the pipeline run flagged 8 data CSVs — `dim_class_target.csv` plus 7 of the `data/kpi/*.csv` — as modified, plus the 3 committed `.planning/data/*.csv` inputs).
- **Investigation:** `git diff --ignore-cr-at-eol -- data/gold/ data/kpi/` is **empty** → the regenerated content is byte-identical; only line endings differ. The committed blobs at HEAD contain CRLF (`git cat-file -p HEAD:data/kpi/ferry_yoy.csv | grep -c $'\r'` → 11), while `.gitattributes` (`*.csv eol=lf`, added in Plan 01) mandates LF, so git emits "CRLF will be replaced by LF the next time Git touches it" and marks the files modified. This is renormalization drift between pre-`.gitattributes` CRLF-committed blobs and the new eol policy — it is NOT churn produced by the orchestrator (the pipeline writes LF; the content matches the committed data exactly). The `.planning/data/*.csv` inputs are committed read-only inputs the pipeline never writes; they carry the same CRLF-blob-vs-eol=lf flag and were already in this state at the worktree base.
- **Decision:** Did NOT stage or commit any `data/gold`, `data/kpi`, or `.planning/data` file. Renormalizing the committed CSV blobs to LF is a Plan-01 line-ending-hygiene concern; doing it here would (a) put data files into this orchestration plan's commit, violating the Task-3 acceptance criterion that the only uncommitted outputs are `pipeline.py` + `test_pipeline.py`, and (b) exceed this plan's scope. `git add --renormalize` was tested locally and confirmed to be a content no-op (`--ignore-cr-at-eol` empty before and after) but was reverted to keep this plan's commits limited to its two source/test files.
- **Why the strict literal criterion ("no modifications under data/gold/ or data/kpi/") reads as partially unmet, yet the INTENT is satisfied:** the criterion exists to prove deterministic, byte-stable regeneration (reproducibility). That is proven at the content level (`--ignore-cr-at-eol` empty). The remaining `M` flags are a pre-existing blob-encoding artifact, not a value/aggregation change. Recommend the orchestrator (or a follow-up Plan-01 touch-up) run `git add --renormalize 'data/**/*.csv'` once to flush the stale CRLF blobs to LF and clear the flags permanently.
- **Files modified:** none (no data file committed).
- **Commit:** n/a (documented finding; no content change committed for data files).

## Authentication Gates

None.

## Threat Surface

No new security-relevant surface. Per the plan threat model:
- **T-6-01 (mitigated):** `pipeline.py` authors no SQL and no f-string interpolation — verified by grep (`f"`/`f'` → no matches). It only calls existing, already-tested builders that interpolate solely internal `config` constants.
- **T-6-02 (accept):** regeneration verified content-identical (`--ignore-cr-at-eol` empty); inputs are committed/trusted; no external value reaches SQL.
- **T-6-SC (accept):** no new package added; build backend from Plan 01 already pinned in `uv.lock` (`uv sync` added only the expected editable local package + its existing deps).

## Known Stubs

None.

## Commits

- `bd1d03d` feat(06-02): add full-chain pipeline.py orchestrator
- `a59bffb` test(06-02): add integration smoke test for orchestrator

## Self-Check: PASSED

- FOUND: src/fleet_analytics/pipeline.py (`def main()` + `if __name__ == "__main__": main()`)
- FOUND: tests/test_pipeline.py (imports `from fleet_analytics import config, pipeline`; invokes `pipeline.main()`)
- FOUND commit: bd1d03d
- FOUND commit: a59bffb
- VERIFIED: `uv run python -m fleet_analytics.pipeline` exits 0; all 6 Gold Parquet + kpi_values.json present; `uv run pytest -q` → 77 passed; pipeline.py has no SQL/f-strings; data regeneration content-identical (`--ignore-cr-at-eol` empty)
