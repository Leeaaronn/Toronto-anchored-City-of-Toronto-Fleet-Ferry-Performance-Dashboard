---
phase: 05-narrative-deliverables
plan: 01
subsystem: deliverables / documentation
tags: [narrative, babok, requirements, ag-audit, NARR-01]
requires:
  - data/kpi/kpi_values.json (committed snapshot — verbatim numbers)
  - deliverables/kpi_definitions.md (house style, KPI names, AG mapping, 5.8%-vs-14% framing)
  - deliverables/dq_report.md (assumptions-log pattern, DQ facts)
  - deliverables/report_spec.md (disposal screening-list framing, dashboard page names)
provides:
  - NARR-01 requirements-gathering approach full draft
affects:
  - Phase 6 packaging (self-consistency check across the three deliverables)
tech-stack:
  added: []
  patterns:
    - "House-style header block (Project/Scope/Method + 'Why this doc exists' blockquote + ---)"
    - "Provenance-tagged number tables (Computed / Cited discipline)"
    - "Prose-then-table cadence (D-08)"
    - "Numbered inline [n] citations resolved in a Sources & Licence footer (D-05/D-06)"
    - "BABOK v3 traceability table instead of knowledge-area headings (D-01)"
key-files:
  created:
    - deliverables/requirements_approach.md
  modified: []
decisions:
  - "Citation scheme: [1] City Open Data, [2] AG Operational Review 2019.AU2.2/2.3, [3] May 2023 FSD report, [4] BABOK Guide v3 / IIBA — all four used, all four resolved, no dangling/unused markers"
  - "BABOK fluency expressed via a single consolidated traceability table near the end; no BABOK knowledge-area name used as a markdown heading"
  - "Disposal candidates framed verbatim as a 34-unit SME screening list, never a disposal decision (matches kpi_definitions.md KPI 5 / report_spec.md Page 3)"
  - "Observation & surveys framed as planned/forward-looking; document analysis + data/interface analysis framed as performed; interviews/workshops as the immediate next step"
metrics:
  duration: 3min
  completed: 2026-06-05
  tasks: 2
  files: 1
---

# Phase 5 Plan 01: Requirements-Gathering Approach (NARR-01) Summary

Authored `deliverables/requirements_approach.md` — a complete, standalone NARR-01 requirements-gathering approach written as a credible public-sector BA practitioner document: AG-themes-first opening, business context, stakeholder identification (3 named + role-based), four elicitation techniques with honest performed-vs-planned status, all five BABOK v3 requirement types with FSD examples, a prepare/conduct/confirm process, AG-theme traceability with the 5.8%-vs-~14% reconciliation, a nine-row assumptions/constraints log, a BABOK v3 traceability table, and a Sources & Licence footer resolving every inline `[n]`.

## What Was Built

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Front matter through elicitation plan and the five requirement types | 358e17f | deliverables/requirements_approach.md |
| 2 | Process, traceability, assumptions, BABOK traceability, and Sources footer | 10bdaff | deliverables/requirements_approach.md |

**Document structure (157 lines, exceeds the 120-line minimum):**
- House-style header (Project / Scope / Method / Snapshot pull date 2026-06-02) + AG-themes-first "Why this document exists" blockquote naming 2019.AU2.2 and 2019.AU2.3 before any other content.
- Business Context (current-state facts table: 4,614 / 2,086 / 272,529; 89.0%; 209 excluded; 5.8% vs ~14%).
- Stakeholder Identification (Jollimore=Sponsor, Lalovic & Lamsaki=SMEs; all others role/title only).
- Elicitation Plan (4 techniques; document + data/interface analysis performed, interviews/workshops next step, observation & surveys planned/forward-looking).
- Requirement Types (business / stakeholder / functional / non-functional / transition, each with a concrete FSD example).
- Prepare / Conduct / Confirm Process (confirm step tied to the 34-unit SME screening list).
- Traceability to AG Themes (KPI↔AU2.2/AU2.3 table + the 5.8%-vs-~14% period/right-sizing reconciliation).
- Assumptions & Constraints (R1–R9 ID | caveat | disposition table).
- BABOK Guide v3 Traceability (consolidated table; no KA names as headings).
- Sources & Licence (numbered [1]–[4], ending "Open Government Licence – Toronto").

## Verification Evidence

- `test -f deliverables/requirements_approach.md` → exists.
- Task 1 automated: 2019.AU2.2 + 2019.AU2.3 + "screening list" present → PASS.
- Task 2 automated: "Sources & Licence" + "Open Government Licence" + "BABOK" + "assumption" + "~14%" present → PASS.
- AG-themes-first: the "Why this document exists" blockquote (first content block) contains both 2019.AU2.2 and 2019.AU2.3.
- All three sourced names present (Jollimore, Lalovic, Lamsaki); no other personal names anywhere.
- All five requirement-type labels and all four elicitation technique names present; "planned" / "forward-looking" appear with observation & surveys.
- "screening list" + "34" present; "recommend disposal" absent.
- No BABOK knowledge-area string used as a markdown heading (verified by regex over heading lines).
- Inline markers used = {[1],[2],[3],[4]}; numbered Sources entries = {1,2,3,4} — every marker resolves, no dangling, no unused.
- All numeric tokens trace to the number registry / cited sources (no out-of-registry data figures); the only non-registry numerals are AG codes, dates, citation markers, section/list numbers, and the "16:9" PDF-canvas solution constraint from report_spec.md.
- `uv run pytest -q` → 76 passed (no code touched, no regression).

## Deviations from Plan

None — plan executed exactly as written. Numbers quoted verbatim from the registry; the three real names only; disposal framed as an SME screening list; observation/surveys framed as planned.

## Authentication Gates

None.

## Known Stubs

None — the document is a complete standalone draft with no placeholder content.

## Threat Flags

None — no new security-relevant surface; this is a documentation-authoring plan (matches the plan's threat register, which is information-integrity only). All five integrity mitigations (T-05-01 number drift, T-05-02 fabricated identity, T-05-03 dangling citation, T-05-04 licence, T-05-05 claim of work not done) were applied and verified above.

## Self-Check: PASSED

- FOUND: deliverables/requirements_approach.md
- FOUND commit: 358e17f (Task 1)
- FOUND commit: 10bdaff (Task 2)
