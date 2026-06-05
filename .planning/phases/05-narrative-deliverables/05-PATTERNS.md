# Phase 5: Narrative Deliverables - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 2 new markdown deliverables
**Analogs found:** 2 / 2 (both map to the existing `deliverables/*.md` doc set)

> **Phase nature:** This is a documentation-authoring phase. There is no code, no role/data-flow taxonomy in the software sense, and no test wiring. The "patterns" here are the **house style** of the five committed `deliverables/*.md` files — heading/header structure, provenance discipline, citation/Sources footer, prose-then-table cadence, and AG-theme framing. The job is assembly and narrative framing of already-committed facts, not generation of new facts.

## File Classification

| New File | Role | "Data Flow" (content flow) | Closest Analog | Match Quality |
|----------|------|----------------------------|----------------|---------------|
| `deliverables/requirements_approach.md` (NARR-01) | narrative deliverable (BA methodology) | transform — read-only sources (KPI snapshot + existing docs + cited externals) → narrative prose + tables | `deliverables/kpi_definitions.md` (primary), `deliverables/dq_report.md` (assumptions/sources) | exact (same doc set, same house style) |
| `deliverables/stakeholder_engagement.md` (NARR-02) | narrative deliverable (stakeholder analysis) | transform — read-only sources (PROJECT.md roster + cited externals) → register/grid/RACI tables + prose | `deliverables/kpi_definitions.md` (header/footer), `deliverables/report_spec.md` (multi-table prose-then-table cadence) | exact (same doc set, same house style) |

**Why these analogs:** All five `deliverables/*.md` share one house style. `kpi_definitions.md` is the canonical clone target for the header block, provenance discipline, AG-theme traceability table, and Sources footer (RESEARCH §Architecture Patterns Pattern 1 lifts its header verbatim). `dq_report.md` is the model for an explicit stated-assumptions section (its §6 "Stated Caveats (Assumptions Log)"). `report_spec.md` is the model for documents that carry many prose-then-table artifacts in sequence (register/grid/RACI in NARR-02).

---

## Pattern Assignments

Both new files clone the **same five patterns** from the existing doc set. Each pattern below names the analog file, the exact line range, and the excerpt to copy.

### Pattern 1 — House-Style Header Block

**Apply to:** Top of BOTH files.
**Analog:** `deliverables/kpi_definitions.md` lines 1-10; identical structure in `dq_report.md` 1-16, `measures_spec.md` 1-8, `report_spec.md` 1-8, `data_dictionary.md` 1-12.

Structure: `# Title — … (REQ-ID)` → bold `**Project:**` / `**Scope:**` / `**Method:**` / `**Snapshot pull date:**` block → a `>` blockquote "Why this doc exists" paragraph (this is where the **locked AG-themes-first framing** lives) → `---`.

Excerpt to clone (`kpi_definitions.md` 1-10):
```markdown
# KPI Definitions — Phase 3 KPI Layer (KPI-02)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** Every Domain A (fleet maintenance) and Domain B (Toronto Island Ferry) KPI computed authoritatively over the Phase-2 Gold star schema (`data/gold/*.parquet`), cross-checked against audit benchmarks.
**Method:** All headline figures are computed deterministically by `src/fleet_analytics/kpis.py` ... Every number below is **transcribed from that snapshot, not re-estimated**; the snapshot is locked by `tests/test_kpis.py`. Audit benchmarks ... are **cited, never recalculated**.
**Snapshot pull date:** **2026-06-02** (the supplied availability file is a point-in-time YTD snapshot — see the [DQ report](dq_report.md), caveat A1).

> **Why this doc exists.** [opens with the AG downtime 2019.AU2.2 / underutilization 2019.AU2.3 framing] ...

---
```
Note the inter-doc relative links (`[DQ report](dq_report.md)`, `[`measures_spec.md`](measures_spec.md)`) — the new docs must cross-link the same way for vocabulary consistency (Phase 6 grades self-consistency).

### Pattern 2 — Provenance-Tagged Number Tables (`**Computed**` / `**Cited**`)

**Apply to:** Anywhere a number appears in either narrative.
**Analog:** `deliverables/kpi_definitions.md` lines 18-23 (Measure/Value/Source 3-col table) and lines 76-81 (the 5.8% vs ~14% reconciliation table); `dq_report.md` lines 86-89.

Every figure is tagged inline as **Computed** (traces to the committed snapshot) or **Cited** (external source). Excerpt (`kpi_definitions.md` 18-23):
```markdown
| Measure | Value | Source |
|---------|-------|--------|
| Overall availability rate (pooled) | **0.8899 ≈ 89.0%** | **Computed** — `AVG(AVAILABILITY_YTD)` over 4,405 non-null rows. |
| Non-null denominator | **4,405** | **Computed** — the 209 NULLs are excluded, never imputed. |
```
Bold the value; tag the provenance in the Source cell. In the narratives, attach a numbered `[n]` to every external/cited figure (D-05). The verbatim values to quote live in RESEARCH §Source-of-Truth Number Registry — copy, never recompute.

### Pattern 3 — Prose-then-Table (D-08)

**Apply to:** Every structured artifact — requirements-types table, BABOK traceability, stakeholder register, power/interest grid, RACI, communication plan, risks.
**Analog:** `deliverables/kpi_definitions.md` (every KPI: a "Plain-language formula." prose paragraph, then the table — see lines 16-23, 29-37); `report_spec.md` 12-36 shows the same cadence repeated across many sequential tables (the model for NARR-02's many-tables layout).

Pattern: one short prose paragraph stating *what the table is and why it matters*, immediately followed by the markdown table, optionally a one-line takeaway after. Excerpt (`kpi_definitions.md` 27-37):
```markdown
**Plain-language formula.** For each asset class, the **pooled availability rate** ... is compared to the **audit-cited class target**. ...

| Asset class | Pooled availability rate (computed) | Audit target (cited) | Signed gap-to-target (computed) | Below-target units (computed) |
|-------------|------------------------------------|----------------------|---------------------------------|-------------------------------|
| Light | **0.9149 ≈ 91.5%** | **95** | **−0.0351** | 877 of 2,101 |
```

### Pattern 4 — Stated-Assumptions / Caveats Section (locked: present in BOTH docs)

**Apply to:** A dedicated assumptions section in BOTH files (locked by roadmap; CONTEXT line 18).
**Analog:** `deliverables/dq_report.md` lines 107-114 ("## 6. Stated Caveats (Assumptions Log)") — an `ID | Caveat | Disposition` table, each row tagged Cited/Computed/flagged-for-SME.

Excerpt (`dq_report.md` 107-114):
```markdown
## 6. Stated Caveats (Assumptions Log)

| ID | Caveat | Disposition |
|----|--------|-------------|
| **A1** | The City Vehicle Availability dataset is listed **Retired** ... treated as a **point-in-time YTD snapshot** ... | **Cited**, not computed. ... |
| **A3** | The Sales-vs-Redemption interpretation for the ferry data is an assumption. | Flagged for **SME validation** (§3). |
```
For the narratives, this section captures: forward-looking elicitation (observation/surveys are planned, not performed — D-09 #4); role-based stakeholders flagged as illustrative not sourced (ATU local numbers, PMMD acronym — RESEARCH A2); BABOK fine-grained task labels (RESEARCH A1); Open Government Licence name (RESEARCH A3).

### Pattern 5 — Sources & Licence Footer (D-05 / D-06)

**Apply to:** End of BOTH files.
**Analog:** `deliverables/kpi_definitions.md` lines 154-161; identical footer in `dq_report.md` 189-197.

Excerpt (`kpi_definitions.md` 154-161):
```markdown
## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** (the ~14% underutilization benchmark and downtime themes).
- Licence: **Open Government Licence – Toronto**.

*KPI figures are computed by ... Audit thresholds are cited, never recalculated.*
```
The narratives ADD a methodology source — **BABOK Guide v3 / IIBA** (D-06) — and resolve every inline `[n]` here as a numbered list (D-05). Reuse the "Open Government Licence – Toronto" line verbatim (RESEARCH A3).

### Pattern 6 — AG-Theme Traceability Table (per-doc)

**Apply to:** NARR-01 as a "BABOK Guide v3 Traceability" table; both docs carry an AG-theme mapping.
**Analog:** `deliverables/kpi_definitions.md` lines 139-150 ("## KPI ↔ AG Theme Traceability") — a two/three-column mapping table preceded by a one-paragraph explanation.

Excerpt (`kpi_definitions.md` 139-150):
```markdown
## KPI ↔ AG Theme Traceability

Every KPI traces to an Auditor General Operational Review theme: **downtime/availability → 2019.AU2.2**; **underutilization → 2019.AU2.3**. ...

| KPI | Domain | AG Theme |
|-----|--------|----------|
| 1. Overall availability rate (pooled) | A | **AU2.2** (downtime / availability) |
```
NARR-01's BABOK traceability table (RESEARCH §Architecture Pattern 4) uses this exact shape: a `This document's section | BABOK v3 Knowledge Area | BABOK v3 Task/Technique` table preceded by one explanatory line. This is how framework fluency is shown WITHOUT BABOK-knowledge-area headings (anti-pattern, RESEARCH).

---

## Shared Patterns (cross-cutting, apply to both narratives)

### AG-themes-first opening (LOCKED)
**Source:** `kpi_definitions.md` line 8 blockquote; vocabulary `2019.AU2.2` (downtime) / `2019.AU2.3` (underutilization).
**Apply to:** The "Why this doc exists" blockquote at the top of BOTH files must lead with this framing. Reuse the exact codes/labels (anti-pattern: paraphrasing the audit themes).

### Falsifiable-number discipline
**Source:** `kpi_definitions.md` Method line 5 ("transcribed from that snapshot, not re-estimated"); RESEARCH §Source-of-Truth Number Registry.
**Apply to:** Every number in both narratives. Quote verbatim from the registry / `data/kpi/kpi_values.json`; never recompute. The 5.8%-computed vs ~14%-cited pair must carry the "different period / right-sizing, not an error" framing (`kpi_definitions.md` lines 72-81, `dq_report.md` 84-104).

### Disposal = SME screening list (LOCKED wording)
**Source:** `kpi_definitions.md` line 70 ("**This is a screening list for SME review, not a disposal decision.**"); `report_spec.md` Page 3.
**Apply to:** Any disposal-candidate (34) mention in both narratives — identical phrasing, never "recommend disposal."

### Real names only — three sourced individuals
**Source:** RESEARCH §Stakeholder Register Reference (Jollimore / Lalovic / Lamsaki).
**Apply to:** NARR-02 register, power/interest grid, RACI. Every other stakeholder is a role/title only (D-04). No fabricated names anywhere.

### Inter-doc cross-linking + vocabulary consistency
**Source:** `report_spec.md` line 8 (links to all four companion docs).
**Apply to:** Use page names exactly as `report_spec.md` defines them and KPI names exactly as `kpi_definitions.md` defines them; cross-link companion docs with relative markdown links. Phase 6 grades self-consistency across the three required deliverables.

---

## No Analog Found

None. Both new files map cleanly to the existing `deliverables/*.md` house style. The only genuinely new *content* (BA-methodology narrative: elicitation plan, stakeholder analysis, RACI, communication plan, risks, BABOK traceability) has no in-repo code/data analog and is framework-driven — its source is RESEARCH §BABOK Framework Reference (cited to BABOK Guide v3), not a codebase file.

## Metadata

**Analog search scope:** `deliverables/*.md` (the five committed deliverables).
**Files scanned:** `kpi_definitions.md` (full), `dq_report.md` (full), `report_spec.md` (header + first 70 lines), `measures_spec.md` (header), `data_dictionary.md` (header); plus CONTEXT.md and RESEARCH.md.
**Pattern extraction date:** 2026-06-05
