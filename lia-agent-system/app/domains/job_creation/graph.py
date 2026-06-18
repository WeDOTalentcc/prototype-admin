"""
JobCreationGraph — LangGraph state machine for the Wizard WSI pipeline.

Maps WSI Bloco A (F1-F6) + publish + calibration + handoff into a
conversational wizard flow with 2 HITL approval points.

Pattern follows scheduling/graph.py: StateGraph, conditional edges,
checkpointer for session persistence, singleton access.

HITL points:
  - jd_enrichment (F1): recruiter approves enriched JD
  - wsi_questions (F6): recruiter approves generated questions

Invariant — data.message obrigatório (Task #1099, generaliza Task #1096):
  Todo node deste graph que retorna ``current_stage`` setado DEVE incluir
  ``ws_stage_payload.data["message"]`` truthy. Sem essa mensagem, o
  ``WizardSessionService`` (path canônico WS/SSE) não encontra uma frase
  natural para devolver ao chat, cai em ``_emit_silent_fallback`` (Task
  #1089) e o recrutador vê o fail-loud
  ``[ATENÇÃO: estado inconsistente — contate suporte]``. Em paths normais
  os ``*_gate_node`` populam ``gate_clarify_message``, que tem precedência
  no consumer; mas em paths de erro/retry/policy DENY/FairnessGuard PRE-BLOCK
  o gate não roda e a mensagem do node é o ÚNICO fallback. A sentinela
  arquitetural ``tests/integration/agents/test_wizard_node_messages_t1099.py``
  exercita os 9 nodes (``bigfive``, ``salary``, ``competency``,
  ``wsi_questions``, ``eligibility``, ``review``, ``publish``, ``calibration``,
  ``handoff``) — adicionar um 10º node sem ``data.message`` quebra o build.
"""

import logging
import os
import time
from pathlib import Path
from functools import lru_cache as _lru_cache
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END


# Generic utils moved to internal/utils.py (PR-17 step 2 ONDA 3 follow-up)
from app.domains.job_creation.internal.utils import (  # noqa: F401
    _extract_last_turns,
    _min_jd_quality_threshold,
    _try_meta_helper,
    _in_graph_runtime,
    _llm_gates_enabled,
)

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
from app.domains.job_creation.services.seniority_resolver import resolve_seniority
from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator
from app.domains.job_creation.api_client import JobCreationAPIClient
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.intake_audit import emit_intake_audit
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.audit_actions import PipelineTemplateAuditAction
from app.domains.job_creation import dispatch_messages as _wizard_dispatch

logger = logging.getLogger(__name__)

# PR-8 ONDA 3 / F-3.4 + F-3.5: Prometheus counters canonical pattern
# (replicado de app/services/voice/wsi_pipeline.py:30-55 race-safe REGISTRY lookup).
#
# - lia_wizard_fairness_l4_check_failed_total: increment quando Layer 4
#   fairness guard exceptiona em wsi_questions_node (antes era silent).
# - lia_wizard_sourcing_mode_default_total: increment quando publish_node
#   recebe sourcing_mode=None e cai no default "local" (UI faltou setar).
try:
    from prometheus_client import REGISTRY as _WIZ_PROM_REGISTRY
    from prometheus_client import Counter as _WIZ_PromCounter

    _L4_METRIC_NAME = "lia_wizard_fairness_l4_check_failed_total"
    _existing_l4 = getattr(_WIZ_PROM_REGISTRY, "_names_to_collectors", {}).get(
        _L4_METRIC_NAME
    )
    if _existing_l4 is not None:
        lia_wizard_fairness_l4_check_failed_total = _existing_l4
    else:
        lia_wizard_fairness_l4_check_failed_total = _WIZ_PromCounter(
            _L4_METRIC_NAME,
            "Layer 4 fairness check failures in wsi_questions_node "
            "(currently silent fail-open -- questions kept as recruiter input). "
            "PR-8 ONDA 3 / F-3.4.",
            labelnames=("node", "reason"),
        )

    _SOURCING_METRIC_NAME = "lia_wizard_sourcing_mode_default_total"
    _existing_sm = getattr(_WIZ_PROM_REGISTRY, "_names_to_collectors", {}).get(
        _SOURCING_METRIC_NAME
    )
    if _existing_sm is not None:
        lia_wizard_sourcing_mode_default_total = _existing_sm
    else:
        lia_wizard_sourcing_mode_default_total = _WIZ_PromCounter(
            _SOURCING_METRIC_NAME,
            "sourcing_mode fell back to default 'local' (UI selector missing). "
            "PR-8 ONDA 3 / F-3.5.",
            labelnames=("stage",),
        )
except (ImportError, ValueError):  # pragma: no cover
    lia_wizard_fairness_l4_check_failed_total = None
    lia_wizard_sourcing_mode_default_total = None


# WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO moved to internal/constants.py (PR-17 ONDA 3 follow-up)
from app.domains.job_creation.internal.constants import (  # noqa: E402, F401
    WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO,
)

# Service singletons moved to internal/services.py (PR-17 step 3 ONDA 3 follow-up)
from app.domains.job_creation.internal.services import (  # noqa: F401
    _get_jd_service,
    _get_wsi_generator,
)


# Telemetry helpers moved to internal/telemetry.py (PR-17 step 5 ONDA 3 follow-up)
from app.domains.job_creation.internal.telemetry import (  # noqa: F401
    _emit_fallback_telemetry,
    _emit_wizard_fallback_metric,
)


# _get_api_client moved to internal/services.py (PR-17 step 3 ONDA 3 follow-up)
from app.domains.job_creation.internal.services import _get_api_client  # noqa: F401


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pipeline template suggestion (Task #1055)
# ---------------------------------------------------------------------------
# Determinístico, sem LLM e sem DB. Espelha a heurística de
# `app/api/v1/recruitment_journey.py:ai_suggest_template` (keyword-based) para
# garantir que o frontend renderize o `WizardPipelineTemplateCard`
# (`[data-testid="wizard-template-card"]`) já no primeiro turno do wizard,
# mesmo se Gemini estiver em 429 ou `/api/v1/company/culture-stack` em 500.
#
# Contrato consumido em `plataforma-lia/.../wizard-plan-card.ts::buildPipelineTemplateCard`:
#   data.suggestions_data.pipeline_template = {
#       "suggested_type": <"technical"|"executive"|"operational"|"mass_hiring"|"intern">,
#       "templates": [<id>, ...]   # ordem canônica dos 5 presets
#   }
# Pipeline template constants moved to internal/constants.py (PR-17 ONDA 3 follow-up)
from app.domains.job_creation.internal.constants import (  # noqa: E402, F401
    _PIPELINE_TEMPLATE_IDS,
    _EXECUTIVE_KEYWORDS,
    _TECHNICAL_KEYWORDS,
    _OPERATIONAL_KEYWORDS,
    _INTERN_KEYWORDS,
)


# Pipeline template helpers moved to internal/pipeline_template_helpers.py (PR-17 step 5)
from app.domains.job_creation.internal.pipeline_template_helpers import (  # noqa: F401
    _suggest_pipeline_template,
    _build_pipeline_template_db_suggestion,
    _apply_pipeline_template_to_state,
)

# ---------------------------------------------------------------------------
# Canonical DB-based pipeline template suggestion
# (Sprint Pipeline Templates 2026-05-26 — Fase 1.6)
# ---------------------------------------------------------------------------
# Complementa o heurístico determinístico _suggest_pipeline_template (Task #1055)
# consultando o repositório real (PipelineTemplateRepository.list_for_suggestion)
# com scoring baseado em department_hint / seniority_hint / job_family_hint.
#
# Fail-open: qualquer erro retorna None. O caller (intake_node / jd_enrichment_node)
# continua emitindo o heurístico legacy. Frontend WizardPipelineTemplateCard pode
# preferir o canonical (com template_id real + score) quando presente.


# ---------------------------------------------------------------------------
# Wizard step audit helper (Task #1061 — EU AI Act Art.13 / SOX)
# ---------------------------------------------------------------------------
# Cada node decisório (`bigfive`, `wsi_questions`, `competency`,
# `eligibility`) emite uma audit row com `decision_type=wizard_step_completed`
# ao concluir. Espelha o padrão de `audit_company_change` em
# `company_settings`: `before/after/target_id/trace_id` ficam em `reasoning`.
# Fail-open por design — falha de audit NUNCA bloqueia o wizard, mas a
# sentinela offline garante que o call site existe.
# Audit emitters moved to internal/audit.py (PR-17 step 4 ONDA 3 follow-up)
from app.domains.job_creation.internal.audit import (  # noqa: F401
    _emit_wizard_step_audit,
    _emit_pipeline_template_audit,
    _emit_jd_gate_audit,
    _emit_competency_gate_audit,
    _emit_wsi_questions_gate_audit,
    _emit_review_gate_audit,
)


# ---------------------------------------------------------------------------
# Wizard fallback observability (Task #1068)
# ---------------------------------------------------------------------------
# Cada um dos 4 nodes com fallback determinístico (jd_enrichment, bigfive,
# salary, wsi_questions — Tasks #1062 + #1065) chama este helper quando cai
# para o caminho fallback. Emite:
#   1. Log estruturado WARNING com `metric=wizard_fallback` + extras
#      (node, tenant_id, reason, timeout_s, elapsed_ms) — consumido pelo
#      `JSONFormatter` em `app/shared/structured_logging.py`, ficando como
#      campos de primeira classe no log JSON para que ELK/CloudWatch/Datadog
#      filtrem por `data.metric:wizard_fallback` e agrupem por
#      `data.node` + `data.tenant_id`.
#   2. Sentry breadcrumb (categoria `wizard.fallback`) + `capture_message`
#      WARNING com tags `wizard.node`, `wizard.fallback_reason`, `tenant_id`
#      — habilita gráficos de "fallback rate por node por dia" e alertas
#      `count_unique(message:"wizard fallback") > X em 1h` no Sentry.
# Fail-open por design — falha de telemetria NUNCA bloqueia o wizard.
# _WIZARD_FALLBACK_NODES moved to internal/constants.py (PR-17 ONDA 3 follow-up)
from app.domains.job_creation.internal.constants import (  # noqa: E402, F401
    _WIZARD_FALLBACK_NODES,
)


# intake_node moved to nodes/intake.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.intake import intake_node  # noqa: F401, E402
from app.domains.job_creation.nodes.intake_gate import (  # noqa: F401, E402
    intake_gate_node, route_after_intake_gate,
)


# jd_enrichment_node moved to nodes/jd_enrichment.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.jd_enrichment import jd_enrichment_node  # noqa: F401, E402


# pipeline_template_node moved to nodes/pipeline_template.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.pipeline_template import pipeline_template_node  # noqa: F401, E402


# bigfive_node moved to nodes/bigfive.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.bigfive import bigfive_node  # noqa: F401, E402


# salary_node moved to nodes/salary.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.salary import salary_node  # noqa: F401, E402


# competency_node moved to nodes/competency.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.competency import competency_node  # noqa: F401, E402

# benefits + variable_comp nodes (2026-06-18) -- inferencia + confirmacao assistida
from app.domains.job_creation.nodes.benefits import benefits_node  # noqa: F401, E402
from app.domains.job_creation.nodes.variable_comp import variable_comp_node  # noqa: F401, E402


# wsi_questions_node moved to nodes/wsi_questions.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.wsi_questions import wsi_questions_node  # noqa: F401, E402


# eligibility_node moved to nodes/eligibility.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.eligibility import eligibility_node  # noqa: F401, E402


# review_node moved to nodes/review.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.review import review_node  # noqa: F401, E402


# publish_node moved to nodes/publish.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.publish import publish_node  # noqa: F401, E402


# calibration_node moved to nodes/calibration.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.calibration import calibration_node  # noqa: F401, E402


# handoff_node moved to nodes/handoff.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.handoff import handoff_node  # noqa: F401, E402


# ---------------------------------------------------------------------------
# T2 (Task #1085) — LLM-based gate node for HITL #1 (jd_enrichment)
# ---------------------------------------------------------------------------
#
# Substitui o classifier brittle keyword-based de
# ``app/domains/job_creation/domain.py::_route_by_stage`` por uma camada LLM
# (Claude Haiku, temp=0) com schema Pydantic obrigatório, allowlist enforced
# e mutação de state DETERMINÍSTICA baseada em ``intent`` ∈ ALLOWED_INTENTS.
#
# **Vetor de prompt injection:** o output do LLM é validado por Pydantic +
# allowlist no classifier. Aqui apenas mapeamos ``intent`` → mutação fixa.
# NUNCA invocamos ``eval()``/``exec()`` sobre o output, e ``conversational_reply``
# nunca é usado como controle de fluxo (apenas devolvido como mensagem).
#
# **Compatibilidade com pattern de resume END-then-resume da codebase:** a
# codebase NÃO usa ``langgraph.types.interrupt`` em lugar nenhum (verificado).
# Em vez de introduzir interrupt() de Once, que exigiria mudar todos os
# callers (``domain.py``, ``graph_runner``, testes), o gate_node opera no
# mesmo pattern dos demais HITLs: quando ``state['gate_resume_message']``
# está vazio, retorna state como está e ``route_after_gate`` devolve ``end``
# (semanticamente equivalente a ``interrupt``); quando o caller faz
# ``graph.resume(thread_id, prior_state, {'gate_resume_message': msg})``,
# o nó classifica o intent e roteia. Isso preserva ``pw-cenario-A/B/C/D``,
# ``T-A → T-F`` e o ``wizard_session_pin`` Tier 0.5 do CascadedRouter.
# jd_gate_node moved to nodes/jd_gate.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.jd_gate import jd_gate_node  # noqa: F401, E402


# competency_gate_node moved to nodes/competency_gate.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.competency_gate import competency_gate_node  # noqa: F401, E402


def route_after_competency_gate(state: JobCreationState) -> str:
    """Routing após competency_gate_node LLM. Determinístico baseado em
    mutações aplicadas pelo gate.

    Sprint F.2 fix — self-loop on non-terminal intent (ask_question /
    undecided / low_confidence clarify). Antes (bug): routing retornava
    ``end`` e graph completava sem interrupt → próximo turno o wizard
    reiniciava do intake (``is_interrupted=False``). Agora: routing
    retorna ``competency_gate`` (self), graph re-entra no node, o bloco
    ``if not msg and _in_graph_runtime(): interrupt()`` pausa o graph
    canonicamente. Próximo turno: ``is_interrupted=True`` →
    ``aresume_with_message`` funciona como esperado. State mutations
    (``gate_clarify_message``) são preservadas via return do node
    anterior antes do self-loop."""
    if state.get("fairness_blocked") is True:
        logger.info("[JobCreation:route] competency_gate -> END (fairness blocked)")
        return "end"
    mode = state.get("screening_mode")
    if mode in ("compact", "full"):
        logger.info("[JobCreation:route] competency_gate -> wsi_questions (mode=%s)", mode)
        return "wsi_questions"
    # ask_question / undecided / low_confidence / pending — Sprint F.2 fix:
    # self-loop em vez de END para que o interrupt() canônico no topo do
    # gate pause o graph (caso contrário is_interrupted=False no próximo
    # turno e wizard reinicia do intake — bug validado em produção).
    intent = state.get("gate_last_intent")
    logger.info(
        "[JobCreation:route] competency_gate -> competency_gate (intent=%s, self-loop to interrupt)",
        intent,
    )
    return "competency_gate"


def route_after_gate(state: JobCreationState) -> str:
    """Routing após gate_node LLM. Determinístico baseado em mutações
    aplicadas por ``jd_gate_node``.

    Sprint F.2 fix — self-loop em ask_question / off_topic (mesma classe
    de bug do competency_gate / wsi_questions_gate). Sem self-loop, graph
    completa sem interrupt quando usuário faz pergunta em vez de aprovar
    → próximo turno reinicia do intake. Approve / reject_with_feedback /
    provide_new_content NÃO precisam de self-loop porque já roteiam para
    estados terminais (bigfive/intake) ou para outro fluxo definido."""
    if state.get("jd_fairness_blocked") is True:
        logger.info("[JobCreation:route] jd_gate -> END (fairness blocked)")
        return "end"

    intent = state.get("gate_last_intent")
    if intent == "provide_new_content" and state.get("jd_approved") is False:
        logger.info("[JobCreation:route] jd_gate -> intake (new content provided)")
        return "intake"

    approved = state.get("jd_approved")
    if approved is True:
        quality = state.get("jd_quality_score", 0.0) or 0.0
        _min_q = _min_jd_quality_threshold()
        if quality < _min_q:
            logger.info(
                "[JobCreation:route] jd_gate -> END (quality %.1f < %.1f, "
                "configurable via LIA_WIZARD_MIN_JD_QUALITY)",
                quality, _min_q,
            )
            return "end"
        logger.info("[JobCreation:route] jd_gate -> bigfive (approved, quality=%.1f)", quality)
        return "bigfive"

    # ask_question / off_topic / pending — Sprint F.2 fix: self-loop para
    # que interrupt() canônico no topo do gate pause o graph; sem isso o
    # próximo turno do recrutador reinicia o wizard do intake.
    logger.info(
        "[JobCreation:route] jd_gate -> jd_gate (intent=%s, self-loop to interrupt)",
        intent,
    )
    return "jd_gate"


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_jd(state: JobCreationState) -> str:
    """After JD enrichment: if HITL pending (not yet approved), END (wait for user).
    If approved and quality >= 50, proceed to bigfive.
    If quality < 30, loop back (recruiter must improve JD).
    If fairness blocked, terminate without looping back.
    """
    approved = state.get("jd_approved")
    quality = state.get("jd_quality_score", 0.0)

    # Fairness block: recruiter must rewrite the input — end (not intake loop)
    if state.get("jd_fairness_blocked") is True:
        logger.info("[JobCreation:route] jd_enrichment -> END (fairness blocked)")
        return "end"

    if approved is None:
        # Waiting for recruiter approval — END to return control
        logger.info("[JobCreation:route] jd_enrichment -> END (awaiting approval)")
        return "end"

    if not approved:
        # Recruiter rejected — they'll provide new input, restart from intake
        logger.info("[JobCreation:route] jd_enrichment -> intake (rejected)")
        return "intake"

    _min_q = _min_jd_quality_threshold()
    if quality < _min_q:
        logger.info(
            "[JobCreation:route] jd_enrichment -> END (quality %.1f < %.1f, "
            "blocked — configurable via LIA_WIZARD_MIN_JD_QUALITY)",
            quality, _min_q,
        )
        return "end"

    logger.info("[JobCreation:route] jd_enrichment -> bigfive (approved, quality=%.1f)", quality)
    return "bigfive"


def route_after_competency(state: JobCreationState) -> str:
    """After competency: need screening_mode chosen to proceed."""
    if not state.get("screening_mode"):
        logger.info("[JobCreation:route] competency -> END (awaiting mode selection)")
        return "end"
    logger.info("[JobCreation:route] competency -> wsi_questions")
    return "wsi_questions"


# wsi_questions_gate_node moved to nodes/wsi_questions_gate.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.wsi_questions_gate import wsi_questions_gate_node  # noqa: F401, E402


def route_after_wsi_questions_gate(state: JobCreationState) -> str:
    """Routing após wsi_questions_gate_node LLM. Determinístico baseado
    em mutações aplicadas pelo gate.

    Sprint F.2 fix — self-loop on non-terminal intent (ask_question /
    low_confidence clarify / remove_question com pacote reduzido).
    Mesma motivação do ``route_after_competency_gate``: sem self-loop,
    graph completa sem interrupt → wizard reinicia próximo turno."""
    if state.get("fairness_blocked") is True:
        logger.info("[JobCreation:route] wsi_questions_gate -> END (fairness blocked)")
        return "end"
    if state.get("questions_approved") is True:
        logger.info("[JobCreation:route] wsi_questions_gate -> eligibility (approved)")
        return "eligibility"
    if state.get("wsi_regenerate_pending") is True:
        logger.info("[JobCreation:route] wsi_questions_gate -> wsi_questions (regen pending)")
        return "wsi_questions"
    # ask_question / low_confidence / remove_question (pacote reduzido aguardando
    # re-aprovação) — Sprint F.2 fix: self-loop para que interrupt() canônico
    # no topo do gate pause o graph.
    intent = state.get("gate_last_intent")
    logger.info(
        "[JobCreation:route] wsi_questions_gate -> wsi_questions_gate (intent=%s, self-loop to interrupt)",
        intent,
    )
    return "wsi_questions_gate"


def route_after_questions(state: JobCreationState) -> str:
    """After WSI questions: HITL point 2 — recruiter must approve all questions."""
    approved = state.get("questions_approved")

    if approved is None:
        logger.info("[JobCreation:route] wsi_questions -> END (awaiting approval)")
        return "end"

    if not approved:
        # Recruiter wants to regenerate — loop back to questions
        logger.info("[JobCreation:route] wsi_questions -> wsi_questions (regenerate)")
        return "wsi_questions"

    logger.info("[JobCreation:route] wsi_questions -> eligibility")
    return "eligibility"


def route_after_review(state: JobCreationState) -> str:
    """After review: check readiness."""
    readiness = state.get("readiness_check", {})
    if readiness.get("ready"):
        logger.info("[JobCreation:route] review -> publish")
        return "publish"
    logger.info("[JobCreation:route] review -> END (not ready)")
    return "end"


# ---------------------------------------------------------------------------
# T6 (Task #1088) — review gate (LLM-based, HITL #3)
# ---------------------------------------------------------------------------

# Review gate constants moved to internal/constants.py (PR-17 ONDA 3 follow-up)
from app.domains.job_creation.internal.constants import (  # noqa: E402, F401
    _REVIEW_DESTINATIONS_ALLOWLIST,
    _REVIEW_TARGET_SECTION_TO_NODE,
    _REVIEW_VALID_TARGET_SECTIONS,
)


def _resolve_effective_destinations_allowlist(state: JobCreationState) -> tuple[frozenset[str], bool]:
    """T6 — resolve allowlist EFETIVA de destinos para o tenant.

    Retorna ``(allowlist, is_tenant_constrained)``. Quando o state contém
    ``tenant_enabled_ats`` populado por upstream (TenantAwareAgentMixin /
    settings hub), o gate INTERSECTA com ``_REVIEW_DESTINATIONS_ALLOWLIST``
    canônica e usa essa intersecção como gate de validação. Quando vazio,
    fail-soft para a allowlist canônica completa (com warning) — preserva
    UX em dev/onboarding sem ATS configurado.

    Crítico para o code review T6: pedir um canal NÃO habilitado pelo
    tenant agora produz clarify fail-loud, não um silent allow.
    """
    raw = state.get("tenant_enabled_ats") or []
    if not isinstance(raw, list) or not raw:
        return _REVIEW_DESTINATIONS_ALLOWLIST, False
    tenant_set = frozenset(
        str(d).strip().lower() for d in raw
        if str(d).strip().lower() in _REVIEW_DESTINATIONS_ALLOWLIST
    )
    if not tenant_set:
        # tenant_enabled_ats existe mas nada cai na canônica — fail-soft
        # para canônica completa (provavelmente config inválido upstream).
        logger.warning(
            "[JobCreation:review_gate] tenant_enabled_ats=%r não intersecta "
            "com allowlist canônica — caindo na canônica completa",
            raw,
        )
        return _REVIEW_DESTINATIONS_ALLOWLIST, False
    return tenant_set, True

# TTL (segundos) entre o 1º ``publish_now`` (que SETA pending) e o 2º
# (que destrava ``policy_confirmed_publish``). Após o TTL expirar, o 2º
# publish_now é tratado como NOVO 1º (volta a pedir confirmação).
# NOTE: kept inline — sentinel test_clock_skew_clip_preserves_canonical_constant
# greps for exact literal "_PUBLISH_DUAL_CONFIRMATION_TTL_S: float = 300.0".
_PUBLISH_DUAL_CONFIRMATION_TTL_S: float = 300.0


# review_gate_node moved to nodes/review_gate.py (PR-10 ONDA 3 sub-B)
from app.domains.job_creation.nodes.review_gate import review_gate_node  # noqa: F401, E402


def route_after_review_gate(state: JobCreationState) -> str:
    """Routing após review_gate_node LLM. Determinístico baseado em
    mutações aplicadas pelo gate.

    Prioridade:
      1. fairness_blocked → END.
      2. policy_confirmed_publish=True (2ª confirmação dual) → publish.
      3. review_request_changes_pending.target_section → nó mapeado.
      4. caso contrário (publish_now 1ª chamada, configure_destinations,
         ask_clarification, schema inválido) → END (aguarda próximo
         turno do recrutador).
    """
    if state.get("fairness_blocked") is True:
        logger.info("[JobCreation:route] review_gate -> END (fairness blocked)")
        return "end"
    if state.get("policy_confirmed_publish") is True:
        # T6 (post-review #2 fix) — defesa em profundidade: mesmo que algum
        # caller seta policy_confirmed_publish externamente, exigimos
        # readiness.ready=True antes de rotear para publish. Espelha o
        # invariant histórico do route_after_review.
        _readiness = state.get("readiness_check") or {}
        if not _readiness.get("ready"):
            logger.warning(
                "[JobCreation:route] review_gate -> END (policy_confirmed_publish=True but readiness NOT ready, missing=%s)",
                _readiness.get("missing"),
            )
            return "end"
        logger.info("[JobCreation:route] review_gate -> publish (dual-confirmation + ready)")
        return "publish"
    pending = state.get("review_request_changes_pending") or {}
    if isinstance(pending, dict):
        target = str(pending.get("target_section") or "").strip().lower()
        node = _REVIEW_TARGET_SECTION_TO_NODE.get(target)
        if node and node != "review":
            logger.info(
                "[JobCreation:route] review_gate -> %s (request_changes target=%s)",
                node, target,
            )
            return node
    intent = state.get("gate_last_intent")
    # Sprint F.2 fix — self-loop em ask_clarification / publish_now FIRST turn /
    # configure_destinations / schema inválido (mesma classe de bug do
    # competency_gate / wsi_questions_gate / jd_gate). Sem self-loop, graph
    # completa sem interrupt → wizard reinicia do intake no próximo turno
    # (bug F2 E2E 2026-05-20: "aprovado, pode publicar a vaga" regredia
    # review-publish → jd-enrichment). interrupt() canônico já existe no
    # topo de review_gate_node.
    logger.info(
        "[JobCreation:route] review_gate -> review_gate (intent=%s, self-loop to interrupt)", intent,
    )
    return "review_gate"


def route_after_publish(state: JobCreationState) -> str:
    """After publish: go to calibration if job was published."""
    if state.get("job_id"):
        logger.info("[JobCreation:route] publish -> calibration")
        return "calibration"
    logger.info("[JobCreation:route] publish -> END (publish failed)")
    return "end"


def route_after_calibration(state: JobCreationState) -> str:
    """After calibration: if threshold met, handoff."""
    if state.get("calibration_complete"):
        logger.info("[JobCreation:route] calibration -> handoff")
        return "handoff"
    logger.info("[JobCreation:route] calibration -> END (awaiting more calibration)")
    return "end"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

# WSI F5 deterministic distribution -- canonical config em YAML.
# PR-8 ONDA 3 / F-3.3: extraido de hardcoded dict para
# app/prompts/job_creation/wsi_question_distribution.yaml.
# Sensor: tests/contract/test_wsi_question_distribution_taxonomy.py
# _WSI_QUESTION_DISTRIBUTION_FILE moved to internal/constants.py (PR-17 ONDA 3 follow-up)
from app.domains.job_creation.internal.constants import (  # noqa: E402, F401
    _WSI_QUESTION_DISTRIBUTION_FILE,
)


@_lru_cache(maxsize=1)
def _load_wsi_question_distributions() -> Dict[str, Dict[str, Dict[str, int]]]:
    """Lazy load do YAML canonical. Cached para evitar I/O repetido."""
    import yaml as _yaml
    with open(_WSI_QUESTION_DISTRIBUTION_FILE) as _fh:
        data = _yaml.safe_load(_fh)
    if not isinstance(data, dict):
        raise RuntimeError(
            f"wsi_question_distribution.yaml malformed: expected dict, got {type(data)}"
        )
    return data


def _get_question_distribution(mode: str, seniority: str) -> Dict[str, int]:
    """WSI F5 deterministic distribution tables.

    Source: WSI_METHODOLOGY_COMPLETE_v2.md (canonical values).
    Storage: app/prompts/job_creation/wsi_question_distribution.yaml
    (PR-8 ONDA 3 / F-3.3 -- extraido do dict hardcoded).

    Os valores devem bater com a methodology exatamente; nao mude o YAML
    sem atualizar o doc + test sentinel.
    """
    # Delegado ao helper canonical (audit 2026-06-05 #3) -- fonte UNICA do
    # split por bloco. Comportamento identico (mesmo YAML + normalizacao).
    from app.domains.job_creation.helpers.wsi_distribution import (
        block_distribution,
    )
    return block_distribution(mode, seniority)


def _build_readiness_check(state: JobCreationState) -> Dict[str, Any]:
    """Check if all required fields are present for publishing."""
    checks = {
        "jd_approved": bool(state.get("jd_approved")),
        "questions_approved": bool(state.get("questions_approved")),
        "has_questions": len(state.get("wsi_questions", [])) > 0,
        "has_seniority": bool(state.get("seniority_resolved")),
        "quality_score_ok": (state.get("jd_quality_score", 0) >= 50),
    }

    ready = all(checks.values())
    missing = [k for k, v in checks.items() if not v]

    return {
        "ready": ready,
        "checks": checks,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def emit_policy_block_audit(*, stage: str, decision: "Any") -> None:
    """Emit an audit row for a policy block or HITL pause.

    Module-level so tests can patch.object(graph, "emit_policy_block_audit").
    In production this writes to the audit_log table (async, fire-and-forget).
    """
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import audit_service as _audit
        _decision_val = str(getattr(getattr(decision, "decision", decision), "value", decision))
        _rationale = getattr(decision, "rationale", "")
        # F-2.6: get_running_loop() canonical Python 3.10+ (raise se nao ha loop ativo)
        # Outer try/except absorve RuntimeError (sem loop) -> emit skip silently.
        _asyncio.get_running_loop().call_soon_threadsafe(
            lambda: logger.info(
                "[PolicyAudit] stage=%s decision=%s rationale=%s",
                stage, _decision_val, _rationale,
            )
        )
    except Exception:
        logger.debug("[PolicyAudit] emit skipped (no event loop or audit service)")


def evaluate_wizard_policy(
    intent: str,
    state: "dict",
    *,
    score: "float | None" = None,
) -> "Any":
    """Module-level wrapper around policy_gate.evaluate — patchable by tests.

    Fails open (returns ALLOW) if policy_gate cannot be imported, ensuring the
    wizard is never blocked in CI or preview environments where PolicyEngine is
    not configured.
    """
    try:
        from app.domains.job_creation.policy_gate import evaluate as _pg_evaluate
        return _pg_evaluate(intent, state, score=score)
    except Exception as _pg_err:
        logger.debug("[PolicyGate] evaluate_wizard_policy fallback ALLOW: %s", _pg_err)
        from app.domains.job_creation.policy_gate import (
            PolicyDecision,
            WizardPolicyResult,
        )
        return WizardPolicyResult(
            decision=PolicyDecision.ALLOW,
            rationale=f"policy gate unavailable: {_pg_err}",
            confidence_band="high",
        )


# P2-K (Onda 1, PLAN_FIX_wizard_memory_loss 2026-05-10): funcao local
# _get_checkpointer() removida. Era duplicacao do fallback canonical em
# lia_agents_core.checkpointer.get_checkpointer (que ja faz a mesma
# defesa: PostgresSaver -> MemorySaver com WARNING em dev). Manter dois
# pontos de fallback cria risco de regressao silenciosa.


def create_job_creation_graph(
    checkpointer=None,
    use_llm_gates: bool | None = None,
) -> StateGraph:
    """Build the job creation wizard graph.

    Flow legacy (use_llm_gates=False):
      intake -> jd_enrichment --(HITL via route_after_jd)--> bigfive -> ...

    Flow T2 (use_llm_gates=True):
      intake -> jd_enrichment -> jd_gate --(LLM intent classifier)--> bigfive | intake | END
      ... demais gates (competency/wsi/review) seguem caminho legacy até
      Tasks #4/#5/#6 migrarem.

    O flag ``LIA_WIZARD_LLM_GATES`` controla o default; ``use_llm_gates``
    sobrepõe explicitamente (usado por testes).
    """
    if use_llm_gates is None:
        use_llm_gates = _llm_gates_enabled()
    builder = StateGraph(JobCreationState)

    # Add all nodes
    builder.add_node("intake", intake_node)
    builder.add_node("jd_enrichment", jd_enrichment_node)
    # Frente 2 (2026-05-29): gate conversacional antes do jd_enrichment.
    builder.add_node("intake_gate", intake_gate_node)
    if use_llm_gates:
        builder.add_node("jd_gate", jd_gate_node)
    builder.add_node("pipeline_template", pipeline_template_node)
    builder.add_node("bigfive", bigfive_node)
    builder.add_node("salary", salary_node)
    builder.add_node("benefits", benefits_node)
    builder.add_node("variable_comp", variable_comp_node)
    builder.add_node("competency", competency_node)
    if use_llm_gates:
        builder.add_node("competency_gate", competency_gate_node)
    builder.add_node("wsi_questions", wsi_questions_node)
    if use_llm_gates:
        builder.add_node("wsi_questions_gate", wsi_questions_gate_node)
    builder.add_node("eligibility", eligibility_node)
    builder.add_node("review", review_node)
    if use_llm_gates:
        builder.add_node("review_gate", review_gate_node)
    builder.add_node("publish", publish_node)
    builder.add_node("calibration", calibration_node)
    builder.add_node("handoff", handoff_node)

    # Entry point
    builder.set_entry_point("intake")

    # Linear edges (no conditional routing needed)
    # Frente 2 (2026-05-29): intake gate conversacional.
    builder.add_edge("intake", "intake_gate")
    builder.add_conditional_edges(
        "intake_gate",
        route_after_intake_gate,
        {
            "jd_enrichment": "jd_enrichment",
            "end": END,
        },
    )

    # HITL point 1: JD enrichment
    if use_llm_gates:
        # T2 — jd_enrichment escapa direto para o gate_node, que classifica
        # o intent do recrutador via LLM e decide o roteamento.
        builder.add_edge("jd_enrichment", "jd_gate")
        builder.add_conditional_edges(
            "jd_gate",
            route_after_gate,
            {
                # Sprint Pipeline Templates 2026-05-26 — Opção B: route_after_gate
                # ainda retorna "bigfive" como aprovação, mas roteamos
                # primeiro para pipeline_template (stage canonical HITL).
                # pipeline_template emite ws_stage_payload e termina;
                # ao resume (recrutador escolhe template ou skip), o graph
                # avança em add_edge("pipeline_template", "bigfive").
                "bigfive": "pipeline_template",
                "intake": "intake",
                "jd_gate": "jd_gate",  # Sprint F.2 fix — self-loop to interrupt
                "end": END,
            },
        )
    else:
        builder.add_conditional_edges(
            "jd_enrichment",
            route_after_jd,
            {
                # Sprint Pipeline Templates 2026-05-26 — Opção B: route_after_jd
                # legacy ainda retorna "bigfive" como aprovação, mas roteamos
                # primeiro para pipeline_template (stage canonical HITL).
                "bigfive": "pipeline_template",
                "intake": "intake",
                "end": END,
            },
        )

    # Sprint Pipeline Templates 2026-05-26 — Opção B (Gap #7 fix 2026-05-26).
    # Linear edge from pipeline_template to bigfive — sem isso, jd_gate roteia para
    # pipeline_template MAS pipeline_template não tem destino e graph termina em __end__,
    # tornando bigfive/salary/competency/wsi/eligibility/review/publish/etc unreachable.
    builder.add_edge("pipeline_template", "bigfive")

    # F2+F3 -> salary -> benefits -> variable_comp -> F4+F5
    builder.add_edge("bigfive", "salary")
    builder.add_edge("salary", "benefits")
    builder.add_edge("benefits", "variable_comp")
    builder.add_edge("variable_comp", "competency")

    # F4+F5: needs screening mode
    if use_llm_gates:
        # T4 — competency escapa direto para o gate_node, que classifica o
        # intent do recrutador via LLM (allowlist select_compact|select_full|
        # ask_question|undecided) e decide o roteamento determinístico.
        builder.add_edge("competency", "competency_gate")
        builder.add_conditional_edges(
            "competency_gate",
            route_after_competency_gate,
            {
                "wsi_questions": "wsi_questions",
                "competency_gate": "competency_gate",  # Sprint F.2 fix — self-loop to interrupt
                "end": END,
            },
        )
    else:
        builder.add_conditional_edges(
            "competency",
            route_after_competency,
            {
                "wsi_questions": "wsi_questions",
                "end": END,
            },
        )

    # HITL point 2: WSI questions
    if use_llm_gates:
        # T5 — wsi_questions escapa direto para o gate_node, que classifica
        # o intent do recrutador via LLM (allowlist approve_all|regenerate_all|
        # edit_specific_question|add_question|remove_question|ask_question)
        # e decide o roteamento determinístico.
        builder.add_edge("wsi_questions", "wsi_questions_gate")
        builder.add_conditional_edges(
            "wsi_questions_gate",
            route_after_wsi_questions_gate,
            {
                "eligibility": "eligibility",
                "wsi_questions": "wsi_questions",
                "wsi_questions_gate": "wsi_questions_gate",  # Sprint F.2 fix — self-loop to interrupt
                "end": END,
            },
        )
    else:
        builder.add_conditional_edges(
            "wsi_questions",
            route_after_questions,
            {
                "eligibility": "eligibility",
                "wsi_questions": "wsi_questions",
                "end": END,
            },
        )

    # Eligibility -> Review
    builder.add_edge("eligibility", "review")

    # HITL point 3: Review/publish
    if use_llm_gates:
        # T6 (Task #1088) — review escapa direto para o gate_node, que
        # classifica o intent do recrutador via LLM (allowlist
        # publish_now|request_changes|ask_clarification|configure_destinations)
        # e decide o roteamento determinístico (incluindo dupla
        # confirmação de chat para publish_now).
        builder.add_edge("review", "review_gate")
        builder.add_conditional_edges(
            "review_gate",
            route_after_review_gate,
            {
                "publish": "publish",
                "jd_enrichment": "jd_enrichment",
                "salary": "salary",
                "wsi_questions": "wsi_questions",
                "eligibility": "eligibility",
                "review": "review",
                "review_gate": "review_gate",  # Sprint F.2 fix — self-loop to interrupt
                "end": END,
            },
        )
    else:
        builder.add_conditional_edges(
            "review",
            route_after_review,
            {
                "publish": "publish",
                "end": END,
            },
        )

    # Publish -> Calibration
    builder.add_conditional_edges(
        "publish",
        route_after_publish,
        {
            "calibration": "calibration",
            "end": END,
        },
    )

    # Calibration -> Handoff
    builder.add_conditional_edges(
        "calibration",
        route_after_calibration,
        {
            "handoff": "handoff",
            "end": END,
        },
    )

    # Handoff -> Done
    builder.add_edge("handoff", END)

    # Compile with checkpointer
    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


# ---------------------------------------------------------------------------
# Singleton access (same pattern as SchedulingGraph)
# ---------------------------------------------------------------------------

# Audit C1/#11 (2026-06-05): ceiling explicito de recursao do wizard.
# LangGraph usa 25 implicito; o caminho HITL com loop-backs cabe folgado em
# ~15 super-steps por invoke, entao 50 da headroom mantendo o guard anti-runaway.
WIZARD_RECURSION_LIMIT = 50


class JobCreationGraph:
    _instance = None
    _graph = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            from lia_agents_core.checkpointer import get_checkpointer
            cls._graph = create_job_creation_graph(
                checkpointer=get_checkpointer()
            )
        return cls._instance

    @property
    def graph(self):
        return self._graph

    def invoke(self, state: JobCreationState, thread_id: str) -> JobCreationState:
        """Invoke the graph for a wizard session.

        Args:
            state: Current wizard state (accumulated across invocations).
            thread_id: Unique session ID for checkpointer persistence.

        Returns:
            Updated state after graph execution (may END at HITL points).
        """
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(state, config={**config, "recursion_limit": WIZARD_RECURSION_LIMIT})

    def resume(
        self,
        thread_id: str,
        prior_state: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> JobCreationState:
        """Resume a wizard session after HITL approval.

        Task #1094 — shim que prefere o canônico LangGraph
        ``Command(resume=...)`` quando o checkpoint está pausado em
        ``interrupt()``. Caso contrário (caminho legacy: gates não-HITL como
        salary/screening_mode/eligibility/publish/calibration que mutam state
        diretamente), re-invoca com state mergeado como antes.
        """
        if self.is_interrupted(thread_id):
            user_msg = (
                updates.get("gate_resume_message")
                or updates.get("user_query")
                or ""
            )
            return self.resume_with_message(thread_id, str(user_msg))
        merged = {**prior_state, **updates}
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(merged, config={**config, "recursion_limit": WIZARD_RECURSION_LIMIT})

    def is_interrupted(self, thread_id: str) -> bool:
        """Task #1094 — True se o graph para esse thread está pausado em
        ``interrupt()`` (existe pelo menos uma task pending com interrupts).

        Fail-OPEN (False) em outage do checkpointer — preserva a semântica
        de ``is_wizard_session_active``.
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = self._graph.get_state(config)
            if snapshot is None:
                return False
            return any(
                getattr(t, "interrupts", None)
                for t in (snapshot.tasks or [])
            )
        except Exception:
            return False

    def get_pending_interrupt_message(self, thread_id: str):
        """Extract user-facing message from the first pending interrupt, if any.

        Called after invoke/resume to surface intake_gate_node interrupt data
        as the visible message when the graph pauses mid-node (stale checkpoint).
        Fail-open: returns None on any error.
        """
        try:
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = self._graph.get_state(config)
            if not snapshot:
                return None
            for task in (snapshot.tasks or []):
                for intr in (getattr(task, "interrupts", None) or []):
                    val = getattr(intr, "value", None)
                    if isinstance(val, dict):
                        data = val.get("data")
                        if isinstance(data, dict) and data.get("message"):
                            return str(data["message"])
            return None
        except Exception:  # noqa: BLE001
            return None

    def resume_with_message(
        self, thread_id: str, user_message: str
    ) -> JobCreationState:
        """Task #1094 — resume canônico via ``Command(resume=<msg>)``.

        O graph deve estar pausado em ``interrupt()`` no thread; caso
        contrário o LangGraph ignora o resume value e re-invoca como
        startup (semântica idêntica ao ``invoke({})``). Caller é
        responsável por checar ``is_interrupted`` quando o caminho de
        fallback importar.
        """
        from langgraph.types import Command
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(
            Command(resume=str(user_message or "")), config={**config, "recursion_limit": WIZARD_RECURSION_LIMIT}
        )

    async def aresume_with_message(
        self, thread_id: str, user_message: str
    ) -> JobCreationState:
        """Task #1094 — versão async de ``resume_with_message`` para o
        caminho WS (``WizardSessionService.process_message``)."""
        from langgraph.types import Command
        config = {"configurable": {"thread_id": thread_id}}
        return await self._graph.ainvoke(
            Command(resume=str(user_message or "")), config={**config, "recursion_limit": WIZARD_RECURSION_LIMIT}
        )


def get_job_creation_graph() -> JobCreationGraph:
    return JobCreationGraph()


# 2026-05-24 fix Bug Checkpointer: módulo costumava ter eager init
# `job_creation_graph: JobCreationGraph = get_job_creation_graph()` que
# chamava `__new__` → `get_checkpointer()` ANTES do FastAPI lifespan rodar
# `initialize_checkpointer_async()`. Em dev caía em MemorySaver fallback,
# mas em APP_ENV=production levantava RuntimeError fatal.
#
# Fix canonical: lazy access via `__getattr__` module-level. Acessos
# `from graph import job_creation_graph` ou `graph_module.job_creation_graph`
# continuam funcionando — só são resolvidos no primeiro uso (sempre depois
# do lifespan). Tests com `monkeypatch.setattr(..., "job_creation_graph", ...)`
# também funcionam porque monkeypatch escreve em __dict__ que faz shadow
# do __getattr__, e raising=True passa porque hasattr(__getattr__)→True.
def __getattr__(name: str):
    if name == "job_creation_graph":
        return get_job_creation_graph()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_intake_extractor():
    """Return a fresh IntakeExtractor instance.

    Tests monkeypatch this function at module level to inject a stub extractor
    without instantiating the full graph stack.
    """
    from app.domains.job_creation.services.intake_extractor import IntakeExtractor
    return IntakeExtractor()
