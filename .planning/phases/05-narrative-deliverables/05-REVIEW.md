---
phase: 05-narrative-deliverables
reviewed: 2026-06-05T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - deliverables/requirements_approach.md
  - deliverables/stakeholder_engagement.md
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-05
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two markdown narrative deliverables for the City of Toronto FSD BA assignment were reviewed against information-integrity dimensions: number fidelity, named-person rules, citation integrity, framing, and markdown quality. Numbers cross-checked against `data/kpi/kpi_values.json` and `deliverables/kpi_definitions.md`.

Assessment: both documents are largely sound on the load-bearing disciplines. Every quantitative figure that does appear is consistent with the locked KPI snapshot (89.0% pooled availability, 5.8%/0.0572 underutilization, 2,080/2,086 join match, 6 unmatched, 209 nulls, 4,405 denominator, 1,734 exception units, 34 disposal candidates, Heavy −0.0552, Light −0.0351). Named persons are restricted to the three sourced individuals (Jollimore, Lalovic, Lamsaki); ATU locals and PMMD are correctly flagged as illustrative. AG themes (2019.AU2.2 / 2019.AU2.3) open both documents. Disposal framing is consistently "SME screening list, never a disposal decision." RACI accountability is singular per row. No BABOK knowledge-area names are used as section headings. All companion-doc links resolve to existing files.

The one Critical finding is a citation-integrity defect in `stakeholder_engagement.md`: a Sources entry that is never cited inline, combined with quantitative claims that lack the inline `[n]` markers the document's own Method section promises. Remaining findings are warnings/info on consistency and ordering.

## Critical Issues

### CR-01: Dangling source entry + uncited quantitative claims in stakeholder_engagement.md

**File:** `deliverables/stakeholder_engagement.md:67`, `deliverables/stakeholder_engagement.md:151`
**Issue:** The document's Method statement (line 5) explicitly promises that "every quantitative claim is a falsifiable, sourced figure transcribed verbatim from the Phase-3 KPI snapshot ... or a cited external source." It also lists Source **[4] — City of Toronto Open Data portal** (line 151). However:

1. The `[4]` marker is **never used inline anywhere** in the body (grep for `[4]` returns no matches). It is a dangling/orphaned Sources entry — the inverse of the integrity rule that "every inline [n] marker resolves to a Sources entry."
2. The headline quantitative claims on line 67 — "89.0% pooled availability; 5.8% underutilization over 2,080 matched units" — carry **no inline citation marker at all**. These are exactly the externally/Open-Data-derived figures that the Method paragraph says must be cited. The only provenance is via markdown links to companion docs in other rows, not via the promised `[n]` system for these numbers.

This breaks the document's stated citation discipline and leaves a panel-graded deliverable with a self-contradiction: it claims an inline-citation regime it does not apply to its own numbers, and ships an unreferenced source.

**Fix:** Either (a) add inline `[4]` (and/or `[1]` for the AG benchmark) markers to the quantitative claims on line 67 and any other body figures, so the promise in line 5 is honoured and `[4]` resolves; or (b) if the document deliberately defers numeric provenance to the companion docs via markdown links, soften the Method wording on line 5 to match reality and **remove the orphaned `[4]` Sources entry** (or demote it to a non-numbered "Background sources" note). Recommended (a):

```markdown
| SMEs (Lalovic, Lamsaki) | Manage closely | Confirm KPI / class targets and validate the **34-unit disposal screening list** for SME review. | These numbers are the snapshot truth (89.0% pooled availability [4]; 5.8% underutilization over 2,080 matched units [4]); confirm targets and the screening list — they are not a disposal decision. |
```

Note: `requirements_approach.md` does this correctly — all four of its Sources entries ([1]–[4]) are cited inline. Bring `stakeholder_engagement.md` to the same standard.

## Warnings

### WR-01: Reconciliation period framing differs across documents

**File:** `deliverables/requirements_approach.md:110`
**Issue:** The 5.8%-vs-~14% reconciliation in `requirements_approach.md` characterizes the AG figure as "the 2019 baseline" (line 110), while `kpi_definitions.md` line 79 labels the same `~14%` benchmark as "(audit Mar-2023 framing)". Both ultimately cite AG 2019.AU2.3, but a panel reading the deliverables side by side sees two different vintages attributed to the same cited number, which weakens the "carried verbatim from kpi_definitions.md" claim made on line 110.
**Fix:** Align the period descriptor. Pick one provenance phrasing (e.g., "AG 2019 Operational Review baseline, restated in the Mar-2023 audit framing") and use it identically in both `requirements_approach.md:110` and `kpi_definitions.md:79`.

### WR-02: Assumption ID "A3" is ambiguous between this document and the DQ report

**File:** `deliverables/stakeholder_engagement.md:127`
**Issue:** This document defines its own assumption `A3` (line 124, the Open Government Licence caveat). On line 127, caveat DQ-3 ends with "([DQ report](dq_report.md) §3, A3)", where `A3` is intended to mean the DQ report's A3 caveat — but the same token `A3` is a live ID within this very table. A reader cannot tell whether the trailing `A3` is a self-reference or a cross-document reference, and the two `A3`s denote different things.
**Fix:** Qualify the cross-reference, e.g. change to "([DQ report](dq_report.md) §3, caveat A3 there)" or "(dq_report.md §3, A3)" with the link clearly scoping it, so the local `A3` and the DQ-report `A3` are unambiguous.

## Info

### IN-01: Stated-assumption IDs are out of sequence

**File:** `deliverables/stakeholder_engagement.md:122-127`
**Issue:** The Stated Assumptions table lists IDs in the order **A2, A1, A3, DQ-1, DQ-2, DQ-3** — A2 precedes A1. For a deliverable graded on rigor, out-of-order IDs read as a copy/transcribe slip.
**Fix:** Reorder to A1, A2, A3, DQ-1, DQ-2, DQ-3 (and confirm cross-references in §9/§4 still point to the right IDs after reordering).

### IN-02: Two parallel assumption-ID schemes (R-series vs A-series) across the two narrative docs

**File:** `deliverables/requirements_approach.md:118-128`, `deliverables/stakeholder_engagement.md:120-127`
**Issue:** `requirements_approach.md` uses `R1–R9` for its caveats while `stakeholder_engagement.md` uses `A1–A3 / DQ-1–DQ-3`. Both encode overlapping facts (209 nulls, 6 unmatched, ferry sales-vs-redemption, PMMD/ATU illustrative labels), but the divergent ID schemes make it hard to cross-walk "the same assumption" between the two graded deliverables. Not a defect on its own, but a missed consistency opportunity.
**Fix:** Optional — add a one-line note in each Assumptions section mapping the shared caveats (e.g., "R4 here = DQ-1 in stakeholder_engagement.md"), or unify the ID scheme across both narrative docs.

### IN-03: "PMMD" / "ATU local numbers" illustrative flags rely on forward section references

**File:** `deliverables/stakeholder_engagement.md:24`, `deliverables/stakeholder_engagement.md:26`
**Issue:** The register rows for Procurement and ATU defer their illustrative-label disclaimer to "see §8, A2" (forward reference). This is correctly disciplined (the labels are flagged, not asserted as fact), but the disclaimer lives only behind a forward pointer; a reader skimming the register table sees "PMMD" and "Local 113 / 416" as if sourced until reaching §8.
**Fix:** Optional polish — append a short inline qualifier in the table cells themselves (e.g., "(illustrative — A2)") so the role-based caveat travels with the claim rather than only at §8.

---

_Reviewed: 2026-06-05_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
