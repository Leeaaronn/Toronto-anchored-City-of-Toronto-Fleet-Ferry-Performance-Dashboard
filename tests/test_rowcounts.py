"""DATA-01 — row-count assertions for the three Bronze tables.

Each source CSV must land exactly the verified number of data rows
(4,614 / 2,086 / 272,529). A mismatch means the CSV was re-supplied or
truncated and downstream work cannot be trusted.
"""

import pytest

from fleet_analytics.config import EXPECTED_ROWS


@pytest.mark.parametrize(
    ("table", "expected"),
    list(EXPECTED_ROWS.items()),
    ids=list(EXPECTED_ROWS.keys()),
)
def test_bronze_rowcount(con, table: str, expected: int) -> None:
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assert got == expected, f"{table}: expected {expected} rows, got {got}"


def test_availability_rowcount(con) -> None:
    got = con.execute("SELECT COUNT(*) FROM bronze_availability").fetchone()[0]
    assert got == 4614


def test_utilization_rowcount(con) -> None:
    got = con.execute("SELECT COUNT(*) FROM bronze_utilization").fetchone()[0]
    assert got == 2086


def test_ferry_rowcount(con) -> None:
    got = con.execute("SELECT COUNT(*) FROM bronze_ferry").fetchone()[0]
    assert got == 272529


def test_unit_no_is_varchar_zero_padded(con) -> None:
    """UNIT_NO must stay VARCHAR so zero-padding (e.g. '001052') is preserved."""
    dtype = con.execute(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name = 'bronze_availability' AND column_name = 'UNIT_NO'"
    ).fetchone()[0]
    assert dtype.upper() == "VARCHAR"
    # At least one genuinely zero-padded unit exists (leading zero preserved).
    padded = con.execute(
        "SELECT COUNT(*) FROM bronze_availability WHERE UNIT_NO LIKE '0%'"
    ).fetchone()[0]
    assert padded > 0


def test_availability_ytd_is_double(con) -> None:
    """AVAILABILITY_YTD must be DOUBLE so blanks become NULL, never 0."""
    dtype = con.execute(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name = 'bronze_availability' AND column_name = 'AVAILABILITY_YTD'"
    ).fetchone()[0]
    assert dtype.upper() == "DOUBLE"
