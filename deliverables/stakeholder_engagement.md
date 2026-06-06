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

---

## 4. Engagement Approach (per group)

The engagement approach assigns each group a posture consistent with its power/interest placement (§2) and states the objective and the key message tailored to it. The postures are the standard four — **manage closely**, **keep satisfied**, **keep informed**, **monitor** — applied so that the high/high stakeholders shape the work, the high-power oversight and funding bodies stay satisfied with governance-grade reporting, and the affected operational groups are informed and consulted before any right-sizing lands.

| Group | Posture | Objective | Key message |
|-------|---------|-----------|-------------|
| Sponsor (Jollimore) | Manage closely | Secure direction, unblock decisions, own the AG-response narrative. | The analytics make the AG themes measurable; here are the targets, the exception list, and the screening list to endorse. |
| SMEs (Lalovic, Lamsaki) | Manage closely | Confirm KPI / class targets and validate the **34-unit disposal screening list** for SME review. | These numbers are the snapshot truth (89.0% pooled availability; 5.8% underutilization over 2,080 matched units) [4]; confirm targets and the screening list — they are not a disposal decision. |
| Auditor General (Toronto) | Keep satisfied | Demonstrate the AG recommendations (2019.AU2.2 / 2019.AU2.3) are being measured and acted on. | Downtime and underutilization are now tracked KPIs with cited benchmarks and documented data gaps. |
| Council's General Govt. Committee | Keep satisfied | Provide governance-grade reporting consistent with the May 2023 FSD report. | Progress against the AG themes, with assumptions and caveats stated. |
| Director, Financial Planning | Keep satisfied | Inform funding for replacement / disposal and the cost-of-downtime case. | The exception list and screening list quantify where downtime and underutilization concentrate. |
| Procurement (PMMD) | Keep satisfied | Prepare the disposal / replacement path once SMEs confirm candidates. | The screening list is a defensible SME shortlist, not an automated disposal trigger. |
| Client divisions | Keep informed | Confirm vehicle-need assumptions; manage expectations on availability and right-sizing. | Availability and right-sizing affect the vehicles you use; your input shapes the underutilization reading. |
| Fleet IT / Telematics lead | Keep informed / consult | Own the telematics (km / engine-hours) remediation that underpins underutilization. | The data gap is the limiting factor on the underutilization KPI; remediation improves trust. |
| President, ATU | Keep informed / consult | Consult on workforce impact of right-sizing before decisions. | Right-sizing is evaluated with workforce impact in scope; consultation precedes action. |

---

## 5. Communication Plan

The communication plan operationalizes the engagement postures into concrete touchpoints — who hears what, through which channel, how often, owned by whom, and to what end. Cadences are sensible public-sector defaults for an initiative of this size; owners are **roster roles only**, never invented individuals.

| Audience | Channel | Cadence | Owner | Purpose |
|----------|---------|---------|-------|---------|
| Sponsor (Jollimore) | 1:1 briefing | Bi-weekly | BA / project lead | Direction, decisions, risk escalation. |
| SMEs (Lalovic, Lamsaki) | Working workshop | Bi-weekly (target/validation cycles) | BA / project lead | Confirm targets; validate the 34-unit screening list; resolve DQ questions. |
| Client divisions | Division update / email digest | Monthly | BA / project lead | Vehicle-need assumptions; availability and right-sizing expectations. |
| Director, Financial Planning | Summary memo | At milestones | Sponsor (Jollimore) | Funding implications of the exception and screening lists. |
| Procurement (PMMD) | Handoff note | On screening-list sign-off | SME — Asset Mgmt (Lalovic) | Confirmed candidates for the disposal / replacement path. |
| Fleet IT / Telematics lead | Technical sync | Monthly | BA / project lead | Telematics remediation status; data-trust items. |
| President, ATU | Consultation session | At right-sizing decision points | Sponsor (Jollimore) | Workforce-impact consultation. |
| Council's Gen. Govt. Committee | Formal report / presentation | At governance milestones | Sponsor (Jollimore) | Governance reporting on the AG response. |
| Auditor General (Toronto) | Status reporting | At governance milestones | Sponsor (Jollimore) | Evidence the AG recommendations are measured and acted on. |

---

## 6. Feedback Loops

Engagement is two-way: stakeholder input is captured, acted on, and reflected back so the analytics stay grounded in operational reality rather than asserted from the data alone. The primary loops are: **SME validation cycles** on the KPI / class targets and the 34-unit disposal screening list, run in the bi-weekly workshops (§5), with each validated decision recorded against its RACI owner (§3); **client-division confirmation** of vehicle-need assumptions, which feeds the underutilization reading and is surfaced for SME review where divisions disagree; and **dashboard iteration** against [`report_spec.md`](report_spec.md), where stakeholders react to the live pages (availability vs target, the exception list, the underutilization views) and changes are folded back into the spec. Data-trust feedback — the 6 unmatched `UNIT_NO` rows and the 209 excluded nulls — is routed to the Fleet IT / Telematics lead and logged as stated assumptions (§8) rather than silently resolved. The sales-vs-redemption interpretation for the ferry data is explicitly **flagged for SME validation** and carried as an open feedback item until confirmed.

---

## 7. Risks

The risks below are engagement and political risks specific to this initiative — the ways stakeholder dynamics, not the code, could undermine a defensible result. Each carries a likelihood, an impact, and a mitigation tied to the engagement approach above.

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Workforce / union reaction to right-sizing perceived as job cuts | Medium | High | Consult the ATU early (§4/§5) before any right-sizing decision; frame the 34-unit list as an SME screening list, not a disposal decision. |
| SME availability constrains target / screening-list validation | Medium | High | Lock bi-weekly SME workshops (§5); keep the screening list short (34 units) and pre-packaged for efficient review. |
| Data-trust erosion from the 6 unmatched `UNIT_NO` rows and 209 excluded nulls | Medium | Medium | Document both as DQ findings ([DQ report](dq_report.md) §2, §7); route to Fleet IT / Telematics; carry as stated assumptions (§8) rather than hide them. |
| The **5.8%** computed underutilization vs **~14%** audit benchmark misread as failure | Medium | High | Brief stakeholders that the gap is a period / right-sizing **insight, not an error** ([`kpi_definitions.md`](kpi_definitions.md) §A-Reconciliation; [DQ report](dq_report.md) §5); the ~14% is cited (AG 2019.AU2.3), not recomputed. |
| Governance reporting drifts from the May 2023 FSD framing | Low | Medium | Anchor Committee/AG communication on the AG themes and the May 2023 report vocabulary; keep Accountable singular (Sponsor). |

---

## 8. Stated Assumptions

Consistent with the data-quality discipline ([DQ report](dq_report.md) §6), every engagement-relevant assumption is recorded before it is relied on, with an explicit disposition. This keeps the role-based stakeholder specifics honest (they are illustrative, not sourced) and echoes the locked data-fidelity caveats so the document stays defensible.

| ID | Caveat | Disposition |
|----|--------|-------------|
| **A2** | Role-based stakeholder specifics — the **ATU local numbers (113 / 416)** and the **PMMD** acronym — are illustrative role-based labels, not sourced facts. | **Stated assumption** — present as role-based; confirm exact locals / division naming with the stakeholder. |
| **A1** | Fine-grained **BABOK Guide v3** task labels are mapped to their knowledge area where the exact task name is uncertain. | **Stated assumption** — knowledge area cited where the task label is uncertain (see §9) [3]. |
| **A3** | The **"Open Government Licence – Toronto"** name is reused verbatim from the source deliverables, not re-derived. | **Cited** — see §10. |
| **DQ-1** | Availability rates exclude the **209 NULL** `AVAILABILITY_YTD` values (denominator **4,405**), never imputed. | **Cited** data-fidelity rule ([DQ report](dq_report.md) §2). |
| **DQ-2** | **6 unmatched** utilization `UNIT_NO` rows fall outside `fact_vehicle` by design. | **Flagged for SME / Fleet IT** ([DQ report](dq_report.md) §7). |
| **DQ-3** | The **sales-vs-redemption** interpretation for the ferry data is an assumption. | **Flagged for SME validation** ([DQ report](dq_report.md) §3, A3). |

---

## 9. BABOK Guide v3 Traceability

This document's stakeholder-analysis content maps to **BABOK Guide v3** practice; the mapping lives here in a single table rather than as section headings, so the framework fluency is explicit without dressing the prose in knowledge-area labels. Where a fine-grained task label is uncertain, the **knowledge area** is referenced (A1). All framework claims cite **BABOK Guide v3 / IIBA** [3].

| This document's section | BABOK v3 Knowledge Area | BABOK v3 Task / Technique |
|-------------------------|-------------------------|---------------------------|
| §1 Stakeholder Register; §2 Power/Interest Grid | Business Analysis Planning & Monitoring | Stakeholder List, Map, or Personas. |
| §3 RACI Matrix | Business Analysis Planning & Monitoring | Roles & Responsibilities Matrix (RACI). |
| §4 Engagement Approach; §6 Feedback Loops | Elicitation & Collaboration | Manage Stakeholder Collaboration (knowledge area where task label uncertain — A1). |
| §5 Communication Plan | Business Analysis Planning & Monitoring | Plan Business Analysis Information Management / communication (knowledge area where task label uncertain — A1). |
| §7 Risks | Strategy Analysis | Assess Risks. |
| §8 Stated Assumptions | Strategy Analysis | Assumptions and constraints documentation (knowledge area where task label uncertain — A1). |

---

## 10. Sources & Licence

1. Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** — vehicle downtime ("Lengthy Downtime Requires Immediate Attention") and underutilization ("Stronger Corporate Oversight Needed for Underutilized Vehicles") themes; the ~14% underutilization benchmark.
2. **May 2023 FSD** report to the City of Toronto's **General Government Committee** — source of the three named stakeholders (David Jollimore, Vukadin Lalovic, Miguel Lamsaki) and the governance body of record.
3. **BABOK Guide v3** (IIBA, *A Guide to the Business Analysis Body of Knowledge*) — stakeholder-analysis tasks and techniques (Stakeholder List/Map/Personas; Roles & Responsibilities / RACI).
4. City of Toronto **Open Data** portal — the three source datasets underlying the cited KPI figures.
- Licence: **Open Government Licence – Toronto**.

*Stakeholder names are sourced from the May 2023 FSD report; every other stakeholder is a role/title only. Quantitative figures are transcribed verbatim from the Phase-3 KPI snapshot (`data/kpi/kpi_values.json`, locked by `tests/test_kpis.py`) and the [DQ report](dq_report.md); audit benchmarks are cited, never recalculated.*
