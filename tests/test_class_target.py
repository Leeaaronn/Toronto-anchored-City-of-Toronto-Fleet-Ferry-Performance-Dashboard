"""REPORT-01 — falsifiable guard on the committed ``dim_class_target`` reference dim.

Mirrors ``tests/test_dimensions.py`` (in-DB row/value guard on the ``gold`` fixture)
and ``tests/test_export.py`` (re-read the exported Parquet via a SECOND ``:memory:``
connection in ``try/finally``).

The 5 audit targets (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90) are
locked as a parametrized guard so any drift fails CI (T-04-01). The key is
``unit_type`` — the validated Phase-3 KPI join key — so the table is a 5-row
1:1 ``UNIT_TYPE -> (class_label, target)`` bridge (one row per audit class), NOT a
``CATEGORY_CLASS`` dim (which would be 19-vs-5). ``config.UNIT_TYPE_TO_CLASS`` defines
exactly the 5 audit unit types, so the bridge has 5 rows and 5 distinct labels/targets.

Null/count columns alias as ``*_ct`` to dodge the ``nulls``/``both`` reserved-word
collision (test_export.py Pitfall 6); paths via ``config.GOLD_DIR / name`` + ``.as_posix()``.
"""

from __future__ import annotations

import duckdb
import pytest

from fleet_analytics import class_target, config


def test_class_target_rows(gold: duckdb.DuckDBPyConnection) -> None:
    """dim_class_target is the 5-row UNIT_TYPE bridge with 5 distinct class labels."""
    total, distinct = gold.execute(
        "SELECT COUNT(*), COUNT(DISTINCT class_label) FROM dim_class_target"
    ).fetchone()
    assert total == 5
    assert distinct == 5


@pytest.mark.parametrize(
    "class_label, expected",
    [("Light", 95), ("Medium", 92), ("Heavy", 85), ("Off-Road", 88), ("Other", 90)],
)
def test_class_target_value(
    gold: duckdb.DuckDBPyConnection, class_label: str, expected: int
) -> None:
    """Each audit class maps to its exact audit-cited target (never recalculated)."""
    target = gold.execute(
        "SELECT DISTINCT target FROM dim_class_target WHERE class_label = ?",
        [class_label],
    ).fetchone()[0]
    assert target == expected


def test_class_target_parquet_roundtrip(gold: duckdb.DuckDBPyConnection) -> None:
    """The committed Parquet re-reads via a second :memory: connection: Heavy -> 85."""
    class_target.write_class_target(gold)

    parquet_path = (config.GOLD_DIR / "dim_class_target.parquet").as_posix()
    rd = duckdb.connect(":memory:")
    try:
        heavy_target = rd.execute(
            "SELECT target FROM read_parquet(?) WHERE class_label = 'Heavy'",
            [parquet_path],
        ).fetchone()[0]
    finally:
        rd.close()

    assert heavy_target == 85
