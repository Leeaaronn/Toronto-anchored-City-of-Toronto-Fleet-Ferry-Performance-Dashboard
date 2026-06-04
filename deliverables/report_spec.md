# Power BI Report Specification — Phase 4 (REPORT-01)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The page-by-page build contract between the Gold layer (`data/gold/*.parquet`) and the **manually-authored** Power BI canvas — model setup, relationships, theme, slicers, per-visual DAX (mapped from [`measures_spec.md`](measures_spec.md)), visual types, and PDF-export layout.
**Method:** Every visual references the column/table names **confirmed verbatim** in the committed Gold output (`data/gold/*.csv`/`.parquet`) and carries the **SQL validation value** it must reproduce (transcribed from `data/kpi/kpi_values.json` / `data/kpi/*.csv` via [`measures_spec.md`](measures_spec.md)). When the user wires these measures against the Gold Parquet, every visual is **falsifiable**: it must reproduce its validation value. Audit thresholds are **cited, never recalculated**.
**Snapshot pull date:** **2026-06-02** (point-in-time YTD availability snapshot — see the [DQ report](dq_report.md), caveat A1).

> **How to read this spec.** Grouped **page → visual**. Each visual carries: **type** · **fields** (real Gold columns, verbatim) · **DAX measure** (transcribed from [`measures_spec.md`](measures_spec.md), **not** re-derived) · **SQL validation value** it must reproduce · **DQ footnote**. **Scope split (locked):** GSD produces this **text spec**; the Power BI report canvas, relationships, theme, and slicers are authored **manually** in Power BI Desktop on top of the modeled output — **no `.pbix` / PBIP / TMDL is generated here.** Two locked framings recur: availability measures **exclude the 209 NULL `AVAILABILITY_YTD` values** (denominator **4,405**, never imputed), and the disposal cross-measure is a **screening list for SME review, never a disposal decision**. Companion docs: [`measures_spec.md`](measures_spec.md) (copy-paste DAX), [`kpi_definitions.md`](kpi_definitions.md) (plain-language KPI defs + AG-theme traceability), the [DQ report](dq_report.md) (caveats surfaced as footnotes), and the [`data_dictionary.md`](data_dictionary.md) (Gold column definitions).

---

## Column Reference Reconciliation

**D-04 (MANDATORY).** This spec references **only** names confirmed in `data/gold/*` (CSV headers read 2026-06-04). [`measures_spec.md`](measures_spec.md) uses Power-BI-friendly **placeholders** that do **not** all match the actual Gold columns. **DAX is corrected here, not copy-pasted blind from `measures_spec.md`.** Every measure in this spec applies the corrections below.

| `measures_spec.md` placeholder | Actual Gold column | Table | Correction note |
|--------------------------------|--------------------|-------|-----------------|
| `dim_time[hour_of_day]` | `dim_time[hour]` | `dim_time` | The hour column is **`hour`** (not `hour_of_day`). The time-of-day label is `time_of_day`; the join surrogate is `time_key`; also `minute`. |
| `dim_date[date]` (e.g. in `DATEADD(dim_date[date], -1, YEAR)`) | `dim_date[date_key]` | `dim_date` | **There is NO bare `date` column.** Mark-as-Date-Table column = **`date_key`**; **all** DATEADD / time-intelligence DAX must reference `dim_date[date_key]`. |
| `fact_ferry[Sales Count]` / `fact_ferry[Redemption Count]` | `fact_ferry[Sales Count]` / `fact_ferry[Redemption Count]` | `fact_ferry` | Confirmed: both carry an **embedded space** — they must be **bracketed** (`fact_ferry[Sales Count]`, `fact_ferry[Redemption Count]`). Not `Sales_Count`. |
| `DimClassTarget[Target]` (via `RELATED`/`SELECTEDVALUE`) | `dim_class_target[target]` | `dim_class_target` | The target resolves through the relationship **`dim_class_target[unit_type]` -> `fact_vehicle[UNIT_TYPE]`**, **NOT** `CATEGORY_CLASS`. Use `RELATED(dim_class_target[target])`. Columns are `unit_type, class_label, target` (lowercase). |
| asset-class join key = `CATEGORY_CLASS` | class label resolves via `UNIT_TYPE` | `fact_vehicle` | `CATEGORY_CLASS` holds **19 granular codes** (CLASS1-8, APPARATUS, BOAT, ...), **not** the 5 audit labels. The 5 audit classes (Light/Medium/Heavy/Off-Road/Other) live one level up via **`UNIT_TYPE`** (the validated Phase-3 join — `kpis.py` joins `fv.UNIT_TYPE = ct.unit_type`). |
| `fact_vehicle[Specialized units]` | `fact_vehicle[specialized_units]` | `fact_vehicle` | Lowercase, underscore (`specialized_units`); value set `{Yes, No}`. |
| division join keys | `owner_division_key` / `using_division_key` | `fact_vehicle` | Two role-playing foreign keys: `owner_division_key` (owns) and `using_division_key` (uses) — see Model Setup below. Division label = `dim_division[division_name]`. |

**Confirmed Gold headers (verbatim, the authoritative reference for every name below):**

| Gold table | Columns (verbatim, in order) |
|------------|------------------------------|
| `fact_vehicle` | `_id, UNIT_NO, YEAR, MAKE, MODEL, CATEGORY, CAT_DESC, UNIT_TYPE, CATEGORY_CLASS, CAT_GRP, IN_SERV_DT, STATUS_DESC, CLASS2, HIGH_PRIORITY, OWNER_DIVISION, REF_DIVISION, SEASONAL, AVAILABILITY_YTD, unit_key_int, fleet_age, Utilization, specialized_units, REF_USING_DIV, owner_division_key, using_division_key` |
| `fact_ferry` | `_id, Timestamp, Redemption Count, Sales Count, ts_15, season, daypart, day_of_week, is_weekend, sales_redemption_gap` |
| `dim_date` | `date_key, year, month, month_name, day, day_of_week, is_weekend, quarter` |
| `dim_time` | `time_key, time_of_day, hour, minute` |
| `dim_division` | `division_key, division_name` |
| `dim_class_target` | `unit_type, class_label, target` |

---

## Model Setup & Relationships

**D-05.** All relationships are **single-direction (dim -> fact)**, one-to-many, cross-filter direction **single** (never both). Build them in **Model view** exactly as listed.

| # | From (one side) | To (many side) | Key | Active? | Cross-filter | Notes |
|---|-----------------|----------------|-----|---------|--------------|-------|
| R1 | `dim_date[date_key]` | `fact_ferry` (slot date derived from `ts_15` / `Timestamp`) | date | Active | Single | Add a `date_key` column on `fact_ferry` in Power Query = the **date** part of `ts_15` (`Date.From([ts_15])`), then relate to `dim_date[date_key]`. Drives YoY / seasonality. |
| R2 | `dim_time[time_key]` | `fact_ferry` (slot time-of-day from `ts_15` / `Timestamp`) | time-of-day | Active | Single | Derive a `time_key` on `fact_ferry` matching `dim_time` grain (the 15-min slot). The heatmap uses `dim_time[hour]` on the column axis. |
| R3 | `dim_division[division_key]` | `fact_vehicle[owner_division_key]` | division (OWNER role) | **Active** | Single | **Owner** division — the division that *owns* the vehicle. The default, active division relationship. |
| R4 | `dim_division[division_key]` | `fact_vehicle[using_division_key]` | division (USING role) | **Inactive** | Single | **Using** division — activated on demand via `USERELATIONSHIP` (see role-playing note below). |
| R5 | `dim_class_target[unit_type]` | `fact_vehicle[UNIT_TYPE]` | unit type -> audit class | Active | Single | The audit **target line** resolves through this. **NOT** `CATEGORY_CLASS` (19 granular codes != 5 audit labels). Matches the validated Phase-3 KPI join (`kpis.py`: `fv.UNIT_TYPE = ct.unit_type`). One-to-many: `dim_class_target` (5 rows) -> `fact_vehicle`. |

**Mark as Date Table.** Select `dim_date`, **Table tools -> Mark as Date Table**, and set the **date column = `date_key`**. (`dim_date` has **no** bare `date` column.) All time-intelligence DAX (`DATEADD`, etc.) references `dim_date[date_key]`.

**Role-playing division (chosen approach — DOCUMENTED).** Use **one** `dim_division` table with **two relationships** to `fact_vehicle`: **R3 owner (active)** on `owner_division_key` and **R4 using (inactive)** on `using_division_key`. The default (active) path slices by **owner** division. Any measure that must slice by **using** division wraps its calculation in `USERELATIONSHIP` to switch the active path for that measure only — e.g.:

```DAX
Underutilization Rate (by Using Division) =
CALCULATE (
    [Underutilization Rate],
    USERELATIONSHIP ( dim_division[division_key], fact_vehicle[using_division_key] )
)
```

This keeps a single conformed `dim_division` (one `division_name` slicer) rather than two duplicated dimension instances, while still letting owner-vs-using measures coexist on one page. (Alternative — two physical `dim_division` copies — was rejected: it duplicates the slicer and breaks single-slicer sync.)

**No fleet <-> ferry relationship (locked).** `fact_vehicle` is a **cross-sectional availability snapshot** with **no ferry time grain** (no `date_key`/`time_key`), and `fact_ferry` has no vehicle key. The two fact tables are **kept independent — there is NO relationship between `fact_vehicle` and `fact_ferry`.** They share only the model, not a join; each page filters its own fact table via its own dimensions.

---

## Power BI Theme (City of Toronto civic)

**D-01.** Import this theme via **View -> Themes -> Browse for themes**. Civic navy base (`#003F87`) with accessible accents and standard fonts; **status colors are color-locked** to semantics (see the lock rule below the JSON).

```json
{
  "name": "City of Toronto — Fleet Services Civic",
  "dataColors": [
    "#003F87", "#0072CE", "#4B9CD3", "#6E7B8B",
    "#8C9BAB", "#2E7D32", "#C62828", "#B58900"
  ],
  "background": "#FFFFFF",
  "foreground": "#1A1A1A",
  "tableAccent": "#003F87",
  "good": "#2E7D32",
  "neutral": "#6E7B8B",
  "bad": "#C62828",
  "maximum": "#003F87",
  "center": "#8C9BAB",
  "minimum": "#C62828",
  "textClasses": {
    "title":    { "fontFace": "Segoe UI Semibold", "fontSize": 14, "color": "#003F87" },
    "header":   { "fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#003F87" },
    "label":    { "fontFace": "Segoe UI", "fontSize": 10, "color": "#1A1A1A" },
    "callout":  { "fontFace": "Segoe UI", "fontSize": 28, "color": "#003F87" }
  }
}
```

**Status color-lock rule (applied everywhere).** **Red (`#C62828`) = below class target; green (`#2E7D32`) = at or above target.** Apply this lock to **every** gap-to-target visual and to **all** conditional formatting (the by-class availability bars/bullets, the exception-list table, the disposal screen, the YoY callouts). Never reuse red/green for any non-status meaning. `good`/`bad` in the theme are bound to this lock so default conditional formatting inherits the correct semantics.

**Accessibility note.** Do **not** rely on red/green **alone**. Pair every status color with **sign** and **position**: show the signed gap value (e.g. `-0.0588`, with the leading minus, never `abs()`) and **sort worst-first** (gap ascending) so the worst items read at the top regardless of color perception. This keeps the panel reading correct for color-vision-deficient viewers and in the grayscale PDF export.

---

## Slicer Plan

**D-06.** Three **synced core** slicers across all three pages, plus two Ferry-page-local slicers. Set **Sync slicers** (View -> Sync slicers) so the core three share selection on every page.

| Page(s) | Slicer field (Gold column) | Slicer type | Sync scope |
|---------|----------------------------|-------------|------------|
| All 3 pages | `dim_division[division_name]` (Division) | Dropdown | **Synced** across Fleet / Ferry / Summary |
| All 3 pages | `fact_vehicle[UNIT_TYPE]` (Asset Class — 5 audit labels) | Dropdown (multi-select) | **Synced** across all pages |
| All 3 pages | `dim_date[year]` (Year) | Dropdown / tile list | **Synced** across all pages |
| Ferry page only | `fact_ferry[season]` (Season) | List (4 tiles) | **Page-local** (not synced) |
| Ferry page only | `fact_ferry[daypart]` (Daypart) | List | **Page-local** (not synced) |

**Default interaction = cross-highlight (NOT full cross-filter).** Set the default visual interaction to **cross-highlight** so that clicking a bar/segment **highlights** related context in the other visuals while keeping the full distribution visible during live drill (rather than filtering everything down and losing context). Override to cross-filter only on a specific visual where filtering-down is the intended drill. The synced **Division / Asset Class / Year** slicers carry the global filter context; the page-local **Season / Daypart** slicers refine the Ferry page only.

---

## Page 1 — Fleet Maintenance

**AG theme (lead): downtime / availability — 2019.AU2.2.** This page answers "how available is the fleet, by audit class, against the cited targets, and which units fall short?" plus the cross-dataset underutilization/disposal value-add. Every DAX block below is transcribed from [`measures_spec.md`](measures_spec.md) **with the D-04 Column Reference Reconciliation corrections applied** (`fact_vehicle[AVAILABILITY_YTD]`, `fact_vehicle[Utilization]`, `fact_vehicle[specialized_units]`; class target via `RELATED(dim_class_target[target])` through the **`UNIT_TYPE`** relationship R5, **not** the `DimClassTarget[Target]` placeholder). All availability measures **exclude the 209 NULL `AVAILABILITY_YTD` values** (denominator **4,405**). Status color is **red = below class target / green = at-or-above**, signed (never `abs()`), sorted worst-first.

| Visual | Type | Fields (Gold cols) | DAX measure | SQL validation value | DQ footnote |
|--------|------|--------------------|-------------|----------------------|-------------|
| **A1 — Overall Availability Rate (pooled)** | KPI card | `fact_vehicle[AVAILABILITY_YTD]` | `Availability Rate (Pooled) = DIVIDE ( SUM ( fact_vehicle[AVAILABILITY_YTD] ), COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) ) ) )` | **0.8899** | Pooled per-vehicle mean (weights each vehicle equally), **NOT** average-of-averages. Excludes the **209 NULLs**; denominator **4,405**. Guard: the mean-of-class-means **0.8786** is the WRONG total — ship only as a guard, never as the headline. |
| **A2 — Availability by Class vs Target** | Clustered bar **or** bullet / bar-with-target-line (gap-to-target) | axis `fact_vehicle[UNIT_TYPE]` (or `dim_class_target[class_label]` via R5); value `[Availability Rate by Class]`; target line `[Class Target] / 100` | `Availability Rate by Class = DIVIDE ( SUM ( fact_vehicle[AVAILABILITY_YTD] ), COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) ) ) )`  ·  `Class Target = AVERAGEX ( VALUES ( fact_vehicle[UNIT_TYPE] ), RELATED ( dim_class_target[target] ) )`  ·  `Gap to Target = [Availability Rate by Class] - DIVIDE ( AVERAGEX ( VALUES ( fact_vehicle[UNIT_TYPE] ), RELATED ( dim_class_target[target] ) ), 100 )` | rates: Light **0.9149** / Medium **0.8612** / Heavy **0.7948** / Off-Road **0.8882** / Other **0.9337**; targets **95 / 92 / 85 / 88 / 90**; **signed** gaps: Light **-0.0351** / Medium **-0.0588** / Heavy **-0.0552** / Off-Road **+0.0082** / Other **+0.0337** | Targets are **audit-cited, never recalculated** (AG 2019.AU2.2 / May 2023 FSD General Government Committee report). Class-fair: each class judged against its own bar. Color-lock: red below / green at-or-above. Signed, never `abs()`. Light/Medium/Heavy are below; Off-Road/Other clear. |
| **A3 — Exception List (critically-low units)** | Table / matrix, sorted `Gap to Target` **ascending** (worst first) | rows `fact_vehicle[UNIT_NO]`, `fact_vehicle[UNIT_TYPE]`, `dim_class_target[class_label]`, `fact_vehicle[AVAILABILITY_YTD]`, `[Class Target]`, `[Gap to Target]`, `fact_vehicle[Utilization]` | `Below Target Unit Count = COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) && fact_vehicle[AVAILABILITY_YTD] < DIVIDE ( RELATED ( dim_class_target[target] ), 100 ) ) )` | **1,734** | One threshold rule (below class target). The strict `<` **excludes NULL availability** (consistent with the 209-NULL exclusion). The named drill-down for the downtime theme (AU2.2). |
| **A4 — Underutilization Rate** | KPI card + by-using-division clustered bar (+ Specialized Share) | `fact_vehicle[Utilization]`, `fact_vehicle[specialized_units]`; using-division via R4 (`USERELATIONSHIP` to `fact_vehicle[using_division_key]`) | `Underutilization Rate = DIVIDE ( CALCULATE ( COUNTROWS ( fact_vehicle ), fact_vehicle[Utilization] = "Underutilized" ), CALCULATE ( COUNTROWS ( fact_vehicle ), NOT ISBLANK ( fact_vehicle[Utilization] ) ) )`  ·  `Specialized Share = DIVIDE ( CALCULATE ( COUNTROWS ( fact_vehicle ), fact_vehicle[specialized_units] = "Yes" ), CALCULATE ( COUNTROWS ( fact_vehicle ), NOT ISBLANK ( fact_vehicle[Utilization] ) ) )` | **0.0572 ≈ 5.8%** over the **2,080** matched light-duty units; Specialized Share per using division in `underutilization_by_division.csv` (e.g. Facilities Mgmt & Real Estate **0.719**) | **5.8% computed vs ~14% cited** reconciliation (AG 2019.AU2.3): the supplied light-duty snapshot classifies 5.8% as Underutilized vs the ~14% audit baseline — a period / right-sizing insight, not an error. Classification is **pre-applied, never recomputed**. Denominator = 2,080 matched units (availability⋈utilization join). By-**using**-division via `USERELATIONSHIP` (R4). |
| **A5 — Disposal-Candidate screening list** | Table / matrix, sorted worst-first; **labeled "screening list for SME review"** | rows `fact_vehicle[UNIT_NO]`, `fact_vehicle[UNIT_TYPE]`, `fact_vehicle[AVAILABILITY_YTD]`, `[Gap to Target]`, `fact_vehicle[Utilization]` | `Disposal Candidate Count = COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) && fact_vehicle[AVAILABILITY_YTD] < DIVIDE ( RELATED ( dim_class_target[target] ), 100 ) && fact_vehicle[Utilization] = "Underutilized" ) )` | **34** | **SME screening list, NEVER a disposal decision.** Below class target (same single D-01 rule as A2/A3 — no second floor) **AND** pre-classified `Underutilized`. This is the cross-dataset **availability⋈utilization value-add** (the join most candidates miss). Footnote: **6 unmatched `UNIT_NO`** fall outside `fact_vehicle` by design (documented in [DQ report](dq_report.md) §7); they have no availability row to attach to. |

**AG-theme traceability (page end).** A1–A3 map to **AU2.2** (downtime / availability); A4 maps to **AU2.3** (underutilization); A5 maps to **AU2.2 + AU2.3** (low availability **and** underutilized — the cross-dataset screen). The disposal screen stays a **screening list for SME review, never a disposal decision**; the 34-unit shortlist is the differentiating value-add, surfaced with its provenance (6 unmatched units, 209 excluded NULLs / 4,405 denominator) attached so the panel reading stays defensible.

---

## Page 2 — Ferry Operations

**AG theme (lead): demand / staffing — the ridership story.** This page answers "how has ferry demand moved over time, when does it peak, and what does the sales-vs-redemption gap tell us?" It is a **standalone fact table** — there is **NO relationship between `fact_ferry` and `fact_vehicle`** (locked; see Model Setup). Every DAX block below is transcribed from [`measures_spec.md`](measures_spec.md) §"Ferry Operations (Domain B)" **with the D-04 Column Reference Reconciliation corrections applied**: ferry measure columns carry an **embedded space** so they are **always bracketed** (`fact_ferry[Sales Count]`, `fact_ferry[Redemption Count]`); all time-intelligence DAX references **`dim_date[date_key]`** (there is no bare `date` column); the heatmap column axis is **`dim_time[hour]`** (the Gold `hour` column, per the D-04 reconciliation row). Signed gaps are shown signed (never `abs()`).

| Visual | Type | Fields (Gold cols) | DAX measure | SQL validation value | DQ footnote |
|--------|------|--------------------|-------------|----------------------|-------------|
| **B1 — Lifetime Totals** | KPI cards (2) | `fact_ferry[Sales Count]`, `fact_ferry[Redemption Count]` | `Lifetime Sales = SUM ( fact_ferry[Sales Count] )`  ·  `Lifetime Redemptions = SUM ( fact_ferry[Redemption Count] )` | Sales **13,257,804** / Redemptions **13,076,317** | All 15-min intervals, full span **May 2015 → Jun 2026** (partial years **included** for lifetime totals). Both columns carry an embedded space — bracket them. |
| **B2 — Year-over-Year Trend** | Line chart with a **2020-dip callout** | axis `dim_date[year]`; value `[Sales by Year]`; growth `[Sales YoY Growth]` | `Sales by Year = CALCULATE ( SUM ( fact_ferry[Sales Count] ), dim_date[year] >= 2016 && dim_date[year] <= 2025 )`  ·  `Sales YoY Growth = DIVIDE ( [Sales by Year] - CALCULATE ( [Sales by Year], DATEADD ( dim_date[date_key], -1, YEAR ) ), CALCULATE ( [Sales by Year], DATEADD ( dim_date[date_key], -1, YEAR ) ) )` | 2019 **1,249,725** / 2020 **366,606** / 2020 YoY **−0.7067** | **2020 < 2019 COVID dip** is a locked guard (`tests/test_kpis.py`). YoY restricted to **complete years 2016–2025**; partial 2015/2026 excluded from YoY only (still counted in B1 lifetime). DATEADD uses **`dim_date[date_key]`** (no bare `date`); `DIVIDE` guards the first-year null denominator. |
| **B3 — Seasonality Profile** | Column / line (by calendar month) | axis `dim_date[month]` (label `month_name`); value `[Sales by Month]`; optional `fact_ferry[season]` grouping | `Sales by Month = CALCULATE ( SUM ( fact_ferry[Sales Count] ), ALLEXCEPT ( dim_date, dim_date[month] ) )` | profile in `data/kpi/ferry_seasonality` — **summer (Jun–Aug) peaks**, winter troughs | Pools **every year by calendar month** — **no annualization / partial-year estimation.** Reuses the Phase-2 `fact_ferry[season]` derivation. |
| **B4 — Day-of-Week × Hour Heatmap** | Matrix with conditional-formatting color scale | rows `fact_ferry[day_of_week]` × columns **`dim_time[hour]`**; values `[Sales by DoW x Hour]` | `Sales by DoW x Hour = SUM ( fact_ferry[Sales Count] )` | long-form grid in `data/kpi/ferry_heatmap.csv` | All data. Column axis is **`dim_time[hour]`** (the Gold column is named `hour` per the D-04 reconciliation table; the placeholder in `measures_spec.md` is corrected here). Reuses the Phase-2 `day_of_week` derivation. Drives the staffing read. |
| **B5 — Sales-Redemption Gap** | **Signed** bar (never `abs()`) | axis `dim_date[year]`; value `[Sales-Redemption Gap]` (reuses `fact_ferry[sales_redemption_gap]`) | `Sales-Redemption Gap = SUM ( fact_ferry[Sales Count] ) - SUM ( fact_ferry[Redemption Count] )` | 2016 **+92,649** / 2020 **−7,940** (`sales_redemption_gap.csv` `total_gap`) | **Signed** (`Sales − Redemption`, never `abs()`). The sales-vs-redemption interpretation is **flagged for SME validation** ([DQ report](dq_report.md) A3) — the exact business meaning of "sales" vs "redemption" is a stated assumption to confirm. |
| **B6 — Distribution Stats** | KPI cards (2) | `fact_ferry[Sales Count]` | `Sales Max = MAX ( fact_ferry[Sales Count] )`  ·  `Sales Median = MEDIAN ( fact_ferry[Sales Count] )` | Max **7,229** / Median **12** | Median **12** vs max **7,229** = **heavy right skew** driven by real peak windows (summer weekends/holidays), **not a data error.** Locked distribution guard (`ferry_sales_max == 7229`). |

**Ferry-page interaction note.** The two page-local slicers — `fact_ferry[season]` and `fact_ferry[daypart]` (D-06) — refine this page only and are **not** synced to Pages 1/3. The synced Division/Asset-Class slicers have **no effect** on ferry visuals (no fleet↔ferry relationship); only the synced **Year** slicer (`dim_date[year]`) cross-filters the ferry trend via the R1 date relationship.

---

## Page 3 — Summary / Insights

**AG-themes-first (D-02).** This is the executive landing page. It leads with the **two Auditor General themes** and keeps the cross-dataset disposal screen visually prominent as the differentiator. **No new DAX is authored here** — every tile **reuses** a measure already defined on Page 1 (Fleet Maintenance) or Page 2 (Ferry Operations); the visuals are compact summary tiles over those existing measures. Status color stays **color-locked** (red `#C62828` = below class target; green `#2E7D32` = at-or-above), signed (never `abs()`), worst-first. Read top-to-bottom in this **exact order**:

| # | Theme block | Visual(s) | Reuses (measure → source page) | Lead value / read | AG / DQ note |
|---|-------------|-----------|--------------------------------|-------------------|--------------|
| **1** | **DOWNTIME (lead)** | Headline KPI card + a compact **gap-to-target bar** by class (worst-first) | `[Availability Rate (Pooled)]` (A1, Page 1) · `[Availability Rate by Class]` + `[Gap to Target]` (A2, Page 1) | Pooled availability **0.8899**; signed gaps Light **−0.0351** / Medium **−0.0588** / Heavy **−0.0552** below benchmark; Off-Road **+0.0082** / Other **+0.0337** clear it | **AG 2019.AU2.2.** Targets audit-cited, never recalculated. Color-lock red below / green at-or-above. 209 NULLs excluded (denom **4,405**). |
| **2** | **UNDERUTILIZATION** | KPI card with the **5.8% vs ~14%** reconciliation callout | `[Underutilization Rate]` (A4, Page 1) | **5.8%** computed (`0.0572`) over **2,080** matched light-duty units **vs ~14%** audit baseline (Mar 2023) | **AG 2019.AU2.3.** A **period / right-sizing** insight, **not an error** — classification is pre-applied, never recomputed. Reconciliation note carried verbatim. |
| **3** | **34-UNIT DISPOSAL SCREENING LIST** *(prominent — the differentiator)* | A **prominent screening-list table** (worst-first), larger than the surrounding tiles | `[Disposal Candidate Count]` (A5, Page 1) | **34** units that are **both** below class target **and** pre-classified `Underutilized` — the availability⋈utilization cross-dataset value-add | **Labeled "screening list for SME review, never a disposal decision."** AG 2019.AU2.2 **+** AU2.3. Provenance attached: **6 unmatched `UNIT_NO`** + 209 excluded NULLs / 4,405 denom. |
| **4** | **FERRY DEMAND** *(last)* | Small-multiple / sparkline of the YoY trend + a peak-window callout | `[Sales by Year]` / `[Sales YoY Growth]` (B2, Page 2) · `[Sales by DoW x Hour]` (B4, Page 2) | The **2020 < 2019 COVID dip** (`−0.7067`); summer + midday peak windows drive staffing | Demand/staffing context, placed **after** the two AG themes. Reuses Page-2 measures; no new DAX. |

**Why this order.** The panel reads downtime → underutilization first because those are the audit's two named themes (AU2.2 / AU2.3). The **34-unit disposal screen sits third and visually prominent** because it is the cross-dataset join most candidates miss — the differentiating value-add — framed honestly as an **SME screening list, never a disposal decision**. Ferry demand lands last as supporting operational context.

---

## DQ Footnotes (consolidated)

These are the locked, audit-defensible **stated assumptions** surfaced as footnotes / tooltips across all three pages (full detail in the [DQ report](dq_report.md)):

1. **209 excluded NULL availabilities (denominator 4,405).** `AVAILABILITY_YTD` has **209** genuine NULLs (4.53%); the locked decision is **exclude, never impute** — every availability rate uses the **4,405** non-null denominator ([DQ report](dq_report.md) §availability; regression-guarded so the non-null count stays exactly 4,405).
2. **6 unmatched `UNIT_NO` (availability⋈utilization join).** Of the light-duty utilization rows, **6** have no matching availability row and fall outside `fact_vehicle` by design ([DQ report](dq_report.md) §7, `test_unmatched_6`). The 2,080 matched count is the underutilization/disposal denominator; the 6 unmatched are documented, not dropped silently.
3. **Sales-vs-redemption interpretation flagged for SME validation.** The exact business meaning of ferry "sales" vs "redemption" is a **stated assumption** flagged for SME validation ([DQ report](dq_report.md) A3); the signed `sales_redemption_gap` is shown signed, never `abs()`.

All three are **audit-defensible stated assumptions**, surfaced openly so the panel reading stays honest and reproducible.

---

## PDF Export Layout

**D-08.** Produce a **three-page** PDF, one page per report page, for the panel hand-off:

| PDF page | Report page | Orientation / size | Fit |
|----------|-------------|--------------------|-----|
| 1 | **Page 1 — Fleet Maintenance** | 16:9 landscape | Fit to page |
| 2 | **Page 2 — Ferry Operations** | 16:9 landscape | Fit to page |
| 3 | **Page 3 — Summary / Insights** | 16:9 landscape | Fit to page |

**Before exporting**, set each report page's **Canvas size = 16:9** in Power BI (Format pane → Canvas settings → Type = 16:9) so the export is landscape and fit-to-page. Then **File → Export → PDF**. A one-page executive summary (Page 3 alone) is **optional**, not required. Keep the grayscale-safe accessibility convention (signed values + worst-first sort) so the PDF reads correctly without color.

---

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets (vehicle availability, light-duty utilization, Toronto Island Ferry ticket counts).
- **May 2023 FSD** General Government Committee report — the cited availability targets.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** — the downtime and underutilization themes.
- Licence: **Open Government Licence – Toronto**.

*This spec is a **text build contract**: DAX measures are transcribed from [`measures_spec.md`](measures_spec.md) (values locked in `data/kpi/` by `tests/test_kpis.py`) and corrected against the verbatim Gold headers via the D-04 reconciliation table. **No `.pbix` / PBIP / TMDL is generated** — the Power BI report canvas, relationships, theme, and slicers are authored **manually** in Power BI Desktop on top of the modeled output. Audit thresholds are **cited, never recalculated.** REPORT-01 satisfied — all three pages (Fleet Maintenance, Ferry Operations, Summary/Insights) specified, plus PDF-export layout and sources.*
