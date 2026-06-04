---
phase: 03-kpi-layer-measures-spec
plan: 03
subsystem: deliverables
tags: [docs, kpi, dax, measures-spec, audit-benchmark, traceability, power-bi-handoff]

# Dependency graph
requires:
  - phase: 03-kpi-layer-measures-spec
    plan: 01
    provides: "Committed falsifiable ground-truth snapshot data/kpi/kpi_values.json + 7 per-table CSVs — the source of every cited number"
provides:
  - "deliverables/kpi_definitions.md — panel-ready plain-language KPI formulas, audit benchmarks, 5.8%-vs-~14% reconciliation, KPI<->AG-theme traceability (AU2.2/AU2.3)"
  - "deliverables/measures_spec.md — Phase-4 build contract: domain->KPI tables pairing copy-paste DAX with snapshot-sourced SQL validation values"
affects: [04-powerbi-report-spec, 05-narrative-deliverables]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deliverable docs mirror dq_report.md header block + computed-vs-cited inline flagging + Sources & Licence footer"
    - "measures_spec.md table-per-KPI (Measure name | DAX | SQL validation value | Notes); every validation value transcribed verbatim from the committed snapshot"

key-files:
  created:
    - "deliverables/kpi_definitions.md"
    - "deliverables/measures_spec.md"
  modified: []

key-decisions:
  - "Every numeric KPI value transcribed verbatim from data/kpi/kpi_values.json / per-table CSVs (no recompute/estimate) — docs inherit the snapshot-as-contract guarantee (T-03-07 mitigation)"
  - "measures_spec.md ships DAX as a TEXT build contract only — explicit scope-split note: no .pbix/PBIP/TMDL; Power BI canvas authored manually in Phase 4"
  - "Overall availability DAX written as pooled grand-total DIVIDE(SUM, COUNTROWS non-null), explicitly noted NOT AVERAGEX-over-class-means; mean-of-class-means shipped as a guard-only measure"
  - "Disposal-candidate measure (34 units) framed as an SME screening list in both docs, never a disposal decision (D-02)"

requirements-completed: [KPI-02]

# Metrics
duration: 6min
completed: 2026-06-04
---

# Phase 3 Plan 03: KPI Definitions & DAX Measures Spec Summary

**Two panel-ready Phase-3 deliverable docs that turn the committed KPI snapshot into (1) a plain-language KPI definitions doc with audit benchmarks, the 5.8%-vs-~14% reconciliation, and KPI<->AG-theme traceability, and (2) a Phase-4 DAX build contract pairing every measure with its snapshot-sourced SQL validation value — every number transcribed verbatim from data/kpi/, never recomputed.**

## Performance

- **Duration:** 6 min
- **Tasks:** 2
- **Files modified:** 2 created

## Accomplishments
- Authored `deliverables/kpi_definitions.md` mirroring `dq_report.md`'s header block + computed-vs-cited inline flagging: numbered Domain A (overall pooled availability with the 4,405 non-null denominator / 209-NULL exclusion stated; availability-by-class vs audit targets 95/92/85/88/90 with signed gap-to-target; 1,734-unit exception list; underutilization 5.8% overall/by-division; 34-unit disposal SME screening list) and Domain B (ferry lifetime totals, complete-years 2016-2025 YoY with the 2020<2019 COVID dip, seasonality, DoW×hour heatmap, signed sales-redemption gap, distribution max 7,229/median 12) sections, the 5.8%-vs-~14% reconciliation cross-referencing dq_report.md §5, a KPI<->AG-theme traceability table (AU2.2 downtime / AU2.3 underutilization), and the Sources & Licence footer.
- Authored `deliverables/measures_spec.md` mirroring `data_dictionary.md`'s table-per-section layout: a Fleet Maintenance (Domain A) and a Ferry Operations (Domain B) section, each KPI a `Measure name | DAX | SQL validation value | Notes` subsection table. Every SQL validation value transcribes a snapshot value (overall availability 0.8899; per-class rates/targets/gaps; underutilization 5.8%; ferry 7,229/12; lifetime 13,257,804/13,076,317; 2019/2020 sales). The overall availability DAX is the pooled grand-total `DIVIDE(SUM, COUNTROWS non-null)` form, noted as NOT average-of-averages; the disposal-candidate Notes frame it as an SME screening list; a scope-split note states the spec is text-only (no `.pbix`/PBIP/TMDL).
- Both verify commands pass; both docs exceed the 60-line minimum and carry the required figures, AG themes, and Sources footer.

## Ground-Truth Values Cited (all verbatim from data/kpi/)
- overall_availability_rate **0.8899** (pooled, 4,405 non-null, 209 excluded); mean_of_class_means **0.8786** (guard-only)
- by-class rate/target/signed-gap: Light 0.9149/95/-0.0351, Medium 0.8612/92/-0.0588, Heavy 0.7948/85/-0.0552, Off-Road 0.8882/88/+0.0082, Other 0.9337/90/+0.0337
- exception_list **1,734** below-target; **34** disposal candidates
- overall_underutilization_rate **0.0572 ≈ 5.8%** over **2,080** matched light-duty; reconciled against cited **~14%** (AG 2019.AU2.3)
- ferry lifetime sales/redemptions **13,257,804 / 13,076,317**; max **7,229** / median **12**; 2019 **1,249,725** vs 2020 **366,606** (COVID dip)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write deliverables/kpi_definitions.md** - `538c9ea` (docs)
2. **Task 2: Write deliverables/measures_spec.md** - `e331f18` (docs)

## Files Created/Modified
- `deliverables/kpi_definitions.md` - Plain-language KPI formulas + audit benchmarks + 5.8%-vs-~14% reconciliation + AG-theme traceability + Sources footer (panel/BA audience).
- `deliverables/measures_spec.md` - Domain->KPI DAX + snapshot-sourced SQL validation value + notes tables; the Phase-4 build contract.

## Decisions Made
- Every numeric value transcribed verbatim from the committed snapshot (no recompute) so the docs inherit Plan 02's snapshot-as-contract test guarantee (T-03-07 mitigation).
- DAX shipped as a text build contract only; explicit scope-split note honors the GSD-owns-data-layer-only boundary (no `.pbix`/PBIP/TMDL).
- Overall availability DAX is the pooled grand-total `DIVIDE` form, with mean-of-class-means shipped as a guard-only measure to demonstrate pooled != average-of-averages.
- Disposal-candidate (34 units) framed as an SME screening list in both docs, never a decision (D-02).

## Deviations from Plan

None — plan executed exactly as written. Both tasks authored docs only; no `src/` or `tests/` files were touched, honoring the docs-only scope constraint.

## Threat Flags

None — both docs transcribe internal committed aggregates and audit-cited benchmarks only (no PII/secrets, no new network/auth/file surface). T-03-07 (doc values drifting from snapshot) is mitigated by verbatim transcription from the single-source-of-truth snapshot.

## Known Stubs
None — every cited figure resolves to a concrete value in `data/kpi/kpi_values.json` or a per-table CSV; no placeholder/empty/"coming soon" values appear in either doc.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `measures_spec.md` is the Phase-4 build contract: every page's DAX measure carries its SQL validation value, so the Power BI build is falsifiable against ground truth.
- `kpi_definitions.md`'s KPI<->AG-theme traceability and the 5.8%-vs-~14% reconciliation feed the Phase-5 narrative deliverables.
- No blockers.

## Self-Check: PASSED
- FOUND: deliverables/kpi_definitions.md
- FOUND: deliverables/measures_spec.md
- FOUND commits: 538c9ea, e331f18

---
*Phase: 03-kpi-layer-measures-spec*
*Completed: 2026-06-04*
