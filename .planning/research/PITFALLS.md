# Pitfalls Research

**Domain:** Fleet/transit analytics — DuckDB/pandas ETL + star-schema modeling + Power BI dimensional reporting + BA narrative deliverables
**Researched:** 2026-06-01
**Confidence:** HIGH (Power BI/DAX/pandas claims verified against Microsoft Learn, dax.guide, pandas 3.0 docs; dataset-specific traps derived from profiled schemas in the brief)

> **Locked decisions this file reinforces (do NOT re-litigate):**
> - Exclude the 209 null `AVAILABILITY_YTD` rows from rate calcs; flag as a DQ gap. **No imputation.**
> - Underutilization is **pre-classified** — surface it, never recompute. The km/engine-hour telematics logic is absent — cite the audit definition, never fabricate.
> - Availability dataset is **Retired** — point-in-time snapshot; state the pull date.
> - Ferry `Sales` = sold, `Redemption` = boarded is an **assumption to state**, not a fact.
> - 5.8% (current) vs 14% (audit, Mar 2023) underutilization is a **period / right-sizing difference**, not an error.
>
> Pitfalls below protect these decisions; they do not reopen them.

---

## Critical Pitfalls

### Pitfall 1: `UNIT_NO` join failure from zero-padding / type mismatch

**What goes wrong:**
Availability stores `UNIT_NO` as a **zero-padded string** (e.g. `"007421"`); Utilization stores it as an **int** (`7421`). A naive join on raw values matches almost nothing, or — worse — *silently* matches a subset and drops the rest with no error, because a string-to-int comparison either fails type-wise or coerces inconsistently. The brief's target is **2,080 of 2,086** utilization rows matching, leaving **6 legitimately unmatched** rows. The trap is producing the *wrong* unmatched count (e.g. 1,500 unmatched from a normalization bug) and either not noticing or blaming the data.

**Why it happens:**
Padding asymmetry (`"00500"` vs `500`), hidden whitespace, an `int` cast on a value with a non-numeric suffix, or DuckDB/pandas implicitly upcasting one side. People eyeball a few rows that happen to match and assume the whole join works.

**How to avoid:**
- Normalize **both** sides to one canonical form before joining. Recommended: cast to int via strip-leading-zeros (`CAST(TRIM(UNIT_NO) AS BIGINT)` in DuckDB, or `pd.to_numeric(s.str.lstrip("0"), errors="coerce")`), because the int side cannot be re-padded reliably without knowing the pad width. Keep the original string in a separate column for traceability.
- **Inspect the 6 unmatched rows explicitly** and document *what* they are (not just the count) — they are a DQ finding, not noise.
- Guard `errors="coerce"` introducing NaN: a `UNIT_NO` that fails to parse must be logged, not silently dropped.

**Warning signs:**
- Match count is not exactly 2,080 (anything materially off = normalization bug, not data).
- Join produces *more* rows than the smaller table (fan-out → duplicate keys on one side).
- Any `UNIT_NO` becomes NaN/NULL after normalization.

**Phase to address:** Phase 2 (Transform & Model).
**pytest checks:** assert matched count == 2,080 and unmatched == 6; assert no NaN in normalized key; assert join row count == utilization row count (no fan-out); assert the normalized key is unique in `fact_vehicle`.

---

### Pitfall 2: Computing availability averages over rows that include (or wrongly exclude) the 209 nulls

**What goes wrong:**
`AVERAGE`/`mean` semantics differ by tool. SQL `AVG()` and pandas `.mean()` skip NULL/NaN automatically; a hand-rolled `SUM(x)/COUNT(*)` does **not** (it divides by the full row count, treating null as 0 → understated availability). Conversely, if nulls were coerced to 0 during ingest, every average is silently dragged down. Either way the audit-benchmarked rate (mean ≈ 0.89) is wrong and the asset-class-vs-target comparison becomes indefensible.

**Why it happens:**
Mixing `COUNT(*)` with `SUM(metric)`; CSV ingest turning blank cells into `0` or `0.0`; or aggregating in Power BI where a blank measure behaves differently than expected. The locked decision is **exclude and flag**, but "exclude" must mean *exclude from both numerator and denominator*, not *treat as zero*.

**How to avoid:**
- Denominator must be **count of non-null `AVAILABILITY_YTD`** (4,614 − 209 = **4,405**), never 4,614, and never with nulls→0.
- Use `AVG(AVAILABILITY_YTD)` (DuckDB) / `.mean()` (pandas) which exclude NULL by design; if hand-rolling, use `SUM(x) / COUNT(x)` (both over the metric column) — never `COUNT(*)`.
- Keep nulls as genuine NULL/NaN through the whole pipeline; never let ingest coerce blanks to 0. Read the CSV with explicit `na_values` and a float dtype.
- Emit the exclusion count in the DQ report so the "209 excluded" choice is visible to the reader.

**Warning signs:**
- Overall availability materially below ~0.89.
- Denominator anywhere equals 4,614 in a rate calc.
- A min `AVAILABILITY_YTD` of exactly 0 that turns out to be an ex-null (distinguish true 0% units from coerced nulls).

**Phase to address:** Phase 1 (DQ baseline) for null preservation; Phase 3 (KPI layer) for denominator correctness.
**pytest checks:** assert null count == 209; assert non-null count == 4,405; assert overall availability rounds to ~0.89; assert no `AVAILABILITY_YTD == 0` that was originally null.

---

### Pitfall 3: DAX `AVERAGE` of an already-averaged YTD (average-of-averages)

**What goes wrong:**
`AVAILABILITY_YTD` is **already a per-vehicle ratio** (a rate, not a raw count). Taking `AVERAGE(fact_vehicle[availability_ytd])` gives an **unweighted mean of ratios** — every vehicle counts equally regardless of fleet weight. Rolling that up across asset classes by averaging the class averages compounds the error (average-of-averages ≠ overall average). A class with 5 vehicles distorts the total as much as one with 2,000. This is the single most common DAX correctness bug and verified as the canonical "average of averages" trap: `(40% + 10%)/2 = 25%` vs the true pooled `20%`.

**Why it happens:**
The metric *looks* like a value you can average, and `AVERAGE()` is the obvious function. Analysts forget that averaging a pre-computed rate silently changes the weighting.

**How to avoid:**
- **Decide and document the weighting** for each KPI. For "overall fleet availability," the brief frames it as `avg AVAILABILITY_YTD` → an unweighted vehicle-level mean is acceptable **as long as it's stated**. But the asset-class-vs-target comparison must roll up the *same way the audit did* (per-vehicle mean within class), and the grand total must NOT be the mean of the 5 class means.
- Prefer an explicit measure: `DIVIDE(SUMX(fact_vehicle, [availability_ytd]), COUNTROWS(filtered non-null))` so the denominator and weighting are visible, rather than relying on implicit `AVERAGE`.
- Compute the same KPI in SQL/pandas in Phase 3 and assert the DAX measure matches it — this catches average-of-averages immediately.

**Warning signs:**
- A "total" or "all classes" card that doesn't equal the pooled per-vehicle mean from the Phase 3 SQL.
- Class-level numbers look right but the grand total drifts.
- Measure uses bare `AVERAGE()` over a ratio column.

**Phase to address:** Phase 3 (define weighting in KPI doc) and Phase 4 (DAX measures spec).
**pytest checks:** Phase 3 produces the canonical overall + per-class availability numbers; the DAX spec must reproduce them. Assert grand-total availability == pooled mean, NOT mean-of-class-means (these differ unless classes are equal-sized — they aren't).

---

### Pitfall 4: DAX divide-by-zero / blank propagation in rates and gap measures

**What goes wrong:**
Underutilization rate by division, % below threshold, sales-to-redemption gap %, and availability ratios all divide. A division with zero qualifying vehicles, or a 15-min ferry window with zero redemptions, throws an error or returns blank that then poisons downstream visuals (blank totals, broken conditional formatting, `Infinity`).

**Why it happens:**
Using the `/` operator instead of `DIVIDE()`; not handling empty filter contexts created by slicers (e.g. a division with no underutilized vehicles).

**How to avoid:**
- Always use `DIVIDE(numerator, denominator, 0)` (or a blank alternate) — verified as the DAX-idiomatic safe-divide.
- For sales-to-redemption gap, decide whether the metric is an absolute count (`sales − redemption`) or a ratio; the **count** form has no divide-by-zero risk and is the safer default for the "gap over time" KPI. Reserve ratio forms for where a denominator is guaranteed non-zero.
- Test KPIs against a filter that yields an empty set.

**Warning signs:**
- Blank or error cards when a slicer narrows to a small division.
- `Infinity`/`NaN` appearing in exported PDF.

**Phase to address:** Phase 3 (define gap as count vs ratio) and Phase 4 (DAX `DIVIDE`).
**pytest checks:** Phase 3 rate functions return 0/None (per documented choice) for empty groups, not error.

---

### Pitfall 5: Ferry timestamp — forcing a timezone / mishandling DST on local wall-clock data

**What goes wrong:**
The 272,529 ferry rows are **local Toronto wall-clock** timestamps at 15-min grain over ~11 years (May 2015 → Jun 2026), each containing **22 DST transitions**. The instinct is to "do it properly" and localize to `America/Toronto`. But localizing wall-clock data that was *recorded* in wall-clock creates real failures: the spring-forward gap produces **nonexistent times** (→ `NaT` or a raised error) and the fall-back hour produces **ambiguous times** (duplicate-hour, `AmbiguousTimeError`). pandas docs confirm: a local-time series modeled without tz info yields duplicate hours each fall and a missing value each spring if you try to localize. Conversely, converting to UTC and then grouping by hour would **shift peak windows by an hour** for half the year — corrupting the day-of-week × hour-of-day staffing heatmap, which is a flagship insight.

**Why it happens:**
Over-engineering timezone handling for data that is single-timezone and already in the display timezone. Or the opposite: ignoring DST entirely and silently double-counting/gapping an hour twice a year.

**How to avoid:**
- **Keep the ferry timestamps tz-naive** (parse with `pd.to_datetime(...)`, no `tz_localize`). The data is Toronto-local and all reporting is Toronto-local — no conversion is needed or correct. **Document this as a stated assumption** alongside the Sales/Redemption interpretation.
- Derive `hour`, `day_of_week`, `is_weekend`, `season`, `daypart` directly from the naive local timestamp so the heatmap reflects what staff actually experience.
- If localization is ever required, use `tz_localize('America/Toronto', ambiguous='infer', nonexistent='shift_forward')` and validate row count is preserved — but the default recommendation is **don't localize**.
- Validate the parse: assert all 272,529 rows parse to valid datetimes (no `NaT`), assert grain is uniformly 15 minutes where contiguous, and assert min/max dates match May 2015 / Jun 2026.

**Warning signs:**
- Any `NaT` after timestamp parsing.
- Row count changes during timestamp handling.
- Two rows with the *same* local timestamp (could be a genuine fall-back duplicate, or a data dupe — investigate, don't silently dedupe).
- Peak-hour heatmap shifts by exactly one hour between summer and winter (sign of a UTC conversion bug).

**Phase to address:** Phase 2 (Transform — parsing + derived date/time fields).
**pytest checks:** assert no NaT post-parse; assert row count == 272,529 through parsing; assert min/max timestamps; assert derived `hour` ∈ 0–23 and `day_of_week` ∈ valid set.

---

### Pitfall 6: Skew-blind ferry aggregation (mean over a long-tailed distribution)

**What goes wrong:**
Ferry volume is **highly skewed** (median 12, max 7,229 per 15-min window). Reporting a plain **mean** of per-window volume buries the seasonality story and misleads on "typical" demand — the summer peak windows dominate the mean while ~half the windows sit near 12. A staffing recommendation built on the mean over-staffs the off-season and under-staffs peaks.

**Why it happens:**
Defaulting to `AVG` for everything; not profiling the distribution before choosing an aggregation.

**How to avoid:**
- For totals/trends (YoY, seasonal), **sum** — sums are robust to skew and answer "how much demand."
- For "typical window" framing, report **median and percentiles** (p50/p90/p95), not mean alone.
- The staffing heatmap should use **peak/high-percentile** volume per (day_of_week, hour) cell, not the mean, to size for demand. State which statistic each visual uses.
- Call out the **2020–2021 COVID dip explicitly** (the brief requires it) so the YoY trend isn't read as organic decline.

**Warning signs:**
- A single "average tickets per window" headline number with no distribution context.
- Seasonality flattened because annual means hide the summer spike.

**Phase to address:** Phase 3 (KPI definitions — choose statistic per metric) and Phase 4 (specify which stat each visual shows).
**pytest checks:** assert max window ≈ 7,229 and median ≈ 12 (sanity on skew); assert YoY 2020 < 2019 (COVID dip present).

---

### Pitfall 7: Star-schema modeling errors in Power BI (bidirectional, missing date table, ambiguous grain)

**What goes wrong:**
Three classic dimensional-modeling failures, all verified against Microsoft Learn guidance:
1. **Bidirectional ("Both") relationships set everywhere** to "make visuals work" → ambiguous filter paths, incorrect totals, and degraded performance. Microsoft Learn explicitly warns ambiguity arises when multiple filter-propagation paths exist.
2. **No dedicated `dim_date`** (relying on Power BI auto date/time or the fact's own timestamp) → time-intelligence functions (`SAMEPERIODLASTYEAR`, `DATESYTD`) behave wrongly or break; YoY/seasonality KPIs become unreliable.
3. **Ambiguous fact grain** — mixing the vehicle 1-row-per-unit grain with the ferry 15-min grain, or trying to relate `fact_vehicle` and `fact_ferry` (they share no key and must stay **separate domains**).

**Why it happens:**
"Both" is the quick fix when a slicer doesn't filter as expected; auto date/time is on by default; analysts try to force one model to span two unrelated domains.

**How to avoid:**
- **Single-direction relationships** from dimensions (one-side) to facts (many-side). Filter flows naturally dim → fact. Only use bidirectional via per-measure `CROSSFILTER`/`TREATAS` if genuinely required, never as the model default.
- Build an explicit **`dim_date`** (continuous date range covering 2015→2026, with year/quarter/month/day/day_of_week/is_weekend/season) and a **`dim_time`** (hour, 15-min slot, daypart). Mark `dim_date` as the date table. Turn **off** Power BI auto date/time.
- Keep **two independent stars**: Fleet (`dim_division` + enriched `fact_vehicle`) and Ferry (`dim_date` + `dim_time` + `fact_ferry`). Do not relate them. The single enriched `fact_vehicle` (doubling as vehicle dim) is idiomatic here because availability⋈utilization is 1:1 per vehicle — but ensure it stays 1:1 (see Pitfall 1 fan-out).
- The `dim_date` must be **gapless** (every day present) or time-intelligence silently misfires.

**Warning signs:**
- Any relationship cross-filter set to "Both" in the model.
- A measure total that doesn't match the SQL ground-truth.
- Date slicer missing dates / time-intelligence returning blanks.
- A relationship attempted between `fact_vehicle` and `fact_ferry`.

**Phase to address:** Phase 2 (build gapless `dim_date`/`dim_time` in the modeled output) and Phase 4 (relationship + date-table guidance in the report spec).
**pytest checks (on modeled tables):** assert `dim_date` is gapless and spans min(ferry) → max(ferry); assert `fact_vehicle` key is unique (1:1); assert `dim_time` covers all 96 15-min slots.

---

### Pitfall 8: BA credibility traps — unsourced claims, ignored audit framing, over-claimed causation

**What goes wrong:**
This is an **assessed BA deliverable** judged on defensibility (70% pass → panel interview). The credibility killers:
- **Unsourced numbers** — quoting targets (95/92/85/88/90), the ~14% audit figure, or the $411K savings without citing the May 2023 FSD report / AG review.
- **Ignoring the AG audit framing** — presenting generic fleet KPIs instead of anchoring on the two AG themes (downtime 2019.AU2.2, underutilization 2019.AU2.3). The whole value proposition is tying analysis to the audit narrative.
- **Over-claiming causation** — e.g. "older vehicles *cause* lower availability" from a correlation, or "disposal candidates" stated as decisions rather than *candidates* for review. The availability⋈utilization cross-measure flags **disposal candidates** (low availability AND underutilized) — it must be framed as a screening list for SME review, not a verdict.
- **Mis-stating the 5.8% vs 14%** as a data error or contradiction instead of a period/right-sizing difference.
- **Presenting the retired snapshot as live** without the pull date, or the Sales/Redemption interpretation as fact.

**Why it happens:**
Analysts optimize for a slick dashboard and under-invest in the narrative and sourcing that a public-sector, audit-grounded audience actually weighs.

**How to avoid:**
- Every benchmark, target, and external figure carries an inline citation to its source (Open Data, May 2023 FSD report, AG 2019.AU2.2/2.3, Open Government Licence – Toronto).
- Open both narrative deliverables and the dashboard summary page with the **AG theme framing**; map each KPI back to downtime or underutilization.
- Use hedged, decision-support language: "candidates for review," "associated with," "suggests" — reserve causal claims for where the data supports them. Disposal candidates = a *list to investigate*, validated by SMEs (the two Directors).
- State assumptions on the dashboard itself (pull date, Sales=sold/Redemption=boarded, 209 excluded, 5.8% vs 14% is period/right-sizing) — a visible assumptions/methodology note is a credibility *gain*, not a weakness.

**Warning signs:**
- Any number on a slide without a traceable source.
- "Disposal" / "remove these vehicles" phrased as a recommendation rather than a screening output.
- The 5.8% vs 14% gap described as an error or inconsistency.
- No mention of the AG audit on the summary page.

**Phase to address:** Phase 1 (capture assumptions + sources), Phase 3 (benchmark validation cites the audit), Phase 5 (narrative grounding + hedged language), Phase 6 (README citations).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Coerce CSV blanks to 0 on ingest | Simpler dtypes, no NaN handling | Silently corrupts the 209-null exclusion and drags availability down | **Never** — preserve NULL/NaN |
| `INNER JOIN` availability⋈utilization without inspecting unmatched | Clean 2,080-row output | Loses the 6 unmatched rows as a DQ finding; hides normalization bugs | Only after the 6 are explicitly profiled and documented |
| Bare `AVERAGE()` over `availability_ytd` for grand totals | One-line measure | Average-of-averages error vs audit benchmark | Only for the explicitly unweighted "avg AVAILABILITY_YTD" KPI, stated as such |
| Plain mean for ferry volume visuals | Familiar aggregation | Misleads on skewed demand; bad staffing advice | Never for "typical/peak" framing; sums are fine for totals |
| Power BI auto date/time instead of `dim_date` | No modeling work | Breaks time intelligence; can't do clean YoY/seasonality | Never for this project (YoY is a required KPI) |
| Localize ferry timestamps to be "correct" | Feels rigorous | Injects NaT/ambiguous-hour errors on single-tz local data | Never — keep tz-naive, document assumption |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| DuckDB → Parquet → Power BI | Float availability re-typed or nulls lost on round-trip | Verify dtypes survive Parquet; confirm NULL stays NULL (not NaN→0) in Power BI import |
| pandas ↔ DuckDB `UNIT_NO` | One side int, one side string → silent mismatch | Normalize to a single canonical type before the boundary; assert uniqueness |
| Modeled tables → Power BI relationships | Relating `fact_vehicle` to `fact_ferry`; "Both" direction | Two separate stars; single-direction dim→fact only |
| `dim_date` ↔ `fact_ferry` | Date table with gaps or shorter range than facts | Gapless `dim_date` covering full 2015→2026 span; mark as date table |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Bidirectional relationships across the model | Slow visuals, wrong totals | Single-direction; per-measure `CROSSFILTER` only if needed | Worsens as relationship count grows |
| 272k ferry rows at raw 15-min grain in every visual | Sluggish heatmap/trend rendering | Pre-aggregate to day/hour where the visual needs it; let the star + `dim_date` do the grouping | Noticeable but manageable at 272k; pre-aggregation keeps it snappy |
| Auto date/time hidden tables per datetime column | Bloated model, slow refresh | Disable auto date/time; one shared `dim_date` | Compounds with multiple datetime columns |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Treating Open Data as unrestricted | Licence non-compliance | Cite Open Government Licence – Toronto; attribute the City as source |
| Publishing without an assumptions/methodology note | Misreading retired snapshot as live; misattributed figures | Visible methodology/assumptions panel (pull date, exclusions, interpretations) |

> (No PII/credential surface — datasets are public, aggregate vehicle/ferry counts. Primary "security" concern is licence/attribution and transparency.)

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Mean-based ferry headline on skewed data | Stakeholders misjudge "typical" demand | Median + percentiles for typical; peaks for staffing |
| No gap-to-target on the flagship availability-by-class visual | Reader can't see how far from audit target | Show actual, target, and gap together (audit framing) |
| Exception lists without drill-through | Can't act on critically low / disposal-candidate units | Drill-through to unit-level detail |
| 2020–21 dip unexplained on YoY | Read as organic decline | Annotate the COVID dip explicitly |
| Assumptions hidden in an appendix | Credibility questioned in panel | Surface assumptions on the dashboard |

## "Looks Done But Isn't" Checklist

- [ ] **Availability⋈utilization join:** verify match == 2,080 *and* the 6 unmatched are profiled and explained — not just counted.
- [ ] **Availability average:** verify denominator == 4,405 (non-null), nulls preserved end-to-end, no null→0 coercion.
- [ ] **Overall vs class availability:** verify grand total is the pooled mean, NOT mean-of-class-means.
- [ ] **Ferry timestamps:** verify tz-naive, no NaT, row count preserved (272,529), grain intact, COVID dip present.
- [ ] **`dim_date`:** verify gapless and spans full ferry date range; auto date/time disabled.
- [ ] **Relationships:** verify all single-direction; `fact_vehicle` and `fact_ferry` unrelated.
- [ ] **DAX rates:** verify `DIVIDE` used (no `/`); empty-filter contexts return 0/blank not error.
- [ ] **Sourcing:** verify every external number (targets, 14%, $411K) carries a citation.
- [ ] **Framing:** verify AG themes appear; disposal candidates phrased as a review list; 5.8% vs 14% framed as period/right-sizing.
- [ ] **Assumptions stated:** pull date, Sales=sold/Redemption=boarded, 209 excluded.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong join match count | LOW | Re-normalize key to canonical int; re-run join-integrity tests; re-profile unmatched |
| Nulls coerced to 0 upstream | MEDIUM | Re-ingest with explicit `na_values`/dtype; re-run all availability KPIs; the 0-vs-null distinction must be rebuilt |
| Average-of-averages in DAX | LOW | Replace `AVERAGE` with `DIVIDE(SUMX(...), COUNTROWS(...))`; reconcile against Phase 3 SQL |
| Localized ferry timestamps (NaT/ambiguous) | MEDIUM | Revert to tz-naive parse; rebuild date/time derived fields and heatmap; re-validate row count |
| Bidirectional relationships shipped | LOW | Set all to single-direction; re-test totals against SQL; add `CROSSFILTER` only where a specific measure needs it |
| Unsourced claims surfaced in panel | HIGH (reputational) | Hard to recover live — prevent in Phase 5/6 with inline citations |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. `UNIT_NO` join failure | Phase 2 (Transform) | pytest: match==2,080, unmatched==6, no NaN key, no fan-out, unique key |
| 2. Null-handling in averages | Phase 1 (DQ) + Phase 3 (KPI) | pytest: null==209, denom==4,405, overall≈0.89, no ex-null zeros |
| 3. Average-of-averages (DAX) | Phase 3 (KPI doc) + Phase 4 (DAX spec) | Phase 3 canonical numbers; DAX grand total == pooled mean |
| 4. Divide-by-zero (DAX) | Phase 3 (gap def) + Phase 4 (DIVIDE) | pytest: rate fns handle empty groups; DAX uses `DIVIDE` |
| 5. Timestamp/DST | Phase 2 (Transform) | pytest: no NaT, row count==272,529, min/max dates, valid hour/dow |
| 6. Skew-blind aggregation | Phase 3 (stat choice) + Phase 4 (visual stat) | pytest: skew sanity (max≈7,229, median≈12), 2020 dip present |
| 7. Star-schema/bidirectional/date table | Phase 2 (build dims) + Phase 4 (model guidance) | pytest: gapless `dim_date`, unique vehicle key, full 15-min slots; spec mandates single-direction + date table |
| 8. BA credibility (sourcing/causation/framing) | Phase 1 + 3 + 5 + 6 | Review: every number cited; AG framing present; hedged language; assumptions visible |

## Sources

- [Bi-directional relationship guidance — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-bidirectional-filtering) — single-direction default; bidirectional only when necessary, per-measure (HIGH)
- [Understand star schema and the importance for Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) — dim→fact filter flow, dedicated date table (HIGH)
- [Model relationships in Power BI Desktop — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand) — ambiguous path mechanics (HIGH)
- [There are ambiguous paths in Power BI — Tabular Editor](https://tabulareditor.com/blog/there-are-ambiguous-paths-in-power-bi) — ambiguity from multiple propagation paths (MEDIUM)
- [Killing me softly… Bi-directional relationships in Power BI — Data Mozart](https://data-mozart.com/killing-me-softly-bi-directional-relationships-in-power-bi/) — performance/correctness cost of "Both" (MEDIUM)
- [AVERAGEX — DAX Guide](https://dax.guide/averagex/) — iterator semantics, context transition (HIGH)
- [AVERAGE function (DAX) — Microsoft Learn](https://learn.microsoft.com/en-us/dax/average-function-dax) — single-column mean semantics (HIGH)
- [Understanding the Average of Averages — Oreate AI](https://www.oreateai.com/blog/understanding-the-average-of-averages-in-excel-pivot-tables/b08806e6e81a14cfe300cb4a67010c33) — pooled vs mean-of-means worked example (MEDIUM)
- [pandas.Series.dt.tz_localize — pandas 3.0 docs](https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.tz_localize.html) — ambiguous/nonexistent params, DST handling (HIGH)
- [Hidden Timezone Issues: Pandas Timestamp Edge Cases and DST Gotchas — Medium](https://medium.com/@ThinkingLoop/hidden-timezone-issues-pandas-timestamp-edge-cases-and-dst-gotchas-08eeab53e692) — duplicate-hour / missing-value on local series (MEDIUM)
- Project brief `Fleet_Services_GSD_Project_Brief.md` and `.planning/PROJECT.md` — profiled schemas, join model, locked decisions, audit framing (HIGH, primary source)

---
*Pitfalls research for: fleet/transit analytics ETL + star-schema + Power BI dimensional reporting*
*Researched: 2026-06-01*
