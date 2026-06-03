# Phase 2: Transform, Model & Join Integrity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-03
**Phase:** 2-Transform, Model & Join Integrity
**Areas discussed:** fact_vehicle grain, dim_division conformance, Vehicle derived buckets, Ferry derived semantics

---

## fact_vehicle grain

| Option | Description | Selected |
|--------|-------------|----------|
| Full fleet 4,614 (LEFT JOIN util) | All availability vehicles; util attrs NULL for non-light-duty; by-class spans whole fleet, cross-measure on matched subset | ✓ |
| Light-duty only 2,086 | Anchor on utilization side; by-class limited to light-duty | |

**User's choice:** Full fleet 4,614, LEFT JOIN utilization.

| Option | Description | Selected |
|--------|-------------|----------|
| Anti-join + DQ note + test asserts ==6 | Anti-join captures the 6; document in DQ report; assert unmatched count == 6 | ✓ |
| Separate gold table | Persist the 6 as a gold table + assertion | |
| dq_report note only | Prose note, no test | |

**User's choice:** Anti-join + DQ note + test asserts == 6.

---

## dim_division conformance

| Option | Description | Selected |
|--------|-------------|----------|
| Conformed dim + role-playing FKs | One dim_division over union of normalized names; owner_division_key (always) + using_division_key (nullable) on fact_vehicle | ✓ |
| Two separate dims | dim_owner_division + dim_using_division | |
| Denormalized text columns | Division as plain text on fact_vehicle, no dim | |

**User's choice:** Conformed dim + role-playing FKs.

| Option | Description | Selected |
|--------|-------------|----------|
| Normalize + union + DQ note | Trim/collapse-ws/uppercase + distinct union; document non-reconciling names | ✓ |
| Manual crosswalk | Hand-maintained owner→using mapping table | |
| Keep separate, no reconciliation | Independent value sets | |

**User's choice:** Normalize + union + DQ note.

---

## Vehicle derived buckets (fleet_age)

| Option | Description | Selected |
|--------|-------------|----------|
| reference_year − model YEAR | Manufacture age from model YEAR (no nulls) | ✓ |
| Years in service (IN_SERV_DT) | reference date − IN_SERV_DT | |
| Both | Two columns | |

**User's choice:** reference_year − model YEAR.

| Option | Description | Selected |
|--------|-------------|----------|
| Config constant (set to data ref year) | REFERENCE_YEAR constant in config.py; stable/reproducible | ✓ |
| 2026 (pull/snapshot year) | Age as of pull date | |
| 2023 (FSD report period) | Age vs May 2023 / audit-period context | |

**User's choice:** Config constant — value pinned to **2023** in follow-up.

| Option | Description | Selected |
|--------|-------------|----------|
| 2023 | May 2023 FSD report + audit 2022/2023 benchmark context | ✓ |
| 2022 | Audit 'actual' year | |
| 2026 | Current pull date | |

**User's choice:** 2023.

---

## Ferry derived semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Meteorological 4-season | Dec-Feb Winter, Mar-May Spring, Jun-Aug Summer, Sep-Nov Fall | ✓ |
| Operational (Peak/Shoulder/Off) | Demand-tuned, subjective boundaries | |
| Astronomical | Solstice/equinox cutoffs | |

**User's choice:** Meteorological 4-season.

| Option | Description | Selected |
|--------|-------------|----------|
| 4 bands | Morning 06-11, Midday 11-15, Aft/Eve 15-20, Night 20-06 | ✓ |
| 3 bands | AM/Midday/PM | |
| You decide | Claude picks aligned to operating hours | |

**User's choice:** 4 bands.

| Option | Description | Selected |
|--------|-------------|----------|
| Sales − Redemption | Positive = sold but not scanned (no-shows / lag) | ✓ |
| Redemption − Sales | Positive = scanned more than sold | |
| Absolute difference | Magnitude only, loses direction | |

**User's choice:** Sales − Redemption.

---

## Claude's Discretion

- Surrogate-key generation strategy for dim_division / dim_date / dim_time.
- DuckDB persistence model for the Gold build (in-memory + COPY vs `.duckdb` file).
- Exact dim_date / dim_time attribute columns beyond the locked constraints (gapless 2015→2026; 96 rows).
- Bucket boundaries as SQL CASE vs lookup tables.

## Deferred Ideas

None — discussion stayed within phase scope.
