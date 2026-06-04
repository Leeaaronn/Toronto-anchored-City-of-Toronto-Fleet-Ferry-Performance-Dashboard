# Phase 4: Power BI Report Specification - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 3 (1 markdown deliverable, 1 reference-dimension data artifact = .csv + .parquet, 1 pytest guard)
**Analogs found:** 3 / 3 (all exact or role-match)

This phase is a documentation-first deliverable. The bulk of the work — `deliverables/report_spec.md` — is prose/tables, so "patterns" here means the **header/sourcing/framing conventions** of the existing Phase-3 deliverable docs plus the **exact Gold column names** the spec must reference. The single code artifact (`dim_class_target.csv/.parquet`) and its guard map onto the existing DuckDB `COPY` export idiom and the existing dimension-guard test idiom.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `deliverables/report_spec.md` | deliverable doc (config/spec) | transform (Gold cols + measures_spec DAX → page-by-page spec) | `deliverables/measures_spec.md` (+ `kpi_definitions.md`, `dq_report.md`, `data_dictionary.md`) | exact (same doc family) |
| `data/gold/dim_class_target.csv` + `.parquet` | model / reference dimension | file-I/O (DuckDB `COPY ... TO`) | `src/fleet_analytics/export.py` `write_gold()` | role-match (COPY idiom; differs in source = a VALUES literal, not a Gold table) |
| `tests/test_class_target.py` (pytest guard) | test | file-I/O assert / CRUD-of-snapshot | `tests/test_dimensions.py` (+ `tests/test_export.py` roundtrip) | exact (committed-snapshot guard family) |

---

## CRITICAL: Column-Reference Reconciliation (D-04) — CONFIRMED against `data/gold/*.csv`

These are the **verbatim header rows** of the committed Gold CSVs (read 2026-06-04). The spec must reference ONLY these names. This table is load-bearing for the planner — `measures_spec.md` uses Power-BI-friendly placeholders that do **not** all match.

| Gold table | Actual column headers (verbatim, in order) |
|------------|---------------------------------------------|
| `fact_vehicle` | `_id, UNIT_NO, YEAR, MAKE, MODEL, CATEGORY, CAT_DESC, UNIT_TYPE, CATEGORY_CLASS, CAT_GRP, IN_SERV_DT, STATUS_DESC, CLASS2, HIGH_PRIORITY, OWNER_DIVISION, REF_DIVISION, SEASONAL, AVAILABILITY_YTD, unit_key_int, fleet_age, Utilization, specialized_units, REF_USING_DIV, owner_division_key, using_division_key` |
| `fact_ferry` | `_id, Timestamp, Redemption Count, Sales Count, ts_15, season, daypart, day_of_week, is_weekend, sales_redemption_gap` |
| `dim_date` | `date_key, year, month, month_name, day, day_of_week, is_weekend, quarter` |
| `dim_time` | `time_key, time_of_day, hour, minute` |
| `dim_division` | `division_key, division_name` |

### Confirmed D-04 fixes (planner must correct the spec, not blind-copy `measures_spec.md`)

1. **`dim_time` hour column is `hour`** (CONFIRMED) — not `hour_of_day`. Time-of-day label is `time_of_day`; join surrogate is `time_key`; also `minute`.
2. **`dim_date` has NO bare `date` column** (CONFIRMED). Columns: `date_key, year, month, month_name, day, day_of_week, is_weekend, quarter`. **"Mark as Date Table" date column = `date_key`**, and all DATEADD/time-intelligence DAX must reference `dim_date[date_key]`.
3. **`fact_ferry` measure columns are `Sales Count` / `Redemption Count`** (CONFIRMED, with the embedded space) plus `day_of_week`, `season`, `daypart`, `is_weekend`, `sales_redemption_gap`, `ts_15`, `Timestamp`. DAX must bracket the spaces: `fact_ferry[Sales Count]`.
4. **`fact_vehicle` keys** (CONFIRMED): availability = `AVAILABILITY_YTD`, utilization = `Utilization`, specialized flag = `specialized_units` (lowercase), asset-class raw = `CATEGORY_CLASS`, **vehicle-type = `UNIT_TYPE`**. Division foreign keys are `owner_division_key` and `using_division_key` (role-playing — see Relationships below).

### ⚠ HIGH-PRIORITY DISCREPANCY the planner MUST resolve — `dim_class_target` join key

CONTEXT.md D-03 says `dim_class_target` joins `fact_vehicle` "on the asset-class key" and labels it "`category_class → target`". **This is not how the Phase-3 KPI layer actually joins targets.** Verified in `src/fleet_analytics/kpis.py`:

- `fact_vehicle.CATEGORY_CLASS` contains **granular codes** (`CLASS1, CLASS2, ... CLASS8, APPARATUS, ATTACHMENT, BOAT, CONSTRUCT, FACILITY, GROUND, LIFTING, ROADMAIN, TRAILER, TRAM, WINTERMAIN`) — **19 distinct values, NOT the 5 audit labels.**
- The audit labels (Light/Medium/Heavy/Off-Road/Other) live one level up via **`UNIT_TYPE`** (`LIGHT DUTY, MEDIUM DUTY, HEAVY DUTY, OFF-ROAD, OTHER`), mapped by `config.UNIT_TYPE_TO_CLASS`.
- The KPI SQL joins targets with `JOIN ... ON fv.UNIT_TYPE = ct.unit_type` (kpis.py line 125 / 178), **NOT** on `CATEGORY_CLASS`.

**Implication for the spec/plan:** `dim_class_target` must relate to `fact_vehicle` on a key that resolves to the 5 audit labels. The cleanest options the planner should choose between and document:
- (a) Make `dim_class_target` a two-column bridge `UNIT_TYPE → (class_label, target)` (10/19 → 5 mapping via `UNIT_TYPE`), relating on `fact_vehicle[UNIT_TYPE]` (matches kpis.py exactly); or
- (b) Add a derived `asset_class` label column to `fact_vehicle` first — out of scope for Phase 4 (would touch the model), so prefer (a).

Do **not** spec a `dim_class_target[category_class]` ↔ `fact_vehicle[CATEGORY_CLASS]` single-column relationship — the cardinalities don't line up (19 raw codes vs 5 targets) and it contradicts the validated KPI join.

---

## Pattern Assignments

### `deliverables/report_spec.md` (deliverable doc, transform)

**Analog:** `deliverables/measures_spec.md` (primary), with header/footer conventions shared across `kpi_definitions.md`, `dq_report.md`, `data_dictionary.md`.

**Deliverable-doc header convention** (`measures_spec.md` lines 1-8 / `kpi_definitions.md` lines 1-8): every deliverable opens with a `# Title — Phase N <LAYER> (REQ-ID)` H1, then a bold metadata block, then a blockquote "how to read" note. Copy this exact shape:

```markdown
# Power BI Report Specification — Phase 4 (REPORT-01)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The page-by-page build contract between the Gold layer (`data/gold/*.parquet`) and the manually-authored Power BI canvas — model setup, relationships, theme, slicers, per-visual DAX (mapped from `deliverables/measures_spec.md`), visual types, and PDF-export layout.
**Method:** Every visual cites the column/table names confirmed in the Gold output and the SQL validation value it must reproduce (carried from `data/kpi/kpi_values.json` via `measures_spec.md`). Scope split (locked): GSD produces this text spec; **no `.pbix` / PBIP / TMDL is generated** — the canvas is authored manually.
**Snapshot pull date:** **2026-06-02**.

> **How to read this spec.** [Grouped page → visual; each visual carries: visual type · fields (real Gold columns) · DAX measure · SQL validation value · DQ footnote.] ...
```

**Cross-doc linking convention** (`measures_spec.md` line 5, `kpi_definitions.md` line 8): deliverables relative-link each other inline — `` [`kpi_definitions.md`](kpi_definitions.md) ``, `` [DQ report](dq_report.md) ``. The report spec should link `measures_spec.md`, `kpi_definitions.md`, `dq_report.md`, `data_dictionary.md`.

**Recurring locked-framing callouts** to repeat verbatim (these phrases appear across all Phase-3 docs and must stay consistent):
- Availability measures "**exclude the 209 NULL `AVAILABILITY_YTD` values** (denominator **4,405**)."
- Disposal cross-measure is a "**screening list for SME review, never a disposal decision**."
- Targets are "**audit-cited, never recalculated**" (AG 2019.AU2.2 / May 2023 FSD General Government Committee report).
- Underutilization "**5.8% computed vs ~14% cited**" reconciliation note (AG 2019.AU2.3).

**Per-visual table column convention** (mirror `measures_spec.md`'s `Measure name | DAX | SQL validation value | Notes`): the report spec's per-visual rows should carry `Visual | Type | Fields (Gold cols) | DAX measure | SQL validation value | DQ footnote`. The DAX + SQL-validation-value cells are transcribed from `measures_spec.md` (A1–A5, B1–B5), NOT re-derived.

**Source/validation values already in `measures_spec.md`** the spec maps onto pages (do not re-estimate): pooled availability **0.8899**; by-class rates Light **0.9149** / Medium **0.8612** / Heavy **0.7948** / Off-Road **0.8882** / Other **0.9337**; gap-to-target signs; exception list **1,734** rows; disposal screen **34**; underutilization **0.0572**; matched **2,080**; lifetime sales **13,257,804** / redemptions **13,076,317**.

---

### `data/gold/dim_class_target.csv` + `data/gold/dim_class_target.parquet` (reference dimension, file-I/O)

**Analog:** `src/fleet_analytics/export.py` `write_gold()` (lines 31-46) — the established DuckDB COPY-to-Parquet+CSV idiom.

**Core COPY idiom** (export.py lines 43-46) — copy this exact two-statement-per-table form (Parquet primary, CSV readable secondary):

```python
for t in config.GOLD_TABLES:
    p = (config.GOLD_DIR / t).as_posix()
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.csv' (FORMAT CSV, HEADER)")
```

**Type-fidelity contract** (export.py docstring lines 1-22): Parquet is **primary** (type-preserving), CSV is the **readable secondary**; for `dim_class_target` the two columns are a VARCHAR class key and an INTEGER `target` — both survive COPY natively. Use `(FORMAT CSV, HEADER)` so the CSV header row is written (consistent with every other Gold CSV).

**Security note to preserve** (export.py lines 18-21): only internal config constants are interpolated into the COPY f-string — no user value. For `dim_class_target`, the values come from `config.ASSET_CLASS_TARGETS` / `config.UNIT_TYPE_TO_CLASS`, so the same "no external value reaches SQL" guarantee holds.

**Source of the 5 target values — `config.py` lines 102-119 (NEVER recalculate):**

```python
ASSET_CLASS_TARGETS: dict[str, int] = {
    "Light": 95, "Medium": 92, "Heavy": 85, "Off-Road": 88, "Other": 90,
}
UNIT_TYPE_TO_CLASS: dict[str, str] = {
    "LIGHT DUTY": "Light", "MEDIUM DUTY": "Medium", "HEAVY DUTY": "Heavy",
    "OFF-ROAD": "Off-Road", "OTHER": "Other",
}
```

**Build idiom for the literal relation** — the cleanest analog for producing `dim_class_target` from config (not from a Gold table) is the existing `_class_targets_relation()` helper in `kpis.py` (lines 79-94), which builds a `VALUES (?, ?, ?)` table bound from config and joins on `UNIT_TYPE`. Reuse that shape: register a VALUES relation (`unit_type, class_label, target`) into DuckDB, then `COPY` it out. This keeps the join key consistent with the validated KPI layer (`fact_vehicle.UNIT_TYPE`). Planner decides whether the committed table is keyed by `UNIT_TYPE` (10-row bridge) or by `class_label` (5-row dim with a separate `UNIT_TYPE→class` map) — document the relationship cardinality either way.

**Placement convention** (config.py line 79): `GOLD_DIR = PROJECT_ROOT / "data" / "gold"`. New files land alongside the other Gold tables. Consider whether to add `"dim_class_target"` to `config.GOLD_TABLES` (line 82) — note that list currently drives the row-count guard (`GOLD_EXPECTED_ROWS`, lines 86-92) and `export.write_gold`, so adding it there wires it into existing tests; planner should decide and update `GOLD_EXPECTED_ROWS` accordingly.

---

### `tests/test_class_target.py` (pytest guard, file-I/O assert)

**Analog:** `tests/test_dimensions.py` (lines 14-39) for the in-DB row/value guard; `tests/test_export.py` (lines 40-100) for the re-read-the-exported-file roundtrip guard.

**Simple dimension-guard idiom** (test_dimensions.py lines 33-39) — assert exact row count + value set on the `gold` fixture:

```python
def test_dim_division_conformed(gold) -> None:
    total, distinct = gold.execute(
        "SELECT COUNT(*), COUNT(DISTINCT division_key) FROM dim_division"
    ).fetchone()
    assert total == 21
    assert total == distinct
```

For `dim_class_target` the analogous guard asserts **5 distinct class labels** (or the chosen key) and the **exact 5 target values** (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90), e.g. a `@pytest.mark.parametrize` over the 5 `(class_label, target)` pairs — table-driven, mirroring the parametrized DQ-guard style described in CLAUDE.md.

**Re-read-the-exported-file roundtrip idiom** (test_export.py lines 40-79) — if the guard should assert the committed file (not just the in-DB table), copy this pattern: build via the `gold` fixture, write, then open a **second `:memory:` connection in `try/finally`** and `read_parquet(...)` / `read_csv(...)` the exported file:

```python
def test_ten_files_written(gold) -> None:
    export.write_gold(gold)
    for t in config.GOLD_TABLES:
        assert (config.GOLD_DIR / f"{t}.parquet").exists()
        assert (config.GOLD_DIR / f"{t}.csv").exists()
```

```python
rd = duckdb.connect(":memory:")
try:
    target = rd.execute(
        "SELECT target FROM read_parquet("
        f"'{(config.GOLD_DIR / 'dim_class_target.parquet').as_posix()}') "
        "WHERE class_label = 'Heavy'"
    ).fetchone()[0]
finally:
    rd.close()
assert target == 85
```

**Fixture convention** (conftest.py lines 14-38): tests depend on the session-scoped `gold` fixture, which runs `transform.build_all → model.build_all → kpis.build_all` once on a shared `:memory:` connection. If `dim_class_target` is built by a new builder, wire it into the `gold` fixture's build chain (the docstring at conftest.py lines 24-32 documents exactly how prior phases added a build line — follow that precedent).

**Path-helper convention** (test_export.py lines 24-37, paths via `config.GOLD_DIR / name` + `.as_posix()`): reuse `(config.GOLD_DIR / "dim_class_target.parquet").as_posix()` rather than hard-coding paths. **Pitfall (test_export.py line 12 + line 66):** alias null/count columns as `null_ct` style names, never `nulls`/`both` (reserved-word collision noted in the codebase).

---

## Shared Patterns

### Deliverable-doc house style
**Source:** `deliverables/measures_spec.md` lines 1-8, `deliverables/kpi_definitions.md` lines 1-8
**Apply to:** `report_spec.md`
H1 `# Title — Phase N (REQ-ID)` → bold `**Project:** / **Scope:** / **Method:** / **Snapshot pull date:**` block → `>` "how to read" blockquote → `---` → grouped sections with markdown tables. Inline relative links between deliverables. Bold the load-bearing numbers.

### Audit-cited-never-recalculated framing
**Source:** `config.py` lines 94-108, repeated in all Phase-3 deliverables
**Apply to:** `report_spec.md` (target line, benchmarks) + `dim_class_target` provenance note
Targets (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90) cite AG 2019.AU2.2 / May 2023 FSD report; never recomputed. Open Government Licence – Toronto.

### DuckDB COPY type-fidelity export
**Source:** `src/fleet_analytics/export.py` lines 31-46
**Apply to:** `dim_class_target.csv` + `.parquet`
`COPY (SELECT ...) TO '{path}.parquet' (FORMAT PARQUET)` then `... '{path}.csv' (FORMAT CSV, HEADER)`. Parquet primary, CSV readable secondary. Only config-sourced values in the SQL string.

### Committed-snapshot falsifiable guard
**Source:** `tests/test_dimensions.py` lines 14-39, `tests/test_export.py` lines 40-100
**Apply to:** `tests/test_class_target.py`
Assert exact row count + exact values on the `gold` fixture; optionally re-read the exported Parquet/CSV via a second `:memory:` connection in `try/finally`. Parametrize the 5 target rows.

### Config as single source of truth
**Source:** `config.py` lines 79-136
**Apply to:** `dim_class_target` builder + any new GOLD_TABLES / GOLD_EXPECTED_ROWS entry
Never inline filenames, paths, or target values; bind from `config.ASSET_CLASS_TARGETS` / `UNIT_TYPE_TO_CLASS` / `GOLD_DIR`. The `_class_targets_relation()` helper (kpis.py lines 79-94) is the canonical "config dict → bound VALUES relation" idiom.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All three artifacts have strong existing analogs. The only novel content is *prose* (theme JSON block, slicer plan, PDF layout, page narratives) which is spec text, not code — no codebase analog needed; the planner uses CONTEXT.md D-01–D-08 + RESEARCH.md for those. |

---

## Metadata

**Analog search scope:** `deliverables/`, `src/fleet_analytics/`, `tests/`, `data/gold/`
**Files scanned / read:** export.py, config.py, kpis.py (targeted grep), conftest.py, test_export.py, test_dimensions.py, measures_spec.md (head), kpi_definitions.md (head); all 5 Gold CSV header rows; distinct `CATEGORY_CLASS`/`UNIT_TYPE` values queried live from `fact_vehicle.parquet`
**Pattern extraction date:** 2026-06-04
