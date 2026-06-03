"""Gold export (MODEL-04): the five Gold tables -> type-preserving Parquet + readable CSV.

This is the Power BI handoff surface. Phases 3–4 consume these files, so the
contract is *type fidelity*: the COPY must preserve

- ``AVAILABILITY_YTD`` as DOUBLE with its 209 genuine NULLs (never 0-filled),
- ``IN_SERV_DT`` as DATE,
- boolean derived flags (e.g. ``is_weekend`` on ``dim_date``) as BOOLEAN.

Parquet is the **primary** output (columnar, compressed, type-preserving — almost
no re-typing in Power Query). CSV is the **readable secondary** for inspection;
DuckDB writes blank cells for SQL NULL, so a re-read keeps the 209 nulls NULL.

No COALESCE / fillna / aggregation anywhere — ``COPY (SELECT * FROM {t})`` ships
each Gold table verbatim, so the locked "exclude, never impute" decision survives
the export boundary.

Security note: the table names interpolated into the COPY statement come *only*
from the internal ``config.GOLD_TABLES`` constant and output paths from
``config.GOLD_DIR`` — no external/user value ever reaches the SQL string, so the
f-string interpolation is safe (02-RESEARCH.md Security note).
"""

from __future__ import annotations

import duckdb

from fleet_analytics import config


def write_gold(con: duckdb.DuckDBPyConnection) -> None:
    """COPY each of the five Gold tables to ``config.GOLD_DIR`` as Parquet + CSV.

    Ensures the output directory exists, then writes ``{table}.parquet``
    (FORMAT PARQUET) and ``{table}.csv`` (FORMAT CSV, HEADER) for every table in
    ``config.GOLD_TABLES`` — 10 files total. Run after ``model.build_all(con)``.

    Types and NULLs pass through untouched: DOUBLE+NULLs / DATE / BOOLEAN are
    preserved natively by COPY. No COALESCE, fill, or aggregation.
    """
    config.GOLD_DIR.mkdir(parents=True, exist_ok=True)

    for t in config.GOLD_TABLES:
        p = (config.GOLD_DIR / t).as_posix()
        con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.parquet' (FORMAT PARQUET)")
        con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.csv' (FORMAT CSV, HEADER)")
