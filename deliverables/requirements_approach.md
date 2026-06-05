# Requirements-Gathering Approach — Fleet Services Analytics (NARR-01)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The business-analysis approach for eliciting, classifying, and tracing the requirements behind the Fleet Services dashboard, anchored on the two Auditor General Operational Review themes — vehicle downtime (**2019.AU2.2**) and underutilization (**2019.AU2.3**). This document is one of two narrative deliverables; the companion is [`stakeholder_engagement.md`](stakeholder_engagement.md).
**Method:** Practitioner-structured (real-world headings such as *Business Context*, *Stakeholder Identification*, *Elicitation Plan*) with an explicit **BABOK Guide v3** traceability table near the end — framework fluency lives in that table, not in the headings. Every external figure carries an inline numbered citation `[n]` resolved in the [Sources & Licence](#sources--licence) section; **no number is recomputed** — every quantitative fact is transcribed verbatim from the committed KPI snapshot (`data/kpi/kpi_values.json`, locked by `tests/test_kpis.py`) or cited from a source document. Audit benchmarks (asset-class targets, the ~14% underutilization figure) are **cited, never recalculated**.
**Snapshot pull date:** **2026-06-02** (the supplied availability file is a point-in-time YTD snapshot — see the [DQ report](dq_report.md), caveat A1).

> **Why this document exists.** The City of Toronto's Auditor General (AG) Operational Review of Fleet Services raised two themes that this whole initiative answers to: **vehicle downtime** (**2019.AU2.2**, "Lengthy Downtime Requires Immediate Attention") and **vehicle underutilization** (**2019.AU2.3**, "Stronger Corporate Oversight Needed for Underutilized Vehicles") [2]. The requirements-gathering approach below exists to make sure the Fleet Services analytics and dashboard demonstrably *trace back to those two audit themes* — that every KPI, exception list, and the value-added availability⋈utilization cross-measure is elicited, classified, and traced as a defensible response to **2019.AU2.2** and **2019.AU2.3**, not as analysis for its own sake.

---

## Business Context

The Fleet Services Division (FSD) manages the City of Toronto's vehicle fleet and the Toronto Island Ferry operation. The May 2023 FSD report to Council's General Government Committee responded to the AG's 2019 Operational Review and committed to improving fleet maintenance efficiency and right-sizing the fleet [3]. The two AG themes — downtime (**2019.AU2.2**) and underutilization (**2019.AU2.3**) — frame the analytics initiative: the dashboard must let FSD management see availability against audit targets, see how underutilized the light-duty fleet is, and surface the small cross-cut of units that are *both* low-availability *and* underutilized [2].

The current state is grounded in three source datasets published on the City of Toronto Open Data portal [1] — vehicle availability, light-duty utilization, and Toronto Island Ferry ticket counts — with row counts of **4,614 / 2,086 / 272,529** respectively [1]. These are the factual baseline the requirements are built on; the headline insight already visible in the data is that the computed underutilization rate of **5.8%** sits materially below the AG's **~14%** benchmark [2], a gap framed (per the analysis layer) as a period / right-sizing insight rather than an error.

The table below states the current-state facts the requirements respond to. Every figure is transcribed from the committed analysis snapshot or a cited source.

| Current-state fact | Value | Source |
|--------------------|-------|--------|
| Source datasets (availability / utilization / ferry) row counts | **4,614 / 2,086 / 272,529** | **Computed** — City Open Data, profiled at ingest [1] |
| Overall vehicle availability rate (pooled) | **0.8899 ≈ 89.0%** | **Computed** — over the **4,405** non-null denominator |
| Null `AVAILABILITY_YTD` rows excluded (not imputed) | **209 (4.53%)** | **Computed** — locked DQ decision |
| Overall light-duty underutilization rate | **5.8% (0.0572)** | **Computed** — over **2,080** matched light-duty units |
| Audit underutilization benchmark | **~14%** | **Cited** — AG Operational Review **2019.AU2.3** [2] |

---

## Stakeholder Identification

Requirements have owners. This section identifies who the requirements are elicited from and confirmed with. Only three individuals are named — they are the sourced names from the May 2023 FSD report to the General Government Committee [3]; every other stakeholder appears by **role/title only**, with no invented personal names. The full register, power/interest analysis, RACI, and engagement plan live in the companion [`stakeholder_engagement.md`](stakeholder_engagement.md); this section identifies who feeds and confirms the requirements.

The prose maps to the table that follows: the **Sponsor** owns the business requirements and the mandate to answer the audit; the two **SMEs** own the subject-matter validation of the KPI targets and the disposal screening list; the role-based stakeholders are the consumers and oversight bodies whose needs the solution and transition requirements must satisfy.

| Stakeholder | Role in this initiative | Requirements they own / confirm | Source |
|-------------|-------------------------|----------------------------------|--------|
| **David Jollimore**, General Manager, Fleet Services | **Sponsor** | Business requirements; the mandate to demonstrably answer **2019.AU2.2** / **2019.AU2.3** | May 2023 FSD report [3] |
| **Vukadin Lalovic**, Director, Fleet Asset Management | **SME** (utilization, right-sizing) | Confirms underutilization KPI scope and the 34-unit disposal screening list | May 2023 FSD report [3] |
| **Miguel Lamsaki**, Acting Director, Fleet Maintenance | **SME** (availability, downtime) | Confirms availability targets and the critically-low exception list | May 2023 FSD report [3] |
| Auditor General (Toronto) | Oversight | Owner of the **2019.AU2.2 / 2019.AU2.3** themes the initiative answers to | AG Operational Review [2] |
| Client divisions (Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc.) | Fleet consumers | Availability and right-sizing needs that drive the by-division views | City Open Data / FSD [1][3] |
| Director, Financial Planning (Finance / Budget) | Funding authority | Cost-of-downtime and replacement/disposal funding requirements | Role-based (stated assumption) |
| Procurement (PMMD — Purchasing & Materials Management Division) | Procurement path | Disposal/replacement procurement requirements | Role-based (stated assumption) |
| Fleet IT / Telematics lead | Data owner | The telematics (km / engine-hour) gap the underutilization classification depends on | Role-based (stated assumption) |
| President, ATU (workforce / union) | Workforce | Workforce-impact constraints on any fleet right-sizing | Role-based (stated assumption) |
| Council's General Government Committee | Governance | The governance body the May 2023 FSD report was presented to | May 2023 FSD report [3] |

---

## Elicitation Plan

Requirements are elicited with a deliberate mix of techniques, each chosen for a specific FSD reason. Two of the four techniques **were performed** in this assignment (the project was supplied as a data-only exercise), one is the **immediate next step**, and one is **planned / forward-looking** — and the document is explicit about which is which, so no claim is made about work that was not done.

The prose-then-table cadence below pairs each technique with its FSD-specific rationale and its honest performed-vs-planned status.

| Technique | FSD-specific rationale | Status |
|-----------|------------------------|--------|
| **Document analysis** | The AG Operational Review (**2019.AU2.2 / 2019.AU2.3**) [2], the May 2023 FSD report to the General Government Committee [3], and the three Open Data source datasets [1] were read to extract the audit themes, the audit-cited asset-class targets, and the data baseline. | **Performed** |
| **Data / interface analysis** | The three datasets were profiled, normalized, and the **availability⋈utilization** join was built (**2,080** matched of **2,086**, **6** unmatched) [1]; the telematics (km / engine-hour) gap underlying the underutilization classification was identified as a data-interface constraint. | **Performed** |
| **Interviews / SME workshops** | The **immediate next step**: facilitated sessions with **Vukadin Lalovic** and **Miguel Lamsaki** to confirm the availability targets and the disposal screening list, and with **David Jollimore** to confirm the business requirements and audit-response scope [3]. | **Next step** (not yet performed) |
| **Observation & surveys** | **Planned / forward-looking**: job-shadowing maintenance bays and ferry operations, and surveying client divisions on availability pain points. These are proposed techniques for a live engagement; the assignment itself was data-only, so observation and surveys have **not** been performed. | **Planned / forward-looking** |

The performed-versus-planned distinction is deliberate: document analysis and data/interface analysis are the work actually done on the supplied data; interviews/workshops are the natural next move to confirm targets with the SMEs; and observation and surveys remain forward-looking proposals, framed as planned rather than claimed as completed.

---

## Requirement Types

Requirements are classified using the BABOK Guide v3 classification schema [4]: **business**, **stakeholder**, **solution** (split into **functional** and **non-functional**), and **transition**. Classifying requirements this way keeps the high-level audit mandate distinct from the concrete dashboard behaviours and from the hand-off activities — and it makes traceability to the AG themes explicit. Each type is illustrated below with a concrete FSD example tied to a KPI or an AG theme; the prose paragraph is followed by the classification table.

In FSD terms: the **business** requirement is the audit-driven mandate; **stakeholder** requirements are what the Sponsor and SMEs each need to see; **functional** requirements are specific dashboard behaviours (such as showing availability gap-to-target by asset class); **non-functional** requirements are qualities such as a panel-readable PDF export; and the **transition** requirement is the SME validation of the 34-unit disposal screening list before any disposal process — a screening list for SME review, never a disposal decision.

| Type | Definition (BABOK v3 schema) [4] | Concrete FSD example |
|------|----------------------------------|----------------------|
| **Business** | High-level goals/needs of the enterprise | Demonstrably respond to AG **2019.AU2.2** (downtime) and **2019.AU2.3** (underutilization) by surfacing availability and right-sizing insight to FSD management [2] |
| **Stakeholder** | Needs of a specific stakeholder or group | The Sponsor needs an executive Summary / Insights view; the maintenance SME needs the critically-low exception list (**1,734** below-target units) |
| **Functional** (solution) | What the solution must *do* | The dashboard shows **availability gap-to-target by asset class** (e.g. Heavy **79.5% vs 85**, gap **−0.0552**; Light **91.5% vs 95**, gap **−0.0351**) |
| **Non-functional** (solution) | Quality attributes / constraints on the solution | The report **exports to a panel-readable PDF** (16:9 landscape, fit-to-page); availability rates exclude the **209** NULLs (denominator **4,405**), never imputed |
| **Transition** | Temporary capabilities needed to move to the future state | **SME validation of the 34-unit disposal screening list** before any disposal process — a screening list for SME review, not a disposal decision |
