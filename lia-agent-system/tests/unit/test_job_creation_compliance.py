"""Compliance gates for the JobCreationGraph wizard.

Covers the three enterprise gates wired into ``app.domains.job_creation.graph``:

* PII masking on recruiter input before it reaches the LLM.
* FairnessGuard pre-check (input) and post-check (LLM output).
* Single ``decision_type="job_creation"`` audit row at handoff.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

def test_mask_pii_for_llm_strips_email_and_cpf():
    from app.domains.job_creation.compliance import mask_pii_for_llm

    raw = (
        "Procuro um PM senior, contato joao.silva@example.com, "
        "CPF 123.456.789-09, telefone (11) 98765-4321."
    )
    masked = mask_pii_for_llm(raw)

    assert "joao.silva@example.com" not in masked
    assert "123.456.789-09" not in masked
    assert "98765-4321" not in masked


def test_jd_enrichment_node_masks_pii_before_llm():
    """The enrichment service must receive a PII-stripped JD, not the raw one."""
    from app.domains.job_creation import graph as job_graph

    fake_enriched = SimpleNamespace(
        model_dump=lambda: {
            "about_role": "Procuramos um PM senior para o time.",
            "responsabilidades": ["Liderar squad"],
            "skills_obrigatorias": [{"skill": "produto"}],
        }
    )
    fake_service = MagicMock()
    fake_service.enrich.return_value = (fake_enriched, 80.0, [])

    state = {
        "raw_input": "Quero um PM senior, email maria@example.com",
        "jd_raw": "Quero um PM senior, email maria@example.com",
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service):
        job_graph.jd_enrichment_node(state)

    # Service must have been called with PII-masked text
    sent_jd = fake_service.enrich.call_args.kwargs["jd_raw"]
    assert "maria@example.com" not in sent_jd


# ---------------------------------------------------------------------------
# FairnessGuard
# ---------------------------------------------------------------------------

def test_jd_enrichment_node_blocks_discriminatory_input():
    """Input mentioning discriminatory filters must be blocked before any LLM call."""
    from app.domains.job_creation import graph as job_graph

    fake_service = MagicMock()
    state = {
        "raw_input": "Vaga apenas para homens jovens, sem deficiencia",
        "jd_raw": "Vaga apenas para homens jovens, sem deficiencia",
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service):
        result = job_graph.jd_enrichment_node(state)

    fake_service.enrich.assert_not_called()
    assert result.get("error")
    assert result.get("jd_approved") is False
    assert result.get("jd_quality_score") == 0.0


def test_jd_enrichment_node_post_check_blocks_biased_output():
    """When the LLM produces biased text the JD must be explicitly blocked."""
    from app.domains.job_creation import graph as job_graph

    biased_enriched = SimpleNamespace(
        model_dump=lambda: {
            "about_role": "Vaga apenas para homens jovens com energia jovem.",
            "responsabilidades": ["Liderar squad"],
            "skills_obrigatorias": [{"skill": "produto"}],
        }
    )
    fake_service = MagicMock()
    fake_service.enrich.return_value = (biased_enriched, 80.0, [])

    state = {
        "raw_input": "Procuramos PM senior para o time",
        "jd_raw": "Procuramos PM senior para o time",
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service):
        result = job_graph.jd_enrichment_node(state)

    # Explicit block: enriched payload removed, approval prevented, error set.
    assert result["jd_enriched"] is None
    assert result["jd_approved"] is False
    assert result.get("error")
    assert result["jd_quality_score"] == 0.0
    assert result["requires_approval"] is False


def test_bigfive_node_masks_pii_and_runs_fairness_post_check():
    """Big Five LLM call must receive PII-masked input and run a post-check."""
    from app.domains.job_creation import graph as job_graph

    fake_bigfive = SimpleNamespace(model_dump=lambda: {
        "openness": {"score": 4, "evidence": "neutral evidence"},
    })
    fake_gen = MagicMock()
    fake_gen.extract_bigfive.return_value = fake_bigfive
    fake_gen.rank_traits.return_value = []

    state = {
        "jd_enriched": {
            "about_role": "Liderar squad. Contato: maria@example.com",
            "responsabilidades": ["Garantir entregas com email joao@example.com"],
            "skills_obrigatorias": [],
            "titulo_padronizado": "PM",
        },
        "stage_history": [],
        "parsed_seniority": "senior",
    }

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen):
        result = job_graph.bigfive_node(state)

    sent = fake_gen.extract_bigfive.call_args.args[0]
    payload = sent.model_dump() if hasattr(sent, "model_dump") else sent
    text_blob = " ".join([
        payload.get("about_role", ""),
        " ".join(payload.get("responsabilidades", []) or []),
    ])
    assert "maria@example.com" not in text_blob
    assert "joao@example.com" not in text_blob
    assert result["bigfive_profile"] is not None


def test_wsi_node_masks_pii_and_runs_pre_check_before_llm():
    """WSI question generation must receive PII-masked input and skip on block."""
    from app.domains.job_creation import graph as job_graph

    fake_q = SimpleNamespace(model_dump=lambda: {"question": "Tell me about a project"})
    fake_gen = MagicMock()
    fake_gen.generate_questions.return_value = [fake_q]

    state = {
        "jd_enriched": {
            "about_role": "Liderar squad. email: maria@example.com",
            "responsabilidades": ["Mentor com email joao@example.com"],
            "skills_obrigatorias": [],
            "titulo_padronizado": "PM",
        },
        "stage_history": [],
        "seniority_resolved": "senior",
        "question_distribution": {"technical": 1, "behavioral": 1},
        "trait_rankings": [],
    }

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen):
        result = job_graph.wsi_questions_node(state)

    fake_gen.generate_questions.assert_called_once()
    sent = fake_gen.generate_questions.call_args.kwargs["enriched"]
    payload = sent.model_dump() if hasattr(sent, "model_dump") else sent
    blob = " ".join([
        payload.get("about_role", ""),
        " ".join(payload.get("responsabilidades", []) or []),
    ])
    assert "maria@example.com" not in blob
    assert "joao@example.com" not in blob
    assert len(result["wsi_questions"]) == 1


def test_wsi_node_blocks_discriminatory_enriched_input():
    """If the enriched JD is discriminatory the WSI LLM must not be called."""
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()
    state = {
        "jd_enriched": {
            "about_role": "Vaga apenas para homens jovens",
            "responsabilidades": [],
            "skills_obrigatorias": [],
        },
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen):
        result = job_graph.wsi_questions_node(state)

    fake_gen.generate_questions.assert_not_called()
    assert result["wsi_questions"] == []


def test_wsi_node_post_check_records_dropped_questions_and_warning():
    """When the LLM emits a biased question, it must be dropped and recorded
    structurally so the wizard can explain it and the audit trail captures it."""
    from app.domains.job_creation import graph as job_graph

    biased = SimpleNamespace(model_dump=lambda: {
        "question": "Voce eh homem jovem sem deficiencia?",
        "category": "behavioral",
    })
    clean = SimpleNamespace(model_dump=lambda: {
        "question": "Conte sobre um projeto que voce liderou.",
        "category": "behavioral",
    })
    fake_gen = MagicMock()
    fake_gen.generate_questions.return_value = [biased, clean]

    state = {
        "jd_enriched": {
            "about_role": "Liderar squad de produto.",
            "responsabilidades": ["Mentor"],
            "skills_obrigatorias": [],
            "titulo_padronizado": "PM",
        },
        "stage_history": [],
        "seniority_resolved": "senior",
        "question_distribution": {"technical": 1, "behavioral": 1},
        "trait_rankings": [],
    }

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen):
        result = job_graph.wsi_questions_node(state)

    # Clean question survives; biased question was dropped.
    assert len(result["wsi_questions"]) == 1
    dropped = result.get("wsi_dropped_questions") or []
    assert len(dropped) == 1
    record = dropped[0]
    assert record["question"].startswith("Voce eh homem")
    assert record["blocked_terms"]
    assert record["message"]

    # Wizard payload surfaces a friendly warning + the dropped list.
    payload = result.get("ws_stage_payload") or {}
    data = payload.get("data") or {}
    warning = data.get("fairness_warning")
    assert warning is not None
    assert warning["kind"] == "questions_dropped"
    assert warning["dropped_count"] == 1
    assert data.get("dropped_questions") == dropped


def test_route_after_jd_terminates_when_fairness_blocks():
    """When fairness blocks the JD stage, routing must NOT loop back to intake."""
    from app.domains.job_creation import graph as job_graph

    state = {
        "jd_approved": False,
        "jd_quality_score": 0.0,
        "jd_fairness_blocked": True,
    }
    assert job_graph.route_after_jd(state) == "end"


def test_jd_blocked_input_then_router_terminates_no_loop():
    """Integrated: discriminatory input → node returns blocked state →
    router must terminate (`end`), never loop back to `intake`."""
    from app.domains.job_creation import graph as job_graph

    fake_service = MagicMock()
    state = {
        "raw_input": "Vaga apenas para homens jovens, sem deficiencia",
        "jd_raw": "Vaga apenas para homens jovens, sem deficiencia",
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_jd_service", return_value=fake_service):
        result = job_graph.jd_enrichment_node(state)

    assert result.get("jd_fairness_blocked") is True
    assert job_graph.route_after_jd(result) == "end"


def test_jd_recovers_after_fairness_block_when_recruiter_retries():
    """Regression: after a fairness block, a clean retry in the same session
    must clear the per-attempt flag and proceed to the next stage."""
    from app.domains.job_creation import graph as job_graph

    fake_enriched = SimpleNamespace(
        model_dump=lambda: {
            "about_role": "Procuramos PM senior para liderar squad.",
            "responsabilidades": ["Mentor"],
            "skills_obrigatorias": [{"skill": "produto"}],
        }
    )
    fake_service = MagicMock()
    fake_service.enrich.return_value = (fake_enriched, 80.0, [])

    # First attempt — discriminatory input, blocked + router ends.
    state = {
        "raw_input": "Vaga apenas para homens jovens",
        "jd_raw": "Vaga apenas para homens jovens",
        "stage_history": [],
    }
    blocked = job_graph.jd_enrichment_node(state)
    assert blocked["jd_fairness_blocked"] is True
    assert job_graph.route_after_jd(blocked) == "end"

    # Second attempt — recruiter rewrites with clean input, same session.
    retry_state = {
        **blocked,
        "raw_input": "Procuramos PM senior para liderar squad",
        "jd_raw": "Procuramos PM senior para liderar squad",
        "jd_approved": None,
    }
    with patch.object(job_graph, "_get_jd_service", return_value=fake_service):
        recovered = job_graph.jd_enrichment_node(retry_state)

    assert recovered.get("jd_fairness_blocked") is False
    # When approval is required (not yet given) the router parks at end,
    # but it must not return "end" because of the stale fairness flag.
    assert job_graph.route_after_jd(
        {**recovered, "jd_approved": True, "jd_quality_score": 80.0}
    ) == "bigfive"


def test_bigfive_node_blocks_discriminatory_input():
    """If the enriched JD already contains banned terms, skip the Big Five LLM."""
    from app.domains.job_creation import graph as job_graph

    fake_gen = MagicMock()
    state = {
        "jd_enriched": {
            "about_role": "Vaga apenas para homens jovens",
            "responsabilidades": [],
            "skills_obrigatorias": [],
        },
        "stage_history": [],
    }

    with patch.object(job_graph, "_get_wsi_generator", return_value=fake_gen):
        job_graph.bigfive_node(state)

    fake_gen.extract_bigfive.assert_not_called()


# ---------------------------------------------------------------------------
# Audit emission at handoff
# ---------------------------------------------------------------------------

def test_handoff_node_emits_single_job_creation_audit():
    from app.domains.job_creation import graph as job_graph

    log_mock = AsyncMock()

    with patch("app.shared.compliance.audit_service.AuditService") as svc_cls, \
         patch("app.domains.job_creation.compliance._run_async", lambda coro: coro.close()):
        svc_cls.return_value.log_decision = log_mock

        state = {
            "workspace_id": 42,
            "raw_input": "Quero um PM senior",
            "jd_enriched": {"about_role": "PM senior"},
            "wsi_questions": [{"question": "q1"}],
            "seniority_resolved": "senior",
            "screening_mode": "compact",
            "jd_quality_score": 78.0,
            "job_id": 999,
            "stage_history": [],
        }
        job_graph.handoff_node(state)

    assert svc_cls.return_value.log_decision.call_count == 1
    kwargs = svc_cls.return_value.log_decision.call_args.kwargs
    assert kwargs["decision_type"] == "job_creation"
    assert kwargs["company_id"] == "42"
    assert kwargs["job_vacancy_id"] == "999"
    # prompt_hash + model captured in reasoning
    reasoning_str = " ".join(str(r) for r in kwargs["reasoning"])
    assert "prompt_hash=" in reasoning_str
    assert "model=" in reasoning_str
