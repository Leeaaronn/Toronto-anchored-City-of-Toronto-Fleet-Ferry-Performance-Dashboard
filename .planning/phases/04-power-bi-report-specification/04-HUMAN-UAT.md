---
status: partial
phase: 04-power-bi-report-specification
source: [04-VERIFICATION.md]
started: "2026-06-04T00:00:00Z"
updated: "2026-06-04T00:00:00Z"
---

## Current Test

[awaiting human testing in Power BI Desktop — these are manual canvas-authoring steps outside the GSD data-engineering scope]

## Tests

### 1. Civic theme JSON renders correctly
expected: Importing the D-01 theme JSON block produces the City of Toronto navy base (#003F87) with the locked status semantics (red = below target, green = at/above target). Accessibility note holds.
result: [pending]

### 2. R1 date relationship + 2020 COVID dip
expected: After adding the Power Query derived date column, wiring the R1 relationship, and Mark-as-Date-Table on `date_key`, the Ferry YoY line chart reproduces the 2019→2020 COVID dip of −0.7067 (1,249,725 → 366,606).
result: [pending]

### 3. USERELATIONSHIP division role-playing
expected: Wiring R3 (owner, active) + R4 (using, inactive via USERELATIONSHIP) against the single conformed `dim_division` yields A4 by-using-division values matching `underutilization_by_division.csv`, with the synced division slicer still functioning across pages.
result: [pending]

### 4. CR-02 filter-context-safe DAX (multi-context)
expected: The fixed `Class Target = AVERAGEX(VALUES(fact_vehicle[UNIT_TYPE]), RELATED(dim_class_target[target]))` and `Gap to Target` are non-BLANK on a Page-3 summary card (all classes in scope) and produce correct signed gaps on the A2 by-class bar chart.
result: [pending]

### 5. Page 3 AG-themes-first layout
expected: On the Summary/Insights page the read order matches D-02 (downtime → underutilization 5.8% vs ~14% → 34-unit disposal screening list → ferry demand), and the disposal screen is visually prominent and labeled "screening list for SME review, never a disposal decision."
result: [pending]

### 6. PDF export three-page landscape
expected: PDF export produces three 16:9 landscape fit-to-page pages with grayscale legibility per the D-08 layout.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
