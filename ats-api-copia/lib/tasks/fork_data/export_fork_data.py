#!/usr/bin/env python3
"""
Export fork data to JSON for Rails import.

Runs on the Replit fork to export PostgreSQL data as JSON files.
No fork app dependencies required -- only psycopg2.

Usage:
    pip install psycopg2-binary
    python export_fork_data.py

Output:
    ./fork_export/candidates.json
    ./fork_export/job_vacancies.json
    ./fork_export/users.json
    ./fork_export/vacancy_candidates.json
    ./fork_export/interviews.json
    ./fork_export/messages.json
    ./fork_export/conversations.json
"""

import os
import json
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://lia_user:lia_password@localhost:5432/lia_db",
)

OUTPUT_DIR = Path("./fork_export")

TABLES = [
    {"name": "candidates",          "expected": 64},
    {"name": "job_vacancies",       "expected": 111},
    {"name": "users",               "expected": 10},
    {"name": "vacancy_candidates",  "expected": 383},
    {"name": "interviews",          "expected": 27},
    {"name": "messages",            "expected": 211},
    {"name": "conversations",       "expected": 131},
]

# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------

class ForkEncoder(json.JSONEncoder):
    """Handle UUID, datetime, date, Decimal, bytes and other Postgres types."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            # Preserve precision: return float for simple values, str otherwise
            if obj == obj.to_integral_value():
                return int(obj)
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, memoryview):
            return bytes(obj).decode("utf-8", errors="replace")
        # UUIDs come back as strings from psycopg2 with RealDictCursor,
        # but just in case:
        if hasattr(obj, "hex") and hasattr(obj, "int"):
            return str(obj)
        return super().default(obj)


def serialize_row(row: dict) -> dict:
    """Ensure every value in a row dict is JSON-safe.

    psycopg2 with RealDictCursor already converts most Postgres types to
    Python equivalents.  JSONB columns come back as dicts/lists, UUIDs as
    strings, etc.  This pass catches anything the cursor missed.
    """
    cleaned = {}
    for key, value in row.items():
        if value is None:
            cleaned[key] = None
        elif isinstance(value, (dict, list)):
            # JSONB -- already native Python; keep as-is
            cleaned[key] = value
        elif isinstance(value, (datetime, date, Decimal, bytes, memoryview)):
            # Let the encoder handle it
            cleaned[key] = value
        else:
            cleaned[key] = value
    return cleaned

# ---------------------------------------------------------------------------
# Export logic
# ---------------------------------------------------------------------------

def export_table(cursor, table_name: str, output_dir: Path) -> int:
    """Export a single table to a JSON file.  Returns row count."""
    query = f'SELECT * FROM "{table_name}" ORDER BY created_at ASC'
    try:
        cursor.execute(query)
    except psycopg2.errors.UndefinedTable:
        # Table might not exist -- try without ordering
        cursor.connection.rollback()
        try:
            cursor.execute(f'SELECT * FROM "{table_name}"')
        except psycopg2.errors.UndefinedTable:
            cursor.connection.rollback()
            print(f"  WARNING: table '{table_name}' does not exist -- skipped")
            return 0

    rows = cursor.fetchall()
    data = [serialize_row(dict(row)) for row in rows]

    output_path = output_dir / f"{table_name}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=ForkEncoder, ensure_ascii=False, indent=2)

    return len(data)


def main():
    print("=" * 60)
    print("Fork Data Export")
    print("=" * 60)
    print(f"Database : {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print(f"Output   : {OUTPUT_DIR.resolve()}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Connect
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_session(readonly=True)
    except psycopg2.OperationalError as e:
        print(f"ERROR: Could not connect to database:\n  {e}")
        sys.exit(1)

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    total_rows = 0
    results = []

    for table_info in TABLES:
        table_name = table_info["name"]
        expected = table_info["expected"]

        count = export_table(cursor, table_name, OUTPUT_DIR)
        total_rows += count

        status = "OK" if count > 0 else "EMPTY/MISSING"
        delta = ""
        if count != expected and count > 0:
            delta = f" (expected {expected})"

        results.append((table_name, count, status, delta))
        print(f"  {table_name:25s} -> {count:>5d} records  [{status}]{delta}")

    cursor.close()
    conn.close()

    print()
    print("-" * 60)
    print(f"Total records exported: {total_rows}")
    print(f"Files written to: {OUTPUT_DIR.resolve()}")
    print()

    # Summary of output files
    print("Output files:")
    for table_info in TABLES:
        path = OUTPUT_DIR / f"{table_info['name']}.json"
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"  {path.name:30s}  {size_kb:>8.1f} KB")

    print()
    print("Export complete. Copy the fork_export/ directory to the Rails")
    print("project at lib/tasks/fork_data/ and run:")
    print("  FORK_DATA_DIR=lib/tasks/fork_data/fork_export rails fork:import")


if __name__ == "__main__":
    main()
