"""Testes para o sensor check_agent_base_class.py (ADR-031 §4).

Verifica que o sensor detecta corretamente violations e respeita isenções.
7 testes unitários.
"""
import sys
import tempfile
from pathlib import Path

import pytest

# Adiciona scripts/ ao path para importar o sensor
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from check_agent_base_class import (
    COMPLIANT_BASE_CLASSES,
    check_r1_base_class,
    check_r3_silent_fallback,
)


def _make_temp_file(content: str) -> Path:
    """Cria arquivo .py temporário com conteúdo dado."""
    f = tempfile.NamedTemporaryFile(
        suffix=".py", delete=False, dir=tempfile.gettempdir(), mode="w", encoding="utf-8"
    )
    f.write(content)
    f.flush()
    f.close()
    return Path(f.name)


class TestR1BaseClass:
    """R1: agentes devem herdar de classe compliance-aware."""

    def test_compliant_class_langgraph_no_violation(self):
        """Agente herdando LangGraphReActBase não gera violation."""
        code = "class MyAgent(LangGraphReActBase): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        assert violations == [], f"Esperado 0 violations, obteve: {violations}"

    def test_compliant_class_compliance_domain_no_violation(self):
        """Agente herdando ComplianceDomainPrompt não gera violation."""
        code = "class MyDomainAgent(ComplianceDomainPrompt): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        assert violations == [], f"Esperado 0 violations, obteve: {violations}"

    def test_missing_base_class_generates_r1_violation(self):
        """Agente herdando apenas 'object' gera R1 violation."""
        code = "class PolicySetupAgent(object): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        assert len(violations) == 1
        assert "R1" in violations[0]
        assert "PolicySetupAgent" in violations[0]

    def test_indirect_subclass_compliant(self):
        """Agente herdando de subclasse indireta conhecida não gera violation."""
        code = "class MyKanbanAgent(KanbanReActAgent): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        # KanbanReActAgent está em COMPLIANT_BASE_CLASSES
        assert violations == [], f"Esperado 0 violations, obteve: {violations}"

    def test_non_agent_class_skipped(self):
        """Classe sem sufixo Agent/Runtime/etc não é verificada."""
        code = "class UtilityHelper(object): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        assert violations == []

    def test_test_class_skipped(self):
        """Classes de teste são ignoradas pelo sensor."""
        code = "class TestMyAgent(LangGraphReActBase): pass"
        f = _make_temp_file(code)
        violations = check_r1_base_class(f)
        assert violations == []


class TestR3SilentFallback:
    """R3: 'except Exception: pass' é silent fallback proibido."""

    def test_except_exception_pass_generates_r3_violation(self):
        """'except Exception: pass' gera R3 violation."""
        code = "try:\n    x()\nexcept Exception:\n    pass\n"
        f = _make_temp_file(code)
        violations = check_r3_silent_fallback(f)
        assert len(violations) == 1
        assert "R3" in violations[0]

    def test_except_with_logging_no_violation(self):
        """'except Exception as e: logger.error(...)' não gera violation."""
        code = "try:\n    x()\nexcept Exception as e:\n    logger.error(str(e))\n"
        f = _make_temp_file(code)
        violations = check_r3_silent_fallback(f)
        assert violations == []

    def test_specific_exception_with_pass_no_violation(self):
        """'except ValueError: pass' não gera violation (específico, não genérico)."""
        code = "try:\n    x()\nexcept ValueError:\n    pass\n"
        f = _make_temp_file(code)
        violations = check_r3_silent_fallback(f)
        assert violations == []

    def test_exempt_marker_suppresses_violation(self):
        """Marcador ADR-031-R3-EXEMPT suprime a violation."""
        code = (
            "try:\n    x()\nexcept Exception:\n"
            "    # ADR-031-R3-EXEMPT: graceful degradation — optional feature\n"
            "    pass\n"
        )
        f = _make_temp_file(code)
        violations = check_r3_silent_fallback(f)
        assert violations == [], f"Esperado 0 violations com EXEMPT, obteve: {violations}"

    def test_r3_shorthand_exempt_suppresses_violation(self):
        """Marcador R3-EXEMPT (shorthand) suprime a violation."""
        code = (
            "try:\n    x()\nexcept Exception:\n"
            "    # R3-EXEMPT: non-critical telemetry, skip on error\n"
            "    pass\n"
        )
        f = _make_temp_file(code)
        violations = check_r3_silent_fallback(f)
        assert violations == [], f"Esperado 0 violations com R3-EXEMPT, obteve: {violations}"


class TestCompliantBaseClassesSet:
    """Verifica integridade da lista COMPLIANT_BASE_CLASSES."""

    def test_primary_bases_present(self):
        """Classes base primárias devem estar no conjunto."""
        assert "LangGraphReActBase" in COMPLIANT_BASE_CLASSES
        assert "ComplianceDomainPrompt" in COMPLIANT_BASE_CLASSES

    def test_known_indirect_subclasses_present(self):
        """Subclasses indiretas conhecidas do projeto devem estar no conjunto."""
        assert "SourcingReActAgent" in COMPLIANT_BASE_CLASSES
        assert "KanbanReActAgent" in COMPLIANT_BASE_CLASSES
        assert "PipelineTransitionAgent" in COMPLIANT_BASE_CLASSES
