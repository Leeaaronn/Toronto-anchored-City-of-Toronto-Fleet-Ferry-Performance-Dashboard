# Phase 3: KPI Layer & Measures Spec - Pattern Map

**Mapped:** 2026-06-02
**Files analyzed:** 6 (1 new module, 1 config modify, 1 snapshot artifact set, 1 new test module, 2 new deliverable docs)
**Analogs found:** 6 / 6 (all exact or strong role-matches inside this repo)

> No RESEARCH.md for this phase — research was skipped. All patterns below are extracted from real repo code, so the planner can instruct the executor to mirror exact conventions rather than invent new ones. The KPI compute layer is a direct continuation of the established DuckDB SQL-first `ingest → transform → model → export` layer.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/fleet_analytics/kpis.py` | service (compute layer) | transform / batch aggregation | `src/fleet_analytics/model.py` (+ `transform.py`, `export.py`) | exact (same layer family) |
| `src/fleet_analytics/config.py` (MODIFY) | config | constants | `config.py` itself (existing `REFERENCE_YEAR` / `GOLD_*` blocks) | exact (in-file pattern) |
| KPI snapshot: `kpi_values.json` + per-table CSVs | output artifact | file-I/O (write) | `src/fleet_analytics/export.py` (`COPY ... TO`); `profile.py` (`.df().to_dict()` → JSON) | role-match (split JSON+CSV is new, idioms exist) |
| `tests/test_kpis.py` | test | request-response (assert) | `tests/test_join_integrity.py`, `tests/test_derived_fields.py`, `tests/conftest.py` | exact |
| `deliverables/kpi_definitions.md` | doc | n/a | `deliverables/dq_report.md` | exact |
| `deliverables/measures_spec.md` | doc | n/a | `deliverables/data_dictionary.md` (table-per-section) + `dq_report.md` | role-match |

---

## Pattern Assignments

### `src/fleet_analytics/kpis.py` (compute service, batch aggregation)

**Analog:** `src/fleet_analytics/model.py` (primary), `transform.py` and `export.py` (secondary).

**Module docstring + imports pattern** (`model.py` lines 1-37 / `transform.py` 26-30):
```python
"""<One-line layer summary>: Gold Parquet -> KPI tables/scalars (KPI-01).

<Locked decisions encoded here block — name the D-01..D-11 rules and the
209-NULL exclusion / pooled-mean / 2020<2019 guards inline, exactly like
model.py lists its locked decisions and Pitfalls.>
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config
```
Every module in this layer opens with `from __future__ import annotations`, imports `duckdb`, and imports `config` as `from fleet_analytics import config`. Match it.

**Per-KPI builder pattern** — one function per KPI, single SQL statement on the shared `con`, type-hinted `(con: duckdb.DuckDBPyConnection)` (`model.py` lines 45-66, 69-95). Use `con.execute(sql).df()` to return a DataFrame for table-valued KPIs (the `.df()` idiom is established in `profile.py` line 49). SQL lives as inline triple-quoted strings (D-50 discretion: inline is the house style — see every builder in `model.py`/`transform.py`/`ingest.py`).

**Bind constants via `?`, never inline** (`transform.py` lines 40-49 binds `config.REFERENCE_YEAR`):
```python
con.execute(
    """
    CREATE OR REPLACE TABLE stg_availability AS
    SELECT *, (? - YEAR) AS fleet_age
    FROM bronze_availability
    """,
    [config.REFERENCE_YEAR],
)
```
The asset-class targets (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90) belong in `config.py` and should be bound/joined in, not hard-coded in the SQL string.

**209-NULL exclusion — the load-bearing rule** (encoded across `transform.py` 22-23, `model.py` 29-30, asserted in `test_derived_fields.py` 64-69): NEVER `COALESCE`/fill `AVAILABILITY_YTD`. Availability rate KPIs must use the 4,405 non-null denominator. DuckDB `AVG(AVAILABILITY_YTD)` ignores NULL automatically; the **pooled per-vehicle mean** (D-13, CONTEXT line 13) is `AVG(AVAILABILITY_YTD)` over the row population — NOT `AVG` of per-class averages. Write it as the pooled grand-total and assert it.

**`build_all` orchestrator with fail-fast assertion loop** (`model.py` lines 169-193) — the signature pattern to copy:
```python
def build_all(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    build_dim_division(con)
    build_fact_vehicle(con)
    # ...
    for table, expected in config.GOLD_EXPECTED_ROWS.items():
        got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert got == expected, (
            f"{table}: expected {expected} Gold rows, got {got} "
            "— a join, filter, or spine regression crept in"
        )
    return con
```
`kpis.py` should expose an equivalent orchestrator that builds all KPI tables/scalars on `con` and returns `con`. The fail-fast `assert ... f"...— regression crept in"` style (regression in code, not only pytest) is the house convention — reuse it for the pooled-mean bounds and the 2020<2019 check at compute time.

**Reading the Gold input** — this phase reads `data/gold/*.parquet` (CONTEXT lines 66-68). Two valid analogs:
- Via the `gold` fixture (in-memory tables already built; tests use this — `conftest.py` lines 22-35).
- Via DuckDB `read_parquet('{config.GOLD_DIR / "fact_vehicle"}.parquet')` for a standalone compute run — the path-building idiom is `(config.GOLD_DIR / t).as_posix()` from `export.py` line 44 / `test_export.py` lines 24-37.

---

### `src/fleet_analytics/config.py` (config, constants) — MODIFY

**Analog:** the existing Phase-2 constants block in the same file (lines 68-92).

**Pattern to mirror** (lines 76, 82-92): typed module-level constants with a comment block citing the decision/source. Add the asset-class targets and KPI thresholds in the same style:
```python
# --- Phase-3 KPI-layer constants --------------------------------------------
# Asset-class availability targets (audit-cited, NEVER recalculated — AG
# 2019.AU2.2 / May 2023 FSD report). A unit is "below threshold" when
# AVAILABILITY_YTD < its class target (D-01). gap_to_target = actual - target (D-03).
ASSET_CLASS_TARGETS: dict[str, int] = {
    "Light": 95, "Medium": 92, "Heavy": 85, "Off-Road": 88, "Other": 90,
}
```
Use the existing `dict[str, int]` typing, the `# --- section ---` divider, and the inline "cited, never recalculated" justification comment exactly as `REFERENCE_YEAR` (lines 69-76) documents its 2023 choice. `REFERENCE_YEAR = 2023` is already present (line 76) — read it as the constants pattern, do not duplicate. Confirm the exact asset-class label strings against the real `UNIT_TYPE` / class values in `fact_vehicle` before locking the dict keys.

---

### KPI snapshot artifact: `kpi_values.json` + per-table CSVs (output, file-I/O)

**Analog:** `export.py` (`COPY ... TO` for tabular output) + `profile.py` line 49 (`.df().to_dict(orient="records")` for structured Python → JSON).

**Per-table CSV write idiom** (`export.py` lines 41-46) — the established committed-artifact pattern:
```python
config.GOLD_DIR.mkdir(parents=True, exist_ok=True)
for t in config.GOLD_TABLES:
    p = (config.GOLD_DIR / t).as_posix()
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.csv' (FORMAT CSV, HEADER)")
```
Mirror this for each table-valued KPI (`availability_by_class.csv`, `availability_by_division.csv`, `exception_list.csv`, `underutilization_by_division.csv`, `ferry_yoy.csv`, `ferry_heatmap.csv`, `sales_redemption_gap.csv`). Define the file list as a `config` constant (parallel to `GOLD_TABLES`) and the output dir as a `config.Path` constant (parallel to `GOLD_DIR`) — D-05 discretion leaves dir choice to planner (`deliverables/` vs new `data/kpi/`); keep it reviewable in git. **Security note from `export.py` lines 18-21 applies**: only interpolate internal `config` table/path names into the f-string SQL, never external values.

**Scalars → JSON idiom** (no JSON writer exists yet, but the build block is `profile.py` line 49): compute scalars/benchmark comparisons into a flat/nested dict via `con.execute(sql).fetchone()` or `.df().to_dict(orient="records")`, then `json.dump`. Key structure is planner's call (D-05 discretion) but should hold: headline pooled availability rate, by-class-vs-target + gap, underutilization rates (incl. 5.8% current), ferry totals/YoY/distribution stats (max≈7229/median≈12). Keep it flat-keyed for direct assertion — `profile.py` docstring lines 10-11 establishes "returned dict is keyed for direct assertion" as the house pattern, and the deliverable docs transcribe these values.

---

### `tests/test_kpis.py` (test, assert-then-guard)

**Analog:** `tests/test_join_integrity.py` (scalar-guard idiom), `tests/test_derived_fields.py` (parametrized + null-preservation), `tests/conftest.py` (fixtures).

**Fixture reuse** (`conftest.py` lines 22-35): use the session-scoped `gold` fixture — it builds Bronze→staging→Gold once on an in-memory `con`. KPI tests either query the in-memory Gold tables directly or read the exported snapshot. Plan should add a `kpis.build_all(con)` line to the `gold` fixture chain OR add a new fixture that depends on `gold` then runs the KPI build (exactly how `gold` depends on `con` — `conftest.py` 22-35).

**Scalar-guard helper + exact-value assert** (`test_join_integrity.py` lines 17-26):
```python
def _scalar(con, sql: str) -> int:
    return con.execute(sql).fetchone()[0]

def test_<kpi>(gold) -> None:
    """<one-line contract>."""
    value = _scalar(gold, "SELECT ... FROM fact_vehicle ...")
    assert value == <snapshot_value>
```
Copy this exactly for the **canonical pooled-mean grand-total guard** (assert the pooled rate is in [0,1] AND equals the snapshot value AND is NOT the mean-of-class-means — assert the two differ), the **2020 < 2019 YoY guard** (`assert vol_2020 < vol_2019`), and the **distribution sanity checks** (`assert sales_max == 7229`, `assert median ≈ 12`).

**209-NULL exclusion guard** (`test_derived_fields.py` lines 64-69 — copy the count idiom):
```python
null_ct = gold.execute(
    "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) FROM fact_vehicle"
).fetchone()[0]
assert null_ct == 209   # 4,405 non-null denominator; never imputed
```

**Parametrized multi-value guards** (`test_derived_fields.py` lines 75-110) — for asserting each asset class's by-class rate/gap against its snapshot value, use `@pytest.mark.parametrize` table-driven cases with `ids=[...]`, exactly the established style. Note: `import pytest` is placed near the parametrized tests with `# noqa: E402` (line 72) — match that local convention if mirroring the file layout.

**Snapshot-as-contract**: per D-06, the committed snapshot values ARE the regression contract — assert the exported JSON/CSV values match the live compute, the same way `test_export.py` (lines 40-100) re-reads exported files in a second `:memory:` connection (`try/finally`, `rd.close()`) to prove the artifact matches the source.

---

### `deliverables/kpi_definitions.md` (doc)

**Analog:** `deliverables/dq_report.md`.

**Structure to mirror** (`dq_report.md` lines 1-16, 84-90): titled header block (`**Project:** / **Scope:** / **Method:** / **Snapshot pull date:**`), a "Why this report exists" callout, numbered `## N.` sections, and Markdown tables for figures. Crucially, `dq_report.md` distinguishes **computed** vs **cited** figures inline (lines 11-16, 84-89) — apply the same for KPI definitions: plain-language formula + audit benchmark (cited, AG 2019.AU2.2/.3), and the **5.8% (computed) vs ~14% (cited audit) reconciliation note** — the exact reconciliation table already exists at `dq_report.md` lines 84-90; extend/cross-reference it, do not recompute thresholds (CONTEXT lines 38, 73-74). Close with the `## Sources & Licence` block verbatim from `data_dictionary.md` lines 84-90 / `dq_report.md`.

---

### `deliverables/measures_spec.md` (doc — build contract for Phase 4)

**Analog:** `deliverables/data_dictionary.md` (section-per-entity, table-per-section) blended with `dq_report.md` header/sourcing.

**Structure** (D-08, CONTEXT line 40): grouped by **domain → KPI** — a Fleet Maintenance `## ` section and a Ferry `## ` section, each KPI a `### ` subsection with a table whose columns are `Measure name | DAX | SQL validation value | Notes`. The table-per-section idiom is exactly `data_dictionary.md` (lines 16-41 `## 1.` table, 45-59 `## 2.` table, 63-73 `## 3.` table). Each "SQL validation value" cell cites the value persisted in the KPI snapshot (`kpi_values.json` / the per-table CSVs) so every Phase-4 DAX measure is falsifiable against ground truth (CONTEXT lines 96, 106). DAX measure naming is planner/spec-author's call (D-49 discretion) — keep it consistent and Power-BI-friendly. Reuse the `## Sources & Licence` footer.

---

## Shared Patterns

### DuckDB SQL-first layer module shape
**Source:** `model.py`, `transform.py`, `ingest.py`, `export.py` (all four follow it)
**Apply to:** `kpis.py`
```python
from __future__ import annotations
import duckdb
from fleet_analytics import config
# one private/public builder per output, single CREATE OR REPLACE / SELECT / COPY per fn,
# all on the shared (con: duckdb.DuckDBPyConnection); a build_all(con) orchestrator
# with a fail-fast assertion loop; returns con for chaining.
```

### 209-NULL "exclude, never impute" rule
**Source:** `transform.py` 22-23, `model.py` 29-30, `config.py` 9-12, asserted `test_derived_fields.py` 64-69 / `test_export.py` 82-100
**Apply to:** every availability-rate KPI in `kpis.py` and its guard in `tests/test_kpis.py`
```python
# NEVER COALESCE/fill AVAILABILITY_YTD. Rate denominator = 4,405 non-null rows.
# Regression guard: COUNT(*) - COUNT(AVAILABILITY_YTD) == 209
```

### Constants in config.py, bound via `?`
**Source:** `config.py` 68-92 (constants), `transform.py` 40-49 (`?`-binding)
**Apply to:** asset-class targets + KPI thresholds (config), and every KPI SQL that references them

### Fail-fast assert-then-pytest-guard
**Source:** `model.py` 186-191 (in-code assert loop) + `test_join_integrity.py` 17-26 (`_scalar` pytest guard)
**Apply to:** the pooled-mean grand-total, 2020<2019 YoY, and distribution (7229/12) checks — assert at compute time AND in `tests/test_kpis.py`

### Path-building + dir-ensure for committed artifacts
**Source:** `export.py` 41-46 (`config.GOLD_DIR.mkdir(parents=True, exist_ok=True)`, `(config.X_DIR / t).as_posix()`, `COPY (...) TO '...'`)
**Apply to:** writing `kpi_values.json` + the per-table KPI CSVs

### Deliverable doc skeleton
**Source:** `dq_report.md` 1-16 + `data_dictionary.md` 84-90 (header block, computed-vs-cited inline flags, `## Sources & Licence` footer)
**Apply to:** both new `deliverables/*.md`

---

## No Analog Found

None. Every Phase-3 file maps to a real, recent repo analog. The only genuinely new idiom is the **scalars → `kpi_values.json` writer** (no prior JSON output), but its two building blocks exist: `profile.py` line 49 (`.df().to_dict(orient="records")` / dict-for-assertion) and `export.py` (dir-ensure + path-building). Treat it as `json.dump` over a `profile.py`-style flat dict.

---

## Metadata

**Analog search scope:** `src/fleet_analytics/` (8 modules), `tests/` (9 files), `deliverables/` (2 docs)
**Files scanned:** 12 read in full/targeted + grep over `profile.py`
**Pattern extraction date:** 2026-06-02
