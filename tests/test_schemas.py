"""DATA-04 — Pandera validation tests (bounds, value sets, dtypes).

These run the declarative DQ contracts in ``fleet_analytics.schemas`` against the
Bronze frames produced by the session ``con`` fixture. A passing ``schema.validate``
is the green signal; any contract violation raises ``SchemaError`` and fails the test.

Test names match the 01-VALIDATION Per-Task Verification Map so the per-requirement
test map stays aligned:
  - test_availability_bounds  (DATA-04: AVAILABILITY_YTD non-null ∈ [0.0, 1.0])
  - test_value_sets           (DATA-04: Utilization / Specialized units value sets)
  - test_dtypes               (DATA-01/04: UNIT_NO str, AVAILABILITY_YTD float held)
  - test_ferry_schema         (DATA-04: ferry counts integer, Timestamp datetime)
"""

from __future__ import annotations

import pandas as pd

from fleet_analytics.schemas import (
    availability_schema,
    ferry_schema,
    utilization_schema,
)


def _df(con, table: str) -> pd.DataFrame:
    """Pull a Bronze table as a pandas frame for Pandera validation."""
    return con.execute(f"SELECT * FROM {table}").df()


def test_availability_bounds(con) -> None:
    """All non-null AVAILABILITY_YTD values lie within [0.0, 1.0].

    availability_schema.validate passes only if every non-null availability value
    is in bounds (Check.in_range) and the 209 nulls are tolerated (nullable=True).
    """
    frame = _df(con, "bronze_availability")
    validated = availability_schema.validate(frame)
    assert len(validated) == 4614


def test_value_sets(con) -> None:
    """Utilization ∈ {Underutilized, Not Underutilized}; Specialized units ∈ {Yes, No}.

    A stray category (e.g. a re-supplied CSV introducing "N/A") would raise
    SchemaError via the Check.isin guards and fail here.
    """
    frame = _df(con, "bronze_utilization")
    validated = utilization_schema.validate(frame)
    assert len(validated) == 2086


def test_dtypes(con) -> None:
    """The explicit-type ingest held: UNIT_NO is str, AVAILABILITY_YTD is float.

    Validating through the schema also confirms the declared dtypes; we then assert
    the realized pandas dtypes directly as a belt-and-braces regression guard.
    """
    frame = availability_schema.validate(_df(con, "bronze_availability"))
    # pandas 3.0 + DuckDB surfaces VARCHAR as the new StringDtype (not object);
    # is_string_dtype covers both the legacy object-str and the modern StringDtype.
    assert pd.api.types.is_string_dtype(frame["UNIT_NO"])
    assert pd.api.types.is_float_dtype(frame["AVAILABILITY_YTD"])


def test_ferry_schema(con) -> None:
    """Ferry counts are integer and Timestamp is a datetime (no nulls)."""
    frame = _df(con, "bronze_ferry")
    validated = ferry_schema.validate(frame)
    assert len(validated) == 272529
