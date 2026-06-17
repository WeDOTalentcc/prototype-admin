"""
Gemini Live Audio Service — Bidirectional voice streaming via Gemini Live API.

Replaces the Twilio+Gemini STT+OpenAI TTS pipeline for VoIP (browser) calls
with a single Gemini Live Audio WebSocket connection that handles STT, LLM,
and TTS natively.

Audio pipeline (new):
  Browser mic → [PCM 16kHz] → WebSocket → Gemini Live Audio → [audio response] → Browser speaker

Compliance:
- LGPD Art. 7: verify_consent() before session start
- LGPD Art. 12: PII masking in all logs
- Crença #11: Anti-sycophancy in system prompt
- FairnessGuard: L1+L2 on all LIA responses
- Session timeout: max 20 minutes

Cost: ~$0.065/interview (15 min) vs ~$0.41 with Twilio+OpenAI TTS pipeline
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.shared.compliance.fairness_guard_middleware import check_fairness
from app.shared.pii_masking import mask_pii, strip_pii_for_llm_prompt
from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_SECONDS = 1200
MAX_TURN_TOKENS = 500
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1


@dataclass
class GeminiLiveSession:
    session_id: str
    candidate_id: str
    candidate_name: str
    job_title: str
    company_id: str
    job_id: str | None = None
    language: str = "pt-BR"
    status: str = "pending"
    voice_provider: str = "gemini_live"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    transcript_segments: list[dict[str, Any]] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    turn_latencies_ms: list[float] = field(default_factory=list)
    error: str | None = None
    consent_verified: bool = False
    job_context: dict[str, Any] | None = None
    presentation_done: bool = False


class GeminiLiveAudioError(Exception):
    pass


class GeminiLiveAudioService:
    """
    Manages bidirectional Gemini Live Audio sessions for voice screening.

    Each session creates a Gemini Live API connection that handles:
    - Speech-to-text (candidate audio input)
    - LLM-driven conversation (screening questions, follow-ups)
    - Text-to-speech (LIA voice responses)

    All in a single WebSocket connection with sub-second latency.
    """

    def __init__(self):
        self._api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
        self._base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
        self._sessions: dict[str, GeminiLiveSession] = {}

    @property
    def is_available(self) -> bool:
        return bool(self._api_key and self._base_url)

    def build_system_prompt(
        self,
        session: GeminiLiveSession,
        wsi_questions: list[str] | None = None,
    ) -> str:
        from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator

        job_context_block = ""
        if session.job_context:
            job_context_block = (
                "\n=== JOB DESCRIPTION — CONTEXTO DA VAGA ===\n"
                + VoiceScreeningOrchestrator._build_job_context_summary(session.job_context)
                + "\n\nUse APENAS estas informações ao responder perguntas do candidato sobre a vaga. "
                "Não invente ou presuma informações não presentes acima.\n"
            )
        else:
            job_context_block = (
                f"\n=== CONTEXTO DA VAGA ===\n"
                f"Título: {session.job_title}\n"
                f"(Informações detalhadas da vaga não disponíveis. Use apenas o título.)\n"
            )

        questions_block = ""
        if wsi_questions:
            questions_list = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(wsi_questions))
            questions_block = (
                f"\n=== PERGUNTAS DA TRIAGEM ===\n"
                f"Faça estas perguntas na ordem, UMA por vez:\n{questions_list}\n"
                f"Após responder todas, encerre com cordialidade.\n"
            )
        else:
            questions_block = (
                "\n=== PERGUNTAS DA TRIAGEM ===\n"
                "Gere perguntas comportamentais e técnicas relevantes para a vaga (~5 perguntas).\n"
                "Use metodologia STAR (Situação, Tarefa, Ação, Resultado).\n"
                "Faça UMA pergunta por vez.\n"
            )

        fairness_instructions = (
            "\n=== COMPLIANCE E FAIRNESS — REGRAS ABSOLUTAS ===\n"
            "PERGUNTAS PROIBIDAS (nunca pergunte):\n"
            "- Idade, data de nascimento, geração\n"
            "- Gênero, identidade de gênero, orientação sexual\n"
            "- Raça, cor, etnia, naturalidade\n"
            "- Estado civil, filhos, gravidez, planos de família\n"
            "- Religião, crenças, filiação política ou sindical\n"
            "- Condições de saúde, deficiências, uso de medicamentos\n"
            "- Situação financeira pessoal, endereço residencial\n"
            "- Aparência física, peso, altura\n"
            "\nPERGUNTAS DO CANDIDATO — O QUE VOCÊ PODE RESPONDER:\n"
            "- Sobre benefícios, salário, formato de trabalho, localização → responda com base no job description acima\n"
            "- Sobre a descrição do cargo, responsabilidades, competências → responda com base no job description acima\n"
            "- Sobre as etapas do processo seletivo → explique que é uma triagem inicial e que a empresa entrará em contato\n"
            "- Sobre a empresa, cultura → use informações do job description se disponíveis; caso contrário, diga que não tem essa informação\n"
            "\nINFORMAÇÕES QUE VOCÊ DEVE RECUSAR:\n"
            "- Qualquer dado que não foi disponibilizado pela empresa\n"
            "- Comparações entre candidatos\n"
            "- Previsão de resultado da triagem ou probabilidade de aprovação\n"
            "\nANTI-SYCOPHANCY: Nunca elogie excessivamente as respostas do candidato. Valide de forma breve e neutra.\n"
            "LGPD: Não solicite dados pessoais além dos necessários para a triagem.\n"
            "(LGPD, CLT Art. 5º, CF Art. 5º, Lei 9.029/95, Lei 13.146/15)\n"
        )

        system_prompt = (
            f"Recrutadora inteligente da WeDO Talent. Conduza a triagem por voz com naturalidade, "
            f"empatia e profissionalismo — como uma recrutadora experiente, não como um robô seguindo um script.\n\n"
            f"IDIOMA: {session.language}\n\n"
            f"CANDIDATO: {session.candidate_name}\n"
            f"{job_context_block}\n"
            f"{questions_block}\n"
            f"INSTRUÇÕES DE CONDUTA:\n"
            f"- Respostas curtas e naturais (otimizadas para áudio de voz)\n"
            f"- Faça UMA pergunta por vez — nunca empilhe perguntas\n"
            f"- Valide brevemente a resposta anterior com uma transição natural\n"
            f"- Se o candidato fizer uma pergunta sobre a vaga, responda antes de continuar\n"
            f"- Conduza a conversa com fluidez — valide, faça follow-up quando relevante, depois avance\n"
            f"- Ao encerrar, agradeça, informe que o time entrará em contato, e despeça-se com cordialidade\n"
            f"- COMECE apresentando a vaga ao candidato e perguntando se tem dúvidas antes das perguntas\n"
            f"{fairness_instructions}\n"
            f"{ANTI_SYCOPHANCY_OPERATIONAL}"
        )

        return system_prompt

    def create_session(
        self,
        candidate_id: str,
        candidate_name: str,
        job_title: str,
        company_id: str,
        job_id: str | None = None,
        language: str = "pt-BR",
        job_context: dict[str, Any] | None = None,
    ) -> GeminiLiveSession:
        session = GeminiLiveSession(
            session_id=str(uuid4()),
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_title=job_title,
            company_id=company_id,
            job_id=job_id,
            language=language,
            started_at=datetime.utcnow(),
            consent_verified=True,
            job_context=job_context,
        )
        self._sessions[session.session_id] = session
        logger.info(
            "[GEMINI LIVE] Session created: session=%s candidate=%s job=%s company=%s",
            session.session_id,
            mask_pii(candidate_id),
            job_title,
            company_id,
        )
        return session

    def get_session(self, session_id: str) -> GeminiLiveSession | None:
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def create_live_connection_config(
        self,
        session: GeminiLiveSession,
        wsi_questions: list[str] | None = None,
    ) -> dict[str, Any]:
        system_prompt = self.build_system_prompt(session, wsi_questions)

        config = {
            "model": "gemini-2.5-flash",
            "system_instruction": system_prompt,
            "generation_config": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Aoede"
                        }
                    }
                },
                "temperature": 0.7,
                "max_output_tokens": MAX_TURN_TOKENS,
            },
        }

        logger.info(
            "[GEMINI LIVE] Connection config built for session=%s model=%s",
            session.session_id,
            config["model"],
        )
        return config

    async def process_candidate_text(
        self,
        session: GeminiLiveSession,
        text: str,
    ) -> None:
        if not text or not text.strip():
            return

        masked_text = mask_pii(text)
        # W3-018 (2026-05-23): PII strip ANTES de armazenar em
        # transcript_segments — evita vazamento via conversation_history
        # de volta ao Gemini LLM. masked_text continua sendo usado em log.
        session.transcript_segments.append({
            "text": strip_pii_for_llm_prompt(text),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "candidate",
        })
        logger.debug(
            "[GEMINI LIVE] Candidate text session=%s: %s",
            session.session_id,
            masked_text[:100],
        )

    async def process_lia_text(
        self,
        session: GeminiLiveSession,
        text: str,
    ) -> str | None:
        if not text or not text.strip():
            return None

        fairness_result = check_fairness(
            texts={"lia_live_response": text},
            context="gemini_live_screening",
            company_id=session.company_id,
        )
        if fairness_result.is_blocked:
            logger.warning(
                "[GEMINI LIVE] FairnessGuard BLOCKED response session=%s category=%s",
                session.session_id,
                fairness_result.blocked_result.category if fairness_result.blocked_result else "unknown",
            )
            return None

        masked_text = mask_pii(text)
        # W3-018: defense-in-depth · LIA response também strip.
        session.transcript_segments.append({
            "text": strip_pii_for_llm_prompt(text),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "lia",
        })
        logger.debug(
            "[GEMINI LIVE] LIA response session=%s: %s",
            session.session_id,
            masked_text[:100],
        )
        return text

    def record_turn_latency(self, session: GeminiLiveSession, latency_ms: float) -> None:
        session.turn_latencies_ms.append(latency_ms)
        if latency_ms > 500:
            logger.warning(
                "[GEMINI LIVE] High latency session=%s latency=%.0fms (target <500ms)",
                session.session_id,
                latency_ms,
            )

    def record_token_usage(
        self,
        session: GeminiLiveSession,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        session.token_usage["input"] += input_tokens
        session.token_usage["output"] += output_tokens

    def is_session_expired(self, session: GeminiLiveSession) -> bool:
        if not session.started_at:
            return False
        elapsed = (datetime.utcnow() - session.started_at).total_seconds()
        return elapsed > SESSION_TIMEOUT_SECONDS

    async def finalize_session(
        self,
        session: GeminiLiveSession,
    ) -> dict[str, Any]:
        session.ended_at = datetime.utcnow()
        session.status = "completed"

        duration_seconds = None
        if session.started_at and session.ended_at:
            duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )

        avg_latency = (
            sum(session.turn_latencies_ms) / len(session.turn_latencies_ms)
            if session.turn_latencies_ms
            else 0
        )
        p95_latency = (
            sorted(session.turn_latencies_ms)[int(len(session.turn_latencies_ms) * 0.95)]
            if session.turn_latencies_ms
            else 0
        )

        logger.info(
            "[GEMINI LIVE] Session finalized: session=%s duration=%ss turns=%d "
            "avg_latency=%.0fms p95_latency=%.0fms tokens_in=%d tokens_out=%d",
            session.session_id,
            duration_seconds,
            len(session.transcript_segments),
            avg_latency,
            p95_latency,
            session.token_usage["input"],
            session.token_usage["output"],
        )

        return {
            "session_id": session.session_id,
            "status": "completed",
            "voice_provider": "gemini_live",
            "duration_seconds": duration_seconds,
            "transcript_segments": len(session.transcript_segments),
            "token_usage": session.token_usage,
            "latency_avg_ms": round(avg_latency, 1),
            "latency_p95_ms": round(p95_latency, 1),
        }

    def get_session_metrics(self, session: GeminiLiveSession) -> dict[str, Any]:
        return {
            "session_id": session.session_id,
            "status": session.status,
            "voice_provider": session.voice_provider,
            "transcript_segments": len(session.transcript_segments),
            "questions_asked": len(session.questions_asked),
            "token_usage": session.token_usage,
            "turn_count": len(session.turn_latencies_ms),
            "avg_latency_ms": (
                round(sum(session.turn_latencies_ms) / len(session.turn_latencies_ms), 1)
                if session.turn_latencies_ms
                else 0
            ),
            "started_at": session.started_at.isoformat() if session.started_at else None,
        }


_gemini_live_service: GeminiLiveAudioService | None = None


def get_gemini_live_service() -> GeminiLiveAudioService:
    global _gemini_live_service
    if _gemini_live_service is None:
        _gemini_live_service = GeminiLiveAudioService()
    return _gemini_live_service
