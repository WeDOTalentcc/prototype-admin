"""End-to-end integration test for the Job Creation wizard graph.

Drives ``JobCreationGraph`` through every node — intake → jd_enrichment →
bigfive → salary → competency → wsi_questions → eligibility → review →
publish → calibration → handoff — with stubbed LLM services and a stubbed
Rails API client. Asserts that exactly **one** ``decision_type="job_creation"``
audit row is emitted at handoff with the expected ``company_id``,
``prompt_hash`` and ``model`` fields.

This complements the per-node unit tests in
``tests/unit/test_job_creation_compliance.py`` by guarding the audit trail
against regressions where a future refactor accidentally moves the audit
emission, breaks the resume path, or duplicates the row.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver


COMPANY_ID = 4242
THREAD_ID = f"wizard-e2e-{uuid.uuid4()}"


def _fake_enriched_dict() -> dict:
    return {
        "titulo_padronizado": "Product Manager Sênior",
        "senioridade_confirmada": "senior",
        "about_role": "Liderar squad de produto end-to-end.",
        "responsabilidades": [
            "Definir roadmap trimestral",
            "Conduzir descoberta com clientes",
        ],
        "skills_obrigatorias": [
            {"skill": "discovery", "contexto": "entrevistas com clientes"},
            {"skill": "analytics", "contexto": "leitura de métricas de produto"},
        ],
        "skills_desejaveis": ["sql"],
        "competencias_comportamentais": [
            {
                "competencia": "comunicação",
                "contexto": "alinhar stakeholders",
                "trait_big_five": "extraversion",
            },
        ],
        "context_signals": {},
        "alteracoes_realizadas": [],
        "fairness_corrections": [],
        "wsi_quality_score": 80.0,
        "wsi_quality_warnings": [],
    }


def _fake_jd_service() -> MagicMock:
    service = MagicMock()
    service.enrich.return_value = (
        SimpleNamespace(model_dump=lambda: _fake_enriched_dict()),
        80.0,
        [],
    )
    return service


def _fake_wsi_generator() -> MagicMock:
    generator = MagicMock()
    generator.extract_bigfive.return_value = SimpleNamespace(
        model_dump=lambda: {
            "openness": 0.6,
            "conscientiousness": 0.7,
            "extraversion": 0.55,
            "agreeableness": 0.5,
            "stability": 0.6,
            "evidences": {"openness": ["liderar squad"]},
        }
    )
    generator.rank_traits.return_value = [
        {"trait": "conscientiousness", "score": 0.7, "rank": 1, "weight": 0.4},
    ]
    generator.generate_questions.return_value = [
        SimpleNamespace(model_dump=lambda: {
            "id": "q1",
            "question": "Conte sobre uma vez em que liderou uma descoberta de produto.",
            "ideal_answer": "Resposta CBI estruturada.",
            "scoring_rubric": {"5": "exemplo concreto"},
            "framework": "CBI",
            "block": "technical",
            "competency": "technical",
            "skill": "discovery",
            "trait_ocean": None,
            "weight": 1.0,
            "source": "wsi_wizard",
            "max_duration_s": 180,
        }),
        SimpleNamespace(model_dump=lambda: {
            "id": "q2",
            "question": "Descreva uma situação real de alinhamento difícil.",
            "ideal_answer": "Resposta CBI estruturada.",
            "scoring_rubric": {"5": "exemplo concreto"},
            "framework": "CBI",
            "block": "behavioral",
            "competency": "behavioral",
            "skill": "comunicação",
            "trait_ocean": "extraversion",
            "weight": 1.0,
            "source": "wsi_wizard",
            "max_duration_s": 180,
        }),
    ]
    return generator


def _fake_api_client() -> MagicMock:
    from app.domains.job_creation.api_client import APIResponse

    api = MagicMock()
    api.get_company_defaults.return_value = APIResponse(success=True, data={})
    api.create_job.return_value = APIResponse(
        success=True,
        data={"data": {"id": 999, "uid": "job-uid-999"}},
    )
    api.save_screening_config.return_value = APIResponse(success=True, data={})
    api.publish_job.return_value = APIResponse(success=True, data={})
    api.get_share_link.return_value = APIResponse(
        success=True, data={"share_link": "https://lia.example/jobs/999"}
    )
    api.get_calibration_candidates.return_value = APIResponse(
        success=True, data={"candidates": []}
    )
    return api


@pytest.fixture
def initial_state() -> dict:
    """Pre-seed approvals + screening choices so the graph can run end-to-end."""
    return {
        "session_id": THREAD_ID,
        "user_id": "recruiter-1",
        "workspace_id": COMPANY_ID,
        "raw_input": "Quero criar uma vaga de Product Manager sênior",
        "user_query": "Quero criar uma vaga de Product Manager sênior",
        "jd_raw": "Procuramos um Product Manager sênior para liderar squad",
        "parsed_title": "Product Manager",
        "parsed_seniority": "senior",
        "salary_min": 18000,
        "salary_max": 26000,
        "screening_mode": "compact",
        # HITL approvals pre-granted so the conditional edges advance.
        "jd_approved": True,
        "questions_approved": True,
        # Calibration: pre-seed one approved candidate so calibration_node
        # marks the stage complete and routes to handoff.
        "calibration_threshold": 1,
        "calibration_candidates": [
            {
                "id": "cand-1",
                "name": "Maria",
                "current_title": "PM",
                "current_company": "Acme",
                "match_score": 0.85,
                "match_criteria": [],
                "decision": "approved",
            }
        ],
        "stage_history": [],
    }


def test_full_wizard_run_emits_single_job_creation_audit(initial_state):
    """End-to-end: graph runs through every node and emits exactly one
    ``decision_type="job_creation"`` audit row with company_id,
    prompt_hash and model captured.

    Pendencia 6 update (2026-05-27): pos Sprint F.2 (LLM gates 2026-05) +
    Sprint Pipeline Templates (2026-05-26), o graph tem 4 HITL interrupts:
    jd_gate, pipeline_template, wsi_questions_gate, review_gate. Test
    pre-Sprint-F.2 (2026-04-26) apenas pre-setava jd_approved=True e
    invocava uma vez -- nao mais suficiente. Pattern canonical agora:
    Command(resume="<msg>") canonical via langgraph.types apos cada
    interrupt(), seguindo aresume_with_message do JobCreationGraph.
    """
    from app.domains.job_creation import graph as job_graph
    from langgraph.types import Command

    log_decision = AsyncMock()

    # Mock classifier que sempre devolve `approve` confidence alta pra
    # bypass dos 4 HITL gates LLM canonical.
    from app.domains.job_creation.services.wizard_gate_classifier import (
        GateClassifierOutput,
    )

    def _make_stage_aware_classifier():
        """Mock canonical: detecta stage via system_prompt + retorna intent apropriado.

        - jd_enrichment / wsi_questions / competency / outros -> approve
        - review -> publish_now (review_gate allowlist nao tem approve)
        """
        async def _classify(system_prompt, context_block, schema, **kw):
            # Detecta stage via system_prompt content
            if "review" in (system_prompt or "").lower() and "publish_now" in (system_prompt or "").lower():
                return GateClassifierOutput(
                    intent="publish_now", confidence=0.95,
                    conversational_reply="(mock publish_now)", extracted_data={},
                )
            return GateClassifierOutput(
                intent="approve", confidence=0.95,
                conversational_reply="(mock approve)", extracted_data={},
            )
        clf = MagicMock()
        clf.classify = AsyncMock(side_effect=_classify)
        return clf

    # Mock intake_intent_classifier para devolver provides_jd_intent (pula
    # guard do jd_enrichment que pede JD ao recrutador). Pos Fix D 2026-05-27
    # (commit 8c5f53ddd), classifier_eligible sempre roda quando nao ha
    # JD enriquecida -- precisa mock pra cobertura E2E.
    from app.domains.job_creation.services.intake_intent_classifier import (
        IntakeIntentOutput,
    )

    class _MockIntakeProvidesJd:
        def classify_sync(self, **kwargs):
            return IntakeIntentOutput(
                intent="provides_jd_intent",
                confidence=0.95,
                conversational_reply="(mock segue pro enrichment)",
            )

    with patch.object(job_graph, "_get_jd_service", return_value=_fake_jd_service()), \
         patch.object(job_graph, "_get_wsi_generator", return_value=_fake_wsi_generator()), \
         patch.object(job_graph, "_get_api_client", return_value=_fake_api_client()), \
         patch("app.shared.compliance.audit_service.AuditService") as audit_cls, \
         patch(
             "app.domains.job_creation.compliance._run_async",
             lambda coro, **kw: coro.close(),
         ), \
         patch(
             "app.domains.job_creation.services.wizard_gate_classifier."
             "get_wizard_gate_classifier",
             return_value=_make_stage_aware_classifier(),
         ), \
         patch(
             "app.domains.job_creation.services.intake_intent_classifier."
             "get_intake_intent_classifier",
             return_value=_MockIntakeProvidesJd(),
         ):
        audit_cls.return_value.log_decision = log_decision

        compiled = job_graph.create_job_creation_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": THREAD_ID}}

        # Initial invoke -- graph runs intake -> jd_enrichment -> jd_gate
        # (pausa em jd_gate via interrupt()).
        state = compiled.invoke(initial_state, config=config)

        # Resume canonical loop -- max 8 resumes (4 HITL gates + dupla confirmacao publish + safety).
        # Cada resume passa "ok" pro Command -- classifier mock sempre
        # devolve approve.
        for _ in range(8):
            if state.get("current_stage") == "handoff":
                break
            state = compiled.invoke(
                Command(resume="ok"),
                config=config,
            )

        final_state = state

    # --- Walk reached every node, including the final handoff stage ---
    assert final_state["current_stage"] == "handoff", (
        f"Wizard nao atingiu handoff. Parou em: {final_state.get('current_stage')!r}. "
        f"stage_history: {final_state.get('stage_history')!r}"
    )
    assert final_state["handoff_url"] == "/jobs/999"
    stages = final_state["stage_history"]
    for required in (
        "intake",
        "jd_enrichment",
        "bigfive",
        "salary",
        "competency",
        "wsi_questions",
        "eligibility",
        "review",
        "publish",
        "calibration",
        "handoff",
    ):
        assert required in stages, f"stage {required!r} missing from {stages!r}"

    # --- Exactly one audit row, with the documented compliance fields ---
    assert log_decision.call_count == 1, (
        f"expected exactly 1 job_creation audit row, got {log_decision.call_count}"
    )
    kwargs = log_decision.call_args.kwargs
    assert kwargs["decision_type"] == "job_creation"
    assert kwargs["agent_name"] == "job_creation_wizard"
    assert kwargs["company_id"] == str(COMPANY_ID)
    assert kwargs["job_vacancy_id"] == "999"

    reasoning_blob = " ".join(str(r) for r in kwargs["reasoning"])
    assert "prompt_hash=" in reasoning_blob
    assert "model=" in reasoning_blob
    assert "seniority=" in reasoning_blob
    assert "screening_mode=compact" in reasoning_blob


def test_first_turn_emits_intake_ws_stage_payload(initial_state):
    """Task #826 — guarantee that the very first turn of "Criar uma nova vaga"
    emits a ``ws_stage_payload`` whose ``stage == 'intake'``. This is the
    canonical signal that powers the chat-feed wizard plan card and the
    top-of-feed ``WizardProgressBar`` on the frontend, so it must keep
    working.

    Completeness on a bare opener may be 0.0 (the user has not provided
    any job details yet) — what matters for the chat surface is that the
    stage event arrives at all so the bar can mount.
    """
    from app.domains.job_creation import graph as job_graph

    # Run a single intake_node call — no LLM, no API client needed for this
    # node — and inspect the wizard payload it sets on state.
    raw_state = {
        "session_id": THREAD_ID + "-intake",
        "user_id": "recruiter-1",
        "workspace_id": COMPANY_ID,
        "user_query": "Criar uma nova vaga",
        "raw_input": "Criar uma nova vaga",
        "stage_history": [],
    }

    new_state = job_graph.intake_node(raw_state)

    payload = new_state.get("ws_stage_payload")
    assert payload is not None, "intake_node must emit ws_stage_payload"
    assert payload.get("type") == "wizard_stage"
    assert payload.get("stage") == "intake", (
        f"first turn must emit stage='intake', got {payload.get('stage')!r}"
    )
    assert payload.get("requires_approval") is False
    completeness = payload.get("completeness")
    assert isinstance(completeness, (int, float)), (
        "completeness must be numeric so the frontend bar can render a "
        "deterministic progress value"
    )
    assert 0.0 <= completeness <= 1.0, (
        f"completeness must be a [0,1] ratio, got {completeness!r}"
    )


def test_resume_after_hitl_does_not_duplicate_audit(initial_state):
    """A wizard that pauses at the HITL points and resumes must still
    emit exactly one audit row — never zero, never duplicated."""
    from app.domains.job_creation import graph as job_graph
    from app.domains.job_creation.services.wizard_gate_classifier import (
        GateClassifierOutput,
    )
    from app.domains.job_creation.services.intake_intent_classifier import (
        IntakeIntentOutput,
    )

    def _make_stage_aware_classifier():
        """Mock canonical: detecta stage via system_prompt + retorna intent apropriado.

        - jd_enrichment / wsi_questions / competency / outros -> approve
        - review -> publish_now (review_gate allowlist nao tem approve)
        """
        async def _classify(system_prompt, context_block, schema, **kw):
            # Detecta stage via system_prompt content
            if "review" in (system_prompt or "").lower() and "publish_now" in (system_prompt or "").lower():
                return GateClassifierOutput(
                    intent="publish_now", confidence=0.95,
                    conversational_reply="(mock publish_now)", extracted_data={},
                )
            return GateClassifierOutput(
                intent="approve", confidence=0.95,
                conversational_reply="(mock approve)", extracted_data={},
            )
        clf = MagicMock()
        clf.classify = AsyncMock(side_effect=_classify)
        return clf

    class _MockIntakeProvidesJd:
        def classify_sync(self, **kwargs):
            return IntakeIntentOutput(
                intent="provides_jd_intent",
                confidence=0.95,
                conversational_reply="(mock segue pro enrichment)",
            )

    log_decision = AsyncMock()

    with patch.object(job_graph, "_get_jd_service", return_value=_fake_jd_service()), \
         patch.object(job_graph, "_get_wsi_generator", return_value=_fake_wsi_generator()), \
         patch.object(job_graph, "_get_api_client", return_value=_fake_api_client()), \
         patch("app.shared.compliance.audit_service.AuditService") as audit_cls, \
         patch(
             "app.domains.job_creation.compliance._run_async",
             lambda coro, **kw: coro.close(),
         ):
        audit_cls.return_value.log_decision = log_decision

        compiled = job_graph.create_job_creation_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": THREAD_ID + "-resume"}}

        # First run: graph pausa em jd_gate (HITL #1 canonical interrupt).
        # Sem gate_resume_message, jd_gate_node chama interrupt() e devolve
        # control ao caller. Pre-set de jd_approved nao basta (PoS Sprint F.2).
        paused_state = dict(initial_state)
        paused_state["jd_approved"] = None
        paused_state["questions_approved"] = None
        first = compiled.invoke(paused_state, config=config)
        assert first["current_stage"] == "jd_enrichment", (
            f"Esperava parar em jd_enrichment (HITL #1), parou em: "
            f"{first.get('current_stage')!r}"
        )
        assert log_decision.call_count == 0

        # Resume canonical via Command(resume=...) -- nao basta invocar
        # com novo state. Loop ate handoff (4 HITL gates).
        from langgraph.types import Command
        resumed = first
        for _ in range(8):
            if resumed.get("current_stage") == "handoff":
                break
            resumed = compiled.invoke(Command(resume="ok"), config=config)

    assert resumed["current_stage"] == "handoff", (
        f"Wizard nao atingiu handoff pos-resume. Parou em: "
        f"{resumed.get('current_stage')!r}"
    )
    assert log_decision.call_count == 1
    kwargs = log_decision.call_args.kwargs
    assert kwargs["decision_type"] == "job_creation"
    assert kwargs["company_id"] == str(COMPANY_ID)
