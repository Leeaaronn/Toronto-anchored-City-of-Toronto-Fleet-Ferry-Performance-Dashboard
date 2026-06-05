---
phase: 5
slug: narrative-deliverables
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-05
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

> **Documentation phase:** Phase 5 produces no executable code. "Validation" is editorial/consistency verification against the Source-of-Truth Number Registry in 05-RESEARCH.md, performed per task and at the phase gate — not a new pytest surface.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None new — documentation phase. Existing repo uses pytest (unchanged). |
| **Config file** | none — no Wave 0 install needed |
| **Quick run command** | n/a (editorial self-review per task) |
| **Full suite command** | `uv run pytest` (regression confirmation only — no code touched) |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Self-review against the relevant CONTEXT success criterion + the Source-of-Truth Number Registry (05-RESEARCH.md)
- **After every plan wave:** Editorial checklist pass over the drafted document(s)
- **Before `/gsd:verify-work`:** Full editorial checklist green + `uv run pytest` passes unchanged
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD (filled by planner) | — | — | NARR-01 | — | N/A | editorial checklist | `test -f deliverables/requirements_approach.md` | ❌ to be created | ⬜ pending |
| TBD (filled by planner) | — | — | NARR-02 | — | N/A | editorial checklist | `test -f deliverables/stakeholder_engagement.md` | ❌ to be created | ⬜ pending |
| TBD (filled by planner) | — | — | NARR-01, NARR-02 | — | N/A | regression | `uv run pytest` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test scaffolding needed — documentation phase.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Number fidelity (every external figure traces to the registry) | NARR-01, NARR-02 | Prose citation accuracy is not machine-checkable | Cross-check each cited number in both documents against the Source-of-Truth Number Registry in 05-RESEARCH.md |
| Only 3 real named persons (Jollimore, Lalovic, Lamsaki); all others role-based | NARR-02 | Name fabrication requires human judgment | Scan stakeholder register and prose for personal names; confirm only the 3 sourced names appear |
| Disposal candidates framed as SME screening list, not decisions | NARR-01, NARR-02 | Tone/framing judgment | Read disposal sections; confirm screening-list language and stated-assumptions section present |
| AG theme framing (AU2.2 + AU2.3) opens both documents | NARR-01, NARR-02 | Structural/editorial judgment | Confirm each document's opening section frames downtime (AU2.2) and underutilization (AU2.3) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or editorial-checklist verification mapped above
- [ ] Sampling continuity: no 3 consecutive tasks without verification
- [ ] Wave 0 covers all MISSING references (none — documentation phase)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
