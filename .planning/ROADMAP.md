# Roadmap: Fleet Services Analytics — City of Toronto BA Assignment

## Overview

This project moves through a strictly sequential data-contract pipeline: ingest three City of Toronto CSVs into validated Bronze tables (Phase 1), transform and model them into a tested Gold star schema with the headline availability⋈utilization join (Phase 2), compute every Domain A and Domain B KPI authoritatively in SQL with a DAX-ready measures spec (Phase 3), then write a page-by-page Power BI report spec the user builds against (Phase 4). Two narrative deliverables are drafted in parallel from Phase 3 onward (Phase 5), and the whole thing is packaged into a reproducible, cited, self-consistent submission (Phase 6). Each early phase has a hard gate test that must pass before the next begins — that gate discipline is how silent correctness bugs are kept out of the dashboard and the panel interview.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Ingest, Profile & DQ Baseline** - Load 3 CSVs into validated Bronze tables; produce data dictionary, DQ report, and Pandera regression guards (completed 2026-06-02)
- [ ] **Phase 2: Transform, Model & Join Integrity** - Build the Gold star schema as Parquet with the availability⋈utilization join and split date/time dimensions, all tested
- [ ] **Phase 3: KPI Layer & Measures Spec** - Compute all Domain A/B KPIs in SQL against audit benchmarks; produce KPI definitions doc + DAX-ready measures spec
- [ ] **Phase 4: Power BI Report Specification** - Page-by-page report spec with exact Gold names, relationships, slicers, theme, DAX, and PDF layout
- [ ] **Phase 5: Narrative Deliverables** - Full drafts of the requirements-gathering approach and stakeholder-engagement strategy narratives
- [ ] **Phase 6: Ship** - README with citations, one-command reproducible pipeline, `data/gold/` Parquet files, repo cleanup, all three deliverables confirmed

## Phase Details

### Phase 1: Ingest, Profile & DQ Baseline
**Goal**: All downstream work can trust the exact shape of the data — three sources land in validated Bronze tables and every data-quality fact is documented as a stated assumption before any transform is written.
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. The three source CSVs load into typed DuckDB Bronze tables and a fail-fast assertion confirms row counts 4,614 / 2,086 / 272,529.
  2. The 209 null `AVAILABILITY_YTD` values are preserved as genuine NULL (zero rows where an originally-null value became 0), and a test asserts null count == 209 and non-null count == 4,405.
  3. A data dictionary and DQ report exist documenting nulls, ranges, ferry skew (median 12 / max 7,229), the retired-dataset pull-date caveat, and the 5.8% vs 14% underutilization discrepancy framed as a stated insight.
  4. Pandera schemas encode the row-count, 209-null, 4,405-non-null, and 0–1 availability-bounds expectations as executable regression guards that run green.
**Plans**: 3 plans
  - [x] 01-01-PLAN.md — uv 3.12 project + Bronze ingest + row-count/null guards (DATA-01, DATA-03)
  - [x] 01-02-PLAN.md — Pandera DQ contracts: 0–1 bounds, value sets, dtypes (DATA-04)
  - [x] 01-03-PLAN.md — profiling facts + data dictionary + DQ report (DATA-02)

### Phase 2: Transform, Model & Join Integrity
**Goal**: The Gold star schema exists as type-preserving Parquet with the value-added availability⋈utilization join correct and tested — the critical-path node that the disposal-candidate cross-measure, ferry heatmap, and time-intelligence all depend on.
**Depends on**: Phase 1
**Requirements**: MODEL-01, MODEL-02, MODEL-03, MODEL-04
**Success Criteria** (what must be TRUE):
  1. `UNIT_NO` is normalized to a canonical integer on both datasets, ferry timestamps are parsed tz-naive and rounded to 15-minute slots (no NaT post-parse, row count == 272,529), and all derived fields (`fleet_age`, `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`) are produced.
  2. The availability⋈utilization join passes integrity tests asserting matched == 2,080, unmatched == 6, no NaN key, no fan-out, and a unique `fact_vehicle` key; the 6 unmatched rows are documented as a DQ finding.
  3. Five Gold tables are built — `dim_division`, `fact_vehicle` (degenerate enriched dim), `fact_ferry`, gapless `dim_date` (2015→2026), and 96-row `dim_time` — with tests asserting `dim_date` is gapless and `dim_time` == 96 rows.
  4. All five Gold tables export as type-preserving Parquet (plus readable CSV) ready for Power BI import.
**Plans**: 3 plans
  - [ ] 02-01-PLAN.md — config Gold constants + transform staging (TRY_CAST key, ferry 15-min, derived fields) + gold fixture + test_derived_fields (MODEL-01)
  - [ ] 02-02-PLAN.md — model.py 5 Gold tables + availability⋈utilization join + role-playing dim_division + join-integrity/dimension tests (MODEL-02, MODEL-03)
  - [ ] 02-03-PLAN.md — export.py Parquet+CSV + roundtrip test + 6-unmatched/44-alphanumeric DQ findings (MODEL-04)

### Phase 3: KPI Layer & Measures Spec
**Goal**: Every KPI has an authoritative SQL/Python ground-truth value cross-checked against audit benchmarks, paired with copy-paste DAX in a measures spec — the values the Power BI dashboard must reproduce.
**Depends on**: Phase 2
**Requirements**: KPI-01, KPI-02
**Success Criteria** (what must be TRUE):
  1. All Domain A KPIs are computed in SQL/Python: overall availability rate, availability by asset class vs. target + gap-to-target, exception list of critically low units, underutilization rate overall and by using division, specialized split, and the disposal-candidate cross-measure (low-availability AND underutilized).
  2. All Domain B ferry KPIs are computed: lifetime/period totals, YoY trend with a test asserting 2020 < 2019 (COVID dip present), seasonality profile, day-of-week × hour-of-day heatmap, and sales-to-redemption gap; distribution stats confirm max window ≈ 7,229 and median ≈ 12.
  3. Overall availability is computed as the pooled per-vehicle mean (not the mean-of-class-means) with all availability rates in [0,1], asserted by test as the canonical grand-total guard.
  4. A KPI definitions doc (formulas) and a DAX-ready measures spec pair each KPI with copy-paste DAX and its SQL validation value, including the 5.8% vs 14% reconciliation note.
**Plans**: TBD

### Phase 4: Power BI Report Specification
**Goal**: The user can build the three-page dashboard with zero ambiguity — the report spec is a precise contract between the Gold data layer and the manually-authored Power BI canvas.
**Depends on**: Phase 3
**Requirements**: REPORT-01
**Success Criteria** (what must be TRUE):
  1. A page-by-page report spec covers all three pages (Fleet Maintenance, Ferry Operations, Summary/Insights) and references only column and table names confirmed to exist in the Gold Parquet output.
  2. The spec defines single-direction dim→fact relationships (no fleet↔ferry relationship) and a "Mark as Date Table" instruction for `dim_date`.
  3. Every DAX measure in the spec has a matching SQL validation value carried from Phase 3, with `DIVIDE` mandated for ratios and the canonical pooled-mean DAX used for grand totals.
  4. The spec includes a slicer plan, Power BI theme, visual types per page, and a PDF-export layout.
**Plans**: TBD
**UI hint**: yes

### Phase 5: Narrative Deliverables
**Goal**: Two credible public-sector BA artifacts are drafted — readable as real IIBA/BABOK-structured documents grounded in the AG audit, real named stakeholders, and inline citations.
**Depends on**: Phase 3 (for confirmed KPI names in traceability; parallelizable with Phases 3/4 otherwise)
**Requirements**: NARR-01, NARR-02
**Success Criteria** (what must be TRUE):
  1. A full draft of the requirements-gathering approach exists (business context, stakeholder identification, elicitation techniques with rationale, requirements types, prepare/conduct/confirm process, traceability to AG themes, assumptions and constraints).
  2. A full draft of the stakeholder-engagement strategy exists (stakeholder register with real named stakeholders, power/interest grid, RACI matrix, engagement approach per group, communication plan, feedback loops, risks).
  3. Both documents open with AG theme framing (downtime AU2.2 + underutilization AU2.3) and every external number carries an inline citation.
  4. Disposal candidates are phrased as a screening list for SME review (not decisions), and an explicit stated-assumptions section is present.
**Plans**: TBD

### Phase 6: Ship
**Goal**: The submission is packaged, reproducible, cited, and self-consistent — all three required components confirmed complete and the pipeline runs clean from a fresh environment.
**Depends on**: Phases 4 and 5
**Requirements**: SHIP-01
**Success Criteria** (what must be TRUE):
  1. `uv run pytest -q` passes from a clean environment and the full pipeline runs as a single one-command invocation.
  2. `data/gold/` contains all five Parquet files and the repo is cleaned of scratch artifacts.
  3. A README documents citations, stated assumptions, the pull date, and test results, citing the three primary sources (Open Data portal, May 2023 FSD report, AG 2019.AU2.2/2.3 Operational Review) under the Open Government Licence – Toronto.
  4. All three required deliverables (modeled data + specs, report spec, two narratives) are confirmed complete and self-consistent.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ingest, Profile & DQ Baseline | 3/3 | Complete   | 2026-06-02 |
| 2. Transform, Model & Join Integrity | 0/3 | Not started | - |
| 3. KPI Layer & Measures Spec | 0/TBD | Not started | - |
| 4. Power BI Report Specification | 0/TBD | Not started | - |
| 5. Narrative Deliverables | 0/TBD | Not started | - |
| 6. Ship | 0/TBD | Not started | - |
