"""DATA-03 — null-preservation guards for AVAILABILITY_YTD.

The 209 blank availability values must remain genuine SQL NULL and never be
imputed or coerced to 0 (locked decision: exclude, never impute). The non-null
count (4,405) is the denominator for every availability rate downstream; if a
fill ever crept in, that count would drift toward 4,614 and these tests fail.

Note: there are 13 *legitimate* 0.0 availability values in the data, so we do
NOT assert zero_ct == 0. The guard is that NULLs were not converted to 0 — which
holds structurally because AVAILABILITY_YTD is typed DOUBLE and never COALESCE'd.
"""


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


def test_no_null_became_zero(con) -> None:
    """Guard against any accidental fill that would inflate non_null toward 4,614.

    A COALESCE/fillna would push non_null from 4,405 up to 4,614. We assert the
    split is exact and reconciles: null + non_null == total == 4,614.
    """
    total, non_null, null_ct = _counts(con)
    assert total == 4614
    assert non_null == 4405
    assert null_ct == 209
    assert null_ct + non_null == total
