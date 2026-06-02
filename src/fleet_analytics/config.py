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

from pathlib import Path

# Repo root = three levels up from this file (src/fleet_analytics/config.py).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# --- Exact source filenames (VERIFIED 2026-06-02) ---------------------------
# NOTE the trailing space before ".csv" on the availability file. Do not "fix" it.
AVAIL_CSV: str = "City Vehicle Availability .csv"
UTIL_CSV: str = "Light duty city vehicle utilization data.csv"
FERRY_CSV: str = "Toronto Island Ferry Ticket Counts.csv"


def csv_path(filename: str) -> str:
    """Absolute path to a source CSV at the repo root, as a string for DuckDB."""
    return str(PROJECT_ROOT / filename)


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
