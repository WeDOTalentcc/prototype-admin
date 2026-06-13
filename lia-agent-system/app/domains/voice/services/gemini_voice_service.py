"""
Gemini Voice-to-Text Service

Transcrição de áudio usando Gemini Flash 2.5 via Replit AI Integrations.
Suporta múltiplos formatos de áudio e vídeo.
"""

from app.shared.llm_models import CANONICAL_GEMINI_FLASH_MODEL
import logging
import os

# R-056: lazy import for optional Google dependency
try:
    from google import genai
    from google.genai import types  # W3-027-EXEMPT: optional module-level import for type availability — client via llm_service canonical
    _GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    _GOOGLE_GENAI_AVAILABLE = False
    import logging as _log
    _log.getLogger(__name__).warning(
        "google-genai not installed -- GeminiVoiceService will not work. "
        "Install with: pip install google-genai"
    )
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

# F-12 P0 fix (audit 2026-05-22): canonical llm_service singleton --
# self._get_llm_service() era ghost method (nunca definido). Substituido por
# referencia direta a llm_service canonical (mesmo pattern do F-01).
from app.domains.ai.services.llm import llm_service as _canonical_llm_service

logger = logging.getLogger(__name__)


def is_rate_limit_error(exception: BaseException) -> bool:
    """Check if the exception is a rate limit or quota violation error."""
    error_msg = str(exception)
    return (
        "429" in error_msg 
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower() 
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, 'status') and exception.status == 429)
    )


class GeminiVoiceService:
    """
    Service for audio/video transcription using Gemini Flash.
    
    Uses Replit AI Integrations (no API key required).
    Charges are billed to Replit credits.
    """
    
    SUPPORTED_AUDIO_FORMATS = [
        "audio/mpeg",  # MP3
        "audio/mp4",   # M4A
        "audio/wav",   # WAV
        "audio/ogg",   # OGG
        "audio/webm",  # WEBM
        "audio/flac",  # FLAC
    ]
    
    SUPPORTED_VIDEO_FORMATS = [
        "video/mp4",
        "video/mpeg",
        "video/webm",
        "video/quicktime",  # MOV
    ]
    
    def __init__(self, company_id: str = ""):
        """Initialize Gemini client — tenant-aware (Choose Your AI)."""
        api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
        base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

        # === Tenant-aware Gemini client (LGPD compliance) ===
        from app.shared.tenant_llm_context import get_gemini_client_for_tenant
        self.client = get_gemini_client_for_tenant(company_id)

        # F-12 P0 fix (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):
        # canonical llm_service singleton. Anteriormente lines 130/220/301
        # chamavam self._get_llm_service() (ghost method nunca definido) ->
        # AttributeError em toda transcribe_audio/analyze_audio/transcribe_interview.
        self._llm_service = _canonical_llm_service

        logger.info("[GeminiVoiceService] Initialized (tenant-aware)")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    async def transcribe_audio(
        self,
        audio_data: bytes,
        mime_type: str,
        prompt: str | None = None,
        language: str = "pt-BR"
    ) -> dict:
        """
        Transcreve áudio para texto usando Gemini Flash.
        
        Args:
            audio_data: Audio file bytes
            mime_type: MIME type (e.g., 'audio/mpeg', 'audio/wav')
            prompt: Optional custom prompt for transcription
            language: Target language (default: pt-BR)
        
        Returns:
            Dict with transcription results:
            {
                "text": str,
                "language": str,
                "mime_type": str,
                "size_bytes": int,
                "model": str
            }
        """
        if mime_type not in self.SUPPORTED_AUDIO_FORMATS and mime_type not in self.SUPPORTED_VIDEO_FORMATS:
            raise ValueError(
                f"Unsupported MIME type: {mime_type}. "
                f"Supported: {self.SUPPORTED_AUDIO_FORMATS + self.SUPPORTED_VIDEO_FORMATS}"
            )
        
        logger.info(f"🎤 Transcribing audio: {len(audio_data)} bytes, {mime_type}")
        
        if not prompt:
            prompt = f"""Transcreva este áudio em {language} com precisão.
            
Instruções:
- Transcreva tudo o que for dito
- Mantenha pontuação adequada
- Identifique diferentes speakers se houver
- Inclua timestamps importantes se mencionados
- Ignore ruídos de fundo

Forneça apenas a transcrição, sem introdução ou explicações."""
        
        try:
            response = self._llm_service.generate_native_gemini_sync(
                model=CANONICAL_GEMINI_FLASH_MODEL,
                contents=[
                    prompt,
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=audio_data
                        )
                    )
                ]
            )
            
            transcription = response.text or ""
            
            logger.info(f"✅ Transcription completed: {len(transcription)} characters")
            
            return {
                "text": transcription.strip(),
                "language": language,
                "mime_type": mime_type,
                "size_bytes": len(audio_data),
                "model": CANONICAL_GEMINI_FLASH_MODEL
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    async def analyze_audio(
        self,
        audio_data: bytes,
        mime_type: str,
        analysis_type: str = "full"
    ) -> dict:
        """
        Analisa áudio além de transcrição (sentimento, tópicos, insights).
        
        Args:
            audio_data: Audio file bytes
            mime_type: MIME type
            analysis_type: "full", "sentiment", "topics", "summary"
        
        Returns:
            Dict with analysis results
        """
        logger.info(f"🔍 Analyzing audio: {analysis_type}")
        
        prompts = {
            "full": """Analise este áudio de candidato em processo de recrutamento:

1. TRANSCRIÇÃO: Texto completo do que foi dito
2. SENTIMENTO: Emoções detectadas (confiante, nervoso, entusiasmado, etc)
3. TÓPICOS PRINCIPAIS: 3-5 tópicos mais relevantes
4. SOFT SKILLS: Comunicação, articulação, clareza
5. RED FLAGS: Sinais de alerta se houver
6. RESUMO: Parágrafo com impressão geral

Forneça análise estruturada e objetiva.""",

            "sentiment": """Analise o sentimento e emoções neste áudio:

- Emoções detectadas
- Nível de confiança
- Entusiasmo/motivação
- Sinais de estresse ou nervosismo
- Tom geral (positivo/neutro/negativo)""",

            "topics": """Identifique os 5 tópicos principais discutidos neste áudio.
Para cada tópico, forneça:
- Tópico
- Relevância (alta/média/baixa)
- Breve resumo (1 frase)""",

            "summary": """Resuma este áudio em 2-3 parágrafos:

Parágrafo 1: O que foi discutido
Parágrafo 2: Principais pontos e conclusões
Parágrafo 3: Próximos passos ou recomendações (se mencionado)"""
        }
        
        prompt = prompts.get(analysis_type, prompts["full"])
        
        try:
            response = self._llm_service.generate_native_gemini_sync(
                model=CANONICAL_GEMINI_FLASH_MODEL,
                contents=[
                    prompt,
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=audio_data
                        )
                    )
                ]
            )
            
            analysis = response.text or ""
            
            logger.info(f"✅ Analysis completed: {len(analysis)} characters")
            
            return {
                "analysis": analysis.strip(),
                "analysis_type": analysis_type,
                "mime_type": mime_type,
                "size_bytes": len(audio_data),
                "model": CANONICAL_GEMINI_FLASH_MODEL
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise
    
    async def transcribe_interview(
        self,
        audio_data: bytes,
        mime_type: str,
        job_title: str | None = None,
        questions: list[str] | None = None
    ) -> dict:
        """
        Transcreve e analisa entrevista de candidato.
        
        Args:
            audio_data: Audio da entrevista
            mime_type: MIME type
            job_title: Cargo da vaga (opcional)
            questions: Perguntas esperadas (opcional)
        
        Returns:
            Dict com transcrição + análise de fit
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"🎯 Transcribing interview for: {job_title or 'unknown position'}")
        
        questions_context = ""
        if questions:
            questions_context = "\n\nPerguntas esperadas:\n" + "\n".join(f"- {q}" for q in questions)
        
        job_context = f" para a vaga de {job_title}" if job_title else ""
        
        prompt = f"""Esta é uma entrevista de candidato{job_context}.
{questions_context}

Forneça:

1. TRANSCRIÇÃO COMPLETA
Texto exato do que foi dito, com timestamps aproximados se possível.

2. ANÁLISE DE RESPOSTAS
Para cada pergunta/tópico:
- Qualidade da resposta (1-5 estrelas)
- Pontos fortes
- Pontos a melhorar

3. AVALIAÇÃO GERAL
- Comunicação (1-5)
- Conhecimento técnico demonstrado (1-5)
- Fit cultural percebido (1-5)
- Recomendação (Avançar / Reconsiderar / Não avançar)

4. PRÓXIMOS PASSOS
Sugestões para follow-up ou próximas etapas."""

        try:
            response = self._llm_service.generate_native_gemini_sync(
                model=CANONICAL_GEMINI_FLASH_MODEL,
                contents=[
                    prompt,
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=audio_data
                        )
                    )
                ]
            )
            
            interview_analysis = response.text or ""
            
            logger.info("✅ Interview transcription and analysis completed")
            
            return {
                "interview_analysis": interview_analysis.strip(),
                "job_title": job_title,
                "questions_count": len(questions) if questions else 0,
                "mime_type": mime_type,
                "size_bytes": len(audio_data),
                "model": CANONICAL_GEMINI_FLASH_MODEL
            }
            
        except Exception as e:
            logger.error(f"❌ Interview analysis failed: {e}")
            raise


# Singleton instance
_voice_service: GeminiVoiceService | None = None


def get_voice_service() -> GeminiVoiceService:
    """Get or create voice service singleton."""
    global _voice_service
    if _voice_service is None:
        _voice_service = GeminiVoiceService()
    return _voice_service
