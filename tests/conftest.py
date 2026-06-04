"""Shared pytest fixtures.

A single session-scoped in-memory DuckDB connection with the three Bronze tables
ingested once (Open Question 1 recommendation: :memory: for tests — fast, no stale
state). Every test in the suite queries this connection.
"""

import duckdb
import pytest

from fleet_analytics.ingest import ingest_bronze


@pytest.fixture(scope="session")
def con() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    ingest_bronze(connection)
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def gold(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """Build the Phase-2 staging (and later Gold) layer once on the Bronze ``con``.

    Depends on ``con`` so Bronze is ingested only once per session, then the
    transform builders run on the same in-memory connection. Plan 02 extends this
    fixture by adding a single ``kpis.build_all(con)`` line after the model call —
    mirroring how Plan 02 of Phase 2 added the ``model.build_all(con)`` line — so the
    KPI layer (every Domain A/B KPI table + the compute-time fail-fast guards) is
    built once per session for ``tests/test_kpis.py`` to assert against.

    Phase 4 Plan 01 extends this same chain by adding a single
    ``class_target.build_class_target(con)`` line after ``kpis.build_all(con)`` — same
    precedent — so ``tests/test_class_target.py`` can assert against the in-DB
    ``dim_class_target`` reference dimension.
    """
    from fleet_analytics import class_target, kpis, model, transform

    transform.build_all(con)
    model.build_all(con)
    kpis.build_all(con)
    class_target.build_class_target(con)
    return con
