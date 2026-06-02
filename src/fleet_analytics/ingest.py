"""Bronze ingest: three source CSVs -> typed DuckDB Bronze tables.

This is where DATA-01 (row counts) and DATA-03 (209-null preservation) are won
or lost. We use DuckDB ``read_csv`` with an explicit per-column ``types`` override
so the load-bearing columns get the right type while the rest are inferred:

- ``UNIT_NO`` -> VARCHAR (preserve zero-padding)
- ``AVAILABILITY_YTD`` -> DOUBLE (blank cell -> SQL NULL, never 0; never COALESCE'd)
- ferry ``Timestamp`` -> TIMESTAMP (tz-naive)

``read_csv`` handles RFC-4180 quoting, so the embedded comma in OWNER_DIVISION
(e.g. ``"ENVIRONMENT, CLIMATE & FORESTR"``) parses correctly without hand-splitting.

After all three tables are created, a fail-fast loop asserts each row count
against ``EXPECTED_ROWS`` and names the offending table on mismatch (T-01-01).
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config


def _types_struct(types: dict[str, str]) -> str:
    """Render a DuckDB STRUCT literal for the read_csv ``types`` override."""
    fields = ", ".join(f"'{col}': '{dtype}'" for col, dtype in types.items())
    return "{" + fields + "}"


def _create_bronze(
    con: duckdb.DuckDBPyConnection,
    table: str,
    filename: str,
    types: dict[str, str],
) -> None:
    """Create one Bronze table from a CSV with explicit type overrides.

    ``auto_detect=true`` infers the remaining columns; ``types`` forces only the
    named load-bearing columns. No COALESCE/fill anywhere — blanks stay NULL.
    """
    path = config.csv_path(filename)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT * FROM read_csv(
            ?,
            header = true,
            auto_detect = true,
            types = {_types_struct(types)}
        )
        """,
        [path],
    )


def ingest_bronze(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Ingest the three source CSVs into typed Bronze tables on ``con``.

    Creates ``bronze_availability``, ``bronze_utilization``, ``bronze_ferry`` and
    runs a fail-fast row-count assertion. Returns the same connection for chaining.

    Raises:
        AssertionError: if any Bronze table row count does not match EXPECTED_ROWS.
    """
    _create_bronze(con, "bronze_availability", config.AVAIL_CSV, config.AVAIL_TYPES)
    _create_bronze(con, "bronze_utilization", config.UTIL_CSV, config.UTIL_TYPES)
    _create_bronze(con, "bronze_ferry", config.FERRY_CSV, config.FERRY_TYPES)

    for table, expected in config.EXPECTED_ROWS.items():
        got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert got == expected, (
            f"{table}: expected {expected} rows, got {got} "
            "— CSV may have been re-supplied or truncated"
        )

    return con
