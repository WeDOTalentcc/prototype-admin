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
from typing import Any

logger = logging.getLogger(__name__)

# Keys carried forward from context into wizard state
_CONTEXT_CARRY_KEYS = ("right_panel_form", "attached_file_text", "tenant_context_snippet")

# Stage-aware default responses (avoids empty string responses)
_STAGE_DEFAULTS: dict[str, str] = {
    "intake": "Captei a vaga. Vou seguir para o próximo passo.",
    "jd_enrichment": "Descrição da vaga enriquecida — preciso da sua aprovação.",
    "wsi_questions": "Perguntas de triagem WSI sugeridas — preciso da sua aprovação.",
    "completed": "Vaga criada com sucesso.",
}


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
        return state

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
        state = cls._build_state(
            thread_id=thread_id,
            user_message=user_message,
            user_id=user_id,
            company_id=company_id,
            session_id=session_id,
            context=context,
            prior_state=prior_state,
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
        if hasattr(wiz_g, "stream_invoke"):
            result, tokens_emitted = await wiz_g.stream_invoke(
                state, thread_id, on_token=on_token,
            )
        else:  # pragma: no cover — defensive: older deploy without stream_invoke
            result = await asyncio.to_thread(wiz_g.invoke, state, thread_id)

        if not isinstance(result, dict):
            return ("Vaga em criação — vamos seguir.", {}, tokens_emitted)

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


        stage_payload = result.get("ws_stage_payload") or {}
        stage_data = stage_payload.get("data") or {}
        current_stage = result.get("current_stage", "") or ""

        # Task #1080: Redis session marker upkeep removed. The canonical
        # ``is_wizard_session_active`` reads the checkpointer directly, so
        # there is nothing to mark/clear on each turn. Wizard "doneness" is
        # detected from ``current_stage == "completed"`` in the checkpoint.

        # T2 fix #5 (code review #4): quando o LLM gate (jd_gate_node) acabou
        # de classificar o turno do recrutador, a resposta contextual está em
        # ``state["gate_clarify_message"]``. Sem esta linha, o WS responde
        # com ``_STAGE_DEFAULTS["jd_enrichment"]`` ("Descrição da vaga
        # enriquecida — preciso da sua aprovação.") em LOOP — exatamente o
        # bug original que a Task #1085 promete corrigir. Preferência:
        # gate_clarify_message > stage_data.message > stage_data.response_text
        # > _STAGE_DEFAULTS. Aplicável APENAS quando o gate registrou um
        # intent neste turno (``gate_last_intent`` truthy) — fora do flow
        # do gate o comportamento legado é preservado.
        gate_msg = result.get("gate_clarify_message") if isinstance(result, dict) else None
        gate_intent = result.get("gate_last_intent") if isinstance(result, dict) else None
        if gate_msg and gate_intent:
            message = str(gate_msg)
        else:
            message = (
                stage_data.get("message")
                or stage_data.get("response_text")
                or _STAGE_DEFAULTS.get(current_stage, f"Etapa atual: {current_stage or 'wizard'}.")
            )
        return (message, stage_payload, tokens_emitted)
