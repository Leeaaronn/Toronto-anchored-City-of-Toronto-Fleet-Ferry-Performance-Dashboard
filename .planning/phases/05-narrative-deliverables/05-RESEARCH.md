# Phase 5: Narrative Deliverables - Research

**Researched:** 2026-06-05
**Domain:** Public-sector business-analysis documentation authoring (IIBA/BABOK-structured markdown deliverables)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

These are LOCKED by the roadmap (not open decisions):
- Both documents OPEN with AG theme framing: downtime (**2019.AU2.2**) + underutilization (**2019.AU2.3**). Section ordering elsewhere is discretionary; the AG-themes-first opening is not.
- Every external number carries an inline citation.
- Disposal candidates are phrased as a **screening list for SME review**, never as decisions.
- An explicit stated-assumptions section is present in **both** documents.

Implementation decisions from `/gsd:discuss-phase`:
- **D-01: Practitioner structure + BABOK traceability callout.** Real-world readable headings (Business Context, Stakeholder Identification, Elicitation Plan, etc.) — NOT strict BABOK knowledge-area headings — but each document carries an explicit **BABOK-technique traceability callout/table** mapping its sections/techniques to BABOK Guide v3 tasks.
- **D-02: Full requirements-types breakdown with FSD examples.** The requirements-gathering doc defines all five types — business, stakeholder, functional (solution), non-functional (solution), transition — each illustrated with a concrete FSD example tied to the KPIs/AG themes.
- **D-03: Extended role-based register.** Register = 3 named real stakeholders + Auditor General + client divisions, PLUS plausible role-based stakeholders the assignment implies (Finance/Budget, Procurement/PMMD, Fleet IT/telematics, ATU/union, Council's General Government Committee).
- **D-04: Role titles only — no invented personal names.** Named individuals are strictly the 3 sourced real people. Every other stakeholder appears by role/title. No fabricated names anywhere in a graded deliverable.
- **D-05: Numbered inline citations `[1]` + Sources section.** Bracketed numeric markers inline, resolved in a "Sources" section at the end of each document, including the Open Government Licence – Toronto note.
- **D-06: Cite methodology sources too.** BABOK Guide v3 / IIBA cited for framework claims, alongside the three domain primaries.
- **D-07: Two separate comprehensive files.** `deliverables/requirements_approach.md` and `deliverables/stakeholder_engagement.md` — each a thorough standalone full draft. Not combined, not abbreviated.
- **D-08: Tables + framing prose.** Structured artifacts rendered as markdown tables, each preceded by a short prose paragraph explaining what it is and why it matters.
- **D-09: Four elicitation techniques featured, each with FSD-specific rationale:** (1) Document analysis, (2) Interviews / SME workshops, (3) Data/interface analysis, (4) Observation & surveys (framed as planned/forward-looking, not already performed).

### Claude's Discretion

- Communication-plan cadence specifics, risk-section depth, exact power/interest quadrant placements, tone/voice — set sensible public-sector defaults consistent with the locked decisions.
- Section ordering within each doc (beyond the locked AG-themes-first opening).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

**Out of scope (from CONTEXT domain):** the Power BI canvas (manual); the report spec (Phase 4, done); packaging/README (Phase 6). These documents are narratives — they do **not** recompute or introduce any new numbers beyond what the KPI snapshot and cited sources already establish.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NARR-01 | A full draft of the requirements-gathering approach narrative (BABOK/IIBA structure, real named stakeholders, elicitation techniques, traceability to AG themes, stated assumptions, inline citations) | §Architecture Patterns (doc skeleton for `requirements_approach.md`), §BABOK Framework Reference (knowledge-area + requirement-type mapping), §Source-of-Truth Number Registry (numbers to echo verbatim), §Common Pitfalls |
| NARR-02 | A full draft of the stakeholder-engagement strategy narrative (stakeholder register, power/interest grid, RACI, engagement + communication plan, feedback loops, risks, inline citations) | §Architecture Patterns (doc skeleton for `stakeholder_engagement.md`), §Stakeholder Register Reference (D-03/D-04 roster), §BABOK Framework Reference (stakeholder-analysis tasks), §Common Pitfalls |
</phase_requirements>

## Summary

This is a **documentation-authoring phase**, not a code or data phase. It produces two standalone markdown deliverables under `deliverables/`, mirroring the established style of the five existing docs (`data_dictionary.md`, `dq_report.md`, `kpi_definitions.md`, `measures_spec.md`, `report_spec.md`). There is **no package to install, no external runtime dependency, no compute step, and no test framework wiring** — the only "validation" is editorial consistency (numbers trace to the committed snapshot; vocabulary matches the existing docs; citations resolve).

The dominant risk is not technical — it is **fabrication and number drift**. Every external/quantitative claim must trace to either (a) the committed KPI snapshot (`data/kpi/kpi_values.json` and the seven CSVs) or (b) a cited source (the three domain primaries + BABOK v3). Inventing stakeholder names, recomputing numbers, restating the 5.8%/14% figures inconsistently with `kpi_definitions.md`/`dq_report.md`, or phrasing disposal candidates as decisions rather than an SME screening list would each undermine the deliverable's defensibility — which is the graded quality (70% pass → panel interview).

The second-largest risk is **framework fluency without academic stiffness**: the panel wants to see BABOK/IIBA literacy (D-01, D-06) expressed through a real practitioner document, surfaced via an explicit BABOK-traceability table rather than by using BABOK knowledge-area names as headings. BABOK Guide **v3** is confirmed as the current edition (six knowledge areas), which matches the CONTEXT lock.

**Primary recommendation:** Author the two markdown files by **cloning the house style of the existing `deliverables/` docs** (bold-number tables, inline `**Computed**`/`**Cited**` provenance discipline, a `## Sources & Licence` footer), open each with AG-theme framing, drive every number from the Source-of-Truth Number Registry below (copy verbatim — never recompute), use the locked stakeholder roster (3 real names + role titles only), and append a BABOK-traceability table to each document. No new tooling.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Author `requirements_approach.md` (NARR-01) | Deliverables / documentation layer (`deliverables/`) | — | Pure markdown authoring; no code, data, or service tier involved |
| Author `stakeholder_engagement.md` (NARR-02) | Deliverables / documentation layer (`deliverables/`) | — | Same — narrative artifact, not a build artifact |
| Source every quoted number | Committed-snapshot layer (`data/kpi/`) — read-only | Existing deliverable docs (vocabulary source) | Falsifiable-value philosophy: narratives quote, never compute |
| Resolve methodology claims | External cited sources (BABOK v3 / IIBA, AG report, FSD report, Open Data) | — | Framework + domain facts are cited, never derived |

**Note:** This phase touches exactly one tier — the documentation layer. The `data/kpi/` snapshot and the existing `deliverables/*.md` files are **read-only inputs** (vocabulary and number sources); this phase only *writes* two new files into `deliverables/`.

## Standard Stack

**Not applicable — no software stack for this phase.** The deliverables are hand-authored markdown. No libraries, no package manager invocation, no runtime.

The only "tools" are:
- A markdown editor (the GSD executor writes the files via the Write/Edit tools).
- Read-only access to the existing `deliverables/*.md` and `data/kpi/*` for verbatim number/vocabulary sourcing.

**Per CLAUDE.md:** even where this project does have a stack (Python/DuckDB/uv/pytest), it is irrelevant here — this phase introduces no code and therefore no dependency, no `uv add`, no pytest target. Do not scaffold any.

## Package Legitimacy Audit

**Not applicable.** This phase installs **zero** external packages. No registry verification, slopcheck, or postinstall audit is required. Any plan task that proposes `uv add`, `pip install`, or `npm install` for this phase is out of scope and should be rejected.

## Architecture Patterns

### "System" = Document Information Architecture

There is no software architecture. The relevant "architecture" is the **information architecture of each document** and the **data-flow of numbers/citations into the prose**.

```
                 SOURCES (read-only, never modified)
  ┌────────────────────────────────────────────────────────────┐
  │  data/kpi/kpi_values.json  +  data/kpi/*.csv  (numbers)     │
  │  deliverables/kpi_definitions.md   (KPI names, AG mapping)  │
  │  deliverables/dq_report.md         (stated assumptions)     │
  │  deliverables/report_spec.md       (dashboard description)  │
  │  deliverables/measures_spec.md     (measure vocabulary)     │
  │  PROJECT.md / CLAUDE.md            (stakeholders, sourcing) │
  │  EXTERNAL CITED: AG 2019.AU2.2/2.3, May-2023 FSD report,    │
  │                  City Open Data, BABOK Guide v3 / IIBA      │
  └───────────────┬───────────────────────────┬────────────────┘
                  │ verbatim numbers           │ cited facts + framework
                  ▼                            ▼
  ┌──────────────────────────┐   ┌──────────────────────────────┐
  │ deliverables/            │   │ deliverables/                │
  │ requirements_approach.md │   │ stakeholder_engagement.md    │
  │ (NARR-01)                │   │ (NARR-02)                    │
  │                          │   │                              │
  │ 1. AG-theme framing      │   │ 1. AG-theme framing          │
  │ 2. Business context      │   │ 2. Stakeholder register      │
  │ 3. Stakeholder ident.    │   │ 3. Power/Interest grid       │
  │ 4. Elicitation plan (4)  │   │ 4. RACI matrix               │
  │ 5. Requirement types (5) │   │ 5. Engagement approach       │
  │ 6. Prepare/conduct/      │   │ 6. Communication plan        │
  │    confirm process       │   │ 7. Feedback loops            │
  │ 7. Traceability to AG    │   │ 8. Risks                     │
  │ 8. Assumptions & constr. │   │ 9. Stated assumptions        │
  │ 9. BABOK traceability    │   │ 10. BABOK traceability       │
  │ 10. Sources & Licence    │   │ 11. Sources & Licence        │
  └──────────────────────────┘   └──────────────────────────────┘
```

A reader (the panel grader) should be able to: open either file → see the AG audit framing first → scan the structured tables → confirm every number resolves to a `[n]` citation or the committed snapshot → close on a Sources section. The two files share vocabulary and the same Sources footer pattern but stand alone.

### Recommended Output Structure

```
deliverables/
├── data_dictionary.md        # existing (Phase 1) — house-style reference
├── dq_report.md              # existing (Phase 1) — assumptions to echo
├── kpi_definitions.md        # existing (Phase 3) — KPI names + AG mapping
├── measures_spec.md          # existing (Phase 3) — measure vocabulary
├── report_spec.md            # existing (Phase 4) — dashboard the narratives describe
├── requirements_approach.md  # NEW (NARR-01)  ← this phase
└── stakeholder_engagement.md # NEW (NARR-02)  ← this phase
```

### Pattern 1: House-Style Header Block (clone from existing docs)

**What:** Every existing deliverable opens with a `**Project:** / **Scope:** / **Method:**` block, then a `>` blockquote "Why this doc exists" paragraph, then `---`. Replicate this so the two new files are visibly part of the same set.

**When to use:** Top of both new files.

**Example (adapt — pattern lifted verbatim from `kpi_definitions.md`):**
```markdown
# Requirements-Gathering Approach — Fleet Services Analytics (NARR-01)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The business-analysis approach for eliciting, classifying, and tracing the
requirements behind the Fleet Services dashboard, anchored on the two Auditor General
Operational Review themes (downtime 2019.AU2.2 / underutilization 2019.AU2.3).
**Method:** Practitioner-structured (real-world headings) with an explicit BABOK Guide v3
traceability callout. Every external figure carries an inline numbered citation [n] resolved
in the Sources section; no number is recomputed — quantitative facts are transcribed from the
committed KPI snapshot (data/kpi/) or cited from the source documents.

> **Why this document exists.** [AG-theme framing paragraph — downtime + underutilization —
> opens here, satisfying the locked AG-themes-first rule.]

---
```

### Pattern 2: Provenance-Tagged Number Tables (the `**Computed**` / `**Cited**` discipline)

**What:** The existing docs tag every number inline as **Computed** (from the snapshot) or **Cited** (external). The narratives quote numbers, so each quoted figure should still carry its citation `[n]`, and where a number is one the data layer produced, phrase it as drawn from the analysis (it traces to the snapshot) rather than re-derived.

**When to use:** Anywhere a number appears in either narrative.

**Example:**
```markdown
The light-duty utilization analysis classified 5.8% of matched units as Underutilized [4],
materially below the ~14% benchmark in the Auditor General's 2019 Operational Review
(2019.AU2.3) [2]. This gap is read as a period / fleet-right-sizing insight, not an error.
```

### Pattern 3: Prose-then-Table (D-08)

**What:** Every structured artifact (register, power/interest grid, RACI, requirements-types table, traceability table) is preceded by one short prose paragraph stating what the table is and why it matters, then the markdown table. Matches the existing docs and keeps the deliverable scannable yet narrative.

### Pattern 4: BABOK Traceability Callout (D-01 / D-06)

**What:** A table at (or near) the end of each document mapping the document's practitioner sections/techniques to BABOK Guide v3 knowledge areas and tasks. This is how framework fluency is demonstrated without academic headings.

**Example skeleton (NARR-01):**
```markdown
## BABOK Guide v3 Traceability

This document uses practitioner headings; the table below maps them to the BABOK Guide v3
knowledge areas and tasks for the panel's reference. [n]

| This document's section | BABOK v3 Knowledge Area | BABOK v3 Task / Technique |
|-------------------------|-------------------------|---------------------------|
| Elicitation Plan        | Elicitation & Collaboration | Plan / Conduct / Confirm Elicitation; Document Analysis, Interviews, Observation, Survey |
| Requirement Types       | Requirements Analysis & Design Definition | Requirements classification schema (business / stakeholder / solution[functional, non-functional] / transition) |
| Traceability to AG themes | Requirements Life Cycle Management | Trace Requirements |
| Business Context        | Strategy Analysis        | Analyze Current State |
| (Approach planning)     | Business Analysis Planning & Monitoring | Plan Business Analysis Approach / Stakeholder Engagement |
```

### Pattern 5: Sources & Licence Footer (D-05 / D-06)

**What:** Both files end with a numbered `## Sources & Licence` section resolving every inline `[n]`, including BABOK v3 / IIBA and the Open Government Licence – Toronto note. Clone the footer pattern already used by `kpi_definitions.md` / `dq_report.md`.

### Anti-Patterns to Avoid

- **BABOK knowledge-area names as top-level headings.** Locked against by D-01 — use practitioner headings + a traceability table instead.
- **Recomputing or "improving" any number.** Narratives quote the committed snapshot; they never recompute. (Falsifiable-value philosophy, STATE.md / kpi_definitions.md.)
- **Inventing personal names** for any stakeholder beyond the three sourced real people (D-04). Role titles only.
- **Phrasing disposal candidates as decisions / recommendations.** Always "screening list for SME review" (locked; identical to report_spec.md §Page 3 and kpi_definitions.md KPI 5).
- **Claiming observation/surveys were performed.** They are planned / forward-looking (D-09 technique 4; honesty posture in CONTEXT §specifics).
- **Combining the two deliverables** or abbreviating either (D-07).
- **Uncited external numbers.** Every external figure gets a `[n]`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| KPI / availability / ferry numbers | A recomputation or fresh query in the narrative | Quote verbatim from `data/kpi/kpi_values.json` + the existing `kpi_definitions.md` / `dq_report.md` | The numbers are already computed, tested, and committed; recomputing risks drift and breaks the falsifiable-value contract |
| Stakeholder names | Invented personas | The 3 sourced real names + role titles only (D-03/D-04 roster below) | Fabricated names in a graded public-sector deliverable are a credibility failure |
| AG-theme codes / wording | Paraphrasing the audit themes | Reuse the exact codes/labels already in PROJECT.md and the existing docs (2019.AU2.2 downtime, 2019.AU2.3 underutilization) | Vocabulary consistency across the three deliverables is itself graded (Phase 6 self-consistency check) |
| Disposal-candidate framing | A new phrasing | The locked "screening list for SME review, never a disposal decision" wording | Identical framing already in kpi_definitions.md and report_spec.md; must match |
| Citation/Sources mechanism | A bespoke footnote system | Numbered `[n]` inline + `## Sources & Licence` footer (same pattern as existing docs) | Works in markdown and PDF; already the house style |

**Key insight:** Almost everything this phase needs already exists in the repo. The job is **assembly and narrative framing of existing, committed facts** — not generation of new facts. Treat the existing `deliverables/` docs and `data/kpi/` snapshot as the single source of truth and quote them; the only genuinely new content is the BA-methodology narrative (elicitation plan, stakeholder analysis, RACI, communication plan, risks), which is framework-driven and cited to BABOK v3.

## Source-of-Truth Number Registry

> **CRITICAL FOR THE PLANNER:** every number the narratives may reference, with its verbatim value and the doc/snapshot it traces to. Tasks must quote these — never recompute. All values `[VERIFIED: data/kpi/kpi_values.json]` or `[VERIFIED: deliverables/*.md]` unless tagged `[CITED]`.

| Fact | Verbatim value | Provenance | Citation type in narrative |
|------|----------------|------------|----------------------------|
| Overall availability rate (pooled) | **0.8899 ≈ 89.0%** | kpi_values.json `overall_availability_rate` / kpi_definitions.md KPI 1 | Computed (traces to snapshot) |
| Non-null availability denominator | **4,405** | kpi_values.json `availability_nonnull_n` | Computed |
| Null availability rows excluded | **209 (4.53%)** | kpi_values.json `availability_null_n` / dq_report §2 | Computed |
| Light availability vs target | **91.5% vs 95 (gap −0.0351)** | kpi_values.json `availability_by_class.Light` | Computed |
| Medium availability vs target | **86.1% vs 92 (gap −0.0588)** | kpi_values.json `availability_by_class.Medium` | Computed |
| Heavy availability vs target | **79.5% vs 85 (gap −0.0552)** | kpi_values.json `availability_by_class.Heavy` | Computed |
| Off-Road availability vs target | **88.8% vs 88 (gap +0.0082)** | kpi_values.json `availability_by_class["Off-Road"]` | Computed |
| Other availability vs target | **93.4% vs 90 (gap +0.0337)** | kpi_values.json `availability_by_class.Other` | Computed |
| Units below their class target (exception list) | **1,734** | kpi_definitions.md KPI 3 / exception_list.csv | Computed |
| Overall underutilization rate (computed) | **5.8% (0.0572)** | kpi_values.json `overall_underutilization_rate` | Computed |
| Matched light-duty denominator | **2,080** | kpi_values.json `light_duty_matched_n` | Computed |
| Underutilization benchmark (audit) | **~14%** | AG 2019.AU2.3 | **Cited** [AG report] |
| Disposal candidates (SME screening list) | **34** | kpi_definitions.md KPI 5 | Computed |
| Unmatched utilization rows (DQ finding) | **6** (2,080 + 6 = 2,086) | dq_report §7 | Computed |
| Alphanumeric availability UNIT_NO preserved | **44** | dq_report §8 | Computed |
| Conformed `dim_division` count | **21** (owner 21 / using 20, 0 unreconciled) | dq_report §9 | Computed |
| Ferry lifetime sales | **13,257,804** | kpi_values.json `ferry_lifetime_sales` | Computed |
| Ferry lifetime redemptions | **13,076,317** | kpi_values.json `ferry_lifetime_redemptions` | Computed |
| Ferry 2019 sales (pre-pandemic) | **1,249,725** | kpi_values.json `ferry_sales_2019` | Computed |
| Ferry 2020 sales (COVID dip) | **366,606** | kpi_values.json `ferry_sales_2020` | Computed |
| Ferry sales median / max (skew) | **12 / 7,229** | kpi_values.json `ferry_sales_median` / `ferry_sales_max` | Computed |
| Source row counts | **4,614 / 2,086 / 272,529** | dq_report §1 | Computed |
| Snapshot pull date | **2026-06-02** | dq_report / kpi_definitions header | Computed (state inline) |
| Ferry span | **2015-05-01 → 2026-06-01 (~11 yrs)** | dq_report §3 / PROJECT.md | Computed |

**Rule for the planner:** if a number is not in this registry and not in a cited source, the narrative may **not** state it.

## Stakeholder Register Reference (D-03 / D-04)

> The exact roster the NARR-02 register, power/interest grid, and RACI must use. **Named individuals are ONLY the three below; everyone else is a role/title.**

**Real, named, sourced (May 2023 FSD report to the General Government Committee):**

| Name | Title | Role in this initiative | Source |
|------|-------|-------------------------|--------|
| **David Jollimore** | General Manager, Fleet Services | **Sponsor** | May 2023 FSD report [VERIFIED: PROJECT.md / CONTEXT.md] |
| **Vukadin Lalovic** | Director, Fleet Asset Management | **SME** (utilization, right-sizing) | May 2023 FSD report [VERIFIED: PROJECT.md / CONTEXT.md] |
| **Miguel Lamsaki** | Acting Director, Fleet Maintenance | **SME** (availability, downtime) | May 2023 FSD report [VERIFIED: PROJECT.md / CONTEXT.md] |

**Role/title-only stakeholders (no invented names — D-04):**

| Role / title | Why on the register (D-03) |
|--------------|----------------------------|
| Auditor General (Toronto) | Oversight; owner of the 2019.AU2.2 / 2019.AU2.3 themes the whole initiative answers to |
| Client divisions (Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc.) | Fleet consumers; affected by availability + right-sizing |
| Director, Financial Planning (Finance/Budget) | Funding for fleet replacement/disposal; cost of downtime |
| Procurement (PMMD — Purchasing & Materials Management Division) | Disposal/replacement procurement path |
| Fleet IT / Telematics lead | Telematics gap (km/engine-hours) that underutilization classification depends on |
| President, ATU (e.g. Local 113/416) — workforce/union | Workforce impact of fleet right-sizing |
| Council's General Government Committee | Governance body the May 2023 FSD report was presented to |

**Note for planner:** ATU local numbers (113/416) and the exact PMMD acronym are plausible public-sector specifics; tag any uncertain specific as a stated assumption rather than asserting it as sourced fact. The three named individuals and their titles ARE sourced and verified.

## BABOK Framework Reference (for the traceability callouts — D-01 / D-06)

> BABOK Guide **v3** is the current edition [CITED: iiba.org]. Use these for the traceability tables. Where exact task names matter for the panel, the executor should cross-check against the actual BABOK v3 guide if accessible; the items below are standard published BABOK v3 structure.

**Six knowledge areas** [CITED: BABOK Guide v3]:
1. Business Analysis Planning & Monitoring
2. Elicitation & Collaboration
3. Requirements Life Cycle Management
4. Strategy Analysis
5. Requirements Analysis & Design Definition (RADD)
6. Solution Evaluation

**Requirements classification schema** [CITED: BABOK Guide v3] (maps directly to D-02's five types):
- Business requirements
- Stakeholder requirements
- Solution requirements → **functional** and **non-functional**
- Transition requirements

**Techniques to cite for the elicitation plan (D-09)** [CITED: BABOK Guide v3 — all are named BABOK v3 techniques]:
- Document Analysis
- Interviews (+ Workshops / Collaborative Games for the facilitated-workshop framing)
- Interface Analysis / Data Modelling (for the "data/interface analysis" technique)
- Observation and Survey or Questionnaire (the forward-looking pair, D-09 technique 4)

**Stakeholder-analysis tools to cite for NARR-02** [CITED: BABOK Guide v3]:
- Stakeholder List, Map, or Personas (the register + power/interest grid)
- RACI as a roles-and-responsibilities matrix (cite BABOK "Roles and Permissions Matrix" / RACI)

**Caveat:** Exact BABOK v3 task/technique wording was not fully retrievable from the public IIBA site (the detailed guide is paywalled). The knowledge-area list and requirements classification schema above are well-established v3 facts `[CITED: BABOK Guide v3]`; if the executor cannot confirm a *specific* technique's exact label, tag the traceability row generically (e.g. "Elicitation & Collaboration knowledge area") rather than asserting a precise task name that might be mislabeled.

## Common Pitfalls

### Pitfall 1: Number drift across the three deliverables
**What goes wrong:** The narrative states "underutilization is 6%" or "88% availability" — a paraphrase that no longer matches `kpi_definitions.md` / the snapshot.
**Why it happens:** Authoring from memory instead of from the registry.
**How to avoid:** Quote the Source-of-Truth Number Registry verbatim; for any number, open `data/kpi/kpi_values.json` or the relevant existing doc and copy.
**Warning signs:** A number in the narrative that isn't in the registry; rounding that differs from the existing docs (e.g. 89% vs 0.8899); the 5.8%/14% pair stated without the "different period / right-sizing, not an error" framing.

### Pitfall 2: Fabricated stakeholder names
**What goes wrong:** A "Jane Smith, Director of Procurement" appears in the register.
**Why it happens:** Filling a register feels like it needs names.
**How to avoid:** Strictly the 3 sourced names; everyone else is a role/title (D-04). Re-read the register before finalizing and confirm only Jollimore/Lalovic/Lamsaki are named persons.
**Warning signs:** Any proper name not in the sourced trio.

### Pitfall 3: Disposal candidates phrased as decisions
**What goes wrong:** "We recommend disposing of these 34 vehicles."
**Why it happens:** The cross-measure looks like a recommendation.
**How to avoid:** Always "a screening list of 34 candidates for SME review — not a disposal decision." Mirror the exact framing in kpi_definitions.md KPI 5 and report_spec.md Page 3.
**Warning signs:** Verbs like "dispose", "remove", "recommend disposal" without the SME-screening qualifier.

### Pitfall 4: Claiming forward-looking elicitation was performed
**What goes wrong:** "We job-shadowed maintenance operations and surveyed divisions."
**Why it happens:** The elicitation plan reads more impressively in past tense.
**How to avoid:** Frame observation + surveys as **planned / proposed** techniques (the assignment itself was data-only). Document analysis and data/interface analysis WERE performed (the actual project work); interviews/workshops are the natural next step; observation/surveys are forward-looking. Be explicit about which is which.
**Warning signs:** Past-tense claims about activities not actually done in this assignment.

### Pitfall 5: BABOK as academic scaffolding instead of practitioner doc
**What goes wrong:** Top-level headings become "Elicitation & Collaboration", "Requirements Life Cycle Management" — reads like an exam answer.
**Why it happens:** Over-correcting toward demonstrating framework knowledge.
**How to avoid:** Practitioner headings (D-01) + one BABOK traceability table near the end. Framework fluency lives in the table, not the headings.
**Warning signs:** Knowledge-area names used as section titles.

### Pitfall 6: Vocabulary inconsistency with the dashboard the narrative describes
**What goes wrong:** The narrative calls a page "Fleet Summary" when report_spec.md calls it "Summary / Insights", or uses KPI names that differ from kpi_definitions.md.
**Why it happens:** Not cross-referencing the existing specs.
**How to avoid:** Use page names and KPI names exactly as report_spec.md / kpi_definitions.md define them (Phase 6 grades self-consistency across all three deliverables).
**Warning signs:** Any dashboard page name, KPI name, or measure name that doesn't appear verbatim in the existing specs.

## Code Examples

**Not applicable — no code in this phase.** The "examples" the planner needs are the document patterns in §Architecture Patterns above and the existing `deliverables/*.md` files as style templates (especially `kpi_definitions.md` and `dq_report.md` for the header block, provenance discipline, and Sources footer).

## Runtime State Inventory

> This phase is **additive documentation only** — it creates two new files and modifies no existing runtime state, data, services, or config. Included for completeness because the project has prior phases with state.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — narratives quote the existing `data/kpi/` snapshot read-only; no new data written | None — verified by phase scope (no compute step) |
| Live service config | None — no services involved | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | None — markdown files are not compiled; two new files added to `deliverables/` | None (Phase 6 packages them) |

**Nothing found in any category** — this is a pure documentation-authoring phase. The only filesystem change is the creation of `deliverables/requirements_approach.md` and `deliverables/stakeholder_engagement.md`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BABOK v2 (and earlier) | **BABOK Guide v3** (six knowledge areas, perspectives, agile coverage) | v3 is the current standard [CITED: iiba.org] | Cite v3 explicitly; the requirements classification schema (business/stakeholder/solution[functional,non-functional]/transition) is the v3 schema that D-02 maps to |

**Deprecated/outdated:**
- Do not cite "BABOK v2" or unversioned "BABOK" — the CONTEXT and current standard are **v3**.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The detailed BABOK v3 task/technique exact labels (e.g. "Plan Elicitation" vs "Prepare for Elicitation") are as listed in §BABOK Framework Reference | BABOK Framework Reference | LOW — knowledge-area list + requirements schema are confirmed v3 facts; only fine-grained task wording is from training, not retrievable from the paywalled guide. Mitigation: traceability table can reference knowledge areas if a precise task label is uncertain |
| A2 | ATU local numbers (113/416) and the exact PMMD acronym are correct Toronto specifics | Stakeholder Register Reference | LOW — plausible role-based stakeholders (D-03 explicitly permits role-based additions); narrative should present them as role-based/illustrative, and tag any uncertain specific as a stated assumption rather than sourced fact |
| A3 | The "Open Government Licence – Toronto" is the correct licence name to cite | both Sources sections | LOW — stated in CLAUDE.md and existing deliverables' footers; reuse verbatim from those footers |

**Note:** All quantitative claims (the Source-of-Truth Number Registry) are `[VERIFIED]` against the committed snapshot — none are assumed. The three named stakeholders are `[VERIFIED]` against PROJECT.md/CONTEXT.md. The assumptions above are confined to framework-label precision and role-based-stakeholder specifics, both LOW risk and both explicitly within the latitude D-03/D-06 grant.

## Open Questions

1. **Exact BABOK v3 task labels for the traceability table.**
   - What we know: the six knowledge areas and the requirements classification schema (confirmed v3).
   - What's unclear: precise sub-task wording (the public IIBA page is promotional; the guide is paywalled).
   - Recommendation: map to knowledge areas + named techniques (which ARE well-established); if a specific task label is uncertain, reference the knowledge area rather than risk a mislabel. Not a blocker.

2. **Whether the user wants the BABOK traceability as a per-section callout or one consolidated table.**
   - What we know: D-01 says "callout/table" — either is acceptable.
   - Recommendation: one consolidated table near the end of each doc (cleaner, scannable); within Claude's discretion. Not a blocker.

## Environment Availability

**Skipped — no external dependencies.** This phase authors markdown with the existing Write/Edit tooling and reads files already in the repo. No tool, runtime, service, or package is required. (Per Step 2.6 skip condition: pure documentation change.)

## Validation Architecture

> `nyquist_validation` is `true` in config. However, this phase produces **no executable code** — there is nothing to unit/integration test. "Validation" here is **editorial / consistency verification**, performed at the phase gate by `/gsd:verify-work`, not by a pytest run.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None applicable — documentation phase (no code). Existing repo uses pytest, but no new tests belong to this phase. |
| Config file | n/a |
| Quick run command | n/a (editorial review, not automated test) |
| Full suite command | `uv run pytest` still passes unchanged (no code touched) — run once at phase end to confirm no regression |

### Phase Requirements → Verification Map
| Req ID | Behavior | Verification Type | Check | Artifact Exists? |
|--------|----------|-------------------|-------|------------------|
| NARR-01 | Requirements-gathering approach full draft | Editorial / checklist | File exists at `deliverables/requirements_approach.md`; contains all CONTEXT success-criterion sections (business context, stakeholder ident., elicitation w/ rationale, 5 requirement types, prepare/conduct/confirm, AG traceability, assumptions); opens with AG framing; every external number has `[n]`; BABOK traceability table present | ❌ to be created |
| NARR-02 | Stakeholder-engagement strategy full draft | Editorial / checklist | File exists at `deliverables/stakeholder_engagement.md`; contains register (3 real names + role-based), power/interest grid, RACI, engagement approach, communication plan, feedback loops, risks, stated assumptions; opens with AG framing; disposal screening-list framing; every external number has `[n]` | ❌ to be created |
| both | No fabrication / number fidelity | Editorial / checklist | Every number traces to the Source-of-Truth Number Registry; only Jollimore/Lalovic/Lamsaki named as persons; disposal = SME screening list; observation/surveys framed as planned | ❌ to be created |

### Sampling / Gate
- **Per task:** self-review against the relevant CONTEXT success criterion + the number registry.
- **Phase gate:** the editorial checklist above, plus `uv run pytest` confirming no code regression (should be untouched).

### Wave 0 Gaps
- None — no test infrastructure is needed for a documentation phase. (If a future plan proposes adding tests for these markdown files, that is out of scope for NARR-01/02.)

## Security Domain

> `security_enforcement` is **not set** in config (absent = enabled by default). However, this phase has **no security-relevant surface**: no authentication, no session management, no access control, no input handling, no cryptography, no network, no data persistence. It authors two static markdown documents.

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | n/a — no auth surface |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a |
| V5 Input Validation | no | n/a — no runtime input; authored static text |
| V6 Cryptography | no | n/a |

**The one relevant "security/governance" consideration is informational, not technical:** the documents must respect data-sourcing and licensing (Open Government Licence – Toronto) and must not fabricate facts (a defensibility/integrity requirement, not an ASVS control). This is covered by the citation discipline (D-05/D-06) and the no-fabrication pitfalls above. No ASVS controls apply to this phase.

## Sources

### Primary (HIGH confidence)
- `data/kpi/kpi_values.json` (read in session) — every quantitative value in the Source-of-Truth Number Registry.
- `deliverables/kpi_definitions.md`, `deliverables/dq_report.md`, `deliverables/report_spec.md` (read in session) — house style, KPI names, AG-theme mapping, stated assumptions, dashboard structure, disposal-screening framing.
- `.planning/PROJECT.md`, `CLAUDE.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/phases/05-narrative-deliverables/05-CONTEXT.md` (read in session) — stakeholders, sourcing rules, locked decisions, requirements.
- [IIBA — A Guide to the Business Analysis Body of Knowledge (BABOK)](https://www.iiba.org/career-resources/a-business-analysis-professionals-foundation-for-success/babok/) — confirmed **v3** is the current edition with six knowledge areas.

### Secondary (MEDIUM confidence)
- BABOK v3 six knowledge areas + requirements classification schema — standard published v3 structure, corroborated by the IIBA overview page; exact sub-task labels not retrievable from public pages.

### Tertiary (LOW confidence)
- ATU local numbers (113/416) and PMMD acronym specifics — plausible Toronto public-sector roles; treat as role-based/illustrative, not sourced fact (Assumptions A2).

## Metadata

**Confidence breakdown:**
- Document structure / patterns: HIGH — cloned directly from five existing, committed deliverables read this session.
- Numbers to echo: HIGH — verbatim from the committed, test-locked snapshot.
- Stakeholder roster: HIGH for the 3 named (sourced); MEDIUM for role-based additions (D-03 explicitly permits, framed as role-based).
- BABOK framework references: HIGH for edition + knowledge areas + requirements schema; MEDIUM for fine-grained task labels (paywalled guide).
- Pitfalls: HIGH — derived from the project's own locked decisions and existing-doc conventions.

**Research date:** 2026-06-05
**Valid until:** 2026-09-05 (stable — internal docs + a stable published standard; no fast-moving dependency)
