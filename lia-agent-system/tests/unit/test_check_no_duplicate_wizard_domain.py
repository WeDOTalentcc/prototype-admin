"""
Sensor-de-sensor — testes do script check_no_duplicate_wizard_domain.py
(Onda 4.D4 do PLAN_FIX_wizard_memory_loss 2026-05-10).

Aplica TDD ao proprio sensor: garante que ele detecta corretamente
duplicacao real e respeita o marker CANONICAL-EXEMPT. Sensor sem teste
e sensor que regride silenciosamente.

Disciplinas CLAUDE.md aplicadas:
  - TDD-IA: cobre o caminho feliz + edge cases do sensor.
  - harness-engineering: meta-sensor (sensor que protege o sensor).
"""
from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest


def _load_script():
    """Carrega o script como modulo Python para teste in-process."""
    here = Path(__file__).resolve()
    project_root = here.parents[2]  # tests/unit/.. -> lia-agent-system/
    script = project_root / "scripts" / "check_no_duplicate_wizard_domain.py"
    spec = importlib.util.spec_from_file_location("check_no_dup_wizard", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_no_dup_wizard"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return p


def test_sensor_returns_zero_when_single_domain(tmp_path, capsys):
    """OK quando ha apenas um dominio canonical."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        class JobCreationGraph:
            pass
        def parsed_title(): pass
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains"])
    out = capsys.readouterr().out
    assert rc == 0, f"Expected 0 violations; got rc={rc}\n{out}"
    assert "0 violations" in out


def test_sensor_detects_duplication_across_domains(tmp_path, capsys):
    """VIOLATION quando >= 2 dominios implementam a capability."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        class JobCreationGraph:
            pass
        def parsed_title(): return "x"
    """)
    _write(tmp_path, "app/domains/job_management/agents/job_wizard_graph.py", """
        from langgraph.graph import StateGraph
        class JobWizardGraph:
            pass
        def jd_enrichment(): return "y"
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains"])
    out = capsys.readouterr().out
    assert rc == 1, f"Expected violation (rc=1); got rc={rc}\n{out}"
    assert "VIOLATION" in out
    assert "vacancy_wizard" in out
    assert "job_creation" in out
    assert "job_management" in out


def test_sensor_respects_canonical_exempt_marker(tmp_path, capsys):
    """EXEMPT marker no header faz arquivo nao contar como dominio adicional."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        class JobCreationGraph: pass
        def parsed_title(): return "x"
    """)
    _write(tmp_path, "app/domains/job_management/agents/job_wizard_graph.py", """
        # CANONICAL-EXEMPT: legacy HITL resume path; consolidacao Onda 4.D1
        from langgraph.graph import StateGraph
        class JobWizardGraph: pass
        def jd_enrichment(): return "y"
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains"])
    out = capsys.readouterr().out
    assert rc == 0, f"Expected 0 (exempt); got rc={rc}\n{out}"


def test_sensor_warn_only_returns_zero_with_violations(tmp_path, capsys):
    """--warn-only converte exit code para 0 mas ainda reporta violations."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        class JobCreationGraph: pass
        def parsed_title(): return "x"
    """)
    _write(tmp_path, "app/domains/job_management/agents/job_wizard_graph.py", """
        from langgraph.graph import StateGraph
        class JobWizardGraph: pass
        def jd_enrichment(): return "y"
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains", "--warn-only"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "VIOLATION" in out
    assert "warn-only" in out


def test_sensor_ignores_files_with_only_one_hint(tmp_path, capsys):
    """Arquivo com apenas STRUCTURAL OU apenas SEMANTIC nao conta."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        # estructural mas sem semantic
        class FooBar: pass
    """)
    _write(tmp_path, "app/domains/job_management/agents/job_wizard_graph.py", """
        # apenas semantic, sem structural
        '''parsed_title parsed_seniority criar_vaga jd_enrichment'''
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains"])
    out = capsys.readouterr().out
    assert rc == 0, out


def test_sensor_ignores_test_subdirs(tmp_path, capsys):
    """Arquivos em /tests/ dentro de dominio nao contam (sao testes)."""
    _write(tmp_path, "app/domains/job_creation/graph.py", """
        from langgraph.graph import StateGraph
        class JobCreationGraph: pass
        def parsed_title(): return "x"
    """)
    _write(tmp_path, "app/domains/job_management/tests/test_job_wizard_graph.py", """
        from langgraph.graph import StateGraph
        class TestJobWizardGraph:
            def test_parsed_title(self): pass
        # jd_enrichment wsi_questions
    """)
    mod = _load_script()
    import os
    os.chdir(tmp_path)
    rc = mod.main(["app/domains"])
    out = capsys.readouterr().out
    assert rc == 0, f"tests/ dir should be ignored; got rc={rc}\n{out}"
