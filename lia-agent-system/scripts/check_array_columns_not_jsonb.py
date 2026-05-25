#!/usr/bin/env python3
"""Sensor: verify ORM array columns are not stored as jsonb in Postgres.

Catches ORM<->DB column type drift that causes DatatypeMismatchError on INSERT.
Pattern: migration creates column as jsonb, ORM declares ARRAY(String), silent
divergence until first full INSERT (cold-start tenant). Bug 2026-05-25 canonical
example: company_culture_profiles.default_languages blocked all first-saves.

Usage:
  python scripts/check_array_columns_not_jsonb.py            # warn-only
  python scripts/check_array_columns_not_jsonb.py --blocking  # exit 1 if violations

Exit codes: 0 = clean, 1 = violations (--blocking only)
"""
import argparse
import os
import sys

TABLES_TO_CHECK: dict[str, list[str]] = {
    "company_culture_profiles": [
        "values",
        "evp_bullets",
        "core_competencies",
        "analyzed_pages",
        "locations",
        "tech_stack",
        "default_languages",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("SKIP: DATABASE_URL not set")
        return 0

    try:
        import psycopg2
    except ImportError:
        print("SKIP: psycopg2 not installed")
        return 0

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    violations: list[str] = []

    for table, columns in TABLES_TO_CHECK.items():
        for col in columns:
            cur.execute(
                """
                SELECT data_type, udt_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                """,
                (table, col),
            )
            row = cur.fetchone()
            if row is None:
                violations.append(f"{table}.{col}: column not found in DB")
                continue
            data_type, udt_name = row
            # Postgres: varchar[] -> data_type='ARRAY', udt_name='_varchar'
            # jsonb    -> data_type='jsonb',  udt_name='jsonb'
            if data_type == "jsonb" or udt_name == "jsonb":
                violations.append(
                    f"{table}.{col}: DB type is jsonb but ORM expects ARRAY(String) "
                    f"-> Fix: run migration to ALTER COLUMN ... TYPE character varying[]"
                )

    cur.close()
    conn.close()

    total_checked = sum(len(cols) for cols in TABLES_TO_CHECK.values())
    if violations:
        print(f"FAIL: Array column type drift ({len(violations)} violation(s) / {total_checked} checked):")
        for v in violations:
            print(f"  {v}")
        if args.blocking:
            return 1
    else:
        print(f"OK: {total_checked} array columns are character varying[] (not jsonb)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
