---
phase: 6
slug: ship
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-06
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.3 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["src"]`) |
| **Quick run command** | `uv run pytest -q` |
| **Full suite command** | `uv run pytest -q` (suite is ~4.5s — quick == full) |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q`
- **After every plan wave:** Run `uv run pytest -q` + `uv run python -m fleet_analytics.pipeline` + `git status --porcelain` clean check
- **Before `/gsd:verify-work`:** Full suite must be green AND one-command pipeline exits 0 AND regeneration is a clean no-op diff
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| P01-T1 | 06-01 | 1 | SHIP-01 | T-6-SC | Build backend = PyPA-official hatchling only | smoke | `uv run python -c "import fleet_analytics"` | ❌→✅ (this task) | ⬜ pending |
| P01-T2 | 06-01 | 1 | SHIP-01 | T-6-01 | Config-only; no code surface | smoke | `git check-attr eol -- data/gold/dim_date.csv` | ❌→✅ (this task) | ⬜ pending |
| P01-T3 | 06-01 | 1 | SHIP-01 | — | N/A | smoke | `uv run pytest -q` (expect 76+ passed) | ✅ (`tests/`) | ⬜ pending |
| P02-T1 | 06-02 | 2 | SHIP-01 | T-6-01 | No new SQL interpolation in pipeline.py (pure wiring) | integration | `uv run python -m fleet_analytics.pipeline` exits 0 | ❌→✅ (this task) | ⬜ pending |
| P02-T2 | 06-02 | 2 | SHIP-01 | — | N/A | integration | `uv run pytest tests/test_pipeline.py -q` | ❌→✅ (this task) | ⬜ pending |
| P02-T3 | 06-02 | 2 | SHIP-01 | T-6-02 | Deterministic outputs (clean no-op diff) | integration | `uv run pytest -q` + `git status --porcelain` empty after run | ✅ (`.gitattributes` P01) | ⬜ pending |
| P03-T1 | 06-03 | 3 | SHIP-01 | T-6-03 | README aggregates, no number drift | smoke | README string-presence check (licence/pull-date/invocation/sources) | ❌→✅ (this task) | ⬜ pending |
| P03-T2 | 06-03 | 3 | SHIP-01 | T-6-03 | Cross-doc number consistency | smoke | deliverable-files-exist + kpi_values.json load | ✅ files present | ⬜ pending |
| P03-T4 | 06-03 | 3 | SHIP-01 | T-6-04 | Reconcile gated by human decision | smoke | REQUIREMENTS.md traceability rows present | ✅ (file) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Checkpoint tasks (P03-T3 decision, P03-T5 human-verify) have no automated command — human gates.*

---

## Wave 0 Requirements

- [ ] `[build-system]` in `pyproject.toml` + `uv sync` — makes `-m fleet_analytics.*` runnable (Plan 06-01 Task 1)
- [ ] `.gitattributes` (`*.csv eol=lf`, `*.parquet binary`) — clean-diff regeneration on Windows (Plan 06-01 Task 2)
- [ ] `src/fleet_analytics/pipeline.py` — full-chain orchestrator (`main()` + `__main__`) covering the SHIP-01 one-command criterion (Plan 06-02 Task 1)
- [ ] `tests/test_pipeline.py` — smoke test asserting the orchestrator runs and produces the 6 Gold Parquet files (Plan 06-02 Task 2)

*(No new test framework needed — pytest is in place and green: 76 passed in 4.49s.)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README reads as credible, citation-complete submission documentation | SHIP-01 | Editorial judgment on prose quality and citation framing | Plan 06-03 Task 5 (checkpoint:human-verify): read README.md; confirm three primary sources cited (Open Data portal, May 2023 FSD report, AG 2019.AU2.2/2.3) under Open Government Licence – Toronto; pull date 2026-06-02 stated; stated assumptions present |
| KPI-01 / REPORT-01 genuinely complete before traceability flip | SHIP-01 | Risk of masking unfinished work; artifacts confirmed but completion is a judgment | Plan 06-03 Task 3 (checkpoint:decision): confirm artifacts (data/kpi/, report_spec.md) represent complete work before reconciling REQUIREMENTS.md |
| Cross-deliverable number self-consistency (89.0% / 5.8% / 2,080 / 6 / 209 / 4,614 / 2,086 / 272,529) | SHIP-01 | Cross-document semantic check; grep-assisted but final judgment manual | Plan 06-03 Task 2: grep each registry number across deliverables/ and README; confirm no conflation of the two 5.8% bases (120/2,086 raw vs 0.0572 over 2,080 matched) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (checkpoint tasks excepted — human gates)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned 2026-06-06
