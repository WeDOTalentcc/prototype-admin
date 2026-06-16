"""Tests for scripts/check_agent_mro_compliance.py — G-MRO sensor.

Verifica que todo agente que herda LangGraphReActBase também herda
TenantAwareAgentMixin, com a ordem correta de MRO (mixin primeiro).

Origem: Gap G (auditoria enterprise-readiness 2026-06-08).
"""
import textwrap
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from check_agent_mro_compliance import scan_file, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_file(tmp_path: Path, content: str) -> Path:
    """Escreve um arquivo .py temporário com o conteúdo fornecido."""
    f = tmp_path / "fake_agent.py"
    f.write_text(textwrap.dedent(content))
    return f


# ---------------------------------------------------------------------------
# Testes de detecção de violação (severity='error')
# ---------------------------------------------------------------------------

def test_missing_mixin_is_violation(tmp_path):
    """Agente que herda LangGraphReActBase SEM TenantAwareAgentMixin → erro."""
    f = _make_agent_file(tmp_path, """
        class MyAgent(LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    assert len(violations) == 1
    v = violations[0]
    assert v["severity"] == "error"
    assert v["klass"] == "MyAgent"
    assert "TenantAwareAgentMixin" in v["reason"]


def test_missing_mixin_with_extra_bases_is_violation(tmp_path):
    """Agente com múltiplas bases mas sem o mixin também é violação."""
    f = _make_agent_file(tmp_path, """
        class MyAgent(EnhancedAgentMixin, LangGraphReActBase, SomeOtherMixin):
            pass
    """)
    violations = scan_file(f)
    errors = [v for v in violations if v["severity"] == "error"]
    assert len(errors) == 1
    assert errors[0]["klass"] == "MyAgent"


def test_missing_mixin_fix_message_is_llm_friendly(tmp_path):
    """Mensagem de fix deve conter instrução acionável em linguagem natural."""
    f = _make_agent_file(tmp_path, """
        class StudioAgent(LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    assert violations
    fix_msg = violations[0]["fix"]
    # Deve conter o nome da classe e o mixin a adicionar
    assert "TenantAwareAgentMixin" in fix_msg
    assert "StudioAgent" in fix_msg
    # Deve ter instrução acionável ("adicione" ou a sintaxe class correta)
    assert "adicione" in fix_msg or "class StudioAgent(" in fix_msg


# ---------------------------------------------------------------------------
# Testes de aceitação (sem violação)
# ---------------------------------------------------------------------------

def test_correct_order_passes(tmp_path):
    """Mixin ANTES da base → correto, sem violação."""
    f = _make_agent_file(tmp_path, """
        class MyAgent(TenantAwareAgentMixin, LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    assert violations == []


def test_correct_order_with_extra_bases_passes(tmp_path):
    """Mixin antes da base com outros mixins também é aceito."""
    f = _make_agent_file(tmp_path, """
        class MyAgent(TenantAwareAgentMixin, EnhancedAgentMixin, LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    assert violations == []


def test_class_without_langraph_base_is_ignored(tmp_path):
    """Classes que NÃO herdam LangGraphReActBase são ignoradas."""
    f = _make_agent_file(tmp_path, """
        class PlainClass:
            pass

        class SomeService(BaseService):
            pass
    """)
    violations = scan_file(f)
    assert violations == []


def test_base_class_definition_itself_is_ignored(tmp_path):
    """A definição da própria LangGraphReActBase não dispara violação."""
    f = _make_agent_file(tmp_path, """
        class LangGraphReActBase:
            pass
    """)
    violations = scan_file(f)
    assert violations == []


# ---------------------------------------------------------------------------
# Testes de ordem incorreta (severity='warning')
# ---------------------------------------------------------------------------

def test_wrong_order_is_warning_not_error(tmp_path):
    """Mixin DEPOIS da base → warning (não blocking) mas reportado."""
    f = _make_agent_file(tmp_path, """
        class MyAgent(LangGraphReActBase, TenantAwareAgentMixin):
            pass
    """)
    violations = scan_file(f)
    assert len(violations) == 1
    assert violations[0]["severity"] == "warning"
    assert violations[0]["klass"] == "MyAgent"
    assert "_process_langgraph" in violations[0]["reason"] or "MRO" in violations[0]["reason"] or "precederá" in violations[0]["reason"]


def test_wrong_order_fix_suggests_reorder(tmp_path):
    """Fix de ordem errada sugere reordenamento."""
    f = _make_agent_file(tmp_path, """
        class BadOrderAgent(LangGraphReActBase, TenantAwareAgentMixin):
            pass
    """)
    violations = scan_file(f)
    assert violations
    fix_msg = violations[0]["fix"]
    assert "TenantAwareAgentMixin" in fix_msg
    assert "LangGraphReActBase" in fix_msg


# ---------------------------------------------------------------------------
# Testes de múltiplas classes no mesmo arquivo
# ---------------------------------------------------------------------------

def test_multiple_agents_one_violation(tmp_path):
    """Arquivo com 2 agentes: um correto, um sem mixin → apenas 1 violação."""
    f = _make_agent_file(tmp_path, """
        class GoodAgent(TenantAwareAgentMixin, LangGraphReActBase):
            pass

        class BadAgent(LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    assert len(violations) == 1
    assert violations[0]["klass"] == "BadAgent"


def test_multiple_agents_both_violated(tmp_path):
    """Dois agentes sem mixin → duas violações."""
    f = _make_agent_file(tmp_path, """
        class AgentA(LangGraphReActBase):
            pass

        class AgentB(LangGraphReActBase):
            pass
    """)
    violations = scan_file(f)
    errors = [v for v in violations if v["severity"] == "error"]
    assert len(errors) == 2
    klasses = {v["klass"] for v in errors}
    assert klasses == {"AgentA", "AgentB"}


# ---------------------------------------------------------------------------
# Testes de exit code (via main() com --root)
# ---------------------------------------------------------------------------

def test_exit_code_1_when_violations(tmp_path):
    """main() retorna exit 1 quando há violações de erro."""
    (tmp_path / "app").mkdir()
    agent_file = tmp_path / "app" / "bad_agent.py"
    agent_file.write_text(textwrap.dedent("""
        class BadAgent(LangGraphReActBase):
            pass
    """))
    import sys as _sys
    old_argv = _sys.argv[:]
    _sys.argv = ["check_agent_mro_compliance.py", "--root", str(tmp_path)]
    try:
        exit_code = main()
    finally:
        _sys.argv = old_argv
    assert exit_code == 1


def test_exit_code_0_when_no_violations(tmp_path):
    """main() retorna exit 0 quando todos os agentes são conformes."""
    (tmp_path / "app").mkdir()
    agent_file = tmp_path / "app" / "good_agent.py"
    agent_file.write_text(textwrap.dedent("""
        class GoodAgent(TenantAwareAgentMixin, LangGraphReActBase):
            pass
    """))
    import sys as _sys
    old_argv = _sys.argv[:]
    _sys.argv = ["check_agent_mro_compliance.py", "--root", str(tmp_path)]
    try:
        exit_code = main()
    finally:
        _sys.argv = old_argv
    assert exit_code == 0


def test_warn_only_exit_0_despite_violations(tmp_path):
    """--warn-only força exit 0 mesmo com violações."""
    (tmp_path / "app").mkdir()
    agent_file = tmp_path / "app" / "bad_agent.py"
    agent_file.write_text(textwrap.dedent("""
        class BadAgent(LangGraphReActBase):
            pass
    """))
    import sys as _sys
    old_argv = _sys.argv[:]
    _sys.argv = ["check_agent_mro_compliance.py", "--root", str(tmp_path), "--warn-only"]
    try:
        exit_code = main()
    finally:
        _sys.argv = old_argv
    assert exit_code == 0


# ---------------------------------------------------------------------------
# Teste de formato JSON
# ---------------------------------------------------------------------------

def test_json_output_structure(tmp_path, capsys):
    """--json produz estrutura com total/errors/warnings/violations."""
    import json as _json
    (tmp_path / "app").mkdir()
    agent_file = tmp_path / "app" / "bad_agent.py"
    agent_file.write_text(textwrap.dedent("""
        class BadAgent(LangGraphReActBase):
            pass
    """))
    import sys as _sys
    old_argv = _sys.argv[:]
    _sys.argv = ["check_agent_mro_compliance.py", "--root", str(tmp_path), "--json", "--warn-only"]
    try:
        main()
    finally:
        _sys.argv = old_argv

    captured = capsys.readouterr()
    data = _json.loads(captured.out)
    assert "total" in data
    assert "errors" in data
    assert "warnings" in data
    assert "violations" in data
    assert data["errors"] >= 1
    v = data["violations"][0]
    assert "file" in v
    assert "line" in v
    assert "klass" in v
    assert "severity" in v
    assert "reason" in v
    assert "fix" in v


# ---------------------------------------------------------------------------
# Testes de robustez (arquivos problemáticos)
# ---------------------------------------------------------------------------

def test_syntax_error_file_is_skipped_gracefully(tmp_path):
    """Arquivo com SyntaxError não deve explodir o sensor."""
    f = tmp_path / "broken.py"
    f.write_text("class Broken(LangGraphReActBase\n    # unclosed paren\n")
    violations = scan_file(f)
    assert violations == []  # retorna vazia, não lança exceção


def test_empty_file_produces_no_violations(tmp_path):
    """Arquivo vazio não gera violações."""
    f = tmp_path / "empty.py"
    f.write_text("")
    violations = scan_file(f)
    assert violations == []
