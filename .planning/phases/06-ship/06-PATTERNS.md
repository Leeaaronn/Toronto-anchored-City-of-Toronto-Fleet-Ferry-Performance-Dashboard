# Phase 6: Ship - Pattern Map

**Mapped:** 2026-06-06
**Files analyzed:** 6 (5 new, 1 edit, + 1 conditional doc touch-up)
**Analogs found:** 5 / 6 (README has a partial analog; `.gitattributes` has no analog — greenfield)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/fleet_analytics/pipeline.py` (NEW) | orchestrator / entry-point | batch (full chain) | `src/fleet_analytics/kpis.py` `main()` + `class_target.py` `main()` | exact (idiom) |
| `pyproject.toml` (EDIT — add `[build-system]`) | config / build | n/a | existing `pyproject.toml` `[project]`/`[tool.*]` stanzas | role-match |
| `.gitattributes` (NEW) | config | n/a | none (greenfield) | no analog |
| `README.md` (NEW) | documentation | n/a | `deliverables/data_dictionary.md` header/citation block | partial (style only) |
| `tests/test_pipeline.py` (NEW, optional) | test | batch smoke | `tests/test_export.py` (`test_ten_files_written`) + `conftest.py` | exact |
| `.planning/REQUIREMENTS.md` (EDIT — traceability) | documentation | n/a | the file itself (table reconcile) | n/a — see A2 caveat |

**Critical sequencing note for the planner:** `pyproject.toml [build-system]` must land and `uv sync` must run **before** `-m fleet_analytics.pipeline` can execute, and `.gitattributes` must exist **before** the "regeneration is a clean git diff" verification (Pitfall 1). Wave 0 ordering: build-system → .gitattributes → pipeline.py → README → smoke test → verify.

## Pattern Assignments

### `src/fleet_analytics/pipeline.py` (orchestrator, batch)

**Analog:** `src/fleet_analytics/class_target.py` (lines 90-101) and `src/fleet_analytics/kpis.py` (lines 478-489) — identical `main()` shape.

**`main()` idiom to copy** (`class_target.py` lines 90-101 — the canonical shape: `duckdb.connect()` → `try` body → `finally: con.close()` → `if __name__ == "__main__"`):
```python
def main() -> None:
    """Regenerate the committed reference dimension: ``uv run python -m fleet_analytics.class_target``."""
    con = duckdb.connect()
    try:
        build_class_target(con)
        write_class_target(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
```

**`kpis.py` `main()` (lines 478-489)** — same shape, two-step `build_all` then `write_*`:
```python
def main() -> None:
    """Regenerate the snapshot from Gold Parquet: ``uv run python -m fleet_analytics.kpis``."""
    con = duckdb.connect()
    try:
        build_all(con)
        write_kpi_snapshot(con)
    finally:
        con.close()
```

**Import pattern to copy** (every module uses `from __future__ import annotations` then `import duckdb` then `from fleet_analytics import config` — see `kpis.py` lines 41-47, `export.py` lines 24-28). For the orchestrator, import the sibling modules:
```python
from __future__ import annotations

import duckdb

from fleet_analytics import class_target, export, ingest, kpis, model, transform
```

**Dependency-ordered body** — every builder shares the exact signature `(con: duckdb.DuckDBPyConnection)` (VERIFIED: `ingest.ingest_bronze` line 57, `transform.build_all` line 91, `model.build_all` line 169, `kpis.build_all` line 412). The orchestrator is a flat sequence of these calls on ONE connection, matching the order already encoded in `tests/conftest.py` `gold` fixture (lines 40-43: `transform.build_all` → `model.build_all` → `kpis.build_all` → `class_target.build_class_target`), plus ingest first and the `write_*` exporters interleaved:
```python
def main() -> None:
    con = duckdb.connect()  # :memory:
    try:
        ingest.ingest_bronze(con)
        transform.build_all(con)
        model.build_all(con)
        export.write_gold(con)              # data/gold/*.parquet + *.csv (10 files)
        class_target.build_class_target(con)
        class_target.write_class_target(con)  # data/gold/dim_class_target.{parquet,csv}
        kpis.build_all(con)                 # fail-fast asserts (pooled!=class-mean, 2020<2019, max==7229)
        kpis.write_kpi_snapshot(con)        # data/kpi/*.csv + kpi_values.json
    finally:
        con.close()


if __name__ == "__main__":
    main()
```

**Module docstring style** — every module opens with a `"""<REQ-ID> — <one-line purpose>."""` summary then a short paragraph (see `export.py` lines 1-22, `class_target.py` lines 1-35, `kpis.py` lines 1-39). `pipeline.py` should open the same way, e.g. `"""SHIP-01 — single one-command orchestrator: ingest → ... → kpi snapshot."""`.

**Anti-pattern (from RESEARCH Pattern 1 / line 152):** Do NOT re-read Gold from Parquet mid-run. `kpis.load_gold_views` (kpis.py lines 50-77) is idempotent — it skips names already present as in-DB tables, so the single shared connection reuses the in-memory Gold tables; no Parquet round-trip needed.

---

### `pyproject.toml` (config, add `[build-system]`)

**Analog:** the existing `pyproject.toml` (read in full — `[project]` lines 1-9, `[tool.pytest.ini_options]` lines 11-13, `[dependency-groups]` lines 15-19). Note: `pythonpath = ["src"]` (line 13) is **pytest-only** and does NOT make the package importable at runtime — this is the blocker (Pitfall 3).

**Current full file:**
```toml
[project]
name = "fleet-analytics"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "duckdb>=1.5,<2",
    "pandas>=2.2",
    "pyarrow>=16",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[dependency-groups]
dev = [
    "pandera>=0.26",
    "pytest>=9.0.3",
]
```

**Stanza to ADD** (from RESEARCH Code Examples lines 210-218; A1/A4 — verify exact keys against current hatchling docs at plan time). The `src` layout needs the explicit `packages` line so hatchling finds `src/fleet_analytics`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/fleet_analytics"]
```
After editing, run `uv sync` so the local package installs editable into `.venv`, then verify `uv run python -c "import fleet_analytics"` exits 0 and `uv run python -m fleet_analytics.pipeline` runs (Pitfall 3 acceptance). Alternative (A1): `[tool.uv] package = true` with uv's native `uv_build` backend adds no third-party dep — planner picks one.

---

### `.gitattributes` (config, NEW — no analog)

**Analog:** none — greenfield. Driven directly by RESEARCH Pitfall 1 (lines 182-186) and Don't Hand-Roll (line 162).

**Content to write** (pin CSV to LF to kill Windows CRLF churn; mark Parquet binary):
```gitattributes
*.csv eol=lf
*.parquet binary
```

**Why:** DuckDB `COPY` writes LF; without this, regenerating `data/gold/*.csv` + `data/kpi/*.csv` shows every CSV as "modified" on Windows even though values are byte-identical (VERIFIED in RESEARCH). Must exist before the "run pipeline → `git status` clean" verification.

---

### `README.md` (documentation, NEW)

**Analog:** `deliverables/data_dictionary.md` (lines 1-20) for the header/attribution style. README **aggregates**, never restates, the canonical numbers (RESEARCH Pattern 2, lines 145-148, and Anti-Patterns lines 149-153).

**Header / citation block style to mirror** (`data_dictionary.md` lines 1-6 — title, bold `**Project:**`, generated-from pointer, dated snapshot with cross-links):
```markdown
# Data Dictionary — Bronze Tables

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Layer:** Bronze (typed, as-ingested; no transforms applied)
**Generated from:** `src/fleet_analytics/profile.py::profile_facts` (DuckDB `SUMMARIZE` + targeted SQL)
**Snapshot pull date:** 2026-06-02 (the supplied files are treated as a point-in-time snapshot — see the [DQ report](dq_report.md), caveat A1)
```

**README required content** (SHIP-01): one-command run (`uv sync` then `uv run python -m fleet_analytics.pipeline`), the committed `.planning/data/` inputs + optional `FLEET_DATA_DIR` override (config.py line 24), `data/gold/` Parquet handoff, test gate stated as a **dated command result** ("`uv run pytest -q` → 76 passed, as of 2026-06-06" — NOT an eternal invariant, Pitfall 4), and the headline numbers linked to `deliverables/kpi_definitions.md` / `data/kpi/kpi_values.json` rather than duplicated.

**Headline numbers (quote only these; source of truth is `data/kpi/kpi_values.json`)** — from RESEARCH lines 222-232:
- 89.0% pooled availability (0.8899) — distinct from mean-of-class-means (0.8786)
- 5.8% underutilization (0.0572) — preserve the two-denominator nuance (RESEARCH line 247: 120/2,086 raw vs over-2,080-matched; do NOT conflate)
- 2,080 matched / 6 unmatched (light-duty join integrity)
- 209 nulls excluded / 4,405 non-null denominator
- Row counts 4,614 / 2,086 / 272,529

**Citations to carry** (already in deliverables; CLAUDE.md Constraints): City of Toronto Open Data; May 2023 FSD General Government Committee report; AG Operational Review 2019.AU2.2 / 2019.AU2.3; Open Government Licence – Toronto. State scope boundary (GSD owns data engineering; Power BI canvas authored manually — no `.pbix`/PBIP/TMDL).

**Anti-patterns (RESEARCH lines 149-153):** no restating every KPI value; no hardcoded stale test count; no "fixing" the trailing space in `City Vehicle Availability .csv`.

---

### `tests/test_pipeline.py` (test, batch smoke — optional but recommended)

**Analog:** `tests/test_export.py` `test_ten_files_written` (lines 40-45) for the "assert N files exist" idiom, and `conftest.py` (lines 14-19) for the fresh `:memory:` connection pattern. Note `test_export.py` uses `:memory:` second readers in `try/finally` (lines 57-74) — same connection-hygiene idiom the smoke test should follow.

**File-existence assertion to copy** (`test_export.py` lines 40-45):
```python
def test_ten_files_written(gold: duckdb.DuckDBPyConnection) -> None:
    """write_gold creates data/gold/ with exactly 10 files (5 .parquet + 5 .csv)."""
    export.write_gold(gold)
    for t in config.GOLD_TABLES:
        assert (config.GOLD_DIR / f"{t}.parquet").exists(), f"{t}.parquet missing"
        assert (config.GOLD_DIR / f"{t}.csv").exists(), f"{t}.csv missing"
```

**Test import / path idiom** (`test_export.py` lines 17-29 — `from __future__`, `import duckdb`, `from fleet_analytics import config, export`, helper functions returning `(config.GOLD_DIR / "x.parquet").as_posix()`):
```python
from __future__ import annotations

import duckdb

from fleet_analytics import config, export
```

**Smoke-test shape:** call `pipeline.main()` (or invoke `build`-chain on a fresh `:memory:` con), then assert the 6 Gold Parquet files exist (`config.GOLD_TABLES` = 5 + `dim_class_target`) and `data/kpi/kpi_values.json` exists. Keep it a single, fast integration smoke test — the deep fidelity asserts already live in `test_export.py` / `test_kpis.py` / `test_join_integrity.py`.

---

### `.planning/REQUIREMENTS.md` (documentation — conditional traceability reconcile)

**Analog:** the file itself. RESEARCH Pitfall 5 (lines 203-205): KPI-01 (Phase 3) / REPORT-01 (Phase 4) show "Pending" `[ ]` while ROADMAP marks Phases 3-4 "Complete". **A2 caveat (line 264): confirm with the user before flipping** — artifacts (KPI tables, `report_spec.md`) exist, so this is very likely stale checkbox drift, but do not edit the table without confirmation that the work is genuinely complete.

---

## Shared Patterns

### Builder signature contract
**Source:** every `src/fleet_analytics/*.py` builder (`ingest.py:57`, `transform.py:91`, `model.py:169`, `kpis.py:412`, `export.py:31`, `class_target.py:44`)
**Apply to:** `pipeline.py`
Every builder/writer is `def name(con: duckdb.DuckDBPyConnection) -> ...` operating on one shared connection. The orchestrator simply calls them in dependency order on a single `con`; introduce NO new SQL or interpolation in `pipeline.py` (pure wiring — RESEARCH Security line 347).

### `main()` entry-point idiom
**Source:** `class_target.py` lines 90-101, `kpis.py` lines 478-489
**Apply to:** `pipeline.py`
`duckdb.connect()` → `try:` (build/write calls) → `finally: con.close()` → module-level `if __name__ == "__main__": main()`, with a docstring naming the `uv run python -m fleet_analytics.<mod>` invocation.

### COPY export idiom (already implemented — do not reinvent)
**Source:** `export.py` lines 31-46, `class_target.py` lines 71-87, `kpis.py` lines 457-475
**Apply to:** referenced by `pipeline.py` (calls existing writers, does not re-implement)
`config.<DIR>.mkdir(parents=True, exist_ok=True)`; path via `(config.<DIR> / name).as_posix()`; `COPY (SELECT * FROM {name}) TO '{p}.parquet' (FORMAT PARQUET)` then `'.csv' (FORMAT CSV, HEADER)`. Only internal `config` names/paths are interpolated (security invariant — keep it).

### Security invariant (no external value in SQL)
**Source:** `export.py` lines 18-21 (docstring), echoed in `kpis.py` lines 36-38, `class_target.py` lines 27-30
**Apply to:** `pipeline.py`, `tests/test_pipeline.py`
The new orchestrator must preserve "no external/user value reaches the SQL string" — it adds no f-string SQL of its own; it only calls existing builders.

### Deliverable header / attribution style
**Source:** `deliverables/data_dictionary.md` lines 1-6 (mirrored across all 7 deliverables)
**Apply to:** `README.md`
`# Title`, bold `**Project:** Fleet Services Analytics — City of Toronto BA Assignment`, a "generated/run from" pointer, a dated snapshot line, and inline cross-links to companion docs.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.gitattributes` | config | n/a | No git-attributes file exists in the repo yet; content is a 2-line greenfield write driven by RESEARCH Pitfall 1 |

`README.md` is listed as "partial" rather than "no analog": the prose/aggregation is greenfield, but the header/citation block style is copied from `deliverables/data_dictionary.md`.

## Metadata

**Analog search scope:** `src/fleet_analytics/`, `tests/`, `deliverables/`, repo-root config (`pyproject.toml`, `.gitignore`)
**Files scanned:** 22 tracked source/test/config files; read in full or targeted: `class_target.py`, `export.py`, `kpis.py` (heads + main/write tail), `conftest.py`, `test_export.py`, `pyproject.toml`, `.gitignore`, `data_dictionary.md` (header); grep-confirmed builder signatures in `ingest.py`/`transform.py`/`model.py`
**Pattern extraction date:** 2026-06-06
