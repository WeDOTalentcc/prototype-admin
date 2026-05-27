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
    """Patch ``AuditService.log_decision`` to record calls in memory.

    Fix J 2026-05-27: pos PR-17, audit usa emit_audit_fire_and_forget que skipa
    em sync test context (sem event loop). Patchamos o helper para invocar o
    coro_factory sincronamente via asyncio.run, garantindo captura no fixture.
    """
    import asyncio

    calls: list[dict[str, Any]] = []

    async def _record(self, **kwargs):
        calls.append(dict(kwargs))
        return None

    from app.shared.compliance import audit_service as audit_svc

    monkeypatch.setattr(audit_svc.AuditService, "log_decision", _record)

    # Patch emit_audit_fire_and_forget canonical (PR-17) -- run coro sync em test.
    # Necessario para capturar audit calls quando node usa o helper canonical
    # (substituiu asyncio.run em sync nodes -- ver scripts/check_no_asyncio_run_in_sync_nodes.py).
    def _sync_emit(coro_factory):
        try:
            coro = coro_factory()
            asyncio.run(coro)
        except Exception:
            pass  # mirror fire-and-forget swallow

    # Patch em ambos os modulos onde emit_audit_fire_and_forget eh referenciado
    # (cada node faz `from helpers.async_audit import emit_audit_fire_and_forget`).
    from app.domains.job_creation.helpers import async_audit
    monkeypatch.setattr(async_audit, "emit_audit_fire_and_forget", _sync_emit)
    # Plus modulos internal/audit.py que reusa o helper
    from app.domains.job_creation.internal import audit as internal_audit
    monkeypatch.setattr(internal_audit, "emit_audit_fire_and_forget", _sync_emit)
    # Plus os 4 nodes que importam direto
    for node_name in ("bigfive", "wsi_questions", "competency", "eligibility"):
        try:
            node_mod = __import__(
                f"app.domains.job_creation.nodes.{node_name}",
                fromlist=["emit_audit_fire_and_forget"],
            )
            if hasattr(node_mod, "emit_audit_fire_and_forget"):
                monkeypatch.setattr(node_mod, "emit_audit_fire_and_forget", _sync_emit)
        except (ImportError, AttributeError):
            pass

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
    """Static guard: pos PR-10 split (2026-05-26), os call sites de
    ``_emit_wizard_step_audit(`` vivem em nodes/*.py individuais (um por
    node decisorio). Pre-PR-10 viviam todos em graph.py. Sentinel atualizado
    Fix J 2026-05-27: checa callsite em cada arquivo node correspondente.

    Falha imediatamente se algum node decisorio perder seu callsite (D3
    ressurgiria silenciosamente)."""
    from pathlib import Path

    NODES_DIR = (
        Path(__file__).resolve().parents[3]
        / "lia-agent-system"
        / "app" / "domains" / "job_creation" / "nodes"
    )
    if not NODES_DIR.exists():
        # Fallback path resolution for non-standard test runners
        NODES_DIR = Path("/home/runner/workspace/lia-agent-system/app/domains/job_creation/nodes")

    for stage in WIZARD_NODES:
        node_file = NODES_DIR / f"{stage}.py"
        assert node_file.exists(), (
            f"PR-10 split: node file {stage}.py nao encontrado em {NODES_DIR}. "
            f"Sentinel obsoleto ou node deletado -- atualizar."
        )
        node_src = node_file.read_text()
        assert "_emit_wizard_step_audit(" in node_src, (
            f"node `{stage}.py` perdeu seu callsite `_emit_wizard_step_audit(` "
            f"-- Drift D3 ressurgiu. Re-adicionar emit antes do return canonical "
            f"do node."
        )
