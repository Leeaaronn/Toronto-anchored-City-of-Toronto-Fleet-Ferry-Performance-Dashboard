# Phase 4: Power BI Report Specification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 04-power-bi-report-specification
**Areas discussed:** Theme & visual identity, Summary page narrative, Class-target table & schema fit, Slicers & interactivity

---

## Theme & visual identity

| Option | Description | Selected |
|--------|-------------|----------|
| City of Toronto civic | Navy/blue civic palette (~#003F87) + accessible accents; red=below / green=at-or-above target | ✓ |
| Neutral executive | Grayscale base + single blue accent; understated, data-forward | |
| Accessibility-first | Colorblind-safe Okabe-Ito, WCAG-AA, patterns not just color | |

**User's choice:** City of Toronto civic (Recommended)
**Notes:** Status semantics locked (red = below class target, green = at/above). Accessibility check folded in as a guardrail (pair color with sign/position) without switching to the full Okabe-Ito option.

---

## Summary page narrative

| Option | Description | Selected |
|--------|-------------|----------|
| AG-themes-first | Lead with downtime (gap-to-target) → underutilization (5.8% vs ~14%) → 34-unit disposal screen → ferry last | ✓ |
| Value-add-first | Lead with availability⋈utilization disposal screen, then AG themes, then ferry | |
| Exec scorecard | Top row 4 KPI cards + one signature chart per domain | |

**User's choice:** AG-themes-first (Recommended)
**Notes:** Disposal screen still featured prominently as the cross-dataset differentiator; framed as an SME screening list, not a disposal decision.

---

## Class-target table & schema fit

| Option | Description | Selected |
|--------|-------------|----------|
| Committed CSV dim | Add data/gold/dim_class_target.csv as a real dimension (single-direction to fact_vehicle) + correct measures_spec column refs | ✓ |
| Manual Enter-Data table | Power BI "Enter Data" table with the 5 rows + a corrected column-reference appendix; no repo artifact | |

**User's choice:** Committed CSV dim (Recommended)
**Notes:** Keeps the audit target line reproducible/falsifiable (pytest guard on the 5 rows), consistent with the Phase-3 committed-snapshot philosophy. Mandatory column-reference reconciliation against actual Gold names (dim_time[hour], dim_date[date_key], etc.).

---

## Slicers & interactivity

| Option | Description | Selected |
|--------|-------------|----------|
| Synced core + page-specific | Division/Asset Class/Year synced all pages; ferry adds Season/Daypart; cross-highlight default | ✓ |
| Per-page independent | Each page owns slicers, no sync; full cross-filter | |
| Minimal for clean demo | One synced Division slicer only; rest static | |

**User's choice:** Synced core + page-specific (Recommended)
**Notes:** Cross-highlight (not full cross-filter) keeps context visible during live panel drill.

## Claude's Discretion

- **Visual types per page** — defaults set in CONTEXT D-07 (KPI cards, bullet/bar-with-target for availability, sorted matrix for exception/disposal lists, line for ferry YoY, conditional-formatted matrix for the DoW×hour heatmap, signed bar for sales-redemption gap). Planner may refine.
- **PDF export layout** — three 16:9 landscape pages, fit-to-page (CONTEXT D-08).
- **Exact relationship cardinality / active-vs-inactive** for role-playing division (owner vs using) — spec to finalize and document (CONTEXT D-05).

## Deferred Ideas

- Narrative deliverables (requirements-gathering approach, stakeholder-engagement strategy) → Phase 5.
- Actual `.pbix` authoring → manual by user, out of GSD scope.
- Optional ferry visuals (avg daily volume by season, peak-day identification) → planner discretion on the Ferry page if they strengthen the staffing story.
