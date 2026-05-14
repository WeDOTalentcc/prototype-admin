"""Task #1061 — Sentinel: cada node decisório do JobCreationGraph
(`bigfive`, `wsi_questions`, `competency`, `eligibility`) emite uma
audit row `decision_type=wizard_step_completed` com `before/after/
target_id/trace_id` em ``reasoning`` quando completa.

Drift D3 da auditoria #1058: antes desta sentinela, só `jd_enrichment`
(no caminho de bloqueio L3) e `publish` deixavam rastro. Sem trail
por step decisório, viola Inegociável #6 (EU AI Act Art. 13 / SOX).

A sentinela:
  * patcha ``AuditService.log_decision`` pra capturar chamadas em
    memória — não toca DB, não exige RLS;
  * patcha ``evaluate_wizard_policy`` pra ALLOW (evita short-circuit
    DENY que pula audit por design);
  * roda cada um dos 4 nodes com state mínimo plausível;
  * exige que cada node emita >=1 row com decision_type=
    ``wizard_step_completed`` cobrindo o stage correspondente;
  * exige que ``reasoning`` contenha ``trace_id=``, ``target_id=``,
    ``before=`` e ``after=`` (espelho do contrato
    ``audit_company_change``).

Falha o build se algum dos 4 nodes voltar a executar sem emitir audit
row, fechando D3.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.domains.job_creation import graph as graph_mod
from app.domains.job_creation.policy_gate import (
    PolicyDecision,
    WizardPolicyResult,
)


WIZARD_NODES = ("bigfive", "wsi_questions", "competency", "eligibility")


@pytest.fixture
def captured_audit_calls(monkeypatch):
    """Patch ``AuditService.log_decision`` to record calls in memory."""
    calls: list[dict[str, Any]] = []

    async def _record(self, **kwargs):
        calls.append(dict(kwargs))
        return None

    from app.shared.compliance import audit_service as audit_svc

    monkeypatch.setattr(audit_svc.AuditService, "log_decision", _record)
    # Allow policy gate (DENY would short-circuit before audit by design)
    monkeypatch.setattr(
        graph_mod,
        "evaluate_wizard_policy",
        lambda intent, state: WizardPolicyResult(
            decision=PolicyDecision.ALLOW,
            rationale="test_allow",
            intent=str(intent),
        ),
    )
    return calls


def _minimal_state(stage: str) -> dict[str, Any]:
    base = {
        "workspace_id": "co-acme-1061",
        "company_id": "co-acme-1061",
        "session_id": "sess-1061",
        "job_id": "job-1061",
        "raw_input": "Engenheiro de software pleno",
        "user_query": "Engenheiro de software pleno",
        "parsed_title": "Engenheiro Backend",
        "parsed_seniority": "pleno",
        "jd_enriched": {
            "titulo_padronizado": "Engenheiro Backend",
            "about_role": "Construir APIs em Python.",
            "responsabilidades": ["APIs", "Code review"],
            "skills_obrigatorias": [
                {"skill": "Python", "contexto": "FastAPI"},
            ],
            "skills_desejaveis": [],
            "competencias_comportamentais": [
                {"competencia": "Comunicação", "contexto": "time", "trait_big_five": "extraversion"},
            ],
        },
        "screening_mode": "compact",
        "question_distribution": {"technical": 5, "behavioral": 2},
        "trait_rankings": [],
        "wsi_questions": [],
        "wsi_dropped_questions": [],
        "eligibility_questions": [
            {"text": "Tem CNH B?", "answer": "yes"},
        ],
    }
    return base


def _assert_wizard_step_audit(
    calls: list[dict[str, Any]], stage: str
) -> dict[str, Any]:
    matching = [
        c for c in calls
        if c.get("decision_type") == "wizard_step_completed"
        and c.get("agent_name") == f"job_creation:{stage}"
    ]
    assert matching, (
        f"node `{stage}` NÃO emitiu audit row "
        f"decision_type=wizard_step_completed. Drift D3 ressurgiu — "
        f"viola EU AI Act Art.13 / Inegociável #6. "
        f"Calls capturadas: {[(c.get('agent_name'), c.get('decision_type')) for c in calls]}"
    )
    call = matching[-1]
    assert call.get("company_id") == "co-acme-1061"
    assert call.get("action") == f"complete_{stage}"
    assert call.get("decision") == "completed"
    reasoning_blob = " | ".join(call.get("reasoning") or [])
    for marker in ("trace_id=", "target_id=", "before=", "after="):
        assert marker in reasoning_blob, (
            f"node `{stage}` audit reasoning sem `{marker}` — "
            f"contrato SOX (espelho audit_company_change) violado. "
            f"reasoning={call.get('reasoning')}"
        )
    criteria = call.get("criteria_used") or []
    assert "wizard_step" in criteria
    assert any(c == f"stage:{stage}" for c in criteria)
    return call


def test_bigfive_node_emits_wizard_step_audit(monkeypatch, captured_audit_calls):
    # Stub the WSI generator so bigfive doesn't call a real LLM
    class _StubGen:
        def extract_bigfive(self, enriched):
            from app.domains.job_creation.schemas import BigFiveExtraction
            return BigFiveExtraction(
                openness=0.5, conscientiousness=0.5, extraversion=0.5,
                agreeableness=0.5, stability=0.7,
            )

        def rank_traits(self, profile, seniority):
            return []

    monkeypatch.setattr(graph_mod, "_get_wsi_generator", lambda: _StubGen())

    state = _minimal_state("bigfive")
    graph_mod.bigfive_node(state)
    _assert_wizard_step_audit(captured_audit_calls, "bigfive")


def test_competency_node_emits_wizard_step_audit(captured_audit_calls):
    state = _minimal_state("competency")
    graph_mod.competency_node(state)
    _assert_wizard_step_audit(captured_audit_calls, "competency")


def test_wsi_questions_node_emits_wizard_step_audit(monkeypatch, captured_audit_calls):
    # Force the "already approved" path so no LLM is called.
    state = _minimal_state("wsi_questions")
    state["questions_approved"] = True
    state["wsi_questions"] = [
        {"question": "Conte sobre sua experiência com Python.", "block": "technical"},
    ]
    graph_mod.wsi_questions_node(state)
    _assert_wizard_step_audit(captured_audit_calls, "wsi_questions")


def test_eligibility_node_emits_wizard_step_audit(captured_audit_calls):
    state = _minimal_state("eligibility")
    graph_mod.eligibility_node(state)
    _assert_wizard_step_audit(captured_audit_calls, "eligibility")


def test_all_four_wizard_nodes_have_audit_callsite_in_source():
    """Static guard: a string ``_emit_wizard_step_audit(`` deve aparecer
    pelo menos 4× em ``graph.py`` (1 call site por node decisório).
    Falha imediatamente se alguém remover um call site sem atualizar a
    sentinela — D3 ressurgiria silenciosamente."""
    import inspect

    src = inspect.getsource(graph_mod)
    occurrences = src.count("_emit_wizard_step_audit(")
    # 1 definição + 4 call sites = 5 ocorrências mínimas
    assert occurrences >= 5, (
        f"Esperava >=5 ocorrências de `_emit_wizard_step_audit(` em "
        f"graph.py (1 def + 4 call sites para "
        f"{WIZARD_NODES}); achei {occurrences}. Algum node decisório "
        f"perdeu o audit — Drift D3 ressurgiu."
    )
    # Garante que cada stage aparece como argumento literal
    for stage in WIZARD_NODES:
        needle = f'stage="{stage}"'
        assert needle in src, (
            f"call site de `_emit_wizard_step_audit` para stage "
            f"`{stage}` ausente em graph.py — D3 ressurgiu."
        )
