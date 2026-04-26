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
    prompt_hash and model captured."""
    from app.domains.job_creation import graph as job_graph

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

        # Build a fresh graph with an in-memory checkpointer so we don't
        # depend on the singleton (which may carry state from other tests).
        compiled = job_graph.create_job_creation_graph(checkpointer=MemorySaver())
        final_state = compiled.invoke(
            initial_state,
            config={"configurable": {"thread_id": THREAD_ID}},
        )

    # --- Walk reached every node, including the final handoff stage ---
    assert final_state["current_stage"] == "handoff"
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

        # First run: simulate a recruiter who has not yet approved the JD.
        # The graph should park at jd_enrichment and emit no audit row.
        paused_state = dict(initial_state)
        paused_state["jd_approved"] = None
        paused_state["questions_approved"] = None
        first = compiled.invoke(paused_state, config=config)
        assert first["current_stage"] == "jd_enrichment"
        assert log_decision.call_count == 0

        # Recruiter approves the JD and the questions; resume the same thread.
        resumed = compiled.invoke(
            {**first, "jd_approved": True, "questions_approved": True},
            config=config,
        )

    assert resumed["current_stage"] == "handoff"
    assert log_decision.call_count == 1
    kwargs = log_decision.call_args.kwargs
    assert kwargs["decision_type"] == "job_creation"
    assert kwargs["company_id"] == str(COMPANY_ID)
