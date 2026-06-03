"""Staging (Silver) transform: Bronze tables -> keyed/derived staging tables (MODEL-01).

This module mirrors ``ingest.py``: one private per-table builder running a single
``CREATE OR REPLACE TABLE ... AS SELECT`` on the shared connection, plus a
``build_all(con)`` orchestrator that returns ``con`` for chaining. The verified SQL
bodies come from 02-RESEARCH.md (Examples 1, 3, 4), live-executed on DuckDB 1.5.3.

Load-bearing columns / locked decisions encoded here:
- ``unit_key_int = TRY_CAST(UNIT_NO AS BIGINT)`` is the canonical integer JOIN key on
  BOTH datasets. TRY_CAST (never plain CAST) returns NULL for the 44 alphanumeric
  availability units (e.g. '296011A', 'CLAW10') so those rows SURVIVE with a NULL key
  rather than throwing/being dropped (D-02, Pitfall 1). Utilization UNIT_NO is 100%
  numeric -> zero NULL keys.
- ``fleet_age = REFERENCE_YEAR - YEAR`` bound via ``?`` (config.REFERENCE_YEAR, D-07/D-08).
  Negatives are legitimate (future model years 2024-2026; range -3..41) and are NOT
  clamped (Pitfall 5).
- Ferry ``ts_15 = time_bucket(INTERVAL '15 minutes', "Timestamp")`` -> 0 NaT, 272,529 preserved.
- Ferry derived fields: season (D-09), daypart (D-10), day_of_week + is_weekend Sat/Sun
  (D-12), and ``sales_redemption_gap = "Sales Count" - "Redemption Count"`` SIGNED (D-11,
  never abs()). Uses scalar month()/hour()/isodow()/dayname() — never double-quoted
  date_part (Binder Error, Pitfall 4).
- AVAILABILITY_YTD nullability is untouched: no COALESCE / fillna anywhere, so the 209
  NULLs flow through unchanged (Phase-1 test_nulls.py is the regression guard).
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config


def build_keyed_availability(con: duckdb.DuckDBPyConnection) -> None:
    """stg_availability: add canonical integer key + fleet_age (D-07/D-08).

    TRY_CAST keeps the 44 alphanumeric units (NULL key, row survives). fleet_age binds
    ``config.REFERENCE_YEAR`` via ``?`` and is NOT clamped for negative (future) years.
    AVAILABILITY_YTD is carried through ``*`` untouched (209 NULLs preserved).
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_availability AS
        SELECT *,
               TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int,
               (? - YEAR)                  AS fleet_age
        FROM bronze_availability
        """,
        [config.REFERENCE_YEAR],
    )


def build_keyed_utilization(con: duckdb.DuckDBPyConnection) -> None:
    """stg_utilization: add the same canonical integer key (D-02; zero NULL keys)."""
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_utilization AS
        SELECT *,
               TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int
        FROM bronze_utilization
        """
    )


def build_staged_ferry(con: duckdb.DuckDBPyConnection) -> None:
    """stg_ferry: 15-minute slot + season/daypart/day_of_week/is_weekend/gap (D-09..D-12).

    ``sales_redemption_gap`` is signed (Sales - Redemption); scalar date functions avoid
    the double-quoted date_part Binder Error (Pitfall 4).
    """
    con.execute(
        """
        CREATE OR REPLACE TABLE stg_ferry AS
        SELECT *,
               time_bucket(INTERVAL '15 minutes', "Timestamp")          AS ts_15,
               CASE WHEN month("Timestamp") IN (12, 1, 2) THEN 'Winter'
                    WHEN month("Timestamp") IN (3, 4, 5)  THEN 'Spring'
                    WHEN month("Timestamp") IN (6, 7, 8)  THEN 'Summer'
                    ELSE 'Fall' END                                     AS season,
               CASE WHEN hour("Timestamp") >= 6  AND hour("Timestamp") < 11 THEN 'Morning'
                    WHEN hour("Timestamp") >= 11 AND hour("Timestamp") < 15 THEN 'Midday'
                    WHEN hour("Timestamp") >= 15 AND hour("Timestamp") < 20 THEN 'Afternoon/Evening'
                    ELSE 'Night' END                                    AS daypart,
               dayname("Timestamp")                                     AS day_of_week,
               (isodow("Timestamp") >= 6)                               AS is_weekend,
               "Sales Count" - "Redemption Count"                       AS sales_redemption_gap
        FROM bronze_ferry
        """
    )


def build_all(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Build the full staging layer on ``con`` and return it for chaining.

    Consumed by the ``gold`` test fixture and (Plan 02) ``model.build_all``.
    """
    build_keyed_availability(con)
    build_keyed_utilization(con)
    build_staged_ferry(con)
    return con
