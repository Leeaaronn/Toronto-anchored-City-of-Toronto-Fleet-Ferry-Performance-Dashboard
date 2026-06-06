---
phase: 6
slug: ship
status: draft
nyquist_compliant: false
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
| (filled by planner) | — | — | SHIP-01 | T-6-01 | No new SQL interpolation surface in pipeline.py | smoke | `uv run python -c "import fleet_analytics"` | ❌ W0 (`[build-system]`) | ⬜ pending |
| (filled by planner) | — | — | SHIP-01 | — | N/A | integration | `uv run python -m fleet_analytics.pipeline` exits 0 | ❌ W0 (`pipeline.py`) | ⬜ pending |
| (filled by planner) | — | — | SHIP-01 | — | N/A | integration | run pipeline → `git status --porcelain` empty | ❌ W0 (`.gitattributes`) | ⬜ pending |
| (filled by planner) | — | — | SHIP-01 | — | N/A | smoke | `uv run pytest -q` (expect 76+ passed) | ✅ (`tests/`) | ⬜ pending |
| (filled by planner) | — | — | SHIP-01 | — | N/A | smoke | assert 6 `.parquet` files in `data/gold/` | ✅ files present | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/fleet_analytics/pipeline.py` — full-chain orchestrator (`main()` + `__main__`) covering the SHIP-01 one-command criterion
- [ ] `[build-system]` in `pyproject.toml` + `uv sync` — makes `-m fleet_analytics.*` runnable (fixes live-verified ModuleNotFoundError)
- [ ] `.gitattributes` (`*.csv eol=lf`, `*.parquet binary`) — clean-diff regeneration on Windows
- [ ] `tests/test_pipeline.py` — smoke test asserting the orchestrator runs and produces the 6 Gold Parquet files

*(No new test framework needed — pytest is in place and green: 76 passed in 4.49s.)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README reads as credible, citation-complete submission documentation | SHIP-01 | Editorial judgment on prose quality and citation framing | Read README.md; confirm three primary sources cited (Open Data portal, May 2023 FSD report, AG 2019.AU2.2/2.3) under Open Government Licence – Toronto; pull date 2026-06-02 stated; stated assumptions present |
| Cross-deliverable number self-consistency (89.0% / 5.8% / 2,080 / 6 / 209 / 4,614 / 2,086 / 272,529) | SHIP-01 | Cross-document semantic check; grep-assisted but final judgment manual | grep each registry number across deliverables/ and README; confirm no conflation of the two 5.8% bases (120/2,086 raw vs 0.0572 over 2,080 matched) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
