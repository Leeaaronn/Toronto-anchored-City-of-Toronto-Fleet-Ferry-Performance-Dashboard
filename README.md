# Fleet Services Analytics — City of Toronto BA Assignment

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Run from:** `uv run python -m fleet_analytics.pipeline` (one-command, end-to-end)
**Snapshot pull date:** 2026-06-02 (the supplied files are treated as a point-in-time snapshot — the City Vehicle Availability dataset is listed as *Retired*; see the [DQ report](deliverables/dq_report.md))
**Companion docs:** [data dictionary](deliverables/data_dictionary.md) · [DQ report](deliverables/dq_report.md) · [KPI definitions](deliverables/kpi_definitions.md) · [measures spec](deliverables/measures_spec.md) · [report spec](deliverables/report_spec.md) · [requirements approach](deliverables/requirements_approach.md) · [stakeholder engagement](deliverables/stakeholder_engagement.md)

---

## What this is

A fleet analytics project for a City of Toronto **Fleet Services Division (FSD)** business-analyst assignment. It ingests, cleans, profiles, and models three real City datasets — vehicle availability, light-duty utilization, and Toronto Island Ferry ticket counts — into a tested star schema, computes audit-grounded KPIs, and hands off clean modeled output plus DAX-ready specs for a Power BI dashboard and two narrative deliverables for FSD management.

The work is anchored on the two Auditor General themes: **vehicle downtime** (2019.AU2.2) and **underutilization** (2019.AU2.3), plus the value-added availability⋈utilization join most candidates miss.

### Scope boundary

Claude Code + GSD own the **data engineering layer only** — ingest, clean, profile, model (star schema), and the KPI/measures logic, all tested. The Power BI **report canvas is authored manually** by the user in Power BI Desktop on top of the modeled output. This repo produces clean modeled tables, a KPI definitions doc, a DAX-ready measures spec, and a page-by-page report spec — it does **not** generate a `.pbix`, PBIP, or TMDL.

## How to run

The pipeline is reproducible from a clean checkout with [uv](https://docs.astral.sh/uv/) (Python 3.12, pinned via `.python-version`):

```bash
uv sync                                      # install locked deps + the editable package
uv run python -m fleet_analytics.pipeline    # ingest -> transform -> model -> export -> KPIs
```

- **Inputs:** the three raw source CSVs are committed under `.planning/data/` — a fresh clone can run with no external downloads. To point at a different input directory, set the optional `FLEET_DATA_DIR` environment variable (defaults to `.planning/data/`).
- **Outputs:** `data/gold/*.parquet` (+ readable `.csv`) — six modeled tables for Power BI import — and the `data/kpi/` snapshot (`kpi_values.json` + per-KPI CSVs). Regeneration is a clean no-op diff (`.gitattributes` pins `*.csv eol=lf`).

## Test gate

```bash
uv run pytest -q     # -> 77 passed, as of 2026-06-06
```

The suite covers schema/row-count contracts, the 209-null DQ guard, the flagship join-integrity asserts (2,080 matched / 6 unmatched, no fan-out), derived-field correctness, KPI bounds, and an end-to-end pipeline smoke test. The count above is a dated result, not an eternal invariant — re-run the command to confirm the current state.

## Outputs / handoff

| Path | Contents | Consumer |
|------|----------|----------|
| `data/gold/*.parquet` | 6 type-preserving star-schema tables (`dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time`, `dim_class_target`) | Power BI Desktop (import) |
| `data/gold/*.csv` | Human-readable mirror of the same tables | Inspection |
| `data/kpi/kpi_values.json` + `*.csv` | Authoritative KPI snapshot — every dashboard number must reproduce a value here | Validation / Power BI |
| `deliverables/*.md` | Data dictionary, DQ report, KPI definitions, measures spec, report spec, two narratives | Submission |

## Headline numbers

The authoritative source of truth is [`data/kpi/kpi_values.json`](data/kpi/kpi_values.json); formulas and the SQL↔DAX validation values live in [`deliverables/kpi_definitions.md`](deliverables/kpi_definitions.md) and [`deliverables/measures_spec.md`](deliverables/measures_spec.md). The full KPI set is **not** restated here — these are only the headline figures:

- **89.0% overall availability** (`0.8899`), computed as the **pooled per-vehicle mean** — deliberately distinct from the mean-of-class-means (`0.8786`), which would misstate the grand total.
- **5.8% underutilization** — note the two legitimate denominators, which must **not** be conflated:
  - `120 / 2,086 = 5.75%` raw light-duty (as reported in the [data dictionary](deliverables/data_dictionary.md) / [DQ report](deliverables/dq_report.md)), and
  - `0.0572` over the **2,080 matched** units (KPI layer).
  - Both round to 5.8%; the denominators differ by design (raw light-duty vs join-matched).
- **2,080 matched / 6 unmatched** on the availability⋈utilization join (`UNIT_NO` normalized; the 6 unmatched are documented as a DQ finding, not dropped silently).
- **34 disposal candidates** — light-duty units both below their availability target and flagged underutilized (the value-added availability⋈utilization cross-measure, tied to AG themes 2019.AU2.2 and AU2.3).
- **209 nulls excluded / 4,405 non-null** availability denominator (excluded, never imputed).
- **Row counts:** 4,614 (availability) / 2,086 (utilization) / 272,529 (ferry).

## Stated assumptions

- **209 null `AVAILABILITY_YTD` values are excluded, not imputed** — imputation would distort the audit-benchmarked availability rates; the null count is itself a regression-tested DQ assertion.
- **Underutilization is pre-classified in the source data, not recomputed** — the audit's km / engine-hour thresholds are cited, not recalculated (the source telematics data is absent).
- **Availability targets are cited from the audit, not recalculated** (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90).
- **5.8% (this snapshot) vs ~14% (audit, Mar 2023) underutilization** is surfaced as a legitimate insight (different period / fleet right-sizing), not treated as an error.
- **Ferry `Redemption Count` is assumed to be tickets scanned at boarding**; the sales-to-redemption gap is an analytical assumption flagged for SME validation.
- The City Vehicle Availability dataset is **Retired** on the portal, so it is treated as a point-in-time snapshot tied to the **2026-06-02** pull date.

## Sources & licence

Three primary sources, all under the **Open Government Licence – Toronto**:

1. **City of Toronto Open Data portal** — the three source datasets (vehicle availability, light-duty utilization, ferry ticket counts).
2. **May 2023 FSD report to the General Government Committee** — availability benchmarks and stakeholder/organizational context.
3. **Auditor General Operational Review of Fleet Services — 2019.AU2.2** ("Lengthy Downtime Requires Immediate Attention") and **2019.AU2.3** ("Stronger Corporate Oversight Needed for Underutilized Vehicles").

Snapshot pull date: **2026-06-02**.
