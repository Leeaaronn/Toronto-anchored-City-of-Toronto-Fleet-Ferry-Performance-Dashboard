"""Pandera DataFrameSchemas — the DATA-04 data-quality contracts (Bronze tier).

Every DQ fact in this phase must be both *documented* (the 01-03 DQ report) and
*ENFORCED* (here). Pandera does both from one declarative definition: when a future
CSV re-supply breaks a contract — an out-of-range availability value, an unknown
``Utilization`` category, a re-typed ``UNIT_NO`` — the matching pytest goes red.

Contracts encoded (all targets [VERIFIED 2026-06-02] against the source CSVs):
- ``AVAILABILITY_YTD`` is a float in ``[0.0, 1.0]`` with ``nullable=True`` — the 209
  blanks are LEGAL (DATA-03 locked decision: exclude, never impute). We *assert* the
  bound; we never clamp.
- ``UNIT_NO`` stays a string (VARCHAR at ingest; zero-padding preserved), non-null.
- ``Utilization`` ∈ {"Underutilized", "Not Underutilized"}; "Specialized units" ∈
  {"Yes", "No"} — value-set guards via ``Check.isin``.
- Ferry ``Sales Count`` / ``Redemption Count`` are integers (non-null); ``Timestamp``
  is a datetime.

All three schemas use ``strict=False`` because Bronze carries more columns than the
contracted load-bearing ones (only the columns named here are validated; extras pass
through). Per "Don't Hand-Roll" — the schema is the single declarative source of the
contract; no per-column assert ladders.

Source: Pandera docs (https://pandera.readthedocs.io/). Import surface follows
RESEARCH Pattern 3: ``import pandera.pandas as pa`` + ``Column``/``Check``/
``DataFrameSchema``.
"""

from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

# Value sets (the categorical contracts). Kept inline and named so a failure
# report points straight at the offending domain.
UTILIZATION_VALUES: list[str] = ["Underutilized", "Not Underutilized"]
SPECIALIZED_VALUES: list[str] = ["Yes", "No"]


# --- City Vehicle Availability (bronze_availability) ------------------------
availability_schema: DataFrameSchema = DataFrameSchema(
    {
        # Zero-padded identifier; kept VARCHAR at ingest, so str here, non-null.
        "UNIT_NO": Column(str, nullable=False),
        # 0–1 availability fraction. nullable=True is the contract that the 209
        # blanks are legal (DATA-03). Check.in_range asserts the bound — never clamp.
        "AVAILABILITY_YTD": Column(
            float,
            Check.in_range(0.0, 1.0),
            nullable=True,
        ),
        # Asset-class label — present on every row.
        "CATEGORY_CLASS": Column(str, nullable=False),
    },
    strict=False,  # Bronze has more columns than the contracted three.
    name="availability_schema",
)


# --- Light-Duty Vehicle Utilization (bronze_utilization) --------------------
utilization_schema: DataFrameSchema = DataFrameSchema(
    {
        "UNIT_NO": Column(str, nullable=False),
        # Pre-applied binary classification — never recomputed (locked decision).
        "Utilization": Column(
            str,
            Check.isin(UTILIZATION_VALUES),
            nullable=False,
        ),
        # Column name carries an embedded space, matching the source CSV header.
        "Specialized units": Column(
            str,
            Check.isin(SPECIALIZED_VALUES),
            nullable=False,
        ),
    },
    strict=False,
    name="utilization_schema",
)


# --- Toronto Island Ferry Ticket Counts (bronze_ferry) ----------------------
ferry_schema: DataFrameSchema = DataFrameSchema(
    {
        # 15-minute grain; tz-naive datetime parsed at ingest.
        "Timestamp": Column(pa.DateTime, nullable=False),
        # Ticket counts — BIGINT at ingest -> integer here; no nulls in the source.
        "Sales Count": Column(pa.Int, nullable=False),
        "Redemption Count": Column(pa.Int, nullable=False),
    },
    strict=False,
    name="ferry_schema",
)
