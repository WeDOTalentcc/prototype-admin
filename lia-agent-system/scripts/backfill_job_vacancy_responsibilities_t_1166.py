"""T-1166 — Backfill `job_vacancies.responsibilities` from the JD that
originated each vacancy.

Strategy (additive, idempotent, dry-run by default):

1. For every `job_vacancies` row with `responsibilities IS NULL OR responsibilities = '{}'`
   AND `additional_data->>'imported_jd_id'` set (i.e. created via ATS import),
   read the linked `imported_job_descriptions.responsibilities` and copy it.
2. Vagas without a linked imported JD are left with the safe default `[]`
   (migration 132 server_default). We do NOT try to re-derive duties from the
   raw description text — that would be a guess, and the wizard will repopulate
   it on the next edit/save.
3. The script reports counts BEFORE doing any UPDATE. Pass `--apply` to commit.

Usage::

    python -m scripts.backfill_job_vacancy_responsibilities_t_1166        # dry-run
    python -m scripts.backfill_job_vacancy_responsibilities_t_1166 --apply

Safe to re-run: a vaga that already has a non-empty `responsibilities` array
is never touched.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as exc:  # pragma: no cover
    print(f"[fatal] missing dependency: {exc}", file=sys.stderr)
    raise


COUNT_SQL = text(
    """
    SELECT
        COUNT(*) FILTER (
            WHERE jv.responsibilities IS NULL OR cardinality(jv.responsibilities) = 0
        ) AS missing_total,
        COUNT(*) FILTER (
            WHERE (jv.responsibilities IS NULL OR cardinality(jv.responsibilities) = 0)
              AND (jv.additional_data ->> 'imported_jd_id') IS NOT NULL
        ) AS missing_with_imported_jd
    FROM job_vacancies jv
    """
)


UPDATE_SQL = text(
    """
    UPDATE job_vacancies jv
    SET responsibilities = ijd.responsibilities,
        updated_at = NOW()
    FROM imported_job_descriptions ijd
    WHERE (jv.additional_data ->> 'imported_jd_id')::text = ijd.id::text
      -- T-1166 — defense-in-depth: only copy when the imported JD and the
      -- vacancy belong to the SAME tenant. Even if data corruption left a
      -- dangling imported_jd_id pointing at another tenant's row, this guard
      -- prevents responsibilities from leaking across companies.
      AND ijd.company_id = jv.company_id
      AND (jv.responsibilities IS NULL OR cardinality(jv.responsibilities) = 0)
      AND ijd.responsibilities IS NOT NULL
      AND cardinality(ijd.responsibilities) > 0
    RETURNING jv.id
    """
)


async def _run(apply: bool, database_url: str) -> int:
    engine = create_async_engine(database_url, future=True)
    try:
        # Count phase — read-only, separate connection so it cannot interfere
        # with the UPDATE transaction below.
        async with engine.connect() as conn:
            counts: dict[str, Any] = (
                (await conn.execute(COUNT_SQL)).mappings().one()
            )
        print(
            "[T-1166] missing responsibilities total      :",
            counts["missing_total"],
        )
        print(
            "[T-1166] missing AND has imported_jd_id link :",
            counts["missing_with_imported_jd"],
        )

        if not apply:
            print(
                "[T-1166] dry-run only — re-run with --apply to perform the UPDATE."
            )
            return 0

        # Single, atomic UPDATE block — engine.begin() owns the transaction.
        async with engine.begin() as conn:
            result = await conn.execute(UPDATE_SQL)
            updated_ids = [row[0] for row in result.fetchall()]
        print(f"[T-1166] backfilled {len(updated_ids)} vagas.")
        for vid in updated_ids[:20]:
            print(f"  - {vid}")
        if len(updated_ids) > 20:
            print(f"  ... ({len(updated_ids) - 20} more)")
    finally:
        await engine.dispose()
    return 0


def _build_database_url() -> str:
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("LIA_DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
    )
    if not url:
        raise SystemExit(
            "[T-1166] DATABASE_URL (or LIA_DATABASE_URL / POSTGRES_URL) is not "
            "set. Export it pointing at the target environment before running."
        )
    # asyncpg driver coercion (mirror of app.db config)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg accepts libpq-style `sslmode` values, but SQLAlchemy passes
    # query args through as connect() kwargs, and asyncpg's `connect()` rejects
    # `sslmode=` as a keyword (it expects `ssl=...`). Strip the query string
    # entirely — local dev runs without TLS and managed prod URLs typically
    # arrive without sslmode. If you need TLS in prod, configure it via the
    # SQLAlchemy `connect_args={"ssl": ...}` block in the calling code.
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    parts = urlsplit(url)
    if parts.query:
        params = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k != "sslmode"
        ]
        url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment)
        )
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the UPDATE (default: dry-run, count-only).",
    )
    args = parser.parse_args()
    return asyncio.run(_run(apply=args.apply, database_url=_build_database_url()))


if __name__ == "__main__":
    sys.exit(main())
