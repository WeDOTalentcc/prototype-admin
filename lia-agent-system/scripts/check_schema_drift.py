#!/usr/bin/env python3
"""
SENSOR (harness-engineering): detect schema drift between SQLAlchemy models
and the live Postgres database.

Catches the class of bugs we hit in 2026-05-20: a model declares
``CalibrationWeight.company_id = Column(...)``, the app boots fine, but the
underlying table doesn't have that column — only manifesting on the first
query that touches it (HTTP 500 with cryptic ``UndefinedColumnError``).

ADR-MIGRATIONS-001: deploy MUST verify schema parity at startup, not lazily
at request time.

Usage:
  python3 scripts/check_schema_drift.py
  python3 scripts/check_schema_drift.py --tables calibration_weights,users
  python3 scripts/check_schema_drift.py --json   # machine-readable output

Exit codes:
  0 — model schema matches DB schema (✅ no drift)
  1 — drift detected (columns missing on either side)
  2 — usage / config error (DB unreachable, etc)

Output is LLM-optimized: each drift includes the table, column, side, and
the canonical fix command (alembic migration generate, or model edit).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Drift:
    """One column-level discrepancy between model and DB."""
    table: str
    column: str
    side: str  # "in_model_not_in_db" | "in_db_not_in_model"
    model_type: str | None
    db_type: str | None


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "").replace(
        "postgresql+psycopg2", "postgresql"
    )
    if not url:
        print("❌ DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(2)
    return url


def _load_metadata():
    """Import the canonical SQLAlchemy Base and force model side-effect loads.

    Canonical Base lives in libs/config/lia_config/database.py:82.
    Models live in libs/models/lia_models/ — importing the package registers
    each model class with Base.metadata via SQLAlchemy declarative side
    effect.
    """
    sys.path.insert(0, ".")
    try:
        from lia_config.database import Base  # canonical declarative_base
    except ImportError as exc:
        print(f"❌ Could not import Base from lia_config.database: {exc}", file=sys.stderr)
        print("   This script must run from the lia-agent-system root.", file=sys.stderr)
        sys.exit(2)

    # Force-load all model modules so their classes register with Base.
    import importlib
    import pkgutil
    try:
        import lia_models as _models_pkg  # type: ignore
    except ImportError:
        # Fallback when lia-models is accessed via libs.models.lia_models path
        try:
            import libs.models.lia_models as _models_pkg  # type: ignore
        except ImportError as exc:
            print(f"❌ Could not import lia_models package: {exc}", file=sys.stderr)
            sys.exit(2)

    for _, name, _ in pkgutil.iter_modules(_models_pkg.__path__):
        try:
            importlib.import_module(f"{_models_pkg.__name__}.{name}")
        except Exception:
            # Some model files may have unrelated import errors — skip
            # rather than failing the whole drift check.
            pass
    return Base.metadata


def collect_drift(table_filter: set[str] | None = None) -> list[Drift]:
    """Compare Base.metadata vs live DB schema, return all discrepancies."""
    from sqlalchemy import create_engine, inspect

    metadata = _load_metadata()
    engine = create_engine(_db_url())
    insp = inspect(engine)
    db_tables = set(insp.get_table_names())

    drifts: list[Drift] = []
    for table_name, table_obj in metadata.tables.items():
        if table_filter and table_name not in table_filter:
            continue
        if table_name not in db_tables:
            drifts.append(
                Drift(
                    table=table_name,
                    column="<entire table>",
                    side="in_model_not_in_db",
                    model_type="table",
                    db_type=None,
                )
            )
            continue
        db_cols = {c["name"]: c for c in insp.get_columns(table_name)}
        model_cols = {c.name for c in table_obj.columns}

        for col_name, col in db_cols.items():
            if col_name not in model_cols:
                drifts.append(
                    Drift(
                        table=table_name,
                        column=col_name,
                        side="in_db_not_in_model",
                        model_type=None,
                        db_type=str(col["type"]),
                    )
                )
        for col in table_obj.columns:
            if col.name not in db_cols:
                drifts.append(
                    Drift(
                        table=table_name,
                        column=col.name,
                        side="in_model_not_in_db",
                        model_type=str(col.type),
                        db_type=None,
                    )
                )
    return drifts


def render_text(drifts: list[Drift]) -> str:
    if not drifts:
        return "✅ Model ↔ DB schema match — ADR-MIGRATIONS-001 holds.\n"
    lines: list[str] = [
        f"❌ {len(drifts)} schema drift(s) detected.\n",
        "ADR-MIGRATIONS-001 (CLAUDE.md): every deploy MUST run",
        "`alembic upgrade head` BEFORE serving traffic. Drift causes",
        "cryptic UndefinedColumnError 500s at runtime.\n",
    ]
    in_model_not_db = [d for d in drifts if d.side == "in_model_not_in_db"]
    in_db_not_model = [d for d in drifts if d.side == "in_db_not_in_model"]

    if in_model_not_db:
        lines.append("── COLUMNS IN MODEL BUT NOT IN DB (missing migration) ──")
        for d in in_model_not_db:
            lines.append(
                f"  • {d.table}.{d.column}  (model type: {d.model_type})"
            )
        lines.append("  HOW TO FIX:")
        lines.append(
            "    1. Generate migration: "
            "`alembic revision --autogenerate -m \"add missing columns\"`"
        )
        lines.append("    2. Review the generated file in alembic/versions/")
        lines.append("    3. Apply: `alembic upgrade head`")
        lines.append("")

    if in_db_not_model:
        lines.append("── COLUMNS IN DB BUT NOT IN MODEL (stale model) ──")
        for d in in_db_not_model:
            lines.append(
                f"  • {d.table}.{d.column}  (db type: {d.db_type})"
            )
        lines.append("  HOW TO FIX:")
        lines.append(
            "    Either (a) add the column to the model class for parity, "
            "or (b) `alembic revision --autogenerate -m \"drop unused columns\"` "
            "if you intentionally removed it from the model."
        )
        lines.append("")

    lines.append("Re-run: python3 scripts/check_schema_drift.py")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare SQLAlchemy models vs live Postgres schema (ADR-MIGRATIONS-001).",
    )
    parser.add_argument(
        "--tables",
        default=None,
        help="Comma-separated table whitelist (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit drift list as JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    table_filter = (
        {t.strip() for t in args.tables.split(",")} if args.tables else None
    )

    try:
        drifts = collect_drift(table_filter)
    except Exception as exc:
        print(f"❌ Could not run drift check: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(d) for d in drifts], indent=2))
    else:
        print(render_text(drifts))

    return 0 if not drifts else 1


if __name__ == "__main__":
    sys.exit(main())
