# Requirements: Fleet Services Analytics — City of Toronto BA Assignment

**Defined:** 2026-06-02
**Core Value:** Produce clean, tested, star-schema modeled output plus documented KPI/DAX specs that let the user build a credible, audit-grounded Power BI dashboard — anchored on the two Auditor General themes (vehicle downtime and underutilization) and the value-added availability⋈utilization join most candidates miss.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Ingest & Quality

- [x] **DATA-01**: Three source CSVs (vehicle availability, light-duty utilization, ferry ticket counts) load into DuckDB Bronze tables with explicit types and fail-fast row-count assertions (4,614 / 2,086 / 272,529)
- [ ] **DATA-02**: A data dictionary and data-quality report document nulls, ranges, outliers, ferry skew (median 12 / max 7,229), the retired-dataset pull-date caveat, and the 5.8% vs 14% underutilization discrepancy as a stated insight
- [x] **DATA-03**: The 209 null `AVAILABILITY_YTD` values are preserved as genuine NULL (never coerced to 0) and excluded from rate calcs (denominator 4,405), flagged as a DQ gap with no imputation
- [x] **DATA-04**: Pandera schemas encode the row-count, 209-null, 4,405-non-null, and 0–1 availability-bounds expectations as executable regression guards

### Transform & Model

- [ ] **MODEL-01**: `UNIT_NO` is normalized to a canonical integer on both datasets; ferry timestamps are parsed tz-naive and rounded to 15-minute slots; derived fields (`fleet_age`, `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`) are produced
- [ ] **MODEL-02**: Gold star-schema tables are built — `dim_division`, `fact_vehicle` (degenerate enriched dim), `fact_ferry`, gapless `dim_date` (2015→2026), and 96-row `dim_time`
- [ ] **MODEL-03**: Availability ⋈ utilization joins on the normalized `UNIT_NO` with join-integrity tests asserting matched == 2,080, unmatched == 6, unique `fact_vehicle` key, and no fan-out; the 6 unmatched rows are documented as a DQ finding
- [ ] **MODEL-04**: All five Gold tables are exported as type-preserving Parquet (plus readable CSV) ready for Power BI import

### KPIs & Measures Spec

- [ ] **KPI-01**: All Domain A (fleet maintenance) and Domain B (ferry) KPIs are computed authoritatively in SQL/Python and cross-checked against audit benchmarks (overall + by-asset-class availability vs targets, exception list, underutilization rate, disposal-candidate cross-measure, ferry YoY/seasonality/heatmap/sales-redemption gap)
- [ ] **KPI-02**: A KPI definitions doc (formulas) and a DAX-ready measures spec pair each KPI with copy-paste DAX and its SQL validation value, including the pooled-mean (not average-of-averages) grand-total guard

### Power BI Report Spec

- [ ] **REPORT-01**: A page-by-page Power BI report spec (Fleet Maintenance, Ferry Operations, Summary/Insights) defines exact Gold column/table names, single-direction relationships, "Mark as Date Table", slicer plan, theme, exact DAX per visual, and PDF-export layout

### Narrative Deliverables

- [ ] **NARR-01**: A full draft of the requirements-gathering approach narrative (BABOK/IIBA structure, real named stakeholders, elicitation techniques, traceability to AG themes, stated assumptions, inline citations)
- [ ] **NARR-02**: A full draft of the stakeholder-engagement strategy narrative (stakeholder register, power/interest grid, RACI, engagement + communication plan, feedback loops, risks, inline citations)

### Packaging & Ship

- [ ] **SHIP-01**: A README with citations, stated assumptions, pull date, and test results; a reproducible one-command pipeline; `data/gold/` with all five Parquet files; repo cleanup; all three required deliverables confirmed complete and self-consistent

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Analytics Extensions

- **EXT-01**: Predictive ferry demand forecasting
- **EXT-02**: Automated GitHub Actions CI running the pytest suite on push

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Generating the `.pbix` report canvas | Authored manually by the user in Power BI Desktop; GSD owns data + specs only |
| PBIP / TMDL semantic-model scaffolding | User explicitly declined the optional scaffold in the kickoff |
| Imputing the 209 null availability values | Decision is to exclude and flag as a DQ gap, not impute (imputation distorts audit-benchmarked rates) |
| Recomputing the underutilization classification | Pre-applied in the data; km/engine-hour thresholds are cited from the audit, not recalculated |
| Recomputing km/engine-hour telematics logic | Source telematics/odometer data is absent; any recomputation would be fabricated |
| Joining the ferry dataset into the fleet star schema | Different domain and grain; forces a meaningless cross-product |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| MODEL-01 | Phase 2 | Pending |
| MODEL-02 | Phase 2 | Pending |
| MODEL-03 | Phase 2 | Pending |
| MODEL-04 | Phase 2 | Pending |
| KPI-01 | Phase 3 | Pending |
| KPI-02 | Phase 3 | Pending |
| REPORT-01 | Phase 4 | Pending |
| NARR-01 | Phase 5 | Pending |
| NARR-02 | Phase 5 | Pending |
| SHIP-01 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14 ✓
- Unmapped: 0

---
*Requirements defined: 2026-06-02*
*Last updated: 2026-06-02 after roadmap creation (6 phases, 14/14 mapped)*
