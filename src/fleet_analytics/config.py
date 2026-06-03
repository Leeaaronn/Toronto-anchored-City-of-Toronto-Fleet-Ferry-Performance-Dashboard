"""Central configuration for Bronze ingest.

Single source of truth for the exact source filenames, expected row counts, and
explicit DuckDB column-type maps. NEVER retype the filenames inline elsewhere —
the availability CSV has a trailing space before ``.csv`` (Pitfall 3).

Data-fidelity rules encoded here (locked decisions):
- ``UNIT_NO`` stays VARCHAR in Bronze to preserve zero-padding (Pitfall 2);
  integer normalization is a Phase-2 task.
- ``AVAILABILITY_YTD`` is DOUBLE so blank cells become genuine SQL NULL, never 0
  (Pitfall 1 / DATA-03 — exclude the 209 nulls, never impute).
- Ferry ``Timestamp`` is tz-naive TIMESTAMP (Pitfall 4).
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root = three levels up from this file (src/fleet_analytics/config.py).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# Source CSVs live under .planning/data/ (override with FLEET_DATA_DIR if needed).
DATA_DIR: Path = Path(os.environ.get("FLEET_DATA_DIR", PROJECT_ROOT / ".planning" / "data"))

# --- Exact source filenames (VERIFIED 2026-06-02) ---------------------------
# NOTE the trailing space before ".csv" on the availability file. Do not "fix" it.
AVAIL_CSV: str = "City Vehicle Availability .csv"
UTIL_CSV: str = "Light duty city vehicle utilization data.csv"
FERRY_CSV: str = "Toronto Island Ferry Ticket Counts.csv"


def csv_path(filename: str) -> str:
    """Absolute path to a source CSV in the data directory, as a string for DuckDB."""
    return str(DATA_DIR / filename)


# --- Expected data-row counts (excl. header) — fail-fast assertion targets ---
EXPECTED_ROWS: dict[str, int] = {
    "bronze_availability": 4614,
    "bronze_utilization": 2086,
    "bronze_ferry": 272529,
}

# --- Explicit DuckDB column-type maps ---------------------------------------
# Only columns needing a forced type are pinned; others fall to read_csv inference.
# Forcing the load-bearing columns keeps the contract defensible (DATA-01/03).
AVAIL_TYPES: dict[str, str] = {
    "UNIT_NO": "VARCHAR",          # preserve zero-padding, e.g. "001052"
    "AVAILABILITY_YTD": "DOUBLE",  # blank cell -> SQL NULL, NEVER 0
    "YEAR": "INTEGER",
    "IN_SERV_DT": "DATE",
}

UTIL_TYPES: dict[str, str] = {
    "UNIT_NO": "VARCHAR",            # same zero-pad concern as availability
    "Specialized units": "VARCHAR",  # {"Yes", "No"}
    "Utilization": "VARCHAR",        # {"Underutilized", "Not Underutilized"}
    "YEAR": "INTEGER",
}

FERRY_TYPES: dict[str, str] = {
    "Timestamp": "TIMESTAMP",       # tz-naive
    "Redemption Count": "BIGINT",
    "Sales Count": "BIGINT",
}

# --- Phase-2 Gold-layer constants -------------------------------------------
# REFERENCE_YEAR drives fleet_age = REFERENCE_YEAR - model YEAR (D-07/D-08).
# 2023 is chosen to anchor fleet age to the audit/reporting baseline: the May
# 2023 FSD report to the General Government Committee and the audit's 2022-2023
# "actual" availability benchmarks (Light Duty 91%, Heavy Duty 76%, etc.) are all
# stated for that year. Using 2023 makes fleet_age comparable to those cited
# benchmarks. Negative ages (future model years 2024-2026) are legitimate and are
# NOT clamped (Pitfall 5; range observed -3..41).
REFERENCE_YEAR: int = 2023

# Target output directory for the modeled Gold tables (SHIP-01 / Power BI import).
GOLD_DIR: Path = PROJECT_ROOT / "data" / "gold"

# The five star-schema Gold tables, in build/export order.
GOLD_TABLES: list[str] = ["dim_division", "fact_vehicle", "fact_ferry", "dim_date", "dim_time"]

# Expected Gold row counts — fail-fast assertion targets (parallel to EXPECTED_ROWS).
# Consumed by model.py's fail-fast loop and test_dimensions.py (Plan 02).
GOLD_EXPECTED_ROWS: dict[str, int] = {
    "dim_division": 21,
    "fact_vehicle": 4614,
    "fact_ferry": 272529,
    "dim_date": 4383,
    "dim_time": 96,
}
