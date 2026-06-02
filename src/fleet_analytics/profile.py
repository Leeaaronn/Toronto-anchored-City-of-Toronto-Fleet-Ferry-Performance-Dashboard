"""Deterministic data-quality profiling (DATA-02).

``profile_facts(con)`` returns a flat dict of the headline DQ facts for the three
Bronze tables, computed with DuckDB ``SUMMARIZE`` plus a small set of targeted
SQL queries (MEDIAN / MAX / COUNT / COUNT(DISTINCT) / MIN-MAX). Per RESEARCH we do
NOT hand-roll aggregation loops and we do NOT generate a profiling-library HTML —
the SQL path is deterministic, fast, and citable, and the optional fg-data-profiling
artifact is explicitly skipped.

The returned dict is keyed for direct assertion (see tests/test_profile.py) and is
the single source the ``deliverables/`` data dictionary and DQ report transcribe.

Data-fidelity notes encoded by the queries (locked decisions):
- AVAILABILITY_YTD nulls are COUNTED, never imputed — the rate denominator is the
  4,405 non-null rows (DATA-03).
- The ferry Sales max (7,229) is a REAL peak-window outlier, surfaced as genuine
  skew (median 12 vs max 7,229), not flagged as an error.
- ``SUMMARIZE`` output is captured verbatim for the report; the headline figures are
  pulled with explicit targeted queries so each number is independently testable.
"""

from __future__ import annotations

from typing import Any

import duckdb


def _summarize(con: duckdb.DuckDBPyConnection, table: str) -> list[dict[str, Any]]:
    """Return DuckDB ``SUMMARIZE`` for a table as a list of row dicts.

    SUMMARIZE emits per-column min/max/approx_unique/null_percentage/etc. We keep
    the full frame so the DQ report can transcribe it without re-deriving anything.
    """
    return con.execute(f"SUMMARIZE {table}").df().to_dict(orient="records")


def profile_facts(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Compute the deterministic DATA-02 DQ facts from the Bronze tables.

    Args:
        con: a DuckDB connection with bronze_availability / bronze_utilization /
            bronze_ferry already ingested (see tests/conftest.py ``con`` fixture).

    Returns:
        A flat dict of headline facts plus the raw per-table SUMMARIZE output under
        ``summaries``. Counts/medians are returned as exact ints; the underutilized
        rate is a float.
    """
    q = con.execute

    # --- Per-table row counts (DATA-01) -------------------------------------
    row_counts = {
        table: q(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("bronze_availability", "bronze_utilization", "bronze_ferry")
    }

    # --- AVAILABILITY_YTD nulls + bounds (DATA-03) --------------------------
    # COUNT(col) ignores NULLs -> non-null count; total - non-null -> null count.
    avail_non_null = q(
        "SELECT COUNT(AVAILABILITY_YTD) FROM bronze_availability"
    ).fetchone()[0]
    avail_null = row_counts["bronze_availability"] - avail_non_null
    avail_min, avail_max = q(
        "SELECT MIN(AVAILABILITY_YTD), MAX(AVAILABILITY_YTD) FROM bronze_availability"
    ).fetchone()

    # --- Ferry skew: median vs max (real peak-window outliers) --------------
    ferry_sales_median, ferry_sales_max = q(
        'SELECT median("Sales Count"), MAX("Sales Count") FROM bronze_ferry'
    ).fetchone()
    ferry_redemption_median, ferry_redemption_max = q(
        'SELECT median("Redemption Count"), MAX("Redemption Count") FROM bronze_ferry'
    ).fetchone()

    # --- Underutilization rate (120 / 2,086 = 5.75% ~ 5.8%) -----------------
    underutilized_count, underutilized_total = q(
        "SELECT COUNT(*) FILTER (WHERE Utilization = 'Underutilized'), COUNT(*) "
        "FROM bronze_utilization"
    ).fetchone()
    underutilized_rate = underutilized_count / underutilized_total

    # --- Categorical domains ------------------------------------------------
    distinct_owner_division = q(
        "SELECT COUNT(DISTINCT OWNER_DIVISION) FROM bronze_availability"
    ).fetchone()[0]
    distinct_category_class = q(
        "SELECT COUNT(DISTINCT CATEGORY_CLASS) FROM bronze_availability"
    ).fetchone()[0]
    distinct_status_desc = q(
        "SELECT COUNT(DISTINCT STATUS_DESC) FROM bronze_availability"
    ).fetchone()[0]

    # --- YEAR range + ferry Timestamp range ---------------------------------
    year_min, year_max = q(
        "SELECT MIN(YEAR), MAX(YEAR) FROM bronze_availability"
    ).fetchone()
    ferry_ts_min, ferry_ts_max = q(
        "SELECT MIN(Timestamp), MAX(Timestamp) FROM bronze_ferry"
    ).fetchone()

    return {
        "row_counts": row_counts,
        "availability_null_count": avail_null,
        "availability_non_null": avail_non_null,
        "availability_null_pct": round(avail_null / row_counts["bronze_availability"], 4),
        "availability_min": avail_min,
        "availability_max": avail_max,
        "ferry_sales_median": int(ferry_sales_median),
        "ferry_sales_max": ferry_sales_max,
        "ferry_redemption_median": int(ferry_redemption_median),
        "ferry_redemption_max": ferry_redemption_max,
        "underutilized_count": underutilized_count,
        "underutilized_total": underutilized_total,
        "underutilized_rate": underutilized_rate,
        "distinct_owner_division": distinct_owner_division,
        "distinct_category_class": distinct_category_class,
        "distinct_status_desc": distinct_status_desc,
        "year_min": year_min,
        "year_max": year_max,
        "ferry_timestamp_min": ferry_ts_min,
        "ferry_timestamp_max": ferry_ts_max,
        # Raw SUMMARIZE output, kept verbatim for the DQ report deliverable.
        "summaries": {
            table: _summarize(con, table)
            for table in (
                "bronze_availability",
                "bronze_utilization",
                "bronze_ferry",
            )
        },
    }
