"""Gold (star-schema) build: staging tables -> five modeled Gold tables (MODEL-02/MODEL-03).

This module mirrors ``ingest.py`` / ``transform.py``: one private per-table builder
running a single ``CREATE OR REPLACE TABLE ... AS SELECT`` on the shared connection,
plus a ``build_all(con)`` orchestrator that calls them in dependency order and runs a
fail-fast Gold count loop before returning ``con``. The verified SQL bodies come from
02-RESEARCH.md Examples 2, 5, 6, live-executed against DuckDB 1.5.3.

This is the critical-path node. The flagship availability⋈utilization join (MODEL-03)
and the conformed star schema (MODEL-02) are won or lost here.

Locked decisions encoded here:
- ``fact_vehicle`` is availability-anchored (``stg_availability a LEFT JOIN
  stg_utilization u ON a.unit_key_int = u.unit_key_int``) so it stays exactly 4,614
  rows with NO fan-out — the 44 alphanumeric units (NULL join key) survive (D-01,
  Pitfall 1). NEVER ``INNER JOIN``; NEVER ``WHERE unit_key_int IS NOT NULL`` before
  the fact build.
- 2,080 fact rows carry a non-null Utilization; the 6 *unmatched* utilization rows
  fall outside the availability-anchored fact by design and are surfaced only via the
  ``dq_unmatched_utilization`` anti-join (D-03, Pitfall 2). 2,080 + 6 == 2,086.
- ``dim_division`` is ONE conformed dimension of 21 rows: a ``ROW_NUMBER()`` surrogate
  over the normalized (``upper(trim(regexp_replace(col,'\\s+',' ','g')))``) distinct
  union of OWNER_DIVISION + REF_USING_DIV. Truncated names stay verbatim (D-06).
- ``fact_vehicle`` carries two role-playing FKs (D-05): ``owner_division_key`` (always
  populated) and ``using_division_key`` (NULL for non-light-duty), each resolved by
  joining the normalized division name back to ``dim_division``.
- ``dim_date`` is a gapless daily spine 2015→2026 (4,383 rows, natural DATE key);
  ``dim_time`` is exactly 96 fifteen-minute slots (D-13).
- AVAILABILITY_YTD nullability is untouched — no COALESCE/fillna anywhere, so the 209
  NULLs flow through the join into ``fact_vehicle`` (Pitfall 3).
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config

# Reusable normalization expression (02-RESEARCH.md Example 5) — collapse internal
# whitespace, trim, upper. Applied identically when building dim_division and when
# resolving the role-playing FKs so names reconcile exactly.
_NORM = "upper(trim(regexp_replace({col}, '\\s+', ' ', 'g')))"


def build_dim_division(con: duckdb.DuckDBPyConnection) -> None:
    """dim_division: one conformed dim of 21 rows (D-04/D-06).

    Surrogate ``division_key`` via ``ROW_NUMBER()`` over the normalized distinct union
    of OWNER_DIVISION (availability) and REF_USING_DIV (utilization). Truncated names
    are kept verbatim — no spelling force-maps (D-06).
    """
    con.execute(
        f"""
        CREATE OR REPLACE TABLE dim_division AS
        WITH names AS (
            SELECT DISTINCT {_NORM.format(col="OWNER_DIVISION")} AS division_name
            FROM stg_availability WHERE OWNER_DIVISION IS NOT NULL
            UNION
            SELECT DISTINCT {_NORM.format(col="REF_USING_DIV")} AS division_name
            FROM stg_utilization WHERE REF_USING_DIV IS NOT NULL
        )
        SELECT ROW_NUMBER() OVER (ORDER BY division_name) AS division_key,
               division_name
        FROM names
        """
    )


def build_fact_vehicle(con: duckdb.DuckDBPyConnection) -> None:
    """fact_vehicle: availability-anchored LEFT JOIN with role-playing division FKs.

    4,614 rows, no fan-out (D-01). Carries Utilization / specialized_units /
    REF_USING_DIV from the LEFT-joined utilization, plus ``owner_division_key``
    (always populated) and ``using_division_key`` (NULL for non-light-duty), resolved
    by joining the normalized name back to ``dim_division`` (D-05). AVAILABILITY_YTD
    passes through untouched — its 209 NULLs survive (Pitfall 3).
    """
    con.execute(
        f"""
        CREATE OR REPLACE TABLE fact_vehicle AS
        SELECT a.*,
               u.Utilization,
               u."Specialized units" AS specialized_units,
               u.REF_USING_DIV,
               od.division_key AS owner_division_key,
               ud.division_key AS using_division_key
        FROM stg_availability a
        LEFT JOIN stg_utilization u
               ON a.unit_key_int = u.unit_key_int
        LEFT JOIN dim_division od
               ON {_NORM.format(col="a.OWNER_DIVISION")} = od.division_name
        LEFT JOIN dim_division ud
               ON {_NORM.format(col="u.REF_USING_DIV")} = ud.division_name
        """
    )


def build_dq_unmatched_utilization(con: duckdb.DuckDBPyConnection) -> None:
    """dq_unmatched_utilization: the 6 utilization rows with no availability match (D-03).

    Anti-join from 02-RESEARCH.md Example 2. These fall outside the availability-
    anchored ``fact_vehicle`` by design (Pitfall 2) and feed the Plan-03 DQ finding.
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE dq_unmatched_utilization AS
        SELECT u.*
        FROM stg_utilization u
        LEFT JOIN stg_availability a ON u.unit_key_int = a.unit_key_int
        WHERE a.unit_key_int IS NULL
        """
    )


def build_fact_ferry(con: duckdb.DuckDBPyConnection) -> None:
    """fact_ferry: full 15-minute grain (272,529 rows).

    Straight projection of ``stg_ferry`` — aggregation/rollup is a Phase-3 concern
    (RESEARCH Open Question 2). Carries ts_15 + all derived ferry fields.
    """
    con.execute("CREATE OR REPLACE TABLE fact_ferry AS SELECT * FROM stg_ferry")


def build_dim_date(con: duckdb.DuckDBPyConnection) -> None:
    """dim_date: gapless daily spine 2015-01-01 → 2026-12-31 (4,383 rows).

    Natural DATE ``date_key`` surrogate (idiomatic; enables Power BI "Mark as Date
    Table"). Gapless by construction via ``generate_series`` (02-RESEARCH.md Example 6).
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE dim_date AS
        SELECT
            CAST(d AS DATE)   AS date_key,
            year(d)           AS year,
            month(d)          AS month,
            monthname(d)      AS month_name,
            day(d)            AS day,
            dayname(d)        AS day_of_week,
            (isodow(d) >= 6)  AS is_weekend,
            quarter(d)        AS quarter
        FROM generate_series(DATE '2015-01-01', DATE '2026-12-31', INTERVAL '1 day') AS t(d)
        """
    )


def build_dim_time(con: duckdb.DuckDBPyConnection) -> None:
    """dim_time: exactly 96 fifteen-minute slots (00:00 → 23:45).

    Integer ``ROW_NUMBER()`` surrogate ``time_key`` (02-RESEARCH.md Example 6).
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE dim_time AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY CAST(g AS TIME)) AS time_key,
            CAST(g AS TIME)                              AS time_of_day,
            hour(g)                                      AS hour,
            minute(g)                                    AS minute
        FROM generate_series(
            TIMESTAMP '2000-01-01 00:00',
            TIMESTAMP '2000-01-01 23:45',
            INTERVAL '15 minutes'
        ) AS s(g)
        """
    )


def build_all(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Build the full Gold layer on ``con`` and return it for chaining.

    Dependency order: ``dim_division`` BEFORE ``fact_vehicle`` so the role-playing FK
    joins resolve. After building, a fail-fast loop asserts each Gold row count against
    ``config.GOLD_EXPECTED_ROWS`` so a regression fails in code, not only in pytest.

    Raises:
        AssertionError: if any Gold table row count does not match GOLD_EXPECTED_ROWS.
    """
    build_dim_division(con)
    build_fact_vehicle(con)
    build_dq_unmatched_utilization(con)
    build_fact_ferry(con)
    build_dim_date(con)
    build_dim_time(con)

    for table, expected in config.GOLD_EXPECTED_ROWS.items():
        got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert got == expected, (
            f"{table}: expected {expected} Gold rows, got {got} "
            "— a join, filter, or spine regression crept in"
        )

    return con
