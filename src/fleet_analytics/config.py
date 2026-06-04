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

# --- Phase-3 KPI-layer constants --------------------------------------------
# Asset-class availability targets (audit-cited, NEVER recalculated — AG
# 2019.AU2.2 / May 2023 FSD General Government Committee report). A unit is
# "below threshold" when AVAILABILITY_YTD < its class target (D-01); the signed
# gap_to_target = actual - target (D-03). These are percentage-point targets on
# the 0-100 scale; AVAILABILITY_YTD is the 0-1 fraction, so the KPI SQL compares
# AVAILABILITY_YTD against target / 100. NEVER inline these into a SQL string —
# bind/join them in via ? (transform.py REFERENCE_YEAR idiom).
ASSET_CLASS_TARGETS: dict[str, int] = {
    "Light": 95,
    "Medium": 92,
    "Heavy": 85,
    "Off-Road": 88,
    "Other": 90,
}

# Maps the real fact_vehicle UNIT_TYPE values (upper-case, VERIFIED against
# data/gold/fact_vehicle.parquet) to the ASSET_CLASS_TARGETS label keys, so the
# by-class KPI SQL can join class targets in without inlining either dict.
UNIT_TYPE_TO_CLASS: dict[str, str] = {
    "LIGHT DUTY": "Light",
    "MEDIUM DUTY": "Medium",
    "HEAVY DUTY": "Heavy",
    "OFF-ROAD": "Off-Road",
    "OTHER": "Other",
}

# Committed KPI-snapshot output directory (parallel to GOLD_DIR). Kept reviewable
# in git — every dashboard number must reproduce a value written here (D-05).
KPI_DIR: Path = PROJECT_ROOT / "data" / "kpi"

# The eight table-valued KPI base names -> one CSV each under KPI_DIR (parallel
# to GOLD_TABLES). Drives the config-driven snapshot writer in kpis.py (D-05).
KPI_TABLE_CSVS: list[str] = [
    "availability_by_class",
    "availability_by_division",
    "exception_list",
    "underutilization_by_division",
    "ferry_yoy",
    "ferry_seasonality",
    "ferry_heatmap",
    "sales_redemption_gap",
]

# Inclusive complete-calendar-year window for the ferry YoY trend KPI (D-10).
# The ~8-month 2015 and ~6-month 2026 partial years are labeled and excluded
# from YoY growth ONLY — lifetime totals (D-09) and seasonality (D-11) use ALL
# data. The 2020 < 2019 COVID-dip guard is asserted within this window.
FERRY_COMPLETE_YEARS: tuple[int, int] = (2016, 2025)
