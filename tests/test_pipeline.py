"""SHIP-01 — integration smoke test for the one-command orchestrator.

This is a single, fast integration smoke test proving ``pipeline.main()`` runs the
full chain end-to-end and produces the Power BI handoff artifacts: the 6 Gold Parquet
files (``config.GOLD_TABLES`` + ``dim_class_target``) and the committed KPI snapshot
``data/kpi/kpi_values.json``.

It deliberately does NOT re-assert the deep fidelity invariants — the pooled-mean !=
mean-of-class-means guard, the 2020 < 2019 COVID-dip, the 7229 ferry max, the 209-null
preservation, and the 2080/6 join integrity all live in ``test_kpis.py`` /
``test_export.py`` / ``test_join_integrity.py``. This test only confirms the
orchestrator wires those builders together and writes the expected files (the file-
existence idiom mirrors ``test_export.py::test_ten_files_written``).
"""

from __future__ import annotations

from fleet_analytics import config, pipeline


def test_pipeline_runs_and_writes_gold() -> None:
    """pipeline.main() runs the full chain and writes all 6 Gold Parquet + the KPI snapshot."""
    pipeline.main()

    for t in [*config.GOLD_TABLES, "dim_class_target"]:
        assert (config.GOLD_DIR / f"{t}.parquet").exists(), f"{t}.parquet missing"

    assert (config.KPI_DIR / "kpi_values.json").exists(), "kpi_values.json missing"
