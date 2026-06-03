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
    fixture by adding a single ``model.build_all(con)`` line after the transform
    call — the import is already in place so that is the only change needed.
    """
    from fleet_analytics import transform  # noqa: F401  (model added in Plan 02)

    transform.build_all(con)
    return con
