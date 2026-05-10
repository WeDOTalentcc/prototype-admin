"""
Voice Screening Analysis — standalone LLM function.

Extracted from app/shared/agents/conversation.py (Phase 7).
Does NOT depend on ConversationGraph or any LangGraph state machine.
"""
import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)


async def analyze_voice_screening(
    transcript: str,
    transcript_object: list[dict] | None,
    job_title: str,
    required_skills: list[str] | None = None,
    job_description: str | None = None,
    candidate_name: str | None = None,
    duration_seconds: int | None = None
) -> dict:
    """
    Analyze voice screening call transcript using LIA's AI (Claude/Gemini/GPT).

    Provides deep analysis beyond keyword matching:
    - Technical skills assessment
    - Communication quality evaluation
    - Cultural fit indicators
    - Experience validation
    - Overall scoring (0-100)
    - Detailed recommendations
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Analyzing voice screening for {job_title} - {len(transcript)} chars transcript")

    # SEG-3B: data minimization — remover PII da transcrição antes de enviar ao LLM (LGPD Art. 12)
    from app.shared.pii_masking import strip_pii_for_llm_prompt
    transcript = strip_pii_for_llm_prompt(transcript)

    duration_info = (
        f"Duração da call: {duration_seconds}s ({duration_seconds // 60}min)"
        if duration_seconds
        else "Duração da call: não disponível"
    )

    analysis_prompt = f"""Especialista em análise de triagem de candidatos (Learning Intelligence Assistant).

CONTEXTO:
Vaga: {job_title}
Candidato: {candidate_name or 'Nome não disponível'}
{duration_info}
"""

    if job_description:
        analysis_prompt += f"\nDESCRIÇÃO DA VAGA:\n{job_description}\n"

    if required_skills:
        analysis_prompt += f"\nHABILIDADES REQUERIDAS:\n{', '.join(required_skills)}\n"

    analysis_prompt += f"""
TRANSCRIÇÃO DA CALL:
{transcript}

TAREFA:
Analise esta triagem por voz e forneça uma avaliação completa do candidato.

ANÁLISE DETALHADA (retorne JSON estruturado):

{{{{
    "technical_assessment": {{{{
        "skills_mentioned": ["lista de tecnologias/skills mencionadas"],
        "skills_matched": ["skills que batem com os requisitos"],
        "skills_missing": ["skills requisitadas mas não mencionadas"],
        "experience_years": "estimativa de anos de experiência baseado na conversa",
        "projects_mentioned": ["projetos ou contextos profissionais citados"],
        "technical_score": 0-100
    }}}},

    "communication_assessment": {{{{
        "clarity": "baixa/média/alta",
        "confidence": "baixa/média/alta",
        "engagement": "baixo/médio/alto",
        "professionalism": "baixo/médio/alto",
        "communication_score": 0-100,
        "notes": "observações sobre comunicação"
    }}}},

    "cultural_fit": {{{{
        "motivation": "o que motiva o candidato com base na conversa",
        "work_preferences": "preferências de trabalho mencionadas",
        "red_flags": ["sinais de alerta identificados, ou lista vazia"],
        "green_flags": ["pontos positivos identificados"],
        "fit_score": 0-100
    }}}},

    "overall_evaluation": {{{{
        "overall_score": 0-100,
        "recommendation": "reject/maybe/interview/strong_yes",
        "confidence": "baixa/média/alta",
        "key_strengths": ["principais pontos fortes"],
        "key_concerns": ["principais preocupações"],
        "next_steps": "recomendação de próximos passos"
    }}}},

    "summary": "Resumo executivo da triagem em 2-3 frases",
    "detailed_notes": "Notas detalhadas para o recrutador"
}}}}

IMPORTANTE:
- Seja objetivo e baseado em evidências
- Identifique tanto pontos fortes quanto fracos
- Considere o contexto brasileiro (sotaques, expressões regionais)
- Avalie fit para a vaga específica
- Forneça recomendações acionáveis
"""

    try:
        llm = llm_service.get_audited_model()
        prompt = ChatPromptTemplate.from_template(analysis_prompt)
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({})

        result["analysis_metadata"] = {
            "analyzed_at": "timestamp",
            "job_title": job_title,
            "candidate_name": candidate_name,
            "transcript_length": len(transcript),
            "duration_seconds": duration_seconds,
            "analysis_model": settings.LLM_PRIMARY_MODEL,
            "analysis_method": "lia_ai_deep_analysis"
        }

        logger.info(f"Voice screening analysis complete - Score: {result['overall_evaluation']['overall_score']}/100")
        return result

    except Exception as e:
        logger.error(f"Error analyzing voice screening: {e}", exc_info=True)
        return {
            "error": str(e),
            "analysis_method": "error_fallback",
            "overall_evaluation": {
                "overall_score": 50,
                "recommendation": "review",
                "confidence": "baixa",
                "key_strengths": [],
                "key_concerns": ["Erro na análise automática - revisar manualmente"],
                "next_steps": "Revisar transcrição manualmente"
            },
            "summary": f"Erro na análise automática. Transcrição disponível ({len(transcript)} chars)"
        }
