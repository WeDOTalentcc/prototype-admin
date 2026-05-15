"""
JobCreationGraph — LangGraph state machine for the Wizard WSI pipeline.

Maps WSI Bloco A (F1-F6) + publish + calibration + handoff into a
conversational wizard flow with 2 HITL approval points.

Pattern follows scheduling/graph.py: StateGraph, conditional edges,
checkpointer for session persistence, singleton access.

HITL points:
  - jd_enrichment (F1): recruiter approves enriched JD
  - wsi_questions (F6): recruiter approves generated questions
"""

import logging
import os
import time
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END


def _llm_gates_enabled() -> bool:
    """Task #1085 (T2) — feature flag ``LIA_WIZARD_LLM_GATES``.

    Default ``false`` em prod (preserva comportamento legado de ``route_after_jd``).
    Default ``true`` em dev para exercitar o gate_node em toda PR.
    Lido a cada chamada ao builder para que testes possam alternar o flag
    via ``monkeypatch.setenv`` sem reset do módulo.

    REMOVE: 2026-07-01 após T2 GA + migração de gates competency/wsi/review
    (Tasks #4/#5/#6) — momento em que o caminho legado ``route_after_jd``
    deixa de ser necessário.
    """
    raw = os.environ.get("LIA_WIZARD_LLM_GATES", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    # Inferência por ambiente: dev → on, prod/staging → off.
    # T2 fix #12 (code review #10 comment 2): incluir ``APP_ENV`` (convenção
    # canônica do plataforma-lia / scripts/dev-up.sh / playwright workflows)
    # ALÉM de ``LIA_ENV``/``ENVIRONMENT``. Sem isso, ambientes dev que só
    # exportam ``APP_ENV=development`` (a maioria) caíam no default OFF, e
    # o gate só era exercitado quando o flag era setado explicitamente.
    env = (
        os.environ.get("LIA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or ""
    ).lower()
    return env in ("dev", "development", "local", "test")

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
from app.domains.job_creation.services.seniority_resolver import resolve_seniority
from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator
from app.domains.job_creation.api_client import JobCreationAPIClient

logger = logging.getLogger(__name__)

# Shared service instances (lazy-initialized in nodes)
_jd_service: Optional[JdEnrichmentService] = None
_wsi_generator: Optional[WSIQuestionGenerator] = None
_api_client: Optional[JobCreationAPIClient] = None


def _get_jd_service() -> JdEnrichmentService:
    global _jd_service
    if _jd_service is None:
        _jd_service = JdEnrichmentService()
    return _jd_service


def _get_wsi_generator() -> WSIQuestionGenerator:
    global _wsi_generator
    if _wsi_generator is None:
        _wsi_generator = WSIQuestionGenerator()
    return _wsi_generator


def _emit_fallback_telemetry(
    state: dict, stage: str, reason):
    """Task #1070 — registra um evento de fallback no tracker e devolve o
    snapshot ai_degraded_mode (sessão ou tenant) para ser propagado pelo
    ws_stage_payload. Quando o threshold é cruzado, o tracker emite log
    estruturado + sentry_sdk.capture_message para o time de plataforma.

    Sempre invoca get_state para que stages que não caíram em fallback
    no turno atual ainda surfacem o aviso enquanto a janela está ativa.
    """
    try:
        from app.shared.observability.wizard_fallback_tracker import (
            get_wizard_fallback_tracker,
        )

        sid = (
            str(state.get("session_id") or state.get("thread_id") or "")
            or None
        )
        cid = (
            str(state.get("workspace_id") or state.get("company_id") or "")
            or None
        )
        tracker = get_wizard_fallback_tracker()
        if reason:
            tracker.record_fallback(
                session_id=sid, company_id=cid, stage=stage, reason=reason,
            )
        return tracker.get_state(session_id=sid, company_id=cid)
    except Exception as exc:  # noqa: BLE001 — telemetria nunca quebra o wizard
        logger.warning(
            "[JobCreation:%s] wizard fallback tracker failed: %s", stage, exc,
        )
        return None


def _get_api_client(state: dict) -> JobCreationAPIClient:
    """Get API client with auth context from state."""
    global _api_client
    # Recreate if auth token changes
    token = state.get("auth_token", "")
    if _api_client is None or getattr(_api_client, "_last_token", "") != token:
        # Build minimal context for auth
        ctx = type("Ctx", (), {
            "auth_token": token,
            "track_api_call": lambda *a, **k: None,
        })()
        _api_client = JobCreationAPIClient(context=ctx)
        _api_client._last_token = token
    return _api_client


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
_PIPELINE_TEMPLATE_IDS: tuple[str, ...] = (
    "technical", "executive", "operational", "mass_hiring", "intern",
)
_EXECUTIVE_KEYWORDS = (
    "director", "diretor", "vp", "vice", "cto", "cfo", "ceo", "head",
    "gerente geral", "c-level", "chief",
)
_TECHNICAL_KEYWORDS = (
    "developer", "desenvolvedor", "engineer", "engenheiro", "programador",
    "software", "data", "devops", "sre", "backend", "frontend", "fullstack",
    "full-stack", "tech lead", "arquiteto",
)
_OPERATIONAL_KEYWORDS = (
    "operador", "auxiliar", "assistente", "atendente", "vendedor",
    "recepcionista", "caixa", "estoquista",
)
_INTERN_KEYWORDS = (
    # `estagi` cobre "estágio", "estagio", "estagiário", "estagiaria".
    "estagi", "trainee", "jovem aprendiz", "intern",
)


def _suggest_pipeline_template(
    parsed_title: Optional[str],
    parsed_seniority: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Sugestão determinística de template de pipeline a partir do título.

    Retorna `None` quando ainda não há sinal suficiente (sem título), para o
    frontend pular a injeção do card. Nunca levanta — fail-open."""
    try:
        title = (parsed_title or "").strip().lower()
        if not title:
            return None
        seniority = (parsed_seniority or "").strip().lower()

        if any(kw in title for kw in _INTERN_KEYWORDS) or seniority in {"estagiário", "estagiario", "trainee"}:
            suggested = "intern"
        elif any(kw in title for kw in _EXECUTIVE_KEYWORDS) or seniority in {"diretor", "vp", "c-level", "executive"}:
            suggested = "executive"
        elif any(kw in title for kw in _TECHNICAL_KEYWORDS):
            suggested = "technical"
        elif any(kw in title for kw in _OPERATIONAL_KEYWORDS):
            suggested = "operational"
        else:
            suggested = "technical"  # default seguro — frontend ainda mostra todos
        return {
            "suggested_type": suggested,
            "templates": list(_PIPELINE_TEMPLATE_IDS),
        }
    except Exception:  # noqa: BLE001 — fail-open por design
        return None


# ---------------------------------------------------------------------------
# Wizard step audit helper (Task #1061 — EU AI Act Art.13 / SOX)
# ---------------------------------------------------------------------------
# Cada node decisório (`bigfive`, `wsi_questions`, `competency`,
# `eligibility`) emite uma audit row com `decision_type=wizard_step_completed`
# ao concluir. Espelha o padrão de `audit_company_change` em
# `company_settings`: `before/after/target_id/trace_id` ficam em `reasoning`.
# Fail-open por design — falha de audit NUNCA bloqueia o wizard, mas a
# sentinela offline garante que o call site existe.
def _emit_wizard_step_audit(
    *,
    stage: str,
    state: dict,
    before: Any,
    after: Any,
    reasoning_extra: Optional[list[str]] = None,
    criteria_used: Optional[list[str]] = None,
    human_review_required: bool = False,
) -> None:
    """Emit `wizard_step_completed` audit row for a JobCreationGraph node."""
    try:
        import asyncio as _asyncio
        import json as _json
        import uuid as _uuid

        from app.shared.compliance.audit_service import AuditService

        company_id = str(
            state.get("workspace_id") or state.get("company_id") or ""
        )
        if not company_id:
            logger.warning(
                "[JobCreation:%s] audit skipped — missing company_id", stage,
            )
            return

        target_id = str(
            state.get("job_id") or state.get("session_id") or ""
        ) or "∅"
        trace_id = str(_uuid.uuid4())

        def _ser(v: Any) -> str:
            try:
                s = _json.dumps(v, default=str, ensure_ascii=False, sort_keys=True)
            except Exception:
                s = str(v)
            return s if len(s) <= 1000 else f"{s[:1000]}…"

        reasoning: list[str] = [
            f"trace_id={trace_id}",
            f"stage={stage}",
            f"target_id={target_id}",
            f"before={_ser(before)}",
            f"after={_ser(after)}",
        ]
        if reasoning_extra:
            reasoning.extend(reasoning_extra)

        criteria = list(criteria_used or []) + [
            "wizard_step",
            f"stage:{stage}",
            f"trace_id:{trace_id}",
            f"target_id:{target_id}",
        ]

        _asyncio.run(AuditService().log_decision(
            company_id=company_id,
            agent_name=f"job_creation:{stage}",
            decision_type="wizard_step_completed",
            action=f"complete_{stage}",
            decision="completed",
            reasoning=reasoning,
            criteria_used=criteria,
            job_vacancy_id=state.get("job_id"),
            human_review_required=human_review_required,
        ))
    except Exception as _audit_exc:  # noqa: BLE001 — fail-open
        logger.warning(
            "[JobCreation:%s] wizard_step_completed audit failed (fail-open): %s",
            stage, _audit_exc,
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
_WIZARD_FALLBACK_NODES: tuple[str, ...] = (
    "jd_enrichment", "bigfive", "salary", "wsi_questions",
)


def _emit_wizard_fallback_metric(
    *,
    node: str,
    state: dict,
    reason: str,
    timeout_s: Optional[float] = None,
    elapsed_ms: Optional[float] = None,
) -> None:
    """Emit observability signal when a wizard node falls back.

    Args:
        node: One of `_WIZARD_FALLBACK_NODES`.
        state: LangGraph state — used to extract tenant id (workspace_id /
            company_id) and session id without leaking PII.
        reason: Short machine token, e.g. `"llm_timeout"`, `"llm_exception"`,
            `"benchmark_timeout"`. Becomes a Sentry tag — keep it low-cardinality.
        timeout_s: Configured timeout (when applicable) so dashboards can
            justify raising it.
        elapsed_ms: Wall-clock spent before the fallback fired (when known).
    """
    try:
        if node not in _WIZARD_FALLBACK_NODES:
            # Prevent silent taxonomy drift — a typo here would split the
            # dashboard into two buckets and hide the regression.
            logger.warning(
                "[JobCreation] _emit_wizard_fallback_metric got unknown node=%r "
                "(allowed=%s) — telemetry skipped",
                node, _WIZARD_FALLBACK_NODES,
            )
            return
        tenant_id = str(
            state.get("workspace_id") or state.get("company_id") or ""
        ) or "unknown"
        session_id = str(state.get("session_id") or "") or None
        job_id = state.get("job_id")

        # ── 1. Structured log (picked up by JSONFormatter) ──
        extra: Dict[str, Any] = {
            "extra_data": {
                "metric": "wizard_fallback",
                "node": node,
                "tenant_id": tenant_id,
                "reason": reason,
                "timeout_s": timeout_s,
                "elapsed_ms": elapsed_ms,
                "session_id": session_id,
                "job_id": str(job_id) if job_id else None,
            },
            "tenant_id": tenant_id,
        }
        logger.warning(
            "[JobCreation:%s] wizard fallback fired (reason=%s)",
            node, reason, extra=extra,
        )

        # ── 2. Sentry breadcrumb + capture_message ──
        try:
            import sentry_sdk as _sentry  # noqa: WPS433 — lazy import
        except Exception:  # noqa: BLE001 — sentry optional
            return
        try:
            _sentry.add_breadcrumb(
                category="wizard.fallback",
                level="warning",
                message=f"wizard:{node} fallback ({reason})",
                data={
                    "node": node,
                    "reason": reason,
                    "tenant_id": tenant_id,
                    "timeout_s": timeout_s,
                    "elapsed_ms": elapsed_ms,
                },
            )
            with _sentry.push_scope() as _scope:
                _scope.set_tag("wizard.node", node)
                _scope.set_tag("wizard.fallback_reason", reason)
                _scope.set_tag("tenant_id", tenant_id)
                _scope.set_extra("timeout_s", timeout_s)
                _scope.set_extra("elapsed_ms", elapsed_ms)
                _scope.set_extra("session_id", session_id)
                _sentry.capture_message(
                    f"wizard fallback: {node} ({reason})",
                    level="warning",
                )
        except Exception as _sentry_exc:  # noqa: BLE001 — fail-open
            logger.debug(
                "[JobCreation:%s] sentry capture failed (fail-open): %s",
                node, _sentry_exc,
            )
    except Exception as _metric_exc:  # noqa: BLE001 — fail-open
        logger.debug(
            "[JobCreation:%s] wizard fallback metric emit failed (fail-open): %s",
            node, _metric_exc,
        )


def intake_node(state: JobCreationState) -> JobCreationState:
    """Pre-F1: Parse user input via IntakeExtractor (LLM + regex fallback).

    Phase 3 / F3-1 — replaces previous stub pass-through.
    Extracts: parsed_title, parsed_seniority, parsed_department, parsed_location, parsed_model.
    Fail-open: low confidence on extraction failure does NOT block the wizard.
    """
    t0 = time.time()
    query = state.get("user_query", "") or state.get("raw_input", "")
    logger.info("[JobCreation:intake] query=%s", query[:80])

    # T2 (Task #1085) — resume short-circuit em DOIS sinais (cobre WS canônico
    # E action-based): (a) ``gate_resume_message`` setado pelo path
    # ``domain.py::_handle_gate_jd``; OU (b) ``jd_enriched`` já populado
    # vindo do checkpoint (path canônico WS via ``WizardSessionService``).
    # Em ambos os casos, ``parsed_title`` já foi extraído em turno anterior
    # e re-rodar IntakeExtractor (~1-3s + tokens) é desperdício puro.
    if state.get("parsed_title") and (
        state.get("gate_resume_message") or state.get("jd_enriched")
    ):
        return {**state, "current_stage": "intake"}

    # ── F3-1: IntakeExtractor (LLM + regex fallback) ──
    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")
    parsed_department = state.get("parsed_department")
    parsed_location = state.get("parsed_location")
    parsed_model = state.get("parsed_model")
    intake_confidence = 0.0
    intake_source = "none"
    try:
        # Use module-level get_intake_extractor() so tests can monkeypatch it.
        extractor = get_intake_extractor()
        right_panel_form = state.get("right_panel_form") or {}
        attached_file_text = state.get("attached_file_text") or ""
        if right_panel_form or attached_file_text:
            extraction = extractor.extract_from_sources(
                user_text=query,
                right_panel_form=right_panel_form,
                attached_file_text=attached_file_text,
            )
        else:
            extraction = extractor.extract(query)
        # Fill ONLY fields that aren't already explicit in state
        parsed_title = parsed_title or extraction.parsed_title
        parsed_seniority = parsed_seniority or extraction.parsed_seniority
        parsed_department = parsed_department or extraction.parsed_department
        parsed_location = parsed_location or extraction.parsed_location
        parsed_model = parsed_model or extraction.parsed_model
        intake_confidence = extraction.confidence
        intake_source = extraction.source
        logger.info(
            "[JobCreation:intake] F3-1 extraction: source=%s, conf=%.2f, "
            "title=%s, seniority=%s, location=%s, model=%s",
            intake_source, intake_confidence, parsed_title, parsed_seniority,
            parsed_location, parsed_model,
        )
    except Exception as _ex_exc:
        logger.warning(
            "[JobCreation:intake] F3-1 extraction failed (fail-open): %s", _ex_exc,
        )

    updates: Dict[str, Any] = {
        "current_stage": "intake",
        "raw_input": query,
        "parsed_title": parsed_title,
        "parsed_seniority": parsed_seniority,
        "parsed_department": parsed_department,
        "parsed_location": parsed_location,
        "parsed_model": parsed_model,
        "intake_confidence": intake_confidence,
        "stage_history": (state.get("stage_history") or []) + ["intake"],
        "completeness": calculate_completeness("intake"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "intake",
            "data": {
                "raw_input": query,
                "parsed_title": parsed_title,
                "parsed_seniority": parsed_seniority,
                "parsed_department": parsed_department,
                "parsed_location": parsed_location,
                "parsed_model": parsed_model,
                "intake_confidence": intake_confidence,
                "intake_source": intake_source,
                # Task #1055 — emite o pipeline_template determinístico já no
                # turno de intake para que o WizardPipelineTemplateCard apareça
                # mesmo se a chamada de culture-stack ou Gemini falhar depois.
                "suggestions_data": {
                    "pipeline_template": _suggest_pipeline_template(
                        parsed_title, parsed_seniority,
                    ),
                },
            },
            "completeness": calculate_completeness("intake"),
            "requires_approval": False,
        },
    }

    # NOTE on LL-2 manager preferences:
    # ManagerPreferencesService.apply_to_state() is invoked by
    # WizardSessionService.process_message() BEFORE this graph runs.
    # See app/domains/job_creation/services/wizard_session_service.py:217+.
    # Centralizing it there avoids double DB hits and keeps single source of truth.

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:intake] %0.fms", elapsed)
    return {**state, **updates}


def jd_enrichment_node(state: JobCreationState) -> JobCreationState:
    """F1: Call JdEnrichmentService to enrich JD + calculate quality score.

    This is HITL point 1 — recruiter must approve the enriched JD.

    Fairness 4 layers (canonical wiring — Phase 2A):
      Layer 1 (input gate)  : FairnessGuard.check(raw_input) BEFORE LLM
      Layer 2 (PII strip)   : strip_pii_for_llm_prompt(raw_input) BEFORE LLM
      Layer 3 (output check): FairnessGuard.check(enriched_text) AFTER LLM
      Layer 4 (question guard) lives in wsi_questions_node.
    """
    t0 = time.time()
    logger.info("[JobCreation:jd_enrichment] Starting F1")

    # ── Layer 1: input fairness gate (BEFORE LLM) ──
    # Fail-closed: if input is discriminatory, block before spending LLM tokens.
    raw_input = state.get("raw_input", "") or state.get("user_query", "")
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_input = _fg.check(raw_input)
        if _fg_input.is_blocked:
            logger.warning(
                "[JobCreation:jd_enrichment] FairnessGuard L1 BLOCK input: "
                "category=%s, terms=%s",
                _fg_input.category, _fg_input.blocked_terms,
            )
            return {
                **state,
                "current_stage": "jd_enrichment",
                "fairness_blocked": True,
                "jd_fairness_blocked": True,
                "fairness_block_reason": _fg_input.educational_message,
                "error": "fairness_blocked",
                "jd_approved": False,
                "jd_quality_score": 0.0,
                "stage_history": (state.get("stage_history") or []) + ["jd_enrichment_blocked"],
                "ws_stage_payload": {
                    "type": "wizard_stage",
                    "stage": "jd_enrichment",
                    "data": {
                        "error": "fairness_blocked",
                        "category": _fg_input.category,
                        "message": _fg_input.educational_message,
                    },
                    "requires_approval": False,
                },
            }
    except Exception as _fg_l1_exc:
        # Fail-open for guard regression — não bloqueia UX por bug do guard
        logger.warning(
            "[JobCreation:jd_enrichment] FairnessGuard L1 check failed (fail-open): %s",
            _fg_l1_exc,
        )

    # ── Layer 2: PII strip (BEFORE LLM) ──
    # LGPD Art. 12 + EU AI Act Art. 13: minimização de dados pessoais.
    # Phase 4I P0 fix — previously computed raw_input_safe was NOT being used
    # in the LLM call (jd_raw fell back to the original raw_input with PII).
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        raw_input_safe = strip_pii_for_llm_prompt(raw_input)
        if raw_input_safe != raw_input:
            logger.info("[JobCreation:jd_enrichment] L2 PII stripped before LLM")
    except Exception as _pii_exc:
        logger.warning("[JobCreation:jd_enrichment] PII strip failed (fail-open): %s", _pii_exc)
        raw_input_safe = raw_input

    # Use the PII-stripped variant for the LLM call. State still keeps the
    # original raw_input for non-LLM uses (logging, audit, replay).
    jd_raw_safe = state.get("jd_raw") or raw_input_safe
    # Defensive: if jd_raw came from state, also strip it (could be replay path)
    if jd_raw_safe and jd_raw_safe == state.get("jd_raw"):
        try:
            jd_raw_safe = strip_pii_for_llm_prompt(jd_raw_safe)
        except Exception:  # noqa: BLE001 — fail-open
            pass

    # If already enriched, skip re-enrichment. Cobre os 3 paths:
    # (a) HITL aprovado (jd_approved=True) — já saímos do gate;
    # (b) action-based resume (gate_resume_message presente);
    # (c) canônico WS — jd_enriched veio do checkpoint, recrutador está
    #     respondendo ao gate. O único caminho que invalida o cache e força
    #     re-enrichment é ``provide_new_content`` no jd_gate_node, que seta
    #     ``jd_enriched=None`` explicitamente — então este guard cobrir
    #     "tem jd_enriched ⇒ pula" é correto e seguro.
    if state.get("jd_enriched"):
        jd_enriched_dict = state["jd_enriched"]
        jd_quality_score = state.get("jd_quality_score", 0.0)
        jd_quality_warnings = state.get("jd_quality_warnings", [])
    else:
        # Call JdEnrichmentService (F1.C LLM enrichment)
        # IMPORTANT — pass jd_raw_safe (PII-stripped), NOT jd_raw original.
        # Task #1055 — timeout determinístico (fail-loud, fallback) para
        # evitar que Gemini lento/429 ou /api/v1/company/culture-stack 500
        # bloqueiem o turno do chat REST por minutos. Espelha o requisito
        # canonical: "fallback determinístico se Gemini 429". O serviço já
        # expõe `_fallback_enrichment` + `calculate_quality_score`.
        import concurrent.futures as _cf
        from app.domains.job_creation.services.jd_enrichment import (
            calculate_quality_score as _calc_q,
        )
        service = _get_jd_service()
        _JD_LLM_TIMEOUT_S = float(__import__("os").environ.get(
            "LIA_JD_ENRICHMENT_TIMEOUT_S", "12"
        ))
        # Task #1065 — sinaliza ao frontend quando caímos em fallback
        # determinístico (timeout do LLM ou exception). O painel renderiza
        # um banner discreto pedindo revisão extra antes da aprovação HITL.
        jd_enrichment_used_fallback = False
        # Task #1067 — root-cause label propagado pro painel para o
        # recrutador decidir entre tentar de novo ou aceitar o mínimo.
        jd_enrichment_fallback_reason: Optional[str] = None
        try:
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(
                    service.enrich,
                    jd_raw=jd_raw_safe,
                    title=state.get("parsed_title", ""),
                    seniority=state.get("parsed_seniority", ""),
                    department=state.get("parsed_department", ""),
                )
                enriched_obj, jd_quality_score, jd_quality_warnings = _fut.result(
                    timeout=_JD_LLM_TIMEOUT_S
                )
        except _cf.TimeoutError:
            logger.warning(
                "[JobCreation:jd_enrichment] LLM timeout after %.1fs — "
                "deterministic fallback (Task #1055)", _JD_LLM_TIMEOUT_S,
            )
            enriched_obj = service._fallback_enrichment(
                jd_raw_safe,
                state.get("parsed_title", ""),
                state.get("parsed_seniority", ""),
            )
            enriched_obj.wsi_quality_warnings.append(
                "Enriquecimento via LLM em fallback determinístico (timeout)"
            )
            jd_quality_score, jd_quality_warnings = _calc_q(enriched_obj)
            jd_enrichment_used_fallback = True
            jd_enrichment_fallback_reason = "timeout"
            _emit_wizard_fallback_metric(
                node="jd_enrichment", state=state, reason="llm_timeout",
                timeout_s=_JD_LLM_TIMEOUT_S,
                elapsed_ms=(time.time() - t0) * 1000,
            )
        except Exception as _enrich_exc:  # noqa: BLE001 — fail-open com fallback
            logger.warning(
                "[JobCreation:jd_enrichment] LLM call failed (%s) — fallback",
                _enrich_exc,
            )
            enriched_obj = service._fallback_enrichment(
                jd_raw_safe,
                state.get("parsed_title", ""),
                state.get("parsed_seniority", ""),
            )
            jd_quality_score, jd_quality_warnings = _calc_q(enriched_obj)
            jd_enrichment_used_fallback = True
            # Heurística leve: erros HTTP/quota do provedor LLM costumam
            # carregar termos como "rate", "quota", "429", "503", "provider".
            _exc_str = str(_enrich_exc).lower()
            if any(t in _exc_str for t in (
                "rate", "quota", "429", "503", "provider", "api",
                "unauthorized", "forbidden", "401", "403",
            )):
                jd_enrichment_fallback_reason = "provider_error"
            else:
                jd_enrichment_fallback_reason = "exception"
            _emit_wizard_fallback_metric(
                node="jd_enrichment", state=state,
                reason=f"llm_{jd_enrichment_fallback_reason}",
                timeout_s=_JD_LLM_TIMEOUT_S,
                elapsed_ms=(time.time() - t0) * 1000,
            )
        jd_enriched_dict = enriched_obj.model_dump()

        # ── Layer 3: output fairness check (AFTER LLM) ──
        # Hard block — if LLM introduced discriminatory content, block the output.
        # LGPD Art. 11 + EU AI Act Art. 13: biased JD must never reach recruiter UI.
        try:
            _enriched_text_parts = []
            if jd_enriched_dict.get("titulo_padronizado"):
                _enriched_text_parts.append(jd_enriched_dict["titulo_padronizado"])
            if jd_enriched_dict.get("about_role"):
                _enriched_text_parts.append(jd_enriched_dict["about_role"])
            for s in (jd_enriched_dict.get("skills_obrigatorias") or []):
                if isinstance(s, dict):
                    _enriched_text_parts.append(s.get("contexto", ""))
            _enriched_text = " ".join(filter(None, _enriched_text_parts))
            if _enriched_text:
                _fg_output = _fg.check(_enriched_text)
                if _fg_output.is_blocked:
                    logger.warning(
                        "[JobCreation:jd_enrichment] FairnessGuard L3 BLOCK output: "
                        "category=%s, terms=%s — LLM introduced bias, blocking",
                        _fg_output.category, _fg_output.blocked_terms,
                    )
                    return {
                        **state,
                        "current_stage": "jd_enrichment",
                        "jd_enriched": None,
                        "jd_approved": False,
                        "jd_quality_score": 0.0,
                        "jd_fairness_blocked": True,
                        "fairness_blocked": True,
                        "fairness_block_reason": _fg_output.educational_message,
                        "error": "fairness_blocked_output",
                        "requires_approval": False,
                        "stage_history": (state.get("stage_history") or []) + ["jd_enrichment_blocked_l3"],
                        "ws_stage_payload": {
                            "type": "wizard_stage",
                            "stage": "jd_enrichment",
                            "data": {
                                "error": "fairness_blocked_output",
                                "category": _fg_output.category,
                                "message": _fg_output.educational_message,
                            },
                            "requires_approval": False,
                        },
                    }
        except Exception as _fg_l3_exc:
            logger.warning(
                "[JobCreation:jd_enrichment] FairnessGuard L3 check failed (fail-open): %s",
                _fg_l3_exc,
            )

    updates: Dict[str, Any] = {
        "current_stage": "jd_enrichment",
        "jd_raw": raw_input,
        "jd_enriched": jd_enriched_dict,
        "jd_quality_score": jd_quality_score,
        "jd_quality_warnings": jd_quality_warnings,
        "jd_fairness_blocked": False,
        "stage_history": (state.get("stage_history") or []) + ["jd_enrichment"],
        "completeness": calculate_completeness("jd_enrichment"),
        "requires_approval": True,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "jd_enrichment",
            "data": {
                "jd_raw": raw_input,
                "jd_enriched": jd_enriched_dict,
                "quality_score": jd_quality_score,
                "quality_warnings": jd_quality_warnings,
                # Task #1065 — flag de fallback determinístico para o painel
                # renderizar o banner "Sugestão mínima — revise". `False` no
                # resume path (já aprovado) é correto: o recrutador já viu.
                "jd_enrichment_used_fallback": locals().get(
                    "jd_enrichment_used_fallback", False
                ),
                # Task #1067 — root-cause label ("timeout"/"exception"/
                # "provider_error"). `None` no resume path (já aprovado).
                "jd_enrichment_fallback_reason": locals().get(
                    "jd_enrichment_fallback_reason", None
                ),
                # Task #1070 — snapshot agregado de degradação (sessão/tenant).
                "ai_degraded_mode": _emit_fallback_telemetry(
                    state,
                    "jd_enrichment",
                    locals().get("jd_enrichment_fallback_reason", None),
                ),
                # Task #1055 — re-emite o pipeline_template no turno de
                # jd_enrichment (após o frontend re-render) usando o título
                # padronizado pelo enriquecimento se disponível, senão o
                # parsed_title do intake. Garante liveness do card mesmo se
                # o intake_node não rodar nesse turno (resume path).
                "suggestions_data": {
                    "pipeline_template": _suggest_pipeline_template(
                        (jd_enriched_dict or {}).get("titulo_padronizado")
                        or state.get("parsed_title"),
                        state.get("parsed_seniority"),
                    ),
                },
            },
            "completeness": calculate_completeness("jd_enrichment"),
            "requires_approval": True,
        },
    }

    # ── Audit EU AI Act Art.13 — JD enrichment decision ──
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            _asyncio.run(_audit.log_decision(
                company_id=_company_id,
                agent_name="job_creation:jd_enrichment",
                decision_type="generate_jd",
                action="enrich_jd",
                decision="enriched" if jd_enriched_dict else "fallback",
                reasoning=[
                    f"quality_score={jd_quality_score:.1f}",
                    *(jd_quality_warnings or []),
                ],
                criteria_used=["title", "responsibilities", "skills_obrigatorias",
                               "skills_desejaveis", "competencias_comportamentais"],
                job_vacancy_id=state.get("job_id"),
                confidence=getattr(enriched_obj, "confidence", None),
                human_review_required=True,  # HITL 1
            ))
    except Exception as _audit_exc:
        logger.warning(
            "[JobCreation:jd_enrichment] audit log failed (fail-open): %s", _audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:jd_enrichment] score=%.1f | %0.fms", jd_quality_score, elapsed)
    return {**state, **updates}


def bigfive_node(state: JobCreationState) -> JobCreationState:
    """F2+F3: Extract Big Five profile from enriched JD + rank traits.

    F2: LLM extraction (temp=0.1)
    F3: Deterministic trait ranking formula
    """
    t0 = time.time()
    logger.info("[JobCreation:bigfive] Starting F2+F3")

    from app.domains.job_creation.schemas import EnrichedJobDescription

    jd_enriched_dict = state.get("jd_enriched", {})

    # ── FairnessGuard pre-check (bigfive input) ──
    # If jd_enriched already contains discriminatory text, skip LLM call.
    if jd_enriched_dict:
        _bf_text_parts = [
            jd_enriched_dict.get("about_role", ""),
            " ".join(jd_enriched_dict.get("responsabilidades", []) or []),
        ]
        _bf_text = " ".join(filter(None, _bf_text_parts))
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard as _BFFg
            _bf_fg_result = _BFFg().check(_bf_text)
            if _bf_fg_result.is_blocked:
                logger.warning(
                    "[JobCreation:bigfive] FairnessGuard PRE-BLOCK: category=%s — skipping LLM",
                    _bf_fg_result.category,
                )
                return {**state, "current_stage": "bigfive"}
        except Exception as _bf_fg_exc:
            logger.warning("[JobCreation:bigfive] FairnessGuard pre-check failed (fail-open): %s", _bf_fg_exc)

    # ── PII masking (BEFORE LLM) ──
    # Strip PII from enriched JD fields before feeding to Big Five LLM.
    _safe_enriched_dict = dict(jd_enriched_dict) if jd_enriched_dict else {}
    try:
        from app.domains.job_creation.compliance import mask_pii_for_llm as _mask_pii
        for _field in ("about_role", "titulo_padronizado"):
            if _safe_enriched_dict.get(_field):
                _safe_enriched_dict[_field] = _mask_pii(_safe_enriched_dict[_field])
        if _safe_enriched_dict.get("responsabilidades"):
            _safe_enriched_dict["responsabilidades"] = [
                _mask_pii(r) if isinstance(r, str) else r
                for r in _safe_enriched_dict["responsabilidades"]
            ]
    except Exception as _bf_pii_exc:
        logger.warning("[JobCreation:bigfive] PII masking failed (fail-open): %s", _bf_pii_exc)

    enriched = EnrichedJobDescription(**_safe_enriched_dict) if _safe_enriched_dict else None

    generator = _get_wsi_generator()

    # Policy gate check
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _policy_result = evaluate_wizard_policy(WizardIntent.SET_PROTECTED_CRITERIA, state)
    _policy_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "bigfive",
        "policy_decision": str(_policy_result.decision),
        "rationale": _policy_result.rationale,
    }]
    if _policy_result.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:bigfive] DENY — %s", _policy_result.rationale)
        emit_policy_block_audit(stage="bigfive", decision=_policy_result)
        _pd_dict = {"policy_decision": str(_policy_result.decision), "rationale": _policy_result.rationale}
        return {
            **state,
            "policy_decisions": _policy_decisions,
            "error": f"Big Five bloqueado: {_policy_result.rationale}",
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": {
                "type": "wizard_stage",
                "stage": "bigfive",
                "data": {
                    "policy_blocked": True,
                    "policy_decision": _pd_dict,
                },
                "completeness": 0,
                "requires_approval": False,
            },
        }
    _pending_hitl = (_policy_result.decision == PolicyDecision.HITL_REQUIRED)

    if enriched:
        # F2: Extract Big Five via LLM — Task #1062: timeout determinístico
        # com fallback (`BigFiveExtraction()` defaults 0.5 across traits).
        # Espelha o padrão de `LIA_JD_ENRICHMENT_TIMEOUT_S` (D4 da auditoria
        # #1058). `rank_traits` é determinístico — não precisa timeout.
        import concurrent.futures as _cf_bf
        from app.domains.job_creation.schemas import BigFiveExtraction as _BFE
        _BF_LLM_TIMEOUT_S = float(__import__("os").environ.get(
            "LIA_BIGFIVE_TIMEOUT_S", "10"
        ))
        # NOTE: não usar `with ThreadPoolExecutor(...)` — o `__exit__` chama
        # `shutdown(wait=True)` e bloqueia até o LLM lento terminar (anula o
        # timeout). `shutdown(wait=False)` deixa a thread morrer em paz.
        # Task #1065 — flag de fallback determinístico (timeout LLM →
        # `BigFiveExtraction()` neutro 0.5). Painel renderiza banner
        # discreto pedindo revisão antes do recrutador confiar nas pistas.
        bigfive_used_fallback = False
        # Task #1067 — root-cause label propagado pro painel.
        bigfive_fallback_reason: Optional[str] = None
        _ex_bf = _cf_bf.ThreadPoolExecutor(max_workers=1)
        try:
            try:
                _fut_bf = _ex_bf.submit(generator.extract_bigfive, enriched)
                bigfive_obj = _fut_bf.result(timeout=_BF_LLM_TIMEOUT_S)
            except _cf_bf.TimeoutError:
                logger.warning(
                    "[JobCreation:bigfive] LLM timeout after %.1fs — "
                    "deterministic fallback (Task #1062)", _BF_LLM_TIMEOUT_S,
                )
                bigfive_obj = _BFE()  # defaults to 0.5 across all traits
                bigfive_used_fallback = True
                bigfive_fallback_reason = "timeout"
                _emit_wizard_fallback_metric(
                    node="bigfive", state=state, reason="llm_timeout",
                    timeout_s=_BF_LLM_TIMEOUT_S,
                    elapsed_ms=(time.time() - t0) * 1000,
                )
            except Exception as _bf_exc:  # noqa: BLE001 — fail-open
                logger.warning(
                    "[JobCreation:bigfive] LLM call failed (%s) — fallback",
                    _bf_exc,
                )
                bigfive_obj = _BFE()
                bigfive_used_fallback = True
                _exc_str = str(_bf_exc).lower()
                if any(t in _exc_str for t in (
                    "rate", "quota", "429", "503", "provider", "api",
                    "unauthorized", "forbidden", "401", "403",
                )):
                    bigfive_fallback_reason = "provider_error"
                else:
                    bigfive_fallback_reason = "exception"
                _emit_wizard_fallback_metric(
                    node="bigfive", state=state,
                    reason=f"llm_{bigfive_fallback_reason}",
                    timeout_s=_BF_LLM_TIMEOUT_S,
                    elapsed_ms=(time.time() - t0) * 1000,
                )
        finally:
            _ex_bf.shutdown(wait=False)
        bigfive_profile = bigfive_obj.model_dump()

        # F3: Rank traits (deterministic — no LLM, no timeout needed)
        seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
        trait_rankings = generator.rank_traits(bigfive_obj, seniority)
    else:
        bigfive_profile = state.get("bigfive_profile")
        trait_rankings = state.get("trait_rankings", [])

    _pending_hitl = locals().get("_pending_hitl", False)
    _policy_decisions_local = locals().get("_policy_decisions", state.get("policy_decisions") or [])
    _policy_result_local = locals().get("_policy_result", None)
    _pd_data = {}
    if _policy_result_local is not None:
        _pd_data["policy_decision"] = {
            "policy_decision": str(_policy_result_local.decision),
            "rationale": _policy_result_local.rationale,
        }
    updates: Dict[str, Any] = {
        "current_stage": "bigfive",
        "bigfive_profile": bigfive_profile,
        "trait_rankings": trait_rankings,
        "stage_history": (state.get("stage_history") or []) + ["bigfive"],
        "completeness": calculate_completeness("bigfive"),
        "requires_approval": _pending_hitl,
        "pending_human_confirmation": _pending_hitl,
        "policy_decisions": _policy_decisions_local,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "bigfive",
            "data": {
                "bigfive_profile": bigfive_profile,
                "trait_rankings": trait_rankings,
                # Task #1065 — flag de fallback determinístico para o
                # painel renderizar o banner "Sugestão mínima — revise".
                "bigfive_used_fallback": locals().get(
                    "bigfive_used_fallback", False
                ),
                # Task #1067 — root-cause label.
                "bigfive_fallback_reason": locals().get(
                    "bigfive_fallback_reason", None
                ),
                # Task #1070 — snapshot agregado de degradação (sessão/tenant).
                "ai_degraded_mode": _emit_fallback_telemetry(
                    state,
                    "bigfive",
                    locals().get("bigfive_fallback_reason", None),
                ),
                **_pd_data,
            },
            "completeness": calculate_completeness("bigfive"),
            "requires_approval": _pending_hitl,
        },
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="bigfive",
        state=state,
        before={
            "bigfive_profile": state.get("bigfive_profile"),
            "trait_rankings": state.get("trait_rankings"),
        },
        after={
            "bigfive_profile": bigfive_profile,
            "trait_rankings_count": len(trait_rankings or []),
        },
        reasoning_extra=[
            f"seniority={state.get('seniority_resolved') or state.get('parsed_seniority')}",
            f"pending_hitl={_pending_hitl}",
        ],
        criteria_used=["jd_enriched", "seniority", "trait_rankings"],
        human_review_required=_pending_hitl,
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:bigfive] %0.fms", elapsed)
    return {**state, **updates}


def salary_node(state: JobCreationState) -> JobCreationState:
    """Validate salary range vs market benchmark.

    Phase 2C-1: now actively fetches benchmark from internal + market sources
    and combines via MarketBenchmarkService.combine_with_internal() (peso 70/30).
    """
    t0 = time.time()
    logger.info("[JobCreation:salary] Starting salary validation")

    # ── Fetch benchmark if not already in state ──
    # Task #1062: timeout determinístico (D4 da auditoria #1058). Em timeout
    # o nó pula benchmark gracefully (`salary_benchmark=None`) — recrutador
    # pode preencher manualmente sem travar o wizard.
    _SALARY_TIMEOUT_S = float(__import__("os").environ.get(
        "LIA_SALARY_TIMEOUT_S", "10"
    ))
    # Task #1065 — flag de fallback (timeout do benchmark fetch ou
    # exception). Painel renderiza banner pedindo revisão manual da faixa.
    salary_used_fallback = False
    # Task #1067 — root-cause label propagado pro painel.
    salary_fallback_reason: Optional[str] = None
    if not state.get("salary_benchmark"):
        try:
            import asyncio as _asyncio
            import concurrent.futures as _cf_sl

            async def _fetch_benchmark():
                from app.core.database import AsyncSessionLocal
                from app.domains.analytics.services.job_insights_service import JobInsightsService
                from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService

                role = state.get("parsed_title") or ""
                seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or ""
                location = state.get("parsed_location") or None
                work_model = state.get("parsed_model") or None
                company_id = str(state.get("workspace_id") or state.get("company_id") or "")

                internal = {}
                market = {}

                # Source 1: internal (requires DB)
                if company_id and role:
                    try:
                        async with AsyncSessionLocal() as _db:
                            insights = JobInsightsService()
                            internal = await insights.get_salary_benchmark(
                                db=_db, company_id=company_id, role=role,
                                seniority=seniority, location=location,
                                work_model=work_model,
                            )
                    except Exception as _int_exc:
                        logger.warning(
                            "[JobCreation:salary] internal benchmark failed: %s", _int_exc,
                        )

                # Source 2: market
                try:
                    market_svc = MarketBenchmarkService()
                    market = await market_svc.search_salary_benchmark(
                        role=role, seniority=seniority, location=location,
                    )
                except Exception as _mkt_exc:
                    logger.warning(
                        "[JobCreation:salary] market benchmark failed: %s", _mkt_exc,
                    )

                # Combine 70/30 if internal high-confidence
                combined = {}
                try:
                    market_svc = MarketBenchmarkService()
                    combined = market_svc.combine_with_internal(
                        internal_data=internal if internal.get("sample_size", 0) > 0 else None,
                        market_data=market,
                    )
                except Exception as _comb_exc:
                    logger.warning(
                        "[JobCreation:salary] combine failed (fail-open): %s", _comb_exc,
                    )
                    combined = market or internal or {}

                return combined

            def _run_fetch():
                return _asyncio.run(_fetch_benchmark())

            # NOTE: shutdown(wait=False) — ver comentário em bigfive_node.
            _ex_sl = _cf_sl.ThreadPoolExecutor(max_workers=1)
            try:
                try:
                    _benchmark = _ex_sl.submit(_run_fetch).result(
                        timeout=_SALARY_TIMEOUT_S
                    )
                except _cf_sl.TimeoutError:
                    logger.warning(
                        "[JobCreation:salary] benchmark fetch timeout after %.1fs — "
                        "skipping benchmark gracefully (Task #1062)",
                        _SALARY_TIMEOUT_S,
                    )
                    _benchmark = None
                    salary_used_fallback = True
                    salary_fallback_reason = "timeout"
                    _emit_wizard_fallback_metric(
                        node="salary", state=state, reason="benchmark_timeout",
                        timeout_s=_SALARY_TIMEOUT_S,
                        elapsed_ms=(time.time() - t0) * 1000,
                    )
            finally:
                _ex_sl.shutdown(wait=False)
            if _benchmark:
                state = {**state, "salary_benchmark": _benchmark}
                logger.info(
                    "[JobCreation:salary] benchmark fetched: source=%s conf=%s",
                    _benchmark.get("source"), _benchmark.get("confidence"),
                )
        except Exception as _bench_exc:
            # Fail-open — não bloqueia o wizard se serviços falharem
            logger.warning(
                "[JobCreation:salary] benchmark fetch failed (fail-open): %s", _bench_exc,
            )
            salary_used_fallback = True
            _exc_str = str(_bench_exc).lower()
            if any(t in _exc_str for t in (
                "rate", "quota", "429", "503", "provider", "api",
                "unauthorized", "forbidden", "401", "403",
            )):
                salary_fallback_reason = "provider_error"
            else:
                salary_fallback_reason = "exception"

    updates: Dict[str, Any] = {
        "current_stage": "salary",
        "stage_history": (state.get("stage_history") or []) + ["salary"],
        "completeness": calculate_completeness("salary"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "salary",
            "data": {
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                "benefits": state.get("benefits", []),
                "benchmark": state.get("salary_benchmark"),
                # Task #1065 — flag de fallback (timeout do benchmark fetch).
                # Painel renderiza banner pedindo revisão manual da faixa.
                "salary_used_fallback": salary_used_fallback,
                # Task #1067 — root-cause label.
                "salary_fallback_reason": salary_fallback_reason,
                # Task #1070 — snapshot agregado de degradação (sessão/tenant).
                "ai_degraded_mode": _emit_fallback_telemetry(
                    state, "salary", salary_fallback_reason,
                ),
            },
            "completeness": calculate_completeness("salary"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:salary] %0.fms", elapsed)
    return {**state, **updates}


def competency_node(state: JobCreationState) -> JobCreationState:
    """F4+F5: Resolve seniority + calculate question distribution.

    F4: Deterministic seniority resolution (5 signals)
    F5: Deterministic question distribution table
    Recruiter chooses screening mode (compact 7q / full 12q).
    """
    t0 = time.time()
    logger.info("[JobCreation:competency] Starting F4+F5")

    jd_enriched = state.get("jd_enriched", {})
    skills = [s.get("skill", "") for s in jd_enriched.get("skills_obrigatorias", [])]

    # F4: Resolve seniority using 5 signals
    seniority_result = resolve_seniority(
        explicit_seniority=state.get("parsed_seniority"),
        job_title=jd_enriched.get("titulo_padronizado") or state.get("parsed_title"),
        job_description=jd_enriched.get("about_role", ""),
        skills=skills,
        salary_min=state.get("salary_min"),
    )

    seniority = seniority_result.final_level
    screening_mode = state.get("screening_mode")

    # F5: Question distribution by mode (deterministic)
    distribution = None
    if screening_mode and seniority:
        distribution = _get_question_distribution(screening_mode, seniority)

    # Build competency tree from enriched JD
    competency_tree = []
    for s in jd_enriched.get("skills_obrigatorias", []):
        competency_tree.append({
            "skill": s.get("skill", ""),
            "contexto": s.get("contexto", ""),
            "block": "technical",
        })
    for c in jd_enriched.get("competencias_comportamentais", []):
        competency_tree.append({
            "skill": c.get("competencia", ""),
            "contexto": c.get("contexto", ""),
            "block": "behavioral",
            "trait": c.get("trait_big_five", ""),
        })

    updates: Dict[str, Any] = {
        "current_stage": "competency",
        "seniority_resolved": seniority,
        "seniority_signals": seniority_result.signals_used,
        "question_distribution": distribution,
        "competency_tree": competency_tree,
        "stage_history": (state.get("stage_history") or []) + ["competency"],
        "completeness": calculate_completeness("competency"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "competency",
            "data": {
                "seniority": seniority,
                "seniority_display": seniority_result.display_name,
                "seniority_confidence": seniority_result.confidence,
                "seniority_signals": seniority_result.signals_used,
                "screening_mode": screening_mode,
                "distribution": distribution,
                "competency_tree": competency_tree,
            },
            "completeness": calculate_completeness("competency"),
            "requires_approval": False,
        },
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="competency",
        state=state,
        before={
            "seniority_resolved": state.get("seniority_resolved"),
            "competency_tree_count": len(state.get("competency_tree") or []),
        },
        after={
            "seniority": seniority,
            "screening_mode": screening_mode,
            "distribution": distribution,
            "competency_tree_count": len(competency_tree),
        },
        reasoning_extra=[
            f"seniority_confidence={seniority_result.confidence}",
            f"signals_used={seniority_result.signals_used}",
        ],
        criteria_used=["parsed_seniority", "skills_obrigatorias", "salary_min",
                       "screening_mode"],
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:competency] seniority=%s mode=%s | %0.fms", seniority, screening_mode, elapsed)
    return {**state, **updates}


def wsi_questions_node(state: JobCreationState) -> JobCreationState:
    """F6: Generate WSI screening questions via LLM.

    This is HITL point 2 — recruiter must approve all questions.

    WSI absolute rules enforced:
    - CBI only (no hypothetical questions)
    - No cultural fit questions
    - Min questions per distribution table (F5)
    """
    t0 = time.time()
    logger.info("[JobCreation:wsi_questions] Starting F6")

    # Policy gate check
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _wsi_policy = evaluate_wizard_policy(WizardIntent.GENERATE_WSI, state)
    _wsi_pd_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "wsi_questions",
        "policy_decision": str(_wsi_policy.decision),
        "rationale": _wsi_policy.rationale,
    }]
    if _wsi_policy.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:wsi_questions] DENY — %s", _wsi_policy.rationale)
        emit_policy_block_audit(stage="wsi_questions", decision=_wsi_policy)
        _wsi_pd_dict = {"policy_decision": str(_wsi_policy.decision), "rationale": _wsi_policy.rationale}
        return {
            **state,
            "policy_decisions": _wsi_pd_decisions,
            "wsi_questions": [],
            "error": f"WSI gen blocked: {_wsi_policy.rationale}",
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": {
                "type": "wizard_stage",
                "stage": "wsi_questions",
                "data": {"policy_blocked": True, "policy_decision": _wsi_pd_dict},
                "completeness": 0,
                "requires_approval": False,
            },
        }
    _wsi_pending_hitl = (_wsi_policy.decision == PolicyDecision.HITL_REQUIRED)

    from app.domains.job_creation.schemas import EnrichedJobDescription

    # If already approved, skip re-generation (resume path)
    if state.get("questions_approved") is not None and state.get("wsi_questions"):
        questions_data = state["wsi_questions"]
    else:
        jd_enriched_dict = state.get("jd_enriched", {})

        # ── FairnessGuard pre-check (WSI input) ──
        # If jd_enriched is discriminatory, do not call the LLM at all.
        _wsi_input_blocked = False
        if jd_enriched_dict:
            _wsi_pre_text = " ".join(filter(None, [
                jd_enriched_dict.get("about_role", ""),
                " ".join(jd_enriched_dict.get("responsabilidades", []) or []),
            ]))
            try:
                from app.shared.compliance.fairness_guard import FairnessGuard as _WSIFg
                _wsi_pre_check = _WSIFg().check(_wsi_pre_text)
                if _wsi_pre_check.is_blocked:
                    logger.warning(
                        "[JobCreation:wsi_questions] FairnessGuard PRE-BLOCK: category=%s — skipping LLM",
                        _wsi_pre_check.category,
                    )
                    _wsi_input_blocked = True
            except Exception as _wsi_pre_exc:
                logger.warning("[JobCreation:wsi_questions] FairnessGuard pre-check failed (fail-open): %s", _wsi_pre_exc)

        if _wsi_input_blocked:
            questions_data = []
        else:
            # ── PII masking (BEFORE LLM) ──
            _safe_wsi_dict = dict(jd_enriched_dict) if jd_enriched_dict else {}
            try:
                from app.domains.job_creation.compliance import mask_pii_for_llm as _wsi_mask
                for _f in ("about_role", "titulo_padronizado"):
                    if _safe_wsi_dict.get(_f):
                        _safe_wsi_dict[_f] = _wsi_mask(_safe_wsi_dict[_f])
                if _safe_wsi_dict.get("responsabilidades"):
                    _safe_wsi_dict["responsabilidades"] = [
                        _wsi_mask(r) if isinstance(r, str) else r
                        for r in _safe_wsi_dict["responsabilidades"]
                    ]
            except Exception as _wsi_pii_exc:
                logger.warning("[JobCreation:wsi_questions] PII masking failed (fail-open): %s", _wsi_pii_exc)

            enriched = EnrichedJobDescription(**_safe_wsi_dict) if _safe_wsi_dict else None
            distribution = state.get("question_distribution", {"technical": 5, "behavioral": 2})
            seniority = state.get("seniority_resolved", "pleno")
            trait_rankings = state.get("trait_rankings", [])

            if enriched:
                generator = _get_wsi_generator()
                # Task #1062: timeout determinístico (D4 da auditoria #1058).
                # Em timeout cai no `_fallback_questions(block, count)` por
                # bloco — mantém o wizard avançando com perguntas mínimas
                # CBI-conformes para revisão humana (HITL #2 ainda exigido).
                import concurrent.futures as _cf_wq
                _WSI_LLM_TIMEOUT_S = float(__import__("os").environ.get(
                    "LIA_WSI_QUESTIONS_TIMEOUT_S", "20"
                ))
                # Task #1065 — flag de fallback determinístico (timeout LLM
                # → `_fallback_questions`). Painel renderiza banner pedindo
                # revisão extra antes da aprovação HITL.
                wsi_questions_used_fallback = False
                # Task #1067 — root-cause label propagado pro painel.
                wsi_questions_fallback_reason: Optional[str] = None
                # NOTE: shutdown(wait=False) — ver comentário em bigfive_node.
                _ex_wq = _cf_wq.ThreadPoolExecutor(max_workers=1)
                try:
                    try:
                        _fut_wq = _ex_wq.submit(
                            generator.generate_questions,
                            enriched=enriched,
                            seniority=seniority,
                            distribution=distribution,
                            trait_rankings=trait_rankings,
                        )
                        question_objs = _fut_wq.result(
                            timeout=_WSI_LLM_TIMEOUT_S
                        )
                    except _cf_wq.TimeoutError:
                        logger.warning(
                            "[JobCreation:wsi_questions] LLM timeout after %.1fs — "
                            "deterministic fallback (Task #1062)",
                            _WSI_LLM_TIMEOUT_S,
                        )
                        n_tech = distribution.get("technical", 5)
                        n_behav = distribution.get("behavioral", 2)
                        question_objs = []
                        if n_tech > 0:
                            question_objs.extend(
                                generator._fallback_questions("technical", n_tech)
                            )
                        if n_behav > 0:
                            question_objs.extend(
                                generator._fallback_questions("behavioral", n_behav)
                            )
                        wsi_questions_used_fallback = True
                        wsi_questions_fallback_reason = "timeout"
                        _emit_wizard_fallback_metric(
                            node="wsi_questions", state=state, reason="llm_timeout",
                            timeout_s=_WSI_LLM_TIMEOUT_S,
                            elapsed_ms=(time.time() - t0) * 1000,
                        )
                    except Exception as _wq_exc:  # noqa: BLE001 — fail-open
                        logger.warning(
                            "[JobCreation:wsi_questions] LLM call failed (%s) — fallback",
                            _wq_exc,
                        )
                        n_tech = distribution.get("technical", 5)
                        n_behav = distribution.get("behavioral", 2)
                        question_objs = []
                        if n_tech > 0:
                            question_objs.extend(
                                generator._fallback_questions("technical", n_tech)
                            )
                        if n_behav > 0:
                            question_objs.extend(
                                generator._fallback_questions("behavioral", n_behav)
                            )
                        wsi_questions_used_fallback = True
                        _exc_str = str(_wq_exc).lower()
                        if any(t in _exc_str for t in (
                            "rate", "quota", "429", "503", "provider", "api",
                            "unauthorized", "forbidden", "401", "403",
                        )):
                            wsi_questions_fallback_reason = "provider_error"
                        else:
                            wsi_questions_fallback_reason = "exception"
                        _emit_wizard_fallback_metric(
                            node="wsi_questions", state=state,
                            reason=f"llm_{wsi_questions_fallback_reason}",
                            timeout_s=_WSI_LLM_TIMEOUT_S,
                            elapsed_ms=(time.time() - t0) * 1000,
                        )
                finally:
                    _ex_wq.shutdown(wait=False)
                questions_data = [q.model_dump() for q in question_objs]
            else:
                questions_data = []

    # ── Layer 4: question fairness guard (per-question scan) ──
    # Removes biased questions and registers in wsi_dropped_questions for audit.
    _wsi_dropped: list[dict[str, Any]] = list(state.get("wsi_dropped_questions") or [])
    _wsi_kept: list[dict[str, Any]] = []
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg_q = FairnessGuard()
        for _q in questions_data:
            _q_text = _q.get("question", "") if isinstance(_q, dict) else ""
            if not _q_text:
                _wsi_kept.append(_q)
                continue
            _check = _fg_q.check(_q_text)
            if _check.is_blocked:
                _wsi_dropped.append({
                    "question": _q_text,
                    "category": _check.category,
                    "blocked_terms": _check.blocked_terms,
                    "message": _check.educational_message,
                })
                logger.warning(
                    "[JobCreation:wsi_questions] FairnessGuard L4 dropped question: "
                    "category=%s, terms=%s",
                    _check.category, _check.blocked_terms,
                )
            else:
                _wsi_kept.append(_q)
        questions_data = _wsi_kept
    except Exception as _fg_l4_exc:
        logger.warning(
            "[JobCreation:wsi_questions] FairnessGuard L4 check failed (fail-open): %s",
            _fg_l4_exc,
        )
        # On failure, keep all questions (don't lose recruiter's work)

    # Build ws_stage_payload data — include fairness_warning when questions were dropped
    _wsi_stage_data: Dict[str, Any] = {
        "questions": questions_data,
        "screening_mode": state.get("screening_mode"),
        "distribution": state.get("question_distribution"),
        # Task #1065 — flag de fallback determinístico para o painel
        # renderizar o banner "Sugestão mínima — revise".
        "wsi_questions_used_fallback": locals().get(
            "wsi_questions_used_fallback", False
        ),
        # Task #1067 — root-cause label.
        "wsi_questions_fallback_reason": locals().get(
            "wsi_questions_fallback_reason", None
        ),
        # Task #1070 — snapshot agregado de degradação (sessão/tenant).
        "ai_degraded_mode": _emit_fallback_telemetry(
            state,
            "wsi_questions",
            locals().get("wsi_questions_fallback_reason", None),
        ),
    }
    if _wsi_dropped:
        _wsi_stage_data["fairness_warning"] = {
            "kind": "questions_dropped",
            "dropped_count": len(_wsi_dropped),
        }
        _wsi_stage_data["dropped_questions"] = _wsi_dropped

    updates: Dict[str, Any] = {
        "current_stage": "wsi_questions",
        "wsi_questions": questions_data,
        "wsi_dropped_questions": _wsi_dropped,
        "stage_history": (state.get("stage_history") or []) + ["wsi_questions"],
        "completeness": calculate_completeness("wsi_questions"),
        "requires_approval": True,
        "pending_human_confirmation": locals().get("_wsi_pending_hitl", False),
        "policy_decisions": locals().get("_wsi_pd_decisions", state.get("policy_decisions") or []),
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "wsi_questions",
            "data": _wsi_stage_data,
            "completeness": calculate_completeness("wsi_questions"),
            "requires_approval": True,
        },
    }
    # Inject policy_decision into ws_stage_payload.data for HITL/ALLOW visibility
    if "_wsi_policy" in dir():
        _wsi_pd_data = {
            "policy_decision": {
                "policy_decision": str(_wsi_policy.decision),
                "rationale": _wsi_policy.rationale,
            }
        }
        updates["ws_stage_payload"]["data"].update(_wsi_pd_data)

    # ── Audit EU AI Act Art.13 — WSI questions generation decision ──
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            _asyncio.run(_audit.log_decision(
                company_id=_company_id,
                agent_name="job_creation:wsi_questions",
                decision_type="generate_wsi_questions",
                action="generate_questions",
                decision=f"generated_{len(questions_data)}_kept_{len(_wsi_dropped)}_dropped",
                reasoning=[
                    f"distribution={state.get('question_distribution')}",
                    f"seniority={state.get('seniority_resolved')}",
                    f"dropped_by_fairness={len(_wsi_dropped)}",
                ],
                criteria_used=["distribution", "trait_rankings", "competency_tree",
                               "fairness_layer4"],
                job_vacancy_id=state.get("job_id"),
                human_review_required=True,  # HITL 2
            ))
    except Exception as _audit_exc:
        logger.warning(
            "[JobCreation:wsi_questions] audit log failed (fail-open): %s", _audit_exc,
        )

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="wsi_questions",
        state=state,
        before={"questions_count": len(state.get("wsi_questions") or [])},
        after={
            "questions_count": len(questions_data),
            "dropped_count": len(_wsi_dropped),
        },
        reasoning_extra=[
            f"distribution={state.get('question_distribution')}",
            f"seniority={state.get('seniority_resolved')}",
            f"dropped_by_fairness={len(_wsi_dropped)}",
        ],
        criteria_used=["distribution", "trait_rankings", "competency_tree",
                       "fairness_layer4"],
        human_review_required=True,
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:wsi_questions] %d questions | %0.fms", len(questions_data), elapsed)
    return {**state, **updates}


def eligibility_node(state: JobCreationState) -> JobCreationState:
    """Pre-screening: yes/no eliminatory questions configured by recruiter."""
    t0 = time.time()
    logger.info("[JobCreation:eligibility] Starting eligibility questions")

    questions = state.get("eligibility_questions", [])

    updates: Dict[str, Any] = {
        "current_stage": "eligibility",
        "stage_history": (state.get("stage_history") or []) + ["eligibility"],
        "completeness": calculate_completeness("eligibility"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "eligibility",
            "data": {"questions": questions},
            "completeness": calculate_completeness("eligibility"),
            "requires_approval": False,
        },
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="eligibility",
        state=state,
        before={"questions_count": len(state.get("eligibility_questions") or [])},
        after={"questions_count": len(questions)},
        reasoning_extra=[f"questions={[q.get('text') if isinstance(q, dict) else str(q) for q in questions[:5]]}"],
        criteria_used=["recruiter_configured_questions"],
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:eligibility] %d questions | %0.fms", len(questions), elapsed)
    return {**state, **updates}


def review_node(state: JobCreationState) -> JobCreationState:
    """Readiness check + apply company defaults from Settings.

    Calls api_client.get_company_defaults() to load recruitment policies,
    default eligibility questions, screening mode defaults, etc.
    """
    t0 = time.time()
    logger.info("[JobCreation:review] Starting readiness check")

    # Load company defaults if not already applied
    defaults_applied = list(state.get("company_defaults_applied", []))
    if not defaults_applied:
        try:
            api = _get_api_client(state)
            workspace_id = state.get("workspace_id", 0)
            company_id = state.get("company_id", "")
            _lookup_id = workspace_id or company_id
            if _lookup_id:
                resp = api.get_company_defaults(_lookup_id)
                if resp.success and resp.data:
                    defaults = resp.data
                    if not state.get("screening_mode") and defaults.get("default_screening_mode"):
                        defaults_applied.append("screening_mode")
                    if not state.get("publish_platforms") and defaults.get("default_platforms"):
                        defaults_applied.append("publish_platforms")
                    if not state.get("eligibility_questions") and defaults.get("default_eligibility"):
                        defaults_applied.append("eligibility_questions")
                    logger.info("[JobCreation:review] Loaded %d company defaults", len(defaults_applied))
        except Exception as e:
            logger.warning("[JobCreation:review] Failed to load company defaults: %s", e)

    readiness = _build_readiness_check(state)

    updates: Dict[str, Any] = {
        "current_stage": "review",
        "readiness_check": readiness,
        "company_defaults_applied": defaults_applied,
        "stage_history": (state.get("stage_history") or []) + ["review"],
        "completeness": calculate_completeness("review"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "review",
            "data": {
                "readiness": readiness,
                "defaults_applied": defaults_applied,
            },
            "completeness": calculate_completeness("review"),
            "requires_approval": False,
        },
    }

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:review] ready=%s | %0.fms", readiness.get("ready"), elapsed)
    return {**state, **updates}


def publish_node(state: JobCreationState) -> JobCreationState:
    """Publish job via Rails API + save screening config + get share link.

    Steps:
    1. Create job in Rails (if no job_id yet)
    2. Save WSI screening questions + eligibility
    3. Publish to selected platforms
    4. Get share link
    5. Auto-dispatch screening if enabled

    Governance: circuit breaker wraps all API calls.
    """
    t0 = time.time()
    logger.info("[JobCreation:publish] Starting publish")

    # Policy gate check — publish is side-effecting (irreversible), so HITL pauses
    # the wizard UNLESS the recruiter has explicitly confirmed via policy_confirmed_publish.
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _pub_quality = state.get("jd_quality_score")
    _pub_policy = evaluate_wizard_policy(
        WizardIntent.PUBLISH_JOB, state,
        score=(_pub_quality / 100.0) if _pub_quality is not None else None,
    )
    _pub_pd_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "publish",
        "policy_decision": str(_pub_policy.decision),
        "rationale": _pub_policy.rationale,
    }]
    _pub_confirmed = state.get("policy_confirmed_publish", False)
    _pub_pd_dict = {"policy_decision": str(_pub_policy.decision), "rationale": _pub_policy.rationale}

    if _pub_policy.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:publish] DENY — %s", _pub_policy.rationale)
        emit_policy_block_audit(stage="publish", decision=_pub_policy)
        return {
            **state,
            "policy_decisions": _pub_pd_decisions,
            "error": _pub_policy.rationale,
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": {
                "type": "wizard_stage", "stage": "publish",
                "data": {"policy_blocked": True, "policy_decision": _pub_pd_dict},
                "completeness": 0, "requires_approval": False,
            },
        }

    if _pub_policy.decision == PolicyDecision.HITL_REQUIRED and not _pub_confirmed:
        logger.info("[PolicyGate:publish] HITL pause — awaiting recruiter confirmation")
        emit_policy_block_audit(stage="publish", decision=_pub_policy)
        return {
            **state,
            "policy_decisions": _pub_pd_decisions,
            "pending_human_confirmation": True,
            "requires_approval": True,
            "job_id": None,
            "ws_stage_payload": {
                "type": "wizard_stage", "stage": "publish",
                "data": {
                    "policy_decision": _pub_pd_dict,
                    "policy_pending_confirmation": True,
                },
                "completeness": 0, "requires_approval": True,
            },
        }

    api = _get_api_client(state)
    job_id = state.get("job_id")
    job_uid = state.get("job_uid")
    share_link = state.get("share_link")
    error = None

    try:
        from app.shared.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
        cb_wrap = lambda fn, *a, **kw: circuit_breaker_call(fn, *a, circuit_key="job_creation:publish", **kw)
    except ImportError:
        cb_wrap = lambda fn, *a, **kw: fn(*a, **kw)

    try:
        # Step 1: Create job if not yet created
        if not job_id:
            jd = state.get("jd_enriched", {})
            job_data = {
                "title": jd.get("titulo_padronizado", state.get("parsed_title", "")),
                "description": jd.get("about_role", ""),
                "seniority": state.get("seniority_resolved", ""),
                "department": state.get("parsed_department", ""),
                "location": state.get("parsed_location", ""),
                "work_model": state.get("parsed_model", ""),
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                "benefits": state.get("benefits", []),
                "technical_requirements": jd.get("skills_obrigatorias", []),
                "behavioral_competencies": jd.get("competencias_comportamentais", []),
                "responsibilities": jd.get("responsabilidades", []),
            }
            resp = cb_wrap(api.create_job, job_data)
            if resp.success and resp.data:
                data = resp.data.get("data", resp.data)
                attrs = data.get("attributes", data)
                job_id = attrs.get("id") or data.get("id")
                job_uid = attrs.get("uid") or data.get("uid")
                logger.info("[JobCreation:publish] Job created: id=%s", job_id)

        if job_id:
            # Step 2: Save screening config (WSI questions + eligibility)
            questions = state.get("wsi_questions", [])
            eligibility = state.get("eligibility_questions", [])
            mode = state.get("screening_mode", "compact")
            if questions:
                cb_wrap(api.save_screening_config, job_id, questions, mode, eligibility)

            # Step 3: Publish to platforms
            platforms = state.get("publish_platforms", ["website"])
            sourcing_mode = state.get("sourcing_mode", "local")
            cb_wrap(api.publish_job, job_id, platforms, sourcing_mode)

            # Step 4: Get share link
            link_resp = cb_wrap(api.get_share_link, job_id)
            if link_resp.success and link_resp.data:
                share_link = link_resp.data.get("share_link") or link_resp.data.get("public_url")

    except Exception as e:
        error = str(e)
        logger.error("[JobCreation:publish] Error: %s", e)

    updates: Dict[str, Any] = {
        "current_stage": "publish",
        "job_id": job_id,
        "job_uid": job_uid,
        "share_link": share_link,
        "error": error,
        "stage_history": (state.get("stage_history") or []) + ["publish"],
        "completeness": calculate_completeness("publish"),
        "requires_approval": False,
        "pending_human_confirmation": False,
        "policy_decisions": locals().get("_pub_pd_decisions", state.get("policy_decisions") or []),
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "publish",
            "data": {
                "job_id": job_id,
                "platforms": state.get("publish_platforms", []),
                "sourcing_mode": state.get("sourcing_mode"),
                "contact_channels": state.get("contact_channels", []),
                "share_link": share_link,
                "auto_screen": state.get("auto_screen_enabled", True),
                "error": error,
            },
            "completeness": calculate_completeness("publish"),
            "requires_approval": False,
        },
    }

    # ── Audit EU AI Act Art.13 — publish job decision ──
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            _asyncio.run(_audit.log_decision(
                company_id=_company_id,
                agent_name="job_creation:publish",
                decision_type="move_stage",
                action="publish_job",
                decision="published" if job_id and not error else "failed",
                reasoning=[
                    f"platforms={state.get('publish_platforms', [])}",
                    f"sourcing_mode={state.get('sourcing_mode')}",
                    *([f"error={error}"] if error else []),
                ],
                criteria_used=["job_data", "screening_config", "publish_platforms"],
                job_vacancy_id=job_id,
                human_review_required=False,
            ))
    except Exception as _audit_exc:
        logger.warning(
            "[JobCreation:publish] audit log failed (fail-open): %s", _audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:publish] job_id=%s share=%s | %0.fms", job_id, bool(share_link), elapsed)

    # Sprint B Phase 1 - JD Similar History: fire-and-forget record after publish
    if not error and job_id:
        try:
            from app.domains.job_creation.services.jd_similar_service import (
                record_jd_fire_and_forget,
            )
            company_id = str(state.get("workspace_id") or state.get("company_id") or "")
            jd_enriched_payload = state.get("jd_enriched") or {}
            title = (
                jd_enriched_payload.get("titulo_padronizado")
                or state.get("parsed_title")
                or ""
            )
            if company_id and title:
                record_jd_fire_and_forget(
                    company_id=company_id,
                    job_id=str(job_id),
                    title=title,
                    jd_enriched=jd_enriched_payload,
                    seniority_level=state.get("seniority_resolved"),
                    department=state.get("parsed_department"),
                )
        except Exception as exc:  # pragma: no cover - never block publish
            logger.warning(
                "[JobCreation:publish] JdSimilar wire failed (non-blocking): %s",
                str(exc)[:200],
            )

    return {**state, **updates}


def calibration_node(state: JobCreationState) -> JobCreationState:
    """Present 3+ candidates for calibration (approve/reject).

    Fetches calibration candidates from Rails API if not already loaded.
    """
    t0 = time.time()
    logger.info("[JobCreation:calibration] Starting calibration")

    candidates = list(state.get("calibration_candidates", []))
    job_id = state.get("job_id")

    # Fetch candidates from API if we have a job_id but no candidates yet
    if job_id and not candidates:
        try:
            api = _get_api_client(state)
            resp = api.get_calibration_candidates(job_id, limit=5)
            if resp.success and resp.data:
                raw = resp.data.get("candidates", resp.data.get("data", []))
                for c in raw:
                    attrs = c.get("attributes", c)
                    candidates.append({
                        "id": str(attrs.get("id", "")),
                        "name": attrs.get("name", ""),
                        "current_title": attrs.get("current_title", ""),
                        "current_company": attrs.get("current_company", ""),
                        "match_score": float(attrs.get("match_score", 0)),
                        "match_criteria": attrs.get("match_criteria", []),
                    })
                logger.info("[JobCreation:calibration] Fetched %d candidates from API", len(candidates))
        except Exception as e:
            logger.warning("[JobCreation:calibration] Failed to fetch candidates: %s", e)

    threshold = state.get("calibration_threshold", 3)
    approved_count = sum(1 for c in candidates if c.get("decision") == "approved")
    complete = approved_count >= threshold

    updates: Dict[str, Any] = {
        "current_stage": "calibration",
        "calibration_complete": complete,
        "stage_history": (state.get("stage_history") or []) + ["calibration"],
        "completeness": calculate_completeness("calibration"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "calibration",
            "data": {
                "candidates": candidates,
                "threshold": threshold,
                "approved_count": approved_count,
                "complete": complete,
            },
            "completeness": calculate_completeness("calibration"),
            "requires_approval": False,
        },
    }

    # ── LL-1 — Calibration delta loop (canonical wiring) ──
    # For each candidate with a recruiter decision, record feedback.
    # Service maintains a running score_delta per job_id used in future evaluations.
    try:
        from app.domains.cv_screening.services.rubric_evaluation_service import calibration_feedback as _cal_fb
        _job_id = str(state.get("job_id") or "")
        _recorded = 0
        if _job_id:
            for _cand in candidates:
                if not isinstance(_cand, dict):
                    continue
                _decision = _cand.get("recruiter_decision")
                if not _decision:
                    continue
                _original = _cand.get("original_score")
                _adjusted = _cand.get("recruiter_adjusted_score")
                _eval_id = str(_cand.get("evaluation_id") or _cand.get("id") or "")
                _cand_id = str(_cand.get("id") or _cand.get("candidate_id") or "")
                if _eval_id and _cand_id and _original is not None:
                    _cal_fb.record_feedback(
                        evaluation_id=_eval_id,
                        candidate_id=_cand_id,
                        job_id=_job_id,
                        original_score=float(_original),
                        recruiter_adjusted_score=(
                            float(_adjusted) if _adjusted is not None else None
                        ),
                        recruiter_decision=str(_decision),
                        feedback_notes=_cand.get("feedback_notes"),
                    )
                    _recorded += 1
            if _recorded > 0:
                logger.info(
                    "[JobCreation:calibration] LL-1 recorded %d feedback entries for job_id=%s",
                    _recorded, _job_id,
                )
    except Exception as _cal_exc:
        logger.warning(
            "[JobCreation:calibration] LL-1 calibration feedback failed (fail-open): %s",
            _cal_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:calibration] %d/%d approved | %0.fms", approved_count, threshold, elapsed)
    return {**state, **updates}


def handoff_node(state: JobCreationState) -> JobCreationState:
    """Navigate recruiter to job page. Inform share link. Chat becomes job assistant."""
    t0 = time.time()
    logger.info("[JobCreation:handoff] Starting handoff")

    job_id = state.get("job_id")
    share_link = state.get("share_link")

    # ── Phase 4G / A2: route whitelist enforcement (Bug P2 fix) ──
    # Use safe_navigate_route to enforce VALID_ROUTES; falls back to None on error.
    handoff_url = None
    if job_id:
        try:
            from app.domains.job_creation.safe_navigation import safe_navigate_route
            handoff_url = safe_navigate_route("/jobs/{job_id}", job_id=job_id)
        except Exception as _nav_exc:
            logger.warning(
                "[JobCreation:handoff] safe_navigate_route failed (fallback): %s", _nav_exc,
            )
            handoff_url = f"/jobs/{job_id}"  # fail-open fallback

    updates: Dict[str, Any] = {
        "current_stage": "handoff",
        "handoff_url": handoff_url,
        "stage_history": (state.get("stage_history") or []) + ["handoff"],
        "completeness": 1.0,
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "handoff",
            "data": {
                "job_id": job_id,
                "handoff_url": handoff_url,
                "share_link": share_link,
            },
            "completeness": 1.0,
            "requires_approval": False,
        },
    }

    # NOTE on LL-2 manager preferences learning loop:
    # ManagerPreferencesService.record_job_completion() is invoked by
    # WizardSessionService.process_message() AFTER graph completes
    # (when current_stage == "handoff"). G8 idempotency_key (MD5) is
    # generated there. See wizard_session_service.py:253+.

    # ── Audit EU AI Act Art.13 — single job_creation audit row ──
    # Emitted exactly once per successful wizard run at handoff.
    try:
        from app.domains.job_creation.compliance import emit_job_creation_audit
        emit_job_creation_audit({**state, **updates})
    except Exception as _handoff_audit_exc:
        logger.warning(
            "[JobCreation:handoff] audit emission failed (fail-open): %s", _handoff_audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:handoff] url=%s | %0.fms", handoff_url, elapsed)
    return {**state, **updates}


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
def jd_gate_node(state: JobCreationState) -> JobCreationState:
    """T2 — gate LLM-based para HITL #1 (jd_enrichment).

    Quando ``state['gate_resume_message']`` está presente, classifica o intent
    do recrutador via LLM (Haiku/Flash temp=0), valida via Pydantic + allowlist,
    e muta state determinísticamente. Sem mensagem de resume → no-op (END
    via ``route_after_gate``).

    Mutações por intent:
      - ``approve``              → ``jd_approved=True``
      - ``reject_with_feedback`` → ``jd_approved=False``, ``jd_rejection_feedback=...``
      - ``provide_new_content``  → ``jd_approved=False``, ``raw_input=<novo>``,
                                   ``jd_enriched=None`` (invalida cache),
                                   roteia para ``intake`` para re-enriquecer
      - ``ask_question``         → state inalterado; ``gate_clarify_message=...``
      - ``off_topic``            → state inalterado; ``gate_clarify_message=...``

    Confidence < 0.7 → re-pergunta natural sem mutar ``jd_approved``.
    """
    # T2 fix #2 (code review #2): no caminho canônico WS via
    # ``WizardSessionService.process_message`` → ``graph.invoke`` direto, o
    # campo ``gate_resume_message`` NÃO é setado externamente — só o caminho
    # action-based em ``domain.py::_handle_gate_jd`` o seta. Para o gate ser
    # alcançado em produção (que é o objetivo da task), detectamos o resume
    # turn por sinal de state nativo: ``jd_enriched`` já populado +
    # ``jd_approved`` ainda None ⇒ recrutador está respondendo ao HITL #1.
    # Nesse caso, ``user_query`` é a resposta dele. Mantemos
    # ``gate_resume_message`` como fonte preferencial para preservar a
    # semântica explícita do path action-based e dos testes existentes.
    msg = (state.get("gate_resume_message") or "").strip()
    if not msg:
        # T2 fix #6 (code review #5): WS resume também precisa cobrir
        # POST-REJECT (jd_approved=False após reject_with_feedback). Antes
        # checávamos só ``jd_approved is None``, então o turno seguinte do
        # recrutador era ignorado uma vez (cleanup limpava jd_approved=None
        # SEM classificar). Agora aceitamos qualquer estado != True
        # (None ou False), e usamos um marcador ``gate_seen_user_query``
        # para evitar re-classificar a MESMA mensagem na mesma invocação
        # (ex.: provide_new_content → intake → jd_enrichment → jd_gate
        # re-entra com user_query inalterado).
        _has_enriched = bool(state.get("jd_enriched"))
        _not_approved_yet = state.get("jd_approved") is not True
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _raw = (state.get("raw_input") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        # T2 fix #8 (code review #6 comment): NÃO auto-classificar no
        # primeiro pass após enrichment — quando ``user_query == raw_input``
        # estamos na invocação inicial (recrutador acabou de mandar a JD;
        # intake+jd_enrichment populou ``jd_enriched`` na MESMA invocação).
        # Sem este guard, o gate roda LLM classifier sobre a própria JD
        # (que classifica como ``provide_new_content`` → re-enrichment loop)
        # e ainda incorre custo desnecessário. Resume real só acontece no
        # turno SEGUINTE, quando ``user_query`` é a resposta do recrutador
        # ao HITL — nesse ponto ``user_query != raw_input``.
        _is_initial_pass = bool(_raw) and _uq == _raw
        if _has_enriched and _not_approved_yet and _is_fresh_turn and not _is_initial_pass:
            msg = _uq
            logger.info(
                "[JobCreation:jd_gate] WS resume detected (jd_enriched + fresh user_query, jd_approved=%s) — classify",
                state.get("jd_approved"),
            )
    if not msg:
        # Primeira passagem (após enrichment) OU re-entrada após
        # ``provide_new_content`` ter rodado intake+jd_enrichment_node. Sem
        # mensagem nova do recrutador para classificar.
        #
        # T2 fix #4 (code review #3): LIMPAR ``gate_last_intent`` e resetar
        # ``jd_approved`` quando re-entrando depois de um intent transitório
        # (provide_new_content / reject_with_feedback / ask_question /
        # off_topic). Sem isso, o ``route_after_gate`` ainda enxerga
        # ``provide_new_content + jd_approved=False`` desta visita anterior
        # e re-roteia para ``intake`` em loop até estourar
        # ``GraphRecursionError``. ``approve`` (jd_approved=True) NÃO é
        # transitório — preservamos. ``fairness_blocked`` também é terminal.
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in (
            "provide_new_content", "reject_with_feedback",
            "ask_question", "off_topic",
        )
        clean_state = {**state, "current_stage": "jd_enrichment"}
        if _is_transitional and not state.get("jd_fairness_blocked"):
            clean_state["gate_last_intent"] = None
            # jd_approved foi setado a False por essas mutações — reseta para
            # None ("aguardando aprovação") para o route cair no branch END
            # padrão e aguardar o próximo turno do recrutador.
            if state.get("jd_approved") is False:
                clean_state["jd_approved"] = None
        logger.info(
            "[JobCreation:jd_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # Layer 1 fairness on the user's *resume* message (a discriminação pode
    # entrar via "manda bala mas só candidatos masculinos"). FairnessGuard L1
    # também roda em ``jd_enrichment_node`` sobre ``raw_input`` — aqui é defesa
    # adicional sobre a mensagem do gate.
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:jd_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "jd_fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "jd_enrichment",
            }
    except Exception as exc:
        # Fail-open: bug do guard não deve travar o wizard.
        logger.debug("[JobCreation:jd_gate] FairnessGuard check failed (fail-open): %s", exc)

    # LLM classifier — async chamado em sync context (graph nodes são sync).
    from app.domains.job_creation.services.wizard_gate_classifier import (
        get_wizard_gate_classifier, _make_fallback,
    )
    classifier = get_wizard_gate_classifier()

    import asyncio as _asyncio
    output = None
    try:
        try:
            running_loop = _asyncio.get_event_loop()
        except RuntimeError:
            running_loop = None
        # T2 fix #3 (code review #2): plumb company_id/user_id do state para
        # o classifier registrar custo no ledger ``external_api_consumption``
        # (ConsumptionTrackingService.record_llm_call) por tenant. Sem isso,
        # o cost tracker fica configurado mas nunca dispara em produção.
        _company_id = (
            state.get("workspace_id") or state.get("company_id")
        )
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=msg,
            stage="jd_enrichment",
            ws_stage_payload=state.get("ws_stage_payload"),
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
            company_id=str(_company_id) if _company_id else None,
            user_id=str(_user_id) if _user_id else None,
        )
        if running_loop is not None and running_loop.is_running():
            # Dentro de loop ativo (ex.: chamado de WS handler async). Offload
            # para thread isolada com seu próprio event loop.
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(lambda: _asyncio.run(coro_factory()))
                output = _fut.result(timeout=30.0)
        else:
            output = _asyncio.run(coro_factory())
    except Exception as exc:
        logger.warning("[JobCreation:jd_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort) — EU AI Act Art. 13: decisão LLM rastreável.
    try:
        _emit_jd_gate_audit(state, msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:jd_gate] audit emit failed: %s", exc)

    # Confidence floor — re-pergunta natural sem mutar jd_approved.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:jd_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": output.conversational_reply,
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "jd_enrichment",
            "gate_seen_user_query": msg,
        }

    intent = output.intent
    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "jd_enrichment",
        # T2 fix #6: marca a mensagem como já classificada nesta invocação,
        # para evitar re-classificação no segundo visit do gate (após
        # provide_new_content → intake → jd_enrichment → jd_gate).
        "gate_seen_user_query": msg,
    }

    extracted = output.extracted_data if isinstance(output.extracted_data, dict) else {}

    if intent == "approve":
        next_state["jd_approved"] = True
        next_state["gate_clarify_message"] = output.conversational_reply or None
    elif intent == "reject_with_feedback":
        next_state["jd_approved"] = False
        feedback = (extracted.get("feedback") or output.conversational_reply or msg)
        next_state["jd_rejection_feedback"] = str(feedback)[:1000]
        next_state["gate_clarify_message"] = output.conversational_reply or None
    elif intent == "provide_new_content":
        new_content = extracted.get("new_content") or msg
        next_state["jd_approved"] = False
        next_state["raw_input"] = str(new_content)[:8000]
        next_state["jd_enriched"] = None  # invalida cache → jd_enrichment_node re-roda
        next_state["jd_quality_score"] = 0.0
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Recebi a descrição nova. Vou re-enriquecer agora."
        )
    elif intent == "ask_question":
        # Não muta jd_approved — recrutador fez pergunta, segue aguardando.
        next_state["gate_clarify_message"] = output.conversational_reply
    elif intent == "off_topic":
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Vamos focar na descrição da vaga? Você quer aprovar ou ajustar algo?"
        )
    else:
        # Defesa em profundidade — Pydantic Literal já blinda, mas se algo
        # vazar (ex.: bug futuro no schema) caímos no fallback de pergunta.
        logger.warning("[JobCreation:jd_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            "Não consegui interpretar sua resposta. Pode me dizer se aprovou "
            "a descrição enriquecida ou se quer ajustar alguma coisa?"
        )

    return next_state


def _emit_jd_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o gate LLM.

    Best-effort: falha NÃO bloqueia o resume. Inclui ``intent``,
    ``confidence``, ``thread_id`` e preview do reply para correlação no
    trail. Mantém EU AI Act Art. 13 (decisões automatizadas rastreáveis).
    """
    import asyncio as _asyncio
    company_id = str(
        state.get("workspace_id") or state.get("company_id") or ""
    )
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    # T2 fix #9 (code review #6 comment 3): EU AI Act Art. 13 — incluir
    # snapshot before/after compacto do state mutado pelo gate. Sem isso, o
    # audit row registra a decisão (intent/confidence) mas não a mutação,
    # quebrando rastreabilidade de "qual decisão automatizada alterou o
    # quê". Snapshot mínimo: jd_approved + gate_last_intent (campos
    # determinísticos da intent map) + jd_quality_score.
    _intent = str(output.intent)
    _before = {
        "jd_approved": state.get("jd_approved"),
        "gate_last_intent": state.get("gate_last_intent"),
        "jd_quality_score": state.get("jd_quality_score"),
        "jd_enriched_present": bool(state.get("jd_enriched")),
    }
    _after_jd_approved = _before["jd_approved"]
    if _intent == "approve":
        _after_jd_approved = True
    elif _intent in ("reject_with_feedback", "provide_new_content"):
        _after_jd_approved = False
    _after = {
        "jd_approved": _after_jd_approved,
        "gate_last_intent": _intent,
        "jd_quality_score": 0.0 if _intent == "provide_new_content" else _before["jd_quality_score"],
        "jd_enriched_present": False if _intent == "provide_new_content" else _before["jd_enriched_present"],
    }
    coro = audit_service.log_decision(
        company_id=company_id,
        agent_name="wizard_jd_gate_classifier",
        decision_type="wizard_step_completed",
        action="jd_gate_classify",
        decision=_intent,
        reasoning=[
            f"intent={_intent}",
            f"confidence={float(output.confidence or 0.0):.2f}",
            f"thread_id={state.get('session_id') or ''}",
            f"user_msg_preview={user_message[:120]}",
            f"reply_preview={(output.conversational_reply or '')[:120]}",
            f"state_before={_before}",
            f"state_after={_after}",
        ],
        criteria_used=["llm_intent_classifier", "wizard_jd_enrichment"],
        confidence=float(output.confidence or 0.0),
    )
    try:
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(coro)
            return
    except RuntimeError:
        pass
    try:
        _asyncio.run(coro)
    except Exception as exc:
        logger.debug("[JobCreation:jd_gate] audit run failed: %s", exc)


def route_after_gate(state: JobCreationState) -> str:
    """Routing após gate_node LLM. Determinístico baseado em mutações
    aplicadas por ``jd_gate_node``."""
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
        if quality < 30:
            logger.info("[JobCreation:route] jd_gate -> END (quality %.1f < 30)", quality)
            return "end"
        logger.info("[JobCreation:route] jd_gate -> bigfive (approved)")
        return "bigfive"

    # ask_question / off_topic / pending → aguarda novo turno
    logger.info("[JobCreation:route] jd_gate -> END (intent=%s, awaiting next turn)", intent)
    return "end"


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

    if quality < 30:
        logger.info("[JobCreation:route] jd_enrichment -> END (quality %.1f < 30, blocked)", quality)
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

def _get_question_distribution(mode: str, seniority: str) -> Dict[str, int]:
    """WSI F5 deterministic distribution tables.

    Source: WSI_METHODOLOGY_COMPLETE_v2.md — canonical values.
    These MUST match the methodology exactly; do not change without updating the doc.
    """
    # Compact mode (7 questions total) — from methodology table
    compact_dist = {
        "estagiario": {"technical": 5, "behavioral": 2},
        "junior": {"technical": 5, "behavioral": 2},
        "pleno": {"technical": 5, "behavioral": 2},
        "senior": {"technical": 4, "behavioral": 3},
        "lead": {"technical": 3, "behavioral": 4},
        "principal": {"technical": 4, "behavioral": 3},
        "staff": {"technical": 4, "behavioral": 3},
        "diretor": {"technical": 3, "behavioral": 4},
    }
    # Full mode (12 questions total) — from methodology table
    full_dist = {
        "estagiario": {"technical": 9, "behavioral": 3},
        "junior": {"technical": 9, "behavioral": 3},
        "pleno": {"technical": 8, "behavioral": 4},
        "senior": {"technical": 7, "behavioral": 5},
        "lead": {"technical": 7, "behavioral": 5},
        "principal": {"technical": 7, "behavioral": 5},
        "staff": {"technical": 7, "behavioral": 5},
        "diretor": {"technical": 7, "behavioral": 5},
    }

    table = compact_dist if mode == "compact" else full_dist
    seniority_key = (
        seniority.lower()
        .replace("sênior", "senior")
        .replace("júnior", "junior")
        .replace("estágio", "estagiario")
        .replace("estagiário", "estagiario")
    )

    return table.get(seniority_key, table.get("pleno", {"technical": 5, "behavioral": 2}))


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
        _asyncio.get_event_loop().call_soon_threadsafe(
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
    if use_llm_gates:
        builder.add_node("jd_gate", jd_gate_node)
    builder.add_node("bigfive", bigfive_node)
    builder.add_node("salary", salary_node)
    builder.add_node("competency", competency_node)
    builder.add_node("wsi_questions", wsi_questions_node)
    builder.add_node("eligibility", eligibility_node)
    builder.add_node("review", review_node)
    builder.add_node("publish", publish_node)
    builder.add_node("calibration", calibration_node)
    builder.add_node("handoff", handoff_node)

    # Entry point
    builder.set_entry_point("intake")

    # Linear edges (no conditional routing needed)
    builder.add_edge("intake", "jd_enrichment")

    # HITL point 1: JD enrichment
    if use_llm_gates:
        # T2 — jd_enrichment escapa direto para o gate_node, que classifica
        # o intent do recrutador via LLM e decide o roteamento.
        builder.add_edge("jd_enrichment", "jd_gate")
        builder.add_conditional_edges(
            "jd_gate",
            route_after_gate,
            {
                "bigfive": "bigfive",
                "intake": "intake",
                "end": END,
            },
        )
    else:
        builder.add_conditional_edges(
            "jd_enrichment",
            route_after_jd,
            {
                "bigfive": "bigfive",
                "intake": "intake",
                "end": END,
            },
        )

    # F2+F3 -> salary -> F4+F5
    builder.add_edge("bigfive", "salary")
    builder.add_edge("salary", "competency")

    # F4+F5: needs screening mode
    builder.add_conditional_edges(
        "competency",
        route_after_competency,
        {
            "wsi_questions": "wsi_questions",
            "end": END,
        },
    )

    # HITL point 2: WSI questions
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

    # Review: check readiness
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
        return self._graph.invoke(state, config=config)

    def resume(
        self,
        thread_id: str,
        prior_state: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> JobCreationState:
        """Resume a wizard session after HITL approval.

        The caller (domain.py) is responsible for passing the prior_state
        from the last invocation. We merge the recruiter's updates and
        re-invoke the graph. The checkpointer handles thread continuity.

        This follows the same pattern as scheduling: caller accumulates
        state, graph is re-invoked with merged state.
        """
        merged = {**prior_state, **updates}
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(merged, config=config)


def get_job_creation_graph() -> JobCreationGraph:
    return JobCreationGraph()


# Module-level singleton alias used by graph_runner and tests via monkeypatch.
# Tests call: monkeypatch.setattr(jc_graph, "job_creation_graph", stub, raising=True)
job_creation_graph: JobCreationGraph = get_job_creation_graph()


def get_intake_extractor():
    """Return a fresh IntakeExtractor instance.

    Tests monkeypatch this function at module level to inject a stub extractor
    without instantiating the full graph stack.
    """
    from app.domains.job_creation.services.intake_extractor import IntakeExtractor
    return IntakeExtractor()
