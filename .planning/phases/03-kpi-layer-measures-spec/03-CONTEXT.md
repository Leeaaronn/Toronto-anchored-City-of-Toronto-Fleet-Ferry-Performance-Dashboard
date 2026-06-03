# Phase 3: KPI Layer & Measures Spec - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Compute **every Domain A (fleet maintenance) and Domain B (ferry) KPI authoritatively in SQL/Python** over the Phase 2 Gold Parquet, cross-checked against audit benchmarks, and persist those ground-truth values. Produce **two deliverable docs** — a KPI definitions doc (plain-language formulas + benchmarks) and a DAX-ready measures spec (copy-paste DAX paired with each KPI's SQL validation value) — including the pooled-mean grand-total guard and the 5.8%-vs-14% reconciliation note.

Discussion clarified **HOW** to compute, persist, threshold, and document these KPIs. The following are already **locked by the roadmap** and are NOT open decisions:
- The full KPI list — Domain A: overall availability rate, availability by asset class vs target + gap-to-target, exception list of critically low units, underutilization rate overall and by using division, specialized split, disposal-candidate cross-measure; Domain B: lifetime/period totals, YoY trend, seasonality profile, day-of-week × hour-of-day heatmap, sales-to-redemption gap, distribution stats (max ≈ 7,229 / median ≈ 12).
- Overall availability = **pooled per-vehicle mean** (not mean-of-class-means), all rates in [0,1], asserted by a canonical grand-total test.
- A test asserting **2020 < 2019** ferry volume (COVID dip present).
- Two deliverable docs pairing each KPI with copy-paste DAX + its SQL validation value, including the 5.8% vs 14% reconciliation note.

**Out of scope (later phases):** the Power BI report canvas / page layout / relationships / slicers / theme (Phase 4); the two narrative deliverables (Phase 5). No `.pbix`/PBIP/TMDL.

</domain>

<decisions>
## Implementation Decisions

### Thresholds (audit-grounded)
- **D-01:** A single coherent threshold rule governs the whole phase — a unit is **"below threshold" when `AVAILABILITY_YTD` < its asset-class audit target** (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90). Class-fair: a heavy-duty unit is judged against the heavy-duty bar, not a light-duty bar. This drives both the **"% below threshold"** metric and the **named exception list** of critically low units (rank/sort below-target units for the list).
- **D-02:** The **disposal-candidate cross-measure** = `below class target` (the same D-01 rule) **AND** the pre-classified `Underutilized` flag. Since disposal candidates are by definition light-duty (utilization present), the availability leg is effectively `< 95` for nearly all. One threshold rule across exception list, % metric, and disposal screen — no second floor. The disposal-candidate output is framed as a **screening list for SME review**, not a decision.
- **D-03:** `gap-to-target` is signed `actual − target` (negative = below benchmark). Mechanical; no judgment.

### KPI compute artifact & value capture
- **D-04:** Compute KPIs in a **`kpis.py` module** (DuckDB SQL over the Gold Parquet in `data/gold/`, returning DataFrames), consistent with the existing `transform.py` / `model.py` / `export.py` layer pattern.
- **D-05:** Persist authoritative ground-truth values as a **committed snapshot**, split by shape:
  - **Scalars + benchmark comparisons** → one structured `kpi_values.json` (headline rates, by-class vs target, underutilization rates, ferry totals/YoY/distribution stats) — easy to cite inline in the measures spec.
  - **Table-valued KPIs** → one **CSV per table** (e.g. `availability_by_class.csv`, `availability_by_division.csv`, `exception_list.csv`, `underutilization_by_division.csv`, `ferry_yoy.csv`, `ferry_heatmap.csv`, `sales_redemption_gap.csv`). Exact file set/names are planner's call; the JSON-scalars / CSV-tables split is the decision.
- **D-06:** **pytest guards assert the snapshot values** (the snapshot is the regression contract). Must include the canonical pooled-mean grand-total guard ([0,1], not mean-of-class-means), the 2020 < 2019 YoY guard, and the distribution sanity checks (max ≈ 7,229 / median ≈ 12). Availability rate calcs **exclude the 209 NULLs** (denominator 4,405) — never impute.

### Deliverable docs
- **D-07:** **Two separate files** (the measures spec consumes the values from D-05):
  - `deliverables/kpi_definitions.md` — plain-language KPI formulas, audit benchmarks, the **5.8% (current) vs ~14% (audit Mar 2023) underutilization reconciliation note**, and the BA-narrative logic (audience: panel/BA).
  - `deliverables/measures_spec.md` — per-measure **DAX + SQL validation value + notes** (audience: the build contract for Phase 4).
- **D-08:** The measures spec is **grouped by domain → KPI** (Fleet Maintenance section, Ferry section; each KPI a subsection with a `Measure name | DAX | SQL validation value | Notes` table). Mirrors how KPIs were reasoned about and preserves audit-benchmark context. Phase 4 maps these measures onto report pages.

### Ferry period/year handling
- **D-09:** **Lifetime / period totals use ALL data** (every 15-min row counts, May 2015 → Jun 2026).
- **D-10:** The **YoY annual-trend KPI is computed only on complete calendar years 2016–2025** — the ~8-month 2015 and ~6-month 2026 partial years are **labeled and excluded** from YoY growth rates so endpoints don't distort the trend. The 2020 < 2019 COVID-dip guard is asserted within this complete-years range.
- **D-11:** **Seasonality pools all years by month** (every month of data contributes to the monthly/seasonal profile). **No annualization / estimation** of partial years — keeps the framing audit-grounded and assumption-free.

### Claude's Discretion
- Exact file names and the precise set of per-table CSVs under D-05 (e.g. whether the heatmap is one wide CSV or long-form), and the `kpi_values.json` key structure — planner's call, consistent with the snapshot-as-contract decision.
- DAX measure naming convention (e.g. `Availability Rate`, `Underutilization %`) — planner/spec-author's call; keep it consistent and Power-BI-friendly.
- Whether KPI SQL lives as inline strings in `kpis.py` or small helper functions — implementation detail.
- Output directory for table CSVs (`deliverables/` vs a new `data/kpi/`) — planner's call; keep the committed snapshot reviewable in git.
- Heatmap orientation (DoW × hour) and exact daypart/season rollup reuse from Phase 2 derived fields — use the locked Phase 2 derivations; presentation orientation is a Phase 4 concern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 3: KPI Layer & Measures Spec" — goal, the 4 success criteria, and the locked KPI list / pooled-mean guard / YoY (2020<2019) guard / distribution stats / two-doc deliverable.
- `.planning/REQUIREMENTS.md` — **KPI-01** (all Domain A/B KPIs computed authoritatively in SQL/Python, cross-checked against audit benchmarks) and **KPI-02** (KPI definitions doc + DAX-ready measures spec pairing each KPI with copy-paste DAX + SQL validation value, including the pooled-mean grand-total guard).
- `.planning/PROJECT.md` — scope split (GSD owns data layer only; no `.pbix`/PBIP/TMDL), the profiled data schemas, asset-class targets, the 5.8%-vs-14% decision, and the Key Decisions table.

### Phase 2 Gold contract (the input this phase computes over)
- `.planning/phases/02-transform-model-join-integrity/02-CONTEXT.md` — the Gold modeling decisions this phase depends on: `fact_vehicle` is the full fleet (4,614, availability-anchored LEFT JOIN; utilization NULL for non-light-duty), the disposal cross-measure runs on the matched light-duty subset; role-playing `owner_division_key` / `using_division_key`; `REFERENCE_YEAR = 2023`; ferry `season`/`daypart`/`day_of_week`/`is_weekend`/`sales_redemption_gap` derivations and their boundary definitions.
- `data/gold/*.parquet` — the type-preserving Gold tables this phase reads: `fact_vehicle`, `fact_ferry`, `dim_division`, `dim_date`, `dim_time`. **Column/table names here are the contract**; KPIs reference only confirmed Gold names. `AVAILABILITY_YTD` carries 209 genuine NULLs (exclude from rate calcs).
- `src/fleet_analytics/config.py` — single source of truth for constants; add asset-class targets / KPI thresholds here rather than inlining. `REFERENCE_YEAR = 2023` already present.
- `src/fleet_analytics/model.py`, `transform.py`, `export.py` — established DuckDB SQL-first layer pattern `kpis.py` should mirror.
- `tests/conftest.py` — session-scoped `:memory:` DuckDB `con` fixture (Bronze ingested once); reuse for KPI tests, or read Gold Parquet directly.

### Phase 1 DQ deliverables (extend, don't duplicate)
- `deliverables/data_dictionary.md` and `deliverables/dq_report.md` — the exception-list and disposal-candidate findings, and the 5.8%-vs-14% reconciliation, extend these; cite, don't recompute, audit thresholds.

### Audit / sourcing context (for documentation, not computation)
- AG Operational Review **2019.AU2.2** (downtime) / **2019.AU2.3** (underutilization) and the **May 2023 FSD General Government Committee report** — source of the asset-class targets, the ~14% underutilization benchmark, and the `REFERENCE_YEAR = 2023` framing. Thresholds are **cited, never recalculated**. Full citations in PROJECT.md / Phase 1 deliverables.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`data/gold/*.parquet`** (Phase 2 output) — the direct input; query with DuckDB `read_parquet`. `fact_vehicle` already carries `AVAILABILITY_YTD`, asset class, `Utilization` flag, `Specialized units`, owner/using division keys, and `fleet_age` on one row — everything Domain A needs including the disposal cross-measure.
- **`fact_ferry`** — already has `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`, and 15-min `ts_15`; Domain B KPIs group over these (no re-derivation).
- **`tests/conftest.py`** `con` fixture + the Phase 1/2 fail-fast-assert-then-pytest-guard pattern — reuse for KPI bounds/value guards.
- **`src/fleet_analytics/config.py`** constants pattern — extend with asset-class targets and any KPI threshold constants.

### Established Patterns
- **DuckDB SQL-first** transforms with explicit, testable assertions — `kpis.py` continues this (SQL `GROUP BY` / window functions for by-class, by-division, YoY, heatmap; assert bounds and exact values).
- **No COALESCE/fill on `AVAILABILITY_YTD`** — 209 NULLs excluded from rate calcs (denominator 4,405), never imputed; assert this in a guard.
- **Markdown deliverables** under `deliverables/` (data_dictionary.md, dq_report.md) — the two new docs follow the same home.

### Integration Points
- The committed KPI snapshot (`kpi_values.json` + per-table CSVs) and `measures_spec.md` are the **handoff surface Phase 4** consumes — every DAX measure in the Phase 4 report spec carries the SQL validation value defined here. Measure names + SQL values become the contract Phase 4 references.
- `kpi_definitions.md` traceability (KPI ↔ AG theme) is also referenced by the Phase 5 narratives.

</code_context>

<specifics>
## Specific Ideas

- One threshold rule end-to-end (below class target) is a deliberate simplicity/defensibility choice — exception list, "% below threshold", and disposal screen all share it, so the dashboard story is internally consistent and easy to defend at the panel.
- Disposal candidates must read as a **screening list for SME review**, never as disposal decisions — phrasing matters for the BA framing.
- The committed snapshot exists so the Power BI build is **falsifiable**: every dashboard number must reproduce a value in `kpi_values.json` / the CSVs.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Power BI page layout, relationships, slicers, theme, and "Mark as Date Table" are Phase 4; the requirements-gathering and stakeholder-engagement narratives are Phase 5.)

</deferred>

---

*Phase: 3-KPI Layer & Measures Spec*
*Context gathered: 2026-06-02*
