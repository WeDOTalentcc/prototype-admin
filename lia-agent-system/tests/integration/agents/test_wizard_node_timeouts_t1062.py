"""Sentinela offline — Task #1062.

Garante que os 3 nós LLM-bound do graph `JobCreation` (`bigfive`, `salary`,
`wsi_questions`) honram timeouts configuráveis via env e caem em fallback
determinístico quando o LLM/serviço externo demora demais. Espelha o padrão
canônico de `LIA_JD_ENRICHMENT_TIMEOUT_S` (D4 da auditoria #1058).

Estratégia: monkeypatcha os helpers (`_get_wsi_generator`, módulos internos
do `salary_node`) para simular um LLM lento (sleep > timeout). O fallback
determinístico precisa preencher o estado mesmo com timeout 0.001s.
"""
from __future__ import annotations

import time

import pytest

from app.domains.job_creation import graph as graph_mod
from app.domains.job_creation.graph import (
    bigfive_node,
    jd_enrichment_node,
    salary_node,
    wsi_questions_node,
)
from app.domains.job_creation.schemas import (
    BigFiveExtraction,
    EnrichedJobDescription,
    GeneratedQuestion,
)


def _enriched_dict() -> dict:
    return EnrichedJobDescription(
        titulo_padronizado="Engenheiro Backend Pleno",
        senioridade_confirmada="pleno",
        about_role="Construir APIs REST resilientes em Python.",
        responsabilidades=["Desenvolver endpoints", "Revisar PRs"],
        skills_obrigatorias=[],
        competencias_comportamentais=[],
    ).model_dump()


class _SlowGenerator:
    """Stub que simula LLM lento — sempre dorme > qualquer timeout sensato."""

    def extract_bigfive(self, _enriched):
        time.sleep(2.0)
        return BigFiveExtraction(
            openness=0.99, conscientiousness=0.99, extraversion=0.99,
            agreeableness=0.99, stability=0.99,
        )

    def rank_traits(self, bigfive, seniority, *_a, **_kw):
        return [{"trait": "openness", "score": bigfive.openness, "rank": 1, "weight": 1.0}]

    def generate_questions(self, *, enriched, seniority, distribution, trait_rankings):
        time.sleep(2.0)
        return [GeneratedQuestion(
            question="should-not-appear",
            ideal_answer="-",
            framework="CBI",
            block="technical",
            competency="technical",
            skill="x",
            weight=1.0,
        )]

    def _fallback_questions(self, block, count):
        # Re-usa a fallback real do generator canônico para realismo do trait
        from app.domains.job_creation.services.wsi_question_generator import (
            WSIQuestionGenerator,
        )
        return WSIQuestionGenerator._fallback_questions(self, block, count)


# ─────────────────────────────────────────────────────────────────────────────
# jd_enrichment_node — Task #1065 fallback flag (timeout surfaces to UI)
# ─────────────────────────────────────────────────────────────────────────────


class _SlowJdService:
    """Stub que simula JdEnrichmentService.enrich() lento."""

    def enrich(self, *_a, **_kw):
        time.sleep(2.0)
        return (
            EnrichedJobDescription(
                titulo_padronizado="should-not-appear",
                senioridade_confirmada="pleno",
                about_role="-",
                responsabilidades=[],
                skills_obrigatorias=[],
                competencias_comportamentais=[],
            ),
            99.0,
            [],
        )

    def _fallback_enrichment(self, jd_raw, title, seniority):
        from app.domains.job_creation.services.jd_enrichment import (
            JdEnrichmentService,
        )
        return JdEnrichmentService._fallback_enrichment(
            self, jd_raw, title, seniority,
        )


def test_jd_enrichment_node_timeout_flags_fallback(monkeypatch):
    """Em timeout do LLM, payload sinaliza `jd_enrichment_used_fallback=True`.

    Pendencia 3 update (2026-05-27): pos Fix D (commit 8c5f53ddd),
    `_classifier_eligible` nao depende mais de `_has_parsed_title`. Sem
    mockar o classifier, ele intercepta antes do LLM call em scenarios com
    raw_input curto -> guard dispara antes do timeout. Pra reproduzir o
    cenario canonical (LLM timeout), patchamos o classifier pra retornar
    intent='provides_jd_intent' que segue direto pro enrichment.
    """
    monkeypatch.setenv("LIA_JD_ENRICHMENT_TIMEOUT_S", "0.05")
    monkeypatch.setattr(graph_mod, "_get_jd_service", lambda: _SlowJdService())

    # Force classifier-first path para enrichment (provides_jd_intent => skip guard)
    from app.domains.job_creation.services.intake_intent_classifier import (
        IntakeIntentOutput,
    )

    class _MockProvidesJdClassifier:
        def classify_sync(self, **kwargs):
            return IntakeIntentOutput(
                intent="provides_jd_intent",
                confidence=0.95,
                conversational_reply="(mock - segue pro enrichment)",
            )

    monkeypatch.setattr(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        lambda: _MockProvidesJdClassifier(),
    )

    state = {
        "raw_input": "Engenheiro Backend Pleno em Python",
        "parsed_title": "Engenheiro Backend",
        "parsed_seniority": "pleno",
    }
    out = jd_enrichment_node(state)
    payload_data = (out.get("ws_stage_payload") or {}).get("data") or {}
    assert payload_data.get("jd_enrichment_used_fallback") is True, (
        "jd_enrichment fallback deveria ser sinalizado para o painel"
    )
    # Task #1067 — root-cause label propagado ao painel
    assert payload_data.get("jd_enrichment_fallback_reason") == "timeout", (
        "jd_enrichment fallback_reason='timeout' deveria ser propagado"
    )
    # Conteúdo do fallback (não o stub lento) deve ter chegado ao state
    assert out.get("jd_enriched"), "fallback deveria popular jd_enriched"


# ─────────────────────────────────────────────────────────────────────────────
# bigfive_node
# ─────────────────────────────────────────────────────────────────────────────

def test_bigfive_node_timeout_falls_back_to_defaults(monkeypatch):
    """Em timeout, `BigFiveExtraction()` defaults (0.5 across traits) é usado."""
    monkeypatch.setenv("LIA_BIGFIVE_TIMEOUT_S", "0.05")
    monkeypatch.setattr(graph_mod, "_get_wsi_generator", lambda: _SlowGenerator())
    # Bypass policy gate
    monkeypatch.setattr(
        graph_mod, "evaluate_wizard_policy",
        lambda *_a, **_kw: type("R", (), {
            "decision": __import__(
                "app.domains.job_creation.policy_gate", fromlist=["PolicyDecision"]
            ).PolicyDecision.ALLOW,
            "rationale": "ok",
        })(),
    )
    state = {
        "jd_enriched": _enriched_dict(),
        "parsed_seniority": "pleno",
    }
    out = bigfive_node(state)
    profile = out.get("bigfive_profile") or {}
    # Defaults of BigFiveExtraction() são 0.5 — confirma fallback (não 0.99 do stub)
    assert profile.get("openness") == 0.5
    assert profile.get("conscientiousness") == 0.5
    # Trait ranking ainda é determinístico — deve existir
    assert out.get("trait_rankings"), "rank_traits deveria rodar mesmo no fallback"
    # Task #1065 — flag de fallback propagada no ws_stage_payload.data
    payload_data = (out.get("ws_stage_payload") or {}).get("data") or {}
    assert payload_data.get("bigfive_used_fallback") is True, (
        "bigfive fallback deveria ser sinalizado para o painel"
    )
    # Task #1067 — root-cause label propagado ao painel
    assert payload_data.get("bigfive_fallback_reason") == "timeout", (
        "bigfive fallback_reason='timeout' deveria ser propagado"
    )


# ─────────────────────────────────────────────────────────────────────────────
# salary_node
# ─────────────────────────────────────────────────────────────────────────────

def test_salary_node_timeout_skips_benchmark_gracefully(monkeypatch):
    """Em timeout, `salary_benchmark` fica `None` e no completa sem travar.

    Pendencia 3 update (2026-05-27): pos Fix J + harness-engineering PR-14
    (run_coro_in_threadpool canonical), mock precisa ser direto no helper.
    Patchar asyncio.run nao funciona porque o helper usa o path "no loop"
    (asyncio.run direto) que ignora timeout em test sync context. Solucao
    canonical: patchar run_coro_in_threadpool para lancar TimeoutError
    diretamente, simulando o cenario real (ThreadPoolExecutor timeout).
    """
    import concurrent.futures as _cf
    monkeypatch.setenv("LIA_SALARY_TIMEOUT_S", "0.05")

    # Patch canonical: run_coro_in_threadpool sempre raise TimeoutError pra
    # forcar o branch except _cf_sl.TimeoutError no salary_node.
    def _raise_timeout(coro_factory, timeout=None):
        # Drena o coroutine pra evitar RuntimeWarning never-awaited
        try:
            coro = coro_factory()
            coro.close()
        except Exception:
            pass
        raise _cf.TimeoutError("simulated timeout for test_salary_node_timeout")

    # Patch no modulo salary onde run_coro_in_threadpool foi importado (Fix J).
    monkeypatch.setattr(
        "app.domains.job_creation.nodes.salary.run_coro_in_threadpool",
        _raise_timeout,
    )

    state = {
        "parsed_title": "Engenheiro Backend",
        "parsed_seniority": "pleno",
        "company_id": "00000000-0000-4000-a000-000000000001",
    }
    t0 = time.time()
    out = salary_node(state)
    elapsed = time.time() - t0

    # Deve retornar bem rapido (timeout 0.05s + overhead) -- NUNCA esperar 2s
    assert elapsed < 1.5, f"salary_node demorou {elapsed:.2f}s (timeout nao respeitado)"
    assert out.get("current_stage") == "salary"
    # Benchmark não foi populado (graceful skip)
    assert not out.get("salary_benchmark")
    # Task #1065 — flag de fallback propagada no ws_stage_payload.data
    payload_data = (out.get("ws_stage_payload") or {}).get("data") or {}
    assert payload_data.get("salary_used_fallback") is True, (
        "salary fallback deveria ser sinalizado para o painel"
    )
    # Task #1067 — root-cause label propagado ao painel
    assert payload_data.get("salary_fallback_reason") == "timeout", (
        "salary fallback_reason='timeout' deveria ser propagado"
    )


# ─────────────────────────────────────────────────────────────────────────────
# wsi_questions_node
# ─────────────────────────────────────────────────────────────────────────────

def test_wsi_questions_node_timeout_uses_deterministic_fallback(monkeypatch):
    """Em timeout, perguntas vêm de `_fallback_questions` (CBI mínimo)."""
    monkeypatch.setenv("LIA_WSI_QUESTIONS_TIMEOUT_S", "0.05")
    monkeypatch.setattr(graph_mod, "_get_wsi_generator", lambda: _SlowGenerator())
    monkeypatch.setattr(
        graph_mod, "evaluate_wizard_policy",
        lambda *_a, **_kw: type("R", (), {
            "decision": __import__(
                "app.domains.job_creation.policy_gate", fromlist=["PolicyDecision"]
            ).PolicyDecision.ALLOW,
            "rationale": "ok",
        })(),
    )
    state = {
        "jd_enriched": _enriched_dict(),
        "question_distribution": {"technical": 2, "behavioral": 1},
        "seniority_resolved": "pleno",
        "trait_rankings": [],
    }
    out = wsi_questions_node(state)
    questions = out.get("wsi_questions") or []
    # Fallback gera 1 pergunta por bloco (count é só para o weight)
    assert len(questions) >= 2, f"esperava ≥2 perguntas fallback, veio {len(questions)}"
    # Nenhuma pergunta veio do stub lento
    for q in questions:
        assert q.get("question") != "should-not-appear", (
            "fallback deveria substituir totalmente as perguntas do LLM lento"
        )
    # Frameworks são CBI (regra absoluta WSI)
    assert all(q.get("framework") == "CBI" for q in questions)
    # Task #1065 — flag de fallback propagada no ws_stage_payload.data
    payload_data = (out.get("ws_stage_payload") or {}).get("data") or {}
    assert payload_data.get("wsi_questions_used_fallback") is True, (
        "wsi_questions fallback deveria ser sinalizado para o painel"
    )
    # Task #1067 — root-cause label propagado ao painel
    assert payload_data.get("wsi_questions_fallback_reason") == "timeout", (
        "wsi_questions fallback_reason='timeout' deveria ser propagado"
    )
