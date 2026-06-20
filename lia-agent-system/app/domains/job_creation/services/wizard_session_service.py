"""
WizardSessionService — Sprint A.1 — Bug 6 (state persistence across WS turns).

harness-engineering guide computacional:
Encapsulates JobCreationGraph session lifecycle so conversation_messages
accumulate across WebSocket turns instead of being reset on every message.
Mirrors the `rail_a_hint_override.py` single-responsibility pattern.

Multi-tenant: workspace_id (= company_id as int) validated in every call.
LGPD: no PII stored beyond what JobCreationState already carries.
"""
from __future__ import annotations
# ADR-001-EXEMPT: fail-open mirror sync of Rails-owned `job_vacancies.wizard_stage`.
# Single fire-and-forget UPDATE inside a fail-open try/except. Source-of-truth
# for this column is Rails (mirror is best-effort); repository abstraction would
# obscure the fail-open semantics.

import asyncio
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# Captura determinística do email do gestor a partir do texto CRU (pré-masking
# LGPD). Mesmo pattern do pii_masking.EMAIL_PATTERN. Usado APENAS no servidor
# (wizard layer) — o valor NUNCA é enviado ao LLM (decisão Paulo 2026-05-31).
_MANAGER_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _extract_manager_email(raw_text: str) -> str | None:
    """Extrai o primeiro email válido do texto cru. None se ausente."""
    if not raw_text:
        return None
    m = _MANAGER_EMAIL_RE.search(raw_text)
    return m.group(0) if m else None


def _competency_tree_for_panel(state: dict) -> list[dict]:
    """Monta competency_tree (shape do CompetencyPanel FE) das competências do
    state. Usa confirmadas; se ainda não confirmadas, cai nas sugeridas (para o
    recrutador ver/ajustar). B3 fix — alinha ao nó canônico competency.py."""
    sugg = state.get("suggested_competencies") or {}
    tech = state.get("confirmed_technical_competencies") or sugg.get("technical") or []
    behav = state.get("confirmed_behavioral_competencies") or sugg.get("behavioral") or []
    tree: list[dict] = []
    for s_ in tech:
        if isinstance(s_, dict):
            name = s_.get("skill") or s_.get("name") or ""
            ctx = s_.get("contexto", "")
        else:
            name, ctx = str(s_), ""
        if name:
            tree.append({"skill": name, "contexto": ctx, "block": "technical"})
    for c_ in behav:
        if isinstance(c_, dict):
            name = c_.get("competencia") or c_.get("skill") or c_.get("name") or ""
            ctx = c_.get("contexto", "")
            trait = c_.get("trait_big_five", "") or c_.get("trait_ocean", "")
        else:
            name, ctx, trait = str(c_), "", ""
        if name:
            tree.append({"skill": name, "contexto": ctx, "block": "behavioral", "trait": trait})
    return tree


def _derive_wizard_stage(state: dict) -> str:
    """Deriva o stage canonical a partir do progresso do estado.

    O orquestrador é não-linear (não tem máquina de stages rígida), mas o
    painel lateral é stage-driven. Derivamos o stage do conteúdo do estado
    para o painel transicionar naturalmente (ficha → JD → publicado).
    """
    # Bug B fix (2026-06-20): read current_stage directly from state.
    # The PREVIOUS fix read ws_stage_payload.stage which is built AFTER
    # _derive_wizard_stage is called (circular dependency). First calibration
    # turn never showed candidates because no previous ws_stage_payload existed
    # (calibration_node had not run yet), so this block never matched.
    # Fix: _handle_calibration in domain.py sets current_stage="calibration"
    # explicitly BEFORE calling graph.resume(), making it a reliable signal.
    # calibration_complete guard preserved for post-advance_calibration handoff.
    #
    # Sensor: tests/contract/test_wizard_calibration_stage.py T-b (RED→GREEN)
    if (
        state.get("current_stage") == "calibration"
        and not state.get("calibration_complete")
    ):
        return "calibration"
    # Navegação explícita OU pós-publish → handoff (o FE auto-navega para a
    # página de vagas quando currentStage == "handoff").
    if state.get("_navigate_to_jobs") or state.get("job_id"):
        return "handoff"
    if state.get("wsi_questions"):
        return "wsi_questions"
    if state.get("jd_enriched"):
        return "jd_enrichment"
    # B3 fix (2026-05-31): stage "competency" — quando há competências
    # sugeridas/confirmadas (mas JD ainda não gerada), o painel mostra o
    # CompetencyPanel (add/remove). Antes o orquestrador pulava direto de
    # intake p/ jd_enrichment e o painel de competências nunca aparecia.
    if (
        state.get("confirmed_technical_competencies")
        or state.get("confirmed_behavioral_competencies")
        or state.get("suggested_competencies")
    ):
        return "competency"
    return "intake"

def _consume_panel_pref(state: dict) -> str | None:
    """Manus F1 — preferência de painel one-shot (tools open_panel/close_panel).

    Remove ``panel_pref`` do state (pop) e retorna o valor SE válido
    ("expanded" | "docked"). One-shot por design: o pop acontece ANTES de
    ``_persist_orchestrator_state`` (que usa ``update_state`` = MERGE no
    checkpoint), então a key nunca chega ao checkpoint — o FE recebe a
    preferência UMA vez no payload do ``wizard_stage`` e as etapas seguintes
    não re-forçam o modo (preserva a escolha manual do recrutador). Valor
    inválido é consumido e descartado (não emite).
    """
    pref = state.pop("panel_pref", None)
    return pref if pref in ("expanded", "docked") else None


# Keys carried forward from context into wizard state
_CONTEXT_CARRY_KEYS = ("right_panel_form", "attached_file_text", "tenant_context_snippet")

# ── Sprint F.2-v2 (2026-05-26) — Supervisor skip with content threshold ──
# Sprint F.2 (2026-05-20) introduziu skip binário do supervisor quando
# prior_stage em ACTIVE_WIZARD_STAGES. Protege respostas curtas a prompts
# HITL ("sim", "ok", "modo compacto", "aprovado") de serem misrotuladas
# pelo Haiku como create_new/meta_question/exit_wizard.
#
# Defeito de Sprint F.2: o skip era BINÁRIO — engolia também JD/briefing
# substancial colado durante stage ativa. Transcript Paulo 2026-05-26:
# user colou JD 1500 chars no turno 2, supervisor skipou, graph reentrou
# em loop de "preciso de mais contexto" sem nunca re-classificar.
#
# Fix v2: skip SOMENTE quando msg_len < 100 chars. Threshold empírico —
# JD real começa em ~120 chars (graph.py:842 documenta), prompt-answers
# canônicos ficam < 30. Margem de 100 dá folga inequívoca.
#
# Sensor: tests/wizard/test_supervisor_skip_long_content_threshold.py
_ACTIVE_WIZARD_STAGES = frozenset({
    "intake", "jd_enrichment", "pipeline_template",
    "bigfive", "salary", "competency",
    "wsi_questions", "eligibility", "review", "publish",
})

# JD real começa em ~120 chars (graph.py:842 documenta esse mesmo número).
# Prompt-answers HITL canônicos ("sim"/"ok"/"modo compacto, 7 perguntas")
# ficam < 30 chars. Threshold 100 dá folga sem ambiguidade.
_SUPERVISOR_SKIP_LONG_CONTENT_THRESHOLD = 100


def _compute_supervisor_skip(
    user_message: str | None, prior_stage: str | None,
) -> bool:
    """Decide if pre-graph supervisor classifier should be skipped.

    Contract:
      skip ⇔ (prior_stage in _ACTIVE_WIZARD_STAGES)
             AND (len(user_message.strip()) < _SUPERVISOR_SKIP_LONG_CONTENT_THRESHOLD)

    Skip protects short HITL prompt-answers from being re-classified
    (Sprint F.2). Long content (JD pastes, briefings) MUST re-classify
    so the graph can ingest new substance instead of swallowing it as
    a no-op HITL answer (Sprint F.2-v2).
    """
    if not isinstance(prior_stage, str) or prior_stage not in _ACTIVE_WIZARD_STAGES:
        return False
    msg_len = len((user_message or "").strip())
    return msg_len < _SUPERVISOR_SKIP_LONG_CONTENT_THRESHOLD



# Task #1089 (T3) — o dict canned por stage que mascarava estado inválido
# do graph (mensagem repetida 4× em HITL, bug original do screenshot) foi
# REMOVIDO. Sentinela arquitetural em
# tests/integration/agents/test_wizard_no_canned_fallback_t3.py veta a
# reintrodução. Path canônico de fallback agora é fail-loud:
# log error + Sentry + audit row (decision_type=wizard_fallback_invoked) +
# Prometheus counter (lia_wizard_silent_fallback_total) + tracker
# rolling-window + mensagem contextual gerada via LLM (Haiku) ou, em
# último caso, mensagem hard-prefixada (NÃO confundível com produto).
# Ver _emit_silent_fallback abaixo.

# Hard-prefix sinaliza estado inconsistente — UX vê isso e contata suporte
# em vez de seguir achando que é resposta válida da LIA.
_FALLBACK_HARD_PREFIX = "[ATENÇÃO: estado inconsistente — contate suporte]"

# Prometheus counter explícito (Task #1089 / code review #2 follow-up).
# Idempotente entre reimports — espelha pattern de tenant_aware_agent.py.
try:  # pragma: no cover — exercitado via integração
    from prometheus_client import Counter as _PromCounter  # type: ignore
    from prometheus_client import REGISTRY as _PROM_REGISTRY  # type: ignore

    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_wizard_silent_fallback_total"
    )
    if _existing is not None:
        _SILENT_FALLBACK_COUNTER = _existing
    else:
        _SILENT_FALLBACK_COUNTER = _PromCounter(
            "lia_wizard_silent_fallback_total",
            "Total de fail-loud fallbacks emitidos por WizardSessionService "
            "(Task #1089). Cada incremento indica estado anômalo do graph e "
            "deve disparar investigação.",
            labelnames=("stage", "company_id", "cause"),
        )
except Exception:  # pragma: no cover — fail-OPEN se prometheus indisponível
    _SILENT_FALLBACK_COUNTER = None


def _build_hard_fallback_message(stage: str | None) -> str:
    """Mensagem de último recurso (LLM indisponível). Prefixada para NUNCA
    ser confundida com mensagem de produto da LIA."""
    stage_label = stage or "wizard"
    return (
        f"{_FALLBACK_HARD_PREFIX} Não consegui interpretar o turno atual "
        f"(etapa: {stage_label}). Você quer (1) tentar novamente, "
        f"(2) revisar o que já registramos ou (3) pedir ajuda?"
    )


async def _generate_fallback_reply(
    *,
    stage: str | None,
    conversation_tail: list[dict] | None,
    tenant_snippet: str | None,
) -> str:
    """LLM-based contextual fallback. Cheap model (Haiku), 3s timeout, safe
    fallback to hard-prefixed message on any failure. Disabled in tests via
    LIA_WIZARD_FALLBACK_LLM_DISABLED=1."""
    if os.environ.get("LIA_WIZARD_FALLBACK_LLM_DISABLED", "").strip() in {"1", "true", "yes"}:
        return _build_hard_fallback_message(stage)
    try:
        from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

        from app.shared.llm_models import CANONICAL_HAIKU_MODEL
        from app.shared.providers.anthropic_client import get_chat_anthropic

        model_name = os.environ.get(
            "LIA_WIZARD_FALLBACK_MODEL", CANONICAL_HAIKU_MODEL,
        )
        timeout_s = float(os.environ.get("LIA_WIZARD_FALLBACK_TIMEOUT_S", "3"))
        # Task #1166: centralized seam — proxy ``base_url`` is enforced
        # by the bootstrap monkey-patch and the AST sentinel forbids
        # bare ``ChatAnthropic(...)`` inside ``app/domains/job_creation/``.
        llm = get_chat_anthropic(
            model=model_name, temperature=0, timeout=timeout_s, max_tokens=200,
        )

        tail_lines: list[str] = []
        for msg in (conversation_tail or [])[-4:]:
            role = (msg.get("role") or "").lower()
            content = str(msg.get("content") or "").strip()[:300]
            if content:
                tail_lines.append(f"- {role or 'msg'}: {content}")
        tail_text = "\n".join(tail_lines) or "(sem histórico)"
        sys = (
            "Você é a LIA, assistente de recrutamento. O wizard está em estado "
            f"inconsistente na etapa '{stage or 'wizard'}'. Gere UMA resposta curta "
            "(1-2 frases) em PT-BR, natural, perguntando o que o recrutador quer "
            "fazer (tentar de novo, revisar o registrado, ou pedir ajuda). NÃO "
            "invente conteúdo da vaga. NÃO repita prompts canned como 'preciso da "
            "sua aprovação'. NUNCA peça ao recrutador dados do tenant "
            "(company_id, id da empresa, nome da empresa, setor, plano, "
            "nome do consultor, nome do gestor, nome do recrutador) — esses "
            "vêm do contexto autenticado. Se faltar contexto, ofereça TENTAR "
            "DE NOVO ou REVISAR o registrado — NUNCA peça dados de identificação."
        )
        if tenant_snippet:
            sys += f"\n\nContexto do tenant: {tenant_snippet[:400]}"
        user = f"Últimos turnos:\n{tail_text}"
        result = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=sys), HumanMessage(content=user)]),
            timeout=timeout_s,
        )
        text = (getattr(result, "content", "") or "").strip()
        # R-008 harness guard (2026-05-19): reject responses that ask for
        # tenant data — regressão B1 anti-pattern (`wizard_no_tenant_leak.jsonl`).
        # Tenant comes from authenticated context, never from chat input.
        _tlow = text.lower() if text else ""
        _tenant_question_patterns = (
            "company_id", "id da empresa", "nome da empresa", "qual o setor",
            "qual a empresa", "qual sua empresa", "qual seu plano",
            "nome do consultor", "nome do gestor", "nome do recrutador",
            "qual o seu nome", "informe a empresa", "qual é a empresa",
        )
        _asks_tenant = any(p in _tlow for p in _tenant_question_patterns)
        if _asks_tenant:
            logger.warning(
                "[WizardSession] fallback LLM tentou perguntar tenant data (stage=%s) "
                "— bloqueado por harness guard e degradado para hard prefix. "
                "Resposta rejeitada (preview): %r",
                stage, text[:120],
            )
        if text and "preciso da sua aprovação" not in _tlow and not _asks_tenant:
            return text[:500]
    except Exception as exc:  # noqa: BLE001 — fallback é fail-open p/ hard prefix
        logger.warning(
            "[WizardSession] fallback LLM falhou (stage=%s): %s — usando hard prefix",
            stage, exc,
        )
    return _build_hard_fallback_message(stage)


def _emit_silent_fallback(
    *,
    stage: str | None,
    company_id: Any,
    session_id: str | None,
    thread_id: str | None,
    conversation_tail: list[dict] | None,
    cause: str,
) -> None:
    """Task #1089 (T3) — fail-LOUD path quando o graph não devolve mensagem.
    Combina:
      (a) ``logger.error`` com contexto completo;
      (b) Sentry ``capture_message`` (level=error) em prod;
      (c) audit row ``decision_type=wizard_fallback_invoked`` (EU AI Act);
      (d) Prometheus counter via :func:`WizardFallbackTracker.record_fallback`
          (label ``stage``, escopo session+tenant, threshold de alerta).
    Todas as 4 sub-chamadas são fail-open individualmente — telemetria nunca
    derruba o turno do recrutador."""
    cid = str(company_id) if company_id else None
    stage_label = stage or "unknown"

    # Sanitized bounded tail snapshot p/ diagnosticabilidade (R-013 / code
    # review #2): mantém apenas role + 200 chars do content dos últimos 3
    # turnos. PII leakage mitigado pelo truncate; log nunca explode.
    tail_snapshot: list[dict] = []
    for _msg in (conversation_tail or [])[-3:]:
        if not isinstance(_msg, dict):
            continue
        _role = str(_msg.get("role") or "")[:24]
        _content = str(_msg.get("content") or "").strip()[:200]
        if _content:
            tail_snapshot.append({"role": _role, "content_excerpt": _content})

    logger.error(
        "[WizardSession] silent fallback invoked stage=%s session=%s thread=%s "
        "company=%s cause=%s tail_len=%s tail=%s — graph returned no message",
        stage_label, session_id, thread_id, cid, cause,
        len(conversation_tail or []), tail_snapshot,
    )

    # (b) Sentry
    try:  # pragma: no cover — Sentry opcional em testes
        import sentry_sdk
        sentry_sdk.capture_message(
            f"Wizard silent fallback invoked (stage={stage_label})",
            level="error",
            extras={
                "stage": stage_label,
                "session_id": session_id,
                "thread_id": thread_id,
                "company_id": cid,
                "cause": cause,
            },
        )
    except Exception:
        pass

    # (c) Audit row
    try:
        from app.shared.compliance.audit_service import AuditService

        if cid:
            asyncio.create_task(AuditService().log_decision(  # AUDIT-NO-DEMO: wizard fallback telemetry (job creation flow, no candidate decision; LGPD Art.20 N/A)
                company_id=cid,
                agent_name=f"wizard_session:{stage_label}",
                decision_type="wizard_fallback_invoked",
                action=f"silent_fallback_{stage_label}",
                decision="fallback_emitted",
                reasoning=[
                    f"stage={stage_label}",
                    f"cause={cause}",
                    f"session_id={session_id or '∅'}",
                    f"thread_id={thread_id or '∅'}",
                ],
                criteria_used=[
                    "wizard_fallback",
                    f"stage:{stage_label}",
                    f"cause:{cause}",
                ],
                human_review_required=True,
            ))
    except Exception as audit_exc:  # noqa: BLE001
        logger.warning(
            "[WizardSession] fallback audit emission failed (fail-open): %s",
            audit_exc,
        )

    # (d) Prometheus counter explícito (Task #1089 / code review #2 follow-up)
    if _SILENT_FALLBACK_COUNTER is not None:
        try:
            _SILENT_FALLBACK_COUNTER.labels(
                stage=stage_label, company_id=(cid or "∅"), cause=cause,
            ).inc()
        except Exception as pm_exc:  # noqa: BLE001
            logger.warning(
                "[WizardSession] prometheus counter inc failed (fail-open): %s",
                pm_exc,
            )

    # (e) Fallback tracker (rolling-window threshold + alerta agregado)
    try:
        from app.shared.observability.wizard_fallback_tracker import (
            get_wizard_fallback_tracker,
        )
        get_wizard_fallback_tracker().record_fallback(
            session_id=session_id, company_id=cid,
            stage=stage_label, reason=f"silent_{cause}",
        )
    except Exception as tr_exc:  # noqa: BLE001
        logger.warning(
            "[WizardSession] fallback tracker emission failed (fail-open): %s",
            tr_exc,
        )


class WizardSessionService:
    """Manages JobCreationGraph invocation with per-session state accumulation.

    Fixes Bug 6: conversation_messages are now accumulated across WS turns.
    On Turn N the service pulls the checkpointed state from LangGraph,
    appends the new user message, and re-invokes — so the graph always has
    the full conversation history.

    Responsibilities
    ────────────────
    - derive_thread_id(): stable session → thread_id mapping
    - _get_prior_state(): non-raising checkpointer read
    - _build_state(): merge or fresh-start state builder
    - process_message(): main entry point for agent_chat_ws.py

    NOT responsible for: HITL approval routing (stays in agent_chat_ws.py),
    token streaming setup (caller provides on_token callback).
    """

    # ── Public helpers ────────────────────────────────────────────────────

    # Task #1080 canonical refactor: the legacy 4-priority ``derive_thread_id``
    # (msg.thread_id custom > company-prefixed > legacy) and the Redis
    # marker bookkeeping (``lia:wizard:active:*``) have been removed. The
    # canonical pure function lives in ``app.shared.sessions.thread_id``
    # and is the SINGLE source of truth across WS / SSE / REST orchestrator.
    # The two thin staticmethods below are delegating wrappers kept for
    # backward compatibility with existing call-sites and tests that mock
    # ``WizardSessionService.derive_thread_id`` / ``.is_session_active``.

    @staticmethod
    def derive_thread_id(
        msg_or_company_id: dict | str | None = None,
        session_id: str = "",
        company_id: str | None = None,
    ) -> str:
        """Delegating wrapper around the canonical
        ``app.shared.sessions.derive_thread_id``.

        Accepts both the legacy signature ``(msg, session_id, company_id=...)``
        AND the canonical ``(company_id, session_id)`` so existing call-sites
        and tests continue to type-check during the migration. The legacy
        ``msg["thread_id"]`` custom honor is INTENTIONALLY ignored — Task
        #1080 collapses the multiple sources of truth into one. New callers
        SHOULD import ``derive_thread_id`` directly from
        ``app.shared.sessions``.
        """
        from app.shared.sessions import derive_thread_id as _canonical

        # Legacy signature: first arg is a dict (the WS msg) — discard it.
        if isinstance(msg_or_company_id, dict):
            return _canonical(company_id, session_id)
        # Canonical signature: first arg is the company_id string (or None).
        return _canonical(msg_or_company_id, session_id)

    @classmethod
    async def is_session_active(
        cls,
        session_id: str,
        company_id: str | None = None,
    ) -> bool:
        """Delegating wrapper around the canonical
        ``app.shared.sessions.is_wizard_session_active``.

        Task #1080: the implementation now reads the LangGraph checkpoint
        for the SINGLE deterministic thread_id derived from
        ``(company_id, session_id)`` — no Redis marker, no candidate list,
        no client-supplied thread_id honor. A session counts as active iff
        a checkpoint exists AND ``current_stage != "completed"``.
        """
        from app.shared.sessions import is_wizard_session_active as _canonical

        return await _canonical(company_id, session_id)

    @staticmethod
    async def _get_prior_state(thread_id: str) -> dict:
        """Read checkpointed wizard state without raising.

        Returns empty dict on any error so callers always get a valid dict.
        Fail-open: a checkpointer miss means start fresh, never crash.

        Harness: computational sensor — reads LangGraph checkpoint directly.
        """
        try:
            from app.domains.job_creation.graph import get_job_creation_graph
            wiz_g = get_job_creation_graph()
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = await asyncio.to_thread(wiz_g._graph.get_state, config)
            if snapshot is not None and snapshot.values:
                state = dict(snapshot.values)
                logger.debug(
                    "[WizardSession] Prior state loaded thread=%s stage=%s conv_len=%d",
                    thread_id,
                    state.get("current_stage") or "?",
                    len(state.get("conversation_messages") or []),
                )
                return state
        except Exception as exc:
            # Audit-final (PLAN_FIX_wizard_memory_loss): promovido de DEBUG
            # para WARNING. O bug V1.d (Onda 1) ficou escondido porque
            # esse miss caia em logger.debug, invisivel em logs INFO+.
            # WARNING + structured fields permite alerta + observabilidade
            # do canary suite + canary detectar regressao silenciosa.
            logger.warning(
                "[WizardSession] Checkpointer read miss thread=%s "
                "reason=%s — falling back to fresh session. Sensor canonical: "
                "tests/integration/test_checkpointer_canonical.py.",
                thread_id, type(exc).__name__,
                extra={
                    "event": "wizard_checkpointer_read_miss",
                    "thread_id": thread_id,
                    "reason": type(exc).__name__,
                },
            )
        return {}

    @staticmethod
    def _build_state(
        *,
        thread_id: str,
        user_message: str,
        user_id: str | None,
        company_id: str | None,
        session_id: str,
        context: dict | None,
        prior_state: dict,
    ) -> dict:
        """Build the state dict for the next JobCreationGraph invocation.

        Bug 6 fix: when prior_state is non-empty (continuing session),
        appends the new message to conversation_messages and preserves
        all accumulated fields. Avoids the previous behaviour of
        overwriting the full history with a single-element list.

        Multi-tenancy: workspace_id always derived from company_id param,
        never trusted from prior_state (prevents tenant escalation via
        stale checkpoint data).

        T-B canonical (Task #970): valida ``company_id`` via
        ``CompanyId.parse`` (UUID v4 ou slug). Em strict-mode (default em
        prod/staging) qualquer entrada inválida — vazia, ``"default"``,
        formato errado — levanta ``InvalidCompanyIdError`` AQUI, antes de
        invocar o grafo. Em legacy/dev mode (``LIA_AGENT_TENANT_STRICT=false``)
        loga warning e degrada para ``workspace_id=0``/``company_id=""`` (compat).

        Para UUID v4 / slug não-numérico: ``workspace_id=0`` e ``company_id``
        normalizado é propagado como string — ``review_node`` faz fallback
        ``workspace_id or company_id`` para ``api_client.get_company_defaults``
        (vide replit.md → "UUID company_id tenants use workspace_id=0 with
        company_id string fallback in review_node").

        Para slug numérico legado: ``workspace_id`` recebe o int (compat com
        Rails ``workspace_id`` integer column).
        """
        from app.shared.agents.tenant_aware_agent import is_tenant_strict_mode
        from app.shared.exceptions.tenant_errors import (
            InvalidCompanyIdError,
            MissingTenantContextError,
        )
        from app.shared.value_objects.company_id import CompanyId

        ctx = context or {}
        resolution_source = "valid"
        try:
            # T-B contract: company_id ausente (None) é "tenant context faltando"
            # — semanticamente distinto de "company_id presente mas malformado".
            # Strict-mode levanta MissingTenantContextError nesse caso.
            if company_id is None:
                raise MissingTenantContextError(
                    details={
                        "tenant_source": "wizard_session_service",
                        "agent": "wizard_react_agent",
                        "company_id_raw": None,
                    },
                )
            parsed_cid = CompanyId.parse(company_id)
            normalized_cid = parsed_cid.as_str()
            # Legacy: slug puramente numérico mapeia 1:1 em workspace_id int
            safe_workspace_id = (
                int(normalized_cid) if normalized_cid.isdigit() else 0
            )
        except (InvalidCompanyIdError, MissingTenantContextError) as exc:
            if is_tenant_strict_mode():
                logger.error(
                    "[WizardSession] tenant context faltando/inválido em strict-mode "
                    "thread=%s raw=%r kind=%s — abortando (fail-closed T-B).",
                    thread_id, company_id, type(exc).__name__,
                )
                raise
            resolution_source = (
                "fail_open_missing"
                if isinstance(exc, MissingTenantContextError)
                else "fail_open_invalid"
            )
            logger.warning(
                "[WizardSession] tenant context faltando/inválido em legacy-mode "
                "thread=%s raw=%r kind=%s — degradando para workspace_id=0 "
                "(compat dev). Set LIA_AGENT_TENANT_STRICT=true para fail-closed.",
                thread_id, company_id, type(exc).__name__,
            )
            normalized_cid = ""
            safe_workspace_id = 0

        # Structured per-turn log: permite eval suite + canary detectarem
        # regressão silenciosa de tenant context no wizard.
        snippet_len = len(ctx.get("tenant_context_snippet") or "")
        logger.info(
            "wizard_tenant_context_resolved",
            extra={
                "event": "wizard_tenant_context_resolved",
                "thread_id": thread_id,
                "company_id": normalized_cid,
                "workspace_id": safe_workspace_id,
                "source": resolution_source,
                "snippet_len": snippet_len,
            },
        )

        if prior_state:
            # ── Continuing session ──────────────────────────────────────
            conv = list(prior_state.get("conversation_messages") or [])
            conv.append({"role": "user", "content": user_message})
            state: dict = {
                **prior_state,
                # Override tenant fields with authoritative values
                "workspace_id": safe_workspace_id,
                "company_id": normalized_cid,
                "user_id": str(user_id) if user_id else prior_state.get("user_id", ""),
                # Update query fields with new message.
                # T2 fix #10 (code review #8): NÃO sobrescrever raw_input
                # em sessões continuing. raw_input é a JD original (fonte
                # de jd_enrichment); sobrescrever a cada turno deixa
                # ``user_query == raw_input`` SEMPRE, neutralizando o
                # initial-pass guard do jd_gate_node (que usa
                # ``user_query != raw_input`` como sinal de "este turno é
                # resposta do recrutador, não a JD inicial"). Sem isso,
                # WS resume nunca dispara → bug original Task #1085 volta.
                # ``provide_new_content`` ainda atualiza raw_input
                # explicitamente dentro do gate (mid-invoke), preservando
                # a semântica de "nova JD trocou a anterior".
                "user_query": user_message,
                "conversation_messages": conv,
                # Reset approval flags — this is NOT an approval resume
                "hitl_approved": False,
            }
            # Carry any fresh context overrides
            for k in _CONTEXT_CARRY_KEYS:
                if ctx.get(k):
                    state[k] = ctx[k]
            # W0-A: recruiter from context (first turn) or prior_state (subsequent turns)
            if ctx.get("user_name"):
                state["parsed_recruiter_name"] = ctx["user_name"]
            if ctx.get("user_email"):
                state["parsed_recruiter_email"] = ctx["user_email"]
            # W0-B: extract jd_similar_reuse_id from right_panel_form if present
            _rpf = ctx.get("right_panel_form") or {}
            if _rpf.get("jd_similar_reuse_id"):
                state["jd_similar_reuse_id"] = str(_rpf["jd_similar_reuse_id"])
            logger.info(
                "[WizardSession] Continuing session thread=%s stage=%s conv_turns=%d",
                thread_id,
                state.get("current_stage") or "?",
                len(conv),
            )
            return state

        # ── Fresh session ─────────────────────────────────────────────────
        logger.info("[WizardSession] New session thread=%s source=wizard_new", thread_id)
        state = {
            "session_id": session_id,
            "user_id": str(user_id) if user_id else "",
            "workspace_id": safe_workspace_id,
            "company_id": normalized_cid,
            "auth_token": "",
            "language": "pt-BR",
            "current_stage": None,
            "stage_history": [],
            "user_query": user_message,
            "raw_input": user_message,
            "conversation_messages": [
                {"role": "user", "content": user_message},
            ],
        }
        for k in _CONTEXT_CARRY_KEYS:
            if ctx.get(k):
                state[k] = ctx[k]
        # W0-A: recruiter identity from session user (passed via context by SSE/REST endpoint)
        state["parsed_recruiter_name"] = ctx.get("user_name") or None
        state["parsed_recruiter_email"] = ctx.get("user_email") or None
        # W0-B: extract jd_similar_reuse_id from right_panel_form if present
        _rpf = ctx.get("right_panel_form") or {}
        if _rpf.get("jd_similar_reuse_id"):
            state["jd_similar_reuse_id"] = str(_rpf["jd_similar_reuse_id"])
        return state

    # ── Task #1127 (T1.1 + T2.1 + T2.2) — Supervisor pre-graph ────────
    #
    # Helper que (a) resolve contexto mínimo (tenant snippet, últimas
    # turns, draft-active flag); (b) chama o ``WizardSupervisorClassifier``
    # síncrono via ``asyncio.to_thread`` (não bloqueia event loop);
    # (c) decide short-circuit para ``meta_question`` / ``exit_wizard``;
    # (d) emite audit row + Prometheus counter (telemetria fail-OPEN).
    #
    # Fail-OPEN é INTENCIONAL: qualquer falha do supervisor (sem API key,
    # timeout, schema inválido, off-allowlist) devolve ``None`` → caller
    # cai 100% no fluxo legacy (preserva contrato vigente do graph).
    # ------------------------------------------------------------------

    @classmethod
    async def _run_supervisor(
        cls,
        *,
        user_message: str,
        prior_state: dict | None,
        context: dict | None,
        company_id: str | None,
        session_id: str,
        thread_id: str,
    ) -> dict | None:
        """Roda o supervisor pre-graph e devolve decisão de roteamento.

        Returns:
            ``None`` se supervisor desabilitado / fail-OPEN — caller cai
            no fluxo legacy (continue_current).

            ``{"intent": str, "short_circuit": False}`` se intent é
            ``continue_current`` / ``create_new`` / ``resume_draft`` /
            ``edit_published`` — caller segue para o graph (esses 3
            últimos terão handlers próprios nas Tasks #1128+).

            ``{"intent": "meta_question", "short_circuit": True,
            "message": str, "ws_stage_payload": dict}`` quando o
            supervisor classifica como meta — caller responde direto sem
            tocar o graph.

            ``{"intent": "exit_wizard", "short_circuit": True,
            "message": str, "ws_stage_payload": dict}`` quando o
            supervisor classifica como saída — caller emite despedida.
        """
        from app.domains.job_creation.services.wizard_supervisor_classifier import (
            get_wizard_supervisor_classifier,
            is_supervisor_enabled,
        )

        if not is_supervisor_enabled():
            return None

        # Contexto mínimo para o classifier — sem PII, snippets curtos.
        ctx = context or {}
        prior = prior_state or {}
        current_stage = prior.get("current_stage") if isinstance(prior, dict) else None

        # tenant snippet via helper canônico (NON-ReAct callsite — T-F).
        # Assinatura canônica: (ctx, *, agent_name, company_id_raw).
        # NÃO use kwargs `company_id=`/`context=` — TypeError silenciado
        # quebraria a postura de governança T-F.
        tenant_snippet = ""
        try:
            from app.shared.agents.tenant_aware_agent import (
                resolve_tenant_snippet_for_non_react,
            )
            tenant_snippet = (
                resolve_tenant_snippet_for_non_react(
                    ctx,
                    agent_name="wizard_supervisor",
                    company_id_raw=company_id,
                )
                or prior.get("tenant_context_snippet")
                or ""
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[WizardSupervisor] tenant snippet resolve failed: %s", exc,
            )

        # Últimas 3 turns (apenas conteúdo, sem role) — sinal pra LLM
        # detectar loop / mudança de intenção.
        last_turns: list[str] = []
        conv = prior.get("conversation_messages") if isinstance(prior, dict) else None
        if isinstance(conv, list):
            for m in conv[-6:]:
                if isinstance(m, dict):
                    c = str(m.get("content") or "").strip()
                    if c:
                        last_turns.append(c)

        has_active_draft = bool(prior)

        classifier = get_wizard_supervisor_classifier()
        try:
            output = await asyncio.to_thread(
                classifier.classify_sync,
                user_message=user_message,
                current_stage=current_stage,
                tenant_context_snippet=tenant_snippet,
                last_turns=last_turns,
                has_active_draft=has_active_draft,
            )
        except Exception as exc:  # noqa: BLE001 — fail-OPEN
            logger.warning(
                "[WizardSupervisor] classify_sync raised (fail-open): %s",
                exc,
            )
            return None

        if output is None:
            return None

        intent = output.intent
        cls._emit_supervisor_telemetry(
            intent=intent,
            confidence=output.confidence,
            company_id=company_id,
            thread_id=thread_id,
            current_stage=current_stage,
        )

        # ── Short-circuit: meta_question ─────────────────────────────
        # Contrato canônico (Task #1127, fase 1.1): meta perguntas são
        # respondidas pelo `wizard_meta_question_helper` (Sonnet, stage-aware).
        # O `output.conversational_reply` do supervisor (Haiku) é APENAS
        # last-resort — nunca primário. Inverter essa ordem produz respostas
        # genéricas e perde a awareness de etapa.
        if intent == "meta_question":
            reply = ""
            try:
                from app.domains.job_creation.services.wizard_meta_question_helper import (
                    generate_meta_response_sync,
                )
                reply = await asyncio.to_thread(
                    generate_meta_response_sync,
                    stage=current_stage or "wizard",
                    user_message=user_message,
                    tenant_context_snippet=tenant_snippet,
                    last_turns=last_turns,
                    stage_description=(
                        f"wizard de criação de vaga, etapa {current_stage}"
                        if current_stage else "wizard de criação de vaga"
                    ),
                ) or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[WizardSupervisor] meta helper failed (fail-open): %s",
                    exc,
                )
            if not reply:
                # Last-resort: usa reply do supervisor classifier (Haiku).
                reply = (output.conversational_reply or "").strip()
            if not reply:
                # Fallback determinístico — NÃO é canned do produto (sentinela
                # T3 veta literais de produto). Hard-prefix sinaliza estado.
                reply = (
                    "Posso responder rapidinho: estamos no wizard de criação "
                    "de vaga. Quer que eu repita o que estava pedindo?"
                )
            return {
                "intent": "meta_question",
                "short_circuit": True,
                "message": reply,
                "ws_stage_payload": {
                    "type": "wizard_meta_reply",
                    "data": {"message": reply, "stage": current_stage or ""},
                },
            }

        # ── Short-circuit: exit_wizard ────────────────────────────────
        if intent == "exit_wizard":
            reply = (output.conversational_reply or "").strip() or (
                "Sem problema, paramos por aqui. Quando quiser retomar, é só "
                "me chamar."
            )
            return {
                "intent": "exit_wizard",
                "short_circuit": True,
                "message": reply,
                "ws_stage_payload": {
                    "type": "wizard_exit",
                    "data": {"message": reply, "stage": current_stage or ""},
                },
            }

        # create_new / resume_draft / edit_published / continue_current
        # caem no fluxo legacy (graph). Handlers dedicados virão nas
        # Tasks #1128+ (follow-ups). Preservar fluxo é a postura segura.
        return {"intent": intent, "short_circuit": False}

    @staticmethod
    def _emit_supervisor_telemetry(
        *,
        intent: str,
        confidence: float,
        company_id: str | None,
        thread_id: str,
        current_stage: str | None,
    ) -> None:
        """Telemetria fail-OPEN do supervisor (Prometheus + audit).

        Counter Prometheus ``lia_wizard_supervisor_intent_total``
        (label=intent,stage) e audit row ``decision_type=
        wizard_supervisor_routed`` (SOX 7y) — best-effort, nunca derruba
        o turno.
        """
        stage_label = current_stage or "unstarted"

        # Prometheus
        try:  # pragma: no cover — exercitado via integração
            from prometheus_client import REGISTRY as _PROM_REGISTRY
            from prometheus_client import Counter as _PromCounter

            existing = getattr(
                _PROM_REGISTRY, "_names_to_collectors", {},
            ).get("lia_wizard_supervisor_intent_total")
            if existing is None:
                counter = _PromCounter(
                    "lia_wizard_supervisor_intent_total",
                    "Total de intents classificados pelo Wizard Supervisor "
                    "(Task #1127). Label intent ∈ allowlist canônica; "
                    "label stage = current_stage do graph ou 'unstarted'.",
                    labelnames=("intent", "stage"),
                )
            else:
                counter = existing
            counter.labels(intent=intent, stage=stage_label).inc()
        except Exception as pm_exc:  # noqa: BLE001
            logger.debug(
                "[WizardSupervisor] prometheus inc failed (fail-open): %s",
                pm_exc,
            )

        # Audit row (best-effort)
        cid = str(company_id) if company_id else ""
        if not cid:
            return
        try:
            from app.shared.compliance.audit_service import AuditService
            asyncio.create_task(AuditService().log_decision(  # AUDIT-NO-DEMO: wizard supervisor routing telemetry (job creation flow, no candidate decision; LGPD Art.20 N/A)
                company_id=cid,
                agent_name="wizard_supervisor_classifier",
                decision_type="wizard_supervisor_routed",
                action=f"supervisor_route:{intent}",
                decision=intent,
                reasoning=[
                    f"intent={intent}",
                    f"confidence={confidence:.2f}",
                    f"stage={stage_label}",
                    f"thread_id={thread_id}",
                ],
                criteria_used=[
                    "wizard_supervisor_t1127",
                    f"intent:{intent}",
                    f"stage:{stage_label}",
                ],
                human_review_required=False,
            ))
        except Exception as audit_exc:  # noqa: BLE001
            logger.debug(
                "[WizardSupervisor] audit emit failed (fail-open): %s",
                audit_exc,
            )

    # ── Orquestrador conversacional (strangler-fig, Paulo 2026-05-31) ────
    # Caminho alternativo ao pipeline LangGraph: um tool-calling agent
    # state-aware. Ligado por LIA_WIZARD_ORCHESTRATOR (default OFF). Quando
    # ON, BYPASSA o graph completamente — lê o state via checkpointer
    # (mesma fonte do graph), roda o orquestrador, e persiste o state
    # mutado via update_state. Coexistência: o schema JobCreationState é o
    # mesmo, então alternar a flag preserva a sessão.
    @staticmethod
    def _orchestrator_enabled() -> bool:
        """Lê a flag de os.environ (prod/Secrets) OU do .env (dev).

        No setup Replit dev, o ``.env`` NÃO é injetado em ``os.environ``
        (pydantic-settings o lê para o objeto Settings, não para o environ).
        Para a flag funcionar em dev sem precisar de Secret nem restart com
        export, fazemos fallback para uma leitura cacheada do ``.env``.
        Fail-open: qualquer erro → False (orquestrador desligado).
        """
        _TRUTHY = ("1", "true", "yes", "on")
        val = os.environ.get("LIA_WIZARD_ORCHESTRATOR")
        if val is not None:
            return val.strip().lower() in _TRUTHY
        try:
            from dotenv import dotenv_values  # type: ignore
            cached = getattr(WizardSessionService, "_dotenv_cache", None)
            if cached is None:
                cached = dotenv_values(".env") or {}
                WizardSessionService._dotenv_cache = cached  # type: ignore[attr-defined]
            dv = (cached.get("LIA_WIZARD_ORCHESTRATOR") or "").strip().lower()
            return dv in _TRUTHY
        except Exception:  # noqa: BLE001 — fail-open
            return False

    @classmethod
    async def _persist_orchestrator_state(
        cls, thread_id: str, values: dict
    ) -> bool:
        """Persiste o state mutado no checkpointer do graph (fonte única).

        Usa ``update_state`` (escreve checkpoint sem rodar nós). Fail-loud:
        loga WARNING se falhar (o reply já foi gerado; só sinaliza que o
        state pode não ter persistido — nunca silent).
        """
        try:
            from app.domains.job_creation.graph import get_job_creation_graph
            wiz_g = get_job_creation_graph()
            config = {"configurable": {"thread_id": thread_id}}
            await asyncio.to_thread(wiz_g._graph.update_state, config, values)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[WizardOrchestrator] state persist FAILED thread=%s reason=%s "
                "— reply entregue mas state pode não ter persistido.",
                thread_id, type(exc).__name__,
            )
            return False

    @classmethod
    async def _process_via_orchestrator(
        cls,
        *,
        thread_id: str,
        user_message: str,
        user_id: str | None,
        company_id: str | None,
        prior_state: dict,
        context: dict | None,
    ) -> tuple[str, dict, int]:
        """Processa o turno via WizardOrchestrator (bypass do graph)."""
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            get_wizard_orchestrator,
        )
        from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
        from app.domains.job_creation.helpers.ws_payload_builder import (
            build_ws_stage_payload,
        )
        from app.domains.job_creation.state import calculate_completeness

        state = dict(prior_state or {})

        # ── Terminal stage guard (belt-and-suspenders) ─────────────────
        # When the checkpoint is at a terminal stage, the previous wizard
        # is finished. Reset to fresh state so a new wizard can start.
        _prior_stage = state.get('current_stage', '')
        if _prior_stage in {'handoff', 'completed', 'done'}:
            logger.info(
                "[WizardOrchestrator] terminal stage: stage=%s thread=%s "
                "— resetting to fresh state for new wizard",
                _prior_stage, thread_id,
            )
            state = {}
        # Carrega campos do context (right_panel_form, tenant snippet) p/ o state.
        for k in _CONTEXT_CARRY_KEYS:
            if context and context.get(k) is not None:
                state[k] = context[k]

        # ── Captura determinística do email do gestor (LGPD) ───────────
        # O email é apagado pelo c3b/pii_masking ('[EMAIL REMOVIDO]') ANTES
        # do LLM. O wizard PRECISA do valor (registro do gestor), mas o LLM
        # NÃO — então extraímos do texto cru (context['_raw_user_message'])
        # no servidor e gravamos direto no state, sem nunca enviar ao LLM.
        # Decisão Paulo 2026-05-31 (extração determinística).
        # Fonte do texto cru para extrair o email:
        #  - WS: context['_raw_user_message'] (user_message chega mascarado).
        #  - SSE: user_message já é cru (SSE não mascara inbound) — fallback.
        # Cobrir ambos torna a captura robusta ao transporte (root cause do
        # round 2: SSE não preenchia _raw_user_message → zero capturas).
        _raw_msg = (context or {}).get("_raw_user_message") or user_message or ""
        _email = _extract_manager_email(_raw_msg)
        if _email:
            # Bug 2a fix: skip if email matches the recruiter's own email.
            # parsed_recruiter_email is set from JWT/session at login time.
            _recruiter_email = (state.get("parsed_recruiter_email") or "").lower().strip()
            if _email.lower() != _recruiter_email:
                state["parsed_manager_email"] = _email
                logger.info(
                    "[WizardOrchestrator] manager_email capturado deterministicamente "
                    "(len=%d) thread=%s", len(_email), thread_id,
                )
                # H2-warning: dominio diferente do recrutador pode indicar email
                # de outra empresa (sem validacao de tenant para manager).
                _mgr_domain = _email.split("@")[-1].lower()
                if _recruiter_email and _mgr_domain != _recruiter_email.split("@")[-1].lower():
                    logger.warning(
                        "[WizardOrchestrator] manager_email dominio difere do recrutador "
                        "(%s vs %s) — sem validacao de tenant, thread=%s",
                        _mgr_domain,
                        _recruiter_email.split("@")[-1].lower(),
                        thread_id,
                    )
            else:
                logger.debug(
                    "[WizardOrchestrator] manager_email ignorado (igual ao email do recrutador) "
                    "thread=%s", thread_id,
                )

        # ── Captura determinISTICa do NOME do gestor (audit 2026-06-05) ─────
        # Mesma razao do email (decisao Paulo 2026-05-31, estendida): por LGPD
        # o nome e mascarado (Presidio PERSON) ANTES do LLM, que entao o
        # INVENTA a cada turno (Carlos Mendes -> Ricardo Almeida...).
        # Capturamos do texto CRU no servidor -- NUNCA pelo LLM. Fontes:
        # (1) texto cru ("o gestor e Paulo Moraes" / correcao "nao e X e Y"),
        # (2) derivacao do email (paulo.moraes@ -> Paulo Moraes). Sugestao a
        # confirmar. Corre a cada turno: a correcao vence; sem sinal, mantem.
        from app.domains.job_creation.helpers.manager_identity import (
            derive_name_from_email,
            extract_manager_name_from_text,
        )
        _mgr_hint = False
        for _m in reversed(state.get("conversation_messages") or []):
            if _m.get("role") == "assistant":
                _c = (_m.get("content") or "").lower()
                _mgr_hint = (
                    "nome do gestor" in _c
                    or "gestor responsavel" in _c
                    or "gestor responsável" in _c
                    or "quem e o gestor" in _c
                    or "quem é o gestor" in _c
                )
                break
        _mgr_name = extract_manager_name_from_text(
            _raw_msg, manager_context_hint=_mgr_hint
        )
        if not _mgr_name and _email:
            _mgr_name = derive_name_from_email(_email)
        if _mgr_name:
            state["parsed_manager_name"] = _mgr_name
            state["manager_name_suggested"] = True
            logger.info(
                "[WizardOrchestrator] manager_name capturado deterministicamente "
                "(len=%d) thread=%s", len(_mgr_name), thread_id,
            )

        ctx = ToolContext(
            company_id=str(company_id or state.get("company_id") or ""),
            user_id=user_id,
            workspace_id=state.get("workspace_id"),
        )
        orch = get_wizard_orchestrator()
        # B5b: pré-busca o company context (missão/valores filtrados por toggle)
        # AQUI no loop async — DB async NÃO funciona dentro do thread do
        # process_turn (MissingGreenlet). Cacheia no state (1x por sessão); o
        # enrich tool lê state['company_context'] e injeta no JD (about_company).
        if "company_context" not in state and ctx.company_id:
            try:
                from app.core.database import AsyncSessionLocal
                from app.shared.services.lia_agent_context_builder import (
                    build_company_agent_context,
                )
                async with AsyncSessionLocal() as _cc_db:
                    state["company_context"] = await build_company_agent_context(
                        company_id=ctx.company_id,
                        db=_cc_db,
                        job_context={
                            "title": state.get("parsed_title", ""),
                            "department": state.get("parsed_department", ""),
                            "seniority": state.get("parsed_seniority", ""),
                        },
                    ) or ""
            except Exception as _cc_exc:  # noqa: BLE001 — fail-open
                logger.warning(
                    "[WizardOrchestrator] company_context fetch falhou: %s", _cc_exc
                )
                state["company_context"] = ""
        result = await asyncio.to_thread(
            orch.process_turn,
            state=state,
            user_message=user_message,
            ctx=ctx,
        )

        new_state = {**state, **result.state_updates}
        new_state["company_id"] = ctx.company_id
        # Stage derivado do progresso (o painel é stage-driven). Persistido
        # para o próximo turno e usado no payload.
        stage = _derive_wizard_stage(new_state)
        new_state["current_stage"] = stage
        # Acumula histórico (mesma estrutura que os nós usam).
        conv = list(new_state.get("conversation_messages") or [])
        conv.append({"role": "user", "content": user_message})
        conv.append({"role": "assistant", "content": result.reply})
        new_state["conversation_messages"] = conv[-50:]

        # Manus F1 — panel_pref one-shot: consumir (pop) ANTES do persist
        # para a key nunca chegar ao checkpoint (update_state faz MERGE —
        # pop pós-persist não removeria, e os turnos seguintes re-emitiriam).
        panel_pref = _consume_panel_pref(new_state)

        await cls._persist_orchestrator_state(thread_id, new_state)

        # Payload alinhado ao contrato canonical do painel (DRY com _ficha_data
        # do intake_gate) + campos de gestor + JD enriquecida. O FE substitui
        # stageData pelo payload (não faz merge) — por isso é cumulativo.
        try:
            from app.domains.job_creation.nodes.intake_gate import _ficha_data
            data = _ficha_data(new_state, result.reply)
            # Gestor (não cobertos por _ficha_data) — painel renderiza estes.
            data["parsed_manager_name"] = new_state.get("parsed_manager_name")
            data["parsed_manager_email"] = new_state.get("parsed_manager_email")
            # T10: stakeholders/envolvidos adicionais
            if new_state.get("parsed_stakeholders"):
                data["parsed_stakeholders"] = new_state["parsed_stakeholders"]
            # Responsabilidades confirmadas (item #2) — surfacar pro painel.
            if new_state.get("confirmed_responsibilities"):
                data["confirmed_responsibilities"] = new_state.get("confirmed_responsibilities")
            # Idiomas confirmados (item #3) — surfacar pro painel.
            if new_state.get("confirmed_languages"):
                data["confirmed_languages"] = new_state.get("confirmed_languages")
            # Bug 3a fix: Benefits and variable compensation — surface to JobCreationPanel.
            if new_state.get("confirmed_benefits"):
                data["confirmed_benefits"] = new_state.get("confirmed_benefits")
            if new_state.get("confirmed_variable_compensation"):
                data["confirmed_variable_compensation"] = new_state.get("confirmed_variable_compensation")
            # B3 fix: competency_tree p/ o CompetencyPanel (add/remove).
            _ctree = _competency_tree_for_panel(new_state)
            if _ctree:
                data["competency_tree"] = _ctree
                data["seniority"] = (
                    new_state.get("seniority_resolved")
                    or new_state.get("parsed_seniority")
                    or ""
                )
                data["seniority_display"] = data["seniority"]
                data.setdefault("distribution", {
                    "technical": sum(1 for x in _ctree if x["block"] == "technical"),
                    "behavioral": sum(1 for x in _ctree if x["block"] == "behavioral"),
                })
            # JD enriquecida — surfacar para o painel exibir a descrição.
            if new_state.get("jd_enriched"):
                _jd = new_state.get("jd_enriched") or {}
                data["jd_enriched"] = _jd
                data["jd_raw"] = new_state.get("jd_raw") or new_state.get("raw_input")
                data["jd_approved"] = new_state.get("jd_approved")
                # B5 fix (2026-05-31): 9 dimensões de qualidade (D1-D9) +
                # band, via o canônico evaluate_jd_quality — MESMO contrato do
                # endpoint /jd-evaluate de Settings. Antes o painel só recebia
                # um score consolidado (sem o breakdown). Determinístico.
                try:
                    from app.domains.cv_screening.services.wsi_service.jd_quality import (
                        evaluate_jd_quality,
                    )
                    _q = evaluate_jd_quality(
                        description=_jd.get("about_role"),
                        job_title=_jd.get("titulo_padronizado"),
                        seniority=_jd.get("senioridade_confirmada"),
                        responsibilities=list(_jd.get("responsabilidades") or []),
                        technical_skills=[
                            x.get("skill", "") for x in (_jd.get("skills_obrigatorias") or [])
                        ],
                        behavioral_competencies=[
                            x.get("competencia", "")
                            for x in (_jd.get("competencias_comportamentais") or [])
                        ],
                    )
                    data["quality_score"] = _q["score"]
                    data["quality_indicators"] = _q["indicators"]
                    data["quality_band"] = _q["band_label"]
                except Exception as _q_exc:  # noqa: BLE001 — fallback p/ score simples
                    logger.warning(
                        "[WizardOrchestrator] jd 9-dim breakdown falhou: %s", _q_exc
                    )
                    data["quality_score"] = new_state.get("jd_quality_score")
                data["jd_enrichment_used_fallback"] = new_state.get(
                    "jd_enrichment_used_fallback", False
                )
            # Perguntas WSI — surfacar para o WsiQuestionsPanel renderizar.
            if new_state.get("wsi_questions"):
                # B7 fix (2026-05-31): o painel FE (WsiQuestionsData) lê
                # `questions` e `distribution` — NÃO `wsi_questions`/
                # `question_distribution`. Key mismatch fazia o painel mostrar
                # "0 perguntas" mesmo com a tool tendo gerado. Alinhado ao nó
                # canônico wsi_questions_node (chave "questions").
                data["questions"] = new_state.get("wsi_questions")
                data["questions_approved"] = new_state.get("questions_approved")
                data["distribution"] = new_state.get("question_distribution")
                data["wsi_questions_used_fallback"] = new_state.get(
                    "wsi_questions_used_fallback", False
                )
                # Task-6 fix: expor seniority_level + screening_mode +
                # expected_distribution para o FE abandonar MIN_DISTRIBUTION
                # hardcoded e usar os dados canônicos do YAML.
                try:
                    from app.domains.job_creation.helpers.wsi_distribution import (
                        block_distribution as _block_dist,
                    )
                    _seniority = new_state.get("seniority_resolved") or "pleno"
                    _mode = new_state.get("screening_mode") or "compact"
                    data["seniority_level"] = _seniority
                    data["screening_mode"] = _mode
                    data["expected_distribution"] = _block_dist(
                        mode=_mode, seniority=_seniority
                    )
                except Exception as _t6_exc:  # noqa: BLE001 — best-effort, não bloqueia painel
                    logger.debug(
                        "[WizardOrchestrator] expected_distribution calc falhou: %s",
                        _t6_exc,
                    )
                # Gate de distribuição (mesma lógica do approve_wsi_questions,
                # fail-open): popula distribution_gap para o banner do
                # WsiQuestionsPanel disparar também no caminho live.
                try:
                    from app.domains.job_creation.orchestrator.wizard_service_tools import (
                        _wsi_distribution_status,
                    )
                    _ds = _wsi_distribution_status(new_state)
                    if _ds["gap"]:
                        data["distribution_gap"] = _ds["gap"]
                except Exception as _dg_exc:  # noqa: BLE001 — banner é best-effort
                    logger.debug(
                        "[WizardOrchestrator] distribution_gap calc falhou: %s",
                        _dg_exc,
                    )
            # W1-A: Perguntas de elegibilidade — surfacar para EligibilityPanel.
            # EligibilityPanel usa data["questions"] (igual ao WSI).
            # Só preenche quando WSI ainda não foi gerado (eligibility vem antes).
            _elig_q = new_state.get("eligibility_questions")
            if _elig_q and not new_state.get("wsi_questions"):
                data["questions"] = _elig_q

            # Bug 13: Calibração — alimenta WizardCalibrationCard
            # threshold: like + dislike contam; skip NÃO (decisão 2026-06-19)
            if new_state.get("calibration_candidates") and stage == "calibration":
                _cands = new_state.get("calibration_candidates") or []
                _threshold = new_state.get("calibration_threshold", 3)
                _signal_count = sum(
                    1 for c in _cands
                    if c.get("decision") in ("approved", "rejected")
                )
                _approved_count = sum(
                    1 for c in _cands if c.get("decision") == "approved"
                )
                _can_advance = new_state.get("can_advance", _signal_count >= _threshold)
                data["calibration_candidates"] = _cands
                data["threshold"] = _threshold
                data["signal_count"] = _signal_count
                data["approved_count"] = _approved_count
                data["can_advance"] = _can_advance
            if new_state.get("job_id"):
                data["job_id"] = new_state.get("job_id")
                data["share_link"] = new_state.get("share_link")
            # handoff_url para o FE navegar à vaga (auto-nav em stage=handoff).
            if stage == "handoff":
                _jid = new_state.get("job_id")
                data["handoff_url"] = f"/jobs/{_jid}" if _jid else "/jobs"
            # Manus F1 — preferência de painel one-shot (open_panel/
            # close_panel). Emitida UMA vez; já removida do state acima.
            if panel_pref:
                data["panel_pref"] = panel_pref
            payload = build_ws_stage_payload(
                stage=stage,
                requires_approval=bool(new_state.get("requires_approval")),
                data=data,
                completeness=calculate_completeness(stage),
            )
            # Bug #3 fix: surface response_blocks (RRP juicybox cards) from orchestrator
            if result.response_blocks:
                payload["response_blocks"] = result.response_blocks
            # P0-E fix (2026-06-14): user pediu "me leve pro chat full" no wizard.
            # Emite ui_action="navigate_to" page="chat" para o SSE handler propagar
            # ao frontend (useUIAction.dispatchOrEmit -> router.push /pt/chat).
            if new_state.get("_navigate_to_fullscreen_chat"):
                payload["ui_action"] = "navigate_to"
                payload["ui_action_params"] = {"page": "chat"}
        except Exception as exc:  # noqa: BLE001  # REGRA-4-EXEMPT: payload é best-effort (UI continua com payload vazio), reply já foi gerado
            logger.warning(
                "[WizardOrchestrator] payload build failed: %s", type(exc).__name__,
                exc_info=True,
            )
            # FIX defect #1: NEVER set payload = {} — empty dict is falsy,
            # SSE handler skips panel_update, panel disappears. Build a
            # minimal valid payload so the panel stays alive.
            payload = {
                "type": "wizard_stage",
                "stage": stage,
                "data": {
                    "message": result.reply or "[Estado do wizard em atualização]",
                },
                "requires_approval": False,
            }

        # ── Fix: mark wizard checkpoint as completed after handoff ──────
        # Same fix as the graph path — the orchestrator persists
        # current_stage="handoff" but never transitions to "completed".
        if stage == "handoff" and thread_id:
            try:
                await cls._persist_orchestrator_state(
                    thread_id, {"current_stage": "completed"}
                )
                logger.info(
                    "[WizardOrchestrator] marked checkpoint completed after "
                    "handoff thread=%s", thread_id,
                )
            except Exception as _mark_exc:  # REGRA-4-EXEMPT: marcar checkpoint é best-effort, falha não cancela o turn
                logger.warning(
                    "[WizardOrchestrator] failed to mark checkpoint completed "
                    "(fail-open): %s", type(_mark_exc).__name__,
                )

        logger.info(
            "[WizardOrchestrator] turn done thread=%s tools=%s iters=%d "
            "fairness_blocked=%s error=%s",
            thread_id, result.tool_calls, result.iterations,
            result.fairness_blocked, result.error,
        )
        return (result.reply, payload, 0)

    @classmethod
    async def process_message(
        cls,
        *,
        thread_id: str,
        user_message: str,
        user_id: str | None,
        company_id: str | None,
        session_id: str,
        context: dict | None,
        on_token: Any | None = None,
    ) -> tuple[str, dict, int]:
        """Invoke JobCreationGraph for a wizard message (new or continuing).

        Entry point for agent_chat_ws.py wizard path. Replaces the inline
        _invoke_wizard_canonical_streaming logic with the session-aware variant.

        Args:
            thread_id:    Stable session thread_id (from derive_thread_id()).
            user_message: Recruiter's current message.
            user_id:      From JWT (never from payload — multi-tenancy).
            company_id:   From JWT (never from payload — multi-tenancy).
            session_id:   WS session id (used as fallback thread_id key).
            context:      Raw WS context dict (right_panel_form, metadata, …).
            on_token:     Optional async callback ``(chunk: str) → None``.

        Returns:
            ``(recruiter_message, ws_stage_payload, tokens_emitted)``
        """
        from app.domains.job_creation.graph import get_job_creation_graph
        wiz_g = get_job_creation_graph()

        prior_state = await cls._get_prior_state(thread_id)

        # ── Orquestrador conversacional (flag LIA_WIZARD_ORCHESTRATOR) ──
        # Quando ON, bypassa o pipeline LangGraph e roda o tool-calling
        # agent state-aware. Default OFF — zero impacto em produção.
        if cls._orchestrator_enabled():
            logger.info(
                "[WizardSession] routing via ORCHESTRATOR thread=%s", thread_id,
            )
            return await cls._process_via_orchestrator(
                thread_id=thread_id,
                user_message=user_message,
                user_id=user_id,
                company_id=company_id,
                prior_state=prior_state,
                context=context,
            )

        # ── Sprint F.2 (2026-05-20) — Skip supervisor mid-flow ─────────
        # CANONICAL FIX (Option A): when ``prior_state.current_stage`` is
        # in the ACTIVE wizard stages, SKIP the pre-graph supervisor
        # classifier entirely. Rationale: those stages have an active
        # HITL gate (``langgraph.types.interrupt()``) waiting for a
        # specific recruiter response (modo compact/full, aprovação JD,
        # ajuste de competência). Re-classifying short answers like
        # "modo compacto" / "aprovado" / "ok" via Haiku risks misrouting
        # them as ``create_new`` / ``meta_question`` / ``exit_wizard``
        # and regressing the wizard to intake. The supervisor must only
        # run for (a) genuine new conversations (no prior_state) or
        # (b) terminal/idle stages where re-classification is safe.
        #
        # Active wizard stages = entire WizardStage Literal minus
        # ``intake`` (where supervisor is needed to detect meta_question
        # / exit_wizard before the first JD parse) and terminal
        # ``done`` / ``handoff`` / ``calibration`` (post-publish).
        # The 8 active stages map 1:1 to nodes with interrupt() gates.
        # Sprint F.2-v2 canonical: helper module-level testable em isolamento.
        # ``_ACTIVE_WIZARD_STAGES`` + threshold vivem no topo do módulo agora.
        _prior_stage = None
        if isinstance(prior_state, dict):
            _prior_stage = prior_state.get("current_stage")
        # ── Terminal stage guard (graph path) ─────────────────────
        if _prior_stage in ('handoff', 'completed', 'done'):
            logger.info(
                "[WizardSession] terminal stage (graph): stage=%s "
                "thread=%s — resetting prior_state for new wizard",
                _prior_stage, thread_id,
            )
            prior_state = {}
        _skip_supervisor = _compute_supervisor_skip(user_message, _prior_stage)
        _msg_len = len((user_message or "").strip())
        # Sprint F.4 (iter 3) — diagnostic INFO so we can see supervisor
        # skip engagement in prod INFO logs (was logger.debug, filtered).
        # Sprint F.2-v2 adiciona ``msg_len`` ao diagnostic pra correlacionar
        # skip decisions com tamanho do conteúdo (root cause Paulo 2026-05-26).
        logger.info(
            "[WizardSession] supervisor decision: prior_stage=%r skip=%s "
            "msg_len=%d thread=%s",
            _prior_stage, _skip_supervisor, _msg_len, thread_id,
        )

        # ── Task #1127 (T1.1 + T2.1) — Supervisor pre-graph ────────────
        # Classifica a INTENÇÃO GLOBAL do turno antes de tocar o graph.
        # Short-circuit determinístico para meta_question / exit_wizard;
        # demais intents (continue_current / create_new / resume_draft /
        # edit_published) caem no fluxo legacy (preserva contrato vigente
        # — extensões nas Tasks #1128+ via follow-ups).
        # Fail-OPEN: qualquer falha do supervisor devolve None →
        # continue_current → fluxo intacto. Sentinela offline em
        # tests/integration/agents/test_wizard_supervisor_t1127.py.
        sv_result = None
        if _skip_supervisor:
            logger.info(
                "[WizardSession] supervisor SKIPPED (active stage=%s "
                "thread=%s) — Sprint F.2 canonical fix",
                _prior_stage, thread_id,
            )
        else:
            try:
                sv_result = await cls._run_supervisor(
                    user_message=user_message,
                    prior_state=prior_state,
                    context=context,
                    company_id=company_id,
                    session_id=session_id,
                    thread_id=thread_id,
                )
            except Exception as sv_exc:  # noqa: BLE001 — supervisor é fail-OPEN
                logger.warning(
                    "[WizardSession] supervisor raised (fail-open): %s", sv_exc,
                )
                sv_result = None
        if sv_result is not None and sv_result.get("short_circuit"):
            return (
                sv_result["message"],
                sv_result.get("ws_stage_payload") or {},
                0,
            )

        # Task #1094 — caminho canônico de resume: se o checkpoint está
        # pausado em ``langgraph.types.interrupt()`` (HITL gate ativo),
        # resumimos via ``Command(resume=<msg>)`` SEM rebuilder/enrichment
        # de state. As enrichments (manager_preferences, hiring_policy_summary,
        # tenant_context_snippet) já vivem no checkpoint desde a invocação
        # inicial do wizard — re-injetar seria desperdício e arrisca
        # sobrescrever mutações que o gate fez no turno anterior.
        if await asyncio.to_thread(wiz_g.is_interrupted, thread_id):
            try:
                result = await wiz_g.aresume_with_message(thread_id, user_message)
            except Exception as inv_exc:  # noqa: BLE001
                # Task #1161 (Bug B): preserve full traceback before fallback.
                # The original catch only logged `type(exc).__name__`, hiding
                # the actual stack and root cause (e.g. `NotImplementedError`
                # from a legacy stub deep in the graph). `logger.exception`
                # writes the full traceback; `sentry_sdk.capture_exception`
                # surfaces it in prod observability.
                logger.exception(
                    "[WizardSession] aresume_with_message raised %s "
                    "(session=%s thread=%s company=%s) — triggering silent "
                    "fallback. Stack trace above is the ROOT CAUSE; do not "
                    "treat fallback message as the real error.",
                    type(inv_exc).__name__, session_id, thread_id, company_id,
                )
                try:  # pragma: no cover — Sentry opcional em testes
                    import sentry_sdk
                    sentry_sdk.capture_exception(inv_exc)
                except Exception:
                    pass
                _emit_silent_fallback(
                    stage=None,
                    company_id=company_id,
                    session_id=session_id,
                    thread_id=thread_id,
                    conversation_tail=(prior_state or {}).get("conversation_messages"),
                    cause=f"resume_exception:{type(inv_exc).__name__}",
                )
                fallback_msg = await _generate_fallback_reply(
                    stage=None,
                    conversation_tail=(prior_state or {}).get("conversation_messages"),
                    tenant_snippet=(prior_state or {}).get("tenant_context_snippet"),
                )
                return (fallback_msg, {}, 0)
            # Fix Loop 1+2: se o graph pausou em interrupt() dentro de um node,
            # o result contém state do checkpoint anterior (stale ws_stage_payload).
            # Extrair a mensagem do interrupt data e injetar como override.
            _intr_msg = await asyncio.to_thread(
                wiz_g.get_pending_interrupt_message, thread_id
            )
            if _intr_msg and isinstance(result, dict):
                result = {**result, "_interrupt_msg_override": _intr_msg}
            state = prior_state or {}
            tokens_emitted = 0
            return await cls._post_process_result(
                result=result,
                state=state,
                prior_state=prior_state,
                company_id=company_id,
                session_id=session_id,
                thread_id=thread_id,
                tokens_emitted=tokens_emitted,
            )

        state = cls._build_state(
            thread_id=thread_id,
            user_message=user_message,
            user_id=user_id,
            company_id=company_id,
            session_id=session_id,
            context=context,
            prior_state=prior_state,
        )

        # ── Create-from-source seeding (PR-A5b — fresh session only) ──
        # If the recruiter started the wizard from a template/vacancy, the
        # source descriptor arrives in context["seed_source"]. Build the
        # seed via the canonical producer + merge it into the fresh state
        # (user input on later turns wins — precedence handled by the mapper).
        # Only on a brand-new session: never re-seed a continuing turn.
        seed_source = (context or {}).get("seed_source")
        if seed_source and not prior_state and company_id:
            from app.core.database import AsyncSessionLocal
            from app.domains.job_creation.helpers.seed_session import (
                seed_initial_state,
            )
            async with AsyncSessionLocal() as _seed_db:
                await seed_initial_state(
                    state, seed_source, str(company_id), _seed_db
                )

        # ── Manager preferences injection (GUIDE — fail-open) ──────────
        # Only on the first message of a session (when manager_email is known)
        # to avoid overwriting state already set by the user in later turns.
        manager_email = state.get("manager_email") or (context or {}).get("manager_email")
        if manager_email and company_id and not state.get("manager_preferences_loaded"):
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
                async with AsyncSessionLocal() as _mp_db:
                    prefs = await ManagerPreferencesService.apply_to_state(
                        _mp_db, str(company_id), manager_email, state
                    )
                    if prefs:
                        state.update(prefs)
                        state["company_defaults_applied"] = list(state.get("company_defaults_applied") or []) + ["manager_preferences"]
                        state["manager_preferences_loaded"] = True
                        logger.info("[WizardSession] manager_preferences applied: %s", list(prefs.keys()))
            except Exception as mp_exc:
                logger.warning("[WizardSession] manager_preferences injection failed (fail-open): %s", mp_exc)

        # ── Sprint 4 (2026-05-26) — Proactive context inject canonical ──
        # Espelha Sprint 3.4 do MainOrchestrator.process para o wizard path.
        # Settings UI edits (notifyChatOfSettingsUpdate dispatch via
        # Sprint 2.4 debounce → Sprint 3.3 POST → Sprint 3.2 Redis store)
        # ficam disponíveis para nodes do wizard que consomem
        # ``state['tenant_context_snippet']`` (jd_enrichment, gate_classifier,
        # bigfive, etc). Sem essa injeção, editar Settings durante wizard
        # ativo NÃO chega ao LLM do wizard — gap identificado no audit
        # 2026-05-26 (~/Documents/wedotalent_audit_2026-05-26/AUDIT_SESSION_REVIEW.md §3.1).
        #
        # Estratégia: appendar notes ao tenant_context_snippet existente
        # (não substituir) para preservar contexto canonical do tenant.
        # Reforça Anti-pattern #1 inline igual Sprint 3.4 (consistência
        # comportamental cross-paths).
        # Fail-open total: Redis down -> noop, NÃO quebra wizard.
        if company_id and user_id:
            try:
                from app.shared.services.proactive_context_store import (
                    ProactiveContextStore,
                    PROACTIVE_CTX_MAX_NOTES,  # PR-12/F-4.15 env-tunable
                    proactive_context_inject_counter,  # PR-12/F-4.14
                )
                _pc_notes = await ProactiveContextStore.list_recent(
                    company_id=str(company_id),
                    user_id=str(user_id),
                    limit=PROACTIVE_CTX_MAX_NOTES,
                )
                if _pc_notes:
                    _pc_lines = [
                        "\n\n### Contexto recente das configurações (últimos 30min)",
                        "O recrutador acabou de editar configurações via UI. "
                        "Considere reagir proativamente APENAS se for relevante "
                        "para a vaga sendo criada. NUNCA enumere features "
                        "(Anti-pattern #1) — comente apenas o que mudou se útil "
                        "para a triagem/wizard.",
                        "",
                    ]
                    for _n in _pc_notes[:PROACTIVE_CTX_MAX_NOTES]:
                        _act = str(_n.get("action_id") or "")
                        _sec = str(_n.get("section") or "")
                        _fld = _n.get("field")
                        _val = _n.get("value")
                        _fld_part = f' · campo "{_fld}"' if _fld else ""
                        _val_part = ""
                        if _val is not None:
                            _val_str = str(_val)
                            if len(_val_str) > 200:
                                _val_str = _val_str[:200] + "…"
                            _val_part = f" = {_val_str}"
                        _pc_lines.append(
                            f"- {_sec}{_fld_part}{_val_part}  (ação: {_act})"
                        )
                    _pc_block = "\n".join(_pc_lines)
                    _existing_snippet = state.get("tenant_context_snippet") or ""
                    state["tenant_context_snippet"] = _existing_snippet + _pc_block
                    logger.info(
                        "[WizardSession] Sprint 4: injected %d proactive context "
                        "notes into tenant_context_snippet (company=%s user=%s)",
                        len(_pc_notes), company_id, user_id,
                    )
                    # PR-12 / F-4.14 — telemetry: count successful injections
                    if proactive_context_inject_counter is not None:
                        try:
                            proactive_context_inject_counter.labels(
                                path="wizard", status="hit"
                            ).inc()
                        except Exception:
                            pass
                    # Clear consumed (Sprint 4 mirror Sprint 3.4) — evita
                    # re-injeção do mesmo contexto a cada turn do wizard.
                    try:
                        await ProactiveContextStore.clear_consumed(
                            company_id=str(company_id),
                            user_id=str(user_id),
                        )
                    except Exception:
                        pass
            except Exception as _pc_exc:
                logger.debug(
                    "[WizardSession] Sprint 4 proactive context inject failed "
                    "(fail-open): %s",
                    _pc_exc,
                )
                # PR-12 / F-4.14 — telemetry: count fail-open occurrences
                try:
                    from app.shared.services.proactive_context_store import (
                        proactive_context_inject_counter as _ctr,
                    )
                    if _ctr is not None:
                        _ctr.labels(path="wizard", status="fail_open").inc()
                except Exception:
                    pass

        # ── Hiring policy summary injection (T2 fix #7 — code review #5) ─
        # O ``wizard_gate_classifier`` recebe ``hiring_policy_summary`` para
        # calibrar a classificação de intent (ex.: tenants com
        # ``manager_approval_for_offer=true`` exigem aprovação explícita;
        # tenants com automação alta podem aceitar "ok" como approve).
        # Sem essa injeção, o classifier opera sem contexto organizacional
        # — requisito da Task #1085. Best-effort lazy load + cache no state.
        if company_id and not state.get("hiring_policy_summary"):
            try:
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import text as _sql_text
                async with AsyncSessionLocal() as _hp_db:
                    row = (await _hp_db.execute(
                        _sql_text(
                            "SELECT pipeline_rules, screening_rules, automation_rules "
                            "FROM company_hiring_policies "
                            "WHERE company_id = CAST(:cid AS uuid) "
                            "LIMIT 1"
                        ),
                        {"cid": str(company_id)},
                    )).first()
                if row:
                    pr, sr, ar = row[0] or {}, row[1] or {}, row[2] or {}
                    parts: list[str] = []
                    if pr.get("manager_approval_for_offer") is not None:
                        parts.append(
                            f"aprovação_gestor_oferta={pr['manager_approval_for_offer']}"
                        )
                    if sr.get("min_quality_score") is not None:
                        parts.append(f"qualidade_min_jd={sr['min_quality_score']}")
                    if ar.get("auto_approve_threshold") is not None:
                        parts.append(
                            f"auto_approve_threshold={ar['auto_approve_threshold']}"
                        )
                    if ar.get("automation_level"):
                        parts.append(f"automação={ar['automation_level']}")
                    if parts:
                        state["hiring_policy_summary"] = " | ".join(parts)[:500]
                        logger.info(
                            "[WizardSession] hiring_policy_summary injected (%d fields)",
                            len(parts),
                        )
            except Exception as _hp_exc:
                # Fail-open: classifier opera com summary vazio, mantém allowlist intacta.
                logger.debug(
                    "[WizardSession] hiring_policy_summary lazy-load failed (fail-open): %s",
                    _hp_exc,
                )

        tokens_emitted = 0
        try:
            if hasattr(wiz_g, "stream_invoke"):
                result, tokens_emitted = await wiz_g.stream_invoke(
                    state, thread_id, on_token=on_token,
                )
            else:  # pragma: no cover — defensive: older deploy without stream_invoke
                result = await asyncio.to_thread(wiz_g.invoke, state, thread_id)
        except Exception as inv_exc:  # noqa: BLE001
            # Task #1089 (T3) — fail-LOUD em invocação do graph. Antes da
            # remoção do dict canned este path PROPAGAVA a exceção e o
            # WS handler caía em outra mensagem canned. Agora: emite
            # telemetria completa + devolve fallback contextual em vez
            # de quebrar o turno (e o cliente WS recebe payload válido).
            _emit_silent_fallback(
                stage=None,
                company_id=company_id,
                session_id=session_id,
                thread_id=thread_id,
                conversation_tail=state.get("conversation_messages") if isinstance(state, dict) else None,
                cause=f"invoke_exception:{type(inv_exc).__name__}",
            )
            fallback_msg = await _generate_fallback_reply(
                stage=None,
                conversation_tail=state.get("conversation_messages") if isinstance(state, dict) else None,
                tenant_snippet=state.get("tenant_context_snippet") if isinstance(state, dict) else None,
            )
            return (fallback_msg, {}, tokens_emitted)

        # Fix Loop 1+2: mesma injecao de interrupt override para o path fresh invoke
        _intr_msg_fresh = await asyncio.to_thread(
            wiz_g.get_pending_interrupt_message, thread_id
        )
        if _intr_msg_fresh and isinstance(result, dict):
            result = {**result, "_interrupt_msg_override": _intr_msg_fresh}

        return await cls._post_process_result(
            result=result,
            state=state,
            prior_state=prior_state,
            company_id=company_id,
            session_id=session_id,
            thread_id=thread_id,
            tokens_emitted=tokens_emitted,
        )

    @classmethod
    async def _post_process_result(
        cls,
        *,
        result: Any,
        state: dict,
        prior_state: dict | None,
        company_id: str | None,
        session_id: str,
        thread_id: str,
        tokens_emitted: int,
    ) -> tuple[str, dict, int]:
        """Task #1094 — pós-processamento compartilhado entre o caminho fresh
        invoke e o caminho ``Command(resume=...)`` (interrupt). Antes da
        Task #1094 esta lógica vivia inline em ``process_message`` no único
        caminho ``stream_invoke`` — agora é compartilhada para garantir que
        gate_clarify_message / wizard_stage sync / manager_preferences
        recording sejam idênticos em ambos os paths."""
        if not isinstance(result, dict):
            # Task #1089 — fail-loud: graph devolveu tipo inesperado.
            _emit_silent_fallback(
                stage=None,
                company_id=company_id,
                session_id=session_id,
                thread_id=thread_id,
                conversation_tail=state.get("conversation_messages") if isinstance(state, dict) else None,
                cause=f"non_dict_result:{type(result).__name__}",
            )
            fallback_msg = await _generate_fallback_reply(
                stage=None,
                conversation_tail=state.get("conversation_messages") if isinstance(state, dict) else None,
                tenant_snippet=state.get("tenant_context_snippet") if isinstance(state, dict) else None,
            )
            return (fallback_msg, {}, tokens_emitted)

        # ── Learning loop: record manager preferences on handoff ──────
        # Called here (async context) instead of inside handoff_node (sync).
        # Idempotency key: prevents double-counting on WS reconnect.
        if (
            result.get("current_stage") == "handoff"
            and result.get("manager_email")
            and company_id
        ):
            import hashlib, datetime as _dt
            _ikey = hashlib.md5(
                f"{company_id}:{result['manager_email']}:{result.get('job_id') or thread_id}:{_dt.date.today().isoformat()}".encode()
            ).hexdigest()
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
                async with AsyncSessionLocal() as _rl_db:
                    await ManagerPreferencesService.record_job_completion(
                        _rl_db,
                        company_id=str(company_id),
                        manager_email=result["manager_email"],
                        final_state=result,
                        initial_state=prior_state or None,
                        idempotency_key=_ikey,
                    )
                    logger.info("[WizardSession] manager_preferences recorded for %s", result["manager_email"])
            except Exception as _rl_exc:
                logger.error("[WizardSession] record_job_completion FAILED — learning loop data loss (company_id=%s, email=%s): %s", company_id, result.get("manager_email", "?"), _rl_exc)

        # ── Phase 4I — wizard_stage sync to job_vacancies.wizard_stage ──
        # Only fires post-publish (state['job_id'] becomes truthy after publish_node
        # creates the JobVacancy via Rails). Pre-publish stages are not tracked
        # at this column — see Phase 4J for extended scope (create row earlier).
        # FAIL-OPEN: any error logs warning and continues — UX never blocked
        # by sync regression.
        _jv_id = result.get("job_id")
        _stage_for_db = result.get("current_stage")
        if _jv_id and _stage_for_db and company_id:
            try:
                from sqlalchemy import text as sa_text
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _ws_db:
                    _ws_res = await _ws_db.execute(
                        sa_text(
                            "UPDATE job_vacancies SET wizard_stage = :s, updated_at = NOW() "
                            "WHERE id = CAST(:jid AS uuid) AND company_id = :co"
                        ),
                        {
                            "s": _stage_for_db,
                            "jid": str(_jv_id),
                            "co": str(company_id),
                        },
                    )
                    await _ws_db.commit()
                    if _ws_res.rowcount == 0:
                        logger.debug(
                            "[WizardSession] wizard_stage sync: no row for job_id=%s "
                            "(Rails-only? not yet mirrored?)",
                            _jv_id,
                        )
                    else:
                        logger.debug(
                            "[WizardSession] wizard_stage=%s synced for job_id=%s",
                            _stage_for_db, _jv_id,
                        )
            except Exception as _ws_exc:
                logger.warning(
                    "[WizardSession] wizard_stage sync failed (fail-open): %s", _ws_exc,
                )


        # ── Fix: mark wizard checkpoint as completed after handoff ──────
        # handoff_node sets current_stage="handoff" for the WS payload,
        # but never transitions to "completed". Without this, the
        # checkpointer keeps the session "active" and the next page load
        # rehydrates the stale handoff panel ("Vaga publicada" on a fresh
        # conversation). We update the checkpoint AFTER the learning loop
        # and wizard_stage sync (which both check for "handoff") so they
        # see the original stage, then mark as terminal.
        if result.get("current_stage") == "handoff" and thread_id:
            try:
                import asyncio as _asyncio_mark
                _mark_config = {"configurable": {"thread_id": thread_id}}
                await _asyncio_mark.to_thread(
                    wiz_g._graph.update_state,
                    _mark_config,
                    {"current_stage": "completed"},
                )
                logger.info(
                    "[WizardSession] marked checkpoint completed after handoff "
                    "thread=%s session=%s",
                    thread_id, session_id,
                )
            except Exception as _mark_exc:
                logger.warning(
                    "[WizardSession] failed to mark checkpoint completed "
                    "(fail-open, TTL will expire): %s", _mark_exc,
                )

        stage_payload = result.get("ws_stage_payload") or {}
        stage_data = stage_payload.get("data") or {}
        current_stage = result.get("current_stage", "") or ""

        # Sprint O.1 canonical: propagate job_vacancy_id forward.
        # publish_node sets state["job_id"] AND ws_stage_payload.data.job_id, but
        # subsequent nodes (calibration_node, handoff_node, review_gate_node)
        # overwrite ws_stage_payload with their own data dict (without job_id),
        # so the orchestrator loses the id after the publish turn. Inject from
        # top-level state so downstream readers always see it regardless of
        # which node produced the final ws_stage_payload.
        _o1_job_id = result.get("job_id") if isinstance(result, dict) else None
        if _o1_job_id:
            stage_payload.setdefault("job_vacancy_id", str(_o1_job_id))
            if isinstance(stage_data, dict):
                stage_data.setdefault("job_id", str(_o1_job_id))
                stage_payload["data"] = stage_data


        # Task #1080: Redis session marker upkeep removed. The canonical
        # ``is_wizard_session_active`` reads the checkpointer directly, so
        # there is nothing to mark/clear on each turn. Wizard "doneness" is
        # detected from ``current_stage == "completed"`` in the checkpoint.

        # Fix Loop 1+2: interrupt override tem prioridade maxima — indica que
        # intake_gate_node chamou interrupt() mid-node e o checkpoint contem
        # ws_stage_payload stale do node anterior. Ver get_pending_interrupt_message.
        interrupt_msg_override = (
            result.get("_interrupt_msg_override") if isinstance(result, dict) else None
        )
        if interrupt_msg_override:
            return (str(interrupt_msg_override), stage_payload, tokens_emitted)

        # T2 fix #5 (code review #4): quando o LLM gate (jd_gate_node) acabou
        # de classificar o turno do recrutador, a resposta contextual está em
        # ``state["gate_clarify_message"]``. Sem esta linha, o WS caía no
        # path canned em LOOP (bug original do screenshot, Task #1085).
        # Preferência: gate_clarify_message > stage_data.message >
        # stage_data.response_text > fail-loud (_emit_silent_fallback +
        # _generate_fallback_reply). Aplicável APENAS quando o gate
        # registrou um intent neste turno (``gate_last_intent`` truthy).
        gate_msg = result.get("gate_clarify_message") if isinstance(result, dict) else None
        gate_intent = result.get("gate_last_intent") if isinstance(result, dict) else None
        # T2 fix #11 (code review #9 comment 2): fairness-block path no
        # ``jd_gate_node`` (FairnessGuard L1) seta ``gate_clarify_message``
        # com a mensagem educacional MAS NÃO seta ``gate_last_intent``
        # (não houve classificação — bloqueio precede o classifier). Se
        # exigíssemos ambos, a mensagem educacional de fairness seria
        # suprimida no WS canônico e o recrutador veria o canned default
        # legado em vez da explicação de fairness. Honrar também quando
        # ``jd_fairness_blocked is True``.
        gate_fairness_blocked = (
            result.get("jd_fairness_blocked") is True if isinstance(result, dict) else False
        )
        if gate_msg and (gate_intent or gate_fairness_blocked):
            message = str(gate_msg)
        else:
            message = (
                stage_data.get("message")
                or stage_data.get("response_text")
            )
            if not message:
                # Task #1089 (T3) — fail-LOUD em vez de canned por stage.
                # O graph chegou aqui sem produzir mensagem nem
                # gate_clarify_message — estado anômalo que ANTES era
                # mascarado pelo dict canned removido (anti-pattern Caso
                # #3/#4 do canonical-fix). Agora: log error + Sentry +
                # audit (wizard_fallback_invoked) + Prometheus counter,
                # e devolve resposta contextual via LLM (ou hard-prefix
                # quando LLM falha).
                _emit_silent_fallback(
                    stage=current_stage,
                    company_id=company_id,
                    session_id=session_id,
                    thread_id=thread_id,
                    conversation_tail=result.get("conversation_messages"),
                    cause="empty_message",
                )
                message = await _generate_fallback_reply(
                    stage=current_stage,
                    conversation_tail=result.get("conversation_messages"),
                    tenant_snippet=result.get("tenant_context_snippet")
                    or (state.get("tenant_context_snippet") if isinstance(state, dict) else None),
                )
        return (message, stage_payload, tokens_emitted)
