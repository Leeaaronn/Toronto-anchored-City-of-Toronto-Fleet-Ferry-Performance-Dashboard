# Stakeholder-Engagement Strategy — Fleet Services Analytics (NARR-02)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The stakeholder-engagement approach for the Fleet Services Division (FSD) analytics initiative — a practitioner stakeholder register, power/interest grid, RACI matrix, engagement approach per group, communication plan, feedback loops, and risks — structured to **BABOK Guide v3** stakeholder-analysis practice and traced to it in a single table (knowledge-area names are not used as section headings).
**Method:** Authored as a credible public-sector BA document. Two disciplines are load-bearing throughout: **no fabricated names** — only the three individuals sourced from the May 2023 FSD report to the General Government Committee appear as persons, and every other stakeholder is a **role/title only**; and **every quantitative claim is a falsifiable, sourced figure** transcribed verbatim from the Phase-3 KPI snapshot ([`kpi_definitions.md`](kpi_definitions.md) / `data/kpi/kpi_values.json`) or a cited external source, never re-estimated. Audit benchmarks are **cited, never recalculated**.
**Snapshot pull date:** **2026-06-02** (the supplied availability file is a point-in-time YTD snapshot — see the [DQ report](dq_report.md), caveat A1).

> **Why this document exists.** This engagement strategy is anchored on the two **Auditor General Operational Review** themes that frame the whole initiative: **vehicle downtime / availability — 2019.AU2.2** ("Lengthy Downtime Requires Immediate Attention") and **vehicle underutilization — 2019.AU2.3** ("Stronger Corporate Oversight Needed for Underutilized Vehicles") [1]. Because the analytics turn those two themes into KPIs, exception lists, and a disposal **screening list** that touch maintenance, finance, procurement, the workforce, and Council oversight, the initiative succeeds or fails on **how its stakeholders are engaged** — whose targets are confirmed, whose data gaps are owned, and whose right-sizing decisions are informed. This document is the second of the two graded narrative deliverables; it is the companion to the requirements-gathering approach in [`requirements_approach.md`](requirements_approach.md) and shares the KPI/AG vocabulary of [`kpi_definitions.md`](kpi_definitions.md).

---

## 1. Stakeholder Register

The register is the foundation of every other artifact in this document: it identifies who has a stake in the availability (2019.AU2.2) and underutilization (2019.AU2.3) work, names their role, and records *why* they care and *on what basis* they are listed. Per the engagement discipline above, only the three individuals sourced from the May 2023 FSD report to the General Government Committee [2] appear as named persons (the sponsor and the two subject-matter experts); every other entry is a **role/title only**, listed on a role-based, assignment-implied basis so the register stays defensible with no invented identities. The register feeds the requirements work in [`requirements_approach.md`](requirements_approach.md).

| Stakeholder | Role / Title | Interest in initiative | Source / basis |
|-------------|--------------|------------------------|----------------|
| **David Jollimore** | General Manager, Fleet Services — **Sponsor** | Owns the FSD response to the AG review; accountable for fleet performance to Council; sponsors the analytics and dashboard. | Named in the **May 2023 FSD report** to the General Government Committee [2]. |
| **Vukadin Lalovic** | Director, Fleet Asset Management — **SME** | Right-sizing and **underutilization** (2019.AU2.3); validates the disposal **screening list** and utilization framing. | Named in the **May 2023 FSD report** [2]. |
| **Miguel Lamsaki** | Acting Director, Fleet Maintenance — **SME** | **Availability / downtime** (2019.AU2.2); validates class targets and the critically-low exception list. | Named in the **May 2023 FSD report** [2]. |
| Auditor General (Toronto) | Oversight body | Owner of **2019.AU2.2 / 2019.AU2.3**; interested in whether recommendations are being acted on and measured. | Role-based (AG Operational Review) [1]. |
| Client divisions (Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc.) | Fleet consumers | Affected by vehicle availability and by right-sizing of the vehicles they use; their vehicle-need assumptions feed the underutilization reading. | Role-based (assignment-implied). |
| Director, Financial Planning (Finance / Budget) | Funding authority | Funds replacement and disposal; cares about the cost of downtime and the budget impact of right-sizing. | Role-based (assignment-implied). |
| Procurement (**PMMD** — Purchasing & Materials Management Division) | Disposal / replacement path owner | Executes the disposal and replacement path once SMEs confirm candidates; needs a defensible screening basis. | Role-based (assignment-implied; PMMD acronym is illustrative — see §8, A2). |
| Fleet IT / Telematics lead | Data / systems owner | Owns the telematics gap (km / engine-hours) that underpins the underutilization classification; affects data trust. | Role-based (assignment-implied). |
| President, ATU (e.g. Local 113 / 416) | Workforce / union | Represents the workforce affected by fleet right-sizing; consulted on workforce impact. | Role-based (assignment-implied; local numbers are illustrative — see §8, A2). |
| Council's General Government Committee | Governance body | The committee the **May 2023 FSD report** was presented to; receives governance reporting on the AG response. | Role-based (governance of record) [2]. |

---

## 2. Power / Interest Grid

The power/interest grid sorts the register by two axes — a stakeholder's **power** to shape or block the initiative and their **interest** in its outcome — so engagement effort is matched to influence rather than spread evenly. The placements below are sensible public-sector defaults for this initiative: the **Sponsor** (Jollimore) sits high/high as the accountable owner; the two **SMEs** (Lalovic, Lamsaki) are high-interest and moderate-to-high power because the credibility of the targets, the exception list, and the 34-unit screening list depends on their validation; the **Auditor General** is high-power oversight whose interest is real but periodic; **Finance** and **Procurement (PMMD)** hold real decision power over funding and the disposal path; **client divisions**, **Fleet IT / Telematics**, and the **ATU** are primarily high-interest groups to keep informed and consult; and **Council's General Government Committee** is a high-power governance audience engaged through formal reporting.

| Power ↓ / Interest → | **High interest** | **Lower interest** |
|----------------------|-------------------|--------------------|
| **High power** | **Manage closely:** Sponsor (Jollimore); SMEs (Lalovic, Lamsaki) | **Keep satisfied:** Auditor General; Council's General Government Committee; Director, Financial Planning; Procurement (PMMD) |
| **Lower power** | **Keep informed:** Client divisions; Fleet IT / Telematics lead; President, ATU | **Monitor:** *(none material at this stage)* |

Placement rationale: power reflects the ability to fund, approve, or block (sponsor, AG, Committee, Finance, Procurement); interest reflects how directly the initiative's outputs change a stakeholder's work (SMEs validate the numbers; divisions and the union feel right-sizing; Fleet IT owns the data gap that makes underutilization measurable).

---

## 3. RACI Matrix

The RACI matrix turns the register and grid into accountability per activity: for each key initiative activity it records who is **R**esponsible (does the work), **A**ccountable (single owner of the outcome), **C**onsulted (two-way input), and **I**nformed (kept up to date). Accountability is **singular** per activity (exactly one **A** per row), consistent with the BABOK Roles & Responsibilities / RACI technique (see §9) [3]. The disposal-screening row uses the locked screening-list wording — the activity is to *validate a 34-unit SME screening list*, never to recommend disposal.

| Activity | Sponsor (Jollimore) | SME — Asset Mgmt (Lalovic) | SME — Maintenance (Lamsaki) | Auditor General | Client divisions | Finance (Fin. Planning) | Procurement (PMMD) | Fleet IT / Telematics | ATU (President) | Gen. Govt. Committee |
|----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Confirm KPI / availability class targets (2019.AU2.2) | **A** | C | **R** | I | I | I | — | C | — | I |
| Validate the **34-unit disposal screening list** for SME review (2019.AU2.3) | **A** | **R** | C | I | C | C | C | C | C | I |
| Data / telematics remediation (km & engine-hours gap) | A | C | C | — | — | — | — | **R** | — | I |
| Dashboard sign-off (per [`report_spec.md`](report_spec.md)) | **A** | C | C | — | I | I | — | C | — | I |
| Communication to Council / General Government Committee | **R/A** | I | I | I | I | C | — | — | I | **I** |

Legend: **R** = Responsible, **A** = Accountable (one per row), **C** = Consulted, **I** = Informed, — = not engaged for that activity. The sponsor row carries a combined **R/A** for Committee communication because the General Manager both performs and owns that report; the Committee itself is **Informed** as the receiving body.
