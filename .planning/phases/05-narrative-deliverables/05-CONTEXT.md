# Phase 5: Narrative Deliverables - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver **full drafts of the two narrative BA artifacts** as markdown documents under `deliverables/`:

1. **Requirements-gathering approach** (`NARR-01`) — business context, stakeholder identification, elicitation techniques with rationale, requirements types, prepare/conduct/confirm process, traceability to AG themes, assumptions and constraints.
2. **Stakeholder-engagement strategy** (`NARR-02`) — stakeholder register with real named stakeholders, power/interest grid, RACI matrix, engagement approach per group, communication plan, feedback loops, risks.

Discussion clarified **HOW** to write them. The following are **locked by the roadmap** and are NOT open decisions:
- Both documents open with AG theme framing: downtime (2019.AU2.2) + underutilization (2019.AU2.3).
- Every external number carries an inline citation.
- Disposal candidates are phrased as a **screening list for SME review**, never as decisions.
- An explicit stated-assumptions section is present in both documents.

**Carried forward (decided in prior phases / PROJECT.md — do not re-ask):**
- Real named stakeholders (May 2023 FSD report to General Government Committee): **David Jollimore** (General Manager, Fleet Services — sponsor), **Vukadin Lalovic** (Director, Fleet Asset Management — SME), **Miguel Lamsaki** (Acting Director, Fleet Maintenance — SME). Client divisions: Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc. Oversight: Auditor General.
- Sourcing: City of Toronto Open Data, May 2023 FSD report, AG Operational Review (2019.AU2.2 / 2019.AU2.3); Open Government Licence – Toronto.
- 5.8% (current) vs ~14% (audit Mar 2023) underutilization is framed as a legitimate insight (period / fleet right-sizing), not an error.
- Deliverables are markdown under `deliverables/` (established pattern Phases 1–4).

**Out of scope:** the Power BI canvas (manual, user-authored); the report spec (Phase 4, done); packaging/README (Phase 6). These documents are narratives — they do not recompute or introduce any new numbers beyond what the KPI snapshot and cited sources already establish.

**Audience:** FSD management + the BA-assignment panel (70% pass mark → panel interview with 10-minute presentation). Documents must read as credible public-sector BA artifacts, defensible line-by-line.

</domain>

<decisions>
## Implementation Decisions

### Structure & framework rigor
- **D-01: Practitioner structure + BABOK traceability callout.** Real-world readable headings (Business Context, Stakeholder Identification, Elicitation Plan, etc.) — NOT strict BABOK knowledge-area headings — but each document carries an explicit **BABOK-technique traceability callout/table** mapping sections/techniques to BABOK Guide v3 tasks, so the panel sees framework fluency without an academic read.
- **D-02: Full requirements-types breakdown with FSD examples.** The requirements-gathering doc defines all five types — business, stakeholder, functional (solution), non-functional (solution), transition — and illustrates **each** with a concrete FSD example tied to the KPIs/AG themes (e.g., functional: "dashboard shows availability gap-to-target by asset class"; non-functional: "PDF export readable by the panel"; transition: "SME validation of the disposal screening list before any disposal process").

### Stakeholder register
- **D-03: Extended role-based register.** Register includes: the 3 named real stakeholders + Auditor General + client divisions, PLUS plausible role-based stakeholders the assignment implies — Finance/Budget, Procurement (PMMD), Fleet IT/telematics, ATU/union (workforce impact of fleet right-sizing), and Council's General Government Committee. Gives the power/interest grid and RACI real substance.
- **D-04: Role titles only — no invented personal names.** Named individuals are strictly the 3 sourced real people. Every other stakeholder appears by role/title (e.g., "Director, Financial Planning"; "President, ATU Local 416/113"). No fabricated names anywhere in a graded deliverable.

### Citations & sourcing
- **D-05: Numbered inline citations `[1]` + Sources section.** Bracketed numeric markers inline, resolved in a "Sources" section at the end of each document, including the Open Government Licence – Toronto note. Works in markdown and PDF export.
- **D-06: Cite methodology sources too.** BABOK Guide v3 / IIBA cited for framework claims (techniques, requirements types, stakeholder-analysis tools), alongside the three domain primaries (City Open Data, May 2023 FSD report, AG Operational Review 2019.AU2.2/2.3).

### Format & depth
- **D-07: Two separate comprehensive files.** `deliverables/requirements_approach.md` and `deliverables/stakeholder_engagement.md` — each a thorough standalone full draft (the user refines later). Not combined, not abbreviated.
- **D-08: Tables + framing prose.** Structured artifacts (stakeholder register, power/interest grid, RACI, requirements-types breakdown, traceability) rendered as markdown tables, each preceded by a short prose paragraph explaining what it is and why it matters. Scannable but still narrative.

### Elicitation techniques (requirements-gathering doc)
- **D-09: Four techniques featured, each with FSD-specific rationale:**
  1. **Document analysis** — the backbone: AG audit reports, May 2023 FSD report, the three datasets.
  2. **Interviews / SME workshops** — structured interviews + facilitated workshops with the named SMEs (Lalovic, Lamsaki) and GM sponsor (Jollimore); core for confirming KPI targets and the disposal screening list.
  3. **Data/interface analysis** — profiling the supplied datasets, the availability⋈utilization join, the telematics gap — ties the data-engineering work into the BA narrative as elicitation of data/system requirements.
  4. **Observation & surveys** — job-shadowing maintenance ops / ferry boarding, division-level surveys on vehicle need; framed honestly as **planned/forward-looking techniques** (the assignment itself was data-only), not as work already performed.

### Claude's Discretion
- Communication-plan cadence specifics, risk-section depth, exact power/interest quadrant placements, and tone/voice details — planner/executor sets sensible public-sector defaults consistent with the decisions above.
- Section ordering within each doc (beyond AG-themes-first opening, which is locked).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 5: Narrative Deliverables" — goal + the 4 success criteria.
- `.planning/REQUIREMENTS.md` — **NARR-01, NARR-02** (the two requirements this phase satisfies).
- `.planning/PROJECT.md` §Context — real stakeholder names/roles, AG themes, dataset facts, deliverable/assessment context. The authoritative stakeholder source.
- `CLAUDE.md` — sourcing rules (three primaries + Open Government Licence – Toronto), assessment constraints.

### Content inputs (numbers and findings the narratives reference — never recompute)
- `deliverables/kpi_definitions.md` — confirmed KPI names for AG-theme traceability, audit benchmarks, the 5.8%-vs-14% reconciliation note.
- `deliverables/dq_report.md` — stated DQ assumptions to echo (209 nulls / 4,405 denominator; 6 unmatched UNIT_NO; sales-vs-redemption interpretation flagged for SME validation; retired-dataset pull-date caveat).
- `deliverables/measures_spec.md` — measure/KPI vocabulary consistency.
- `deliverables/report_spec.md` — the dashboard the narratives describe (3 pages, AG-themes-first Summary, disposal screening list framing).
- `data/kpi/kpi_values.json` — falsifiable values for any number quoted in the narratives.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`deliverables/` doc set** (data_dictionary, dq_report, kpi_definitions, measures_spec, report_spec) — established markdown deliverable style, citation discipline, and the exact numbers/insights the narratives must echo verbatim.
- **`data/kpi/` committed snapshot** — every number quoted in the narratives must trace to these values (committed-artifact philosophy from Phase 3).

### Established Patterns
- **Falsifiable/committed-value philosophy:** narratives quote only numbers that exist in the KPI snapshot or carry an external citation — no new computation, no uncited figures.
- **SME-screening framing:** disposal candidates are a screening list for SME review (locked Phase 3/4 framing) — narratives must use identical language.
- **Deliverables are markdown** under `deliverables/`; this phase adds two files there.

### Integration Points
- The narratives reference the dashboard exactly as `report_spec.md` defines it (page names, AG-themes-first summary hierarchy) and the KPI names exactly as `kpi_definitions.md` defines them — vocabulary consistency across all three required deliverables is itself a graded quality (Phase 6 confirms self-consistency).

</code_context>

<specifics>
## Specific Ideas

- The panel context (70% pass → interview, 10-minute presentation) means both docs should be **scannable by a grader**: tables for structure, prose for narrative, AG framing up top.
- Honesty posture: forward-looking techniques (observation, surveys) framed as planned, not performed; no invented names; assumptions stated explicitly — defensibility over polish.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-narrative-deliverables*
*Context gathered: 2026-06-05*
