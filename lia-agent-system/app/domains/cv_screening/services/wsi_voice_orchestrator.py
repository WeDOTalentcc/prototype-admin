"""
WSI Voice Orchestrator Service

Connects Twilio Voice screening with WSI (WeDoTalent Skill Index) scoring.
Orchestrates the complete voice screening workflow:
1. Generate WSI questions
2. Start Twilio voice call with questions
3. Process completed call transcript
4. Calculate WSI scores
"""

import json
import logging
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    build_transparency_extras_payload,
)
from app.domains.cv_screening.services.wsi_service import (
    Competency,
    ResponseAnalysis,
    WSIQuestion,
    WSIResult,
    wsi_service,
)
from app.shared.security.wsi_hashing import hash_response

logger = logging.getLogger(__name__)

_event_dispatcher = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


class VoiceScreeningRequest(BaseModel):
    """Request model for starting voice screening."""
    candidate_id: str
    job_vacancy_id: str
    competencies: list[dict[str, Any]]
    candidate_phone: str
    candidate_name: str
    job_title: str | None = None
    job_description: str | None = None
    mode: str = "compact"


class VoiceScreeningResult(BaseModel):
    """Result of starting a voice screening."""
    session_id: str
    call_id: str
    agent_id: str
    candidate_id: str
    job_vacancy_id: str
    status: str
    questions_generated: int


class WSIVoiceOrchestrator:
    """
    Orchestrates voice screening with WSI methodology.
    
    Flow:
    1. start_voice_screening: Generate questions → Create agent → Start call
    2. process_call_completed: Parse transcript → Analyze responses → Calculate WSI
    """
    
    def __init__(self):
        self.wsi_service = wsi_service
        logger.info("✅ WSI Voice Orchestrator initialized")
    
    # Audit task #496 (PR2) — função canônica movida para
    # `wsi_service/question_builder.py`. Shim mantém a API interna estável
    # para `start_voice_screening` (e qualquer subclasse de teste).
    def _convert_snapshot_to_wsi_questions(self, snapshot: list) -> list[WSIQuestion]:
        from .wsi_service.question_builder import convert_snapshot_to_wsi_questions
        return convert_snapshot_to_wsi_questions(snapshot)

    
    async def start_voice_screening(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        competencies: list[Competency],
        candidate_phone: str,
        candidate_name: str,
        job_title: str | None = None,
        job_description: str | None = None,
        seniority: str | None = None,
        mode: str = "compact",
        enriched_jd: dict | None = None,
        db: AsyncSession | None = None
    ) -> VoiceScreeningResult:
        """
        Start a voice screening session with WSI methodology.
        
        Steps:
        1. Generate WSI questions based on competencies
        2. Create WSI session with screening_type="voice"
        3. Initiate Twilio voice call with WSI questions
        4. Return session and call IDs
        
        Args:
            candidate_id: Internal candidate ID
            job_vacancy_id: Job vacancy ID
            competencies: List of competencies to assess
            candidate_phone: Candidate phone (format: +5511999999999)
            candidate_name: Candidate full name
            job_title: Optional job title for context
            job_description: Optional job description
            mode: "compact" (6-8 questions) or "compact_plus" (8-10)
            db: Optional AsyncSession - if not provided, creates own session
            
        Returns:
            VoiceScreeningResult with session_id, call_id, agent_id
        """
        logger.info(f"🎤 Starting WSI voice screening for {candidate_name} (candidate_id: {candidate_id})")
        
        session_id = f"system:{uuid.uuid4()}"
        
        async def _execute_with_db(session: AsyncSession) -> VoiceScreeningResult:
            try:
                from app.domains.cv_screening.services.screening_question_set_service import (
                    screening_question_set_service,
                )
                active_qs = await screening_question_set_service.get_active_version(session, job_vacancy_id)
                
                if active_qs and active_qs.questions_snapshot:
                    questions = self._convert_snapshot_to_wsi_questions(active_qs.questions_snapshot)
                    qs_version = active_qs.version
                    qs_id = str(active_qs.id)
                    logger.info(f"Using versioned question set v{qs_version} with {len(questions)} questions for voice screening")
                else:
                    questions = await self.wsi_service.generate_screening_questions(
                        competencies=competencies,
                        mode=mode,
                        job_description=job_description,
                        seniority=seniority,
                        enriched_jd=enriched_jd,
                    )
                    qs_version = None
                    qs_id = None
                    logger.info(f"No versioned question set found, generated {len(questions)} questions dynamically")
                
                logger.info(f"📝 {len(questions)} WSI questions ready for session {session_id}")

                await session.execute(text("""
                    INSERT INTO wsi_sessions (
                        id, candidate_id, job_vacancy_id, screening_type, mode, status, question_set_version, question_set_id
                    )
                    VALUES (:id, :candidate_id, :job_vacancy_id, :screening_type, :mode, :status, :question_set_version, :question_set_id)
                """), {
                    "id": session_id,
                    "candidate_id": candidate_id,
                    "job_vacancy_id": job_vacancy_id,
                    "screening_type": "voice",
                    "mode": mode,
                    "status": "in_progress",
                    "question_set_version": qs_version,
                    "question_set_id": qs_id,
                })
                
                for idx, question in enumerate(questions):
                    await session.execute(text("""
                        INSERT INTO wsi_questions (
                            id, session_id, competency, framework, question_type,
                            question_text, weight, expected_signals, scoring_criteria, sequence_order
                        )
                        VALUES (:id, :session_id, :competency, :framework, :question_type,
                                :question_text, :weight, :expected_signals::jsonb, :scoring_criteria::jsonb, :sequence_order)
                    """), {
                        "id": question.id,
                        "session_id": session_id,
                        "competency": question.competency,
                        "framework": question.framework,
                        "question_type": question.question_type,
                        "question_text": question.question_text,
                        "weight": question.weight,
                        "expected_signals": json.dumps(question.expected_signals),
                        "scoring_criteria": json.dumps({**question.scoring_criteria, "is_critical": getattr(question, "is_critical", False)}),
                        "sequence_order": idx + 1
                    })
                
                await session.commit()
                
                logger.info(f"💾 WSI session {session_id} saved to database")
                
                question_texts = [q.question_text for q in questions]
                list(set(c.name for c in competencies))
                
                from app.domains.communication.services.twilio_voice_service import twilio_voice_service
                call = await twilio_voice_service.start_screening_call(
                    candidate_phone=candidate_phone,
                    candidate_name=candidate_name,
                    candidate_id=candidate_id,
                    job_title=job_title or f"Vaga {job_vacancy_id}",
                    questions=question_texts,
                )
                
                agent_id = call.get("agent_id", "twilio")
                
                call_id = call.get("call_id")
                logger.info(f"📞 Started call: {call_id} to {candidate_name}")
                
                await session.execute(text("""
                    UPDATE wsi_sessions
                    SET call_id = :call_id, agent_id = :agent_id, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :session_id
                """), {
                    "call_id": call_id,
                    "agent_id": agent_id,
                    "session_id": session_id
                })
                
                await session.commit()
                
                logger.info(f"✅ Voice screening started - Session: {session_id}, Call: {call_id}")
                
                return VoiceScreeningResult(
                    session_id=session_id,
                    call_id=call_id,
                    agent_id=agent_id,
                    candidate_id=candidate_id,
                    job_vacancy_id=job_vacancy_id,
                    status="call_initiated",
                    questions_generated=len(questions)
                )
                
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.error(f"❌ Failed to start voice screening: {e}", exc_info=True)
                
                try:
                    await session.execute(text("""
                        UPDATE wsi_sessions SET status = 'cancelled'
                        WHERE id = :session_id
                    """), {"session_id": session_id})
                    await session.commit()
                except Exception:
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    pass
                
                raise
        
        if db is not None:
            return await _execute_with_db(db)
        else:
            async with AsyncSessionLocal() as session:
                return await _execute_with_db(session)
    
    async def process_call_completed(
        self,
        call_id: str,
        transcript: str,
        transcript_object: list[dict[str, Any]] | None = None,
        db: AsyncSession | None = None
    ) -> WSIResult | None:
        """
        Process a completed voice call and calculate WSI scores.
        
        Steps:
        1. Load WSI session linked to call_id
        2. Parse transcript into Q/A pairs
        3. Analyze each response using wsi_service
        4. Calculate final WSI scores
        5. Persist results to database
        
        Args:
            call_id: Voice call ID
            transcript: Full call transcript text
            transcript_object: Optional structured transcript with speaker labels
            db: Optional AsyncSession - if not provided, creates own session
            
        Returns:
            WSIResult with final scores, or None if session not found
        """
        logger.info(f"🔄 Processing completed call: {call_id}")
        
        # Audit task #496 (PR4) — pipeline linear. Cada etapa é um helper
        # privado isolado, mantendo `process_call_completed` legível como
        # uma sequência de passos de negócio (Load → Analyze → Score →
        # Persist → Dispatch).
        async def _execute_with_db(session: AsyncSession) -> WSIResult | None:
            session_meta = await self._load_session_for_call(session, call_id)
            if session_meta is None:
                return None
            session_id, candidate_id, job_vacancy_id, _mode = session_meta

            questions = await self._load_questions_for_session(session, session_id)
            if not questions:
                return None

            response_analyses, weights = await self._analyze_and_persist_responses(
                session=session,
                session_id=session_id,
                questions=questions,
                transcript=transcript,
                transcript_object=transcript_object,
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
            )
            if not response_analyses:
                await self._mark_session_cancelled(session, session_id)
                return None

            wsi_result = await self._persist_wsi_result(
                session=session,
                session_id=session_id,
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                response_analyses=response_analyses,
                weights=weights,
            )

            await self._dispatch_screening_completed_event(
                session=session,
                session_id=session_id,
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                wsi_result=wsi_result,
            )
            return wsi_result

        if db is not None:
            return await _execute_with_db(db)
        else:
            async with AsyncSessionLocal() as session:
                return await _execute_with_db(session)

    # ------------------------------------------------------------------
    # Audit task #496 (PR4) — helpers privados do pipeline de
    # `process_call_completed`. Cada um tem responsabilidade única e pode
    # ser testado isoladamente com uma `AsyncSession` mockada.
    # ------------------------------------------------------------------

    async def _load_session_for_call(
        self, session: AsyncSession, call_id: str
    ) -> tuple[str, str, str, str] | None:
        """SELECT da sessão WSI vinculada ao `call_id`. Retorna a tupla
        (session_id, candidate_id, job_vacancy_id, mode) ou `None` se
        não existir."""
        result = await session.execute(
            text(
                "SELECT id, candidate_id, job_vacancy_id, mode "
                "FROM wsi_sessions WHERE call_id = :call_id"
            ),
            {"call_id": call_id},
        )
        row = result.fetchone()
        if not row:
            logger.warning(f"⚠️  No WSI session found for call_id: {call_id}")
            return None
        session_id, candidate_id, job_vacancy_id, mode = row
        logger.info(
            f"📋 Found WSI session: {session_id} for candidate: {candidate_id}"
        )
        return session_id, candidate_id, job_vacancy_id, mode

    async def _load_questions_for_session(
        self, session: AsyncSession, session_id: str
    ) -> list[WSIQuestion]:
        """SELECT das perguntas persistidas + parsing dos campos JSON
        (`expected_signals`, `scoring_criteria`) que podem chegar como
        string crua dependendo do driver."""
        questions_result = await session.execute(
            text(
                """
                SELECT id, competency, framework, question_type, question_text, weight,
                       expected_signals, scoring_criteria, sequence_order
                FROM wsi_questions
                WHERE session_id = :session_id
                ORDER BY sequence_order
                """
            ),
            {"session_id": session_id},
        )
        rows = questions_result.fetchall()
        if not rows:
            logger.error(f"❌ No questions found for session: {session_id}")
            return []

        questions: list[WSIQuestion] = []
        for row in rows:
            expected_signals = row[6]
            if isinstance(expected_signals, str):
                expected_signals = (
                    json.loads(expected_signals) if expected_signals else []
                )
            elif not isinstance(expected_signals, list):
                expected_signals = []

            scoring_criteria = row[7]
            if isinstance(scoring_criteria, str):
                scoring_criteria = (
                    json.loads(scoring_criteria) if scoring_criteria else {}
                )
            elif not isinstance(scoring_criteria, dict):
                scoring_criteria = {}

            questions.append(
                WSIQuestion(
                    id=row[0],
                    competency=row[1],
                    framework=row[2],
                    question_type=row[3],
                    question_text=row[4],
                    weight=float(row[5]),
                    expected_signals=expected_signals,
                    scoring_criteria=scoring_criteria,
                )
            )
        logger.info(f"📝 Loaded {len(questions)} questions for analysis")
        return questions

    async def _analyze_and_persist_responses(
        self,
        session: AsyncSession,
        session_id: str,
        questions: list[WSIQuestion],
        transcript: str,
        transcript_object: list[dict[str, Any]] | None,
        candidate_id: str | None = None,
        job_vacancy_id: str | None = None,
    ) -> tuple[list[ResponseAnalysis], dict[str, float]]:
        """Para cada Q/A extraído do transcript, invoca o `wsi_service.analyze_response`,
        persiste a análise em `wsi_response_analyses` e devolve a lista
        agregada + mapa de pesos.

        Falhas individuais não derrubam o pipeline: cai num
        `ResponseAnalysis` de fallback com `category` derivada do framework
        (audit #498) para preservar o split técnico/comportamental
        determinístico no scoring.
        """
        qa_pairs = self._extract_qa_pairs(
            transcript=transcript,
            transcript_object=transcript_object,
            questions=questions,
        )
        logger.info(f"🔍 Extracted {len(qa_pairs)} Q/A pairs from transcript")

        response_analyses: list[ResponseAnalysis] = []
        weights: dict[str, float] = {}

        # Task #511 round 3 — resolve company_id uma única vez via FK do job
        # vacancy para enriquecer o audit trail (wsi_responses.company_id).
        # Mantemos opcional: se faltar job_vacancy_id (call site legado),
        # gravamos NULL ao invés de quebrar.
        company_id: str | None = None
        if job_vacancy_id:
            row = (await session.execute(
                text("SELECT company_id FROM job_vacancies WHERE id = :jv"),
                {"jv": job_vacancy_id},
            )).first()
            if row:
                company_id = str(row[0])

        for qa in qa_pairs:
            question: WSIQuestion = qa["question"]
            response_text: str = qa["response"]
            logger.debug(f"Analyzing response for: {question.competency}")

            # Round 3 (audit comment): isolamos a chamada à LLM em try/except
            # — falhas de análise caem no fallback determinístico (audit
            # #498). Mas as escritas de auditoria (wsi_responses +
            # wsi_response_analyses) ficam FORA do try: depois que houve
            # análise bem-sucedida, persistir o hash é OBRIGATÓRIO para
            # compliance EU AI Act Art. 12. Falha de DB aborta a transação.
            try:
                # Audit task #532 (G23-04) — propaga contexto para que a
                # Camada 2 grave consumo em `AiConsumption` (chave de
                # cobrança por uso). Sem company_id, o tracking vira no-op.
                tracking_ctx = {
                    "company_id": company_id,
                    "candidate_id": candidate_id,
                    "vacancy_id": job_vacancy_id,
                    "session_id": session_id,
                    "operation": "wsi_layer2_extract",
                } if company_id else None
                analysis = await self.wsi_service.analyze_response(
                    question=question,
                    response=response_text,
                    tracking_context=tracking_ctx,
                )
            except Exception as e:
                logger.error(
                    f"⚠️  Failed to analyze response for {question.competency}: {e}"
                )
                # Audit task #498 — mesmo no fallback de erro, derivamos a
                # categoria a partir do framework da pergunta para que o
                # split tech/behavioral permaneça determinístico.
                from app.domains.cv_screening.services.wsi_service.response_analyzer import (
                    _category_from_framework,
                )
                response_analyses.append(
                    ResponseAnalysis(
                        question_id=question.id,
                        competency=question.competency,
                        response_text=response_text,
                        final_score=2.5,
                        evidences=["Análise parcial - falha no processamento"],
                        red_flags=["Análise incompleta"],
                        justification=(
                            "Análise automatizada falhou. Requer revisão manual."
                        ),
                        category=_category_from_framework(question.framework),
                    )
                )
                weights[question.competency] = question.weight

                # Round 3 (audit comment): mesmo no fallback de análise,
                # persistimos a trilha imutável (wsi_responses) com o
                # response_text bruto do candidato. EU AI Act Art. 12 exige
                # que TODA resposta do candidato seja auditável — falha
                # da análise não pode justificar perda da trilha.
                resp_hash_fb = hash_response(response_text, session_id, question.id)
                await session.execute(
                    text(
                        """
                        INSERT INTO wsi_responses (
                            session_id, question_id, raw_text, response_hash,
                            candidate_id, company_id
                        )
                        VALUES (:session_id, :question_id, :raw_text, :response_hash,
                                :candidate_id, :company_id)
                        """
                    ),
                    {
                        "session_id": session_id,
                        "question_id": question.id,
                        "raw_text": response_text or "",
                        "response_hash": resp_hash_fb,
                        "candidate_id": candidate_id,
                        "company_id": company_id,
                    },
                )
                continue

            # Sucesso da análise — append + persistência FAIL-FAST.
            response_analyses.append(analysis)
            weights[question.competency] = question.weight

            # Task #511 — EU AI Act Art. 12 / LGPD Art. 20 audit trail.
            # Hash determinístico calculado UMA vez e gravado em ambas
            # tabelas (wsi_responses + wsi_response_analyses). Falhas de
            # DB aqui propagam (FAIL-FAST) — trilha de auditoria de IA de
            # Alto Risco não pode ser silenciosamente perdida.
            resp_hash = hash_response(
                analysis.response_text, session_id, question.id
            )
            await session.execute(
                text(
                    """
                    INSERT INTO wsi_responses (
                        session_id, question_id, raw_text, response_hash,
                        candidate_id, company_id
                    )
                    VALUES (:session_id, :question_id, :raw_text, :response_hash,
                            :candidate_id, :company_id)
                    """
                ),
                {
                    "session_id": session_id,
                    "question_id": question.id,
                    "raw_text": analysis.response_text or "",
                    "response_hash": resp_hash,
                    "candidate_id": candidate_id,
                    "company_id": company_id,
                },
            )
            await session.execute(
                text(
                    """
                    INSERT INTO wsi_response_analyses (
                        id, session_id, question_id, competency, response_text,
                        autodeclaration_score, context_score, bloom_level, dreyfus_level,
                        evidences, red_flags, consistency_penalty, final_score, justification,
                        response_hash, transparency_extras
                    )
                    VALUES (:id, :session_id, :question_id, :competency, :response_text,
                            :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level,
                            :evidences::jsonb, :red_flags::jsonb, :consistency_penalty, :final_score, :justification,
                            :response_hash, :transparency_extras::jsonb)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "question_id": question.id,
                    "competency": analysis.competency,
                    "response_text": analysis.response_text,
                    "autodeclaration_score": analysis.autodeclaration_score,
                    "context_score": analysis.context_score,
                    "bloom_level": analysis.bloom_level,
                    "dreyfus_level": analysis.dreyfus_level,
                    "evidences": json.dumps(analysis.evidences),
                    "red_flags": json.dumps(analysis.red_flags),
                    "consistency_penalty": analysis.consistency_penalty,
                    "final_score": analysis.final_score,
                    "justification": analysis.justification,
                    "response_hash": resp_hash,
                    # Audit task #528 (G23-02 / G23-03) — transparência LGPD/EU AI Act.
                    # Audit task #534 — payload construído via helper canônico para
                    # manter o formato em sincronia com o backfill histórico.
                    "transparency_extras": json.dumps(
                        build_transparency_extras_payload(
                            analysis,
                            layer2_degraded_reason=analysis.layer2_degraded_reason,
                        )
                    ),
                },
            )
            logger.info(
                f"✅ Analyzed {question.competency}: Score {analysis.final_score}/5"
            )

        return response_analyses, weights

    async def _mark_session_cancelled(
        self, session: AsyncSession, session_id: str
    ) -> None:
        """Marca a sessão como `cancelled` quando não foi possível gerar
        nenhuma análise — evita deixar a sessão presa em `in_progress`."""
        logger.error(
            f"❌ No response analyses generated for session: {session_id}"
        )
        await session.execute(
            text(
                "UPDATE wsi_sessions SET status = 'cancelled' WHERE id = :session_id"
            ),
            {"session_id": session_id},
        )
        await session.commit()

    async def _persist_wsi_result(
        self,
        session: AsyncSession,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        response_analyses: list[ResponseAnalysis],
        weights: dict[str, float],
    ) -> WSIResult:
        """Calcula o WSI agregado, persiste em `wsi_results`, marca a
        sessão como `completed` e devolve o resultado."""
        wsi_result = self.wsi_service.calculate_wsi(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            responses=response_analyses,
            weights=weights,
        )

        logger.info(
            f"🎯 WSI Calculated - Technical: {wsi_result.technical_wsi}, "
            f"Behavioral: {wsi_result.behavioral_wsi}, Overall: {wsi_result.overall_wsi}"
        )

        await session.execute(
            text(
                """
                INSERT INTO wsi_results (
                    id, session_id, candidate_id, job_vacancy_id,
                    technical_wsi, behavioral_wsi, overall_wsi, classification, percentile
                )
                VALUES (:id, :session_id, :candidate_id, :job_vacancy_id,
                        :technical_wsi, :behavioral_wsi, :overall_wsi, :classification, :percentile)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "technical_wsi": wsi_result.technical_wsi,
                "behavioral_wsi": wsi_result.behavioral_wsi,
                "overall_wsi": wsi_result.overall_wsi,
                "classification": wsi_result.classification,
                "percentile": wsi_result.percentile,
            },
        )

        await session.execute(
            text(
                "UPDATE wsi_sessions "
                "SET status = 'completed', completed_at = CURRENT_TIMESTAMP "
                "WHERE id = :session_id"
            ),
            {"session_id": session_id},
        )
        await session.commit()

        logger.info(f"✅ WSI Voice Screening completed for session {session_id}")
        logger.info(f"   Classification: {wsi_result.classification.upper()}")
        logger.info(f"   Overall WSI: {wsi_result.overall_wsi}/5.0")
        return wsi_result

    async def _dispatch_screening_completed_event(
        self,
        session: AsyncSession,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        wsi_result: WSIResult,
    ) -> None:
        """Publica `screening-completed` para os consumidores downstream
        (automation handlers, recommendation engine etc). Falha no
        dispatch é absorvida — a triagem em si já foi persistida com
        sucesso e não pode ser revertida por um event broker indisponível."""
        try:
            company_id = await self._get_company_id_for_vacancy(
                session, job_vacancy_id
            )
            dispatcher = get_event_dispatcher()
            await dispatcher.on_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=job_vacancy_id,
                company_id=company_id,
                wsi_scores={
                    "technical_wsi": wsi_result.technical_wsi,
                    "behavioral_wsi": wsi_result.behavioral_wsi,
                    "overall_wsi": wsi_result.overall_wsi,
                },
                screening_type="voice_wsi",
                passed=wsi_result.classification in ["strong", "recommended"],
                classification=wsi_result.classification,
                session_id=str(session_id),
            )
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to dispatch screening-completed event: {e}"
            )
    
    # Audit task #496 (PR3) — acesso a dados extraído para
    # `wsi_service/session_repository.py`. Shim mantém a API interna
    # estável para `process_call_completed`.
    async def _get_company_id_for_vacancy(self, session: AsyncSession, job_vacancy_id: str) -> str:
        from .wsi_service.session_repository import get_company_id_for_vacancy
        return await get_company_id_for_vacancy(session, job_vacancy_id)

    
    # Audit task #496 (PR1) — funções de extração foram movidas para
    # `wsi_service/transcript_extractor.py` (puras, testáveis isoladas).
    # Mantemos shims de instância chamando as funções módulo-nível para
    # preservar 100% da API interna usada por `process_call_completed`.
    def _extract_qa_pairs(
        self,
        transcript: str,
        transcript_object: list[dict[str, Any]] | None,
        questions: list[WSIQuestion],
    ) -> list[dict[str, Any]]:
        from .wsi_service.transcript_extractor import extract_qa_pairs
        return extract_qa_pairs(transcript, transcript_object, questions)

    # Audit task #496 (PR3) — leitura de sessão extraída para
    # `wsi_service/session_repository.py`. A API pública (`db` opcional)
    # é preservada: o orquestrador continua sendo o único ponto que
    # decide entre usar a sessão recebida ou abrir uma própria.
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get current status of a voice screening session."""
        from .wsi_service.session_repository import get_session_status as _repo_get_status

        if db is not None:
            return await _repo_get_status(db, session_id)
        async with AsyncSessionLocal() as session:
            return await _repo_get_status(session, session_id)

    async def get_session_by_call_id(
        self,
        call_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get session by voice call ID."""
        from .wsi_service.session_repository import get_session_by_call_id as _repo_get_by_call

        if db is not None:
            return await _repo_get_by_call(db, call_id)
        async with AsyncSessionLocal() as session:
            return await _repo_get_by_call(session, call_id)


wsi_voice_orchestrator = WSIVoiceOrchestrator()
