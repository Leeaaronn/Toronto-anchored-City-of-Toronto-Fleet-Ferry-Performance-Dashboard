"""KPI-01 — the snapshot-as-contract guards (D-06).

The committed snapshot (``data/kpi/kpi_values.json`` + the per-table CSVs) IS the
regression contract: every headline KPI the Power BI dashboard must reproduce is
asserted here against the live compute built by the session-scoped ``gold`` fixture
(which now runs ``kpis.build_all(con)``). A silently-edited snapshot or an
aggregation/NULL-handling regression fails one of these guards (threat T-03-04).

Guards (mirroring ``test_join_integrity.py``'s ``_scalar`` exact-value idiom and
``test_derived_fields.py``'s parametrized + 209-NULL-count style):

- ``test_pooled_grand_total_mean`` — the canonical pooled per-vehicle mean
  ``AVG(AVAILABILITY_YTD)``: in [0,1], == the snapshot ~0.8899, AND genuinely
  different from the mean-of-class-means (the WRONG "average-of-averages" grand
  total). This is the value-added "pooled, not average-of-averages" proof.
- ``test_availability_null_exclusion`` — the 209 NULLs are excluded, never imputed:
  ``COUNT(*) - COUNT(AVAILABILITY_YTD) == 209`` and the rate denominator is 4,405.
- ``test_ferry_2020_below_2019`` — the COVID dip is present within the complete-years
  range: 2020 Sales < 2019 Sales.
- ``test_ferry_distribution_sanity`` — the skewed ferry distribution: Sales max ==
  7229 and median == 12.
- ``test_availability_by_class`` — each asset class's pooled rate is in [0,1] and its
  signed gap == rate - target/100 (D-03), matching the snapshot.
- ``test_snapshot_matches_live`` — load ``kpi_values.json`` and assert the persisted
  headline keys equal the live ``gold``-fixture compute (snapshot-as-contract, D-06).
- ``test_ferry_yoy_complete_years_only`` — the YoY rows cover only complete calendar
  years 2016..2025 (D-10); no partial 2015/2026 leaks in.

Reserved words are never used as aliases (Pitfall 6).
"""

from __future__ import annotations

import csv
import json

from fleet_analytics import config


def _scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


# Snapshot ground-truth values (the regression contract — data/kpi/kpi_values.json).
EXPECTED_OVERALL_AVAILABILITY = 0.8899126467628139
EXPECTED_AVAILABILITY_NULL_N = 209
EXPECTED_AVAILABILITY_NONNULL_N = 4405
EXPECTED_FERRY_SALES_2019 = 1249725
EXPECTED_FERRY_SALES_2020 = 366606
EXPECTED_FERRY_SALES_MAX = 7229
EXPECTED_FERRY_SALES_MEDIAN = 12.0


def test_pooled_grand_total_mean(gold) -> None:
    """Overall availability is the pooled per-vehicle mean — NOT average-of-averages.

    Asserts the rate is in [0,1], reproduces the snapshot ~0.8899, and is genuinely
    different from the mean-of-class-means (the canonical pooled-not-avg-of-avgs proof).
    """
    pooled = _scalar(gold, "SELECT AVG(AVAILABILITY_YTD) FROM fact_vehicle")
    assert 0.0 <= pooled <= 1.0
    assert round(pooled, 10) == round(EXPECTED_OVERALL_AVAILABILITY, 10)

    mean_of_class_means = _scalar(
        gold,
        """
        SELECT AVG(class_rate) FROM (
            SELECT AVG(AVAILABILITY_YTD) AS class_rate
            FROM fact_vehicle GROUP BY UNIT_TYPE
        )
        """,
    )
    # The pooled grand total must differ from the mean-of-class-means; if they were
    # equal the grand total was wrongly computed as an average-of-averages.
    assert abs(pooled - mean_of_class_means) > 1e-9


def test_availability_null_exclusion(gold) -> None:
    """The 209 AVAILABILITY_YTD NULLs are excluded (never imputed); denominator 4,405."""
    null_ct = _scalar(
        gold, "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) FROM fact_vehicle"
    )
    nonnull_ct = _scalar(gold, "SELECT COUNT(AVAILABILITY_YTD) FROM fact_vehicle")
    assert null_ct == EXPECTED_AVAILABILITY_NULL_N
    assert nonnull_ct == EXPECTED_AVAILABILITY_NONNULL_N


def test_ferry_2020_below_2019(gold) -> None:
    """The COVID dip is present: 2020 ferry Sales < 2019 ferry Sales (within 2016..2025)."""
    lo, hi = config.FERRY_COMPLETE_YEARS
    assert lo <= 2019 <= hi and lo <= 2020 <= hi  # both years inside the complete-years range
    vol_2019 = _scalar(
        gold, 'SELECT SUM("Sales Count") FROM fact_ferry WHERE year(Timestamp) = 2019'
    )
    vol_2020 = _scalar(
        gold, 'SELECT SUM("Sales Count") FROM fact_ferry WHERE year(Timestamp) = 2020'
    )
    assert vol_2019 == EXPECTED_FERRY_SALES_2019
    assert vol_2020 == EXPECTED_FERRY_SALES_2020
    assert vol_2020 < vol_2019


def test_ferry_distribution_sanity(gold) -> None:
    """The skewed ferry distribution: Sales max == 7229 and median == 12."""
    sales_max = _scalar(gold, 'SELECT MAX("Sales Count") FROM fact_ferry')
    sales_median = _scalar(gold, 'SELECT median("Sales Count") FROM fact_ferry')
    assert sales_max == EXPECTED_FERRY_SALES_MAX
    assert abs(sales_median - EXPECTED_FERRY_SALES_MEDIAN) < 1e-9


import pytest  # noqa: E402  (kept near the parametrized test for readability)

# Per-class snapshot values (kpi_values.json -> availability_by_class).
_BY_CLASS = {
    "Light": (0.9148903939302883, 95, -0.035109606069711696),
    "Medium": (0.8611638211554251, 92, -0.05883617884457493),
    "Heavy": (0.7947783575446652, 85, -0.055221642455334785),
    "Off-Road": (0.8882087992549461, 88, 0.008208799254946109),
    "Other": (0.9337194166028758, 90, 0.03371941660287581),
}


@pytest.mark.parametrize(
    ("asset_class", "expected_rate", "expected_target", "expected_gap"),
    [(k, *v) for k, v in _BY_CLASS.items()],
    ids=list(_BY_CLASS.keys()),
)
def test_availability_by_class(
    gold,
    asset_class: str,
    expected_rate: float,
    expected_target: int,
    expected_gap: float,
) -> None:
    """Each class's pooled rate is in [0,1] and gap == rate - target/100 (signed, D-03)."""
    rate, target, gap = gold.execute(
        "SELECT availability_rate, target, gap_to_target "
        "FROM availability_by_class WHERE asset_class = ?",
        [asset_class],
    ).fetchone()
    assert 0.0 <= rate <= 1.0
    assert target == expected_target
    assert round(rate, 10) == round(expected_rate, 10)
    assert round(gap, 10) == round(expected_gap, 10)
    # The signed gap is mechanically rate - target/100 (no judgment, no abs()).
    assert abs(gap - (rate - target / 100.0)) < 1e-9


def test_snapshot_matches_live(gold) -> None:
    """The committed kpi_values.json equals the live compute for the headline keys (D-06)."""
    json_path = config.KPI_DIR / "kpi_values.json"
    with open(json_path, encoding="utf-8") as fh:
        snap = json.load(fh)

    live_rate = _scalar(gold, "SELECT AVG(AVAILABILITY_YTD) FROM fact_vehicle")
    live_null_n = _scalar(
        gold, "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) FROM fact_vehicle"
    )
    live_sales_max = _scalar(gold, 'SELECT MAX("Sales Count") FROM fact_ferry')

    assert round(snap["overall_availability_rate"], 10) == round(live_rate, 10)
    assert snap["availability_null_n"] == live_null_n
    assert snap["ferry_sales_max"] == live_sales_max


def test_ferry_yoy_complete_years_only(gold) -> None:
    """The YoY rows cover only complete calendar years 2016..2025 — no 2015/2026 (D-10)."""
    lo, hi = config.FERRY_COMPLETE_YEARS
    complete_range = set(range(lo, hi + 1))

    # Live builder output (the in-memory ferry_yoy table built by kpis.build_all).
    live_years = {
        row[0] for row in gold.execute("SELECT year FROM ferry_yoy").fetchall()
    }
    assert live_years <= complete_range
    assert min(live_years) >= 2016 and max(live_years) <= 2025

    # The committed snapshot CSV must agree (snapshot-as-contract).
    csv_path = config.KPI_DIR / "ferry_yoy.csv"
    with open(csv_path, encoding="utf-8", newline="") as fh:
        csv_years = {int(row["year"]) for row in csv.DictReader(fh)}
    assert csv_years <= complete_range
    assert csv_years == live_years
