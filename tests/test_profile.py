"""DATA-02 profiling assertions.

Locks the headline DQ numbers emitted by ``profile_facts`` against the
[VERIFIED 2026-06-02] targets from the 01-VALIDATION Per-Task Verification Map.
Every number here is produced deterministically by DuckDB SUMMARIZE + targeted
SQL inside ``profile_facts`` — these tests are the regression guard that the
data dictionary and DQ report transcribe real, reproducible figures.

The ferry Sales max (7,229) is treated as a REAL peak-window outlier, not an
error (Anti-Patterns): we assert it equals the genuine maximum.
"""

from pathlib import Path

from fleet_analytics.profile import profile_facts


def test_row_counts(con):
    facts = profile_facts(con)
    assert facts["row_counts"]["bronze_availability"] == 4614
    assert facts["row_counts"]["bronze_utilization"] == 2086
    assert facts["row_counts"]["bronze_ferry"] == 272529


def test_availability_nulls(con):
    facts = profile_facts(con)
    assert facts["availability_null_count"] == 209
    assert facts["availability_non_null"] == 4405
    assert facts["availability_min"] == 0.0
    assert facts["availability_max"] == 1.0


def test_ferry_sales_skew(con):
    facts = profile_facts(con)
    # Heavy right skew: median 12 vs max 7,229 — a real peak-window story.
    assert facts["ferry_sales_median"] == 12
    assert facts["ferry_sales_max"] == 7229


def test_ferry_redemption_skew(con):
    facts = profile_facts(con)
    assert facts["ferry_redemption_median"] == 11
    assert facts["ferry_redemption_max"] == 7216


def test_underutilized_rate(con):
    facts = profile_facts(con)
    assert facts["underutilized_count"] == 120
    assert facts["underutilized_total"] == 2086
    # 120 / 2,086 = 5.75% -> rounds to 5.8% (contrasts with the AG ~14% benchmark).
    assert round(facts["underutilized_rate"] * 100, 1) == 5.8


def test_distinct_domains(con):
    facts = profile_facts(con)
    assert facts["distinct_owner_division"] == 21
    assert facts["distinct_category_class"] == 19


def test_year_range(con):
    facts = profile_facts(con)
    assert facts["year_min"] == 1982
    assert facts["year_max"] == 2026
    assert (facts["year_min"], facts["year_max"]) == (1982, 2026)


def test_dq_report_artifact_exists():
    """The DATA-02 DQ report deliverable must exist and carry the 5.8% insight."""
    root = Path(__file__).resolve().parents[1]
    report = root / "deliverables" / "dq_report.md"
    assert report.exists(), "deliverables/dq_report.md is missing"
    text = report.read_text(encoding="utf-8")
    assert "5.8%" in text
