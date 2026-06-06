"""SHIP-01 — single one-command orchestrator: ingest -> transform -> model -> export -> class_target -> kpi snapshot.

This module is pure wiring. It introduces NO new SQL and NO f-string interpolation
of its own — it simply calls the existing, already-tested builder/writer functions
(each ``def name(con: duckdb.DuckDBPyConnection)``) in dependency order on ONE shared
in-memory DuckDB connection, then closes it in a ``finally`` block. The call order
mirrors the ``tests/conftest.py`` ``gold`` fixture (transform -> model -> kpis ->
class_target), extended with ``ingest`` first and the ``write_*`` exporters interleaved.

Because the run reuses a single connection, the in-memory Gold tables built by
``model.build_all`` are reused by ``kpis.build_all`` (``kpis.load_gold_views`` is
idempotent — it skips Gold names already present as in-DB tables), so there is no
Parquet re-read mid-run.

Security note: ``pipeline.py`` authors no SQL string — the "no external/user value
reaches the SQL string" guarantee held by ``export.py`` / ``kpis.py`` /
``class_target.py`` is preserved (T-6-01).

Run it: ``uv run python -m fleet_analytics.pipeline``.
"""

from __future__ import annotations

import duckdb

from fleet_analytics import class_target, export, ingest, kpis, model, transform


def main() -> None:
    """Run the full chain end-to-end on one connection: ``uv run python -m fleet_analytics.pipeline``."""
    con = duckdb.connect()
    try:
        ingest.ingest_bronze(con)
        transform.build_all(con)
        model.build_all(con)
        export.write_gold(con)
        class_target.build_class_target(con)
        class_target.write_class_target(con)
        kpis.build_all(con)
        kpis.write_kpi_snapshot(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
