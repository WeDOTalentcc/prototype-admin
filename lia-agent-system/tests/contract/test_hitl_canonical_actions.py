"""
Contract tests: HITL canonical actions — single source of truth.

Phase 3 (RED): estes testes DEVEM FALHAR antes da implementação do canonical.
Phase 4 (GREEN): passam após criar app/shared/hitl/hitl_canonical_actions.py.

Testa:
  T-a: ações de alto risco (reject, send_email, delete, bulk_*) estão no canonical
  T-b: todos os agentes importam do mesmo canonical (sem frozensets locais divergentes)
  T-c: gate OFF (LIA_HITL_GATE não setado) → gate não bloqueia (zero regressão)
  T-d: canonical frozenset é frozenset[str] (tipo correto)
  T-e: todo elemento do canonical é string não-vazia
  T-f: canonical não tem duplicatas entre domínios (union coerente)
  T-g: HITL_REQUIRED_ACTIONS existe e é importável do canonical
"""
from __future__ import annotations

import ast
import os
import pathlib
import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
_CANONICAL_MODULE = _ROOT / "app" / "shared" / "hitl" / "hitl_canonical_actions.py"


# ---------------------------------------------------------------------------
# T-a: high-risk actions must be present in canonical frozenset
# ---------------------------------------------------------------------------

HIGH_RISK_ACTIONS = {
    # Rejection — irreversible external communication
    "bulk_reject_candidates",
    "auto_reject_low_score",
    "auto_reject_funnel",
    "reject_candidate",
    "bulk_reject",
    "ats_reject_application",
    # External communication
    "send_batch_communication",
    "send_report_email",
    "bulk_sourcing_outreach",
    # Destructive job mutations
    "delete_vacancy",
    "delete_automation",
    "publish_vacancy",
    "unpublish_vacancy",
    # Bulk moves (irreversible at scale)
    "bulk_move_candidates",
    "bulk_move",
    "batch_move_candidates",
    "bulk_candidate_move",
    # ATS write ops (external system mutation)
    "sync_to_ats",
    "ats_create_application",
    "ats_update_application",
    # Automation mutations
    "activate_automation",
    "deactivate_automation",
    "bulk_trigger_automation",
}


class TestHITLCanonicalActionsExist:
    """T-a: canonical file existe e contém o frozenset HITL_REQUIRED_ACTIONS."""

    def test_canonical_file_exists(self):
        assert _CANONICAL_MODULE.exists(), (
            f"Canonical HITL actions file NOT found at {_CANONICAL_MODULE}.\n"
            "Fix: criar app/shared/hitl/hitl_canonical_actions.py com "
            "HITL_REQUIRED_ACTIONS: frozenset[str] = frozenset({...})."
        )

    def test_canonical_has_hitl_required_actions_symbol(self):
        assert _CANONICAL_MODULE.exists(), "canonical file missing — see test above"
        src = _CANONICAL_MODULE.read_text(encoding="utf-8")
        assert "HITL_REQUIRED_ACTIONS" in src, (
            "HITL_REQUIRED_ACTIONS não encontrado em hitl_canonical_actions.py.\n"
            "Fix: definir `HITL_REQUIRED_ACTIONS: frozenset[str] = frozenset({...})`."
        )

    def test_hitl_required_actions_importable(self):
        """T-a: HITL_REQUIRED_ACTIONS deve ser importável."""
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS  # noqa: F401
        assert HITL_REQUIRED_ACTIONS is not None

    def test_high_risk_actions_in_canonical(self):
        """T-a: todas as ações de alto risco estão no canonical."""
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS
        missing = HIGH_RISK_ACTIONS - HITL_REQUIRED_ACTIONS
        assert not missing, (
            f"Ações de alto risco AUSENTES em HITL_REQUIRED_ACTIONS:\n"
            + "\n".join(f"  - {a}" for a in sorted(missing))
            + "\nFix: adicionar essas strings a HITL_REQUIRED_ACTIONS em "
            "app/shared/hitl/hitl_canonical_actions.py."
        )


# ---------------------------------------------------------------------------
# T-b: consumer divergence test — each agent's local frozenset must be a
#       subset of (or equal to) HITL_REQUIRED_ACTIONS
# ---------------------------------------------------------------------------

AGENT_FILES_WITH_LOCAL_SETS: dict[str, str] = {
    "pipeline": "app/domains/cv_screening/agents/pipeline_react_agent.py",
    "analytics": "app/domains/analytics/agents/analytics_react_agent.py",
    "ats_integration": "app/domains/ats_integration/agents/ats_integration_react_agent.py",
    "automation": "app/domains/automation/agents/automation_react_agent.py",
    "jobs_mgmt": "app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py",
    "kanban": "app/domains/recruiter_assistant/agents/kanban_react_agent.py",
    "talent_funnel": "app/domains/recruiter_assistant/agents/talent_funnel_react_agent.py",
    "recruiter_copilot": "app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py",
    "communication": "app/domains/communication/agents/communication_react_agent.py",
}


def _extract_frozenset_strings(filepath: pathlib.Path, constant_name: str) -> set[str]:
    """Extract string elements from a frozenset assignment via AST."""
    if not filepath.exists():
        return set()
    src = filepath.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == constant_name:
                    val = node.value
                    # frozenset({...}) or frozenset([...])
                    if isinstance(val, ast.Call) and val.args:
                        try:
                            return set(ast.literal_eval(val.args[0]))
                        except (ValueError, TypeError):
                            return set()
                    # Direct set literal
                    try:
                        return set(ast.literal_eval(val))
                    except (ValueError, TypeError):
                        return set()
    return set()


class TestHITLConsumerDivergence:
    """T-b: cada agente's local frozenset deve ser subconjunto do canonical."""

    @pytest.mark.parametrize("agent_name,rel_path", list(AGENT_FILES_WITH_LOCAL_SETS.items()))
    def test_agent_local_set_subset_of_canonical(self, agent_name, rel_path):
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS

        filepath = _ROOT / rel_path
        # Try standard name first, then legacy name for communication agent
        local_set = _extract_frozenset_strings(filepath, "_HITL_ACTION_TYPES")
        if not local_set and agent_name == "communication":
            local_set = _extract_frozenset_strings(filepath, "_HITL_MESSAGE_TYPES")

        if not local_set:
            pytest.skip(f"{agent_name}: local set not found (file missing or empty)")

        not_in_canonical = local_set - HITL_REQUIRED_ACTIONS
        assert not not_in_canonical, (
            f"Agente '{agent_name}' tem ações locais NÃO presentes no canonical:\n"
            + "\n".join(f"  - {a}" for a in sorted(not_in_canonical))
            + f"\nFix: adicionar essas strings a HITL_REQUIRED_ACTIONS em "
            "app/shared/hitl/hitl_canonical_actions.py."
        )


# ---------------------------------------------------------------------------
# T-c: gate OFF → zero regression (hitl_preflight returns None)
# ---------------------------------------------------------------------------

class TestHITLGateOff:
    """T-c: quando LIA_HITL_GATE não está setado, gate é dormante."""

    def test_gate_off_hitl_preflight_returns_none(self, monkeypatch):
        """gate OFF → hitl_preflight deve retornar None (sem bloqueio)."""
        monkeypatch.delenv("LIA_HITL_GATE", raising=False)
        from app.shared.hitl.hitl_approval_context import hitl_preflight
        result = hitl_preflight(
            tool="bulk_reject_candidates",
            domain="pipeline",
            data={"candidate_ids": ["c1", "c2"]},
        )
        assert result is None, (
            "gate OFF: hitl_preflight deveria retornar None mas retornou dados.\n"
            "Fix: hitl_preflight deve checar hitl_gate_enabled() primeiro."
        )

    def test_gate_off_no_action_blocked(self, monkeypatch):
        """gate OFF → nenhuma ação em HITL_REQUIRED_ACTIONS é bloqueada."""
        monkeypatch.delenv("LIA_HITL_GATE", raising=False)
        from app.shared.hitl.hitl_approval_context import hitl_preflight
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS

        for action in list(HITL_REQUIRED_ACTIONS)[:5]:  # sample first 5
            result = hitl_preflight(tool=action, domain="test")
            assert result is None, (
                f"gate OFF: ação '{action}' foi bloqueada mesmo com LIA_HITL_GATE off.\n"
                "Fix: confirmar que hitl_gate_enabled() retorna False quando env não setado."
            )


# ---------------------------------------------------------------------------
# T-d: canonical frozenset is frozenset[str]
# ---------------------------------------------------------------------------

class TestHITLCanonicalType:
    """T-d: HITL_REQUIRED_ACTIONS é frozenset[str]."""

    def test_is_frozenset(self):
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS
        assert isinstance(HITL_REQUIRED_ACTIONS, frozenset), (
            f"HITL_REQUIRED_ACTIONS deve ser frozenset, mas é {type(HITL_REQUIRED_ACTIONS)}."
        )

    def test_all_elements_are_strings(self):
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS
        non_strings = [x for x in HITL_REQUIRED_ACTIONS if not isinstance(x, str)]
        assert not non_strings, (
            f"Elementos não-string em HITL_REQUIRED_ACTIONS: {non_strings}.\n"
            "Fix: todos os elementos devem ser str."
        )

    def test_all_elements_non_empty(self):
        """T-e: sem strings vazias."""
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS
        empties = [x for x in HITL_REQUIRED_ACTIONS if not x.strip()]
        assert not empties, (
            "HITL_REQUIRED_ACTIONS contém strings vazias. "
            "Fix: remover entradas em branco."
        )


# ---------------------------------------------------------------------------
# T-f: domain-by-domain union is coherent (no duplicates between domains)
# ---------------------------------------------------------------------------

class TestHITLCanonicalCoherence:
    """T-f: HITL_REQUIRED_ACTIONS é a união coerente de todos os domínios."""

    def test_union_of_all_local_sets_is_subset_of_canonical(self):
        """Todos os action_types locais de todos os agentes estão no canonical."""
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS

        all_local: set[str] = set()
        for agent_name, rel_path in AGENT_FILES_WITH_LOCAL_SETS.items():
            filepath = _ROOT / rel_path
            local = _extract_frozenset_strings(filepath, "_HITL_ACTION_TYPES")
            if not local and agent_name == "communication":
                local = _extract_frozenset_strings(filepath, "_HITL_MESSAGE_TYPES")
            all_local.update(local)

        not_in_canonical = all_local - HITL_REQUIRED_ACTIONS
        assert not not_in_canonical, (
            f"Ações locais (union de todos agentes) NÃO em canonical:\n"
            + "\n".join(f"  - {a}" for a in sorted(not_in_canonical))
            + "\nFix: adicionar ao HITL_REQUIRED_ACTIONS."
        )

    def test_canonical_not_empty(self):
        """T-f: canonical deve ter pelo menos 20 ações (todos os domínios cobertos)."""
        from app.shared.hitl.hitl_canonical_actions import HITL_REQUIRED_ACTIONS
        assert len(HITL_REQUIRED_ACTIONS) >= 20, (
            f"HITL_REQUIRED_ACTIONS tem só {len(HITL_REQUIRED_ACTIONS)} ações. "
            "Esperado >= 20 (cobrindo 8 domínios de agentes + bulk REST ops).\n"
            "Fix: incluir todas as ações dos agentes canonical."
        )


# ---------------------------------------------------------------------------
# T-g: canonical module exports correct docstring context
# ---------------------------------------------------------------------------

class TestHITLCanonicalDocstring:
    """T-g: canonical tem docstring explicando o que qualifica como HITL."""

    def test_module_has_docstring(self):
        assert _CANONICAL_MODULE.exists(), "canonical file missing"
        src = _CANONICAL_MODULE.read_text(encoding="utf-8")
        tree = ast.parse(src)
        docstring = ast.get_docstring(tree)
        assert docstring, (
            "hitl_canonical_actions.py não tem module docstring.\n"
            "Fix: adicionar docstring explicando critérios de HITL."
        )

    def test_docstring_mentions_criteria(self):
        assert _CANONICAL_MODULE.exists(), "canonical file missing"
        src = _CANONICAL_MODULE.read_text(encoding="utf-8")
        # Must mention irreversible, external, or similar qualifier
        qualifiers = ["irrevers", "externo", "externa", "destructiv", "bulk", "LGPD", "aprovação"]
        lower_src = src.lower()
        found = any(q.lower() in lower_src for q in qualifiers)
        assert found, (
            "hitl_canonical_actions.py deve ter docstring mencionando critérios de HITL "
            "(ex: ações irreversíveis, comunicação externa, bulk, LGPD).\n"
            "Fix: adicionar critérios ao módulo docstring."
        )
