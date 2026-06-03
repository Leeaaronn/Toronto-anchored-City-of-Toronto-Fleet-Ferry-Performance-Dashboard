# Fleet Services Analytics — City of Toronto BA Assignment

## What This Is

A fleet analytics project for a City of Toronto **Fleet Services Division (FSD)** business-analyst assignment. It analyzes three real City datasets — vehicle availability, light-duty utilization, and Toronto Island Ferry ticket counts — to define meaningful KPIs, surface exceptions and insights, and feed a Power BI dashboard plus two narrative deliverables for FSD management.

**Scope boundary:** Claude Code + GSD own the **data engineering layer only** — ingest, clean, profile, model (star schema), and the KPI/measures logic, all tested. The Power BI **report canvas is authored manually** by the user in Power BI Desktop on top of the modeled output. GSD produces clean modeled tables, a KPI definitions doc, a DAX-ready measures spec, and a page-by-page report spec — it does **not** generate a `.pbix`, PBIP, or TMDL.

## Core Value

Produce clean, tested, star-schema modeled output plus documented KPI/DAX specs that let the user build a credible, audit-grounded Power BI dashboard — anchored on the two Auditor General themes (vehicle downtime and underutilization) and the value-added availability⋈utilization join most candidates miss.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Ingest 3 CSVs into DuckDB with schema + row-count validation — *Validated in Phase 1 (DATA-01/03); typed Bronze ingest, fail-fast counts 4,614/2,086/272,529, 24 green tests*
- [x] Data dictionary + data-quality report (nulls, ranges, outliers, the 5.8% vs 14% underutilization discrepancy, documented assumptions) — *Validated in Phase 1 (DATA-02); `deliverables/data_dictionary.md` + `dq_report.md`*
- [x] Exclude the 209 null `AVAILABILITY_YTD` values from rate calcs and flag as a DQ gap (no imputation) — *Validated in Phase 1 (DATA-03/04); raw-CSV value-level guard + Pandera 0–1 bounds*
- [x] Normalize `UNIT_NO` (canonical-integer `TRY_CAST`, 44 alphanumeric units preserved), parse ferry timestamps (15-min slots, 0 NaT), derive fleet_age / season / daypart / day_of_week / is_weekend / sales_redemption_gap — *Validated in Phase 2 (MODEL-01)*
- [x] Build star-schema tables: `dim_division` (21 conformed), `fact_vehicle` (4,614 enriched), `fact_ferry` (272,529), gapless `dim_date` (4,383), 96-row `dim_time` — *Validated in Phase 2 (MODEL-02)*
- [x] Join availability ⋈ utilization on normalized `UNIT_NO` (matched 2,080 / unmatched 6 anti-join, no fan-out, unique key) with join-integrity tests; 6-unmatched + 44-alphanumeric DQ findings documented — *Validated in Phase 2 (MODEL-03)*
- [x] Output clean type-preserving Parquet + readable CSV (10 files in `data/gold/`, 209 NULLs preserved through export) for Power BI import — *Validated in Phase 2 (MODEL-04)*

### Active

<!-- Current scope. Building toward these. Detailed in REQUIREMENTS.md. -->

- [ ] Implement all Domain A (fleet maintenance) and Domain B (ferry) KPIs as SQL/Python, validated against audit benchmarks
- [ ] KPI definitions doc (formulas) + DAX-ready measures spec (copy-paste into Power BI)
- [ ] Page-by-page Power BI report spec (Fleet Maintenance, Ferry Operations, Summary/Insights) with slicer plan, theme, exact DAX, PDF-export layout
- [ ] Full draft of the requirements-gathering approach narrative
- [ ] Full draft of the stakeholder-engagement strategy narrative
- [ ] README with citations, assumptions, and screenshots; repo cleanup; package all three components

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- **Generating the `.pbix` report canvas** — authored manually by the user in Power BI Desktop; GSD owns data + specs only.
- **PBIP / TMDL semantic-model scaffolding** — explicitly excluded by the user in the kickoff (brief sec. 6 offered it as optional; decision is: do not scaffold).
- **Imputing the 209 null availability values** — decision is to exclude and flag as a DQ gap, not impute.
- **Recomputing the underutilization classification** — it is pre-applied in the data; km/engine-hour thresholds are cited from the audit, not recalculated.
- **Recomputing km/engine-hour telematics logic** — not present in the supplied data.

## Context

**Domain background.** The City of Toronto's Fleet Services Division manages the City's vehicle fleet and Toronto Island Ferry operations. The Auditor General audited FSD and issued recommendations to improve fleet maintenance efficiency. Two AG report themes anchor this work: **vehicle downtime** (2019.AU2.2, "Lengthy Downtime Requires Immediate Attention") and **underutilization** (2019.AU2.3, "Stronger Corporate Oversight Needed for Underutilized Vehicles"). The user is the business analyst: analyze the datasets, define KPIs and value-added measures, build a dashboard, and summarize findings + recommendations for management.

**Real stakeholders** (from the FSD report to the General Government Committee, May 2023): David Jollimore (General Manager, Fleet Services — sponsor); Vukadin Lalovic (Director, Fleet Asset Management — SME); Miguel Lamsaki (Acting Director, Fleet Maintenance — SME). Client divisions (Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc.) are the fleet consumers. Oversight: the Auditor General.

**The data (real schemas profiled from supplied CSVs):**
- **City Vehicle Availability** — 4,614 rows (one row per vehicle; cross-sectional, no date grain). Key fields: `UNIT_NO` (zero-padded string), `AVAILABILITY_YTD` (0–1 fraction; mean ≈ 0.89; **209 nulls ≈ 4.5%**), `UNIT_TYPE` (asset class), `OWNER_DIVISION` (21 divisions), model `YEAR` (1982–2026), `IN_SERV_DT`, `SEASONAL` (375 seasonal), `STATUS_DESC` (4,195 Active), plus `MAKE`, `MODEL`, `CATEGORY`/`CAT_DESC`/`CATEGORY_CLASS`/`CAT_GRP`, `HIGH_PRIORITY`, `REF_DIVISION`. Asset-class targets (audit): Light Duty 95% (2022 actual 91%), Off-Road 88% (84%), Heavy Duty 85% (76%), Medium Duty 92% (83%), Other 90% (94%). Portal lists this dataset as **Retired** — treat as a point-in-time snapshot and state the pull date.
- **Light-Duty Vehicle Utilization** — 2,086 rows (one per light-duty vehicle). `UNIT_NO` (int), `Utilization` (binary: Not Underutilized 1,966 / Underutilized 120 ≈ **5.8%**), `Specialized units` (Yes 825 / No 1,261), `REF_USING_DIV` (20 divisions), plus `YEAR`, `MAKE`, `MODEL`. Classification is pre-applied; audit definition: under 5,000 km or 125 engine hours and avg usage under 3 days/week (where telematics exists). Audit reported ~14% underutilized (Mar 2023); the 5.8% here is a legitimate insight (period / fleet right-sizing differences).
- **Toronto Island Ferry Ticket Counts** — 272,529 rows (15-minute grain, May 2015 → Jun 2026, ~11 yrs). `Timestamp`, `Sales Count` (sold), `Redemption Count` (scanned at boarding — assumed). Highly skewed (median 12, max 7,229 per 15-min window). No nulls.
- **Join model:** Availability ⋈ Utilization on `UNIT_NO` (strip leading zeros / cast); 2,080 of 2,086 utilization records match. Ferry stands alone.

**KPIs / insights:**
- *Domain A (Fleet Maintenance):* overall availability rate; availability by asset class vs. target + gap-to-target (flagship); % below threshold + exception list of critically low units; availability by owner division; fleet age and availability-vs-age trend; underutilization rate overall and by using division; specialized vs non-specialized split; **value-added cross-measure** — availability of underutilized vs not-underutilized → disposal candidates (low availability AND underutilized).
- *Domain B (Ferry):* total tickets sold & redeemed (lifetime + period); YoY annual trend + growth rate (call out 2020–21 dip); seasonality (monthly + seasonal profile); day-of-week × hour-of-day demand heatmap → staffing insight; sales-to-redemption gap over time; avg daily volume by season + peak-day identification.

**Deliverables (three required + PDF):** (1) requirements-gathering approach, (2) stakeholder-engagement strategy, (3) Power BI dashboard + PDF export. Pass mark 70% → panel interview with a 10-minute presentation.

## Constraints

- **Scope split**: GSD owns data engineering only; Power BI canvas authored manually — Do not generate `.pbix`/PBIP/TMDL.
- **Tech stack**: Python + DuckDB for ETL, pandas where convenient, pytest for transformation/join-integrity tests, optional GitHub Actions CI. Output clean Parquet/CSV for Power BI import.
- **Data fidelity**: 209 availability nulls excluded (not imputed); underutilization pre-classified (not recomputed); thresholds cited from audit, not recalculated.
- **Assessment**: Late submissions rejected; 70% pass → panel interview. Output must be defensible and audit-grounded.
- **Sourcing**: Cite City of Toronto Open Data, the May 2023 FSD General Government Committee report, and the AG Operational Review (2019.AU2.2 / 2019.AU2.3); Open Government Licence – Toronto.

## Key Decisions

<!-- Decisions that constrain future work. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Exclude 209 null `AVAILABILITY_YTD` values; flag as DQ gap, don't impute | Imputation would distort audit-benchmarked rates; transparency on data gaps is the defensible BA choice | — Pending |
| GSD owns data layer only; Power BI report authored manually | User authors canvas in Desktop; version-controlling `.pbix` is low-value and brittle | — Pending |
| Do not scaffold PBIP/TMDL | User explicitly declined the optional scaffold in the kickoff | — Pending |
| Surface 5.8% (current) vs 14% (audit Mar 2023) underutilization as an insight | Different period / fleet right-sizing since 2023 — a legitimate finding, not an error | — Pending |
| Single enriched `fact_vehicle` (doubles as vehicle dim) | Availability & utilization are 1:1 per vehicle — idiomatic for this grain | — Pending |
| Full drafts of both narrative deliverables | User will refine; drafts grounded in AG audit + FSD report | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-03 — Phase 2 (Transform, Model & Join Integrity) complete: Gold star schema (5 tables) + availability⋈utilization join (2,080 matched, no fan-out) + type-preserving Parquet/CSV export in `data/gold/`, 58 tests green; verification 12/12 must-haves on DuckDB 1.5.3*
