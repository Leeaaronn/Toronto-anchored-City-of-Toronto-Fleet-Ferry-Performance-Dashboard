---
phase: 05-narrative-deliverables
plan: 02
subsystem: narrative-deliverables
tags: [stakeholder-engagement, babok, raci, narrative, NARR-02]
requires:
  - "deliverables/kpi_definitions.md (house style + KPI/AG vocabulary + number registry)"
  - "deliverables/dq_report.md (assumptions-log table shape + Sources footer)"
  - "deliverables/report_spec.md (prose-then-table cadence + dashboard page names)"
  - "data/kpi/kpi_values.json (source-of-truth numbers)"
provides:
  - "NARR-02 stakeholder-engagement strategy full draft (deliverables/stakeholder_engagement.md)"
affects:
  - "deliverables/ (second graded narrative deliverable)"
tech-stack:
  added: []
  patterns:
    - "AG-themes-first opening blockquote (2019.AU2.2 / 2019.AU2.3)"
    - "Prose-then-table cadence cloned from kpi_definitions.md / report_spec.md"
    - "Inline [n] citations resolved in a Sources & Licence footer"
    - "Real names only (3 sourced) + role/title-based roster"
    - "BABOK v3 fluency in a traceability table, never as section headings"
key-files:
  created:
    - "deliverables/stakeholder_engagement.md"
  modified: []
decisions:
  - "Cross-linked to deliverables/requirements_approach.md as the sibling NARR-01 deliverable (parallel wave-1 plan 05-01) by name; textual reference is valid even though the file is authored in a sibling worktree."
  - "RACI Committee-communication row uses combined R/A on the Sponsor (GM both performs and owns the report); all other rows keep Accountable singular."
  - "Source row counts (4,614/2,086/272,529) are in-registry but were not needed in the prose; only used numbers must trace to the registry, not every registry number must appear."
metrics:
  duration: "~6 min"
  tasks: 2
  files: 1
  completed: "2026-06-05"
---

# Phase 5 Plan 02: Stakeholder-Engagement Strategy (NARR-02) Summary

Authored `deliverables/stakeholder_engagement.md` — a complete, standalone NARR-02 stakeholder-engagement strategy written as a credible public-sector BA document: an AG-themes-first opening, a stakeholder register (3 sourced names + role-based roster), a power/interest grid, a RACI matrix, engagement approach per group, a communication plan, feedback loops, a risks table, a stated-assumptions log, a BABOK v3 traceability table, and a Sources & Licence footer resolving every inline citation.

## What Was Built

- **Header + AG-themes-first blockquote** cloned from `kpi_definitions.md` house style; the "Why this document exists" blockquote leads with downtime **2019.AU2.2** and underutilization **2019.AU2.3** before any other content.
- **§1 Stakeholder Register** — table of the three sourced named persons (David Jollimore, Vukadin Lalovic, Miguel Lamsaki, all cited to the May 2023 FSD report) plus the role/title-based roster (Auditor General, client divisions, Finance/Budget, Procurement/PMMD, Fleet IT/Telematics, ATU, General Government Committee).
- **§2 Power/Interest Grid** — quadrant table (manage closely / keep satisfied / keep informed / monitor) with placement rationale.
- **§3 RACI Matrix** — activities × roster roles, Accountable singular per row, disposal row uses the locked "34-unit disposal screening list" wording.
- **§4 Engagement Approach**, **§5 Communication Plan**, **§6 Feedback Loops**, **§7 Risks** — each prose-then-table, owners are roster roles only.
- **§8 Stated Assumptions** — cloned from `dq_report.md` §6 (ID | Caveat | Disposition); role-based specifics (ATU 113/416, PMMD) marked as stated assumptions (A2), BABOK task labels (A1), OGL name reuse (A3), data-fidelity caveats echoed.
- **§9 BABOK Guide v3 Traceability** — single table mapping sections to knowledge areas and tasks/techniques (Stakeholder List/Map/Personas; RACI); no knowledge-area name used as a heading.
- **§10 Sources & Licence** — numbered list resolving [1]–[3] (AG Operational Review; May 2023 FSD report; BABOK v3/IIBA) plus Open Data and the verbatim "Open Government Licence – Toronto" line.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Front matter, register, power/interest grid, RACI | ec353a7 | deliverables/stakeholder_engagement.md |
| 2 | Engagement approach, comms plan, feedback loops, risks, assumptions, BABOK traceability, Sources | c519498 | deliverables/stakeholder_engagement.md |

## Verification

- `test -f deliverables/stakeholder_engagement.md` — PASS.
- Opens with AG framing (2019.AU2.2 + 2019.AU2.3 in the blockquote) — PASS.
- Register (3 named + role-based), power/interest grid, RACI, engagement approach, communication plan, feedback loops, risks, stated assumptions — all present.
- Only the three sourced names appear as persons (scan: Jollimore ×11, Lalovic ×8, Lamsaki ×7; no honorific+name patterns, no invented director names) — PASS.
- Every inline [n] ([1]–[3]) resolves to a numbered Sources entry and vice versa — PASS.
- All numbers trace to the number registry (89.0%, 4,405, 209, 5.8%, ~14%, 34, 2,080, 6, 113/416, 2026-06-02, AG codes) — PASS.
- Disposal framed as a 34-unit SME screening list ("screening list" ×14; the only "recommend disposal" string is the negation "never to recommend disposal") — PASS.
- No BABOK knowledge-area name used as a markdown heading — PASS.
- File is 154 lines (≥ 120 min) — PASS.
- `uv run pytest -q` unchanged: no source code touched (git status shows only the markdown deliverable) — PASS by construction.

## Deviations from Plan

None — plan executed exactly as written. The plan references `deliverables/requirements_approach.md` for a cross-link; that file is the NARR-01 deliverable authored by the parallel wave-1 plan (05-01) and is referenced by name (a valid textual cross-link even when authored in a sibling worktree).

## Known Stubs

None. The deliverable is a complete standalone draft with no placeholder data, no TODO/FIXME markers, and no unwired sections.

## Self-Check: PASSED

- FOUND: deliverables/stakeholder_engagement.md
- FOUND commit: ec353a7 (Task 1)
- FOUND commit: c519498 (Task 2)
