"""MODEL-04 — Parquet/CSV roundtrip: type + 209-null preservation across export.

These tests are the integrity control proving the Gold export does not 0-fill the
209 missing ``AVAILABILITY_YTD`` values and does not lose column types at the
Power BI handoff boundary (T-02-06).

Method mirrors ``test_nulls.py::test_no_null_became_zero``: build the Gold layer on
the session connection, ``export.write_gold(con)`` to ``config.GOLD_DIR``, then open
a SECOND ``:memory:`` connection in ``try/finally`` and re-read the exported files
as a fresh reader would. A fill that crept in on export would surface here as a
null count drifting off 209 or a type changing under the roundtrip.

Type assertions use DuckDB ``typeof(...)`` on the re-read frame; null counts alias
as ``null_ct`` (never ``nulls``/``both`` — Pitfall 6).
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config, export


def _fact_vehicle_parquet() -> str:
    return (config.GOLD_DIR / "fact_vehicle.parquet").as_posix()


def _fact_vehicle_csv() -> str:
    return (config.GOLD_DIR / "fact_vehicle.csv").as_posix()


def _dim_division_parquet() -> str:
    return (config.GOLD_DIR / "dim_division.parquet").as_posix()


def _dim_date_parquet() -> str:
    return (config.GOLD_DIR / "dim_date.parquet").as_posix()


def test_ten_files_written(gold: duckdb.DuckDBPyConnection) -> None:
    """write_gold creates data/gold/ with exactly 10 files (5 .parquet + 5 .csv)."""
    export.write_gold(gold)
    for t in config.GOLD_TABLES:
        assert (config.GOLD_DIR / f"{t}.parquet").exists(), f"{t}.parquet missing"
        assert (config.GOLD_DIR / f"{t}.csv").exists(), f"{t}.csv missing"


def test_parquet_types(gold: duckdb.DuckDBPyConnection) -> None:
    """fact_vehicle.parquet preserves AVAILABILITY_YTD DOUBLE+209 NULLs, IN_SERV_DT DATE.

    A boolean column (dim_date.is_weekend) is checked separately to prove BOOLEAN
    survives the roundtrip — fact_vehicle has no boolean column because availability
    is cross-sectional (no date grain), so is_weekend lives on dim_date / fact_ferry.
    """
    export.write_gold(gold)

    rd = duckdb.connect(":memory:")
    try:
        avail_type = rd.execute(
            f"SELECT typeof(AVAILABILITY_YTD) FROM read_parquet('{_fact_vehicle_parquet()}') LIMIT 1"
        ).fetchone()[0]
        serv_type = rd.execute(
            f"SELECT typeof(IN_SERV_DT) FROM read_parquet('{_fact_vehicle_parquet()}') "
            "WHERE IN_SERV_DT IS NOT NULL LIMIT 1"
        ).fetchone()[0]
        null_ct = rd.execute(
            "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) AS null_ct "
            f"FROM read_parquet('{_fact_vehicle_parquet()}')"
        ).fetchone()[0]
        weekend_type = rd.execute(
            f"SELECT typeof(is_weekend) FROM read_parquet('{_dim_date_parquet()}') LIMIT 1"
        ).fetchone()[0]
    finally:
        rd.close()

    assert avail_type == "DOUBLE", f"AVAILABILITY_YTD type drifted to {avail_type}"
    assert serv_type == "DATE", f"IN_SERV_DT type drifted to {serv_type}"
    assert null_ct == 209, f"Parquet AVAILABILITY_YTD nulls == {null_ct}, expected 209"
    assert weekend_type == "BOOLEAN", f"is_weekend type drifted to {weekend_type}"


def test_csv_nulls(gold: duckdb.DuckDBPyConnection) -> None:
    """fact_vehicle.csv re-reads with AVAILABILITY_YTD NULL count == 209 (blanks stay NULL).

    A second :memory: reader parses the exported CSV with AVAILABILITY_YTD forced
    DOUBLE; the 209 blanks must come back as SQL NULL, never 0-filled.
    """
    export.write_gold(gold)

    rd = duckdb.connect(":memory:")
    try:
        null_ct = rd.execute(
            "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) AS null_ct FROM read_csv("
            f"'{_fact_vehicle_csv()}', header=true, auto_detect=true, "
            "types={'AVAILABILITY_YTD': 'DOUBLE'})"
        ).fetchone()[0]
    finally:
        rd.close()

    assert null_ct == 209, f"CSV AVAILABILITY_YTD nulls == {null_ct}, expected 209"
