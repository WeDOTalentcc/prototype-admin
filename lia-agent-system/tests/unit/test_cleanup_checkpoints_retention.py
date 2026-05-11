"""
Smoke test do cleanup_checkpoints_retention.py (Onda 4.D2).

Disciplinas: TDD-IA + compliance-risk (LGPD Art. 16).
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)


def _load_script():
    here = Path(__file__).resolve()
    project_root = here.parents[2]
    script = project_root / "scripts" / "cleanup_checkpoints_retention.py"
    spec = importlib.util.spec_from_file_location("cleanup_retention", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cleanup_retention"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_retention_script_imports_and_has_cleanup_fn():
    """Smoke: script carrega e expoe cleanup()."""
    mod = _load_script()
    assert callable(mod.cleanup), "cleanup() function missing"
    assert callable(mod.main), "main() function missing"


def test_retention_returns_zero_threads_in_conservative_fallback():
    """Quando track_commit_timestamp off, fallback conservador nao apaga.

    Sensor de seguranca: garante que script nao apaga state em ambiente
    Replit (default) onde pg_xact_commit_timestamp nao esta disponivel.
    """
    mod = _load_script()
    stats = mod.cleanup(days=90, dry_run=True)
    assert isinstance(stats, dict)
    assert stats["threads"] == 0, (
        f"Conservative fallback should NOT identify threads to delete "
        f"when track_commit_timestamp is off. Got {stats}"
    )
    assert stats["by_table"] == {}, (
        f"by_table should be empty in conservative fallback; got {stats}"
    )


def test_retention_dry_run_does_not_modify_postgres():
    """Sanity: --dry-run never executes DELETE."""
    import psycopg
    from lia_config.config import settings
    sync_url = (
        settings.DATABASE_URL
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
    )

    with psycopg.connect(sync_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM checkpoints")
            before = cur.fetchone()[0]

    mod = _load_script()
    mod.cleanup(days=90, dry_run=True)

    with psycopg.connect(sync_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM checkpoints")
            after = cur.fetchone()[0]

    assert before == after, (
        f"--dry-run modified checkpoints! before={before} after={after}"
    )
