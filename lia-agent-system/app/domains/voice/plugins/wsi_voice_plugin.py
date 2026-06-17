"""
WSIVoicePlugin — domain-specific WSI screening behavior (Sprint 3.3).

Implements VoiceCorePlugin for the canonical WSI (Work Sample Inventory)
flow: register WSI session in DB, generate competency-based questions, load
them during the call, and surface as next-question candidates.

Audit 2026-05-22 (AUDIT_VOICE_SCREENING_ORCHESTRATOR.md secao 9.1): Sprint 3.3
extrai a logica WSI do monolito voice_screening_orchestrator.py — antes
hardcoded em 3 metodos da classe orchestrator (_register_wsi_session,
_generate_and_store_wsi_questions, _load_wsi_questions_for_session) — para
este plugin separado, permitindo coexistir com plugins de outros dominios
(BigFive, custom agents) no futuro.

Backward compat: VoiceScreeningOrchestrator pre-instala esta plugin no __init__
e mantem 3 thin delegate methods (_register_wsi_session etc.) que chamam para
ca, preservando `patch.object(orch, '_register_wsi_session')` em ~240 tests.

Hooks implementados
───────────────────
- on_session_initiated: registra wsi_session em DB + gera/persiste perguntas
  via screening_question_set_service (versioned) OU WSIService dinamico
  (fallback competencias default). LGPD Art. 20 audit log via
  log_automated_decision (silent_on_persist_error=True — voice e fire-and-forget).
- get_next_question: le wsi_questions table; retorna list[0] (chamador faz
  pop-and-track via session.questions_asked). Sprint 3.3 retorna None: legacy
  scripted-question flow continua via _get_next_scripted_question.
- on_session_finalized: Sprint 3.3 retorna {} (finalize_screening continua
  usando inline _WSIVoiceOrchestrator + _analyze_voice_screening; F-17 strategy
  PRIMARY/FALLBACK/SKIP nao precisa ainda virar plugin).

Constructor recebe `orchestrator` reference para reuso de helpers compartilhados
(`_fetch_job_context_from_db` — multi-tenancy enforcement com session.company_id).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.core.config import settings
from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

if TYPE_CHECKING:
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceCoreOrchestrator,
        VoiceScreeningSession,
    )

logger = logging.getLogger(__name__)


class WSIVoicePlugin(VoiceCorePlugin):
    """
    VoiceCorePlugin implementing the canonical WSI screening flow.

    Owns the 3 WSI methods historically embedded in VoiceScreeningOrchestrator:
    1. _register_wsi_session_impl: upsert wsi_sessions row + delegate question gen
    2. _generate_and_store_wsi_questions_impl: versioned OR dynamic question
       generation with LGPD audit log
    3. _load_wsi_questions_for_session_impl: read wsi_questions table

    Plugin instance is bound to a VoiceCoreOrchestrator (typically
    VoiceScreeningOrchestrator) to access shared helpers like
    _fetch_job_context_from_db (multi-tenancy-aware).
    """

    def __init__(self, orchestrator: "VoiceCoreOrchestrator | None" = None):
        # Optional orchestrator reference for callbacks (e.g., job context lookup).
        # When None, those code paths gracefully skip (best-effort).
        self._orchestrator = orchestrator

    @property
    def plugin_name(self) -> str:
        return "wsi_screening"

    # ── VoiceCorePlugin protocol implementations ───────────────────────────

    async def on_session_initiated(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """Register WSI session + generate questions when call/voip starts."""
        if db is None:
            return
        await self._register_wsi_session_impl(session, db)

    async def get_next_question(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> str | None:
        """
        Sprint 3.3: returns None (defers to legacy scripted-question flow).

        The core's generate_lia_response still uses `_get_next_scripted_question`
        with wsi_questions loaded inline via `_load_wsi_questions_for_session`.
        Promoting that to a plugin-driven flow is Sprint 3.5+ scope.
        """
        return None

    async def on_session_finalized(
        self,
        session: "VoiceScreeningSession",
        db: Any,
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Sprint 3.3: returns empty dict (defers to legacy finalize_screening).

        finalize_screening still uses inline _WSIVoiceOrchestrator + F-17 strategy
        (PRIMARY/FALLBACK/SKIP). Promoting that to plugin-driven completion is
        Sprint 3.5+ scope.
        """
        return {}

    # ── Internal WSI implementations (extracted from orchestrator) ─────────
    #
    # These were the 3 methods on VoiceScreeningOrchestrator pre-Sprint 3.3.
    # Logic is verbatim — only `self` (orchestrator) calls became
    # `self._orchestrator` (the bound parent reference).

    async def _register_wsi_session_impl(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """
        Register Twilio call in wsi_sessions table and generate WSI questions.

        1. Creates wsi_sessions row with call_id = Twilio call_sid
        2. Tries to load versioned question set for the job vacancy
        3. If none, generates WSI questions dynamically via wsi_service
        4. Inserts questions into wsi_questions table for use during the call

        Schema: wsi_sessions(id, candidate_id, job_vacancy_id, mode, call_id, status)
        """
        try:
            # F-13 (audit 2026-05-22): canonical write via WsiRepository (ADR-001).
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            await WsiRepository(db).upsert_voice_session(
                session_id=session.session_id,
                candidate_id=session.candidate_id,
                job_vacancy_id=session.job_id or session.session_id,
                mode="compact",
                call_id=session.call_sid,
                status="in_progress",
            )
            await db.commit()
            logger.info(
                "[VOICE SCREENING] WSI session registered: session=%s call_sid=%s",
                session.session_id,
                session.call_sid,
            )

            # Fetch job context eagerly so LIA can present the vaga from the first turn.
            # Sprint 3.3: delegate to bound orchestrator's helper (multi-tenancy preserved).
            if session.job_context is None and session.job_id and self._orchestrator is not None:
                session.job_context = await self._orchestrator._fetch_job_context_from_db(
                    session.job_id, db, company_id=session.company_id
                )

            await self._generate_and_store_wsi_questions_impl(session, db)

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning(
                "[VOICE SCREENING] Failed to register WSI session (non-blocking): %s", e
            )

    async def _generate_and_store_wsi_questions_impl(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """
        Generate WSI questions for a voice session and store them in wsi_questions table.

        Tries (in order):
        1. Load versioned question set for the job vacancy
        2. Generate questions dynamically via WSI service using job title as context
        """
        try:
            existing = await self._load_wsi_questions_for_session_impl(session.session_id, db)
            if existing:
                logger.info(
                    "[VOICE SCREENING] WSI questions already exist for session=%s (%d questions)",
                    session.session_id, len(existing),
                )
                return

            question_texts = []
            try:
                from app.domains.cv_screening.services.screening_question_set_service import (
                    screening_question_set_service,
                )
                job_vacancy_id = session.job_id or session.session_id
                active_qs = await screening_question_set_service.get_active_version(db, job_vacancy_id)
                if active_qs and active_qs.questions_snapshot:
                    question_texts = [
                        q.get("question_text", q.get("text", ""))
                        for q in active_qs.questions_snapshot
                        if q.get("question_text") or q.get("text")
                    ]
                    logger.info(
                        "[VOICE SCREENING] Loaded %d questions from versioned set v%s for session=%s",
                        len(question_texts), active_qs.version, session.session_id,
                    )
            except Exception as e:
                logger.debug(
                    "[VOICE SCREENING] Versioned question set not available: %s", e
                )

            if not question_texts:
                try:
                    from app.domains.cv_screening.services.wsi_service import Competency, WSIService
                    wsi_svc = WSIService()
                    default_competencies = [
                        Competency(name="Experiência Relevante", type="technical", weight=0.3, seniority_level="pleno"),
                        Competency(name="Resolução de Problemas", type="behavioral", weight=0.25, seniority_level="pleno"),
                        Competency(name="Comunicação", type="behavioral", weight=0.2, seniority_level="pleno"),
                        Competency(name="Trabalho em Equipe", type="cultural", weight=0.15, seniority_level="pleno"),
                        Competency(name="Adaptabilidade", type="behavioral", weight=0.1, seniority_level="pleno"),
                    ]
                    wsi_questions = await wsi_svc.generate_screening_questions(
                        competencies=default_competencies,
                        mode="compact",
                        job_description=f"Vaga: {session.job_title}",
                    )
                    question_texts = [q.question_text for q in wsi_questions if q.question_text]
                    logger.info(
                        "[VOICE SCREENING] Generated %d WSI questions dynamically for session=%s",
                        len(question_texts), session.session_id,
                    )

                    # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
                    # Voice screening orchestrator default-competencies fallback.
                    # session.company_id e source canonical. silent_on_persist_error=True
                    # porque voice call e fire-and-forget critico — nao bloquear
                    # ligacao por audit gap.
                    try:
                        # TENANT-FALLBACK-OK: session is WSI voice session from upstream RLS-validated API gate
                        company_id = getattr(session, "company_id", None)
                        if company_id:
                            await log_automated_decision(
                                db=db,
                                company_id=str(company_id),
                                candidate_id=getattr(session, "candidate_id", None),
                                job_id=getattr(session, "job_id", None),
                                decision_type="wsi_voice_orchestrator",
                                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                explanation_text=(
                                    f'Voice screening orchestrator gerou {len(question_texts)} pergunta(s) '
                                    f'WSI dinamicamente para session {session.session_id} '
                                    f'(job_title={session.job_title}). Fallback default-competencies '
                                    f'(Experiencia, Resolucao, Comunicacao, Trabalho-em-Equipe, Adaptabilidade), '
                                    f'mode=compact. Versioned question set ausente.'
                                ),
                                criteria_used=[
                                    *[f"competency:{c.name}" for c in default_competencies],
                                    "seniority:pleno",
                                    "mode:compact",
                                    "screening_type:voice",
                                    "fallback:default_competencies",
                                ],
                                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                                confidence_score=None,
                                review_eligible=True,
                                extra_metadata={
                                    "endpoint": "voice_screening_orchestrator._generate_and_store_wsi_questions",
                                    "session_id": session.session_id,
                                    "candidate_id": getattr(session, "candidate_id", None),
                                    "job_id": getattr(session, "job_id", None),
                                    "job_title": session.job_title,
                                    "questions_count": len(question_texts),
                                    "mode": "compact",
                                    "seniority": "pleno",
                                    "screening_type": "voice",
                                    "default_competencies_used": True,
                                    "prompt_template_version": "wsi_F6_pipeline_v2",
                                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                    "frameworks_used": sorted({q.framework for q in wsi_questions}),
                                },
                                silent_on_persist_error=True,  # voice call: nao bloquear
                            )
                        else:
                            logger.warning(
                                "WT-2022 P0.C wave 2: voice_screening_orchestrator sem session.company_id. "
                                "LGPD Art. 20 audit gap session_id=%s",
                                session.session_id,
                            )
                    except ValueError:
                        raise
                    except Exception as audit_err:
                        logger.error(
                            "WT-2022 P0.C wave 2: log_automated_decision falhou em "
                            "voice_screening_orchestrator session_id=%s: %s",
                            session.session_id, audit_err, exc_info=True,
                        )
                except Exception as e:
                    logger.warning(
                        "[VOICE SCREENING] WSI dynamic question generation failed for session=%s: %s — "
                        "Gemini will generate questions autonomously during the call",
                        session.session_id, e,
                    )
                    return

            if not question_texts:
                logger.info(
                    "[VOICE SCREENING] No WSI questions generated for session=%s — "
                    "Gemini will generate questions autonomously during the call",
                    session.session_id,
                )
                return

            # F-13 (audit 2026-05-22): canonical write via WsiRepository (ADR-001).
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            wsi_repo = WsiRepository(db)
            for idx, q_text in enumerate(question_texts):
                await wsi_repo.insert_voice_question(
                    question_id=str(uuid4()),
                    session_id=session.session_id,
                    competency="voice_screening",
                    framework="CBI",
                    question_type="behavioral",
                    question_text=q_text,
                    weight=1.0 / len(question_texts),
                    sequence_order=idx + 1,
                )
            await db.commit()
            logger.info(
                "[VOICE SCREENING] Stored %d WSI questions in DB for session=%s",
                len(question_texts), session.session_id,
            )

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning(
                "[VOICE SCREENING] WSI question generation/storage failed (non-blocking) session=%s: %s",
                session.session_id, e,
            )

    async def _load_wsi_questions_for_session_impl(
        self,
        session_id: str,
        db: Any,
    ) -> list[str]:
        """
        Load WSI question texts from wsi_questions table for the given session.

        Returns list of question_text strings ordered by sequence_order.
        Returns empty list if not found or DB unavailable (caller falls back
        to SCREENING_QUESTIONS_PT).
        """
        if db is None:
            return []
        try:
            # F-13 (audit 2026-05-22): canonical read via WsiRepository (ADR-001).
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            questions = await WsiRepository(db).list_question_texts_for_session(session_id)
            if questions:
                logger.info(
                    "[VOICE SCREENING] Loaded %d WSI questions from DB for session=%s",
                    len(questions), session_id,
                )
                return questions
        except Exception as e:
            logger.warning(
                "[VOICE SCREENING] Failed to load WSI questions for session=%s: %s",
                session_id, e,
            )
        return []
