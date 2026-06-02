---
phase: 1
slug: ingest-profile-dq-baseline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-02
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` ## Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (install via `uv add --dev pytest`) + Pandera (`uv add "pandera>=0.26"`) |
| **Config file** | none yet — Wave 0 creates `tests/conftest.py` (+ optional `[tool.pytest.ini_options]` in `pyproject.toml`) |
| **Quick run command** | `uv run pytest tests/test_rowcounts.py tests/test_nulls.py -x -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~15 seconds (single ferry CSV load of 272,529 rows dominates) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_rowcounts.py tests/test_nulls.py -x -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green (hard gate that unlocks Phase 2)
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

> Task IDs (`{plan}-{task}`) are assigned by the planner; rows below are keyed by requirement + assertion so the planner can attach each to a concrete task.

| Req | Behavior (assertion) | Test Type | Automated Command | File Exists |
|-----|----------------------|-----------|-------------------|-------------|
| DATA-01 | `bronze_availability` row count == 4,614 | unit | `uv run pytest tests/test_rowcounts.py::test_availability_rowcount -x` | ❌ W0 |
| DATA-01 | `bronze_utilization` row count == 2,086 | unit | `uv run pytest tests/test_rowcounts.py::test_utilization_rowcount -x` | ❌ W0 |
| DATA-01 | `bronze_ferry` row count == 272,529 | unit | `uv run pytest tests/test_rowcounts.py::test_ferry_rowcount -x` | ❌ W0 |
| DATA-01 | explicit column set / dtypes (esp. `UNIT_NO` VARCHAR, `AVAILABILITY_YTD` DOUBLE) | unit (Pandera) | `uv run pytest tests/test_schemas.py -x` | ❌ W0 |
| DATA-03 | `AVAILABILITY_YTD` null count == 209 | unit | `uv run pytest tests/test_nulls.py::test_null_count -x` | ❌ W0 |
| DATA-03 | `AVAILABILITY_YTD` non-null count == 4,405 | unit | `uv run pytest tests/test_nulls.py::test_nonnull_count -x` | ❌ W0 |
| DATA-03 | zero originally-null values became 0 (DOUBLE typing, no COALESCE/fill; non_null stays 4,405) | unit | `uv run pytest tests/test_nulls.py::test_no_null_became_zero -x` | ❌ W0 |
| DATA-04 | non-null `AVAILABILITY_YTD` within [0.0, 1.0] | unit (Pandera `Check.in_range(0,1)`) | `uv run pytest tests/test_schemas.py::test_availability_bounds -x` | ❌ W0 |
| DATA-04 | `Utilization` ∈ {Underutilized, Not Underutilized}; `Specialized units` ∈ {Yes, No} | unit (Pandera `Check.isin`) | `uv run pytest tests/test_schemas.py::test_value_sets -x` | ❌ W0 |
| DATA-02 | DQ-report carries headline numbers: ferry Sales median 12 / max 7,229; underutilized 5.8% (120/2,086); 21 divisions; YEAR 1982–2026 | unit (assert on `profile.py` output) + artifact-exists | `uv run pytest tests/test_profile.py -x` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — all rows ⬜ pending until executed.*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — session fixture: connect DuckDB, run `ingest.py` into Bronze once
- [ ] `tests/test_rowcounts.py` — DATA-01 (3 parametrized count assertions)
- [ ] `tests/test_nulls.py` — DATA-03 (null==209, non-null==4,405, no-null-became-0)
- [ ] `tests/test_schemas.py` — DATA-04 (Pandera: 0–1 bounds, value sets, dtypes)
- [ ] `tests/test_profile.py` — DATA-02 (profiling output numbers + DQ-report artifact exists)
- [ ] `src/fleet_analytics/schemas.py` — Pandera schemas
- [ ] Framework install: `uv add --dev pytest "pandera>=0.26"`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The DQ-report narrative frames the 5.8% vs 14% gap as a stated insight (not an error) with citation | DATA-02 | Prose quality is judgment, not assertable beyond keyword presence | Read `dq_report.md`; confirm the 5.8% vs 14% paragraph cites the audit and frames it as a period/right-sizing insight |
| The retired-dataset pull-date caveat is documented | DATA-02 | Pull-date provenance is an external fact | Confirm `dq_report.md` states the availability dataset is portal-retired and records the pull/snapshot date |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
