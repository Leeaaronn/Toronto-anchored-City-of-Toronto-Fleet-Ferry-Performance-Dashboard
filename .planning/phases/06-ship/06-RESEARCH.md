# Phase 6: Ship - Research

**Researched:** 2026-06-06
**Domain:** Packaging / reproducibility / documentation for a Python + DuckDB + uv data pipeline (no new product features)
**Confidence:** HIGH (the entire surface is the local repo, directly inspected and exercised this session)

## Summary

Phase 6 is a **packaging and reproducibility** phase, not a feature phase. The data-engineering work is done: 76 pytest tests pass cleanly in ~4.5s, all five (actually six, counting `dim_class_target`) Gold Parquet tables exist in `data/gold/`, the KPI snapshot is committed in `data/kpi/`, and all seven deliverable docs are written, internally consistent, and already carry citations, the 2026-06-02 pull date, and the Open Government Licence – Toronto attribution. The repo is already remarkably clean — no notebooks, HTML, tmp, or log scratch artifacts; no stray `__pycache__`/`.pyc` files tracked in git; the working tree is clean.

There is **one hard blocker and several smaller gaps** the plan must close. The hard blocker: `uv run python -m fleet_analytics.kpis` (and any `-m fleet_analytics.*` invocation) **fails today** with `ModuleNotFoundError: No module named 'fleet_analytics'` — verified live this session. The package lives under `src/` but `pyproject.toml` has **no `[build-system]`**, so `uv` treats the project as non-packaged and never puts `fleet_analytics` on the runtime path; `pythonpath = ["src"]` only applies to pytest. The CLAUDE.md-documented one-command invocation `uv run python -m fleet_analytics.pipeline` therefore cannot work on two counts: (1) no `pipeline` module exists, and (2) the package is not importable at runtime. Success Criterion 1 ("the full pipeline runs as a single one-command invocation") cannot be met until both are fixed.

The smaller gaps: there is **no single orchestrator** that runs the whole chain (`ingest → transform → model → export → kpis → class_target` and writes every artifact) — `export.write_gold` is called only from tests, never from production code; there is **no README** at all; and CSV regeneration produces **spurious LF↔CRLF git diffs on Windows** (verified — values are byte-identical, only line endings differ). A `.gitattributes` should pin `*.csv eol=lf` to make regeneration a clean no-op. Finally, REQUIREMENTS.md traceability lists KPI-01 and REPORT-01 as "Pending" while the ROADMAP marks Phases 3 and 4 "Complete" — a documentation inconsistency Ship should reconcile (these are checkbox/table drift, not unfinished work).

**Primary recommendation:** Add a `[build-system]` to `pyproject.toml` (hatchling) so the package is importable, create `src/fleet_analytics/pipeline.py` with a `main()` that runs the full chain end-to-end and writes all artifacts, then write a README that aggregates the citations/assumptions/pull-date/test-results already present in the deliverables. Add `.gitattributes` (`*.csv eol=lf`) to kill the CRLF churn. Reconcile the REQUIREMENTS traceability table. Do **not** add GitHub Actions CI (deferred to v2 / EXT-02).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| One-command pipeline run | Application entry (`pipeline.py` `__main__`) | uv (process/env) | A single `main()` orchestrating the existing module `build_all`/`write_*` functions in dependency order; uv provides the reproducible interpreter + locked deps |
| Package importability | Build system (`pyproject.toml [build-system]`) | uv (`uv sync` installs the local package editable) | `-m fleet_analytics.x` only resolves if the package is installed or on `sys.path`; pytest's `pythonpath` does not help at runtime |
| Reproducible deps | uv + `uv.lock` | `.python-version` (3.12) | Lockfile already committed; `uv sync` from a clean checkout is the reproducibility contract |
| Deterministic outputs | DuckDB `COPY` + `.gitattributes` | git | DuckDB writes byte-stable CSV/Parquet; `.gitattributes` `*.csv eol=lf` prevents Windows CRLF rewrites that fake a diff |
| Documentation (README) | Repo root markdown | deliverables/ (source of truth for numbers/citations) | README aggregates existing facts; it must not invent or restate numbers that could drift |
| Self-consistency verification | Test suite + manual cross-read | deliverables/ + `data/kpi/kpi_values.json` | The canonical numbers live in `kpi_values.json`; every doc already transcribes from it |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SHIP-01 | README (citations, assumptions, pull date, test results); one-command reproducible pipeline; `data/gold/` with all five Parquet files; repo cleanup; all three deliverables confirmed complete and self-consistent | Gold Parquet present (6 files incl. `dim_class_target`); 76 tests green; deliverables complete + consistent; **gaps**: no README, no importable package, no `pipeline.py` orchestrator, CRLF churn, traceability-table drift — all enumerated below with verified evidence |

## Standard Stack

No new libraries are needed for this phase. The shipping toolchain is already in place and verified this session.

### Core (already present, verified)
| Library / Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uv | 0.10.4 | Env, lockfile, one-command run wrapper | `[VERIFIED: uv --version this session]`. Already the project's manager; `uv.lock` committed |
| Python | 3.12 | Runtime (pinned via `.python-version`) | `[VERIFIED: .python-version = 3.12, pyproject requires-python >=3.12,<3.13]` |
| DuckDB | >=1.5,<2 | Pipeline engine + `COPY` exporters | `[VERIFIED: pyproject.toml]`. Already drives every builder |
| pytest | >=9.0.3 | Test runner (`uv run pytest -q`) | `[VERIFIED: 76 passed in 4.49s this session]` |

### Supporting (build-system to ADD)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hatchling | latest (build backend) | `[build-system]` backend so `fleet_analytics` becomes an importable installed package | **Required** to fix the `ModuleNotFoundError` blocker. uv's default/native build backend; minimal config. `[ASSUMED — see Assumptions Log A1]` |

**Why hatchling:** It is the most common, lowest-config build backend for `src`-layout uv projects and is what `uv init --package` scaffolds. An equally valid alternative is uv's own native build backend (`uv_build`) or setting `[tool.uv] package = true` with an existing backend. The plan should pick one; the goal is simply "make `fleet_analytics` importable at runtime from the project root."

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `[build-system]` + hatchling (install the package) | `uv run --with-editable .` or a `[tool.uv] package = true` flag | Flag-only approaches still need a backend; an explicit `[build-system]` is the clearest, most portable fix and documents intent |
| `pipeline.py` orchestrator module | A root `run.py` script or a `Makefile`/`justfile` | A module inside the package is consistent with the existing `main()` idiom in `kpis.py`/`class_target.py` and matches the CLAUDE.md-documented `-m fleet_analytics.pipeline` path |
| GitHub Actions CI | Skip CI entirely | CI is **deferred to v2 (EXT-02)** and marked OPTIONAL in the brief. Adding it now is scope creep; a green local `uv run pytest -q` is the evidence the README cites |

**Installation:** No new third-party runtime deps. The only `pyproject.toml` change is adding a `[build-system]` block (and optionally a `[tool.hatch.build.targets.wheel] packages = ["src/fleet_analytics"]` line for the `src` layout). After editing, re-run `uv sync` so the local package installs into the venv.

**Version verification:** `uv 0.10.4 (2026-02-17)` `[VERIFIED: uv --version this session]`. DuckDB/pandas/pyarrow/pytest already locked in `uv.lock` (32 KB, committed) — no registry changes required.

## Package Legitimacy Audit

> Only one package is *added* this phase (a build backend); everything else is already locked in `uv.lock`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| hatchling | PyPI | mature (PyPA-maintained, years) | very high | github.com/pypa/hatch | not run this session | Approved `[ASSUMED]` — PyPA-official, ubiquitous; planner may gate behind a verify step if desired |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck was not run this session. hatchling is a PyPA-maintained backend (same org as pip/build/setuptools) and is the standard uv build backend; risk is negligible. If the plan prefers uv's native `uv_build` backend, no third-party package is added at all — strictly safer.*

## Architecture Patterns

### System Architecture Diagram (target end-state pipeline)

```
                    .planning/data/*.csv  (3 raw source CSVs — committed)
                              │
                              ▼
         ┌─────────────────────────────────────────────────────┐
         │  uv run python -m fleet_analytics.pipeline           │  ← NEW single entry
         │  (pipeline.main(): one DuckDB :memory: connection)   │
         └─────────────────────────────────────────────────────┘
                              │
   ingest_bronze(con) ────────┤  3 typed Bronze tables (row-count guards)
   transform.build_all(con) ──┤  keyed availability/util + staged ferry + derived fields
   model.build_all(con) ──────┤  5 Gold tables + dq_unmatched (join integrity asserts)
   export.write_gold(con) ────┤  data/gold/{5 tables}.parquet + .csv   ← currently test-only
   class_target.build + write ┤  data/gold/dim_class_target.parquet + .csv
   kpis.build_all(con) ───────┤  8 KPI tables + scalars (fail-fast asserts)
   kpis.write_kpi_snapshot ───┘  data/kpi/*.csv + kpi_values.json
                              │
                              ▼
        data/gold/*.parquet  +  data/kpi/*  +  deliverables/*.md
                              │
                              ▼
        Power BI Desktop (manual canvas) ── README documents this handoff
```

Note: `kpis.load_gold_views` reads Gold **from `data/gold/*.parquet`** when names are not already in-DB. If the orchestrator runs everything on one connection, the in-DB Gold tables are reused (no Parquet round-trip needed mid-run); the Parquet files still get written by `export.write_gold` for Power BI. `[VERIFIED: kpis.py load_gold_views idempotency logic, lines 50-77]`

### Recommended Project Structure (additions only)
```
fleet-analytics/
├── README.md                       # NEW — SHIP-01 deliverable
├── .gitattributes                  # NEW — pin *.csv eol=lf (kill CRLF churn)
├── pyproject.toml                  # EDIT — add [build-system]
└── src/fleet_analytics/
    └── pipeline.py                 # NEW — full-chain main() orchestrator
```

### Pattern 1: Full-chain orchestrator mirroring the existing `main()` idiom
**What:** A `pipeline.py` `main()` that opens one DuckDB connection, runs every `build_all`/`write_*` in dependency order, and closes in `finally` — exactly the shape of the existing `kpis.main()` and `class_target.main()`.
**When to use:** This is the single entry point Success Criterion 1 requires.
**Example:**
```python
# Pattern transcribed from src/fleet_analytics/kpis.py main() (lines 478-485)
# and class_target.py main() (lines 90-97) — VERIFIED this session.
import duckdb
from fleet_analytics import ingest, transform, model, export, kpis, class_target

def main() -> None:
    con = duckdb.connect()  # :memory:
    try:
        ingest.ingest_bronze(con)
        transform.build_all(con)
        model.build_all(con)
        export.write_gold(con)            # writes data/gold/*.parquet+csv
        class_target.build_class_target(con)
        class_target.write_class_target(con)
        kpis.build_all(con)               # asserts pooled-mean / 2020<2019 / max 7229
        kpis.write_kpi_snapshot(con)      # writes data/kpi/*
    finally:
        con.close()

if __name__ == "__main__":
    main()
```

### Pattern 2: README that aggregates, never restates, the canonical numbers
**What:** The README points to `deliverables/` and `data/kpi/kpi_values.json` as the source of truth; it states the *headline* facts (89.0% pooled availability, 5.8% underutilization, 2,080 matched / 6 unmatched, 209 nulls, row counts 4,614/2,086/272,529) and how to regenerate them, rather than maintaining a parallel copy that can drift.
**When to use:** SHIP-01 README content.

### Anti-Patterns to Avoid
- **Restating every KPI value in the README:** creates a fourth place numbers can drift. Quote only the headline figures and link to `kpi_definitions.md` / `kpi_values.json`.
- **Hardcoding a fresh "test results: N passed" count that goes stale:** state the command (`uv run pytest -q`) and the current result (76 passed) with the date, framed as "as of <date>", not as an eternal invariant.
- **Adding `pipeline.py` that re-reads Gold from Parquet mid-run:** unnecessary — the in-memory tables are already present on the connection; let `load_gold_views` short-circuit on existing names.
- **"Fixing" the trailing space in `City Vehicle Availability .csv`:** locked decision — `config.AVAIL_CSV` depends on it (Pitfall in `config.py` docstring).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reproducible env from a clean checkout | A `requirements.txt` + manual venv steps | `uv sync` from the committed `uv.lock` | Lockfile already exists; `uv sync` is the one-liner that gives byte-reproducible deps |
| Making `fleet_analytics` importable | `sys.path.append("src")` hacks in scripts | `[build-system]` so `uv sync` installs the package | Path hacks are brittle and don't fix `-m` from arbitrary cwd |
| Parquet/CSV export | Custom pandas `to_parquet` loops | Existing `export.write_gold` / `write_kpi_snapshot` DuckDB `COPY` | Already written, tested (roundtrip test proves type + 209-null fidelity) |
| Stable CSV line endings across OSes | Post-processing scripts to normalize EOL | `.gitattributes` `*.csv eol=lf` | git-native; one line; makes regeneration a clean no-op on Windows |

**Key insight:** Almost everything Ship needs already exists as tested module functions. The phase is *wiring + documenting*, not building.

## Runtime State Inventory

> This is a ship/packaging phase touching `pyproject.toml`, adding files, and reconciling a doc table. It is not a rename, but the "what runtime state isn't captured by file edits?" lens still applies.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Committed outputs `data/gold/*` (12 files) + `data/kpi/*` (9 files) are the shipped artifacts. Regenerating them via the new pipeline must be a **no-op diff** (values byte-identical). | After building `pipeline.py`, run it once and confirm `git status` is clean (only after `.gitattributes` is in place — see Pitfall 1). |
| Live service config | None — no external services. | None — verified (project is single-machine, in-process DuckDB). |
| OS-registered state | None — no schedulers/daemons. | None — verified. |
| Secrets/env vars | `FLEET_DATA_DIR` (optional override in `config.py`); no secrets. | README should mention `FLEET_DATA_DIR` is optional; default `.planning/data/`. `[VERIFIED: config.py line 24]` |
| Build artifacts | `.venv/`, `__pycache__/`, `*.pyc` exist on disk but are **gitignored and not tracked** `[VERIFIED: git ls-files shows none]`. Adding `[build-system]` will create an editable-install entry / possibly `*.egg-info` or `build/` — ensure `.gitignore` covers it. | Add `build/`, `*.egg-info/`, `dist/` to `.gitignore` when adding `[build-system]`. |

**Nothing found** in Live service config / OS-registered state — explicitly verified.

## Common Pitfalls

### Pitfall 1: Windows CRLF rewrites fake a "dirty" repo after pipeline regeneration
**What goes wrong:** Running the pipeline regenerates `data/kpi/*.csv` (and `data/gold/*.csv`); DuckDB `COPY` writes LF, but git on Windows warns "LF will be replaced by CRLF" and shows all CSVs as modified — **even though the values are byte-identical**. `[VERIFIED: regenerated availability_by_class.csv this session; the only diff was line endings, all numbers unchanged]`
**Why it happens:** No `.gitattributes`; git's `core.autocrlf` behavior on Windows normalizes line endings on checkout/commit.
**How to avoid:** Add `.gitattributes` with `*.csv eol=lf` (and `*.parquet binary`). Then regeneration is a clean no-op. The plan should include "run pipeline → `git status` clean" as a verification step **performed after** `.gitattributes` exists.
**Warning signs:** `git status` shows every CSV modified after a fresh pipeline run with no value changes.

### Pitfall 2: "Clean environment" claim that can't actually reproduce
**What goes wrong:** A README claims a reproducible pipeline, but the raw inputs aren't in the repo, so a fresh clone can't run.
**Why it doesn't apply here (but verify):** The three raw CSVs **are committed** under `.planning/data/` `[VERIFIED: git ls-files]`, so a clean clone + `uv sync` + run **does** work. The plan should still verify by running the full chain from a clean checkout (or at minimum after `uv sync`).
**How to avoid:** README "How to run" must reference the committed `.planning/data/` inputs (or `FLEET_DATA_DIR`).

### Pitfall 3: `-m fleet_analytics.pipeline` documented but not runnable
**What goes wrong:** CLAUDE.md documents `uv run python -m fleet_analytics.pipeline`, but it errors `ModuleNotFoundError`. `[VERIFIED: uv run python -m fleet_analytics.kpis → ModuleNotFoundError this session]`
**Why it happens:** No `[build-system]` → package not installed → not on runtime `sys.path` (pytest's `pythonpath=["src"]` is test-only).
**How to avoid:** Add `[build-system]`, `uv sync`, then confirm `uv run python -m fleet_analytics.pipeline` exits 0 and the documented invocation in CLAUDE.md/README is actually the one that works.
**Warning signs:** `uv run python -c "import fleet_analytics"` raises ModuleNotFoundError; `importlib.util.find_spec('fleet_analytics')` returns `None` `[VERIFIED this session: returned None]`.

### Pitfall 4: README test-count / KPI-number drift
**What goes wrong:** README hardcodes "X tests pass" or restates KPI values that later change, contradicting `kpi_values.json`.
**How to avoid:** State the *command* and a dated result ("76 passed, as of 2026-06-06"); link headline numbers to `kpi_definitions.md` / `kpi_values.json` rather than duplicating the full set.

### Pitfall 5: REQUIREMENTS traceability table out of sync with reality
**What goes wrong:** `.planning/REQUIREMENTS.md` traceability shows KPI-01 (Phase 3) and REPORT-01 (Phase 4) as "Pending" and the checkbox `[ ]`, but ROADMAP marks Phases 3 & 4 "Complete" and STATE shows 15/15 plans complete. `[VERIFIED: REQUIREMENTS.md lines 26/31/78/80 vs ROADMAP lines 17-18]`
**How to avoid:** Ship should reconcile the traceability table/checkboxes to match completed work (this is doc hygiene, part of "all deliverables confirmed self-consistent"). Confirm with the user whether KPI-01/REPORT-01 are truly complete before flipping — the work appears done (KPI tables, report_spec exist), so this is almost certainly stale checkbox drift, not missing work. `[ASSUMED — see A2]`

## Code Examples

### Adding a build-system to a `src`-layout uv project
```toml
# pyproject.toml — ADD (illustrative; planner verifies against current hatchling docs)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/fleet_analytics"]
```
`[ASSUMED]` — exact stanza should be confirmed against current hatchling docs at plan time (Context7 / pypi). The intent is verified; the precise keys are conventional.

### Self-consistency cross-check values (the canonical numbers — `data/kpi/kpi_values.json`)
```
overall_availability_rate   = 0.8899126...  → 89.0% pooled  [VERIFIED]
mean_of_class_means         = 0.8785522     → MUST differ from pooled (guard)  [VERIFIED]
overall_underutilization_rate = 0.0572      → "5.8%" headline  [VERIFIED]
availability_null_n         = 209           [VERIFIED]
availability_nonnull_n      = 4405          [VERIFIED]
light_duty_matched_n        = 2080          [VERIFIED]  (6 unmatched = 2086 - 2080)
ferry_sales_2019 = 1,249,725 > ferry_sales_2020 = 366,606  (COVID dip)  [VERIFIED]
ferry_sales_max  = 7229,  ferry_sales_median = 12.0   [VERIFIED]
ferry_lifetime_sales = 13,257,804,  redemptions = 13,076,317  [VERIFIED]
Row counts: availability 4,614 / utilization 2,086 / ferry 272,529  [VERIFIED: config.EXPECTED_ROWS]
```

## Self-Consistency Cross-Check Map (for SHIP-01 success criterion 4)

The README and the verification step should confirm these numbers agree across the seven deliverables and the snapshot. All were spot-checked this session and **do agree**:

| Number | Canonical source | Confirmed consistent in |
|--------|------------------|--------------------------|
| 89.0% pooled availability (0.8899) | `kpi_values.json` | report_spec, stakeholder_engagement, kpi_definitions/measures_spec (via per-class) `[VERIFIED]` |
| 5.8% underutilization (0.0572) | `kpi_values.json` | kpi_definitions, measures_spec, report_spec, requirements_approach, stakeholder_engagement, dq_report, data_dictionary `[VERIFIED]` |
| 2,080 matched / 6 unmatched | `kpi_values.json` + MODEL-03 tests | report_spec, measures_spec, requirements_approach `[VERIFIED]` |
| 209 nulls / 4,405 denom | `kpi_values.json` | dq_report, kpi_definitions, report_spec `[VERIFIED]` |
| Row counts 4,614/2,086/272,529 | `config.EXPECTED_ROWS` | requirements_approach, data_dictionary `[VERIFIED]` |

**One nuance to preserve, not "fix":** underutilization is "5.8%" two ways — `120/2,086 = 5.75%` (raw light-duty, in `data_dictionary`/`dq_report`) and `0.0572` over **2,080 matched** units (KPI layer). Both legitimately round to 5.8%; the denominators differ by design (raw vs join-matched). The README must not conflate them. `[VERIFIED: grep across deliverables]`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `requirements.txt` + manual venv | `uv sync` from `uv.lock` | uv mainstream 2024-2026 | One-command reproducible env; already adopted here |
| `setup.py` / flat layout | `pyproject.toml` `[build-system]` + `src` layout | PEP 517/621 era | Need the `[build-system]` to make the `src` package importable — the missing piece here |

**Deprecated/outdated:**
- The CLAUDE.md "Installation" / `What NOT to Use` sections are accurate; nothing to deprecate. The only doc fix is the traceability table (Pitfall 5).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | hatchling is the right `[build-system]` backend (vs uv's native `uv_build` or a `[tool.uv] package = true` flag) | Standard Stack / Code Examples | Low — any approach that makes `fleet_analytics` importable satisfies the goal; planner picks one and verifies `-m` runs |
| A2 | KPI-01 / REPORT-01 "Pending" in REQUIREMENTS.md is stale checkbox drift, not missing work | Pitfall 5 | Medium — if a requirement is genuinely unfinished, flipping the table would hide a gap. The artifacts (KPI tables, report_spec.md) exist, so this is very likely drift, but **confirm with the user before editing the table** |
| A3 | GitHub Actions CI is out of Phase-6 scope (deferred to EXT-02) | Standard Stack / Alternatives | Low — REQUIREMENTS.md explicitly lists CI under v2 EXT-02 and the brief marks it OPTIONAL |
| A4 | The exact hatchling `[tool.hatch.build.targets.wheel]` stanza | Code Examples | Low — verify against current hatchling docs at plan time; intent is solid |

## Open Questions

1. **Is `pipeline.py` the desired entry, or should the README document `uv run pytest` + per-module `main()`s instead?**
   - What we know: CLAUDE.md already prescribes `uv run python -m fleet_analytics.pipeline`; two `main()`s exist as precedent.
   - What's unclear: whether the user wants one orchestrator or is content documenting the existing module entries.
   - Recommendation: Build `pipeline.py` — it directly satisfies "single one-command invocation" and matches the documented path.

2. **Should regenerated outputs be re-committed, or treated as build artifacts?**
   - What we know: `data/gold/` and `data/kpi/` are currently committed (the shipped deliverable). README says `data/gold/` must contain the five Parquet files.
   - What's unclear: whether the plan re-commits a fresh regeneration or just verifies the committed ones reproduce.
   - Recommendation: Keep them committed (they ARE the deliverable for Power BI handoff); after `.gitattributes`, verify a fresh run is a no-op diff.

3. **KPI-01 / REPORT-01 completion (ties to A2)** — confirm with the user these are done before reconciling the table.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | One-command run, `uv sync` | ✓ | 0.10.4 | — |
| Python 3.12 | Runtime (pinned) | ✓ | 3.12 (via uv) | uv provisions it |
| DuckDB | Pipeline | ✓ | >=1.5,<2 (locked) | — |
| pytest | Test gate | ✓ | >=9.0.3 (76 passed) | — |
| Raw source CSVs | Clean-env reproduction | ✓ | committed in `.planning/data/` | `FLEET_DATA_DIR` override |
| git | `.gitattributes`, cleanup | ✓ | repo present | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — every dependency is present and verified this session.

## Validation Architecture

> nyquist_validation is enabled (config.json `workflow.nyquist_validation: true`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["src"]`) |
| Quick run command | `uv run pytest -q` |
| Full suite command | `uv run pytest -q` (suite is ~4.5s — quick == full) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SHIP-01 | Full suite green from clean env | smoke | `uv run pytest -q` (expect 76 passed) | ✅ (entire `tests/`) |
| SHIP-01 | One-command pipeline runs end-to-end exit 0 | integration | `uv run python -m fleet_analytics.pipeline` | ❌ Wave 0 — `pipeline.py` to be created |
| SHIP-01 | Pipeline regeneration is a no-op git diff | integration | run pipeline → `git status --porcelain` empty | ❌ Wave 0 — needs `.gitattributes` first |
| SHIP-01 | `data/gold/` has all 5 (+class_target) Parquet | smoke | assert 6 `.parquet` in `data/gold/` | ✅ files present; add a guard if desired |
| SHIP-01 | Package importable | smoke | `uv run python -c "import fleet_analytics"` exit 0 | ❌ Wave 0 — needs `[build-system]` |

### Sampling Rate
- **Per task commit:** `uv run pytest -q`
- **Per wave merge:** `uv run pytest -q` + `uv run python -m fleet_analytics.pipeline` + `git status` clean
- **Phase gate:** Full suite green AND one-command pipeline exits 0 AND clean-diff regeneration, before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `src/fleet_analytics/pipeline.py` — full-chain orchestrator (`main()` + `__main__`) covering SHIP-01 one-command criterion
- [ ] `[build-system]` in `pyproject.toml` + `uv sync` — makes `-m fleet_analytics.*` runnable
- [ ] `.gitattributes` (`*.csv eol=lf`, `*.parquet binary`) — clean-diff regeneration on Windows
- [ ] `README.md` — SHIP-01 documentation deliverable
- [ ] Optional: a tiny `tests/test_pipeline.py` smoke test asserting the orchestrator runs and produces the 6 Gold Parquet files

*(No new test framework needed — pytest is in place and green.)*

## Security Domain

> security_enforcement is not set to false in config.json (no `security_enforcement` key present → treat as enabled). This phase adds no network, auth, input-handling, or crypto surface.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (local single-machine pipeline) |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No multi-user access |
| V5 Input Validation | partial | The pipeline reads only **committed, trusted** CSVs; existing `COPY`/SQL interpolation uses **only internal `config` constants** (documented security note in `export.py`/`kpis.py`/`class_target.py`) — no external value reaches SQL. `[VERIFIED: export.py docstring lines 18-21]` |
| V6 Cryptography | no | No secrets, no crypto (`FLEET_DATA_DIR` is a path, not a secret) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via table/path interpolation in `COPY` f-strings | Tampering | Already mitigated — only internal `config.GOLD_TABLES` / `config.KPI_TABLE_CSVS` names and `config`-derived paths are interpolated; no user input. New `pipeline.py` must preserve this (call existing builders; introduce no new interpolation). `[VERIFIED: all COPY callers reviewed]` |
| Supply-chain (build backend addition) | Tampering | Add only a PyPA-official backend (hatchling) or uv's native backend; `uv.lock` pins everything else |

## Sources

### Primary (HIGH confidence — direct repo inspection / execution this session)
- `pyproject.toml`, `.gitignore`, `.python-version`, `uv.lock` — packaging state (no `[build-system]`; pytest-only `pythonpath`)
- `src/fleet_analytics/{config,export,kpis,class_target}.py` — module entry points, `main()` idiom, `load_gold_views` Parquet-read logic, security notes
- `tests/conftest.py` + `uv run pytest -q` → **76 passed in 4.49s** — actual test count
- `uv run python -m fleet_analytics.kpis` → **ModuleNotFoundError** — the import blocker (live-verified)
- `uv run python -c "find_spec('fleet_analytics')"` → **None** — package not importable
- `git ls-files`, `git status --porcelain`, `find` — committed CSVs, clean tree, zero scratch artifacts, no tracked `__pycache__`
- `data/kpi/kpi_values.json` — canonical numbers
- KPI CSV regeneration diff — proves CRLF-only churn (values byte-identical)
- `.planning/{REQUIREMENTS,ROADMAP,STATE,PROJECT}.md` — requirements, traceability drift
- `deliverables/*.md` (grep) — citations, pull date, licence, number consistency

### Secondary (MEDIUM)
- CLAUDE.md — documented `-m fleet_analytics.pipeline` invocation and stack rationale (the documented path currently does not run — Pitfall 3)

### Tertiary (LOW / to verify at plan time)
- Exact hatchling `[build-system]` stanza (A1/A4) — confirm against current hatchling docs

## Metadata

**Confidence breakdown:**
- Repo state / blockers: HIGH — every claim live-verified against the working tree this session
- Standard stack: HIGH — no new runtime deps; toolchain exercised
- Build-system fix specifics: MEDIUM — approach certain, exact TOML keys to confirm at plan time
- Self-consistency of deliverables: HIGH — numbers cross-checked and agree

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (stable; the only volatile item is the live test count, which is trivially re-checkable)
