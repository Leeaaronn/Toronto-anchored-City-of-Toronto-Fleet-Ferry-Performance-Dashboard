# Phase 4: Power BI Report Specification - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a single **page-by-page Power BI report specification** — the precise, unambiguous contract between the Gold data layer (`data/gold/*.parquet`) and the **manually-authored** Power BI canvas. The spec covers the three pages (Fleet Maintenance, Ferry Operations, Summary/Insights) plus the model setup that sits underneath them: single-direction dim→fact relationships, "Mark as Date Table", a theme, a slicer plan, per-visual DAX (mapped from `deliverables/measures_spec.md`), per-visual types, and a PDF-export layout. One small committed reference dimension (`dim_class_target`) is added so the audit target line is reproducible.

Discussion clarified **HOW** to lay out, theme, relate, slice, and reconcile the spec. The following are **locked by the roadmap** and are NOT open decisions:
- Three pages: Fleet Maintenance, Ferry Operations, Summary/Insights.
- Single-direction dim→fact relationships; **no fleet↔ferry relationship**; "Mark as Date Table" on `dim_date`.
- Every DAX measure has a matching **SQL validation value** carried from Phase 3; `DIVIDE` for ratios; the canonical **pooled-mean** DAX for grand totals (never average-of-averages).
- Spec references **only** column/table names confirmed to exist in the Gold Parquet output.
- Includes a slicer plan, a Power BI theme, visual types per page, and a PDF-export layout.

**Out of scope (other phases / manual):** generating a `.pbix` / PBIP / TMDL (the canvas is authored manually by the user — out of GSD scope entirely); the two narrative deliverables — requirements-gathering approach and stakeholder-engagement strategy (Phase 5).

**Audience:** FSD management + the BA-assignment panel (10-minute presentation + PDF export). The spec must let the user build with zero guesswork and tell a defensible, audit-grounded story.

</domain>

<decisions>
## Implementation Decisions

### Theme & visual identity
- **D-01:** **City of Toronto civic theme.** The spec includes a Power BI **theme JSON** block: navy/blue civic base (≈`#003F87`) with accessible accents, standard fonts. **Status semantics are consistent and color-locked:** red = below class target, green = at/above target — applied to gap-to-target visuals and conditional formatting everywhere. Note an accessibility check (avoid red/green-only encoding where feasible; pair with sign/position) so the panel reading isn't color-dependent.

### Summary / Insights page narrative
- **D-02:** **AG-themes-first hierarchy.** The Summary page leads with the two Auditor General themes, in order: (1) **downtime** — availability gap-to-target by class (Light/Medium/Heavy below benchmark; Off-Road/Other clear it); (2) **underutilization** — 5.8% current vs ~14% audit (Mar 2023), with the reconciliation note; (3) the **34-unit disposal screening list** — the availability⋈utilization cross-dataset value-add, framed explicitly as an **SME screening list, not a disposal decision**; (4) **ferry demand** (COVID dip + DoW×hour staffing) last. The cross-dataset disposal screen stays visually prominent as the differentiator even though AG themes lead.

### Class-target reference + schema reconciliation
- **D-03:** **Committed reference dimension.** Add `data/gold/dim_class_target.csv` (+ type-preserving `.parquet`) — `category_class → target` (Light 95, Medium 92, Heavy 85, Off-Road 88, Other 90), sourced from the audit constants already in `src/fleet_analytics/config.py` (cited, never recalculated). It imports as a real dimension with a **single-direction** relationship to `fact_vehicle` on the asset-class key. A small pytest guard asserts the 5 rows/values so the target line stays falsifiable and reproducible — consistent with the Phase-3 committed-snapshot philosophy.
- **D-04:** **Column-reference reconciliation is mandatory.** The spec references only names confirmed in the Gold output and corrects the Power-BI-friendly placeholders in `measures_spec.md` that don't match actual Gold columns. Known fixes to verify against `data/gold/*` headers: `dim_time` hour column is **`hour`** (not `hour_of_day`); `dim_date` exposes `date_key / year / month / month_name / day / day_of_week / is_weekend / quarter` (no bare `date` — time-intelligence/DATEADD uses the **Mark-as-Date-Table date column = `date_key`**); `fact_ferry` uses `day_of_week`, `Sales Count`, `Redemption Count`, `season`, `daypart`; `fact_vehicle` asset class = `CATEGORY_CLASS`, availability = `AVAILABILITY_YTD`, utilization = `Utilization`, `specialized_units`. The spec carries an explicit "column reference reconciliation" table so DAX is corrected, not copy-pasted blind.

### Relationships & model setup
- **D-05:** Single-direction dim→fact only. Planned relationships (spec to finalize exact cardinality/active-vs-inactive): `dim_date` → `fact_ferry` (via the slot date from `Timestamp`/`ts_15`), Marked as Date Table on `date_key`; `dim_time` → `fact_ferry` (`hour`/`time_key`); `dim_division` → `fact_vehicle` with **role-playing** owner vs using division (one active + `USERELATIONSHIP`, or two `dim_division` instances — spec decides and documents); `dim_class_target` → `fact_vehicle` (asset class). `fact_vehicle` is a **cross-sectional availability snapshot** (no ferry time grain) — keep the two fact tables independent; **no fleet↔ferry relationship**.

### Slicers & interactivity
- **D-06:** **Synced core + page-specific.** `Division`, `Asset Class` (`CATEGORY_CLASS`), and `Year` are **synced across all pages** (sync-slicers); the Ferry page adds **Season** and **Daypart**. Default visual interaction = **cross-highlight** (not full cross-filter) so context stays visible during live drill. The spec documents each slicer per page: field, slicer type (dropdown/list), and sync scope.

### Claude's Discretion (defaults set; planner may refine)
- **D-07 (visual types):** KPI **cards** for headline scalars; **clustered bar or bullet/bar-with-target-line** for availability-by-class vs target (gap-to-target); **table/matrix sorted gap ascending** (worst first) for the exception list and the 34-unit disposal screening list; **line chart** for ferry YoY with a 2020-dip callout; **matrix with a conditional-formatting color scale** for the DoW×hour heatmap (`day_of_week` rows × `hour` columns); column/line for seasonality; **signed bar** (never `abs()`) for the sales-redemption gap; cards for distribution stats (max 7,229 / median 12).
- **D-08 (PDF export):** Three **16:9 landscape** pages (one per report page) matching the canvas, fit-to-page; set page size in Power BI before export. A separate one-page exec summary is optional, not required.
- **DQ footnotes:** Surface the locked DQ caveats as small footnotes/tooltips where relevant — 209 excluded NULL availabilities (denominator 4,405), 6 unmatched `UNIT_NO`, and the sales-vs-redemption interpretation flagged for SME validation (from `dq_report.md`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 4: Power BI Report Specification" — goal + the 4 success criteria.
- `.planning/REQUIREMENTS.md` — **REPORT-01** (the single requirement this phase satisfies).
- `CLAUDE.md` — scope split (no `.pbix`/PBIP/TMDL), sourcing & Open Government Licence – Toronto.

### Build inputs (Phase 3 deliverables — the contract to map onto pages)
- `deliverables/measures_spec.md` — copy-paste DAX + SQL validation value per KPI; **correct its column refs against actual Gold names (D-04)**.
- `deliverables/kpi_definitions.md` — plain-language KPI defs, audit benchmarks, KPI↔AG-theme traceability, the 5.8% vs ~14% reconciliation.
- `deliverables/dq_report.md` — DQ caveats to surface as footnotes (209 nulls / 4,405 denom; 6 unmatched; sales-vs-redemption A3).
- `deliverables/data_dictionary.md` — Gold column definitions.

### Authoritative schema & values
- `data/gold/*.parquet` (+ `.csv`) — the **authoritative** column/table names the spec must reference (`fact_vehicle`, `fact_ferry`, `dim_date`, `dim_division`, `dim_time`).
- `data/kpi/kpi_values.json` + `data/kpi/*.csv` — falsifiable validation values every visual must reproduce.
- `src/fleet_analytics/config.py` — audit target constants (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90) + UNIT_TYPE→class map; source for `dim_class_target`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Gold star schema** (`data/gold/`, 5 tables) + **KPI snapshot** (`data/kpi/`) — the spec references these column names verbatim; the KPI CSVs/JSON are the validation values.
- **`config.py`** audit targets + class map — the single source for the new `dim_class_target` reference table (no recalculation).
- **`measures_spec.md` DAX** — the per-visual measures; map onto pages, fix column refs.

### Established Patterns
- **Committed-artifact / falsifiable philosophy** (Phase 3): every dashboard number reproduces a committed value. `dim_class_target.csv` + a tiny pytest guard mirrors this for the audit targets.
- **Deliverables are markdown docs** under `deliverables/` (e.g. `report_spec.md`); a small data artifact (`dim_class_target.csv/.parquet`) lands in `data/gold/` and is produced via the existing DuckDB `COPY` export pattern.

### Integration Points
- The report spec consumes Gold column names + `measures_spec.md` DAX; the new `dim_class_target` joins `fact_vehicle` on asset class (single direction).

</code_context>

<specifics>
## Specific Ideas

- **10-minute panel presentation + PDF export** is the consumption context — the spec must be buildable with zero guesswork.
- **City of Toronto civic look** (navy/blue), official-deliverable feel.
- **AG-themes-first** Summary story; the **availability⋈utilization disposal screen** is the prominent value-add, framed as an **SME screening list, not a decision**.
- Status color is **locked**: red = below class target, green = at/above.

</specifics>

<deferred>
## Deferred Ideas

- **Narrative deliverables** — requirements-gathering approach + stakeholder-engagement strategy → **Phase 5**.
- **Actual `.pbix` authoring** — done manually by the user in Power BI Desktop; **out of GSD scope** entirely.
- **Optional ferry visuals** (avg daily volume by season, explicit peak-day identification) — fold into the Ferry page at planner discretion if they strengthen the staffing story; not required by the success criteria.

[None of the above are scope creep for Phase 4 — they are correctly routed elsewhere.]

</deferred>

---

*Phase: 04-power-bi-report-specification*
*Context gathered: 2026-06-04*
