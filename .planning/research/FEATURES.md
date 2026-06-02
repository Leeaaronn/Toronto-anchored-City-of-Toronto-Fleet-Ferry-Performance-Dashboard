# Feature Research

**Domain:** Public-sector fleet-maintenance + ferry-operations analytics deliverable (audit-driven BA assignment: KPIs/measures, Power BI dashboard content, and two BA narrative deliverables)
**Researched:** 2026-06-01
**Confidence:** HIGH for KPI/measure landscape and BA narrative conventions (grounded in the brief's own profiled schemas + audit benchmarks, BABOK/IIBA stakeholder & elicitation conventions, and fleet-KPI industry sources); MEDIUM for exact AG recommendation wording (cited from brief, not re-verified against the primary AG PDF)

> **How to read this file.** "Features" here = analytical measures/KPIs, dashboard content, and the structural elements of the two narrative deliverables. Categories map directly to grading risk: **Table Stakes** = omit and the deliverable looks weak or fails the 70% bar; **Differentiators** = the value-added measures graders reward (especially the availability⋈utilization join most candidates miss); **Anti-Features** = things to deliberately NOT build because they undermine defensibility. Every KPI ties back to one of the two AG themes — **vehicle downtime (2019.AU2.2)** and **underutilization (2019.AU2.3)** — or to the ferry operations domain.

## Feature Landscape

### Table Stakes (Graders / Domain Experts Expect These)

Omit any of these and the deliverable reads as incomplete for a fleet/transit analytics engagement. These are the conventional fleet-KPI set (availability, utilization, fleet age) plus the ferry time-series basics.

| Feature / Measure | Why Expected | AG Theme | Complexity | Notes |
|---|---|---|---|---|
| **Overall fleet availability rate** (mean `AVAILABILITY_YTD`, nulls excluded) | The headline "north star" fleet KPI; availability/uptime is the #1 industry metric | Downtime (AU2.2) | LOW | Single aggregate; state n and excluded-null count alongside |
| **Availability by asset class vs. target + gap-to-target** (flagship) | Audit published per-class targets (LD 95 / MD 92 / HD 85 / Off-Road 88 / Other 90); comparing actual-to-target is the core audit expectation | Downtime (AU2.2) | MEDIUM | Validate your computed actuals against the audit's 2022 actuals (91/83/76/84/94) as a sanity check, not a match — different period. Gap = actual − target |
| **% of vehicles below an availability threshold + exception list of critically low / near-0% units** (drill-through) | Auditors think in exceptions; "lengthy downtime requires immediate attention" is literally the AU2.2 title | Downtime (AU2.2) | MEDIUM | Choose a defensible threshold (e.g. below class target, or below a fixed % like 70). Exception list = drill-through detail page |
| **Availability by owner division** | Shows where downtime concentrates; supports corporate-oversight narrative | Downtime (AU2.2) | LOW | 21 divisions; use `OWNER_DIVISION` |
| **Fleet age** (derived from model `YEAR` / `IN_SERV_DT`) | Standard fleet KPI; underpins replacement/right-sizing discussion | Both | LOW | Decide YEAR vs IN_SERV_DT; state choice. Watch YEAR=2026 future-dated rows |
| **Underutilization rate overall + by using division** (flag divisions above fleet avg) | Directly operationalizes AU2.3 "stronger corporate oversight for underutilized vehicles" | Underutilization (AU2.3) | LOW | `REF_USING_DIV`; the 5.8% headline must appear with the 14%-audit context |
| **Specialized vs. non-specialized underutilization split** | Specialized units legitimately sit idle; splitting prevents false-positive disposal flags | Underutilization (AU2.3) | LOW | `Specialized units` Yes/No; important nuance graders look for |
| **Ferry total tickets sold & redeemed** (lifetime + period) | Baseline volume measure for the time-series domain | Ferry | LOW | Cards; lifetime + selected period |
| **Ferry YoY annual volume trend + growth rate** (call out 2020–21 COVID dip) | Trend is table stakes for any time series; explicitly naming the dip shows analytical literacy | Ferry | LOW | Line chart; annotate the dip rather than letting it look like a data error |
| **Ferry seasonality** (monthly + seasonal demand profile, summer peak) | Toronto Island Ferry is overwhelmingly seasonal; a profile without seasonality is missing the point | Ferry | MEDIUM | Needs `dim_date` season; the median-12 / max-7,229 skew is the story |
| **Avg daily volume by season + peak-day identification** | Operational planning baseline | Ferry | LOW | Builds on `dim_date` |
| **Power BI dashboard with KPI cards + target indicators** | Deliverable #3 explicitly requires KPIs, trends, exceptions, insights; industry convention is 4 "north star" KPIs large at top, 4–6 supporting below | Both | MEDIUM | Avoid the 30-KPIs-equal-weight anti-pattern (dashboard fatigue) |
| **PDF export of the dashboard** | Explicitly a required artifact | — | LOW | Layout must survive export (no clipped visuals) |
| **Stated assumptions + data-quality disclosures** | Defensibility for a panel interview; audit-grade work names its gaps | Both | LOW | 209 nulls excluded, retired-dataset pull date, Sales=sold/Redemption=boarded, 5.8% vs 14% |

### Differentiators (The Value-Added Measures Graders Reward)

These separate a pass from a strong pass. The first is explicitly called out in the brief as "the value-added measurement most candidates miss."

| Feature / Measure | Value Proposition | AG Theme | Complexity | Notes |
|---|---|---|---|---|
| **Availability ⋈ Utilization disposal-candidate cross-measure** (vehicles that are BOTH low-availability AND underutilized) | THE flagship differentiator. Most candidates analyze the two datasets separately; joining them on `UNIT_NO` and isolating the low-availability ∩ underutilized quadrant directly produces the audit's right-sizing story (143 assets removed, ~$411K/yr maintenance saved). Ties both AG themes together in one measure | **Both** (AU2.2 + AU2.3) | HIGH | Depends on the normalized-`UNIT_NO` join (2,080/2,086). Present as a 2×2 quadrant or a ranked candidate list. Exclude specialized units from disposal flags to avoid false positives |
| **Availability of underutilized vs. not-underutilized vehicles** (comparative) | Tests whether underutilized vehicles also have worse availability — quantifies the "double-cost" asset population that is the strongest disposal argument | Both | MEDIUM | The analytical bridge to the disposal-candidate list; a single comparative bar makes the case |
| **Availability-vs-age trend** (availability by fleet-age band / scatter) | Connects aging fleet to downtime — supports a fleet-renewal recommendation, an industry-standard fleet-age analysis | Downtime (AU2.2) | MEDIUM | Age banding on derived fleet_age; watch sparse old-vehicle bins |
| **Ferry sales-to-redemption gap over time** | Surfaces advance-sales / no-show / timing-lag behavior — a non-obvious operational insight from an otherwise plain ticket count | Ferry | MEDIUM | Derived `gap = sales − redemption`; trend it; caveat the Sales/Redemption interpretation assumption |
| **Ferry day-of-week × hour-of-day demand heatmap** (identify peak 15-min windows) | Converts raw counts into a staffing/scheduling recommendation — the actionable insight that elevates the ferry page from descriptive to prescriptive | Ferry | MEDIUM | Needs `dim_time` (hour, 15-min slot, daypart) + `dim_date` day-of-week; the 15-min grain is what makes peak-window detection possible |
| **Insights / recommendations landing page** (disposal candidates; ferry peak-staffing windows) | Synthesizes findings into management recommendations — what the assignment actually asks for ("summarize findings + recommendations for management") and what the 10-min panel presentation will lead with | Both | MEDIUM | Tie each recommendation to its AG theme + supporting visual |
| **Underutilization period-reconciliation insight** (5.8% now vs ~14% audit Mar 2023) | Reframes an apparent discrepancy as evidence of fleet right-sizing since the audit — shows analytical maturity rather than glossing over a mismatch | Underutilization (AU2.3) | LOW | A narrative callout, not a chart; strong panel-interview talking point |

### Anti-Features (Do NOT Build — They Undermine Defensibility)

These are tempting but reduce credibility for an audit-grounded, panel-defended deliverable. Each is already a Key Decision in PROJECT.md — this section documents *why* so they are not re-added.

| Anti-Feature | Why It's Tempting | Why Problematic | Do This Instead |
|---|---|---|---|
| **Imputing the 209 null `AVAILABILITY_YTD` values** | Cleaner-looking 100%-complete dataset; no "missing" caveat | Imputed values distort audit-benchmarked rates and are indefensible at a panel ("where did that number come from?") | Exclude from rate calcs, report n and the 4.5% gap as a DQ finding |
| **Recomputing the underutilization classification** (km / engine-hour thresholds) | "Show your work" by re-deriving the under-5,000km / 125-engine-hour / 3-days-week rule | The source telematics/odometer data is NOT in the supplied files — any recomputation is fabricated | Use the pre-applied `Utilization` flag; cite the audit definition as the documented threshold |
| **Fabricating or simulating telematics / mileage data** | Enables a richer "true utilization" measure | Inventing data is disqualifying in an audit context | Scope utilization analysis to the binary flag that exists; note the limitation |
| **Joining the ferry dataset into the fleet star schema** | "One unified model" looks sophisticated | Ferry is a separate domain at a different grain (15-min time series, no `UNIT_NO`); forcing a join creates a meaningless cross product | Keep ferry standalone (`fact_ferry` + `dim_date` + `dim_time`); two domains, two report pages |
| **Treating the retired availability dataset as live/current** | Simpler narrative | Portal lists it Retired — claiming currency is inaccurate | State it is a point-in-time snapshot with the pull date |
| **30+ KPIs with equal visual weight on one page** | "Comprehensive" | Dashboard fatigue; forces the viewer to prioritize; hides the story | 4 north-star KPIs large at top, 4–6 supporting below, exceptions on drill-through |
| **Generating the `.pbix` / PBIP / TMDL** | Full automation | Out of scope by explicit decision; brittle and low-value; user authors the canvas | Deliver clean modeled tables + KPI definitions doc + DAX-ready measures spec + page-by-page report spec |
| **Recasting `UNIT_NO` join leniently to force 2,086/2,086** | "Perfect" match rate | Hides 6 genuinely-unmatched records; over-fitting the join misrepresents data | Normalize (strip leading zeros / cast), accept 2,080/2,086, report the 6 unmatched as a DQ note |

## Narrative Deliverables — Expected Sections

The two narrative deliverables are graded on whether they read like real public-sector BA artifacts. Both should be explicitly grounded in the AG audit + the May 2023 FSD report and use recognized BABOK/IIBA structure. Conventions below are grounded in BABOK knowledge areas (Plan Business Analysis Approach; Prepare for / Conduct / Confirm Elicitation; Plan Stakeholder Engagement; Manage Stakeholder Collaboration) and standard stakeholder-engagement practice (power/interest grid, RACI, communication plan).

### Deliverable 1 — Requirements-Gathering Approach (expected elements)

| Section | What It Contains | Confidence |
|---|---|---|
| **Objective & business context** | Frame the engagement against the AG themes (downtime AU2.2, underutilization AU2.3) and the FSD mandate; this is the "why" | HIGH |
| **Stakeholder identification** | Sponsor (GM Fleet Services), SMEs (Directors — Asset Management, Maintenance), consumers (client divisions), oversight (Auditor General) — who you would gather requirements from | HIGH |
| **Elicitation techniques (with rationale)** | Map techniques to this engagement: **document analysis** (AG report, May 2023 FSD report, open-data dictionaries — the primary technique given a data-led assignment), **interviews** (Directors/SMEs for KPI definitions & targets), **workshops** (KPI prioritization), **observation/data profiling** (the actual CSV profiling as a form of elicitation) | HIGH |
| **Requirements types captured** | Business requirements (reduce downtime, improve oversight), stakeholder requirements (per division), and the functional/data requirements that became KPIs (the measures in this file) | HIGH |
| **Process / sequence** | Prepare → Conduct → Confirm; how high-level needs (early interviews/document analysis) were refined into specific KPI definitions and validated against audit benchmarks | HIGH |
| **Traceability** | Each KPI traced back to an AG theme or stakeholder need — the through-line graders look for | HIGH |
| **Assumptions & constraints** | The stated data assumptions (nulls excluded, classification pre-applied, retired snapshot) as requirements-stage constraints | HIGH |

### Deliverable 2 — Stakeholder Engagement Strategy (expected elements)

| Section | What It Contains | Confidence |
|---|---|---|
| **Stakeholder register / analysis** | List the real named stakeholders with role, interest, and influence | HIGH |
| **Power/Interest grid** | Classify: GM Fleet Services = high power / high interest (manage closely, key player); Directors/SMEs = high interest (consult, keep informed); Auditor General = high power, satisfaction-focused (keep satisfied); client divisions = keep informed | HIGH |
| **RACI matrix** | Who is Responsible / Accountable / Consulted / Informed across the analytics activities — e.g. GM accountable for outcomes, Directors consulted on KPI definitions, divisions informed of findings | HIGH |
| **Engagement approach per group** | Tailored cadence/format: close engagement for the sponsor, consultative for SMEs, periodic summaries for low-influence consumers, formal/satisfaction for oversight | HIGH |
| **Communication plan** | What is communicated, to whom, how often, in what channel/format (e.g. dashboard walkthroughs, the PDF export, the 10-min panel presentation) | HIGH |
| **Collaboration & feedback loops** | How KPI definitions and findings get validated with SMEs; how disagreements (e.g. 5.8% vs 14%) are surfaced and resolved | MEDIUM |
| **Risks / engagement challenges** | E.g. data limitations affecting trust, retired-dataset caveats, getting time from busy Directors | MEDIUM |

## Feature Dependencies

```
fact_vehicle (enriched: asset_class, age, seasonal/specialized flags, status)
    └──requires──> normalized UNIT_NO + 209-null handling + derived fleet_age
            │
            ├──enables──> Availability by class vs target (flagship)
            ├──enables──> % below threshold + exception list
            ├──enables──> Availability-vs-age trend
            │
   Availability ⋈ Utilization join (2,080/2,086 on normalized UNIT_NO)
            └──enables──> Disposal-candidate cross-measure (DIFFERENTIATOR)
                    └──enables──> Insights / recommendations landing page

fact_ferry (sales, redemption, gap) + dim_date + dim_time
    └──requires──> timestamp parse + season/daypart/day-of-week/is_weekend derivation
            │
            ├──enables──> YoY trend + seasonality + avg-daily-by-season
            ├──enables──> Sales-to-redemption gap trend (DIFFERENTIATOR)
            └──enables──> Day-of-week × hour-of-day heatmap (DIFFERENTIATOR)

Stakeholder analysis (register + power/interest)
    └──feeds──> Stakeholder Engagement Strategy (RACI, comms plan)
    └──feeds──> Requirements-Gathering Approach (elicitation targets)

All KPIs ──feed──> KPI definitions doc + DAX-ready measures spec ──feed──> page-by-page report spec ──feed──> Power BI canvas (authored manually) ──feed──> PDF export
```

### Dependency Notes

- **Disposal-candidate measure requires the join, which requires UNIT_NO normalization** — the single highest-value differentiator sits at the end of a dependency chain; if the join is wrong, the flagship insight collapses. Prioritize join-integrity tests.
- **Every ferry differentiator requires `dim_time` at 15-min grain** — the heatmap and peak-window detection are impossible without the time dimension; this is why the 15-min grain is preserved rather than aggregated early.
- **Narrative deliverables depend on stakeholder analysis, not on the data pipeline** — they can be drafted in parallel with ETL, but their *credibility* improves when they reference the actual KPIs produced (traceability).
- **The report spec is the contract** between the GSD-owned data layer and the manually-authored Power BI canvas — KPIs without a DAX-ready spec are not deliverable to the user.

## MVP Definition

### Launch With (the gradeable core)

- [ ] Overall availability + availability-by-class-vs-target + gap-to-target — flagship table-stakes KPI
- [ ] Underutilization rate overall + by division + specialized split — covers AU2.3
- [ ] **Disposal-candidate cross-measure (availability ⋈ utilization)** — the differentiator that separates pass from strong pass
- [ ] Exception list of critically low-availability units — covers AU2.2's "immediate attention" framing
- [ ] Ferry: YoY trend, seasonality, sales-to-redemption gap, day×hour heatmap
- [ ] KPI definitions doc + DAX-ready measures spec + page-by-page report spec
- [ ] Stated assumptions / DQ disclosures
- [ ] Both narrative deliverables (full drafts)
- [ ] Power BI dashboard + PDF export

### Add After Core (polish that raises the grade)

- [ ] Availability-vs-age trend — strong supporting differentiator
- [ ] Insights/recommendations landing page with tied-back recommendations — anchors the panel presentation
- [ ] Underutilization 5.8%-vs-14% reconciliation callout

### Out of Scope (defer / never)

- [ ] Any recomputation of utilization thresholds (no source data) — never
- [ ] `.pbix` / PBIP / TMDL generation — never (explicit decision)
- [ ] Predictive / forecasting models on ferry demand — defer; not asked for, adds risk without grading reward

## Feature Prioritization Matrix

| Feature | User/Grader Value | Implementation Cost | Priority |
|---|---|---|---|
| Availability by class vs target + gap | HIGH | MEDIUM | P1 |
| Disposal-candidate cross-measure (join) | HIGH | HIGH | P1 |
| Underutilization rate + division + specialized split | HIGH | LOW | P1 |
| Exception list of low-availability units | HIGH | MEDIUM | P1 |
| Ferry seasonality + YoY trend | HIGH | MEDIUM | P1 |
| Ferry day×hour heatmap | HIGH | MEDIUM | P1 |
| Both narrative deliverables | HIGH | MEDIUM | P1 |
| Ferry sales-to-redemption gap | MEDIUM | MEDIUM | P2 |
| Availability-vs-age trend | MEDIUM | MEDIUM | P2 |
| Insights/recommendations landing page | HIGH | MEDIUM | P2 |
| Overall availability rate (single card) | MEDIUM | LOW | P2 |
| 5.8%-vs-14% reconciliation callout | MEDIUM | LOW | P2 |

**Priority key:** P1 = must have for a credible/passing submission; P2 = should have, raises the grade and strengthens the panel presentation; P3 = none recommended (everything else is anti-feature/out-of-scope).

## Sources

- `Fleet_Services_GSD_Project_Brief.md` and `.planning/PROJECT.md` — profiled schemas, KPI set, audit targets/benchmarks, stakeholders, join model (HIGH; primary authoritative project context)
- Auditor General Fleet Services Operational Review — 2019.AU2.2 (downtime), 2019.AU2.3 (underutilization); FSD report to General Government Committee, May 8 2023 — targets, thresholds, right-sizing figures (MEDIUM; cited via brief, not re-verified against primary PDF)
- [Fleet Management KPIs: 15 Metrics and Benchmarks (Opsima, 2026)](https://opsima.com/blog/kpis/fleet-management-kpis/) — availability/utilization/fleet-age conventions (MEDIUM)
- [Fleet Management KPIs (Geotab)](https://www.geotab.com/blog/fleet-management-kpis/) and [Fleet Analytics Dashboard real-time KPIs (Oxmaint)](https://oxmaint.com/industries/fleet-management/fleet-analytics-dashboard-real-time-kpis-2026) — dashboard "north star" design convention (MEDIUM)
- [Stakeholder Analysis | IIBA BABOK Extended](https://www.iiba.org/knowledgehub/babok-applied/stakeholder-analysis/) and [Engaging Stakeholders in Elicitation and Collaboration (IIBA)](https://www.iiba.org/professional-development/knowledge-centre/articles/engaging-stakeholders-in-elicitation-and-collaboration/) — BABOK knowledge areas, power/interest grid (HIGH)
- [Maximizing stakeholder engagement with the RACI matrix (Lucen)](https://www.lucensoftware.com/blog/raci-matrix) and [Stakeholder communication plan five-step guide (Finance Alliance)](https://www.financealliance.io/stakeholder-communication-plan/) — RACI + communication-plan conventions (MEDIUM)
- [9 Elicitation Techniques Used by Business Analysts (BusinessAnalystMentor)](https://businessanalystmentor.com/elicitation-technique/) and [Mastering Requirement Elicitation Techniques (The BA Guide)](https://thebaguide.com/blog/mastering-requirement-elicitation-techniques-for-business-analysts/) — interviews / document analysis / workshops / observation (MEDIUM)

---
*Feature research for: public-sector fleet + ferry analytics BA deliverable*
*Researched: 2026-06-01*
