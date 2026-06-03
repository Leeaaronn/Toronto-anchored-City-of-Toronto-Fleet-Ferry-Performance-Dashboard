"""MODEL-03 — the flagship availability⋈utilization join-integrity hard gate.

This is the non-negotiable < 5s gate and the value-added step most candidates
miss. ``fact_vehicle`` is availability-anchored (LEFT JOIN), so it stays exactly
4,614 rows with NO fan-out — the 44 alphanumeric availability units (NULL join
key) survive, and the 6 unmatched *utilization* rows fall outside the fact by
design (surfaced only via the ``dq_unmatched_utilization`` anti-join).

Mirrors ``test_nulls.py``'s count-helper + reconciliation idiom. Aliases use
``null_ct`` / ``in_both`` — never the reserved words ``both`` / ``nulls``
(Pitfall 6).
"""

from __future__ import annotations


def _scalar(con, sql: str) -> int:
    return con.execute(sql).fetchone()[0]


def test_matched_2080(gold) -> None:
    """Exactly 2,080 fact_vehicle rows carry a non-null Utilization flag."""
    matched = _scalar(
        gold, "SELECT COUNT(*) FROM fact_vehicle WHERE Utilization IS NOT NULL"
    )
    assert matched == 2080


def test_unmatched_6(gold) -> None:
    """The anti-join surfaces 6 unmatched utilization rows; 2080 + 6 == 2086."""
    unmatched = _scalar(gold, "SELECT COUNT(*) FROM dq_unmatched_utilization")
    matched = _scalar(
        gold, "SELECT COUNT(*) FROM fact_vehicle WHERE Utilization IS NOT NULL"
    )
    assert unmatched == 6
    assert matched + unmatched == 2086


def test_fact_rowcount_4614(gold) -> None:
    """fact_vehicle is availability-anchored: 4,614 rows, no fan-out.

    The 44 alphanumeric availability units (NULL join key) survive — an INNER
    JOIN or a pre-filter on the key would drop them below 4,614.
    """
    total = _scalar(gold, "SELECT COUNT(*) FROM fact_vehicle")
    assert total == 4614


def test_fact_unique_key(gold) -> None:
    """No row duplication: COUNT(*) == COUNT(DISTINCT UNIT_NO) == 4,614."""
    total, distinct = gold.execute(
        "SELECT COUNT(*), COUNT(DISTINCT UNIT_NO) FROM fact_vehicle"
    ).fetchone()
    assert total == distinct == 4614


def test_util_key_not_null(gold) -> None:
    """Every utilization join key is non-NULL (D-02 'no NaN join key')."""
    null_ct = _scalar(
        gold,
        "SELECT COUNT(*) FILTER (WHERE unit_key_int IS NULL) FROM stg_utilization",
    )
    assert null_ct == 0
