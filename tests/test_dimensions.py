"""MODEL-02 — star-schema dimension guards (dim_date / dim_time / dim_division).

- ``dim_date`` must be a gapless daily spine 2015-01-01 → 2026-12-31 (4,383 rows);
  gaplessness is proven by ``datediff('day', MIN, MAX) + 1 == COUNT(*)``.
- ``dim_time`` is exactly 96 fifteen-minute slots.
- ``dim_division`` is ONE conformed dimension of 21 rows with a unique surrogate
  ``division_key`` (normalized distinct union of owner + using division names,
  truncated names kept verbatim per D-06).
"""

from __future__ import annotations


def test_dim_date_gapless(gold) -> None:
    """dim_date has 4,383 rows and is gapless (span == row count)."""
    total, span = gold.execute(
        """
        SELECT COUNT(*),
               datediff('day', MIN(date_key), MAX(date_key)) + 1
        FROM dim_date
        """
    ).fetchone()
    assert total == 4383
    assert span == total


def test_dim_time_96(gold) -> None:
    """dim_time is exactly 96 fifteen-minute slots."""
    total = gold.execute("SELECT COUNT(*) FROM dim_time").fetchone()[0]
    assert total == 96


def test_dim_division_conformed(gold) -> None:
    """dim_division is 21 conformed rows with a unique surrogate key."""
    total, distinct = gold.execute(
        "SELECT COUNT(*), COUNT(DISTINCT division_key) FROM dim_division"
    ).fetchone()
    assert total == 21
    assert total == distinct
