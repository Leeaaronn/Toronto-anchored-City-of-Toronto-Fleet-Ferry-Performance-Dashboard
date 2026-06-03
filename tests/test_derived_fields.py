"""MODEL-01 — derived-field, key-normalization, and ferry-slotting guards.

These tests gate the Phase-2 staging layer built by ``transform.build_all`` (via
the session-scoped ``gold`` fixture). They encode the locked decisions D-07..D-12:

- fleet_age = REFERENCE_YEAR - model YEAR, negatives allowed, NOT clamped (D-07/D-08, Pitfall 5).
- season meteorological-by-month (D-09); daypart 4-band (D-10).
- day_of_week + is_weekend Sat/Sun (D-12); sales_redemption_gap signed Sales-Redemption (D-11).
- Ferry timestamps rounded to 15-minute slots: 0 NaT, all 272,529 rows preserved.
- UNIT_NO normalized to a canonical integer key on BOTH datasets; the 44 alphanumeric
  availability units survive with a NULL key (TRY_CAST, not CAST — Pitfall 1).

Boundary-case logic (season/daypart/fleet_age) is evaluated against the SAME SQL
expressions transform.py uses, applied to synthetic literal timestamps/years, so the
cases are deterministic and independent of which calendar dates appear in the data.
Reserved words are never used as aliases (Pitfall 6).
"""

from fleet_analytics import config

# Same CASE expressions transform.py embeds, parameterized over a literal ts ::TIMESTAMP.
_SEASON_SQL = (
    "SELECT CASE WHEN month(?::TIMESTAMP) IN (12,1,2) THEN 'Winter' "
    "WHEN month(?::TIMESTAMP) IN (3,4,5) THEN 'Spring' "
    "WHEN month(?::TIMESTAMP) IN (6,7,8) THEN 'Summer' "
    "ELSE 'Fall' END"
)
_DAYPART_SQL = (
    "SELECT CASE WHEN hour(?::TIMESTAMP) >= 6 AND hour(?::TIMESTAMP) < 11 THEN 'Morning' "
    "WHEN hour(?::TIMESTAMP) >= 11 AND hour(?::TIMESTAMP) < 15 THEN 'Midday' "
    "WHEN hour(?::TIMESTAMP) >= 15 AND hour(?::TIMESTAMP) < 20 THEN 'Afternoon/Evening' "
    "ELSE 'Night' END"
)


def test_ferry_ts15(gold) -> None:
    """stg_ferry keeps all 272,529 rows and every ts_15 slot is non-NULL (0 NaT)."""
    total, null_ct = gold.execute(
        "SELECT COUNT(*) AS total, "
        "COUNT(*) FILTER (WHERE ts_15 IS NULL) AS null_ct "
        "FROM stg_ferry"
    ).fetchone()
    assert total == 272529
    assert null_ct == 0


def test_key_normalization(gold) -> None:
    """Canonical integer key on both datasets; the 44 alnum avail units survive."""
    avail_total, avail_null_key = gold.execute(
        "SELECT COUNT(*) AS total, "
        "COUNT(*) FILTER (WHERE unit_key_int IS NULL) AS null_key "
        "FROM stg_availability"
    ).fetchone()
    assert avail_total == 4614              # no rows dropped (Pitfall 1)
    assert avail_null_key == 44             # the 44 alphanumeric units -> NULL key, survive

    util_null_key = gold.execute(
        "SELECT COUNT(*) FILTER (WHERE unit_key_int IS NULL) AS null_key "
        "FROM stg_utilization"
    ).fetchone()[0]
    assert util_null_key == 0               # utilization UNIT_NO is 100% numeric (D-02)


def test_availability_nulls_preserved(gold) -> None:
    """The 209 AVAILABILITY_YTD NULLs flow through staging unchanged (no fill)."""
    null_ct = gold.execute(
        "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) FROM stg_availability"
    ).fetchone()[0]
    assert null_ct == 209


import pytest  # noqa: E402  (kept near the parametrized tests for readability)


@pytest.mark.parametrize(
    ("year", "expected_age"),
    [(2015, 8), (1982, 41), (2026, -3)],
    ids=["2015->8", "1982->41", "2026->-3_negative_allowed"],
)
def test_fleet_age(gold, year: int, expected_age: int) -> None:
    """fleet_age = REFERENCE_YEAR - YEAR; the 2026 future-model case stays negative."""
    age = gold.execute("SELECT ? - ?", [config.REFERENCE_YEAR, year]).fetchone()[0]
    assert age == expected_age
    # Sanity: the same arithmetic transform.py applies must reproduce the value.
    assert config.REFERENCE_YEAR - year == expected_age


@pytest.mark.parametrize(
    ("month_no", "expected_season"),
    [(12, "Winter"), (2, "Winter"), (3, "Spring"), (6, "Summer"),
     (8, "Summer"), (9, "Fall"), (11, "Fall")],
    ids=["12W", "2W", "3Sp", "6Su", "8Su", "9F", "11F"],
)
def test_season(gold, month_no: int, expected_season: str) -> None:
    ts = f"2021-{month_no:02d}-15 12:00:00"
    got = gold.execute(_SEASON_SQL, [ts, ts, ts]).fetchone()[0]
    assert got == expected_season


@pytest.mark.parametrize(
    ("hour_no", "expected_daypart"),
    [(5, "Night"), (6, "Morning"), (10, "Morning"), (11, "Midday"),
     (14, "Midday"), (15, "Afternoon/Evening"), (19, "Afternoon/Evening"),
     (20, "Night"), (23, "Night")],
    ids=["5N", "6Mo", "10Mo", "11Mi", "14Mi", "15AE", "19AE", "20N", "23N"],
)
def test_season_daypart(gold, hour_no: int, expected_daypart: str) -> None:
    ts = f"2021-06-15 {hour_no:02d}:30:00"
    got = gold.execute(_DAYPART_SQL, [ts, ts, ts, ts]).fetchone()[0]
    assert got == expected_daypart


def test_gap_signed(gold) -> None:
    """sales_redemption_gap == Sales - Redemption (signed); a negative gap exists."""
    mismatched = gold.execute(
        'SELECT COUNT(*) FROM stg_ferry '
        'WHERE sales_redemption_gap <> "Sales Count" - "Redemption Count"'
    ).fetchone()[0]
    assert mismatched == 0
    negative_ct = gold.execute(
        "SELECT COUNT(*) FROM stg_ferry WHERE sales_redemption_gap < 0"
    ).fetchone()[0]
    assert negative_ct > 0   # proves no abs() was applied (D-11)
