---
phase: 02
slug: transform-model-join-integrity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-03
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` § Validation Architecture — every target number below was reproduced by live DuckDB 1.5.3 execution against the real Bronze tables.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.3 (+ optional Pandera >=0.26) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["src"]`) |
| **Quick run command** | `uv run pytest -q tests/test_join_integrity.py` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | < 5 s quick gate · ~full suite seconds (in-memory DuckDB) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q tests/test_join_integrity.py` (the < 5s hard gate — MODEL-03 is the flagship value-added measure).
- **After every plan wave:** Run `uv run pytest -q` (full suite, includes Phase-1 regression guards).
- **Before `/gsd:verify-work`:** Full suite must be green; the join-integrity file is the non-negotiable gate.
- **Max feedback latency:** < 5 seconds (quick gate).

---

## Per-Task Verification Map

> Keyed by phase requirement (task IDs assigned by the planner). All target counts verified live against Bronze.

| Requirement | Behavior | Test Type | Automated Command | File Exists |
|-------------|----------|-----------|-------------------|-------------|
| MODEL-03 | matched == 2,080 | unit | `uv run pytest tests/test_join_integrity.py::test_matched_2080 -x` | ❌ W0 |
| MODEL-03 | unmatched (anti-join) == 6 | unit | `…::test_unmatched_6 -x` | ❌ W0 |
| MODEL-03 | fact_vehicle == 4,614, no fan-out | unit | `…::test_fact_rowcount_4614 -x` | ❌ W0 |
| MODEL-03 | unique fact_vehicle key (UNIT_NO distinct == 4,614) | unit | `…::test_fact_unique_key -x` | ❌ W0 |
| MODEL-03 | utilization join key has no NULL post-normalization | unit | `…::test_util_key_not_null -x` | ❌ W0 |
| MODEL-01 | ferry 15-min slot: 0 NaT, 272,529 rows | unit | `tests/test_derived_fields.py::test_ferry_ts15 -x` | ❌ W0 |
| MODEL-01 | fleet_age = 2023 − YEAR (parametrized, negatives allowed) | unit | `…::test_fleet_age[case] -x` | ❌ W0 |
| MODEL-01 | season/daypart/day_of_week/is_weekend boundary cases | unit | `…::test_season_daypart[case] -x` | ❌ W0 |
| MODEL-01 | sales_redemption_gap signed (Sales − Redemption) | unit | `…::test_gap_signed -x` | ❌ W0 |
| MODEL-02 | dim_date gapless (count == 4,383, max−min+1 == count) | unit | `tests/test_dimensions.py::test_dim_date_gapless -x` | ❌ W0 |
| MODEL-02 | dim_time == 96 rows | unit | `…::test_dim_time_96 -x` | ❌ W0 |
| MODEL-02 | dim_division conformed == 21, surrogate keys unique | unit | `…::test_dim_division_conformed -x` | ❌ W0 |
| MODEL-04 | Parquet roundtrip preserves DOUBLE+209 NULLs, DATE, boolean | integration | `tests/test_export.py::test_parquet_types -x` | ❌ W0 |
| MODEL-04 | CSV reread preserves 209 NULLs (no 0-fill) | integration | `…::test_csv_nulls -x` | ❌ W0 |
| (regression) | Phase-1 null guard still green (209/4,405) | unit | `tests/test_nulls.py` (existing) | ✅ exists |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Boundary test cases (parametrize like Phase 1 `test_rowcounts.py`):**
- `season`: month 12→Winter, 2→Winter, 3→Spring, 6→Summer, 8→Summer, 9→Fall, 11→Fall.
- `daypart`: hour 5→Night, 6→Morning, 10→Morning, 11→Midday, 14→Midday, 15→Afternoon/Evening, 19→Afternoon/Evening, 20→Night, 23→Night.
- `is_weekend`: a known Saturday/Sunday timestamp → true; a Wednesday → false.
- `fleet_age`: YEAR 2015→8, YEAR 1982→41, YEAR 2026→−3 (assert negatives allowed — do NOT clamp).

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — add `gold` fixture that runs `transform.build_all(con)` + `model.build_all(con)` on the existing session `con`.
- [ ] `tests/test_join_integrity.py` — matched/unmatched/fan-out/unique-key/null-key asserts (MODEL-03).
- [ ] `tests/test_derived_fields.py` — parametrized fleet_age/season/daypart/dow/is_weekend/gap + ferry 15-min slot (MODEL-01).
- [ ] `tests/test_dimensions.py` — dim_date gapless, dim_time 96, dim_division conformed 21 (MODEL-02).
- [ ] `tests/test_export.py` — Parquet/CSV roundtrip type+null preservation (MODEL-04).
- [ ] (optional) `schemas.py` Gold-tier Pandera contracts (`fleet_age` int, `season`/`daypart` value sets) — nice-to-have, not gating.
- Framework install: **none** — pytest/pandera already in the dev group.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The 6-unmatched + 44-alphanumeric-unit DQ findings are documented in a deliverable | MODEL-03 | Documentation quality is a prose judgment, not a count | Confirm `deliverables/dq_report.md` (or a Phase-2 addendum) records the 6 unmatched utilization rows AND the 44 alphanumeric availability units, each with the anti-join / TRY_CAST rationale |

*The count assertions for both findings ARE automated (test_unmatched_6); only the prose documentation is manual.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (5 new test files + gold fixture)
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
