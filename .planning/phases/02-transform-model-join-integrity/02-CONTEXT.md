# Phase 2: Transform, Model & Join Integrity - Context

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the **Gold star schema** as type-preserving Parquet (plus readable CSV) on top of the Phase 1 Bronze tables. Five Gold tables — `dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time` — with the value-added **availability ⋈ utilization** join correct and tested. This is the critical-path node the disposal-candidate cross-measure, ferry heatmap, and time-intelligence (Phases 3–4) all depend on.

Discussion clarified **HOW** to model and derive within this scope. The following are already **locked by the roadmap** and are NOT open decisions: canonical-integer `UNIT_NO` normalization on both sides; ferry `Timestamp` parsed tz-naive and rounded to 15-min slots (no NaT, row count == 272,529); the derived-field list (`fleet_age`, `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`); join targets matched == 2,080 / unmatched == 6; gapless `dim_date` (2015→2026); 96-row `dim_time`; Parquet + CSV export.

</domain>

<decisions>
## Implementation Decisions

### fact_vehicle grain & join
- **D-01:** `fact_vehicle` is anchored on the **full fleet — all 4,614 availability rows** — with a **LEFT JOIN to utilization**. `Utilization` and `Specialized units` (and any using-division attribute) are NULL for the ~2,528 non-light-duty units. Rationale: availability-by-asset-class must span the whole fleet (Light/Medium/Heavy/Off-Road/Other vs audit targets), while the disposal-candidate cross-measure runs on the matched light-duty subset.
- **D-02:** The join is `bronze_availability LEFT JOIN bronze_utilization` on the normalized canonical-integer `UNIT_NO`. Matched (utilization present) == 2,080. A join-integrity test must assert: matched == 2,080, no NaN/NULL join key on the utilization side post-normalization, no fan-out (fact_vehicle stays exactly 4,614 rows — unique `fact_vehicle` key), and the utilization side reconciles as 2,080 matched + 6 unmatched == 2,086.
- **D-03:** The **6 unmatched** rows (utilization records with no availability match) are surfaced via an **anti-join** (`bronze_utilization LEFT JOIN bronze_availability ... WHERE availability IS NULL`), documented as a **DQ finding** (dq_report.md or a Phase-2 addendum), and guarded by a **test asserting unmatched count == 6**. These 6 rows fall outside `fact_vehicle` (which is availability-anchored) — that is expected; they are captured only by the anti-join.

### dim_division (conformed, role-playing)
- **D-04:** Build **one conformed `dim_division`** with a surrogate key over the **distinct union of normalized division names** from both `OWNER_DIVISION` (availability, 21) and `REF_USING_DIV` (utilization, 20). These are different roles (owns vs uses the vehicle).
- **D-05:** `fact_vehicle` carries **two role-playing FKs**: `owner_division_key` (always populated, from `OWNER_DIVISION`) and `using_division_key` (light-duty only, **nullable**, from `REF_USING_DIV`). In Power BI this becomes a role-playing dimension (Phase 4 concern).
- **D-06:** Name reconciliation = **normalize (trim, collapse internal whitespace, uppercase) + distinct union**. Do **not** force-map spellings. Surface any owner/using names that do not reconcile across the two sources as a **documented DQ finding**. (Note: `OWNER_DIVISION` is truncated in source, e.g. `"ENVIRONMENT, CLIMATE & FORESTR"` — preserve as-is, document the truncation.)

### Vehicle derived field — fleet_age
- **D-07:** `fleet_age = REFERENCE_YEAR − model YEAR` (manufacture age). Use model `YEAR` (no nulls), not `IN_SERV_DT`.
- **D-08:** `REFERENCE_YEAR` is a **config constant in `config.py`** (stable/reproducible — age does not drift per run), set to **2023**. Rationale: aligns with the May 2023 FSD General Government Committee report and the audit's 2022/2023 "actual" benchmark context the dashboard is measured against. Document the chosen value + rationale.

### Ferry derived fields
- **D-09:** `season` = **meteorological 4-season by month**: Dec–Feb = Winter, Mar–May = Spring, Jun–Aug = Summer, Sep–Nov = Fall. (Lets the summer ferry peak emerge naturally in the seasonality profile.)
- **D-10:** `daypart` = **4 bands** on hour-of-day: Morning 06:00–11:00, Midday 11:00–15:00, Afternoon/Evening 15:00–20:00, Night 20:00–06:00. (Coarse rollup alongside the locked hour-of-day heatmap.)
- **D-11:** `sales_redemption_gap` = **`Sales Count − Redemption Count`** per 15-min row. Positive = tickets sold but not scanned at boarding (potential no-shows / timing lag). Direction is meaningful — do not use absolute value.
- **D-12:** `day_of_week` and `is_weekend` (Sat/Sun) are mechanical derivations from the parsed timestamp — no judgment calls.

### Claude's Discretion
- Surrogate-key generation strategy for `dim_division`, `dim_date`, `dim_time` (e.g., `ROW_NUMBER()`/sequence vs natural date keys) — planner's call, consistent with star-schema norms.
- DuckDB persistence model for the Gold build (in-memory build → COPY to Parquet vs a `.duckdb` file) — implementation detail; in-memory is consistent with the Phase 1 conftest pattern.
- Exact `dim_date` / `dim_time` attribute columns beyond what KPIs require (the locked constraints are gapless 2015→2026 and 96 rows respectively).
- Whether derived bucket boundaries live as SQL `CASE` expressions or small lookup tables — either is fine if documented.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 2: Transform, Model & Join Integrity" — goal, the 4 success criteria, and all locked constraints (join targets, derived-field list, 5 Gold tables, gapless dim_date, 96-row dim_time, Parquet+CSV export).
- `.planning/REQUIREMENTS.md` — MODEL-01, MODEL-02, MODEL-03, MODEL-04 (the requirements this phase satisfies).
- `.planning/PROJECT.md` — scope split (GSD owns data layer only; no `.pbix`/PBIP/TMDL), locked data-fidelity decisions, the profiled data schemas, and the Key Decisions table.

### Phase 1 deliverables & code (the Bronze contract to build on)
- `src/fleet_analytics/config.py` — source filenames, `EXPECTED_ROWS`, and the explicit type maps. **`UNIT_NO` is VARCHAR in Bronze** (zero-padding preserved) → integer normalization happens here in Phase 2. `AVAILABILITY_YTD` is DOUBLE with 209 genuine NULLs. Ferry `Timestamp` is tz-naive TIMESTAMP. Add `REFERENCE_YEAR = 2023` here (D-08).
- `src/fleet_analytics/ingest.py` — `ingest_bronze(con)` creates `bronze_availability` / `bronze_utilization` / `bronze_ferry` with fail-fast row-count asserts. Gold transforms consume these tables.
- `tests/conftest.py` — session-scoped `:memory:` DuckDB `con` fixture with Bronze ingested once; Phase-2 join-integrity and model tests should reuse this pattern.
- `deliverables/data_dictionary.md` and `deliverables/dq_report.md` — Phase 1 DQ deliverables; the 6-unmatched-rows finding (D-03) and division-name-reconciliation finding (D-06) extend these.

### Audit / sourcing context (for documentation, not computation)
- AG Operational Review 2019.AU2.2 (downtime) / 2019.AU2.3 (underutilization) and the May 2023 FSD General Government Committee report — cited for the `REFERENCE_YEAR = 2023` rationale and benchmark framing (full citations in PROJECT.md / Phase 1 deliverables; thresholds are cited, never recalculated).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fleet_analytics.ingest.ingest_bronze(con)` — entry point that produces the three typed Bronze tables on a DuckDB connection. Phase 2 builds a `transform`/`model` layer that consumes these.
- `tests/conftest.py` `con` fixture (session-scoped `:memory:`) — reuse for Phase-2 tests; Gold tables can be built on the same connection.
- `config.py` pattern of "single source of truth" constants (filenames, row counts, type maps) — extend with `REFERENCE_YEAR` and any Gold-layer constants rather than inlining values.

### Established Patterns
- **DuckDB SQL-first** transforms with explicit, testable assertions (Phase 1 used fail-fast row-count asserts in code + pytest guards). Continue: express normalization/join/derivation in DuckDB SQL; assert counts and bounds.
- **No COALESCE/fill on `AVAILABILITY_YTD`** — the 209 NULLs stay NULL through to Gold (exclude from rate calcs, never impute).
- `UNIT_NO` is intentionally VARCHAR in Bronze — Phase 2 owns the canonical-integer normalization (strip leading zeros / cast) on **both** datasets before joining.

### Integration Points
- Gold Parquet/CSV output (target `data/gold/` per REQUIREMENTS SHIP-01) is the handoff surface Phase 3 (KPIs) and Phase 4 (Power BI report spec) consume — column/table names defined here become the contract those phases reference.

</code_context>

<specifics>
## Specific Ideas

- The disposal-candidate cross-measure (Phase 3) is the headline "value-added" output most candidates miss — it needs `fact_vehicle` to carry both `AVAILABILITY_YTD` and the `Utilization` flag on the same row, which D-01's full-fleet LEFT JOIN delivers (NULL utilization simply excludes non-light-duty from that specific cross-measure).
- `OWNER_DIVISION` source values are truncated (e.g. `"ENVIRONMENT, CLIMATE & FORESTR"`); keep them verbatim and note the truncation rather than "fixing" spellings.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (KPI computation, DAX measures, and the Power BI report spec are Phases 3–4; narrative deliverables are Phase 5.)

</deferred>

---

*Phase: 2-Transform, Model & Join Integrity*
*Context gathered: 2026-06-03*
