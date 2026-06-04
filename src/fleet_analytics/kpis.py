"""KPI compute layer (KPI-01): Gold Parquet -> KPI tables/scalars + committed snapshot.

This module mirrors ``model.py`` / ``transform.py`` / ``export.py``: one builder per
KPI, a single SQL statement on the shared ``con``, type-hinted
``(con: duckdb.DuckDBPyConnection)``; plus a ``build_all(con)`` orchestrator with a
fail-fast assertion loop and a ``write_kpi_snapshot(con)`` writer that COPYs the
table-valued KPIs to CSV and ``json.dump``s the scalars. The committed snapshot
(``data/kpi/kpi_values.json`` + 7 CSVs) is the falsifiable ground truth that the
Plan-02 test guards and the Plan-03 deliverable docs both consume.

Reads ``data/gold/*.parquet`` via DuckDB ``read_parquet`` (config.GOLD_DIR path
idiom from export.py) into CREATE OR REPLACE staging views, then aggregates.

Locked decisions encoded here:
- 209-NULL exclusion (D-06): NEVER COALESCE/fill ``AVAILABILITY_YTD``. Availability
  rate denominator is the 4,405 non-null rows. DuckDB ``AVG(AVAILABILITY_YTD)``
  ignores NULL automatically; the null count (209) is itself a regression guard.
- Pooled per-vehicle mean (CONTEXT line 13 / D-06): overall availability is the
  pooled ``AVG(AVAILABILITY_YTD)`` over the whole non-null row population — NOT the
  mean of per-class averages. ``build_all`` asserts the two genuinely differ.
- Single below-class-target threshold (D-01/D-02/D-03): a unit is "below threshold"
  when ``AVAILABILITY_YTD < class_target / 100``. ``gap_to_target = actual - target``
  is signed (negative = below benchmark). The exception list, the "% below" metric,
  and the disposal screen all share this one rule. Targets are audit-cited and
  ``?``-bound from ``config.ASSET_CLASS_TARGETS`` — never inlined.
- Disposal candidates (D-02) = below class target AND pre-classified
  ``Utilization = 'Underutilized'`` — surfaced as a boolean ``disposal_candidate``
  column on the exception list, framed as a screening list for SME review, never a
  decision.
- Ferry period handling: lifetime/period totals use ALL data (D-09); YoY is computed
  ONLY on complete calendar years ``config.FERRY_COMPLETE_YEARS`` 2016-2025 (D-10) —
  the partial 2015/2026 years are excluded from the YoY growth rows; the 2020 < 2019
  COVID-dip guard is asserted within that window; seasonality pools ALL years by
  month with no annualization (D-11).

Security note (export.py lines 18-21): only internal ``config`` table/path names
(``config.KPI_TABLE_CSVS`` / ``config.KPI_DIR`` / ``config.GOLD_DIR``) are ever
interpolated into the f-string SQL — no external/user value reaches the SQL string.
"""

from __future__ import annotations

import json

import duckdb

from fleet_analytics import config


def load_gold_views(con: duckdb.DuckDBPyConnection) -> None:
    """Register the Gold Parquet tables as views on ``con`` (read-only KPI input).

    Uses the export.py ``(config.GOLD_DIR / t).as_posix()`` path idiom. Only the
    internal ``config.GOLD_TABLES`` names are interpolated (security note).

    Idempotent against an already-populated connection: if a Gold name already
    exists on ``con`` as a relation (e.g. the in-memory Tables built by
    ``model.build_all`` when this runs through the ``gold`` pytest fixture), it is
    left untouched — re-creating it as a Parquet-backed View would raise
    ``Catalog Error: Existing object ... is of type Table, trying to replace with
    type View``. Only the missing names (the standalone ``main()`` path over a fresh
    ``:memory:`` connection) are loaded from ``data/gold/*.parquet``.
    """
    existing = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
    }
    for t in config.GOLD_TABLES:
        if t in existing:
            continue
        p = (config.GOLD_DIR / t).as_posix()
        con.execute(
            f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('{p}.parquet')"
        )


def _class_targets_relation() -> tuple[str, list[object]]:
    """Build a VALUES relation + bind params for ASSET_CLASS_TARGETS (never inlined).

    Returns a ``(sql_fragment, params)`` pair where the fragment is a
    ``(VALUES (?, ?, ?), ...) AS ct(unit_type, class_label, target)`` table that joins
    the real UNIT_TYPE -> class label -> audit target. The relation alias is ``ct`` so
    the builders reference its columns directly. Targets are ``?``-bound from config so
    no value is hard-coded in the SQL string (D-01/D-03).
    """
    rows: list[str] = []
    params: list[object] = []
    for unit_type, class_label in config.UNIT_TYPE_TO_CLASS.items():
        target = config.ASSET_CLASS_TARGETS[class_label]
        rows.append("(?, ?, ?)")
        params.extend([unit_type, class_label, target])
    values = ", ".join(rows)
    relation = f"(VALUES {values}) AS ct(unit_type, class_label, target)"
    return relation, params


# --------------------------------------------------------------------------- #
# Domain A — Fleet maintenance KPIs                                            #
# --------------------------------------------------------------------------- #


def build_availability_by_class(con: duckdb.DuckDBPyConnection) -> None:
    """availability_by_class: pooled rate vs audit target + signed gap, per class (D-01/D-03).

    Pooled per-vehicle mean ``AVG(AVAILABILITY_YTD)`` (NULLs ignored => 4,405-row
    denominator) joined to the ``?``-bound class targets; ``gap_to_target`` is signed
    (rate - target/100); ``below_target_n`` counts units strictly below their class
    bar. Class targets are bound in, never inlined (D-01).
    """
    relation, params = _class_targets_relation()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE availability_by_class AS
        SELECT ct.class_label                                AS asset_class,
               ct.target                                     AS target,
               AVG(fv.AVAILABILITY_YTD)                      AS availability_rate,
               AVG(fv.AVAILABILITY_YTD) - (ct.target / 100.0) AS gap_to_target,
               COUNT(fv.AVAILABILITY_YTD)                    AS rated_n,
               COUNT(*) FILTER (
                   WHERE fv.AVAILABILITY_YTD < ct.target / 100.0
               )                                             AS below_target_n
        FROM fact_vehicle fv
        JOIN {relation} ON fv.UNIT_TYPE = ct.unit_type
        GROUP BY ct.class_label, ct.target
        ORDER BY gap_to_target, asset_class
        """,
        params,
    )


def build_availability_by_division(con: duckdb.DuckDBPyConnection) -> None:
    """availability_by_division: pooled availability rate by owner division name.

    Owner-division rollup via ``using``/``owner_division_key`` -> ``dim_division``.
    Pooled mean ignores the 209 NULLs (never imputed). Sorted worst-first so the
    lowest-availability divisions surface for the BA narrative.
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE availability_by_division AS
        SELECT d.division_name                AS owner_division,
               AVG(fv.AVAILABILITY_YTD)        AS availability_rate,
               COUNT(fv.AVAILABILITY_YTD)      AS rated_n,
               COUNT(*)                        AS fleet_n
        FROM fact_vehicle fv
        JOIN dim_division d ON fv.owner_division_key = d.division_key
        GROUP BY d.division_name
        ORDER BY availability_rate, owner_division
        """
    )


def build_exception_list(con: duckdb.DuckDBPyConnection) -> None:
    """exception_list: units below their class target, ranked by gap, with disposal screen.

    One row per unit with ``AVAILABILITY_YTD < class_target/100`` (D-01), carrying
    UNIT_NO / UNIT_TYPE / asset_class / AVAILABILITY_YTD / target / signed
    gap_to_target / Utilization, ranked ascending by gap (worst first). The
    ``disposal_candidate`` boolean = below class target AND pre-classified
    ``Utilization = 'Underutilized'`` (D-02) — a screening flag for SME review, not a
    decision. NULL AVAILABILITY_YTD rows are excluded by the strict ``<`` comparison.
    """
    relation, params = _class_targets_relation()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE exception_list AS
        SELECT fv.UNIT_NO                                       AS unit_no,
               fv.UNIT_TYPE                                     AS unit_type,
               ct.class_label                                   AS asset_class,
               fv.AVAILABILITY_YTD                              AS availability_ytd,
               ct.target                                        AS target,
               fv.AVAILABILITY_YTD - (ct.target / 100.0)        AS gap_to_target,
               fv.Utilization                                   AS utilization,
               (fv.Utilization = 'Underutilized')               AS disposal_candidate
        FROM fact_vehicle fv
        JOIN {relation} ON fv.UNIT_TYPE = ct.unit_type
        WHERE fv.AVAILABILITY_YTD < ct.target / 100.0
        ORDER BY gap_to_target, unit_no
        """,
        params,
    )


def build_underutilization_by_division(con: duckdb.DuckDBPyConnection) -> None:
    """underutilization_by_division: underutilization share on the matched light-duty subset.

    Computed only on the matched light-duty rows (``Utilization IS NOT NULL``, ~2,080),
    grouped by using-division name, with the overall rate (~5.7%) carried as a
    window-style column and the specialized split (``specialized_units``) surfaced as
    a Yes-share. The classification is pre-applied in the data — never recomputed.
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE underutilization_by_division AS
        SELECT d.division_name                                            AS using_division,
               COUNT(*)                                                   AS light_duty_n,
               AVG(CASE WHEN fv.Utilization = 'Underutilized'
                        THEN 1.0 ELSE 0.0 END)                            AS underutilization_rate,
               COUNT(*) FILTER (WHERE fv.Utilization = 'Underutilized')   AS underutilized_n,
               AVG(CASE WHEN fv.specialized_units = 'Yes'
                        THEN 1.0 ELSE 0.0 END)                            AS specialized_share
        FROM fact_vehicle fv
        JOIN dim_division d ON fv.using_division_key = d.division_key
        WHERE fv.Utilization IS NOT NULL
        GROUP BY d.division_name
        ORDER BY underutilization_rate DESC, using_division
        """
    )


# --------------------------------------------------------------------------- #
# Domain B — Ferry KPIs                                                        #
# --------------------------------------------------------------------------- #


def build_ferry_yoy(con: duckdb.DuckDBPyConnection) -> None:
    """ferry_yoy: per-complete-year Sales/Redemption totals + YoY growth (D-10).

    Rows ONLY for years within ``config.FERRY_COMPLETE_YEARS`` (2016-2025) so the
    partial 2015/2026 years never distort the trend; the ``?``-bound year bounds are
    never inlined. YoY pct via ``LAG`` window. The 2020 < 2019 COVID dip lives in
    these rows and is asserted by ``build_all``.
    """
    lo, hi = config.FERRY_COMPLETE_YEARS
    con.execute(
        """
        CREATE OR REPLACE TABLE ferry_yoy AS
        WITH yearly AS (
            SELECT year(Timestamp)        AS year,
                   SUM("Sales Count")      AS sales,
                   SUM("Redemption Count") AS redemptions
            FROM fact_ferry
            WHERE year(Timestamp) BETWEEN ? AND ?
            GROUP BY year(Timestamp)
        )
        SELECT year,
               sales,
               redemptions,
               sales - LAG(sales) OVER (ORDER BY year) AS sales_delta,
               (sales - LAG(sales) OVER (ORDER BY year))
                   / NULLIF(LAG(sales) OVER (ORDER BY year), 0) AS sales_yoy_growth
        FROM yearly
        ORDER BY year
        """,
        [lo, hi],
    )


def build_ferry_seasonality(con: duckdb.DuckDBPyConnection) -> None:
    """ferry_seasonality: monthly/seasonal Sales profile pooling ALL years (D-11).

    Every month of data contributes; NO annualization / partial-year estimation.
    Groups by calendar month + the Phase-2 ``season`` derived field (no re-derivation).
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE ferry_seasonality AS
        SELECT month(Timestamp)        AS month,
               season,
               SUM("Sales Count")      AS sales,
               SUM("Redemption Count") AS redemptions,
               COUNT(*)                AS slots_n
        FROM fact_ferry
        GROUP BY month(Timestamp), season
        ORDER BY month, season
        """
    )


def build_ferry_heatmap(con: duckdb.DuckDBPyConnection) -> None:
    """ferry_heatmap: day-of-week x hour-of-day Sales demand, ALL data (D-09).

    Long-form (one row per day_of_week x hour) for Phase-4 presentation flexibility.
    Reuses the Phase-2 ``day_of_week`` derived field; hour via ``hour(Timestamp)``.
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE ferry_heatmap AS
        SELECT day_of_week,
               hour(Timestamp)         AS hour_of_day,
               SUM("Sales Count")      AS sales,
               SUM("Redemption Count") AS redemptions,
               COUNT(*)                AS slots_n
        FROM fact_ferry
        GROUP BY day_of_week, hour(Timestamp)
        ORDER BY hour_of_day, day_of_week
        """
    )


def build_sales_redemption_gap(con: duckdb.DuckDBPyConnection) -> None:
    """sales_redemption_gap: signed Sales-Redemption aggregates per complete year.

    Uses the Phase-2 signed ``sales_redemption_gap`` derived field (Sales - Redemption,
    never abs()). Aggregated by complete calendar year so the gap trend is comparable
    year over year; the ``?``-bound complete-year window matches ferry_yoy (D-10).
    """
    lo, hi = config.FERRY_COMPLETE_YEARS
    con.execute(
        """
        CREATE OR REPLACE TABLE sales_redemption_gap AS
        SELECT year(Timestamp)             AS year,
               SUM("Sales Count")           AS sales,
               SUM("Redemption Count")      AS redemptions,
               SUM(sales_redemption_gap)    AS total_gap,
               AVG(sales_redemption_gap)    AS avg_gap_per_slot
        FROM fact_ferry
        WHERE year(Timestamp) BETWEEN ? AND ?
        GROUP BY year(Timestamp)
        ORDER BY year
        """,
        [lo, hi],
    )


# --------------------------------------------------------------------------- #
# Scalars + orchestrator + snapshot writer                                    #
# --------------------------------------------------------------------------- #


def build_scalars(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    """Compute the headline scalar/benchmark facts as a flat dict for direct assertion.

    profile.py-style: each value pulled with an explicit targeted query so every
    number is independently testable and transcribable into kpi_values.json and the
    deliverable docs. Availability rates exclude the 209 NULLs (4,405-row denominator).
    """
    q = con.execute

    overall_availability_rate = q(
        "SELECT AVG(AVAILABILITY_YTD) FROM fact_vehicle"
    ).fetchone()[0]
    avail_nonnull = q(
        "SELECT COUNT(AVAILABILITY_YTD) FROM fact_vehicle"
    ).fetchone()[0]
    avail_total = q("SELECT COUNT(*) FROM fact_vehicle").fetchone()[0]
    avail_null = avail_total - avail_nonnull

    # Mean-of-class-means: the WRONG grand total, kept to prove pooled != average-of-
    # averages (the canonical pooled-mean guard). Rounded to 10 dp for a deterministic
    # snapshot — DuckDB's nested AVG can flip the last float bit across runs; 10 dp is
    # far tighter than the ~0.011 pooled-vs-class gap the guard relies on.
    mean_of_class_means = round(
        q(
            """
            SELECT AVG(class_rate) FROM (
                SELECT AVG(AVAILABILITY_YTD) AS class_rate
                FROM fact_vehicle GROUP BY UNIT_TYPE
            )
            """
        ).fetchone()[0],
        10,
    )

    overall_underutilization_rate = q(
        "SELECT AVG(CASE WHEN Utilization = 'Underutilized' THEN 1.0 ELSE 0.0 END) "
        "FROM fact_vehicle WHERE Utilization IS NOT NULL"
    ).fetchone()[0]
    light_duty_matched_n = q(
        "SELECT COUNT(*) FROM fact_vehicle WHERE Utilization IS NOT NULL"
    ).fetchone()[0]

    ferry_lifetime_sales, ferry_lifetime_redemptions = q(
        'SELECT SUM("Sales Count"), SUM("Redemption Count") FROM fact_ferry'
    ).fetchone()
    ferry_sales_max = q('SELECT MAX("Sales Count") FROM fact_ferry').fetchone()[0]
    ferry_sales_median = q(
        'SELECT median("Sales Count") FROM fact_ferry'
    ).fetchone()[0]

    lo, hi = config.FERRY_COMPLETE_YEARS
    ferry_sales_2019 = q(
        "SELECT SUM(\"Sales Count\") FROM fact_ferry WHERE year(Timestamp) = 2019"
    ).fetchone()[0]
    ferry_sales_2020 = q(
        "SELECT SUM(\"Sales Count\") FROM fact_ferry WHERE year(Timestamp) = 2020"
    ).fetchone()[0]

    # Per-class rate/target/gap, flat-keyed for direct assertion in the JSON.
    by_class: dict[str, dict[str, float]] = {}
    rows = q(
        "SELECT asset_class, availability_rate, target, gap_to_target "
        "FROM availability_by_class"
    ).fetchall()
    for asset_class, rate, target, gap in rows:
        by_class[asset_class] = {
            "availability_rate": rate,
            "target": target,
            "gap_to_target": gap,
        }

    return {
        "overall_availability_rate": overall_availability_rate,
        "mean_of_class_means": mean_of_class_means,
        "availability_nonnull_n": avail_nonnull,
        "availability_null_n": avail_null,
        "availability_by_class": by_class,
        "overall_underutilization_rate": overall_underutilization_rate,
        "light_duty_matched_n": light_duty_matched_n,
        "ferry_lifetime_sales": ferry_lifetime_sales,
        "ferry_lifetime_redemptions": ferry_lifetime_redemptions,
        "ferry_sales_max": ferry_sales_max,
        "ferry_sales_median": ferry_sales_median,
        "ferry_complete_years": list(config.FERRY_COMPLETE_YEARS),
        "ferry_sales_2019": ferry_sales_2019,
        "ferry_sales_2020": ferry_sales_2020,
    }


def build_all(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Build every KPI table on ``con`` and return it for chaining (KPI-01).

    Registers the Gold views, runs each Domain A + Domain B builder, then a fail-fast
    assertion loop so a regression fails in code, not only in pytest:
    pooled rate in [0,1] AND != mean-of-class-means; 2020 Sales < 2019 Sales; ferry
    Sales max == 7229.

    Raises:
        AssertionError: if any compute-time invariant is violated.
    """
    load_gold_views(con)

    build_availability_by_class(con)
    build_availability_by_division(con)
    build_exception_list(con)
    build_underutilization_by_division(con)
    build_ferry_yoy(con)
    build_ferry_seasonality(con)
    build_ferry_heatmap(con)
    build_sales_redemption_gap(con)

    s = build_scalars(con)

    pooled = s["overall_availability_rate"]
    assert 0.0 <= pooled <= 1.0, (
        f"overall_availability_rate {pooled} outside [0,1] "
        "— an aggregation or NULL-handling regression crept in"
    )
    assert abs(pooled - s["mean_of_class_means"]) > 1e-9, (
        "pooled per-vehicle mean equals the mean-of-class-means "
        "— the grand total was computed as average-of-averages (regression)"
    )
    assert s["ferry_sales_2020"] < s["ferry_sales_2019"], (
        f"2020 Sales {s['ferry_sales_2020']} >= 2019 Sales {s['ferry_sales_2019']} "
        "— the COVID-dip guard failed; a year filter or sum regression crept in"
    )
    assert s["ferry_sales_max"] == 7229, (
        f"ferry Sales max {s['ferry_sales_max']} != 7229 "
        "— a distribution/skew regression crept in"
    )

    return con


def write_kpi_snapshot(con: duckdb.DuckDBPyConnection) -> None:
    """Write the committed KPI snapshot: kpi_values.json + one CSV per table KPI (D-05).

    Ensures ``config.KPI_DIR`` exists (export.py idiom), COPYs each table-valued KPI
    named in ``config.KPI_TABLE_CSVS`` to ``{name}.csv`` (FORMAT CSV, HEADER) — only
    internal config names are interpolated (security note) — and ``json.dump``s the
    ``build_scalars`` flat dict (indent=2, sorted keys) for a reviewable git diff.
    Run after ``build_all(con)``.
    """
    config.KPI_DIR.mkdir(parents=True, exist_ok=True)

    for name in config.KPI_TABLE_CSVS:
        p = (config.KPI_DIR / name).as_posix()
        con.execute(f"COPY (SELECT * FROM {name}) TO '{p}.csv' (FORMAT CSV, HEADER)")

    scalars = build_scalars(con)
    json_path = (config.KPI_DIR / "kpi_values.json").as_posix()
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(scalars, fh, indent=2, sort_keys=True)


def main() -> None:
    """Regenerate the snapshot from Gold Parquet: ``uv run python -m fleet_analytics.kpis``."""
    con = duckdb.connect()
    try:
        build_all(con)
        write_kpi_snapshot(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
