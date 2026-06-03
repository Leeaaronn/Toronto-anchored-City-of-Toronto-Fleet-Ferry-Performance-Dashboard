"""DATA-03 — null-preservation guards for AVAILABILITY_YTD.

The 209 blank availability values must remain genuine SQL NULL and never be
imputed or coerced to 0 (locked decision: exclude, never impute). The non-null
count (4,405) is the denominator for every availability rate downstream; if a
fill ever crept in, that count would drift toward 4,614 and these tests fail.

Note: there are 13 *legitimate* 0.0 availability values in the data, so we do
NOT assert zero_ct == 0. The guard is that NULLs were not converted to 0 — which
holds structurally because AVAILABILITY_YTD is typed DOUBLE and never COALESCE'd.
"""

import duckdb

from fleet_analytics import config


def _counts(con):
    return con.execute(
        """
        SELECT COUNT(*)                           AS total,
               COUNT(AVAILABILITY_YTD)            AS non_null,
               COUNT(*) - COUNT(AVAILABILITY_YTD) AS null_ct
        FROM bronze_availability
        """
    ).fetchone()


def test_null_count(con) -> None:
    """Exactly 209 NULL AVAILABILITY_YTD values are preserved (the DQ gap)."""
    _total, _non_null, null_ct = _counts(con)
    assert null_ct == 209


def test_nonnull_count(con) -> None:
    """4,405 non-null values — the denominator for every availability rate."""
    _total, non_null, _null_ct = _counts(con)
    assert non_null == 4405


def test_count_reconciliation(con) -> None:
    """Counts reconcile exactly: null + non_null == total == 4,614.

    A full COALESCE/fillna would push non_null from 4,405 toward 4,614; this
    reconciliation catches that coarse failure mode.
    """
    total, non_null, null_ct = _counts(con)
    assert total == 4614
    assert non_null == 4405
    assert null_ct == 209
    assert null_ct + non_null == total


def test_no_null_became_zero(con) -> None:
    """Value-level guard against the RAW CSV — blanks stay NULL, zeros are intact.

    Counts alone can be fooled by an offsetting edit. Here we re-read the raw
    availability CSV with AVAILABILITY_YTD forced to VARCHAR (so original textual
    cells are visible) and prove the Bronze table preserved them cell-for-cell:
      - every blank raw cell is NULL in Bronze (no blank -> 0 and no blank -> value fill)
      - the count of literal-0 raw cells equals Bronze's 0.0 count (no NULL coerced
        to 0, and no genuine 0 dropped) — the 13 legitimate zeros must survive.
    """
    raw = duckdb.connect(":memory:")
    try:
        raw.execute(
            "CREATE TABLE raw AS SELECT * FROM read_csv("
            "?, header=true, auto_detect=true, types={'AVAILABILITY_YTD': 'VARCHAR'})",
            [config.csv_path(config.AVAIL_CSV)],
        )
        raw_blank = raw.execute(
            "SELECT COUNT(*) FROM raw "
            "WHERE AVAILABILITY_YTD IS NULL OR TRIM(AVAILABILITY_YTD) = ''"
        ).fetchone()[0]
        raw_zero = raw.execute(
            "SELECT COUNT(*) FROM raw WHERE TRY_CAST(AVAILABILITY_YTD AS DOUBLE) = 0.0"
        ).fetchone()[0]
    finally:
        raw.close()

    bronze_null = con.execute(
        "SELECT COUNT(*) - COUNT(AVAILABILITY_YTD) FROM bronze_availability"
    ).fetchone()[0]
    bronze_zero = con.execute(
        "SELECT COUNT(*) FILTER (WHERE AVAILABILITY_YTD = 0.0) FROM bronze_availability"
    ).fetchone()[0]

    assert raw_blank == bronze_null == 209, (
        f"blank raw cells ({raw_blank}) != Bronze NULLs ({bronze_null}) — a fill crept in"
    )
    assert raw_zero == bronze_zero, (
        f"raw literal-0 cells ({raw_zero}) != Bronze 0.0 values ({bronze_zero}) "
        "— a NULL may have been coerced to 0, or a genuine 0 dropped"
    )
