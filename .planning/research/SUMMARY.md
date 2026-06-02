# Project Research Summary

**Project:** City of Toronto Fleet Services Analytics — BA Assignment
**Domain:** Public-sector fleet + ferry analytics ETL feeding a manually-authored Power BI star-schema dashboard
**Researched:** 2026-06-01
**Confidence:** HIGH

## Executive Summary

This is a small, single-machine analytics ETL project: ingest three City of Toronto CSVs (4,614-row vehicle availability, 2,086-row light-duty utilization, 272,529-row ferry ticket counts at 15-min grain), clean and model them into a star schema, compute KPIs validated against Auditor General benchmarks, and hand the output to a manually-authored Power BI dashboard. The entire engineering layer is Python + DuckDB (SQL-first) producing Parquet/CSV; the pipeline is reproducible, tested with pytest, and sized appropriately — no orchestration frameworks, no server databases, no `.pbix` generation. All four research files converged independently on the same architecture: medallion-lite (Bronze/Silver/Gold), a degenerate enriched `fact_vehicle` (1:1 availability ⋈ utilization join on normalized `UNIT_NO`), and split `dim_date` + `dim_time` dimensions for the sub-daily ferry grain.

The highest-leverage analytical asset in the whole project is the availability ⋈ utilization join. Most candidates analyze the two datasets in isolation; bridging them on normalized `UNIT_NO` (zero-padded string vs integer — a deliberate normalization step) yields the disposal-candidate cross-measure that directly operationalizes both AG themes (downtime AU2.2 + underutilization AU2.3). The join target is 2,080 of 2,086 utilization rows matched, with 6 unmatched rows treated as a documented DQ finding rather than a bug. This single join — and the pytest assertion that guards it — is the densest test surface and the headline differentiator graders reward.

The primary risks are correctness traps, not performance ones: wrong null handling in availability averages (denominator must be 4,405 non-null, not 4,614; nulls must never be coerced to 0), average-of-averages errors in DAX grand totals, ferry DST ambiguity if timestamps are localized (keep tz-naive), pre-aggregating KPIs into the model instead of leaving them as DAX measures, and BA credibility failures from unsourced numbers or causal over-claims. Every trap has a concrete prevention strategy and maps to a specific pytest check. The mitigation posture: establish DQ assertions in Phase 1, gate on join-integrity tests before Phase 3, and validate every SQL KPI value against the Phase 3 measures spec before any DAX is authored.

---

## Key Findings

### Recommended Stack

The stack is intentionally minimal: Python 3.12 + DuckDB 1.5.x as the in-process analytical engine, pandas 2.2.x for calendar generation and DuckDB-boundary convenience, pyarrow 16+ for type-preserving Parquet output, pytest 8.4.x for the test suite, and uv as the package manager (lockfile reproducibility, fast CI installs). Pandera 0.20+ encodes DQ rules — including the 209-null assertion and the 0–1 availability bounds — as executable contracts. `fg-data-profiling` (not the retired `ydata-profiling`) generates the profiling HTML artifact for the Phase 1 deliverable. The entire pipeline runs as a single `python -m fleet_analytics.pipeline` invocation; no Airflow, no dbt, no server database.

Parquet is the primary output format because it preserves types end-to-end (dates stay dates, availability floats stay floats, nulls stay null) with zero re-typing in Power Query. CSV is emitted as a readable fallback. Power BI Desktop has a native local-filesystem Parquet connector; no Azure required. One Parquet file per Gold table maps cleanly to one Power BI table.

**Core technologies:**
- **Python 3.12:** Runtime — stable 2026 sweet spot; DuckDB 1.5 floor is 3.10.
- **DuckDB 1.5.x:** In-process OLAP — reads CSV natively, writes Parquet, expresses the entire transform/join/aggregate pipeline in SQL. Zero server setup.
- **pandas 2.2.x:** Edge-cases only — `dim_date`/`dim_time` calendar generation, EDA input, test assertions. DuckDB returns DataFrames via `.df()`; pass frames back via `FROM df`.
- **pyarrow 16+:** Parquet engine — type-preserving round-trip. `fastparquet` is being retired in pandas 3.1 and must not be used.
- **pytest 8.4.x + Pandera 0.20+:** Test runner + declarative schema/DQ contracts — encode the 209-null expectation, 2,080/2,086 join target, 0–1 availability bounds, and KPI sanity checks as regression guards.
- **uv:** Package manager — lockfile reproducibility (`uv.lock` committed), fast CI installs, Python version pinning in one tool.
- **fg-data-profiling 4.19.x:** One-line HTML/JSON profiling report. Use this name, not the frozen `ydata-profiling`.

### Expected Features

All features map to one of two AG audit themes — vehicle downtime (2019.AU2.2) or underutilization (2019.AU2.3) — or to the ferry operations domain. Every KPI leaving the pipeline must be traceable to an audit theme; that traceability thread runs through the narrative deliverables and the panel presentation.

**Must have (table stakes):**
- Overall fleet availability rate (nulls excluded; state n=4,405 and the 209-null DQ gap) — AU2.2
- Availability by asset class vs. audit targets + gap-to-target (LD 95% / MD 92% / HD 85% / Off-Road 88% / Other 90%) — AU2.2 flagship
- Exception list of critically low / near-zero availability units with drill-through — AU2.2
- Underutilization rate overall + by using division + specialized vs. non-specialized split — AU2.3
- Ferry YoY annual trend + growth rate with explicit COVID-dip annotation — Ferry
- Ferry seasonality profile (monthly + seasonal; summer peak) — Ferry
- Both narrative deliverables: requirements-gathering approach + stakeholder-engagement strategy grounded in BABOK/IIBA structure with real named stakeholders (David Jollimore / Vukadin Lalovic / Miguel Lamsaki) and power/interest grid + RACI
- Power BI dashboard + PDF export; stated assumptions visible on the dashboard

**Should have (differentiators that raise the grade):**
- **Availability ⋈ utilization disposal-candidate cross-measure** — vehicles that are BOTH low-availability AND underutilized; the highest-value differentiator, directly ties AU2.2 + AU2.3; depends on the normalized `UNIT_NO` join (2,080/2,086)
- Ferry day-of-week × hour-of-day demand heatmap (requires `dim_time` at 15-min grain) — staffing insight
- Ferry sales-to-redemption gap over time (row-level subtraction in the model; trend in DAX)
- Availability-vs-age trend (fleet renewal recommendation anchor) — AU2.2
- 5.8% (current) vs 14% (audit Mar 2023) underutilization reconciliation callout — frames period/right-sizing difference as an insight, not an error
- Insights/recommendations landing page tying each recommendation to an AG theme

**Defer / never:**
- Recomputing underutilization thresholds — telematics/odometer source data is absent; any recomputation is fabricated. Never.
- Generating `.pbix`/PBIP/TMDL — explicit locked decision. Never.
- Joining ferry dataset into the fleet star schema — different domain, different grain; forces a meaningless cross-product. Never.
- Predictive ferry demand forecasting — not asked for; adds risk without grading reward. Defer.

### Architecture Approach

The pipeline is a medallion-lite, single-machine flow: Bronze (verbatim typed CSV loads with row-count assertions), Silver (cleaned/conformed per source), Gold (star schema exported as Parquet). Two independent star schemas share nothing: the Fleet star (`dim_division` one-to-many `fact_vehicle`) and the Ferry star (`dim_date` and `dim_time` one-to-many `fact_ferry`). `fact_vehicle` is a degenerate dimension — availability and utilization are 1:1 per vehicle so splitting into `dim_vehicle` + `fact_vehicle` adds a join with zero benefit. `dim_date` is a daily spine (gapless, 2015→2026); `dim_time` is 96 rows (one per 15-min slot); `fact_ferry` carries both FKs. KPIs are computed in SQL/Python in Phase 3 as validation values; the measures spec pairs each with DAX text that reproduces the same number under slicer context — SQL validates DAX, never replaces it.

**Major components:**
1. **Ingest / Bronze (`ingest.py`)** — `read_csv_auto` with explicit types; assert 4,614 / 2,086 / 272,529 row counts; fail-fast gate.
2. **Profile / DQ (`profile.py`)** — DuckDB `SUMMARIZE` + Pandera + `fg-data-profiling`; data dictionary + DQ report (209 nulls, 5.8% vs 14%, ferry skew median 12/max 7,229, 6 unmatched join rows).
3. **Transform / Silver (`transform.py`)** — normalize `UNIT_NO` both sides to canonical int (`CAST(TRIM(...) AS BIGINT)`); preserve 209 nulls as genuine NULL; parse ferry timestamps tz-naive; round to 15-min slot; derive `fleet_age`, `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`.
4. **Model / Gold (`model.py`)** — build `dim_division`, `fact_vehicle` (availability LEFT JOIN utilization on normalized key), `fact_ferry`, `dim_date` (gapless), `dim_time` (96 rows); export Parquet per table; the 2,080/2,086 join assertion lives here.
5. **KPI layer (`kpis.py`)** — aggregate every KPI in SQL/Python; KPI definitions doc + measures spec with paired DAX text; SQL values are the ground-truth the DAX must reproduce.
6. **Report spec + Narratives (`specs/`, `docs/`)** — page-by-page Power BI spec; requirements-gathering approach; stakeholder-engagement strategy.

### Critical Pitfalls

1. **`UNIT_NO` join failure from zero-padding/type mismatch** — normalize BOTH sides to canonical int (`CAST(TRIM(UNIT_NO) AS BIGINT)`) before joining; assert matched == 2,080 and unmatched == 6 in pytest; inspect and document the 6 unmatched rows explicitly; a wrong count means a normalization bug, not bad data.

2. **Null-coercion corrupting availability averages** — keep 209 `AVAILABILITY_YTD` nulls as genuine NULL through the entire pipeline; never coerce CSV blanks to 0; denominator for any rate calc is 4,405 (non-null), never 4,614; use `AVG()` (SQL/DAX) or `.mean()` (pandas), which skip NULL by design; assert `null count == 209` and `non-null count == 4,405` in pytest.

3. **Average-of-averages in DAX grand totals** — `AVAILABILITY_YTD` is already a per-vehicle ratio; the grand total must be the pooled per-vehicle mean (`DIVIDE(SUMX(...), COUNTROWS(non-null))`), not the mean of class-level averages; compute the canonical value in Phase 3 SQL and assert the DAX matches it.

4. **Ferry timestamp DST trap** — keep timestamps tz-naive; localizing to `America/Toronto` injects nonexistent-time NaTs (spring forward) and ambiguous-hour duplicates (fall back), and shifts peak windows by one hour for half the year if converted to UTC; derive all time dimensions directly from the naive local time; document this as a stated assumption.

5. **Pre-aggregating KPIs into model tables** — keep `fact_vehicle` at one row per vehicle and `fact_ferry` at 15-min grain; express all aggregations as DAX measures; use SQL KPI values only to validate the DAX spec; pre-aggregating freezes numbers and breaks slicer interactivity.

6. **BA credibility failures** — every external figure (audit targets 95/92/85/88/90, ~14% audit figure, $411K savings) must carry an inline citation; anchor every KPI to its AG theme; frame disposal candidates as a screening list for SME review, not a decision; describe the 5.8% vs 14% gap as a period/right-sizing insight, not an error.

---

## Implications for Roadmap

The four research files are unanimous: the phase order is strictly data-contract-driven for Phases 1–3, with report spec and narratives parallelizable from Phase 4 onward. The transform + join step (Phase 2) is the highest-risk phase because two flagship differentiators (disposal-candidate cross-measure and the ferry heatmap) depend entirely on getting `UNIT_NO` normalization and the 15-min time-dimension split correct. No phase should begin until the previous phase's gate test passes.

### Phase 1: Ingest, Profile, and DQ Baseline

**Rationale:** All downstream work depends on knowing the exact shape of the data. Profiling is not optional ceremony; the DQ findings (209 nulls, 6 unmatched join rows, retired-dataset status, Sales/Redemption interpretation) become stated assumptions that appear on the dashboard and in both narrative deliverables. Establish these facts before writing a single transform.
**Delivers:** Bronze tables with row-count assertions passing; data dictionary; DQ report (209 nulls, 5.8% vs 14%, ferry skew, stated assumptions); Pandera schemas encoding null count and row-count assertions as regression guards.
**Addresses:** DQ disclosures; overall availability rate baseline; stated assumptions for dashboard; 5.8% vs 14% framing.
**Avoids:** Pitfall 2 (null preservation established at ingest); Pitfall 6 (pull date and dataset status documented at source).
**Gate:** Row counts 4,614 / 2,086 / 272,529 asserted; null count == 209 asserted; no `AVAILABILITY_YTD == 0` that was originally null.

### Phase 2: Transform, Model, and Join Integrity

**Rationale:** Highest-risk phase. `UNIT_NO` normalization, the availability ⋈ utilization join, the 15-min timestamp split, and the star-schema build all land here. The disposal-candidate cross-measure and the ferry heatmap both have a hard dependency on this phase being correct. The `dim_date` gapless spine and `dim_time` 96-row table are built here — without them, Power BI time intelligence breaks in Phase 4.
**Delivers:** Silver cleaning tables; Gold star schema as Parquet (`dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time`); all derived fields; join-integrity tests green; 6 unmatched rows documented.
**Uses:** DuckDB SQL for normalization and joins; pandas for `dim_date`/`dim_time` generation; pyarrow for Parquet export.
**Avoids:** Pitfall 1 (UNIT_NO join failure); Pitfall 4 (DST/timestamp trap — tz-naive, no localization); split date+time dimension (not a combined datetime dimension).
**Gate:** Matched == 2,080, unmatched == 6, no NaN key, no fan-out, `fact_vehicle` key unique; no NaT post-parse, row count == 272,529, `dim_date` gapless, `dim_time` == 96 rows.

### Phase 3: KPI Layer and Measures Spec

**Rationale:** Once Gold tables are locked and tested, every KPI is computed authoritatively in SQL/Python. These Phase 3 values are the ground truth the DAX must reproduce. Weighting decisions (unweighted per-vehicle mean for availability, pooled grand total not mean-of-class-means, sum vs median for ferry volume) are decided and documented here. The disposal-candidate count is computed here — the headline differentiator number.
**Delivers:** All Domain A and Domain B KPI values cross-checked against audit benchmarks; KPI definitions doc; DAX-ready measures spec (copy-paste DAX paired with SQL validation values); underutilization 5.8% vs 14% reconciliation note; ferry distribution stats (median 12, p90/p95, COVID-dip year confirmed).
**Avoids:** Pitfall 3 (average-of-averages — grand total == pooled mean, asserted); divide-by-zero (`DIVIDE()` with alternate specified in spec); skew-blind aggregation (sum for totals, median/percentiles for typical, peak stats for staffing heatmap).
**Gate:** Availability rates in [0,1]; overall availability == pooled mean (not mean-of-class-means); YoY shows 2020 < 2019 (COVID dip present); max window ≈ 7,229, median ≈ 12.

### Phase 4: Power BI Report Specification

**Rationale:** The report spec is the contract between the GSD-owned data layer and the manually-authored Power BI canvas. It must be precise enough that the user can build the dashboard without ambiguity: exact DAX for every measure, exact column and table names from Gold Parquet, relationship diagram (single-direction dim→fact; no fleet↔ferry relationship), `dim_date` "Mark as Date Table" instruction, slicer plan, visual types, PDF-export layout. Cannot be written before Phase 3.
**Delivers:** Page-by-page report spec for three dashboard pages (Fleet Maintenance; Ferry Operations; Summary/Insights); relationship model diagram; Power BI theme and PDF-layout guidance; DAX measures pasted from Phase 3 spec.
**Avoids:** Bidirectional relationships + missing date table (mandated single-direction + Mark as Date Table); divide-by-zero (`DIVIDE` mandated); average-of-averages (canonical DAX from Phase 3 used directly).
**Gate:** Spec references only column and table names confirmed in Gold Parquet; every DAX measure has a matching SQL validation value from Phase 3.

### Phase 5: Narrative Deliverables

**Rationale:** Independent of the data pipeline; can be drafted in parallel with Phases 3/4. Final polish should happen after Phase 3 so the traceability section references confirmed KPI names. Both deliverables must read as real public-sector BA artifacts using BABOK/IIBA structure, real named stakeholders, AG audit framing, and inline citations.
**Delivers:** Full draft of the requirements-gathering approach (business context, stakeholder identification, elicitation techniques with rationale, requirements types, prepare/conduct/confirm process, traceability to AG themes, assumptions and constraints); full draft of the stakeholder-engagement strategy (stakeholder register, power/interest grid, RACI matrix, engagement approach per group, communication plan, feedback loops, risks).
**Avoids:** Pitfall 6 (AG framing, sourced numbers, hedged causal language, disposal candidates as review list not decisions, 5.8% vs 14% as period/right-sizing insight, assumptions stated).
**Gate:** Every external number carries an inline citation; both documents open with AG theme framing; disposal candidates phrased as screening list for SME review; stated assumptions section explicit.

### Phase 6: Ship

**Rationale:** Final packaging, README, citations, and confirmation that all three required components are complete and self-consistent.
**Delivers:** README with citations and assumptions (Open Government Licence – Toronto, pull date, key assumptions, test results); `data/gold/` containing all five Parquet files; one-command pipeline reproducibility verified; all three required deliverables confirmed complete.
**Avoids:** Pitfall 6 (licence attribution, pull date, assumptions visible).
**Gate:** `uv run pytest -q` passes from a clean environment; README cites the three primary sources (Open Data portal, May 2023 FSD report, AG 2019.AU2.2/2.3 Operational Review).

### Phase Ordering Rationale

- Phases 1→2→3 are strictly sequential data contracts. Each phase's output is the input contract for the next. Skipping any gate is how silent correctness bugs reach the dashboard and then the panel interview.
- The Phase 2 join is the critical path node. The flagship differentiator (disposal candidates), the ferry staffing heatmap, and YoY time-intelligence all depend on Phase 2 outputs. More test investment goes here than anywhere else.
- Phase 4 depends on Phase 3 measure names. The report spec must reference column names and validation values that exist — it cannot be written speculatively.
- Phase 5 is parallelizable from Phase 3 onward. Draft narratives early; polish after KPIs are confirmed so the traceability section is accurate.
- DAX lives in Power BI, never pre-aggregated into the model. Pre-aggregating to avoid DAX work is the most common architecture mistake and directly kills the slicer interactivity that is graded in the dashboard component.

### Research Flags

Phases needing deeper research during planning:
- **None.** All four research files returned HIGH confidence on the core technical decisions. The DuckDB/Parquet/pytest/Pandera stack is verified with current versions. Power BI star-schema, date-table, and relationship patterns are verified against Microsoft Learn + SQLBI. DAX average-of-averages and divide-by-zero patterns are verified against dax.guide. BABOK/IIBA narrative structure is verified against IIBA knowledge resources.

Phases with standard, well-documented patterns (skip research-phase):
- **All phases.** The only non-standard element is the `UNIT_NO` zero-padding join — fully characterized in PITFALLS.md with a concrete normalization recipe.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | DuckDB 1.5.x / Python 3.12 / pyarrow / pytest versions verified against PyPI and release notes. Power BI native Parquet connector verified against Microsoft Learn. `fg-data-profiling` rename confirmed against GitHub. fastparquet retirement confirmed against pandas 3.1 release notes. |
| Features | HIGH | KPI set, audit targets, stakeholder names, and narrative structure grounded in the project brief (primary source) and corroborated against BABOK/IIBA resources and fleet-KPI industry references. Only MEDIUM element: exact AG wording on benchmark targets cited via the brief, not re-verified against the primary AG PDF. |
| Architecture | HIGH | Star-schema, degenerate-dim, split date+time dimension, and medallion-lite patterns verified against Microsoft Learn, SQLBI, RADACAD, and current DuckDB practice. Degenerate-dim justification explicitly supported by Microsoft guidance on 1:1 entity tables. |
| Pitfalls | HIGH | Power BI/DAX claims verified against Microsoft Learn and dax.guide. pandas DST/tz-localize behavior verified against pandas 3.0 docs. UNIT_NO zero-padding trap and null-coercion denominator error derived directly from profiled schema facts in the project brief. Average-of-averages is the canonical DAX correctness trap, well-sourced. |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact 2022 audit actuals vs current data:** The audit published 2022 actuals (LD 91%, Off-Road 84%, HD 76%, MD 83%, Other 94%) as sanity benchmarks. The pipeline should compute current-period actuals and document that the comparison is for directional orientation, not exact match. Documentation task, not a blocker.
- **6 unmatched `UNIT_NO` rows:** The count is asserted; the nature of the rows (retired units, data entry errors, outside light-duty scope) will be profiled in Phase 1/2 and documented as the DQ finding. No planning impact.
- **Sales vs Redemption interpretation:** The assumption that `Sales Count` = tickets sold and `Redemption Count` = tickets scanned at boarding is stated but not verified against primary Toronto Island Ferry documentation. Surface as an explicit assumption on the dashboard; flag for SME validation in the stakeholder-engagement strategy.
- **`AVAILABILITY_YTD` denominator confirmation:** The 4,405 non-null count (4,614 − 209) must be asserted in Phase 1 tests to confirm the brief's profiled figure reproduces exactly from the supplied CSV. Phase 1 gate check, not a planning blocker.

---

## Sources

### Primary (HIGH confidence)

- `Fleet_Services_GSD_Project_Brief.md` and `.planning/PROJECT.md` (this repo) — profiled schemas, row counts, null counts, join model, stakeholder names, audit targets and benchmark actuals, locked decisions
- [Understand star schema and the importance for Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Design guidance for date tables in Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables)
- [Set and use date tables in Power BI Desktop — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-date-tables)
- [Bi-directional relationship guidance — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-bidirectional-filtering)
- [Model relationships in Power BI Desktop — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand)
- [AVERAGE function (DAX) — Microsoft Learn](https://learn.microsoft.com/en-us/dax/average-function-dax) and [AVERAGEX — dax.guide](https://dax.guide/averagex/)
- [Power Query Parquet connector — Microsoft Learn](https://learn.microsoft.com/en-us/power-query/connectors/parquet)
- [pandas.DataFrame.to_parquet — pandas docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html)
- [pandas.Series.dt.tz_localize — pandas 3.0 docs](https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.tz_localize.html)
- [duckdb · PyPI](https://pypi.org/project/duckdb/) — 1.5.0, Python 3.10 floor
- [pytest · PyPI](https://pypi.org/project/pytest/) — 8.4.2 stable
- [ydata-profiling / fg-data-profiling GitHub](https://github.com/ydataai/ydata-profiling) — rename confirmed, old package frozen
- [Stakeholder Analysis | IIBA BABOK Extended](https://www.iiba.org/knowledgehub/babok-applied/stakeholder-analysis/)

### Secondary (MEDIUM confidence)

- [Power BI — Star schema or single table — SQLBI](https://www.sqlbi.com/articles/power-bi-star-schema-or-single-table/) — degenerate-dim justification
- [Choosing between Date or Integer to represent dates — SQLBI](https://www.sqlbi.com/articles/choosing-between-date-or-integer-to-represent-dates-in-power-bi-and-tabular/)
- [How to Use Time and Date Dimensions in a Power BI Model — RADACAD](https://radacad.com/how-to-use-time-and-date-dimensions-in-a-power-bi-model/) — sub-daily split pattern
- [DuckDB Medallion Architecture — Medium/datatomas](https://medium.com/@datatomas/duckdb-medallion-architecture-a-complete-local-lakehouse-guide-0f1944b6bcdf)
- [The data validation landscape in 2025 — aeturrell](https://aeturrell.com/blog/posts/the-data-validation-landscape-in-2025/) — Pandera as lightweight code-first choice
- [Best Python Package Managers 2026 — scopir](https://scopir.com/posts/best-python-package-managers-2026/) and [uv vs pip vs Poetry — danilchenko.dev](https://www.danilchenko.dev/posts/uv-vs-pip-vs-poetry/)
- [9 Elicitation Techniques Used by Business Analysts — BusinessAnalystMentor](https://businessanalystmentor.com/elicitation-technique/)
- [Hidden Timezone Issues: Pandas Timestamp Edge Cases and DST Gotchas — Medium](https://medium.com/@ThinkingLoop/hidden-timezone-issues-pandas-timestamp-edge-cases-and-dst-gotchas-08eeab53e692)
- Auditor General Fleet Services Operational Review — 2019.AU2.2 / 2019.AU2.3; FSD report to General Government Committee, May 2023 (cited via brief)

---

*Research completed: 2026-06-01*
*Ready for roadmap: yes*
