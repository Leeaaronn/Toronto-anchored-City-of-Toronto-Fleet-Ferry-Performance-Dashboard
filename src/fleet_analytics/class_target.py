"""REPORT-01 — the committed ``dim_class_target`` reference dimension (Power BI handoff).

This module produces the small audit-target table the Power BI report joins to
``fact_vehicle`` so the availability-by-class **target line** is reproducible and
falsifiable. It mirrors the ``export.py`` COPY idiom (Parquet primary, CSV readable
secondary) and the ``kpis.py`` ``_class_targets_relation()`` "config dict -> bound
VALUES relation" idiom — every value is ``?``-bound from ``config``, never inlined.

GRAIN / KEY DECISION (resolves the 04-PATTERNS.md high-priority discrepancy, D-03/D-04):
``dim_class_target`` is a **5-row bridge keyed on ``unit_type``**, NOT a
``category_class`` dim. Rationale: ``fact_vehicle.CATEGORY_CLASS`` holds **19 granular
codes** (CLASS1-8, APPARATUS, ATTACHMENT, BOAT, CONSTRUCT, FACILITY, GROUND, LIFTING,
ROADMAIN, TRAILER, TRAM, WINTERMAIN), while the **5 audit labels** (Light / Medium /
Heavy / Off-Road / Other) live one level up via ``UNIT_TYPE`` (LIGHT DUTY / MEDIUM DUTY
/ HEAVY DUTY / OFF-ROAD / OTHER), mapped by ``config.UNIT_TYPE_TO_CLASS``. The validated
Phase-3 KPI layer joins targets with ``JOIN ... ON fv.UNIT_TYPE = ct.unit_type``
(kpis.py), so the Power BI relationship MUST be
``dim_class_target[unit_type] -> fact_vehicle[UNIT_TYPE]``. A naive
``CATEGORY_CLASS`` relationship would NOT reproduce the validated by-class values
(19-vs-5 cardinality mismatch) and would contradict the KPI join.

Provenance: the 5 targets (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90)
are **audit-cited, never recalculated** (AG 2019.AU2.2 / May 2023 FSD General Government
Committee report). They are sourced solely from ``config.ASSET_CLASS_TARGETS`` /
``config.UNIT_TYPE_TO_CLASS``.

Security note (export.py lines 18-21): only internal ``config`` constants reach the
COPY/VALUES SQL string — no external/user value is ever interpolated, and the 5 target
values are ``?``-bound (never literal in the SQL), so the same "no external value
reaches SQL" guarantee as ``export.py`` holds.

This reference dimension is deliberately kept OFF ``config.GOLD_TABLES`` — that list
drives ``GOLD_EXPECTED_ROWS`` and the 5-table ``export.write_gold`` contract guarded by
existing tests; this dedicated builder/exporter keeps those tests green.
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config


def build_class_target(con: duckdb.DuckDBPyConnection) -> None:
    """Register ``dim_class_target`` on ``con`` from config (5-row UNIT_TYPE bridge).

    Reuses the canonical ``_class_targets_relation()`` shape from kpis.py: a
    ``(VALUES (?, ?, ?), ...) AS ct(unit_type, class_label, target)`` fragment with
    ``?``-bound params drawn from ``config.UNIT_TYPE_TO_CLASS`` +
    ``config.ASSET_CLASS_TARGETS``, then materializes it as a table. The 5 target
    values are NEVER inlined into the SQL string (D-01/D-03; security note).
    """
    rows: list[str] = []
    params: list[object] = []
    for unit_type, class_label in config.UNIT_TYPE_TO_CLASS.items():
        target = config.ASSET_CLASS_TARGETS[class_label]
        rows.append("(?, ?, ?)")
        params.extend([unit_type, class_label, target])
    values = ", ".join(rows)
    relation = f"(VALUES {values}) AS ct(unit_type, class_label, target)"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE dim_class_target AS
        SELECT ct.unit_type, ct.class_label, ct.target
        FROM {relation}
        """,
        params,
    )


def write_class_target(con: duckdb.DuckDBPyConnection) -> None:
    """COPY ``dim_class_target`` to ``config.GOLD_DIR`` as Parquet + readable CSV.

    Mirrors the ``export.py`` two-statement COPY idiom: Parquet is the type-preserving
    primary (VARCHAR ``unit_type``/``class_label`` + INTEGER ``target`` survive
    natively), CSV is the readable secondary. Only the literal table name and the
    ``config.GOLD_DIR``-derived path are interpolated — no external value reaches the
    SQL string. Run after ``build_class_target(con)``.
    """
    config.GOLD_DIR.mkdir(parents=True, exist_ok=True)
    p = (config.GOLD_DIR / "dim_class_target").as_posix()
    con.execute(
        f"COPY (SELECT * FROM dim_class_target) TO '{p}.parquet' (FORMAT PARQUET)"
    )
    con.execute(
        f"COPY (SELECT * FROM dim_class_target) TO '{p}.csv' (FORMAT CSV, HEADER)"
    )


def main() -> None:
    """Regenerate the committed reference dimension: ``uv run python -m fleet_analytics.class_target``."""
    con = duckdb.connect()
    try:
        build_class_target(con)
        write_class_target(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
