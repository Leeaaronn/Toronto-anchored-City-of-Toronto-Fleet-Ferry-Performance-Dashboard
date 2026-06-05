---
phase: 05-narrative-deliverables
verified: 2026-06-05T00:00:00Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Both documents open with AG theme framing (downtime AU2.2 + underutilization AU2.3) and every external number carries an inline citation."
    status: failed
    reason: >
      stakeholder_engagement.md line 67 contains the quantitative claims "89.0% pooled availability; 5.8% underutilization over 2,080 matched units" with no inline [n] marker of any kind. Source [4] (City of Toronto Open Data) is listed in §10 Sources & Licence but is never cited inline anywhere in the document body. The document's own Method statement (line 5) explicitly promises "every quantitative claim is a falsifiable, sourced figure transcribed verbatim... or a cited external source, never re-estimated" — this promise is not fulfilled at line 67.
    artifacts:
      - path: "deliverables/stakeholder_engagement.md"
        issue: "Line 67: 89.0% and 5.8%/2,080 carry no inline [n] marker. Line 151: Source [4] listed but never cited inline — dangling source entry."
    missing:
      - "Add inline citation markers to the quantitative claims on line 67 (e.g., [4] for the Open Data figures, and/or [1] for the AG benchmark context)."
      - "Ensure Source [4] in §10 is referenced at least once inline, or remove the orphaned entry and fold its content into an existing source."
---

# Phase 5: Narrative Deliverables Verification Report

**Phase Goal:** Two credible public-sector BA artifacts are drafted — readable as real IIBA/BABOK-structured documents grounded in the AG audit, real named stakeholders, and inline citations.
**Verified:** 2026-06-05
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A full draft of the requirements-gathering approach exists (business context, stakeholder identification, elicitation techniques with rationale, requirements types, prepare/conduct/confirm process, traceability to AG themes, assumptions and constraints). | VERIFIED | `deliverables/requirements_approach.md` is 157 lines, substantive throughout — all sections confirmed present: Business Context, Stakeholder Identification, Elicitation Plan (4 techniques, performed-vs-planned explicit), Requirement Types (all 5 with FSD examples), Prepare/Conduct/Confirm, Traceability to AG Themes, Assumptions & Constraints, BABOK v3 traceability table, Sources & Licence footer. |
| 2 | A full draft of the stakeholder-engagement strategy exists (stakeholder register with real named stakeholders, power/interest grid, RACI matrix, engagement approach per group, communication plan, feedback loops, risks). | VERIFIED | `deliverables/stakeholder_engagement.md` is 154 lines, substantive throughout — all sections confirmed present: §1 Register, §2 Power/Interest Grid, §3 RACI, §4 Engagement Approach, §5 Communication Plan, §6 Feedback Loops, §7 Risks, §8 Stated Assumptions, §9 BABOK traceability, §10 Sources & Licence. |
| 3 | Both documents open with AG theme framing (downtime AU2.2 + underutilization AU2.3) and every external number carries an inline citation. | FAILED | `requirements_approach.md`: VERIFIED — all four sources [1]–[4] cited inline; AG themes in the opening blockquote. `stakeholder_engagement.md`: FAILED — line 67 contains "89.0% pooled availability; 5.8% underutilization over 2,080 matched units" with no inline [n] marker. Source [4] (City of Toronto Open Data portal) is listed in §10 but never cited inline anywhere. The document's own Method statement (line 5) promises inline citations for every quantitative claim — that promise is broken at line 67. |
| 4 | Disposal candidates are phrased as a screening list for SME review (not decisions), and an explicit stated-assumptions section is present. | VERIFIED | Both documents: "screening list" with "34" appears correctly throughout; "recommend disposal" does not appear in either document. requirements_approach.md has §"Assumptions & Constraints" (R1–R9 table). stakeholder_engagement.md has §8 "Stated Assumptions" (A1–A3, DQ-1–DQ-3 table). |

**Score:** 3/4 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `deliverables/requirements_approach.md` | NARR-01 full draft, min 120 lines, contains "2019.AU2.2" | VERIFIED | File exists, 157 lines, substantive, all required sections present. |
| `deliverables/stakeholder_engagement.md` | NARR-02 full draft, min 120 lines, contains "2019.AU2.2" | VERIFIED (with citation defect) | File exists, 154 lines, substantive, all required sections present. Citation integrity defect on line 67 is the blocking gap. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `requirements_approach.md` | `data/kpi/kpi_values.json` | Verbatim number transcription (89.0%, 5.8%, 4,405, 209, 34, etc.) | WIRED | All number-registry figures verified present; none appear outside the registry. |
| `requirements_approach.md` | `deliverables/kpi_definitions.md` | Shared KPI vocabulary + 5.8% vs ~14% reconciliation | WIRED | Reconciliation present at line 110 with "different periods" and "right-sizing, not an error" framing verbatim. |
| `stakeholder_engagement.md` | RESEARCH stakeholder roster | Verbatim sourced names (Jollimore, Lalovic, Lamsaki) | WIRED | All three names present with correct titles; no other personal names found. |
| `stakeholder_engagement.md` | `deliverables/kpi_definitions.md` | Shared KPI/AG vocabulary + disposal screening-list framing | WIRED | "screening list" × 14 occurrences; "2019.AU2.3" present; no "recommend disposal" in body. |
| `stakeholder_engagement.md` | Sources [1]–[4] | Every inline [n] resolves; no dangling entries | PARTIAL — BLOCKER | [1], [2], [3] all used inline and resolve to Sources entries. [4] (City of Toronto Open Data) is listed in §10 but cited nowhere inline. Quantitative claims on line 67 carry no [n] marker. |

---

### Data-Flow Trace (Level 4)

Not applicable. This phase produces markdown narrative documents, not runnable code with dynamic data rendering.

---

### Behavioral Spot-Checks

Step 7b: SKIPPED — this is a documentation-authoring phase with no runnable entry points.

---

### Probe Execution

Step 7c: No probe scripts declared or applicable. This phase has no `scripts/*/tests/probe-*.sh` files.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NARR-01 | 05-01-PLAN.md | Full draft of requirements-gathering approach narrative (BABOK/IIBA structure, real named stakeholders, elicitation techniques, traceability to AG themes, stated assumptions, inline citations) | SATISFIED | `deliverables/requirements_approach.md` exists and fulfils all listed criteria. |
| NARR-02 | 05-02-PLAN.md | Full draft of stakeholder-engagement strategy narrative (stakeholder register, power/interest grid, RACI, engagement + communication plan, feedback loops, risks, inline citations) | PARTIALLY SATISFIED | `deliverables/stakeholder_engagement.md` exists and fulfils structure criteria. Citation-integrity defect (CR-01): line 67 quantitative claims lack inline [n]; Source [4] is a dangling entry. The "inline citations" sub-criterion of NARR-02 is not fully met. |

**Note on REQUIREMENTS.md tracking:** Both NARR-01 and NARR-02 remain marked `[ ] Pending` in `.planning/REQUIREMENTS.md` (lines 35–36 and 81–82). The checkboxes were not updated after execution. This is a bookkeeping gap but is not a content defect; however it means the traceability table is inaccurate.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `deliverables/stakeholder_engagement.md` | 151 | Source [4] listed in §10 but never cited inline | BLOCKER | Breaks the document's own stated citation discipline; a panel reviewer sees a self-contradiction between the Method promise and the body. |
| `deliverables/stakeholder_engagement.md` | 67 | "89.0% pooled availability; 5.8% underutilization over 2,080 matched units" — no inline [n] marker | BLOCKER | Same defect as above. The headline KPI figures in the SME engagement row carry no citation despite the Method statement's explicit promise. |
| `.planning/REQUIREMENTS.md` | 35–36, 81–82 | NARR-01 and NARR-02 still marked Pending (`[ ]`) after completion | WARNING | Traceability table is stale; requirements not marked complete. Does not affect deliverable content but leaves the planning record inaccurate. |

No TODO / FIXME / TBD / XXX / HACK / PLACEHOLDER markers were found in either deliverable file.

---

### Human Verification Required

None — all must-have checks are resolvable from codebase evidence. The citation defect (CR-01) is a concrete, machine-verifiable finding. No visual or runtime behavior needs a human observer.

---

## Gaps Summary

One blocking gap prevents the phase goal from being fully achieved.

**Root cause:** `stakeholder_engagement.md` was authored with Sources [1]–[3] wired to inline citations, but Source [4] (City of Toronto Open Data) was added to the footer without being wired to any inline usage. Simultaneously, the highest-visibility quantitative claims in the engagement-approach table (line 67) were written as prose context rather than as formally cited figures.

This is a narrow, single-file, single-location fix: add `[4]` (or `[1]`/`[4]` as appropriate) to the line 67 quantitative claims so the Method promise is honoured and the orphaned source entry resolves. The review (05-REVIEW.md, finding CR-01) supplies the exact recommended fix verbatim.

The fix does not affect any other section of the file, does not touch code, does not require re-running tests, and does not cascade to `requirements_approach.md` (which correctly wires all four citations).

**What passes:** SC1 (requirements-gathering approach, full draft), SC2 (stakeholder-engagement strategy, full structure), SC4 (disposal screening-list framing and stated-assumptions section). Both documents open with AG framing. Named-person discipline is clean across both files. BABOK knowledge-area names are not used as headings. Numbers trace to the registry throughout.

**What fails:** SC3 — the "every external number carries an inline citation" clause — is broken in `stakeholder_engagement.md` at line 67.

---

_Verified: 2026-06-05_
_Verifier: Claude (gsd-verifier)_
