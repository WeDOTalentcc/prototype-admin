"""jd_enrichment_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Enrich job description via LLM JdEnrichmentService with fallback templates.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)

logger = logging.getLogger(__name__)


def jd_enrichment_node(state: JobCreationState) -> JobCreationState:
    """F1: Call JdEnrichmentService to enrich JD + calculate quality score.

    This is HITL point 1 — recruiter must approve the enriched JD.

    Fairness 4 layers (canonical wiring — Phase 2A):
      Layer 1 (input gate)  : FairnessGuard.check(raw_input) BEFORE LLM
      Layer 2 (PII strip)   : strip_pii_for_llm_prompt(raw_input) BEFORE LLM
      Layer 3 (output check): FairnessGuard.check(enriched_text) AFTER LLM
      Layer 4 (question guard) lives in wsi_questions_node.
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _apply_pipeline_template_to_state,
        _build_pipeline_template_db_suggestion,
        _emit_fallback_telemetry,
        _emit_wizard_fallback_metric,
        _extract_last_turns,
        _get_jd_service,
        _suggest_pipeline_template,
    )

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
                "ws_stage_payload": build_ws_stage_payload(
                    stage="jd_enrichment",
                    requires_approval=False,
                    data={
                        "error": "fairness_blocked",
                        "category": _fg_input.category,
                        "message": _fg_input.educational_message,
                    },
                ),
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
    # Fix D 2026-05-27 (WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P1-NOVO-#1):
    # Removido "and not _has_parsed_title". Ter title extraido pelo
    # intake_node eh evidencia DE PROGRESSO mas NAO substitui ter JD real.
    # Pre-fix: title set bloqueava classifier; guard tambem nao disparava
    # (depende de _classifier_eligible); LLM enrichment invocado com 40 chars
    # de input inventava about_role/requirements ficticios. Recrutador aprovava
    # JD ilusoria, vaga publicada com conteudo nao escrito por ele.
    # Pos-fix: classifier sempre roda quando jd_enriched=None e nao ha JD
    # estruturada (panel_form/attached). Title eh evidencia auxiliar mas
    # nao gate.
    _classifier_eligible = (
        not state.get("jd_enriched")  # nunca short-circuit em resume
        and not _has_panel_form
        and not _has_attached
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
            or msg("jd_enrichment.ask_for_title")
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
                        msg("jd_enrichment.stage_description_hitl")
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
                "ws_stage_payload": build_ws_stage_payload(
                    stage="jd_enrichment",
                    requires_approval=False,
                    data={
                        "awaiting_jd_input": True,
                        "intent_classified": _intent,
                        "message": _reply,
                    },
                ),
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
        _ask_jd_msg = msg("jd_enrichment.ask_for_jd")
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
            "ws_stage_payload": build_ws_stage_payload(
                stage="jd_enrichment",
                requires_approval=False,
                data={
                    "awaiting_jd_input": True,
                    "message": _ask_jd_msg,
                },
            ),
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
                msg("jd_enrichment.fallback_warning")
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
            # Heurística canonical extraída para helper compartilhado (F-2.9).
            jd_enrichment_fallback_reason = classify_llm_exception_reason(_enrich_exc)
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
                        "ws_stage_payload": build_ws_stage_payload(
                            stage="jd_enrichment",
                            requires_approval=False,
                            data={
                                "error": "fairness_blocked_output",
                                "category": _fg_output.category,
                                "message": _fg_output.educational_message,
                            },
                        ),
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
        _stage_message = msg("jd_enrichment.enriched_fallback", title=_enriched_title, quality=_q_int)
    else:
        _stage_message = msg("jd_enrichment.enriched_ok", title=_enriched_title, quality=_q_int)

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
        "ws_stage_payload": build_ws_stage_payload(
            stage="jd_enrichment",
            completeness=calculate_completeness("jd_enrichment"),
            requires_approval=True,
            data={
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
        ),
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
            emit_audit_fire_and_forget(
                lambda: _audit.log_decision(
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
                )
            )
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

