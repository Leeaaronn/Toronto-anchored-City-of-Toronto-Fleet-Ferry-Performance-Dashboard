---
phase: 01-ingest-profile-dq-baseline
plan: 03
subsystem: data-quality
tags: [duckdb, summarize, profiling, data-quality, dq-report, data-dictionary, pytest, deliverables]

# Dependency graph
requires:
  - "01-01 (Bronze ingest, config.py, conftest `con` fixture)"
  - "01-02 (Pandera schemas — the same DQ facts these deliverables document)"
provides:
  - "src/fleet_analytics/profile.py — profile_facts(con) returning a deterministic dict of DATA-02 DQ facts via DuckDB SUMMARIZE + targeted SQL"
  - "tests/test_profile.py — 8 DATA-02 guards on profile_facts output + DQ-report artifact-exists/content check"
  - "deliverables/data_dictionary.md — per-column dictionary for all three Bronze tables"
  - "deliverables/dq_report.md — nulls, ranges, ferry skew (12/7,229), retired-dataset pull-date caveat (A1), 5.8% vs 14% as cited stated insight (A2)"
affects:
  - "Phase 2 (transforms/joins reuse profile_facts for before/after DQ deltas; deliverables seed the report narrative)"
  - "Phase 5 (narrative deliverables build on the DQ report's cited insights)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DuckDB SUMMARIZE captured verbatim + targeted MEDIAN/MAX/COUNT(DISTINCT) queries — deterministic, citable, no hand-rolled aggregation loops"
    - "profile_facts returns a flat dict keyed for direct pytest assertion (single source the deliverables transcribe)"
    - "Cited-not-computed provenance: ~14% benchmark and retired-dataset pull date flagged inline as A1/A2 narrative facts"
    - "Ferry max 7,229 surfaced as real peak-window skew, not flagged as an error"

key-files:
  created:
    - "src/fleet_analytics/profile.py"
    - "tests/test_profile.py"
    - "deliverables/data_dictionary.md"
    - "deliverables/dq_report.md"
  modified: []

key-decisions:
  - "Profiling is SQL-based (SUMMARIZE + targeted queries); the fg-data-profiling HTML path is explicitly skipped per RESEARCH (reproducible, citable baseline)"
  - "profile_facts denominator for availability is 4,405 non-null (209 nulls excluded, never imputed) — DATA-03 carried into the report"
  - "ferry Sales/Redemption medians cast to int for exact-equality assertions; underutilized rate rounded to 1 decimal for the 5.8% test"
  - "5.8% vs ~14% framed as a period/right-sizing INSIGHT with inline AG 2019.AU2.3 citation, not an error or a recomputation"
  - "Snapshot pull date recorded as 2026-06-02 (A1) — the retired availability dataset is treated as a point-in-time snapshot"

patterns-established:
  - "Pattern: one deterministic profile_facts(con) dict as the single source for both tests and markdown deliverables"
  - "Pattern: cited-vs-computed labelling in the DQ report so audit-graded claims stay defensible (T-01-03 mitigation)"

requirements-completed: [DATA-02]

# Metrics
duration: 3min
completed: 2026-06-02
---

# Phase 01 Plan 03: Profiling & DQ Baseline Deliverables Summary

**Deterministic `profile_facts(con)` (DuckDB SUMMARIZE + targeted SQL) emitting the DATA-02 headline numbers — ferry Sales median 12 / max 7,229, underutilized 120/2,086 = 5.8%, 21 divisions, YEAR 1982–2026 — plus a data dictionary and a DQ report that frames the retired-dataset pull-date caveat and the 5.8%-vs-14% gap as cited, audit-grounded insights. Full phase suite now 23 green.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-02T19:16:23Z
- **Completed:** 2026-06-02T19:19:16Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments

- Authored `src/fleet_analytics/profile.py` with `profile_facts(con)` — a flat dict of DQ facts computed deterministically from DuckDB `SUMMARIZE` (captured verbatim per table) plus targeted `MEDIAN` / `MAX` / `COUNT` / `COUNT(DISTINCT)` / `MIN`-`MAX` queries. No hand-rolled aggregation loops; the fg-data-profiling HTML path is intentionally skipped (RESEARCH).
- Wrote `tests/test_profile.py` (8 guards) locking the verified DATA-02 headline numbers: row counts (4,614 / 2,086 / 272,529); AVAILABILITY_YTD 209 null / 4,405 non-null / [0,1] bounds; ferry Sales median 12 / max 7,229 and Redemption median 11 / max 7,216; underutilized 120/2,086 rounding to 5.8%; 21 OWNER_DIVISION, 19 CATEGORY_CLASS; YEAR range (1982, 2026); and a DQ-report artifact-exists + `5.8%` content check.
- Produced `deliverables/data_dictionary.md` documenting every Bronze column across all three tables (name, DuckDB type as ingested, nullability, notes — zero-padded `UNIT_NO`, the 209-null `AVAILABILITY_YTD`, the pre-classified `Utilization` value set, the embedded-comma `OWNER_DIVISION`).
- Produced `deliverables/dq_report.md` covering row counts; the 209-null gap (excluded, denominator 4,405, with the 13 legitimate 0.0 values noted); the ferry skew (median 12 vs max 7,229) framed as a real peak-window outlier story; the retired-dataset pull-date caveat (A1, snapshot 2026-06-02); and the 5.8% vs ~14% underutilization discrepancy framed as a cited period/right-sizing insight (A2, AG 2019.AU2.3). All three primary sources and the Open Government Licence – Toronto are cited.

## Task Commits

Each task was committed atomically:

1. **Task 1 (tdd): profile_facts via SUMMARIZE + targeted SQL, with tests (DATA-02)**
   - RED — `0b27b90` (test): failing assertions (`ModuleNotFoundError: fleet_analytics.profile`).
   - GREEN — `69fbcc9` (feat): `profile.py` implementing `profile_facts`; 7/8 profile tests green (artifact check deselected pending Task 2).
2. **Task 2: author data_dictionary.md and dq_report.md** — `7471ed1` (docs): both deliverables; the previously-deselected artifact-exists/`5.8%` test now passes, full profile suite 8/8.

_No REFACTOR commit — Task 1's implementation was clean on first GREEN._

## Files Created/Modified

- `src/fleet_analytics/profile.py` — `profile_facts(con)` returning a flat dict of DQ facts (+ raw per-table `SUMMARIZE` under `summaries`); SQL-only, deterministic.
- `tests/test_profile.py` — 8 DATA-02 guards on `profile_facts` output + DQ-report artifact/content check.
- `deliverables/data_dictionary.md` — per-column dictionary for the three Bronze tables.
- `deliverables/dq_report.md` — DQ report with nulls, ranges, ferry skew, A1 pull-date caveat, and the 5.8%-vs-14% cited insight.

## Decisions Made

- **SQL-based profiling, HTML skipped** — `SUMMARIZE` + targeted queries are deterministic and citable; the optional fg-data-profiling artifact adds heavy deps and non-determinism for no graded benefit (RESEARCH).
- **4,405 non-null denominator** carried into both deliverables — the 209 nulls are excluded, never imputed (DATA-03); the 13 legitimate `0.0` values are documented as distinct from missing.
- **Medians cast to int, rate rounded to 1 decimal** — ferry medians (12 / 11) assert by exact integer equality; the underutilized rate asserts via `round(rate*100,1) == 5.8` (120/2,086 = 5.75%).
- **Cited-not-computed labelling** — the ~14% benchmark (A2, AG 2019.AU2.3) and the retired-dataset pull date (A1, snapshot 2026-06-02) are flagged inline as narrative facts, mitigating T-01-03 (indefensible/unsourced claim in an audit-graded deliverable).

## Deviations from Plan

None — the plan executed exactly as written. Both tasks' acceptance criteria were met, all numbers matched the [VERIFIED 2026-06-02] targets on first run, and no auto-fixes (Rules 1–3) or architectural decisions (Rule 4) were required.

## Issues Encountered

- Minor authoring slip: an initial `Write` used a wrong absolute path (a non-existent sibling directory) and created a stray `profile.py`. Caught immediately, the stray directory was removed, and the file was re-written to the correct `src/fleet_analytics/profile.py`. No commit included the stray file; working tree is clean.

## User Setup Required

None — in-process DuckDB profiling over local Bronze tables produces local markdown deliverables. No external services, secrets, or env vars.

## Threat Surface

- **T-01-03 (Information disclosure — uncited external benchmark presented as derived): mitigated.** The DQ report cites the AG 2019.AU2.3 audit for the ~14% figure and the retired-dataset pull-date caveat (A1/A2); all profiled numbers come from deterministic SQL and are test-locked. No new surface introduced — local read-only CSVs, public Open-Government-Licence data, no secrets/auth/network. No threat flags.

## Known Stubs

None — `profile_facts` is fully wired against real Bronze data and both deliverables transcribe live profiled numbers (no placeholders, no empty/mock data).

## Next Phase Readiness

- **DATA-02 complete.** ROADMAP success criterion 3 (data dictionary + DQ report documenting nulls, ranges, ferry skew 12/7,229, the retired-dataset pull-date caveat, and the 5.8% vs 14% discrepancy as a stated insight) is MET.
- Phase 1 is functionally complete across DATA-01/02/03/04: row-count, null-preservation, Pandera DQ contracts, and the profiling/DQ deliverables. Full suite: `uv run pytest -q` → **23 passed** (the hard gate that unlocks Phase 2).
- `profile_facts(con)` is reusable in Phase 2 for before/after DQ deltas on transformed/joined tables; the DQ report's cited insights seed the Phase-5 narrative deliverables.

## Self-Check: PASSED

- All 4 created files verified present on disk (`profile.py`, `test_profile.py`, `data_dictionary.md`, `dq_report.md`).
- Commits `0b27b90`, `69fbcc9`, `7471ed1` verified in `git log`.
- `uv run pytest tests/test_profile.py -x -q` → 8 passed; `uv run pytest -q` → 23 passed.

---
*Phase: 01-ingest-profile-dq-baseline*
*Completed: 2026-06-02*
