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
