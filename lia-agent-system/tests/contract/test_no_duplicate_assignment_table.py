"""
Onda 3.B5 — pin do sensor check_no_duplicate_assignment_table.

Sensor é BLOCKING por default. Verifica que:
1. Exit 0 no estado canonical (baseline 0).
2. Detecta padrão `__tablename__ = "job_agent_assignments"` em qualquer model.
3. Detecta `op.create_table("job_agent_assignments", ...)` em alembic.
4. Honra marker `# DUPLICATE-TABLE-EXEMPT: <razão>`.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR = REPO_ROOT / "scripts" / "check_no_duplicate_assignment_table.py"


def _run_sensor(extra_args: list[str] = None) -> tuple[int, str]:
    """Executa o sensor canonical e retorna (exit_code, combined_output)."""
    args = [sys.executable, str(SENSOR)] + (extra_args or [])
    proc = subprocess.run(args, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return proc.returncode, proc.stdout + proc.stderr


def test_sensor_baseline_zero():
    """Baseline canonical: 0 violations no repo no momento da Onda 3."""
    rc, out = _run_sensor()
    assert rc == 0, f"Sensor falhou inesperadamente:\n{out}"
    assert "0 violations" in out or "OK" in out


def test_sensor_detects_banned_tablename(tmp_path, monkeypatch):
    """Model com __tablename__ banido é detectado."""
    fake_models_dir = tmp_path / "fake_pkg"
    fake_models_dir.mkdir()
    bad_model = fake_models_dir / "bad_model.py"
    bad_model.write_text(textwrap.dedent("""
        from sqlalchemy import Column, Integer
        class BadModel:
            __tablename__ = "job_agent_assignments"
            id = Column(Integer, primary_key=True)
    """))

    # Importar o módulo do sensor e chamar find_violations diretamente
    import importlib.util
    spec = importlib.util.spec_from_file_location("sensor_mod", SENSOR)
    sensor_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sensor_mod)

    violations = sensor_mod.find_violations(bad_model)
    assert len(violations) == 1
    assert violations[0]["name"] == "job_agent_assignments"
    assert violations[0]["kind"] == "model_tablename"


def test_sensor_detects_alembic_create_table(tmp_path):
    """alembic op.create_table com nome banido é detectado."""
    bad_migration = tmp_path / "fake_migration.py"
    bad_migration.write_text(textwrap.dedent("""
        from alembic import op
        import sqlalchemy as sa

        def upgrade():
            op.create_table(
                "pipeline_agent_assignments",
                sa.Column("id", sa.Integer, primary_key=True),
            )

        def downgrade():
            op.drop_table("pipeline_agent_assignments")
    """))

    import importlib.util
    spec = importlib.util.spec_from_file_location("sensor_mod2", SENSOR)
    sensor_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sensor_mod)

    violations = sensor_mod.find_violations(bad_migration)
    assert any(v["kind"] == "alembic_create_table" for v in violations)
    assert any(v["name"] == "pipeline_agent_assignments" for v in violations)


def test_sensor_honors_exempt_marker(tmp_path):
    """Marker `# DUPLICATE-TABLE-EXEMPT: ...` suprime a violation."""
    legacy_model = tmp_path / "legacy.py"
    legacy_model.write_text(textwrap.dedent("""
        from sqlalchemy import Column, Integer
        class Legacy:
            # DUPLICATE-TABLE-EXEMPT: rollback histórico Sprint 7C
            __tablename__ = "job_agent_assignments"
            id = Column(Integer, primary_key=True)
    """))

    import importlib.util
    spec = importlib.util.spec_from_file_location("sensor_mod3", SENSOR)
    sensor_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sensor_mod)

    violations = sensor_mod.find_violations(legacy_model)
    assert violations == [], f"Marker EXEMPT não respeitado: {violations}"
