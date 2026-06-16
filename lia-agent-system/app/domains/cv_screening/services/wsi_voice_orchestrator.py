# ADR-001-EXEMPT: wsi-tables write path (session.execute), migration to session_repository.py tracked in wsi-session-repo ticket.
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
import re
import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.runtime_context import RuntimeContext
from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)

from app.core.database import AsyncSessionLocal
from app.domains.cv_screening.services.wsi_service import (
    Competency,
    ResponseAnalysis,
    WSIQuestion,
    WSIResult,
    wsi_service,
)
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

_event_dispatcher = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


class VoiceScreeningRequest(WeDoBaseModel):
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
    
    def _convert_snapshot_to_wsi_questions(self, snapshot: list) -> list[WSIQuestion]:
        converted = []
        for idx, q in enumerate(snapshot):
            text = q.get("text", q.get("question", q.get("question_text", "")))
            if not text:
                continue
            category = q.get("category", "technical")
            framework_map = {
                "technical": "Bloom",
                "behavioral": "BigFive",
                "company": "CBI",
            }
            type_map = {
                "technical": "autodeclaration",
                "behavioral": "situational",
                "company": "contextual",
            }
            question = WSIQuestion(
                id=q.get("id", f"qs_{idx}"),
                competency=q.get("skill_targeted", q.get("competency_validated", category)),
                framework=framework_map.get(category, "Bloom"),
                question_type=type_map.get(category, "contextual"),
                question_text=text,
                weight=float(q.get("weight", 0.75)),
                expected_signals=q.get("expected_signals", []),
                scoring_criteria=q.get("scoring_criteria", {}),
            )
            converted.append(question)
        return converted
    
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
        # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
        logger.info(f"🎤 Starting WSI voice screening for {candidate_id} (candidate_id: {candidate_id})")
        
        session_id = f"system:{uuid.uuid4()}"
        
        async def _execute_with_db(session: AsyncSession) -> VoiceScreeningResult:
            ia_invoked_in_voice = False
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
                    ia_invoked_in_voice = True
                    logger.info(f"No versioned question set found, generated {len(questions)} questions dynamically")

                logger.info(f"📝 {len(questions)} WSI questions ready for session {session_id}")

                # RLS-EXEMPT: wsi_sessions — transitive via job_vacancy_id (migration 118)
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
                    # RLS-EXEMPT: wsi_questions — transitive via session
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

                # WT-2022 P0.C wave 2 / LGPD Art. 20 + EU AI Act Art. 13.
                # Voice screening orchestration. company_id vem do ContextVar
                # (RuntimeContext canonical pattern — service layer nao recebe
                # company_id por param). Se ContextVar vazio (chamado fora de
                # request HTTP, ex: triagem fire-and-forget), passa silent_on_persist_error
                # pra nao quebrar voice call. Log apenas quando houve invocacao IA
                # (snapshot ausente).
                if ia_invoked_in_voice:
                    try:
                        ctx = RuntimeContext.from_contextvars()
                        if ctx.company_id:
                            await log_automated_decision(
                                db=session,
                                company_id=ctx.company_id,
                                candidate_id=candidate_id,
                                job_id=job_vacancy_id,
                                decision_type="wsi_voice_generation",
                                ai_model_used=getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                explanation_text=(
                                    f'Gerou {len(questions)} pergunta(s) WSI dinamicamente para voice screening '
                                    f'session {session_id} (candidate={candidate_id}, job={job_vacancy_id}). '
                                    f'Mode={mode}, seniority={seniority}, job_title={job_title}. '
                                    f'Pipeline canonical via wsi_voice_orchestrator (CBI+Bloom+Dreyfus+BigFive). '
                                    f'Versioned question set ausente — fallback dinamico ativado.'
                                ),
                                criteria_used=[
                                    *[f"competency:{c.name}" for c in competencies],
                                    f"seniority:{seniority}",
                                    f"mode:{mode}",
                                    "screening_type:voice",
                                ],
                                criteria_ignored=list(PROTECTED_CRITERIA_PT),
                                confidence_score=None,
                                review_eligible=True,
                                extra_metadata={
                                    "endpoint": "wsi_voice_orchestrator.start_voice_screening",
                                    "session_id": session_id,
                                    "candidate_id": candidate_id,
                                    "job_vacancy_id": job_vacancy_id,
                                    "job_title": job_title,
                                    "questions_count": len(questions),
                                    "mode": mode,
                                    "seniority": seniority,
                                    "screening_type": "voice",
                                    "enriched_jd": bool(enriched_jd),
                                    "fallback_dynamic": True,
                                    "prompt_template_version": "wsi_F6_pipeline_v2",
                                    "llm_model": getattr(settings, "LLM_PRIMARY_MODEL", "claude-sonnet-4-6"),
                                    "frameworks_used": sorted({q.framework for q in questions}),
                                },
                                silent_on_persist_error=True,  # voice fire-and-forget
                            )
                        else:
                            logger.warning(
                                "WT-2022 P0.C wave 2: wsi_voice_orchestrator sem company_id no "
                                "ContextVar (fora de request HTTP). LGPD Art. 20 audit gap session_id=%s",
                                session_id,
                            )
                    except ValueError:
                        # Compliance gate raised — re-raise fail-loud per LGPD.
                        raise
                    except Exception as audit_err:
                        logger.error(
                            "WT-2022 P0.C wave 2: log_automated_decision falhou em "
                            "wsi_voice_orchestrator.start_voice_screening session_id=%s: %s",
                            session_id, audit_err, exc_info=True,
                        )

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
                logger.info(f"📞 Started call: {call_id} to {candidate_id}")
                
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
        
        async def _execute_with_db(session: AsyncSession) -> WSIResult | None:
            result = await session.execute(text("""
                SELECT id, candidate_id, job_vacancy_id, mode
                FROM wsi_sessions
                WHERE call_id = :call_id
            """), {"call_id": call_id})
            
            row = result.fetchone()
            
            if not row:
                logger.warning(f"⚠️  No WSI session found for call_id: {call_id}")
                return None
            
            session_id, candidate_id, job_vacancy_id, mode = row
            
            logger.info(f"📋 Found WSI session: {session_id} for candidate: {candidate_id}")
            
            questions_result = await session.execute(text("""
                SELECT id, competency, framework, question_type, question_text, weight, 
                       expected_signals, scoring_criteria, sequence_order
                FROM wsi_questions
                WHERE session_id = :session_id
                ORDER BY sequence_order
            """), {"session_id": session_id})
            
            questions_rows = questions_result.fetchall()
            
            if not questions_rows:
                logger.error(f"❌ No questions found for session: {session_id}")
                return None
            
            questions = []
            for row in questions_rows:
                expected_signals = row[6]
                if isinstance(expected_signals, str):
                    expected_signals = json.loads(expected_signals) if expected_signals else []
                elif not isinstance(expected_signals, list):
                    expected_signals = []
                    
                scoring_criteria = row[7]
                if isinstance(scoring_criteria, str):
                    scoring_criteria = json.loads(scoring_criteria) if scoring_criteria else {}
                elif not isinstance(scoring_criteria, dict):
                    scoring_criteria = {}
                
                q = WSIQuestion(
                    id=row[0],
                    competency=row[1],
                    framework=row[2],
                    question_type=row[3],
                    question_text=row[4],
                    weight=float(row[5]),
                    expected_signals=expected_signals,
                    scoring_criteria=scoring_criteria
                )
                questions.append(q)
            
            logger.info(f"📝 Loaded {len(questions)} questions for analysis")
            
            qa_pairs = self._extract_qa_pairs(
                transcript=transcript,
                transcript_object=transcript_object,
                questions=questions
            )
            
            logger.info(f"🔍 Extracted {len(qa_pairs)} Q/A pairs from transcript")
            
            response_analyses = []
            weights = {}
            
            for qa in qa_pairs:
                question = qa['question']
                response_text = qa['response']
                
                logger.debug(f"Analyzing response for: {question.competency}")
                
                try:
                    analysis = await self.wsi_service.analyze_response(
                        question=question,
                        response=response_text
                    )
                    
                    response_analyses.append(analysis)
                    weights[question.competency] = question.weight
                    
                    analysis_id = str(uuid.uuid4())
                    # RLS-EXEMPT: wsi_response_analyses — transitive via session
                    await session.execute(text("""
                        INSERT INTO wsi_response_analyses (
                            id, session_id, question_id, competency, response_text,
                            autodeclaration_score, context_score, bloom_level, dreyfus_level,
                            evidences, red_flags, consistency_penalty, final_score, justification
                        )
                        VALUES (:id, :session_id, :question_id, :competency, :response_text,
                                :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level,
                                :evidences::jsonb, :red_flags::jsonb, :consistency_penalty, :final_score, :justification)
                    """), {
                        "id": analysis_id,
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
                        "justification": analysis.justification
                    })
                    
                    logger.info(f"✅ Analyzed {question.competency}: Score {analysis.final_score}/5")
                    
                except Exception as e:
                    logger.error(f"⚠️  Failed to analyze response for {question.competency}: {e}")
                    fallback_analysis = ResponseAnalysis(
                        question_id=question.id,
                        competency=question.competency,
                        response_text=response_text,
                        final_score=2.5,
                        evidences=["Análise parcial - falha no processamento"],
                        red_flags=["Análise incompleta"],
                        justification="Análise automatizada falhou. Requer revisão manual."
                    )
                    response_analyses.append(fallback_analysis)
                    weights[question.competency] = question.weight
            
            if not response_analyses:
                logger.error(f"❌ No response analyses generated for session: {session_id}")
                await session.execute(text("""
                    UPDATE wsi_sessions SET status = 'cancelled'
                    WHERE id = :session_id
                """), {"session_id": session_id})
                await session.commit()
                return None
            
            wsi_result = self.wsi_service.calculate_wsi(
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                responses=response_analyses,
                weights=weights
            )
            
            logger.info(f"🎯 WSI Calculated - Technical: {wsi_result.technical_wsi}, "
                       f"Behavioral: {wsi_result.behavioral_wsi}, Overall: {wsi_result.overall_wsi}")
            
            result_id = str(uuid.uuid4())
            # RLS-EXEMPT: wsi_results — transitive via session
            await session.execute(text("""
                INSERT INTO wsi_results (
                    id, session_id, candidate_id, job_vacancy_id,
                    technical_wsi, behavioral_wsi, overall_wsi, classification, percentile
                )
                VALUES (:id, :session_id, :candidate_id, :job_vacancy_id,
                        :technical_wsi, :behavioral_wsi, :overall_wsi, :classification, :percentile)
            """), {
                "id": result_id,
                "session_id": session_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "technical_wsi": wsi_result.technical_wsi,
                "behavioral_wsi": wsi_result.behavioral_wsi,
                "overall_wsi": wsi_result.overall_wsi,
                "classification": wsi_result.classification,
                "percentile": wsi_result.percentile
            })
            
            await session.execute(text("""
                UPDATE wsi_sessions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
            """), {"session_id": session_id})
            
            await session.commit()
            
            logger.info(f"✅ WSI Voice Screening completed for session {session_id}")
            logger.info(f"   Classification: {wsi_result.classification.upper()}")
            logger.info(f"   Overall WSI: {wsi_result.overall_wsi}/5.0")
            
            try:
                company_id = await self._get_company_id_for_vacancy(session, job_vacancy_id)
                
                dispatcher = get_event_dispatcher()
                await dispatcher.on_screening_completed(
                    candidate_id=candidate_id,
                    vacancy_id=job_vacancy_id,
                    company_id=company_id,
                    wsi_scores={
                        "technical_wsi": wsi_result.technical_wsi,
                        "behavioral_wsi": wsi_result.behavioral_wsi,
                        "overall_wsi": wsi_result.overall_wsi
                    },
                    screening_type="voice_wsi",
                    passed=wsi_result.classification in ["strong", "recommended"],
                    classification=wsi_result.classification,
                    session_id=str(session_id)
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to dispatch screening-completed event: {e}")
            
            return wsi_result
        
        if db is not None:
            return await _execute_with_db(db)
        else:
            async with AsyncSessionLocal() as session:
                return await _execute_with_db(session)
    
    async def _get_company_id_for_vacancy(self, session: AsyncSession, job_vacancy_id: str) -> str:
        """
        Get the company_id for a vacancy from the database.
        
        Args:
            session: Database session
            job_vacancy_id: Job vacancy ID
            
        Returns:
            Company ID as string, or "unknown" if not found
        """
        try:
            result = await session.execute(text("""
                SELECT company_id FROM job_vacancies WHERE id = :vacancy_id
            """), {"vacancy_id": job_vacancy_id})
            
            row = result.fetchone()
            if row and row[0]:
                return str(row[0])
            
            logger.warning(f"⚠️ No company_id found for vacancy {job_vacancy_id}")
            return "unknown"
        except Exception as e:
            logger.warning(f"⚠️ Error fetching company_id for vacancy {job_vacancy_id}: {e}")
            return "unknown"
    
    def _build_job_context_from_competencies(self, competencies: list[Competency]) -> str:
        """Build job context string from competencies for voice screening."""
        technical = [c.name for c in competencies if c.type == "technical"]
        behavioral = [c.name for c in competencies if c.type == "behavioral"]
        cultural = [c.name for c in competencies if c.type == "cultural"]
        
        context = "Competências avaliadas:\n"
        
        if technical:
            context += f"\nTécnicas: {', '.join(technical)}"
        if behavioral:
            context += f"\nComportamentais: {', '.join(behavioral)}"
        if cultural:
            context += f"\nCulturais: {', '.join(cultural)}"
        
        return context
    
    def _extract_qa_pairs(
        self,
        transcript: str,
        transcript_object: list[dict[str, Any]] | None,
        questions: list[WSIQuestion]
    ) -> list[dict[str, Any]]:
        """
        Extract Question/Answer pairs from transcript.
        
        Strategy:
        1. If transcript_object available, use speaker labels
        2. Otherwise, use fuzzy matching to find questions in transcript
        3. Match each question with subsequent candidate response
        
        Returns:
            List of dicts with 'question' and 'response' keys
        """
        qa_pairs = []
        
        if transcript_object and len(transcript_object) > 0:
            qa_pairs = self._extract_from_structured_transcript(transcript_object, questions)
        
        if not qa_pairs:
            qa_pairs = self._extract_from_raw_transcript(transcript, questions)
        
        return qa_pairs
    
    def _extract_from_structured_transcript(
        self,
        transcript_object: list[dict[str, Any]],
        questions: list[WSIQuestion]
    ) -> list[dict[str, Any]]:
        """Extract Q/A pairs from structured transcript with speaker labels."""
        qa_pairs = []
        
        agent_utterances = []
        user_utterances = []
        
        for item in transcript_object:
            speaker = item.get('speaker', item.get('role', '')).lower()
            text_content = item.get('text', item.get('content', ''))
            
            if 'agent' in speaker or 'lia' in speaker or 'assistant' in speaker:
                agent_utterances.append({
                    'text': text_content,
                    'index': len(agent_utterances)
                })
            elif 'user' in speaker or 'human' in speaker or 'candidato' in speaker:
                user_utterances.append({
                    'text': text_content,
                    'agent_index': len(agent_utterances) - 1 if agent_utterances else -1
                })
        
        for question in questions:
            best_match_idx = -1
            best_score = 0.3
            
            q_words = set(question.question_text.lower().split())
            
            for idx, utterance in enumerate(agent_utterances):
                u_words = set(utterance['text'].lower().split())
                
                if len(q_words) > 0:
                    overlap = len(q_words & u_words) / len(q_words)
                    if overlap > best_score:
                        best_score = overlap
                        best_match_idx = idx
            
            if best_match_idx >= 0:
                response_parts = []
                for u in user_utterances:
                    if u.get('agent_index') == best_match_idx:
                        response_parts.append(u.get('text', ''))
                
                if response_parts:
                    qa_pairs.append({
                        'question': question,
                        'response': ' '.join(response_parts)
                    })
        
        return qa_pairs
    
    def _extract_from_raw_transcript(
        self,
        transcript: str,
        questions: list[WSIQuestion]
    ) -> list[dict[str, Any]]:
        """Extract Q/A pairs from raw transcript using pattern matching."""
        qa_pairs = []
        
        if not transcript or not transcript.strip():
            return qa_pairs
        
        transcript_lower = transcript.lower()
        
        for question in questions:
            q_text_lower = question.question_text.lower()
            q_words = q_text_lower.split()[:6]
            search_pattern = ' '.join(q_words)
            
            q_position = transcript_lower.find(search_pattern)
            
            if q_position == -1 and len(q_words) > 3:
                search_pattern = ' '.join(q_words[:3])
                q_position = transcript_lower.find(search_pattern)
            
            if q_position >= 0:
                after_question = transcript[q_position:]
                
                response_match = re.search(
                    r'(?:candidato|user|resposta)[:\s]+(.+?)(?:(?:agente|lia|pergunta)[:\s]|$)',
                    after_question,
                    re.IGNORECASE | re.DOTALL
                )
                
                if response_match:
                    response_text = response_match.group(1).strip()
                else:
                    paragraphs = after_question.split('\n\n')
                    if len(paragraphs) > 1:
                        response_text = paragraphs[1].strip()
                    else:
                        sentences = after_question.split('. ')
                        if len(sentences) > 1:
                            response_text = '. '.join(sentences[1:3]).strip()
                        else:
                            response_text = after_question[:500].strip()
                
                if response_text and len(response_text) > 10:
                    qa_pairs.append({
                        'question': question,
                        'response': response_text[:2000]
                    })
        
        if not qa_pairs and questions:
            logger.warning("⚠️  Could not match questions to transcript. Using full transcript for first question.")
            qa_pairs.append({
                'question': questions[0],
                'response': transcript[:3000]
            })
        
        return qa_pairs
    
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get current status of a voice screening session."""
        
        async def _execute_with_db(session: AsyncSession) -> dict[str, Any] | None:
            result = await session.execute(text("""
                SELECT s.id, s.candidate_id, s.job_vacancy_id, s.screening_type, s.mode,
                       s.status, s.call_id, s.agent_id, s.started_at, s.completed_at,
                       r.overall_wsi, r.technical_wsi, r.behavioral_wsi, r.classification
                FROM wsi_sessions s
                LEFT JOIN wsi_results r ON r.session_id = s.id
                WHERE s.id = :session_id
            """), {"session_id": session_id})
            
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                "session_id": row[0],
                "candidate_id": row[1],
                "job_vacancy_id": row[2],
                "screening_type": row[3],
                "mode": row[4],
                "status": row[5],
                "call_id": row[6],
                "agent_id": row[7],
                "started_at": row[8].isoformat() if row[8] else None,
                "completed_at": row[9].isoformat() if row[9] else None,
                "result": {
                    "overall_wsi": float(row[10]) if row[10] else None,
                    "technical_wsi": float(row[11]) if row[11] else None,
                    "behavioral_wsi": float(row[12]) if row[12] else None,
                    "classification": row[13]
                } if row[10] else None
            }
        
        if db is not None:
            return await _execute_with_db(db)
        else:
            async with AsyncSessionLocal() as session:
                return await _execute_with_db(session)
    
    async def get_session_by_call_id(
        self,
        call_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """Get session by voice call ID."""
        
        async def _execute_with_db(session: AsyncSession) -> dict[str, Any] | None:
            result = await session.execute(text("""
                SELECT id FROM wsi_sessions WHERE call_id = :call_id
            """), {"call_id": call_id})
            
            row = result.fetchone()
            
            if row:
                return await self.get_session_status(row[0], db=session)
            
            return None
        
        if db is not None:
            return await _execute_with_db(db)
        else:
            async with AsyncSessionLocal() as session:
                return await _execute_with_db(session)


wsi_voice_orchestrator = WSIVoiceOrchestrator()
