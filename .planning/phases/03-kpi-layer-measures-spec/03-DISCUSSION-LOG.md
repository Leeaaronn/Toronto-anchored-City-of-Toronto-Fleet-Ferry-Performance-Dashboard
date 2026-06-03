# Phase 3: KPI Layer & Measures Spec - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 3-KPI Layer & Measures Spec
**Areas discussed:** Threshold definitions, KPI compute artifact, Measures spec format, Ferry period/year handling

---

## Threshold definitions

### Q1 — Below-target / "critically low" cutoff for the exception list

| Option | Description | Selected |
|--------|-------------|----------|
| Per-class audit target | Below threshold if `AVAILABILITY_YTD` < asset-class target (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90). Class-fair, audit-grounded. | ✓ |
| Per-class target + critical floor | Two tiers: below-target for the % metric + a stricter absolute floor (e.g. <50%) for the named list. | |
| Single fixed floor | One flat cutoff across all classes. | |

**User's choice:** Per-class audit target.

### Q2 — "Low availability" leg of the disposal-candidate screen

| Option | Description | Selected |
|--------|-------------|----------|
| Below class target | Same rule as the exception list — one coherent threshold across the phase. | ✓ |
| Below fleet-wide mean | Below the overall pooled mean (~0.89); relative-underperformer framing. | |
| Stricter absolute floor | Tighter cut (e.g. <80%/<70%) to keep the SME list short. | |

**User's choice:** Below class target.
**Notes:** Settled a single coherent threshold rule (below asset-class target) for the exception list, the "% below threshold" metric, and the disposal screen's low-availability leg.

---

## KPI compute artifact

### Q1 — How ground-truth values are computed and persisted

| Option | Description | Selected |
|--------|-------------|----------|
| kpis.py + committed snapshot | `kpis.py` (DuckDB SQL over Gold Parquet) + a committed machine-readable values snapshot the tests assert and the spec embeds. | ✓ |
| kpis.py, test-only values | Numbers live only in pytest assertions, no committed file. | |
| SQL files + values doc | Raw `.sql` files + a hand-written values doc. | |

**User's choice:** kpis.py + committed snapshot.

### Q2 — Snapshot shape for scalar vs table-valued KPIs

| Option | Description | Selected |
|--------|-------------|----------|
| JSON scalars + CSV tables | Scalars/benchmarks in `kpi_values.json`; each table-valued KPI as its own CSV. | ✓ |
| All-JSON | One nested JSON for scalars and arrays-of-rows. | |
| All-CSV | Every KPI (incl. scalars) as CSV rows. | |

**User's choice:** JSON scalars + CSV tables.
**Notes:** Snapshot is the regression contract; pytest guards assert it (pooled-mean grand-total, 2020<2019 YoY, distribution stats).

---

## Measures spec format

### Q1 — Organization of the DAX-ready measures spec

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by domain/KPI | Sections by domain (Fleet / Ferry); each KPI a subsection with Measure \| DAX \| SQL value \| Notes. | ✓ |
| Grouped by Power BI page | Organized by the three report pages up front. | |
| Flat measures catalog | One big table of every measure. | |

**User's choice:** Grouped by domain/KPI.

### Q2 — One combined doc vs two separate files

| Option | Description | Selected |
|--------|-------------|----------|
| Two separate files | `kpi_definitions.md` (business formulas + reconciliation) and `measures_spec.md` (DAX + SQL value). | ✓ |
| One combined doc | A single doc carrying both per KPI. | |

**User's choice:** Two separate files.
**Notes:** Clean split — one for the BA narrative/panel, the other is the build contract for Phase 4.

---

## Ferry period/year handling

### Q1 — Handling partial 2015 / 2026 calendar years

| Option | Description | Selected |
|--------|-------------|----------|
| Full lifetime + YoY on complete years | Totals use all data; YoY only on complete years 2016–2025 (partials labeled/excluded); seasonality pools all years by month. | ✓ |
| Include all years, partial-flagged | Every year in YoY carrying a partial flag + month-coverage count. | |
| Annualize partial years | Scale partial years to full-year-equivalent estimates. | |

**User's choice:** Full lifetime + YoY on complete years.
**Notes:** No annualization/estimation — keeps the framing audit-grounded and assumption-free; COVID 2020<2019 dip asserted within the complete-years range.

---

## Claude's Discretion

- Exact per-table CSV file set/names and `kpi_values.json` key structure.
- DAX measure naming convention (consistent, Power-BI-friendly).
- KPI SQL as inline strings vs helper functions in `kpis.py`.
- Output directory for table CSVs (`deliverables/` vs `data/kpi/`).
- Heatmap orientation and daypart/season rollup reuse (use locked Phase 2 derivations).

## Deferred Ideas

None — discussion stayed within phase scope. (Power BI page layout/relationships/slicers/theme are Phase 4; the two narratives are Phase 5.)
