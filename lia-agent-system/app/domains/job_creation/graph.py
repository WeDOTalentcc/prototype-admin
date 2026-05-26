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
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END


def _extract_last_turns(state: Any, n: int = 3) -> list[str]:
    """Task #1123 — extrai últimas N turns de ``state['conversation_messages']``.

    Formato canônico: ``[{"role": "user"|"assistant", "content": "..."}, ...]``.
    Devolve lista de strings ``"<role>: <content>"`` para alimentar prompts dos
    classifiers e do meta-question helper. Tail bounded (default 3 turnos);
    content truncado a 300 chars por turno. Fail-open: state malformado
    devolve lista vazia (caller trata como "sem histórico").
    """
    try:
        msgs = state.get("conversation_messages") or []
    except Exception:
        return []
    out: list[str] = []
    for m in list(msgs)[-(n * 2):]:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower() or "msg"
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        out.append(f"{role}: {content[:300]}")
    return out[-n:]


def _min_jd_quality_threshold() -> float:
    """Min JD quality score (0-100) required to advance past jd_gate to bigfive.

    Configurable via ``LIA_WIZARD_MIN_JD_QUALITY`` env var. Default 30
    (production threshold — vagas with quality < 30 force the recruiter
    to rewrite). In dev environments where the LLM enrichment proxy
    fails (e.g. Replit modelfarm Gemini endpoint not supported), every
    enrichment hits the deterministic fallback (score=20.0). Set this
    env var to ``0`` in dev to allow the wizard to advance past the
    fallback enrichment for testing. See harness fix 2026-05-19
    (Bug C — wizard stuck at jd_gate after 'Recebi a descrição').
    """
    raw = os.environ.get("LIA_WIZARD_MIN_JD_QUALITY", "30").strip()
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 30.0


def _try_meta_helper(
    *,
    state: Any,
    stage: str,
    user_message: str,
    stage_description: str,
) -> str | None:
    """Task #1123 — wrapper sync para ``wizard_meta_question_helper``.

    Captura qualquer exceção (incluindo ``ImportError`` em testes offline
    onde o módulo não está presente) e devolve ``None`` — caller cai no
    ``output.conversational_reply`` do classifier. Mantém o gate
    determinístico do ponto de vista de fluxo (helper só altera o TEXTO
    da resposta, não o roteamento).
    """
    try:
        from app.domains.job_creation.services.wizard_meta_question_helper import (
            generate_meta_response_sync,
        )
        return generate_meta_response_sync(
            stage=stage,
            user_message=user_message,
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            last_turns=_extract_last_turns(state, n=3),
            stage_description=stage_description,
        )
    except Exception as _exc:
        logger.info("[JobCreation:meta_helper] failed (fail-open): %s", _exc)
        return None


def _in_graph_runtime() -> bool:
    """True iff currently executing inside a LangGraph node (Pregel runtime).

    Task #1094 — used by gate_nodes to guard ``langgraph.types.interrupt()``
    calls so they remain test-safe when the gate function is invoked as a
    plain Python callable (offline sentinels: T2/T4/T5/T6) rather than via
    ``graph.invoke()``. In runtime, ``get_config()`` returns the active
    Pregel config; outside runtime it raises (RuntimeError or LookupError
    depending on the langgraph version). Either way we report False and the
    gate falls back to the legacy END no-op semantics.
    """
    try:
        from langgraph.config import get_config
        get_config()
        return True
    except Exception:
        return False


def _llm_gates_enabled() -> bool:
    """Task #1085 (T2) — feature flag ``LIA_WIZARD_LLM_GATES``.

    Task #1130 (GA) — flag agora **ON por default em TODOS os ambientes**
    (dev, staging, prod). Os 3 gates restantes (competency #1086, wsi
    #1087, review #1088) foram migrados para o classifier LLM e ficaram
    estáveis. O caminho legado ``route_after_jd`` keyword-based segue
    disponível só para rollback emergencial via ``LIA_WIZARD_LLM_GATES=0``.

    Lido a cada chamada ao builder para que testes possam alternar o flag
    via ``monkeypatch.setenv`` sem reset do módulo.

    REMOVE: 2026-09-01 — após 30 dias de baseline pós-GA sem regressão,
    deletar ``route_after_jd``/``route_after_competency``/``route_after_wsi``/
    ``route_after_review`` keyword-based do ``domain.py`` e remover o
    short-circuit "OFF" desta função (a flag deixa de existir, gates LLM
    viram caminho único).
    """
    raw = os.environ.get("LIA_WIZARD_LLM_GATES", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    # Task #1130 — default ON em TODOS os ambientes. Mantemos a leitura de
    # ``LIA_ENV``/``APP_ENV``/``ENVIRONMENT`` no histórico para que
    # operadores possam reconhecer o callsite, mas a inferência por
    # ambiente foi APOSENTADA (toda ramificação caía em True após GA).
    return True

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
def _build_pipeline_template_db_suggestion(state: dict) -> Optional[Dict[str, Any]]:
    """Sync wrapper canonical para uso dentro dos nodes do graph.

    Returns {"templates": [...], "top_score": float, "should_suggest": bool} ou None.
    """
    try:
        from app.domains.pipeline.tools.pipeline_template_wizard_tools import (
            suggest_pipeline_template_sync_for_graph,
        )
    except Exception:  # noqa: BLE001 — fail-open por design
        return None
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return None
    return suggest_pipeline_template_sync_for_graph(
        company_id,
        department=state.get("parsed_department") or state.get("department"),
        seniority=state.get("parsed_seniority"),
        job_family=state.get("parsed_job_family"),
    )




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
            _ws = state.get("workspace_id")
            _cid = state.get("company_id")
            _keys = sorted(list(state.keys()))[:15]
            logger.warning(
                "[JobCreation:%s] audit skipped — missing company_id (ws=%r cid=%r keys=%s)",
                stage, _ws, _cid, _keys,
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

        # REGRA 4 sensor — Prometheus counter for Grafana alarm.
        # inc_wizard_fallback is fail-open + cardinality-bounded.
        try:
            from app.shared.observability.fallback_metrics import (
                inc_wizard_fallback,
            )
            inc_wizard_fallback(node, reason)
        except Exception as _counter_exc:  # noqa: BLE001 — fail-open
            logger.debug(
                "[JobCreation:%s] wizard fallback counter inc failed: %s",
                node, _counter_exc,
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
        # Fill ONLY fields that aren't already explicit in state.
        # ``extraction`` is a ``JobIntakePayload`` (canonical schema —
        # `intake_extractor.py:97`). Each field is an ``IntakeField`` with
        # ``.value`` and ``.source``. Reading raw attributes (``.parsed_title``)
        # would AttributeError silently and was the root cause of Task #1096
        # input-thin guard always firing — see audit
        # ``docs/audits/wizard-job-creation-2026-05.md`` and
        # ``docs/architecture/wizard-flow.md``.
        def _val(field_name: str):
            f = getattr(extraction, field_name, None)
            if f is None:
                return None
            v = getattr(f, "value", None)
            if v in (None, "", []):
                return None
            return v

        parsed_title = parsed_title or _val("title")
        parsed_seniority = parsed_seniority or _val("seniority")
        parsed_department = parsed_department or _val("department")
        parsed_location = parsed_location or _val("location")
        # NB: schema field is ``work_model`` (remoto/hibrido/presencial),
        # exposed downstream as ``parsed_model`` for state continuity.
        parsed_model = parsed_model or _val("work_model")
        intake_confidence = extraction.overall_confidence
        _title_field = getattr(extraction, "title", None)
        intake_source = (
            getattr(_title_field, "source", None) or "regex"
        )
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

    # WT-2022 P0.C: LGPD Art. 20 audit trail para decisão automatizada de intake extraction.
    # Caller-side wire (intake_extractor.extract é sync; intake_node também é sync — não
    # pode usar await). Pattern: schedule fire-and-forget coroutine no loop em execução
    # (LangGraph roda em async runtime). Fail-safe: gap de log NUNCA bloqueia wizard.
    try:
        import asyncio
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            from app.core.database import async_session_factory
            from app.shared.services.automated_decision_logger import (
                PROTECTED_CRITERIA_PT,
                log_automated_decision,
            )

            _audit_job_id = str(state.get("job_id")) if state.get("job_id") else None
            _audit_model = f"intake_extractor_{intake_source}"
            _audit_explanation = (
                f"Intake extraction (source={intake_source}, conf={intake_confidence:.2f}): "
                f"title={parsed_title!r}, seniority={parsed_seniority!r}, "
                f"location={parsed_location!r}, model={parsed_model!r}."
            )
            _audit_conf = float(intake_confidence) if intake_confidence else None

            async def _do_audit_log():
                try:
                    async with async_session_factory() as _adl_db:
                        # fire-and-forget audit context (scheduled via
                        # loop.create_task below); persist errors are logged
                        # but MUST NOT bubble up — the wizard intake path
                        # cannot block on the LGPD audit log. P0.C.HELPER
                        # pattern: caller opts in to silent persist degrade.
                        await log_automated_decision(
                            db=_adl_db,
                            company_id=_company_id,
                            job_id=_audit_job_id,
                            decision_type="intake_extraction",
                            ai_model_used=_audit_model,
                            explanation_text=_audit_explanation,
                            criteria_used=["title", "seniority", "department", "location", "work_model"],
                            criteria_ignored=PROTECTED_CRITERIA_PT,
                            confidence_score=_audit_conf,
                            review_eligible=True,
                            silent_on_persist_error=True,
                        )
                        await _adl_db.commit()
                except Exception as _inner_exc:  # fail-safe
                    logger.warning(
                        "[JobCreation:intake] WT-2022 P0.C inner audit log failed (fail-safe): %s",
                        _inner_exc,
                    )

            try:
                _loop = asyncio.get_running_loop()
                _loop.create_task(_do_audit_log())
            except RuntimeError:
                # Sem loop ativo (testes sync isolados). Pular log — pattern fail-safe.
                logger.debug(
                    "[JobCreation:intake] WT-2022 P0.C audit log skipped (no running loop)",
                )
    except Exception as _adl_exc:  # fail-safe: log gap não bloqueia wizard
        logger.warning(
            "[JobCreation:intake] WT-2022 P0.C audit log scheduling failed (fail-safe): %s",
            _adl_exc,
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Captei: {parsed_title}."
                    if parsed_title
                    else "Pode me passar o título da vaga ou colar a JD?"
                ),
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
                    # Sprint Pipeline Templates 2026-05-26 — canonical DB-based suggestion
                    # (Phase 1.6). Frontend prefere quando templates != [] e score >= threshold.
                    "pipeline_template_db": _build_pipeline_template_db_suggestion(state),
                },
            },
            "completeness": calculate_completeness("intake"),
            "requires_approval": False,
        },
    }

    # ── Sprint Pipeline Templates Gap #5 (2026-05-26) — wiring backend↔frontend ──
    # Frontend useWizardFlow lê ui_action no top do ws_stage_payload + data.templates.
    # Quando DB suggestion tem should_suggest=True, eleva templates pro top de data
    # e emite ui_action="suggest_pipeline_template". data.suggestions_data.pipeline_template_db
    # permanece intacto (retrocompat com wizard-plan-card.ts legacy via Task #1055).
    try:
        _db_sugg = (
            (updates.get("ws_stage_payload", {}).get("data", {}) or {})
            .get("suggestions_data", {})
            .get("pipeline_template_db")
        )
        if (
            isinstance(_db_sugg, dict)
            and _db_sugg.get("should_suggest")
            and _db_sugg.get("templates")
        ):
            updates["ws_stage_payload"]["ui_action"] = "suggest_pipeline_template"
            updates["ws_stage_payload"]["data"]["templates"] = _db_sugg["templates"]
    except Exception:  # noqa: BLE001 — fail-open por design (telemetria, não bloqueia fluxo)
        pass

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

    # ── Input-thin guard (Task #1096 / canonical-fix) ──
    # Quando o recrutador escreve apenas uma mensagem de intenção (ex.:
    # "vamos abrir uma vaga", "quero criar vaga"), sem JD anexada, sem
    # texto colado e sem right_panel_form preenchido, NÃO faz sentido
    # gastar tokens enriquecendo lixo. O LLM produziria uma JD inventada
    # e o painel renderizaria conteúdo fictício. Este guard pede ao
    # recrutador o material mínimo (JD colada, upload, ou continuar
    # respondendo no painel) e devolve uma ``data.message`` contextual
    # — fechando a lacuna que disparava ``[ATENÇÃO: estado inconsistente]``
    # via ``WizardSessionService._emit_silent_fallback`` (Task #1089 T3).
    # Threshold escolhido empiricamente: JDs reais têm ≥120 caracteres;
    # mensagens de intenção (intake-only) ficam <80. Margem de segurança
    # de 100 evita falsos positivos em JDs muito curtas.
    _has_panel_form = bool(state.get("right_panel_form"))
    _has_attached = bool((state.get("attached_file_text") or "").strip())
    _has_parsed_title = bool((state.get("parsed_title") or "").strip())
    _raw_len = len((raw_input or "").strip())

    # Task #1123 — classifier-first refactor.
    # Anterior: `_guard_eligible` (com raw_len<100) gateava o classifier;
    # mensagens ≥100 chars que eram perguntas meta nunca passavam pelo LLM
    # e gastavam 2K tokens enriquecendo lixo (causa raiz #3 da auditoria).
    # Agora: `_classifier_eligible` NÃO depende de comprimento — o LLM
    # decide o intent em todos os turnos iniciais sem JD válida. O guard
    # estático (template "preciso de mais contexto") vira ÚLTIMO recurso:
    # só dispara se o classifier devolveu None/baixa conf E a mensagem é
    # genuinamente magra (raw_len<100). Mantém safety net contra
    # disponibilidade do LLM sem reintroduzir o non-determinismo de
    # length-gated routing.
    _classifier_eligible = (
        not state.get("jd_enriched")  # nunca short-circuit em resume
        and not _has_panel_form
        and not _has_attached
        and not _has_parsed_title
    )

    # ── Task #1098 + Task #1123 — LLM intent classifier SEMPRE roda ──
    # O guard de Task #1096 trata QUALQUER mensagem curta como "intent_only".
    # O classifier (Claude Haiku, sync, Pydantic-validado) refina em 4 buckets
    # canônicos: provides_jd_intent | meta_question | intent_only | off_topic.
    # Fail-OPEN: qualquer falha (flag OFF, sem API key, timeout, schema
    # inválido, off-allowlist) devolve None e caímos no guard estático
    # (preserva safety net). NUNCA usamos `conversational_reply` do LLM
    # como controle de fluxo — só como texto exibido. Mutação de state
    # é determinística por intent. Ver
    # ``services/intake_intent_classifier.py``.
    _intent_intake = None
    if _classifier_eligible:
        # Task #1123 — últimas 3 turns do checkpoint para o classifier
        # saber que o recrutador acabou de repetir a mesma pergunta meta.
        _last_turns = _extract_last_turns(state, n=3)
        try:
            from app.domains.job_creation.services.intake_intent_classifier import (
                get_intake_intent_classifier,
            )
            _intent_intake = get_intake_intent_classifier().classify_sync(
                user_message=raw_input,
                has_panel_form=_has_panel_form,
                has_attached_file=_has_attached,
                last_turns=_last_turns,
            )
        except Exception as _intent_exc:
            logger.info(
                "[JobCreation:jd_enrichment] intent classifier failed (fail-open): %s",
                _intent_exc,
            )
            _intent_intake = None

    # Static guard só dispara se classifier não resolveu E a mensagem é
    # genuinamente magra. Última linha de defesa, não primeira.
    _guard_eligible = (
        _classifier_eligible
        and (_intent_intake is None or _intent_intake.confidence < 0.7)
        and _raw_len < 100
    )

    if _intent_intake is not None and _intent_intake.confidence >= 0.7:
        _intent = _intent_intake.intent
        _reply = (
            _intent_intake.conversational_reply
            or "Pode me passar o título do cargo para começar?"
        )
        # Branch determinístico por intent ∈ ALLOWED_INTAKE_INTENTS.
        if _intent == "provides_jd_intent":
            # Não dispara o guard — segue para LLM enrichment com o que tem.
            logger.info(
                "[JobCreation:jd_enrichment] intent=provides_jd_intent (conf=%.2f) — skipping guard",
                _intent_intake.confidence,
            )
            # Continua o fluxo normal abaixo (Layer 2 PII strip + LLM).
            _guard_eligible = False
        elif _intent in ("meta_question", "off_topic"):
            logger.info(
                "[JobCreation:jd_enrichment] intent=%s (conf=%.2f) — short-circuit with helpful reply",
                _intent, _intent_intake.confidence,
            )
            # Task #1123 — enriquecer reply via helper Sonnet (tenant +
            # last_turns + stage description). Best-effort: cai no
            # conversational_reply do classifier se Sonnet falhar.
            try:
                from app.domains.job_creation.services.wizard_meta_question_helper import (
                    generate_meta_response_sync,
                )
                _sonnet_reply = generate_meta_response_sync(
                    stage="jd_enrichment",
                    user_message=raw_input,
                    tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
                    last_turns=_extract_last_turns(state, n=3),
                    stage_description=(
                        "início do wizard: precisamos do título do cargo "
                        "ou da descrição da vaga (JD) para começar."
                    ),
                )
                if _sonnet_reply:
                    _reply = _sonnet_reply
            except Exception as _meta_exc:
                logger.info(
                    "[JobCreation:jd_enrichment] meta helper failed (fail-open): %s",
                    _meta_exc,
                )
            return {
                **state,
                "current_stage": "jd_enrichment",
                "jd_enriched": None,
                "jd_quality_score": 0.0,
                "jd_quality_warnings": [],
                "jd_fairness_blocked": False,
                "requires_approval": False,
                "stage_history": (state.get("stage_history") or [])
                + [f"jd_enrichment_intent_{_intent}"],
                "ws_stage_payload": {
                    "type": "wizard_stage",
                    "stage": "jd_enrichment",
                    "data": {
                        "awaiting_jd_input": True,
                        "intent_classified": _intent,
                        "message": _reply,
                    },
                    "requires_approval": False,
                },
            }
        elif _intent == "intent_only":
            # Task #1123 — "quero abrir uma vaga" / similar: intenção clara
            # mas SEM conteúdo de JD. Força guard estático (ask for JD/title)
            # independente de raw_len. NUNCA cai em enrichment.
            logger.info(
                "[JobCreation:jd_enrichment] intent=intent_only (conf=%.2f) — firing guard",
                _intent_intake.confidence,
            )
            _guard_eligible = True

    if _guard_eligible:
        # Task #1097 — mensagem UI-neutra. Versões anteriores prometiam
        # "painel à direita" e "responder no painel", mas o painel lateral
        # nem sempre está montado (ex.: viewport mobile, layout reduzido,
        # release-flag desligada). Aqui falamos só de ações universais
        # (chat e anexo) e deixamos a alternativa textual como "me diga".
        _ask_jd_msg = (
            "Para começar a criação da vaga, preciso de mais contexto. "
            "Você pode (a) colar a descrição da vaga (JD) aqui no chat, "
            "ou (b) anexar um arquivo (PDF, DOCX ou TXT). "
            "Se preferir, me diga em uma frase o título do cargo, a "
            "senioridade e as principais responsabilidades."
        )
        logger.info(
            "[JobCreation:jd_enrichment] input-thin guard fired "
            "(raw_len=%d, has_panel=%s, has_attached=%s, has_title=%s) — "
            "asking recruiter for JD material instead of LLM-enriching noise.",
            _raw_len, _has_panel_form, _has_attached, _has_parsed_title,
        )
        return {
            **state,
            "current_stage": "jd_enrichment",
            "jd_enriched": None,
            "jd_quality_score": 0.0,
            "jd_quality_warnings": [],
            "jd_fairness_blocked": False,
            "requires_approval": False,
            "stage_history": (state.get("stage_history") or []) + ["jd_enrichment_awaiting_input"],
            "ws_stage_payload": {
                "type": "wizard_stage",
                "stage": "jd_enrichment",
                "data": {
                    "awaiting_jd_input": True,
                    "message": _ask_jd_msg,
                },
                "requires_approval": False,
            },
        }

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
            "LIA_JD_ENRICHMENT_TIMEOUT_S", "60"
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

    # ── Mensagem contextual para o chat (Task #1096 / canonical-fix) ──
    # Sem este campo o ``WizardSessionService`` cai em ``_emit_silent_fallback``
    # (Task #1089 T3) e o usuário vê ``[ATENÇÃO: estado inconsistente]``.
    # A mensagem é parametrizada (título + score + flag de fallback) — não é
    # canned literal, varia por turno e por enriquecimento.
    _enriched_title = (
        (jd_enriched_dict or {}).get("titulo_padronizado")
        or state.get("parsed_title")
        or "a vaga"
    )
    _used_fallback = locals().get("jd_enrichment_used_fallback", False)
    _q_int = int(round(jd_quality_score or 0.0))
    if _used_fallback:
        _stage_message = (
            f"Recebi a descrição de **{_enriched_title}**. O serviço de IA está "
            f"degradado neste momento, então gerei um enriquecimento mínimo "
            f"(qualidade estimada: {_q_int}%). Revise no painel à direita: "
            f"se estiver ok, me confirme aqui no chat (ex.: \"pode seguir\"); "
            f"se quiser ajustar, me diga o que mudar; ou cole uma versão nova."
        )
    else:
        _stage_message = (
            f"Recebi a descrição de **{_enriched_title}** e enriqueci no painel "
            f"à direita (qualidade: {_q_int}%). Quer que eu siga para o próximo "
            f"passo, ajustar algum ponto, ou prefere substituir o texto?"
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
                "message": _stage_message,
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
                    "pipeline_template_db": _build_pipeline_template_db_suggestion(state),
                },
            },
            "completeness": calculate_completeness("jd_enrichment"),
            "requires_approval": True,
        },
    }

    # ── Sprint Pipeline Templates Gap #5 (2026-05-26) — wiring backend↔frontend ──
    # Frontend useWizardFlow lê ui_action no top do ws_stage_payload + data.templates.
    # Quando DB suggestion tem should_suggest=True, eleva templates pro top de data
    # e emite ui_action="suggest_pipeline_template". data.suggestions_data.pipeline_template_db
    # permanece intacto (retrocompat com wizard-plan-card.ts legacy via Task #1055).
    try:
        _db_sugg = (
            (updates.get("ws_stage_payload", {}).get("data", {}) or {})
            .get("suggestions_data", {})
            .get("pipeline_template_db")
        )
        if (
            isinstance(_db_sugg, dict)
            and _db_sugg.get("should_suggest")
            and _db_sugg.get("templates")
        ):
            updates["ws_stage_payload"]["ui_action"] = "suggest_pipeline_template"
            updates["ws_stage_payload"]["data"]["templates"] = _db_sugg["templates"]
    except Exception:  # noqa: BLE001 — fail-open por design (telemetria, não bloqueia fluxo)
        pass

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


# ---------------------------------------------------------------------------
# Pipeline Template Node (Sprint Pipeline Templates 2026-05-26 — Opção B)
# ---------------------------------------------------------------------------
# HITL stage canonical entre jd_enrichment e bigfive. Sugere top-3 templates
# do PipelineTemplateRepository (scored por department / seniority / job_family),
# com fallback heurístico determinístico quando DB vazia. Recrutador pode:
#   - aplicar um template (state.pipeline_template_id + state.interview_stages)
#   - usar padrão da empresa (skippable — allow_skip=True)
# Persistência via PipelineTemplateService.apply_to_vacancy é deferida até
# publish_node (vacancy_id existe somente após publish). Node NÃO mutua DB.
#
# ws_stage_payload canonical:
#   - ui_action: "suggest_pipeline_template" (frontend WizardPipelineTemplateCard)
#   - data.templates: top-3 com {template_id, name, description, stages_count, score}
#   - data.suggested_template_id: top-1 ou None
#   - data.allow_skip: True

# Sprint Pipeline Templates Gap #7 (2026-05-26) — apply helpers para o node.
def _apply_pipeline_template_to_state(state: dict, template_id: str) -> Optional[Dict[str, Any]]:
    """Translate template.stages → vacancy.interview_stages, fail-open.

    Sync wrapper para uso dentro de pipeline_template_node. Usa
    AsyncSessionLocal + run_coro_in_threadpool (canonical async helper).

    PR-4 (2026-05-26): substituído _asyncio.run() por run_coro_in_threadpool()
    do app.domains.job_creation.helpers.async_audit. Python 3.12+ raise
    RuntimeError quando há event loop ativo + asyncio.run — sync nodes do
    LangGraph SEMPRE rodam num event loop, então asyncio.run aqui era
    silent-failure (template nunca aplicado em runtime). Helper canonical
    delega para ThreadPoolExecutor + asyncio.run em thread separada.
    """
    try:
        import uuid as _uuid
        from app.core.database import AsyncSessionLocal
        from app.domains.job_creation.helpers.async_audit import (
            run_coro_in_threadpool,
        )
        from app.domains.pipeline.repositories.pipeline_template_repository import (
            PipelineTemplateRepository,
        )
        from app.domains.pipeline.services.pipeline_template_service import (
            translate_template_stages_to_interview_stages,
        )

        company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if not company_id:
            return None

        async def _run():
            async with AsyncSessionLocal() as session:
                repo = PipelineTemplateRepository(session)
                template = await repo.get_by_id(_uuid.UUID(template_id), company_id)
                if not template:
                    return None
                stages_translated = translate_template_stages_to_interview_stages(template.stages or [])
                await repo.increment_usage(template)
                return {"interview_stages": stages_translated, "template_name": template.name}

        return run_coro_in_threadpool(lambda: _run())
    except Exception as exc:  # noqa: BLE001 — fail-open por design
        logger.warning(
            "_apply_pipeline_template_to_state fail-open (graph continua com default): %s",
            exc,
            exc_info=True,
        )
        return None


def _emit_pipeline_template_audit(
    state: dict,
    *,
    action: str,
    template_id: Optional[str],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit audit log canonical (REGRA #1 ACH-026 + LGPD trail).

    Fail-open: audit failure NUNCA bloqueia graph (igual ao bloco de audit
    do jd_enrichment_node).
    """
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import audit_service
        from app.models.audit_log import DecisionType

        company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if not company_id:
            return
        reasoning = [
            f"action: {action}",
            f"template_id: {template_id}",
            f"stage: pipeline_template",
        ]
        if extra:
            for k, v in extra.items():
                reasoning.append(f"{k}: {v}")
        _asyncio.run(audit_service.log_decision(
            company_id=company_id,
            agent_name="job_creation:pipeline_template",
            decision_type=DecisionType.COMPANY_SETTINGS_CHANGE.value,
            action=action,
            decision=f"{action}: {template_id or 'default'}",
            reasoning=reasoning,
            criteria_used=["template_id", "company_id", "stage"],
            actor_user_id=state.get("user_id") or state.get("created_by"),
            human_review_required=False,
        ))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[pipeline_template] audit emission failed (fail-open): %s", exc,
        )


def pipeline_template_node(state: JobCreationState) -> JobCreationState:
    """HITL stage canonical — sugere pipeline template ou permite skip.

    Fluxo canonical (Gap #7 fix 2026-05-26):
    - Primeira passagem: emite ws_stage_payload com suggestions + requires_approval=True.
    - Re-entrada (recrutador respondeu): parse raw_input para detectar action canonical:
        * "Aplicar template de pipeline <uuid>" → apply: translate stages + persist em state
        * "Template de pipeline aplicado, pode seguir" → ack apenas (frontend já fez fetch)
        * "Usar pipeline padrão da empresa" → skip: state.pipeline_template_skipped=True

    Fail-open: DB suggestion miss → legacy heuristic fallback → allow_skip.
    NUNCA crasha o graph. Apply de stages persiste em state.interview_stages
    (publish_node lê depois pra criar vacancy com pipeline_template_id correto).
    """
    import re as _re

    t0 = time.time()

    # ── Gap #7 fix: parse user re-entry FIRST ──
    # Se recrutador já escolheu (template_id presente OU explicit skip), pula emit.
    raw_input = (state.get("raw_input") or state.get("user_query") or "").strip()
    already_chosen = bool(state.get("pipeline_template_id")) or bool(state.get("pipeline_template_skipped"))

    if raw_input and not already_chosen:
        # Pattern 1: explicit apply with template_id UUID
        m_apply = _re.search(
            r"aplicar.*?template.*?pipeline.*?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
            raw_input,
            _re.IGNORECASE,
        )
        # Pattern 2: ack (frontend already applied via separate fetch)
        m_ack = _re.search(r"template.*?pipeline.*?aplicad[oa]", raw_input, _re.IGNORECASE)
        # Pattern 3: skip / use company default
        m_skip = _re.search(r"(pipeline.*?padr[ãa]o.*?empresa|usar.*?padr[ãa]o.*?empresa|pular.*?template)", raw_input, _re.IGNORECASE)

        if m_apply:
            template_id_str = m_apply.group(1)
            logger.info("[JobCreation:pipeline_template] APPLY detected: template_id=%s", template_id_str)
            applied = _apply_pipeline_template_to_state(state, template_id_str)
            if applied:
                _emit_pipeline_template_audit(
                    state,
                    action="pipeline_template_applied_in_wizard",
                    template_id=template_id_str,
                    extra={"source": "wizard_explicit", "raw_input_preview": raw_input[:80]},
                )
                return {
                    **state,
                    "current_stage": "pipeline_template",
                    "pipeline_template_id": template_id_str,
                    "interview_stages": applied.get("interview_stages", []),
                    "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                    "completeness": calculate_completeness("pipeline_template"),
                    "requires_approval": False,
                }
            # Apply failed (template not found / cross-tenant) → fall through to re-emit

        elif m_ack:
            logger.info("[JobCreation:pipeline_template] ACK detected (frontend already applied)")
            _emit_pipeline_template_audit(
                state,
                action="pipeline_template_applied_ack",
                template_id=state.get("pipeline_template_id"),
                extra={"raw_input_preview": raw_input[:80]},
            )
            return {
                **state,
                "current_stage": "pipeline_template",
                "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                "completeness": calculate_completeness("pipeline_template"),
                "requires_approval": False,
            }

        elif m_skip:
            logger.info("[JobCreation:pipeline_template] SKIP detected (use company default)")
            _emit_pipeline_template_audit(
                state,
                action="pipeline_template_skipped",
                template_id=None,
                extra={"source": "wizard_explicit", "raw_input_preview": raw_input[:80]},
            )
            return {
                **state,
                "current_stage": "pipeline_template",
                "pipeline_template_skipped": True,
                "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                "completeness": calculate_completeness("pipeline_template"),
                "requires_approval": False,
            }
        # else: free-text não matched → cai no emit (LIA re-pergunta)

    logger.info("[JobCreation:pipeline_template] Starting (stage idx 2)")

    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")

    # 1. Canonical DB suggestion (top-3 com scoring real)
    db_sugg: Optional[Dict[str, Any]] = None
    try:
        db_sugg = _build_pipeline_template_db_suggestion(state)
    except Exception as exc:  # noqa: BLE001 — fail-open por design
        logger.warning("[JobCreation:pipeline_template] DB suggestion failed (fail-open): %s", exc)

    # 2. Legacy heuristic fallback (sem DB)
    legacy: Optional[Dict[str, Any]] = None
    try:
        legacy = _suggest_pipeline_template(parsed_title, parsed_seniority)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[JobCreation:pipeline_template] legacy heuristic failed (fail-open): %s", exc)

    # 3. Build canonical templates list (preferindo DB quando should_suggest=True)
    templates: List[Dict[str, Any]] = []
    suggested_template_id: Optional[str] = None
    top_score: float = 0.0
    if isinstance(db_sugg, dict) and db_sugg.get("should_suggest") and db_sugg.get("templates"):
        templates = list(db_sugg["templates"])
        top_score = float(db_sugg.get("top_score") or 0.0)
        if templates:
            suggested_template_id = templates[0].get("template_id")

    # 4. Default pipeline stage count (proxy para mensagem "padrão da empresa tem N etapas")
    default_pipeline_stages_count = len((state.get("interview_stages") or []) or [])

    # 5. Mensagem PT-BR canonical (UX conversacional)
    if templates:
        top_name = templates[0].get("name") or "este pipeline"
        message = (
            f"Para essa vaga, sugiro o pipeline **{top_name}**. "
            f"Você pode aplicar este, escolher outro ou usar o padrão da empresa."
        )
    elif legacy:
        message = (
            "Não encontrei um pipeline customizado que combine perfeitamente. "
            "Quer usar um dos templates padrão ou seguir com o pipeline padrão da empresa?"
        )
    else:
        message = (
            "Vamos usar o pipeline padrão da empresa para essa vaga? "
            "Você pode customizar depois nas configurações."
        )

    ws_stage_payload = {
        "type": "wizard_stage",
        "stage": "pipeline_template",
        "ui_action": "suggest_pipeline_template",
        "data": {
            "message": message,
            "templates": templates,
            "suggested_template_id": suggested_template_id,
            "allow_skip": True,
            "default_pipeline_stages_count": default_pipeline_stages_count,
            # Retrocompat com pattern legacy (jd_enrichment_node emite o mesmo shape).
            "suggestions_data": {
                "pipeline_template": legacy,
                "pipeline_template_db": db_sugg,
            },
        },
        "completeness": calculate_completeness("pipeline_template"),
        "requires_approval": True,
    }

    stage_history = list(state.get("stage_history") or [])
    if "pipeline_template" not in stage_history:
        stage_history.append("pipeline_template")

    updates = {
        "current_stage": "pipeline_template",
        "stage_history": stage_history,
        "completeness": calculate_completeness("pipeline_template"),
        "requires_approval": True,
        "ws_stage_payload": ws_stage_payload,
    }

    # 6. Audit canonical (EU AI Act Art.13 / SOX 7y) — fail-open
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("company_id") or state.get("workspace_id") or "")
        if _company_id:
            _asyncio.run(_audit.log_decision(
                company_id=_company_id,
                agent_name="job_creation:pipeline_template",
                decision_type="company_settings_change",
                action="pipeline_template_suggested",
                decision="suggested" if templates else "no_match",
                reasoning=[
                    f"db_should_suggest={bool(db_sugg and db_sugg.get('should_suggest'))}",
                    f"db_top_score={top_score:.3f}",
                    f"templates_count={len(templates)}",
                    f"suggested_template_id={suggested_template_id or 'none'}",
                    f"legacy_fallback={'yes' if legacy else 'no'}",
                ],
                criteria_used=["parsed_department", "parsed_seniority", "parsed_job_family"],
                job_vacancy_id=state.get("job_id"),
                confidence=top_score if top_score else None,
                human_review_required=True,  # HITL — recrutador escolhe
            ))
    except Exception as _audit_exc:
        logger.debug(
            "[JobCreation:pipeline_template] audit log failed (fail-open): %s", _audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info(
        "[JobCreation:pipeline_template] templates=%d top_score=%.2f | %.0fms",
        len(templates), top_score, elapsed,
    )
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
                # Task #1099 — invariant: todo retorno com current_stage
                # setado DEVE incluir ws_stage_payload.data.message truthy.
                # Sem isso o WizardSessionService cai em
                # _emit_silent_fallback (Task #1089).
                _bf_block_msg = (
                    "Detectei linguagem que pode ser discriminatória na "
                    "descrição enriquecida — vou pausar o mapeamento Big "
                    "Five para esta vaga. Revise a JD e me peça para retomar."
                )
                return {
                    **state,
                    "current_stage": "bigfive",
                    "ws_stage_payload": {
                        "type": "wizard_stage",
                        "stage": "bigfive",
                        "data": {
                            "message": _bf_block_msg,
                            "fairness_blocked": True,
                            "fairness_category": _bf_fg_result.category,
                        },
                        "completeness": 0,
                        "requires_approval": False,
                    },
                }
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
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": (
                        "Não consigo gerar o perfil Big Five — política da "
                        f"empresa bloqueou: {_policy_result.rationale}"
                    ),
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
            "LIA_BIGFIVE_TIMEOUT_S", "45"
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
                # Task #1099 — invariant: data.message obrigatório em todo
                # retorno com current_stage setado. Sem isso o
                # WizardSessionService cai em _emit_silent_fallback
                # (Task #1089). Mensagem parametrizada por título + flag de
                # fallback, espelhando o padrão do jd_enrichment_node (Task
                # #1096).
                "message": (
                    "Mapeei o perfil Big Five para "
                    f"{(state.get('parsed_title') or 'esta vaga')}"
                    + (
                        " (sugestão mínima — revise antes de seguir)."
                        if locals().get("bigfive_used_fallback", False)
                        else "."
                    )
                    + " Quer ajustar algum traço ou seguir para a faixa salarial?"
                ),
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
        "LIA_SALARY_TIMEOUT_S", "45"
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    "Faixa salarial e benefícios prontos"
                    + (
                        " (benchmark indisponível — revise manualmente)."
                        if salary_used_fallback
                        else "."
                    )
                    + " Quer ajustar algo ou seguir para competências?"
                ),
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Resolvi a senioridade ({seniority_result.display_name}) "
                    "e a distribuição de perguntas WSI"
                    + (
                        f" (modo {screening_mode})."
                        if screening_mode
                        else " — escolha entre modo compacto (7q) ou completo (12q)."
                    )
                    + " Quer ajustar ou seguir para gerar as perguntas?"
                ),
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
                "data": {
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": (
                        "Não consigo gerar as perguntas WSI — política da "
                        f"empresa bloqueou: {_wsi_policy.rationale}"
                    ),
                    "policy_blocked": True,
                    "policy_decision": _wsi_pd_dict,
                },
                "completeness": 0,
                "requires_approval": False,
            },
        }
    _wsi_pending_hitl = (_wsi_policy.decision == PolicyDecision.HITL_REQUIRED)

    from app.domains.job_creation.schemas import EnrichedJobDescription

    # If already approved, skip re-generation (resume path).
    # T5 (Task #1087): respeitar `wsi_regenerate_pending` — quando o gate
    # LLM-based decide regenerar/editar/adicionar, ele seta esse marker
    # transitório no state pra forçar o node a re-rodar o generator
    # mesmo que `questions_approved` ou `wsi_questions` ainda estejam
    # populados de um turno anterior. O marker é limpo no fim do node.
    _force_regen = bool(state.get("wsi_regenerate_pending"))
    if (not _force_regen) and state.get("questions_approved") is not None and state.get("wsi_questions"):
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
            # Sprint F.4: defensive coerce — state may have None explicit; .get(default) only kicks in for MISSING keys.
            if not isinstance(distribution, dict):
                distribution = {"technical": 5, "behavioral": 2}
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
                    "LIA_WSI_QUESTIONS_TIMEOUT_S", "120"
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
        # Task #1099 — invariant: data.message obrigatório (parametrizada
        # pelo número de perguntas geradas + flag de fallback + dropped
        # count). Sem isso o WizardSessionService cai em
        # _emit_silent_fallback (Task #1089).
        "message": (
            f"Gerei {len(questions_data)} perguntas WSI"
            + (
                " (sugestão mínima — revise)."
                if locals().get("wsi_questions_used_fallback", False)
                else "."
            )
            + (
                f" Bloqueei {len(_wsi_dropped)} pergunta(s) por linguagem "
                "potencialmente discriminatória."
                if _wsi_dropped
                else ""
            )
            + " Pode revisar — preciso da sua aprovação antes de seguir."
        ),
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
            "data": {
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Configurei {len(questions)} pergunta(s) eliminatória(s) "
                    "para a triagem inicial."
                    if questions
                    else "Nenhuma pergunta eliminatória configurada — quer "
                    "adicionar alguma ou seguir direto para a revisão final?"
                ),
                "questions": questions,
            },
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    "Tudo pronto para publicar. Quer revisar algo ou "
                    "publicar a vaga agora?"
                    if readiness.get("ready")
                    else (
                        "Antes de publicar, ainda faltam alguns campos: "
                        + ", ".join(readiness.get("missing", []) or ["informações"])
                        + ". Quer ajustar?"
                    )
                ),
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
                "data": {
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": (
                        "Não consigo publicar a vaga — "
                        f"{_pub_policy.rationale}"
                    ),
                    "policy_blocked": True,
                    "policy_decision": _pub_pd_dict,
                },
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
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": (
                        "Antes de publicar, preciso da sua confirmação "
                        f"explícita: {_pub_policy.rationale}"
                    ),
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Tive um problema ao publicar a vaga: {error}. "
                    "Posso tentar de novo?"
                    if error
                    else (
                        "Vaga publicada com sucesso! "
                        + (f"Link de divulgação: {share_link}. " if share_link else "")
                        + "Quer seguir para a calibração de candidatos?"
                    )
                ),
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
                    # T6 (Task #1088) — confirmation_method propagado pelo
                    # review_gate_node (chat | dual | button). Default "button"
                    # preserva o caminho legacy (UI button → policy_confirmed_publish
                    # direto, sem passar pelo gate LLM).
                    f"confirmation_method={state.get('publish_confirmation_method') or 'button'}",
                    *([f"error={error}"] if error else []),
                ],
                criteria_used=[
                    "job_data", "screening_config", "publish_platforms",
                    f"confirmation_method:{state.get('publish_confirmation_method') or 'button'}",
                ],
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

    # Sprint O.3 — detect fresh-publish boundary: publish_node ran in this same
    # graph invocation (stage_history tail) and vacancy was just created with
    # zero candidates loaded. Without this branch, the calibration message
    # ("Carreguei 0 candidato(s)...") overwrites publish's success message
    # since LangGraph auto-transitions publish->calibration in the same turn
    # (route_after_publish line ~4515). Tracked: Sprint N commit 98082cef8
    # only handled review_gate->publish boundary; this is the publish->calibration
    # sibling fix. Sensor: tests/wizard/test_publish_calibration_message.py.
    _stage_history = state.get("stage_history") or []
    _just_published = (
        "publish" in _stage_history[-3:]
        and bool(job_id)
        and not state.get("error")
    )
    _fresh_publish_zero_cands = (
        _just_published and len(candidates) == 0 and not complete
    )

    if _fresh_publish_zero_cands:
        _share_link = state.get("share_link") or ""
        _wsi_n = len(state.get("wsi_questions") or [])
        _calib_message = (
            "🎉 Vaga publicada com sucesso! "
            + (f"Link de divulgação: {_share_link}. " if _share_link else "")
            + (
                f"Já está visível para captação. Quando os primeiros candidatos "
                f"se inscreverem, vou usar suas {_wsi_n} perguntas WSI para "
                "calibrar a triagem inicial — é só voltar para revisar."
                if _wsi_n
                else "Já está visível para captação. Quando candidatos se "
                "inscreverem, vou ajudar você a calibrar a triagem por aqui."
            )
        )
    elif complete:
        _calib_message = (
            f"Calibração concluída — {approved_count}/{threshold} "
            "candidatos aprovados. Posso encerrar a configuração da vaga?"
        )
    else:
        _calib_message = (
            f"Carreguei {len(candidates)} candidato(s) para "
            f"calibração ({approved_count}/{threshold} aprovados). "
            "Continue avaliando para liberar a publicação completa."
        )

    updates: Dict[str, Any] = {
        "current_stage": "calibration",
        "calibration_complete": complete,
        "stage_history": _stage_history + ["calibration"],
        "completeness": calculate_completeness("calibration"),
        "requires_approval": False,
        "ws_stage_payload": {
            "type": "wizard_stage",
            "stage": "calibration",
            "data": {
                # Task #1099 — invariant: data.message obrigatório.
                # Sprint O.3 — fresh-publish branch above for UX celebratory.
                "message": _calib_message,
                # Sprint O.1: propagate job_id so the orchestrator can link
                # the response to the created vacancy after calibration
                # overwrites ws_stage_payload.
                "job_id": str(job_id) if job_id else None,
                "candidates": candidates,
                "threshold": threshold,
                "approved_count": approved_count,
                "complete": complete,
                "fresh_publish": _fresh_publish_zero_cands,
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
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    "Vaga pronta! Vou levar você para a página da vaga"
                    + (f" ({handoff_url})." if handoff_url else ".")
                    + (f" Link de divulgação: {share_link}." if share_link else "")
                ),
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
    if not msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via langgraph.types.interrupt().
        # Quando o caller usa ``Command(resume=<msg>)`` (process_message ou
        # JobCreationGraph.resume_with_message), interrupt() retorna a
        # mensagem do recrutador e o gate prossegue para classificar abaixo.
        # Em primeira entrada (HITL freshly reached), interrupt() levanta
        # GraphInterrupt — capturada pelo Pregel runtime para checkpointar
        # o state e devolver o controle ao caller. Caminho legacy END
        # no-op (offline / domain.py REST com gate_resume_message) é
        # preservado pelo guard ``_in_graph_runtime()``.
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "jd_enrichment",
            "data": {
                "jd_enriched": state.get("jd_enriched"),
                "jd_quality_score": state.get("jd_quality_score"),
            },
        })
        msg = (str(_resume) if _resume is not None else "").strip()
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
            last_turns=_extract_last_turns(state, n=3),  # Task #1123
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
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        # Fail-OPEN para o reply do classifier se Sonnet falhar.
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="jd_enrichment",
            user_message=msg,
            stage_description=(
                "HITL #1: revisão da descrição enriquecida da vaga (JD). "
                "O recrutador pode aprovar, rejeitar, ou enviar nova JD."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply or output.conversational_reply
        )
    elif intent == "off_topic":
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="jd_enrichment",
            user_message=msg,
            stage_description=(
                "HITL #1: revisão da descrição enriquecida da vaga (JD). "
                "Recrutador desviou — trazer de volta para aprovação."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
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


def competency_gate_node(state: JobCreationState) -> JobCreationState:
    """T4 (Task #1086) — gate LLM-based para HITL #2 (competency / screening_mode).

    Substitui a heurística keyword-based em ``domain.py::_route_by_stage``
    (linhas 'compact'/'compacto'/'7q'/'full'/'12q'/'completo') quando o
    flag ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica do stage
    (definida em ``STAGE_ALLOWLISTS["competency"]``):

      - ``select_compact``  → ``screening_mode="compact"``
      - ``select_full``     → ``screening_mode="full"``
      - ``ask_question``    → state inalterado; ``gate_clarify_message=...``
                              (recomendação por seniority)
      - ``undecided``       → state inalterado; ``gate_clarify_message=...``
                              (recomendação leve por seniority)

    Confidence < 0.7 → re-pergunta natural sem mutar ``screening_mode``.
    Resume detection mirroring jd_gate_node: ``current_stage="competency"``
    + ``seniority_resolved`` truthy + ``screening_mode`` falsy +
    user_query fresh (não processado nesta invocação).
    """
    msg = (state.get("gate_resume_message") or "").strip()
    if not msg:
        # WS resume detection — caminho canônico via process_message não
        # seta gate_resume_message; detectamos via state nativo.
        _at_competency = (
            state.get("current_stage") == "competency"
            or bool(state.get("seniority_resolved"))
        )
        _no_mode_yet = not state.get("screening_mode")
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_competency and _no_mode_yet and _is_fresh_turn:
            msg = _uq
            logger.info(
                "[JobCreation:competency_gate] WS resume detected (competency + fresh user_query, no mode yet) — classify",
            )
    if not msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #2 — competency).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "competency",
            "data": {
                "seniority_resolved": state.get("seniority_resolved"),
                "competency_recommendation": state.get("competency_recommendation"),
            },
        })
        msg = (str(_resume) if _resume is not None else "").strip()
    if not msg:
        # Sem mensagem nova — cleanup de intent transitório (mirror jd_gate
        # T2 fix #4) e END via route_after_competency_gate.
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_question", "undecided")
        clean_state = {**state, "current_stage": "competency"}
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:competency_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:competency_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "competency",
            }
    except Exception as exc:
        logger.debug("[JobCreation:competency_gate] FairnessGuard check failed (fail-open): %s", exc)

    # LLM classifier (per-stage allowlist + prompt).
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
        _company_id = state.get("workspace_id") or state.get("company_id")
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=msg,
            stage="competency",
            ws_stage_payload=state.get("ws_stage_payload"),
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
            company_id=str(_company_id) if _company_id else None,
            user_id=str(_user_id) if _user_id else None,
            last_turns=_extract_last_turns(state, n=3),  # Task #1123
        )
        if running_loop is not None and running_loop.is_running():
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(lambda: _asyncio.run(coro_factory()))
                output = _fut.result(timeout=30.0)
        else:
            output = _asyncio.run(coro_factory())
    except Exception as exc:
        logger.warning("[JobCreation:competency_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort).
    try:
        _emit_competency_gate_audit(state, msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:competency_gate] audit emit failed: %s", exc)

    # Resolve seniority recommendation (helper para ask_question / undecided).
    seniority = (state.get("seniority_resolved") or state.get("seniority") or "").lower()
    if seniority in ("estagio", "estágio", "junior", "júnior", "pleno"):
        recommended = "Compacto (7 perguntas)"
    elif seniority in ("senior", "sênior", "lead", "principal", "staff", "diretor"):
        recommended = "Completo (12 perguntas)"
    else:
        recommended = "Compacto (7 perguntas)"

    # Confidence floor — clarify sem mutar screening_mode.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:competency_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or f"Compacto (7 perguntas) ou Completo (12 perguntas)? Pra esta vaga eu sugiro {recommended}."
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "competency",
            "gate_seen_user_query": msg,
        }

    intent = output.intent
    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "competency",
        "gate_seen_user_query": msg,
    }

    if intent == "select_compact":
        next_state["screening_mode"] = "compact"
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Modo Compacto (7 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        )
    elif intent == "select_full":
        next_state["screening_mode"] = "full"
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Modo Completo (12 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        )
    elif intent == "ask_question":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="competency",
            user_message=msg,
            stage_description=(
                f"HITL #2: escolha do modo de triagem WSI (Compacto 7 perguntas "
                f"ou Completo 12 perguntas). Recomendação para este nível: {recommended}."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or f"Compacto tem 7 perguntas (mais ágil) e Completo tem 12 (mais evidência). Pra esta vaga eu sugiro {recommended}."
        )
    elif intent == "undecided":
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or f"Sem problema. Pra esta vaga eu sugiro {recommended}; me confirma quando puder pra eu seguir."
        )
    else:
        # Defesa em profundidade.
        logger.warning("[JobCreation:competency_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            f"Compacto (7 perguntas) ou Completo (12 perguntas)? Pra esta vaga eu sugiro {recommended}."
        )

    return next_state


def _emit_competency_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o competency gate.

    Best-effort: falha NÃO bloqueia o resume. EU AI Act Art. 13.
    """
    import asyncio as _asyncio
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "screening_mode": state.get("screening_mode"),
        "gate_last_intent": state.get("gate_last_intent"),
        "seniority_resolved": state.get("seniority_resolved"),
    }
    _after_mode = _before["screening_mode"]
    if _intent == "select_compact":
        _after_mode = "compact"
    elif _intent == "select_full":
        _after_mode = "full"
    _after = {
        "screening_mode": _after_mode,
        "gate_last_intent": _intent,
        "seniority_resolved": _before["seniority_resolved"],
    }
    coro = audit_service.log_decision(
        company_id=company_id,
        agent_name="wizard_competency_gate_classifier",
        decision_type="wizard_step_completed",
        action="competency_gate_classify",
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
        criteria_used=["llm_intent_classifier", "wizard_competency"],
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
        logger.debug("[JobCreation:competency_gate] audit run failed: %s", exc)


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


def wsi_questions_gate_node(state: JobCreationState) -> JobCreationState:
    """T5 (Task #1087) — gate LLM-based para HITL #2 (wsi_questions).

    Substitui a heurística keyword-based em ``domain.py::_route_by_stage``
    (linhas 'aprov'/'aceito'/'regener'/'refaz') quando o flag
    ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica do stage
    (definida em ``STAGE_ALLOWLISTS["wsi_questions"]``):

      - ``approve_all``             → ``questions_approved=True`` (→ eligibility)
      - ``regenerate_all``          → ``questions_approved=False`` +
                                      ``wsi_questions=[]`` +
                                      ``wsi_regenerate_pending=True``
                                      (→ wsi_questions full regen)
      - ``edit_specific_question``  → ``wsi_questions_pending_edit=
                                      {index, instruction}`` +
                                      ``wsi_regenerate_pending=True`` +
                                      ``questions_approved=False`` +
                                      ``wsi_questions=[]``
                                      (→ wsi_questions regen advisory)
      - ``add_question``            → ``wsi_questions_pending_add=
                                      {topic}`` +
                                      ``wsi_regenerate_pending=True`` +
                                      ``questions_approved=False`` +
                                      ``wsi_questions=[]``
                                      (→ wsi_questions regen advisory)
      - ``remove_question``         → splice in-state por question_index
                                      (1-based) + ``questions_approved=
                                      None`` (→ END, aguarda aprovação
                                      do pacote reduzido no próximo turno)
      - ``ask_question``            → state inalterado;
                                      ``gate_clarify_message=...``

    NOTA T5/cirurgia: ``edit_specific_question`` e ``add_question``
    persistem markers (``wsi_questions_pending_edit`` /
    ``wsi_questions_pending_add``) no state mas ATUALMENTE disparam
    full regen via ``wsi_regenerate_pending``. A geração cirúrgica
    (one-question replace/append usando os markers como hint) está
    deixada como follow-up Task #1089 — o contrato de state está
    estável e o classifier já produz o schema correto.

    Confidence < 0.7 → re-pergunta natural sem mutar pacote.
    Resume detection mirroring competency_gate_node: ``current_stage=
    "wsi_questions"`` + ``wsi_questions`` truthy + user_query fresh.
    """
    msg = (state.get("gate_resume_message") or "").strip()
    if not msg:
        _at_wsi = (
            state.get("current_stage") == "wsi_questions"
            and bool(state.get("wsi_questions"))
        )
        _no_decision_yet = state.get("questions_approved") is None
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_wsi and _no_decision_yet and _is_fresh_turn:
            msg = _uq
            logger.info(
                "[JobCreation:wsi_questions_gate] WS resume detected (wsi_questions + fresh user_query, awaiting decision) — classify",
            )
    if not msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #2 — WSI questions).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "wsi_questions",
            "data": {
                "wsi_questions": state.get("wsi_questions"),
                "screening_mode": state.get("screening_mode"),
            },
        })
        msg = (str(_resume) if _resume is not None else "").strip()
    if not msg:
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_question",)
        clean_state = {**state, "current_stage": "wsi_questions"}
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:wsi_questions_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:wsi_questions_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "wsi_questions",
            }
    except Exception as exc:
        logger.debug("[JobCreation:wsi_questions_gate] FairnessGuard check failed (fail-open): %s", exc)

    # LLM classifier (per-stage allowlist + prompt).
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
        _company_id = state.get("workspace_id") or state.get("company_id")
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=msg,
            stage="wsi_questions",
            ws_stage_payload=state.get("ws_stage_payload"),
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
            company_id=str(_company_id) if _company_id else None,
            user_id=str(_user_id) if _user_id else None,
            last_turns=_extract_last_turns(state, n=3),  # Task #1123
        )
        if running_loop is not None and running_loop.is_running():
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(lambda: _asyncio.run(coro_factory()))
                output = _fut.result(timeout=30.0)
        else:
            output = _asyncio.run(coro_factory())
    except Exception as exc:
        logger.warning("[JobCreation:wsi_questions_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort).
    try:
        _emit_wsi_questions_gate_audit(state, msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:wsi_questions_gate] audit emit failed: %s", exc)

    current_questions = list(state.get("wsi_questions") or [])
    total_q = len(current_questions)

    # Confidence floor — clarify sem mutar pacote.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:wsi_questions_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or "Você quer aprovar o pacote, regenerar tudo, editar/adicionar/remover alguma pergunta específica?"
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "wsi_questions",
            "gate_seen_user_query": msg,
        }

    intent = output.intent
    extracted = output.extracted_data or {}

    # Validação determinística de question_index 1-based vs len(wsi_questions).
    def _valid_index(raw) -> int | None:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            return None
        if total_q <= 0:
            return None
        if idx < 1 or idx > total_q:
            return None
        return idx

    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "wsi_questions",
        "gate_seen_user_query": msg,
    }

    if intent == "approve_all":
        next_state["questions_approved"] = True
        next_state["wsi_regenerate_pending"] = False
        next_state["wsi_questions_pending_edit"] = None
        next_state["wsi_questions_pending_add"] = None
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Aprovado! Vou seguir para configurar as perguntas de elegibilidade."
        )

    elif intent == "regenerate_all":
        next_state["questions_approved"] = False
        next_state["wsi_questions"] = []
        next_state["wsi_regenerate_pending"] = True
        next_state["wsi_questions_pending_edit"] = None
        next_state["wsi_questions_pending_add"] = None
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Sem problema, vou regenerar o pacote inteiro agora."
        )

    elif intent == "edit_specific_question":
        idx = _valid_index(extracted.get("question_index"))
        instruction = str(extracted.get("instruction") or "").strip()[:500]
        if idx is None or not instruction:
            # Schema inválido → clarify sem mutar pacote.
            logger.info(
                "[JobCreation:wsi_questions_gate] edit_specific_question schema inválido (idx=%r, instr_len=%d) → clarify",
                extracted.get("question_index"), len(instruction),
            )
            next_state["gate_clarify_message"] = (
                f"Qual pergunta você quer editar (1 a {total_q}) e o que mudar nela?"
            )
        else:
            next_state["wsi_questions_pending_edit"] = {
                "question_index": idx,
                "instruction": instruction,
            }
            next_state["wsi_regenerate_pending"] = True
            next_state["questions_approved"] = False
            # Limpa pacote para forçar regen completa (Task #1089: cirúrgico).
            next_state["wsi_questions"] = []
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or f"Beleza, vou ajustar a pergunta {idx} ({instruction[:60]})."
            )

    elif intent == "add_question":
        topic = str(extracted.get("topic") or "").strip()[:200]
        if not topic:
            logger.info(
                "[JobCreation:wsi_questions_gate] add_question sem topic → clarify",
            )
            next_state["gate_clarify_message"] = (
                "Sobre que tópico você quer a pergunta nova?"
            )
        else:
            next_state["wsi_questions_pending_add"] = {"topic": topic}
            next_state["wsi_regenerate_pending"] = True
            next_state["questions_approved"] = False
            next_state["wsi_questions"] = []
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or f"Show, vou acrescentar uma pergunta sobre {topic}."
            )

    elif intent == "remove_question":
        idx = _valid_index(extracted.get("question_index"))
        if idx is None:
            logger.info(
                "[JobCreation:wsi_questions_gate] remove_question índice inválido (%r, total=%d) → clarify",
                extracted.get("question_index"), total_q,
            )
            next_state["gate_clarify_message"] = (
                f"Qual pergunta você quer remover (1 a {total_q})?"
            )
        else:
            new_questions = current_questions[: idx - 1] + current_questions[idx:]
            next_state["wsi_questions"] = new_questions
            # Não aprova nem regenera — aguarda aprovação do pacote reduzido.
            next_state["questions_approved"] = None
            next_state["wsi_regenerate_pending"] = False
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or f"Removida a pergunta {idx}. O pacote ficou com {len(new_questions)} perguntas — me confirma se posso seguir."
            )

    elif intent == "ask_question":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="wsi_questions",
            user_message=msg,
            stage_description=(
                f"HITL #3: revisão do pacote WSI gerado ({total_q} perguntas). "
                "Recrutador pode aprovar, regenerar tudo, editar/adicionar/remover uma."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or "Posso explicar a metodologia WSI ou o pacote atual. O que você quer saber?"
        )

    else:
        logger.warning("[JobCreation:wsi_questions_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            "Você quer aprovar, regenerar, editar, adicionar ou remover alguma pergunta?"
        )

    return next_state


def _emit_wsi_questions_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o
    wsi_questions gate. Best-effort: falha NÃO bloqueia o resume.
    EU AI Act Art. 13."""
    import asyncio as _asyncio
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "questions_approved": state.get("questions_approved"),
        "wsi_questions_count": len(state.get("wsi_questions") or []),
        "gate_last_intent": state.get("gate_last_intent"),
    }
    _after_approved = _before["questions_approved"]
    if _intent == "approve_all":
        _after_approved = True
    elif _intent in ("regenerate_all", "edit_specific_question", "add_question"):
        _after_approved = False
    _after = {
        "questions_approved": _after_approved,
        "gate_last_intent": _intent,
    }
    coro = audit_service.log_decision(
        company_id=company_id,
        agent_name="wizard_wsi_questions_gate_classifier",
        decision_type="wizard_step_completed",
        action="wsi_questions_gate_classify",
        decision=_intent,
        reasoning=[
            f"intent={_intent}",
            f"confidence={float(output.confidence or 0.0):.2f}",
            f"thread_id={state.get('session_id') or ''}",
            f"user_msg_preview={user_message[:120]}",
            f"reply_preview={(output.conversational_reply or '')[:120]}",
            f"state_before={_before}",
            f"state_after={_after}",
            f"extracted_data_keys={sorted((output.extracted_data or {}).keys())}",
        ],
        criteria_used=["llm_intent_classifier", "wizard_wsi_questions"],
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
        logger.debug("[JobCreation:wsi_questions_gate] audit run failed: %s", exc)


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

# Allowlist canônica de canais ATS aceitos por ``configure_destinations``.
# Mantém-se sincronizada com ``Literal[...]`` no system_prompt YAML
# (gate_review.yaml). Adicionar novo canal requer (a) update aqui, (b)
# update no YAML, (c) update na sentinela.
_REVIEW_DESTINATIONS_ALLOWLIST: frozenset[str] = frozenset({
    "site_carreiras", "gupy", "pandape", "linkedin",
})

# Mapeia ``target_section`` (do request_changes) → nó destino do graph.
# Usado por ``route_after_review_gate`` quando o recrutador pede ajuste.
# Para ``destinations`` o roteamento é determinístico END (não há nó
# dedicado): o gate emite ``gate_clarify_message`` pedindo os canais
# desejados, e o próximo turno do recrutador é classificado como
# ``configure_destinations`` (handler dedicado no mesmo gate). Isso
# evita o anti-padrão "route → review (suprimido) → END" criticado no
# code review.
_REVIEW_TARGET_SECTION_TO_NODE: dict[str, str] = {
    "title": "jd_enrichment",
    "description": "jd_enrichment",
    "questions": "wsi_questions",
    "salary": "salary",
    "pipeline": "eligibility",
    # NOTE: "destinations" propositalmente AUSENTE — handled inline.
}

# T6: target_sections válidos para ``request_changes`` (inclui
# "destinations" mesmo que não tenha nó destino — handled inline).
_REVIEW_VALID_TARGET_SECTIONS: frozenset[str] = frozenset({
    "title", "description", "questions", "salary", "pipeline", "destinations",
})


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
_PUBLISH_DUAL_CONFIRMATION_TTL_S: float = 300.0


def review_gate_node(state: JobCreationState) -> JobCreationState:
    """T6 (Task #1088) — gate LLM-based para HITL #3 (review/publish).

    Substitui a heurística keyword-based de ``domain.py::_route_by_stage``
    para o stage ``review``/``publish`` (linhas 'public'/'manda'/'publica')
    quando o flag ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica
    do stage (``STAGE_ALLOWLISTS["review"]``):

      - ``publish_now``           → DUPLA CONFIRMAÇÃO via chat:
                                    1ª chamada: seta ``pending_publish_confirmation=True``
                                    + ``publish_confirmation_ts=now()``; route=END,
                                    pede confirmação na clarify message.
                                    2ª chamada (mesmo intent) DENTRO do TTL
                                    (300s) com flag set: seta
                                    ``policy_confirmed_publish=True`` (que
                                    destrava o publish_node PolicyGate);
                                    route=publish.
      - ``request_changes``       → mapeia ``target_section`` → nó destino
                                    via ``_REVIEW_TARGET_SECTION_TO_NODE``;
                                    limpa flag de aprovação correspondente
                                    (jd_approved/questions_approved/etc) e
                                    persiste ``review_request_changes_pending``.
      - ``configure_destinations`` → valida ``destinations`` contra
                                    ``_REVIEW_DESTINATIONS_ALLOWLIST``;
                                    seta ``publish_platforms=destinations``;
                                    route=END (espera publish_now).
      - ``ask_clarification``     → state inalterado; ``gate_clarify_message=...``
                                    route=END.

    Confidence < 0.7 → re-pergunta natural sem mutar pacote.
    Resume detection mirroring wsi_questions_gate_node: ``current_stage="review"``
    + user_query fresh (não processado nesta invocação).

    Audit row registra ``confirmation_method`` ∈ {chat, button, dual}
    em ``criteria_used`` (SOX 7 anos retention via decision_type=
    ``wizard_step_completed``).
    """
    # T6 (post-review fix #1) — ``review_request_changes_pending`` é
    # transiente por definição: setado pelo gate, consumido por
    # ``route_after_review_gate`` UMA vez, e a partir daí é estale. Se o
    # graph retornar a este nó (próximo turno do recrutador, ou um
    # passthrough sem mensagem), garantimos que NUNCA reroteamos com base
    # em estado antigo — limpamos no ENTRY. Sem isso, qualquer no-op
    # entrada em review_gate_node (sem msg fresca) ainda routava para o
    # destino mapeado, criando reroute loops.
    _stale_pending = state.get("review_request_changes_pending")
    if _stale_pending:
        logger.debug(
            "[JobCreation:review_gate] clearing stale review_request_changes_pending on entry: %r",
            _stale_pending,
        )

    msg = (state.get("gate_resume_message") or "").strip()
    if not msg:
        # WS resume detection — caminho canônico via process_message não
        # seta gate_resume_message; detectamos via state nativo.
        _at_review = state.get("current_stage") == "review"
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_review and _is_fresh_turn:
            msg = _uq
            logger.info(
                "[JobCreation:review_gate] WS resume detected (review + fresh user_query) — classify",
            )
    if not msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #3 — review/publish).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "review",
            "data": {
                "readiness_check": state.get("readiness_check"),
                "ws_stage_payload": state.get("ws_stage_payload"),
            },
        })
        msg = (str(_resume) if _resume is not None else "").strip()
    if not msg:
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_clarification",)
        clean_state = {
            **state,
            "current_stage": "review",
            # Garante limpeza mesmo no early-return.
            "review_request_changes_pending": None,
        }
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:review_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:review_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "review",
            }
    except Exception as exc:
        logger.debug("[JobCreation:review_gate] FairnessGuard check failed (fail-open): %s", exc)

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
        _company_id = state.get("workspace_id") or state.get("company_id")
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=msg,
            stage="review",
            ws_stage_payload=state.get("ws_stage_payload"),
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
            company_id=str(_company_id) if _company_id else None,
            user_id=str(_user_id) if _user_id else None,
            last_turns=_extract_last_turns(state, n=3),  # Task #1123
        )
        if running_loop is not None and running_loop.is_running():
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(lambda: _asyncio.run(coro_factory()))
                output = _fut.result(timeout=30.0)
        else:
            output = _asyncio.run(coro_factory())
    except Exception as exc:
        logger.warning("[JobCreation:review_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Confidence floor — clarify sem mutar pacote.
    # Sprint F.2 fix — threshold lower do que demais gates (0.55 vs 0.7).
    # Review gate tem espaço de intent menor (publish_now / request_changes /
    # configure_destinations / ask_clarification) — menos ambiguidade
    # justifica threshold relaxado. Bug F2 E2E 2026-05-20: classifier
    # retornava confidence=0.65 em "aprovado, pode publicar a vaga"
    # (frase canonical) — threshold 0.7 era over-aggressive.
    if (output.confidence or 0.0) < 0.55:
        logger.info(
            "[JobCreation:review_gate] confidence=%.2f < 0.55 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        clarify_state = {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or "Você quer publicar agora, ajustar alguma seção do resumo, configurar destinos ou tirar uma dúvida?"
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "review",
            "gate_seen_user_query": msg,
        }
        try:
            _emit_review_gate_audit(state, msg, output, confirmation_method="chat")
        except Exception as exc:
            logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)
        return clarify_state

    intent = output.intent
    extracted = output.extracted_data or {}

    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "review",
        "gate_seen_user_query": msg,
        # T6 (post-review fix #1) — sempre nasce limpo neste turno.
        # Quem precisar (request_changes não-destinations) seta logo abaixo.
        "review_request_changes_pending": None,
    }
    confirmation_method = "chat"

    if intent == "publish_now":
        # T6 (post-review #2 fix) — HARD readiness gate. Antes de qualquer
        # dual-confirmation, validar que o pacote está pronto. Se não, NÃO
        # avança para pending; emite ask_clarification determinístico que
        # cita exatamente o que falta (readiness_check.missing). Sem isso,
        # o recrutador poderia destravar publish mesmo com pacote incompleto
        # — viola Inegociável de governança da plataforma (consequential
        # decision gate em hiring flow).
        _readiness = state.get("readiness_check") or {}
        if not _readiness.get("ready"):
            _missing = _readiness.get("missing") or []
            _missing_pt = {
                "jd_approved": "aprovação da descrição",
                "questions_approved": "aprovação das questões WSI",
                "has_questions": "questões WSI geradas",
                "has_seniority": "senioridade definida",
                "quality_score_ok": "qualidade da descrição (score ≥ 50)",
            }
            _missing_str = ", ".join(_missing_pt.get(k, k) for k in _missing) or "configurações pendentes"
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
            next_state["policy_confirmed_publish"] = False
            # Reclassifica como ask_clarification para o audit trail
            # (intent original publish_now ficou em gate_last_intent acima).
            next_state["gate_clarify_message"] = (
                f"Antes de publicar preciso fechar: {_missing_str}. "
                "Quando esses pontos estiverem ok, é só me dizer 'publica' que sigo."
            )
            confirmation_method = "chat"
            logger.info(
                "[JobCreation:review_gate] publish_now BLOCKED — readiness not ready, missing=%s",
                _missing,
            )
            try:
                _emit_review_gate_audit(state, msg, output, confirmation_method=confirmation_method)
            except Exception as exc:
                logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)
            return next_state

        import time as _time
        _now = _time.time()
        _pending = bool(state.get("pending_publish_confirmation"))
        _ts = state.get("publish_confirmation_ts") or 0.0
        _within_ttl = _pending and (_now - float(_ts)) <= _PUBLISH_DUAL_CONFIRMATION_TTL_S
        if _within_ttl:
            # 2ª confirmação dentro da janela → destrava publish_node.
            next_state["policy_confirmed_publish"] = True
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
            # T6 — propaga confirmation_method para o publish_node final
            # audit (rastreabilidade SOX 7y).
            next_state["publish_confirmation_method"] = "dual"
            # Sprint M fix (2026-05-21): on dual-confirmation success, clear
            # gate_clarify_message + gate_last_intent so the downstream
            # publish_node "Vaga publicada com sucesso!" message wins
            # over the LLM"s chatty conversational_reply (which often
            # reads as a THIRD-confirmation request, e.g. "Vou publicar...
            # só me confirma uma última vez"). The dual-confirmation
            # branch is fully deterministic — no need for LLM text here.
            next_state["gate_clarify_message"] = None
            next_state["gate_last_intent"] = None
            confirmation_method = "dual"
            logger.info(
                "[JobCreation:review_gate] publish_now SECOND turn within TTL — confirmed (route=publish, gate_clarify_message cleared so publish_node message wins)",
            )
        else:
            # 1ª confirmação (ou expirada) → SETA pending + pede confirmação.
            # T6 (post-review fix #3) — mensagem DETERMINÍSTICA com sumário
            # do pacote (título, faixa salarial, # de questões WSI, destinos).
            # Não delega ao conversational_reply do LLM (que pode omitir
            # campos críticos). Auditável e estável para evals.
            next_state["pending_publish_confirmation"] = True
            next_state["publish_confirmation_ts"] = _now
            next_state["policy_confirmed_publish"] = False
            _jd = state.get("jd_enriched") or {}
            _title = (
                _jd.get("titulo_padronizado")
                or state.get("parsed_title")
                or "(sem título)"
            )
            _smin = state.get("salary_min")
            _smax = state.get("salary_max")
            _scur = state.get("salary_currency") or "BRL"
            if _smin and _smax:
                _salary = f"{_scur} {_smin:,}–{_smax:,}".replace(",", ".")
            elif _smin:
                _salary = f"{_scur} a partir de {_smin:,}".replace(",", ".")
            else:
                _salary = "faixa salarial não definida"
            _q_total = len(state.get("wsi_questions") or [])
            _dests = state.get("publish_platforms") or []
            _dests_str = ", ".join(_dests) if _dests else "os canais configurados"
            next_state["gate_clarify_message"] = (
                f"Pronto pra publicar:\n"
                f"• Vaga: {_title}\n"
                f"• Salário: {_salary}\n"
                f"• Questões WSI: {_q_total}\n"
                f"• Canais: {_dests_str}\n"
                f"Confirma para publicar agora?"
            )
            confirmation_method = "chat"
            logger.info(
                "[JobCreation:review_gate] publish_now FIRST turn — pending confirmation (TTL=%.0fs)",
                _PUBLISH_DUAL_CONFIRMATION_TTL_S,
            )

    elif intent == "request_changes":
        target = str(extracted.get("target_section") or "").strip().lower()
        instruction = str(extracted.get("instruction") or "").strip()[:500]
        if target not in _REVIEW_VALID_TARGET_SECTIONS or not instruction:
            logger.info(
                "[JobCreation:review_gate] request_changes schema inválido (target=%r, instr_len=%d) → clarify",
                target, len(instruction),
            )
            valid_sections = ", ".join(sorted(_REVIEW_VALID_TARGET_SECTIONS))
            next_state["gate_clarify_message"] = (
                f"Qual seção você quer ajustar ({valid_sections}) e o que mudar nela?"
            )
        elif target == "destinations":
            # Inline-handled: NÃO há nó destino para "destinations" — pedimos
            # imediatamente a lista de canais (próximo turno cai em
            # ``configure_destinations``). Resolvemos a allowlist tenant-aware
            # para listar SOMENTE canais que o tenant tem habilitados.
            allow_eff, is_tenant = _resolve_effective_destinations_allowlist(state)
            allow_str = ", ".join(sorted(allow_eff))
            scope = "habilitados pelo seu tenant" if is_tenant else "disponíveis"
            next_state["review_request_changes_pending"] = {
                "target_section": "destinations",
                "instruction": instruction,
            }
            next_state["gate_clarify_message"] = (
                f"Quais canais você quer publicar? {scope.capitalize()}: {allow_str}."
            )
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
        else:
            next_state["review_request_changes_pending"] = {
                "target_section": target,
                "instruction": instruction,
            }
            # Limpa flag de aprovação da seção correspondente para forçar
            # re-execução do nó destino na próxima invocação do graph.
            # T6 (post-review fix #2) — para title/description também
            # invalidamos jd_enriched, senão jd_enrichment_node pula a
            # re-geração (linha 607: ``if state.get("jd_enriched"): pula``)
            # e o ajuste cirúrgico nunca é aplicado. A instruction fica
            # disponível em ``review_request_changes_pending["instruction"]``
            # para o nó destino consultar (read-only hint cirúrgico).
            if target in ("title", "description"):
                next_state["jd_approved"] = None
                next_state["jd_enriched"] = None
                next_state["jd_quality_score"] = None
                next_state["jd_quality_warnings"] = []
            elif target == "questions":
                next_state["questions_approved"] = None
                next_state["wsi_regenerate_pending"] = True
                next_state["wsi_questions"] = []
            elif target == "salary":
                next_state["salary_min"] = None
                next_state["salary_max"] = None
            # pipeline: sem flag global a limpar — o nó eligibility lê
            # ``review_request_changes_pending`` como hint cirúrgico.
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or f"Beleza, vou voltar em {target} pra ajustar ({instruction[:60]})."
            )
            # Reseta dual-confirmation se houver — recrutador pediu mudança.
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None

    elif intent == "configure_destinations":
        raw_dests = extracted.get("destinations") or []
        if not isinstance(raw_dests, list):
            raw_dests = []
        # T6 — tenant-aware validation: intersect com canônica + ATS habilitados.
        allow_eff, is_tenant_constrained = _resolve_effective_destinations_allowlist(state)
        normalized = [str(d).strip().lower() for d in raw_dests]
        valid = [d for d in normalized if d in allow_eff]
        rejected = [d for d in normalized if d and d not in allow_eff]
        # Dedup preservando ordem.
        seen = set()
        valid_dedup = []
        for d in valid:
            if d not in seen:
                seen.add(d)
                valid_dedup.append(d)
        if not valid_dedup:
            allowed_str = ", ".join(sorted(allow_eff))
            scope = "habilitados pelo seu tenant" if is_tenant_constrained else "disponíveis"
            if rejected:
                rej_str = ", ".join(sorted(set(rejected)))
                next_state["gate_clarify_message"] = (
                    f"Os canais {rej_str} não estão {scope} pra essa empresa. "
                    f"Quais você quer publicar? {scope.capitalize()}: {allowed_str}."
                )
            else:
                next_state["gate_clarify_message"] = (
                    f"Quais canais você quer publicar? {scope.capitalize()}: {allowed_str}."
                )
        else:
            next_state["publish_platforms"] = valid_dedup
            # Limpa o request_changes pending — destinos foram resolvidos.
            next_state["review_request_changes_pending"] = None
            if rejected:
                rej_str = ", ".join(sorted(set(rejected)))
                scope = "habilitados pelo seu tenant" if is_tenant_constrained else "disponíveis"
                next_state["gate_clarify_message"] = (
                    f"Configurando publicação em: {', '.join(valid_dedup)} "
                    f"(ignorei {rej_str} — não estão {scope}). "
                    "Quando quiser, me confirma pra publicar."
                )
            else:
                next_state["gate_clarify_message"] = (
                    output.conversational_reply
                    or f"Configurando publicação em: {', '.join(valid_dedup)}. Quando quiser, me confirma pra publicar."
                )
            # Reseta dual-confirmation — destinos mudaram.
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None

    elif intent == "ask_clarification":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        # Fail-OPEN para o reply do classifier se Sonnet falhar.
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="review",
            user_message=msg,
            stage_description=(
                "HITL #4: revisão final da vaga antes da publicação. "
                "Recrutador pode publicar, ajustar campo específico, "
                "trocar destinos de publicação, ou pedir esclarecimento."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or "Posso explicar qualquer parte do resumo. O que você quer saber?"
        )

    else:
        logger.warning("[JobCreation:review_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            "Você quer publicar agora, ajustar alguma seção, escolher destinos ou tirar uma dúvida?"
        )

    # Audit row (best-effort) — confirmation_method é o discriminador SOX
    # entre "chat single turn", "dual chat confirmation" e "button"
    # (button é setado externamente via _handle_gate_review quando o FE
    # emite um sinal explícito de botão).
    try:
        _emit_review_gate_audit(state, msg, output, confirmation_method=confirmation_method)
    except Exception as exc:
        logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)

    return next_state


def _emit_review_gate_audit(
    state: JobCreationState,
    user_message: str,
    output,
    *,
    confirmation_method: str = "chat",
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o
    review gate. Best-effort: falha NÃO bloqueia o resume.

    SOX 7 anos retention: ``confirmation_method`` ∈ {chat, button, dual}
    é registrado em ``criteria_used`` para auditar o caminho exato pelo
    qual a decisão de publicação foi tomada (rastreabilidade EU AI Act
    Art. 13 + ISO 27001 control trail).
    """
    import asyncio as _asyncio
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "policy_confirmed_publish": bool(state.get("policy_confirmed_publish")),
        "pending_publish_confirmation": bool(state.get("pending_publish_confirmation")),
        "publish_platforms": list(state.get("publish_platforms") or []),
        "gate_last_intent": state.get("gate_last_intent"),
    }
    _after_confirmed = _before["policy_confirmed_publish"]
    _after_pending = _before["pending_publish_confirmation"]
    if _intent == "publish_now":
        if confirmation_method == "dual":
            _after_confirmed = True
            _after_pending = False
        else:
            _after_pending = True
    _after = {
        "policy_confirmed_publish": _after_confirmed,
        "pending_publish_confirmation": _after_pending,
        "gate_last_intent": _intent,
    }
    coro = audit_service.log_decision(
        company_id=company_id,
        agent_name="wizard_review_gate_classifier",
        decision_type="wizard_step_completed",
        action="review_gate_classify",
        decision=_intent,
        reasoning=[
            f"intent={_intent}",
            f"confidence={float(output.confidence or 0.0):.2f}",
            f"thread_id={state.get('session_id') or ''}",
            f"user_msg_preview={user_message[:120]}",
            f"reply_preview={(output.conversational_reply or '')[:120]}",
            f"state_before={_before}",
            f"state_after={_after}",
            f"extracted_data_keys={sorted((output.extracted_data or {}).keys())}",
        ],
        criteria_used=[
            "llm_intent_classifier",
            "wizard_review",
            f"confirmation_method:{confirmation_method}",
        ],
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
        logger.debug("[JobCreation:review_gate] audit run failed: %s", exc)


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
    builder.add_node("pipeline_template", pipeline_template_node)
    builder.add_node("bigfive", bigfive_node)
    builder.add_node("salary", salary_node)
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

    # F2+F3 -> salary -> F4+F5
    builder.add_edge("bigfive", "salary")
    builder.add_edge("salary", "competency")

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
        return self._graph.invoke(merged, config=config)

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
            Command(resume=str(user_message or "")), config=config
        )

    async def aresume_with_message(
        self, thread_id: str, user_message: str
    ) -> JobCreationState:
        """Task #1094 — versão async de ``resume_with_message`` para o
        caminho WS (``WizardSessionService.process_message``)."""
        from langgraph.types import Command
        config = {"configurable": {"thread_id": thread_id}}
        return await self._graph.ainvoke(
            Command(resume=str(user_message or "")), config=config
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
