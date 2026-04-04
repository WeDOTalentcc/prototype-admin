"""
OpenMic.ai Voice Screening Service

Handles voice call screening integration with OpenMic.ai for candidate interviews.
Provides methods to create agents, initiate calls, and process webhooks.

# OpenMic.ai - For automated voice CALLS (future feature)
# Use case: Automated phone screening calls
# Pricing: $0.08-$0.15/min (includes TTS + STT + AI agent)
#
# For WhatsApp AUDIO TRANSCRIPTION, use deepgram_service.py instead
# Deepgram pricing: $0.0043/min (just transcription)
"""

import os
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

from tenacity import retry, stop_after_attempt, wait_exponential
from app.shared.resilience.circuit_breaker import circuit_breaker
from app.core.database import AsyncSessionLocal
from app.models import VoiceScreeningCall, VoiceScreeningAnalysis
from app.services.activity_service import activity_service

logger = logging.getLogger(__name__)


class OpenMicCallData(BaseModel):
    """OpenMic.ai call data model - flexible for different event types"""
    call_id: str
    call_type: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None
    agent_id: Optional[str] = None
    call_status: str
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_seconds: Optional[int] = None
    disconnection_reason: Optional[str] = None
    transcript: Optional[str] = None
    transcript_object: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None  # Data from OpenMic webhook payload


class OpenMicWebhookEvent(BaseModel):
    """OpenMic.ai webhook event model - supports all event types"""
    event: str
    timestamp: str
    call_id: str
    agent_id: Optional[str] = None
    call: Optional[OpenMicCallData] = None  # Optional - not present in all events


class CreateCallRequest(BaseModel):
    """Request model for creating screening calls"""
    job_title: str = Field(..., description="Job title (e.g., Backend Engineer Sênior Node.js)")
    job_description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field(..., description="List of required skills")
    candidate_phone: str = Field(..., description="Candidate phone number (format: +5511999999999)")
    candidate_name: str = Field(..., description="Candidate full name")
    candidate_id: Optional[str] = Field(None, description="Optional internal candidate ID")
    questions: Optional[List[str]] = Field(None, description="Optional custom questions")


async def _openmic_agent_fallback(*args, **kwargs):
    """Fallback retornado quando circuit breaker do OpenMic está aberto (create_agent)."""
    logger.warning("[CIRCUIT-BREAKER] OpenMic circuit aberto — create_screening_agent indisponível")
    return {"error": "Serviço OpenMic temporariamente indisponível", "circuit_open": True}


async def _openmic_call_fallback(*args, **kwargs):
    """Fallback retornado quando circuit breaker do OpenMic está aberto (start_call)."""
    logger.warning("[CIRCUIT-BREAKER] OpenMic circuit aberto — start_screening_call indisponível")
    return {"error": "Serviço OpenMic temporariamente indisponível", "circuit_open": True, "call_id": None}


class OpenMicService:
    """Service for OpenMic.ai voice screening integration"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENMIC_API_KEY")
        self.webhook_secret = os.getenv("OPENMIC_WEBHOOK_SECRET")  # For signature verification
        
        if not self.api_key:
            logger.warning("⚠️  OPENMIC_API_KEY not configured")
        if not self.webhook_secret:
            logger.warning("⚠️  OPENMIC_WEBHOOK_SECRET not configured - webhook signature verification disabled!")
        
        self.base_url = "https://api.openmic.ai/v1"
        self.webhook_url = os.getenv("OPENMIC_WEBHOOK_URL", "https://your-domain.replit.dev/api/v1/openmic/webhook")
        
        logger.info("✅ OpenMic.ai service initialized")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify OpenMic.ai webhook signature using HMAC-SHA256.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from X-OpenMic-Signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("⚠️  Webhook signature verification skipped - OPENMIC_WEBHOOK_SECRET not configured!")
            return True  # Allow in dev, but warn
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"❌ Signature verification error: {e}")
            return False
    
    @circuit_breaker("openmic", failure_threshold=5, recovery_timeout=60.0, fallback=_openmic_agent_fallback)
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
    async def create_screening_agent(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a voice screening agent for a specific job position.
        
        Args:
            job_title: Job title (e.g., "Backend Engineer Sênior Node.js")
            job_description: Full job description
            required_skills: List of required skills to assess
            questions: Optional custom questions
            
        Returns:
            Agent configuration with agent_id
        """
        if not self.api_key:
            raise ValueError("OPENMIC_API_KEY not configured")
        
        # Build screening prompt in Portuguese
        prompt = f"""Você é a LIA (Learning Intelligence Assistant), uma recrutadora especializada da WedoTalent.

Sua missão é fazer uma triagem inicial de candidatos para a vaga de {job_title}.

DESCRIÇÃO DA VAGA:
{job_description}

HABILIDADES REQUERIDAS:
{', '.join(required_skills)}

INSTRUÇÕES:
1. Cumprimente o candidato de forma amigável e profissional
2. Explique que esta é uma triagem inicial por voz de 10 minutos
3. Pergunte sobre experiência com as tecnologias principais: {', '.join(required_skills[:3])}
4. Explore projetos anteriores e contexto profissional
5. Avalie fit cultural e motivação
6. Ao final, agradeça e informe que o recrutador entrará em contato

PERSONALIDADE:
- Amigável mas profissional
- Curiosa e empática
- Focada em extrair informações relevantes
- Respeita sotaques regionais brasileiros

IMPORTANTE:
- Mantenha a conversa fluida e natural
- Faça perguntas abertas
- Não interrompa o candidato
- Adapte-se ao ritmo de fala do candidato
"""

        if questions:
            prompt += f"\n\nPERGUNTAS ESPECÍFICAS:\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        
        payload = {
            "name": f"LIA Screening - {job_title}",
            "voice": {
                "provider": "google",  # Brazilian Portuguese voices
                "voice_id": "pt-BR-Standard-A",  # Female Brazilian voice
                "language": "pt-BR"
            },
            "prompt": prompt,
            "llm": {
                "model": "gpt-4",
                "temperature": 0.7
            },
            "stt": {
                "provider": "deepgram",  # Best for Portuguese BR
                "language": "pt-BR"
            },
            "webhook_url": self.webhook_url,
            "metadata": {
                "job_title": job_title,
                "screening_type": "initial",
                "created_by": "lia_backend"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/agents",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                agent_data = response.json()
                logger.info(f"✅ Created screening agent: {agent_data.get('agent_id')}")
                
                return agent_data
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to create agent: {e}")
            raise
    
    @circuit_breaker("openmic", failure_threshold=5, recovery_timeout=60.0, fallback=_openmic_call_fallback)
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
    async def start_screening_call(
        self,
        agent_id: str,
        candidate_phone: str,
        candidate_name: str,
        candidate_id: Optional[str] = None,
        job_title: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Start a screening call to a candidate.
        
        Args:
            agent_id: OpenMic agent ID
            candidate_phone: Candidate phone number (format: +5511999999999)
            candidate_name: Candidate full name
            candidate_id: Optional internal candidate ID
            job_title: Optional job title for tracking
            dry_run: If True, returns mock response without calling API (safe for testing)
            
        Returns:
            Call data with call_id
        """
        if dry_run:
            logger.info(f"🧪 DRY RUN: Simulating screening call to {candidate_name} ({candidate_phone})")
            return {
                "call_id": f"dry_run_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "status": "simulated",
                "dry_run": True,
                "agent_id": agent_id,
                "to_number": candidate_phone,
                "candidate_name": candidate_name,
                "candidate_id": candidate_id,
                "job_title": job_title,
                "message": "This is a dry run - no actual call was made"
            }
        
        if not self.api_key:
            raise ValueError("OPENMIC_API_KEY not configured")
        
        payload = {
            "agent_id": agent_id,
            "to_number": candidate_phone,
            "from_number": None,  # OpenMic will use trial/purchased number
            "metadata": {
                "candidate_name": candidate_name,
                "candidate_id": candidate_id,
                "job_title": job_title,
                "call_type": "screening",
                "initiated_by": "lia_backend",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/calls",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                call_data = response.json()
                logger.info(f"✅ Started screening call: {call_data.get('call_id')} to {candidate_name}")
                
                return call_data
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to start call: {e}")
            raise
    
    async def process_webhook(self, event: OpenMicWebhookEvent) -> Dict[str, Any]:
        """
        Process OpenMic.ai webhook event.
        
        Args:
            event: Webhook event data
            
        Returns:
            Processing result with candidate analysis
        """
        logger.info(f"📞 Processing OpenMic webhook: {event.event} - Call {event.call_id}")
        
        if event.event == "call.started":
            return await self._handle_call_started(event)
        elif event.event == "call.ended":
            return await self._handle_call_ended(event)
        else:
            logger.warning(f"⚠️  Unknown event type: {event.event}")
            return {"status": "ignored", "event": event.event}
    
    async def _handle_call_started(self, event: OpenMicWebhookEvent) -> Dict[str, Any]:
        """Handle call started event"""
        logger.info(f"🎤 Call started: {event.call_id}")
        
        # TODO: Update database - call started
        # TODO: Send notification to recruiter
        
        return {
            "status": "call_started",
            "call_id": event.call_id,
            "timestamp": event.timestamp
        }
    
    async def _handle_call_ended(self, event: OpenMicWebhookEvent) -> Dict[str, Any]:
        """Handle call ended event - main processing with LIA AI analysis"""
        if not event.call:
            logger.error(f"❌ call.ended event missing call data: {event.call_id}")
            return {
                "status": "error",
                "message": "Missing call data in event"
            }
        
        logger.info(f"📞 Call ended: {event.call_id} - Duration: {event.call.duration_seconds}s")
        
        if not event.call.transcript:
            logger.warning(f"⚠️  No transcript available for call {event.call_id}")
            return {
                "status": "error",
                "message": "No transcript available"
            }
        
        # Extract candidate information from metadata
        candidate_name = event.call.metadata.get("candidate_name", "Unknown") if event.call.metadata else "Unknown"
        candidate_id = event.call.metadata.get("candidate_id") if event.call.metadata else None
        job_title = event.call.metadata.get("job_title", "Unknown") if event.call.metadata else "Unknown"
        
        # DUAL ANALYSIS: Basic keywords + Deep LIA AI analysis
        logger.info(f"🤖 Running dual analysis (basic + LIA AI) for call {event.call_id}")
        
        # 1. Basic keyword analysis (fast, simple)
        basic_analysis = await self._analyze_transcript(
            transcript=event.call.transcript,
            transcript_object=event.call.transcript_object,
            job_title=job_title
        )
        
        # 2. Deep LIA AI analysis (slow, comprehensive) - imported from conversation_agent
        try:
            from app.services.voice_screening_analysis import analyze_voice_screening
            
            logger.info(f"🧠 Triggering deep LIA AI analysis...")
            
            ai_analysis = await analyze_voice_screening(
                transcript=event.call.transcript,
                transcript_object=event.call.transcript_object,
                job_title=job_title,
                required_skills=None,  # TODO: Extract from job metadata
                job_description=None,  # TODO: Extract from job metadata
                candidate_name=candidate_name,
                duration_seconds=event.call.duration_seconds
            )
            
            logger.info(f"✅ LIA AI analysis complete - Score: {ai_analysis['overall_evaluation']['overall_score']}/100")
            
        except Exception as e:
            logger.error(f"⚠️  LIA AI analysis failed, using basic analysis only: {e}")
            ai_analysis = None
        
        result = {
            "status": "processed",
            "call_id": event.call_id,
            "candidate_name": candidate_name,
            "candidate_id": candidate_id,
            "job_title": job_title,
            "duration_seconds": event.call.duration_seconds,
            "transcript": event.call.transcript,
            "transcript_object": event.call.transcript_object,
            "basic_analysis": basic_analysis,  # Fast keyword-based
            "ai_analysis": ai_analysis,  # Deep LIA AI analysis
            "timestamp": event.timestamp
        }
        
        # Use AI analysis score if available, otherwise fall back to basic
        final_score = ai_analysis["overall_evaluation"]["overall_score"] if ai_analysis else basic_analysis.get("overall_score", 50)
        logger.info(f"✅ Call processed: {event.call_id} - Final Score: {final_score}/100")
        
        # Save to database (both call and analyses)
        try:
            db_call_id = await self._save_screening_to_database(event, basic_analysis, ai_analysis)
            logger.info(f"💾 Screening saved to database: {db_call_id}")
            result["db_id"] = str(db_call_id)
        except Exception as e:
            logger.error(f"❌ Failed to save to database: {e}", exc_info=True)
            result["db_error"] = str(e)
        
        # Check if this call is linked to a WSI session and process it
        try:
            from app.services.wsi_voice_orchestrator import wsi_voice_orchestrator
            
            wsi_session = await wsi_voice_orchestrator.get_session_by_call_id(event.call_id)
            if wsi_session:
                logger.info(f"🎯 WSI session found for call {event.call_id} - Running WSI analysis")
                
                wsi_result = await wsi_voice_orchestrator.process_call_completed(
                    call_id=event.call_id,
                    transcript=event.call.transcript,
                    transcript_object=event.call.transcript_object
                )
                
                if wsi_result:
                    result["wsi_analysis"] = {
                        "overall_wsi": wsi_result.overall_wsi,
                        "technical_wsi": wsi_result.technical_wsi,
                        "behavioral_wsi": wsi_result.behavioral_wsi,
                        "classification": wsi_result.classification
                    }
                    logger.info(f"✅ WSI analysis complete - Overall WSI: {wsi_result.overall_wsi}/5.0")
        except Exception as e:
            logger.error(f"⚠️  WSI analysis failed for call {event.call_id}: {e}")

        # Reconcile with TriagemSession if this call was initiated from the triagem phone flow
        try:
            await self._reconcile_triagem_session(event.call_id, result)
        except Exception as e:
            logger.error(f"⚠️  Triagem reconciliation failed for call {event.call_id}: {e}")
        
        return result

    async def _reconcile_triagem_session(
        self, call_id: str, call_result: Dict[str, Any]
    ) -> None:
        """Update TriagemSession when a phone call initiated from triagem completes."""
        from sqlalchemy import text as sql_text

        async with AsyncSessionLocal() as db:
            from app.models.triagem import TriagemSession

            from sqlalchemy import select
            stmt = select(TriagemSession).where(
                TriagemSession.metadata_json["phone_call"]["call_id"].as_string() == call_id
            )
            r = await db.execute(stmt)
            session = r.scalar_one_or_none()
            if not session:
                return

            logger.info(f"[Triagem] Reconciling phone call {call_id} with triagem session {session.token}")

            meta = session.metadata_json or {}
            phone_call = meta.get("phone_call", {})
            phone_call["completed_at"] = datetime.utcnow().isoformat()
            phone_call["duration_seconds"] = call_result.get("duration_seconds")

            wsi_analysis = call_result.get("wsi_analysis")
            if wsi_analysis:
                phone_call["wsi_overall"] = wsi_analysis.get("overall_wsi")
                phone_call["wsi_classification"] = wsi_analysis.get("classification")
                session.wsi_final_score = wsi_analysis.get("overall_wsi")
                session.recommendation = (
                    "approved" if wsi_analysis.get("classification") in ("A", "B")
                    else "rejected" if wsi_analysis.get("classification") in ("D", "E")
                    else "pending"
                )

            ai_analysis = call_result.get("ai_analysis")
            if ai_analysis and not wsi_analysis:
                overall_score = ai_analysis.get("overall_evaluation", {}).get("overall_score", 0)
                phone_call["ai_score"] = overall_score

            meta["phone_call"] = phone_call
            session.metadata_json = meta
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            await db.commit()

            logger.info(
                f"[Triagem] Phone triagem completed: token={session.token}, "
                f"wsi={session.wsi_final_score}, recommendation={session.recommendation}"
            )
    
    async def _save_screening_to_database(
        self,
        event: OpenMicWebhookEvent,
        basic_analysis: Dict[str, Any],
        ai_analysis: Optional[Dict[str, Any]]
    ):
        """
        Save voice screening call and analysis to database.
        
        Returns:
            Database ID of created screening call
        """
        async with AsyncSessionLocal() as session:
            # Convert timestamps from milliseconds to datetime
            start_dt = None
            end_dt = None
            if event.call.start_timestamp:
                start_dt = datetime.fromtimestamp(event.call.start_timestamp / 1000)
            if event.call.end_timestamp:
                end_dt = datetime.fromtimestamp(event.call.end_timestamp / 1000)
            
            # Extract metadata
            metadata = event.call.metadata or {}
            candidate_name = metadata.get("candidate_name", "Unknown")
            candidate_id = metadata.get("candidate_id")
            job_title = metadata.get("job_title", "Unknown")
            
            # Create screening call record
            screening_call = VoiceScreeningCall(
                call_id=event.call_id,
                agent_id=event.agent_id,
                call_type=event.call.call_type or "outbound",
                call_status=event.call.call_status,
                direction=event.call.direction or "outbound",
                from_number=event.call.from_number,
                to_number=event.call.to_number,
                start_timestamp=start_dt,
                end_timestamp=end_dt,
                duration_seconds=event.call.duration_seconds,
                disconnection_reason=event.call.disconnection_reason,
                candidate_name=candidate_name,
                candidate_id=candidate_id,
                candidate_phone=event.call.to_number or "",
                job_title=job_title,
                transcript=event.call.transcript,
                transcript_object=event.call.transcript_object or [],
                webhook_event=event.event,
                webhook_timestamp=datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')),
                processing_status="completed" if ai_analysis else "basic_only",
                is_analyzed=bool(ai_analysis)
            )
            
            session.add(screening_call)
            await session.flush()  # Get ID before creating analysis
            
            # ALWAYS create analysis record (either basic-only or full AI analysis)
            if ai_analysis:
                # Full AI analysis available
                tech_assessment = ai_analysis.get("technical_assessment", {})
                comm_assessment = ai_analysis.get("communication_assessment", {})
                fit = ai_analysis.get("cultural_fit", {})
                overall = ai_analysis.get("overall_evaluation", {})
                
                analysis = VoiceScreeningAnalysis(
                    screening_call_id=screening_call.id,
                    analysis_model=ai_analysis.get("analysis_metadata", {}).get("analysis_model", "claude-sonnet-4-6"),
                    analysis_method="lia_ai_deep_analysis",
                    
                    # Basic analysis
                    basic_skills_mentioned=basic_analysis.get("skills_mentioned", []),
                    basic_overall_score=basic_analysis.get("overall_score"),
                    basic_recommendation=basic_analysis.get("recommendation"),
                    
                    # Technical assessment
                    tech_skills_mentioned=tech_assessment.get("skills_mentioned", []),
                    tech_skills_matched=tech_assessment.get("skills_matched", []),
                    tech_skills_missing=tech_assessment.get("skills_missing", []),
                    tech_experience_years=tech_assessment.get("experience_years"),
                    tech_projects_mentioned=tech_assessment.get("projects_mentioned", []),
                    tech_score=tech_assessment.get("technical_score"),
                    
                    # Communication assessment
                    comm_clarity=comm_assessment.get("clarity"),
                    comm_confidence=comm_assessment.get("confidence"),
                    comm_engagement=comm_assessment.get("engagement"),
                    comm_professionalism=comm_assessment.get("professionalism"),
                    comm_score=comm_assessment.get("communication_score"),
                    comm_notes=comm_assessment.get("notes"),
                    
                    # Cultural fit
                    fit_motivation=fit.get("motivation"),
                    fit_work_preferences=fit.get("work_preferences"),
                    fit_red_flags=fit.get("red_flags", []),
                    fit_green_flags=fit.get("green_flags", []),
                    fit_score=fit.get("fit_score"),
                    
                    # Overall evaluation
                    overall_score=overall.get("overall_score", 50),
                    overall_recommendation=overall.get("recommendation", "review"),
                    overall_confidence=overall.get("confidence"),
                    key_strengths=overall.get("key_strengths", []),
                    key_concerns=overall.get("key_concerns", []),
                    next_steps=overall.get("next_steps"),
                    
                    # Summaries
                    summary=ai_analysis.get("summary"),
                    detailed_notes=ai_analysis.get("detailed_notes"),
                    
                    # Full payload for debugging
                    full_analysis_payload=ai_analysis,
                    
                    analysis_status="completed"
                )
            else:
                # AI analysis failed - save basic-only analysis
                analysis = VoiceScreeningAnalysis(
                    screening_call_id=screening_call.id,
                    analysis_model="keyword-matcher",
                    analysis_method="basic_keywords_only",
                    
                    # Basic analysis only
                    basic_skills_mentioned=basic_analysis.get("skills_mentioned", []),
                    basic_overall_score=basic_analysis.get("overall_score", 50),
                    basic_recommendation=basic_analysis.get("recommendation", "review"),
                    
                    # Use basic scores for overall evaluation (required NOT NULL fields)
                    overall_score=basic_analysis.get("overall_score", 50),
                    overall_recommendation=basic_analysis.get("recommendation", "review"),
                    overall_confidence="baixa",  # Low confidence for basic-only analysis
                    
                    # Leave AI fields as empty arrays (not null)
                    tech_skills_mentioned=[],
                    tech_skills_matched=[],
                    tech_skills_missing=[],
                    tech_projects_mentioned=[],
                    fit_red_flags=[],
                    fit_green_flags=[],
                    key_strengths=[],
                    key_concerns=[],
                    
                    # Summary note about basic-only analysis
                    summary=f"Análise básica por keywords (AI analysis não disponível). {len(basic_analysis.get('skills_mentioned', []))} tecnologias mencionadas.",
                    
                    analysis_status="basic_only"
                )
            
            session.add(analysis)
            
            await session.commit()
            
            # Create activity feed entry for this screening
            try:
                await self._create_activity_feed_entry(screening_call, analysis)
                logger.info(f"✅ Activity feed entry created for screening {screening_call.call_id}")
            except Exception as e:
                logger.error(f"⚠️  Failed to create activity feed entry: {e}")
            
            return screening_call.id
    
    async def _create_activity_feed_entry(
        self,
        screening_call: VoiceScreeningCall,
        analysis: VoiceScreeningAnalysis
    ):
        """
        Create activity feed entry after voice screening is completed.
        
        Args:
            screening_call: The completed screening call
            analysis: The analysis results (AI or basic-only)
        """
        # Determine priority based on score
        priority = "normal"
        if analysis.overall_score >= 80:
            priority = "urgent"
        elif analysis.overall_score < 60:
            priority = "low"
        
        # Create emoji based on recommendation
        emoji_map = {
            "strong_yes": "🔥",
            "interview": "🎯",
            "maybe": "💡",
            "reject": "⚠️"
        }
        emoji = emoji_map.get(analysis.overall_recommendation, "📞")
        
        # Build title
        title = f"{emoji} Voice Screening Completado"
        
        # Build summary
        summary = f"{screening_call.candidate_name} • {screening_call.job_title}\nScore {analysis.overall_score}/100 | {analysis.overall_recommendation.replace('_', ' ').title()}"
        
        # Build description with key insights
        description_parts = []
        
        if analysis.key_strengths:
            strengths_str = ", ".join(analysis.key_strengths[:3])
            description_parts.append(f"✅ Pontos fortes: {strengths_str}")
        
        if analysis.key_concerns:
            concerns_str = ", ".join(analysis.key_concerns[:2])
            description_parts.append(f"⚠️  Atenção: {concerns_str}")
        
        if analysis.next_steps:
            description_parts.append(f"🚀 Próximos passos: {analysis.next_steps}")
        
        description = "\n\n".join(description_parts) if description_parts else analysis.summary
        
        # Create activity metadata
        metadata = {
            "call_id": screening_call.call_id,
            "screening_id": str(screening_call.id),
            "overall_score": analysis.overall_score,
            "tech_score": analysis.tech_score,
            "comm_score": analysis.comm_score,
            "fit_score": analysis.fit_score,
            "recommendation": analysis.overall_recommendation,
            "confidence": analysis.overall_confidence,
            "analysis_method": analysis.analysis_method,
            "duration_seconds": screening_call.duration_seconds,
            "key_strengths": analysis.key_strengths or [],
            "key_concerns": analysis.key_concerns or [],
        }
        
        # Create activity
        await activity_service.create_activity(
            activity_type="voice_screening",
            title=title,
            description=description,
            summary=summary,
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=screening_call.candidate_id or screening_call.call_id,
            target_name=screening_call.candidate_name,
            target_type="candidate",
            extra_data=metadata,
            priority=priority,
            category="screening",
            action_url=f"/voice-screening/{screening_call.id}",
            action_label="Ver Análise Completa",
            created_by="system"
        )
    
    async def _analyze_transcript(
        self,
        transcript: str,
        transcript_object: Optional[List[Dict[str, Any]]],
        job_title: str
    ) -> Dict[str, Any]:
        """
        Analyze call transcript to extract skills, experience, and fit.
        
        This is a basic analysis. Full analysis will be done by LIA conversation agent.
        """
        # Basic keyword extraction (will be replaced by LIA Claude/Gemini/GPT analysis)
        skills_mentioned = []
        experience_years = None
        
        # Common tech skills to look for
        tech_keywords = [
            "node.js", "nodejs", "react", "vue", "angular", "python", "java",
            "docker", "kubernetes", "aws", "azure", "gcp", "postgresql", "mongodb",
            "microservices", "api", "rest", "graphql", "typescript", "javascript",
            "ci/cd", "devops", "terraform", "git", "agile", "scrum"
        ]
        
        transcript_lower = transcript.lower()
        for keyword in tech_keywords:
            if keyword in transcript_lower:
                skills_mentioned.append(keyword)
        
        # Basic scoring (placeholder - will be enhanced by LIA)
        overall_score = min(100, 50 + len(skills_mentioned) * 5)
        
        return {
            "skills_mentioned": skills_mentioned,
            "experience_years": experience_years,
            "overall_score": overall_score,
            "communication_quality": "good",  # Placeholder
            "recommendation": "proceed" if overall_score >= 60 else "review",
            "analysis_method": "basic_keywords",  # Will be "lia_ai" after integration
            "notes": f"Candidate mentioned {len(skills_mentioned)} relevant technologies"
        }


# Global service instance
openmic_service = OpenMicService()
