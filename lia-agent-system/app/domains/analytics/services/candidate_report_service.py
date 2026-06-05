"""
Candidate Report Service - Generate AI-powered candidate evaluations.

This service generates comprehensive candidate reports/pareceres
for hiring managers, including:
- Executive summary
- Professional experience analysis
- Technical competencies assessment
- Behavioral competencies evaluation
- Screening results (if available)
- Strengths and areas of attention
- Final recommendation
"""
import logging
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.cv_screening.constants.wsi_constants import WSI_DIMENSION_LABELS
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy
from lia_models.voice_screening import VoiceScreeningAnalysis, VoiceScreeningCall
from app.domains.ai.services.llm import llm_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)
_fairness_guard = FairnessGuard()


class RecommendationLevel(StrEnum):
    HIGHLY_RECOMMENDED = "HIGHLY_RECOMMENDED"
    RECOMMENDED = "RECOMMENDED"
    POTENTIAL = "POTENTIAL"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    INCOMPLETE = "INCOMPLETE"


class DataSourceType(StrEnum):
    CV = "cv"
    TEXT_SCREENING = "text_screening"
    VOICE_SCREENING = "voice_screening"
    INTERVIEW = "interview"
    BIG_FIVE = "big_five"
    WSI = "wsi"
    TECHNICAL_TEST = "technical_test"


class ParecerGenerationError(Exception):
    """Levantada quando a geração de seções do parecer falha.
    Fail-loud: NUNCA cair em fallback degradado silencioso (CLAUDE.md REGRA 4)."""


class CandidateReportService:
    """
    Service for generating comprehensive candidate reports.
    """
    
    async def generate_parecer(
        self,
        db: AsyncSession,
        candidate_id: str,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate the 7-section Parecer Automático for a candidate.
        
        Sections:
        1. Resumo Executivo
        2. Experiência Profissional
        3. Competências Técnicas
        4. Competências Comportamentais (conditional - only if WSI/Big Five)
        5. Resultados da Triagem (conditional - only if screening data)
        6. Pontos Fortes e Atenção
        7. Recomendação Final
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            job_id: Optional job vacancy ID for context
            
        Returns:
            Complete parecer with 7 sections and metadata
        """
        candidate = await self._get_candidate(db, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        job = None
        if job_id:
            job = await self._get_job(db, job_id)
        
        available_data = await self._detect_available_data(db, candidate_id, candidate)
        
        screening_data = None
        if available_data["has_voice_screening"] or available_data["has_text_screening"]:
            screening_data = await self._get_screening_data(db, candidate_id)
        
        wsi_data = None
        if available_data["has_wsi"]:
            wsi_data = await self._get_wsi_data(db, candidate_id)
        
        big_five_data = None
        if available_data["has_big_five"]:
            big_five_data = await self._get_big_five_data(db, candidate_id)
        
        interview_data = None
        if available_data["has_interview"]:
            interview_data = await self._get_interview_data(db, candidate_id)
        
        sections = await self._generate_parecer_sections(
            candidate=candidate,
            job=job,
            screening_data=screening_data,
            wsi_data=wsi_data,
            big_five_data=big_five_data,
            interview_data=interview_data,
            available_data=available_data
        )
        
        completeness_score = self._calculate_completeness_score(available_data)
        data_sources = self._get_data_sources_list(available_data)
        
        recommendation = self._determine_recommendation_level(
            sections=sections,
            completeness_score=completeness_score,
            screening_data=screening_data
        )
        
        qualification_matrix = None
        if job is not None:
            try:
                from app.domains.analytics.services.criteria_derivation import (
                    derive_from_job,
                )
                qm = derive_from_job(
                    self._build_job_dict(job),
                    self._build_candidate_dict(candidate),
                    None,
                )
                qualification_matrix = qm.model_dump()
            except Exception as _qm_err:
                # Matriz é enriquecimento; ausência (None) é honesta, não fabricada.
                logger.warning(f"qualification_matrix derivation skipped: {_qm_err}")

        parecer = {
            "id": f"parecer_{candidate_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "version": "2.0",
            "generated_at": datetime.utcnow().isoformat(),
            "candidate": {
                "id": str(candidate.id),
                "name": candidate.name,
                "email": candidate.email,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "linkedin_url": candidate.linkedin_url,
                "location": f"{candidate.location_city or ''}, {candidate.location_country or ''}".strip(", "),
            },
            "job": {
                "id": str(job.id),
                "title": job.title,
                "department": job.department,
            } if job else None,
            "sections": sections,
            "completeness_score": completeness_score,
            "data_sources": data_sources,
            "data_profile": self._get_data_profile(available_data),
            "recommendation": recommendation,
            "lia_score": await self._calculate_lia_score(candidate, job, screening_data),
            "qualification_matrix": qualification_matrix,
        }
        
        return parecer
    
    async def _detect_available_data(
        self, 
        db: AsyncSession, 
        candidate_id: str,
        candidate: Candidate
    ) -> dict[str, bool]:
        """
        Detect which data sources are available for the candidate.
        
        Returns dict indicating availability of each data source.
        """
        has_cv = bool(
            candidate.resume_text or 
            candidate.resume_url or
            (candidate.technical_skills and len(candidate.technical_skills) > 0) or
            candidate.current_title
        )
        
        # ADR-001-EXEMPT: cross-domain read of VoiceScreeningCall for analytics report
        # readiness check. WsiRepository is owned by another agent in Sprint Q2 cleanup;
        # consolidate this query into voice repo in follow-up sprint.
        voice_screening = await db.execute(
            select(VoiceScreeningCall)
            .where(VoiceScreeningCall.candidate_id == candidate_id)
            .where(VoiceScreeningCall.processing_status == "completed")
        )
        has_voice_screening = voice_screening.scalar_one_or_none() is not None
        
        has_text_screening = bool(
            candidate.lia_insights and 
            candidate.lia_insights.get("screening_answers")
        )
        
        has_wsi = bool(
            candidate.lia_insights and 
            candidate.lia_insights.get("wsi_score")
        )
        
        has_big_five = bool(
            candidate.lia_insights and 
            candidate.lia_insights.get("big_five_profile")
        )
        
        has_interview = bool(
            candidate.lia_insights and 
            candidate.lia_insights.get("interview_notes")
        )
        
        has_technical_test = bool(
            candidate.lia_insights and 
            candidate.lia_insights.get("technical_test_results")
        )
        
        return {
            "has_cv": has_cv,
            "has_text_screening": has_text_screening,
            "has_voice_screening": has_voice_screening,
            "has_wsi": has_wsi,
            "has_big_five": has_big_five,
            "has_interview": has_interview,
            "has_technical_test": has_technical_test,
        }
    
    def _calculate_completeness_score(self, available_data: dict[str, bool]) -> float:
        """
        Calculate completeness score (0-1) based on available data.
        
        Weights:
        - CV: 30%
        - Screening (text or voice): 25%
        - WSI/Big Five: 20%
        - Interview: 15%
        - Technical Test: 10%
        """
        score = 0.0
        
        if available_data["has_cv"]:
            score += 0.30
        
        if available_data["has_voice_screening"]:
            score += 0.25
        elif available_data["has_text_screening"]:
            score += 0.20
        
        if available_data["has_wsi"] or available_data["has_big_five"]:
            score += 0.20
        
        if available_data["has_interview"]:
            score += 0.15
        
        if available_data["has_technical_test"]:
            score += 0.10
        
        return round(min(score, 1.0), 2)
    
    def _get_data_sources_list(self, available_data: dict[str, bool]) -> list[str]:
        """Get list of available data sources."""
        sources = []
        
        if available_data["has_cv"]:
            sources.append(DataSourceType.CV.value)
        if available_data["has_text_screening"]:
            sources.append(DataSourceType.TEXT_SCREENING.value)
        if available_data["has_voice_screening"]:
            sources.append(DataSourceType.VOICE_SCREENING.value)
        if available_data["has_wsi"]:
            sources.append(DataSourceType.WSI.value)
        if available_data["has_big_five"]:
            sources.append(DataSourceType.BIG_FIVE.value)
        if available_data["has_interview"]:
            sources.append(DataSourceType.INTERVIEW.value)
        if available_data["has_technical_test"]:
            sources.append(DataSourceType.TECHNICAL_TEST.value)
        
        return sources
    
    def _get_data_profile(self, available_data: dict[str, bool]) -> str:
        """
        Determine the data profile based on available sources.
        
        Profiles:
        - CV_ONLY: Only CV data
        - CV_TEXT_SCREENING: CV + Text Screening
        - CV_VOICE_SCREENING: CV + Voice Screening
        - COMPLETE: CV + Screening + Interview (or WSI/Big Five)
        """
        has_cv = available_data["has_cv"]
        has_screening = available_data["has_voice_screening"] or available_data["has_text_screening"]
        has_behavioral = available_data["has_wsi"] or available_data["has_big_five"]
        has_interview = available_data["has_interview"]
        
        if has_cv and has_screening and (has_behavioral or has_interview):
            return "COMPLETE"
        elif has_cv and available_data["has_voice_screening"]:
            return "CV_VOICE_SCREENING"
        elif has_cv and available_data["has_text_screening"]:
            return "CV_TEXT_SCREENING"
        elif has_cv:
            return "CV_ONLY"
        else:
            return "INCOMPLETE"
    
    def _determine_recommendation_level(
        self,
        sections: dict[str, Any],
        completeness_score: float,
        screening_data: dict | None
    ) -> dict[str, Any]:
        """
        Determine the recommendation level based on all available data.
        
        Levels:
        - HIGHLY_RECOMMENDED: Score >= 85, good screening
        - RECOMMENDED: Score 70-84
        - POTENTIAL: Score 55-69
        - NOT_RECOMMENDED: Score < 55
        - INCOMPLETE: Insufficient data (completeness < 0.3)
        """
        if completeness_score < 0.30:
            return {
                "level": RecommendationLevel.INCOMPLETE.value,
                "confidence": "low",
                "reason": "Dados insuficientes para gerar recomendação. Recomenda-se coletar mais informações do candidato.",
            }
        
        overall_score = sections.get("recomendacao_final", {}).get("score", 50)
        
        if screening_data and screening_data.get("overall_score"):
            screening_score = screening_data["overall_score"]
            overall_score = (overall_score * 0.6) + (screening_score * 0.4)
        
        if overall_score >= 85:
            level = RecommendationLevel.HIGHLY_RECOMMENDED.value
            reason = "Candidato com excelente aderência ao perfil. Priorizar para entrevista."
        elif overall_score >= 70:
            level = RecommendationLevel.RECOMMENDED.value
            reason = "Candidato com boa aderência ao perfil. Considerar para próximas etapas."
        elif overall_score >= 55:
            level = RecommendationLevel.POTENTIAL.value
            reason = "Candidato com potencial. Avaliar gaps específicos antes de prosseguir."
        else:
            level = RecommendationLevel.NOT_RECOMMENDED.value
            reason = "Candidato não apresenta aderência suficiente ao perfil."
        
        confidence = "high" if completeness_score >= 0.7 else "medium" if completeness_score >= 0.5 else "low"
        
        return {
            "level": level,
            "score": round(overall_score, 1),
            "confidence": confidence,
            "reason": reason,
        }
    
    async def _generate_parecer_sections(
        self,
        candidate: Candidate,
        job: JobVacancy | None,
        screening_data: dict | None,
        wsi_data: dict | None,
        big_five_data: dict | None,
        interview_data: dict | None,
        available_data: dict[str, bool]
    ) -> dict[str, Any]:
        """Generate all 7 sections of the parecer using AI."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em recrutamento e seleção. Gere um parecer profissional e objetivo do candidato.

O parecer deve ser baseado em dados, útil para a tomada de decisão do gestor, e seguir o formato especificado.

SEÇÕES A GERAR (em JSON):

1. resumo_executivo: {{
   "texto": "2-3 parágrafos sintetizando o perfil do candidato",
   "highlights": ["3-5 pontos-chave do perfil"]
}}

2. experiencia_profissional: {{
   "analise": "Análise da trajetória profissional",
   "anos_experiencia": número,
   "progressao_carreira": "ascendente/estável/diversificada",
   "empresas_relevantes": ["lista de empresas de destaque"],
   "gaps": ["possíveis gaps identificados"]
}}

3. competencias_tecnicas (dimensão WSI: "{label_technical}"): {{
   "skills_destacados": ["skills com maior evidência"],
   "nivel_geral": "junior/pleno/senior/especialista",
   "areas_expertise": ["áreas de maior domínio"],
   "gaps_tecnicos": ["skills que podem faltar"],
   "score": 0-100
}}

4. competencias_comportamentais (dimensão WSI: "{label_behavioral}" — APENAS SE DADOS DISPONÍVEIS): {{
   "traits_identificados": ["traços comportamentais observados"],
   "big_five": {{openness, conscientiousness, extraversion, agreeableness, stability}},
   "comunicacao": "avaliação da comunicação",
   "lideranca": "potencial de liderança",
   "score": 0-100
}}

5. resultados_triagem (APENAS SE DADOS DISPONÍVEIS): {{
   "score_geral": 0-100,
   "score_tecnico": 0-100,
   "score_comunicacao": 0-100,
   "score_cultural_fit": 0-100,
   "resumo": "resumo da triagem",
   "tipo_triagem": "texto/voz"
}}

6. pontos_fortes_e_atencao: {{
   "pontos_fortes": ["3-5 pontos fortes"],
   "pontos_atencao": ["3-5 pontos de atenção/riscos"],
   "diferenciais": ["o que destaca esse candidato"]
}}

7. recomendacao_final: {{
   "score": 0-100,
   "acao_sugerida": "AVANÇAR/CONSIDERAR/NÃO_AVANÇAR",
   "justificativa": "justificativa da recomendação",
   "proximos_passos": ["sugestões de próximos passos"]
}}

IMPORTANTE:
- Gere APENAS as seções para as quais há dados disponíveis
- Seção 4 (comportamentais) só se has_behavioral = true
- Seção 5 (triagem) só se has_screening = true
- Seja objetivo e baseado em evidências
- Evite suposições não fundamentadas

Responda em JSON válido."""),
            ("user", """DADOS DO CANDIDATO:
Nome: {candidate_name}
Cargo Atual: {current_title}
Empresa Atual: {current_company}
Localização: {location}
Skills Técnicos: {technical_skills}
Anos de Experiência: {years_experience}
Educação: {education}
Idiomas: {languages}
LinkedIn: {linkedin_url}

DADOS DISPONÍVEIS:
- has_cv: {has_cv}
- has_screening: {has_screening}
- has_behavioral: {has_behavioral}
- has_interview: {has_interview}

{job_context}

{screening_context}

{behavioral_context}

{interview_context}

Gere o parecer em formato JSON com as 7 seções especificadas.""")
        ])
        
        job_context = ""
        if job:
            job_context = f"""VAGA EM ANÁLISE:
Título: {job.title}
Departamento: {job.department}
Requisitos: {job.requirements if hasattr(job, 'requirements') else 'N/A'}
Skills Desejados: {job.required_skills if hasattr(job, 'required_skills') else 'N/A'}"""
        
        screening_context = ""
        if screening_data:
            screening_context = f"""RESULTADO DA TRIAGEM:
Score Geral: {screening_data.get('overall_score', 'N/A')}/100
Comunicação: {screening_data.get('communication_score', 'N/A')}/100
Técnico: {screening_data.get('technical_score', 'N/A')}/100
Fit Cultural: {screening_data.get('cultural_fit_score', 'N/A')}/100
Resumo: {screening_data.get('summary', 'N/A')}
Pontos Fortes: {', '.join(screening_data.get('strengths', []))}
Pontos de Atenção: {', '.join(screening_data.get('concerns', []))}"""
        
        behavioral_context = ""
        if big_five_data:
            behavioral_context = f"""PERFIL BIG FIVE:
Abertura: {big_five_data.get('openness', 'N/A')}/100
Conscienciosidade: {big_five_data.get('conscientiousness', 'N/A')}/100
Extroversão: {big_five_data.get('extraversion', 'N/A')}/100
Amabilidade: {big_five_data.get('agreeableness', 'N/A')}/100
Estabilidade: {big_five_data.get('stability', 'N/A')}/100"""
        elif wsi_data:
            behavioral_context = f"""SCORE WSI:
Score Geral: {wsi_data.get('overall_score', 'N/A')}/100
Competências Técnicas: {wsi_data.get('technical_score', 'N/A')}/100
Competências Comportamentais: {wsi_data.get('behavioral_score', 'N/A')}/100"""
        
        interview_context = ""
        if interview_data:
            interview_context = f"""NOTAS DA ENTREVISTA:
Score: {interview_data.get('score', 'N/A')}/100
Resumo: {interview_data.get('summary', 'N/A')}"""
        
        has_screening = available_data["has_voice_screening"] or available_data["has_text_screening"]
        has_behavioral = available_data["has_wsi"] or available_data["has_big_five"]
        
        llm = llm_service.get_audited_model()
        chain = prompt | llm | JsonOutputParser()
        
        try:
            result = await chain.ainvoke({
                "candidate_name": candidate.name,
                "current_title": candidate.current_title or "N/A",
                "current_company": candidate.current_company or "N/A",
                "location": f"{candidate.location_city}, {candidate.location_country}" if candidate.location_city else "N/A",
                "technical_skills": ", ".join(candidate.technical_skills or []) if candidate.technical_skills else "N/A",
                "years_experience": candidate.years_of_experience or "N/A",
                "education": candidate.education_level if hasattr(candidate, 'education_level') else "N/A",
                "languages": str(candidate.languages) if candidate.languages else "N/A",
                "linkedin_url": candidate.linkedin_url or "N/A",
                "has_cv": available_data["has_cv"],
                "has_screening": has_screening,
                "has_behavioral": has_behavioral,
                "has_interview": available_data["has_interview"],
                "job_context": job_context,
                "screening_context": screening_context,
                "behavioral_context": behavioral_context,
                "interview_context": interview_context,
                # Labels canônicos WSI para consistência nos pareceres gerados
                "label_technical": WSI_DIMENSION_LABELS["technical"],
                "label_behavioral": WSI_DIMENSION_LABELS["behavioral"],
            })
        except Exception as e:
            request_id = uuid.uuid4().hex[:12]
            logger.error(
                "Parecer sections generation failed — failing loud (no silent fallback)",
                extra={
                    "request_id": request_id,
                    "candidate_id": str(getattr(candidate, "id", "")),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise ParecerGenerationError(
                f"Falha ao gerar seções do parecer (request_id={request_id})"
            ) from e
        
        if not has_behavioral and "competencias_comportamentais" in result:
            del result["competencias_comportamentais"]

        if not has_screening and "resultados_triagem" in result:
            del result["resultados_triagem"]

        # FairnessGuard — verificar seções de avaliação do candidato (3, 4, 6)
        fairness_warnings: list[str] = []
        sections_with_eval_text = [
            "competencias_tecnicas",
            "competencias_comportamentais",
            "pontos_fortes_e_atencao",
        ]
        for section_key in sections_with_eval_text:
            section = result.get(section_key)
            if not section:
                continue
            text = " ".join(filter(None, [
                str(section.get("analise", "")),
                str(section.get("comunicacao", "")),
                " ".join(section.get("pontos_fortes", [])),
                " ".join(section.get("pontos_atencao", [])),
                " ".join(section.get("traits_identificados", [])),
            ]))
            if not text.strip():
                continue
            guard_result = _fairness_guard.check(text)
            if guard_result.is_blocked:
                logger.warning(
                    "FairnessGuard bloqueou seção do candidate_report_service",
                    extra={
                        "section": section_key,
                        "category": guard_result.category,
                        "blocked_terms": guard_result.blocked_terms,
                    },
                )
                result[section_key]["analise"] = (
                    "[Seção em revisão — conteúdo identificado para verificação de compliance]"
                )
            else:
                implicit = _fairness_guard.check_implicit_bias(text)
                if implicit.blocked_terms:
                    fairness_warnings.extend(implicit.blocked_terms)

        if fairness_warnings:
            result["fairness_warnings"] = fairness_warnings

        return result
    
    def _build_candidate_dict(self, candidate) -> dict[str, Any]:
        """Adapta o ORM Candidate para o dict puro consumido por criteria_derivation."""
        return {
            "technical_skills": list(getattr(candidate, "technical_skills", None) or []),
            "seniority_level": getattr(candidate, "seniority_level", None),
            "years_of_experience": getattr(candidate, "years_of_experience", None),
            "location_city": getattr(candidate, "location_city", None),
            "location_state": getattr(candidate, "location_state", None),
            "location_country": getattr(candidate, "location_country", None),
            "languages": getattr(candidate, "languages", None),
            "current_title": getattr(candidate, "current_title", None),
        }

    def _build_job_dict(self, job) -> dict[str, Any]:
        """Adapta o ORM JobVacancy para o dict puro consumido por criteria_derivation."""
        if not job:
            return {}
        return {
            "technical_requirements": getattr(job, "technical_requirements", None) or [],
            "languages": getattr(job, "languages", None) or [],
            "behavioral_competencies": getattr(job, "behavioral_competencies", None) or [],
            "requirements": getattr(job, "requirements", None) or [],
        }


    async def _get_wsi_data(self, db: AsyncSession, candidate_id: str) -> dict | None:
        """Get WSI data for candidate."""
        candidate = await self._get_candidate(db, candidate_id)
        if candidate and candidate.lia_insights:
            return candidate.lia_insights.get("wsi_score")
        return None
    
    async def _get_big_five_data(self, db: AsyncSession, candidate_id: str) -> dict | None:
        """Get Big Five data for candidate."""
        candidate = await self._get_candidate(db, candidate_id)
        if candidate and candidate.lia_insights:
            return candidate.lia_insights.get("big_five_profile")
        return None
    
    async def _get_interview_data(self, db: AsyncSession, candidate_id: str) -> dict | None:
        """Get interview data for candidate."""
        candidate = await self._get_candidate(db, candidate_id)
        if candidate and candidate.lia_insights:
            return candidate.lia_insights.get("interview_notes")
        return None
    
    async def generate_report(
        self,
        db: AsyncSession,
        candidate_id: str,
        job_id: str | None = None,
        include_screening: bool = True,
        include_tests: bool = True,
        format: str = "detailed"
    ) -> dict[str, Any]:
        """
        Generate a comprehensive candidate report (legacy method).
        
        This method maintains backward compatibility with existing code.
        For the new 7-section parecer, use generate_parecer() instead.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            job_id: Optional job vacancy ID for context
            include_screening: Include voice screening results
            include_tests: Include test results (English, Big Five)
            format: Report format (detailed, executive, comparison)
            
        Returns:
            Complete report data
        """
        candidate = await self._get_candidate(db, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        job = None
        if job_id:
            job = await self._get_job(db, job_id)
        
        screening_data = None
        if include_screening:
            screening_data = await self._get_screening_data(db, candidate_id)
        
        report_data = await self._generate_ai_analysis(
            candidate=candidate,
            job=job,
            screening_data=screening_data,
            format=format
        )
        
        available_data = await self._detect_available_data(db, candidate_id, candidate)
        
        report = {
            "id": f"report_{candidate_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "candidate": {
                "id": str(candidate.id),
                "name": candidate.name,
                "email": candidate.email,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "linkedin_url": candidate.linkedin_url,
                "location": f"{candidate.location_city or ''}, {candidate.location_country or ''}".strip(", "),
            },
            "job": {
                "id": str(job.id),
                "title": job.title,
                "department": job.department,
            } if job else None,
            "format": format,
            "sections": report_data,
            "lia_score": await self._calculate_lia_score(candidate, job, screening_data),
            "recommendation": report_data.get("recommendation"),
            "completeness_score": self._calculate_completeness_score(available_data),
            "data_sources": self._get_data_sources_list(available_data),
        }
        
        return report
    
    async def _get_candidate(self, db: AsyncSession, candidate_id: str) -> Candidate | None:
        """Get candidate by ID."""
        repo = CandidateRepository(db)
        return await repo.get_by_id_str(candidate_id)
    
    async def _get_job(self, db: AsyncSession, job_id: str) -> JobVacancy | None:
        """Get job vacancy by ID."""
        from uuid import UUID
        repo = JobVacancyCrudRepository(db)
        try:
            return await repo.get_vacancy_by_id_only(UUID(job_id))
        except (ValueError, TypeError):
            return None
    
    async def _get_screening_data(self, db: AsyncSession, candidate_id: str) -> dict | None:
        """Get voice screening data for candidate."""
        # ADR-001-EXEMPT: cross-domain JOIN on voice_screening tables for analytics
        # report. WsiRepository is owned by another agent (Sprint Q2 scope split);
        # promote this JOIN to a voice repo method in a follow-up sprint.
        result = await db.execute(
            select(VoiceScreeningCall, VoiceScreeningAnalysis)
            .join(VoiceScreeningAnalysis, VoiceScreeningCall.id == VoiceScreeningAnalysis.screening_call_id, isouter=True)
            .where(VoiceScreeningCall.candidate_id == candidate_id)
            .order_by(VoiceScreeningCall.created_at.desc())
        )
        row = result.first()
        
        if not row:
            return None
        
        call, analysis = row
        
        return {
            "call_duration": call.duration_seconds if call else None,
            "call_status": call.call_status if call else None,
            "overall_score": analysis.overall_score if analysis else None,
            "communication_score": analysis.comm_score if analysis else None,
            "technical_score": analysis.tech_score if analysis else None,
            "cultural_fit_score": analysis.fit_score if analysis else None,
            "summary": analysis.summary if analysis else None,
            "strengths": analysis.key_strengths if analysis else [],
            "concerns": analysis.key_concerns if analysis else [],
            "recommendation": analysis.overall_recommendation if analysis else None,
            "screening_type": "voice" if call else None,
        }
    
    async def _generate_ai_analysis(
        self,
        candidate: Candidate,
        job: JobVacancy | None,
        screening_data: dict | None,
        format: str
    ) -> dict[str, Any]:
        """Generate AI-powered analysis of the candidate."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em recrutamento e seleção. Gere um parecer profissional e detalhado do candidato.

O parecer deve ser objetivo, baseado em dados, e útil para a tomada de decisão do gestor.

FORMATO: {format}
- detailed: Parecer completo com todas as seções
- executive: Resumo executivo focado em pontos-chave
- comparison: Foco em pontos de comparação com a vaga

SEÇÕES OBRIGATÓRIAS:
1. resumo_executivo: 2-3 parágrafos sintetizando o perfil
2. experiencia_profissional: Análise da trajetória
3. competencias_tecnicas: Avaliação de skills técnicos
4. competencias_comportamentais: Soft skills observadas
5. pontos_fortes: Lista de 3-5 pontos positivos
6. pontos_atencao: Lista de 3-5 pontos de atenção/riscos
7. fit_com_vaga: Análise de aderência (se vaga fornecida)
8. recommendation: AVANÇAR, CONSIDERAR, ou NÃO_AVANÇAR com justificativa

Responda em JSON."""),
            ("user", """DADOS DO CANDIDATO:
Nome: {candidate_name}
Cargo Atual: {current_title}
Empresa Atual: {current_company}
Localização: {location}
Skills Técnicos: {technical_skills}
Anos de Experiência: {years_experience}
Educação: {education}
Idiomas: {languages}

{job_context}

{screening_context}

Gere o parecer em formato JSON com as seções especificadas.""")
        ])
        
        job_context = ""
        if job:
            job_context = f"""VAGA EM ANÁLISE:
Título: {job.title}
Departamento: {job.department}
Requisitos: {job.requirements if hasattr(job, 'requirements') else 'N/A'}
Skills Desejados: {job.required_skills if hasattr(job, 'required_skills') else 'N/A'}"""
        
        screening_context = ""
        if screening_data:
            screening_context = f"""RESULTADO DA TRIAGEM POR VOZ:
Score Geral: {screening_data.get('overall_score', 'N/A')}/100
Comunicação: {screening_data.get('communication_score', 'N/A')}/100
Técnico: {screening_data.get('technical_score', 'N/A')}/100
Fit Cultural: {screening_data.get('cultural_fit_score', 'N/A')}/100
Resumo: {screening_data.get('summary', 'N/A')}
Pontos Fortes: {', '.join(screening_data.get('strengths', []))}
Pontos de Atenção: {', '.join(screening_data.get('concerns', []))}"""
        
        llm = llm_service.get_audited_model()
        chain = prompt | llm | JsonOutputParser()
        
        result = await chain.ainvoke({
            "format": format,
            "candidate_name": candidate.name,
            "current_title": candidate.current_title or "N/A",
            "current_company": candidate.current_company or "N/A",
            "location": f"{candidate.location_city}, {candidate.location_country}" if candidate.location_city else "N/A",
            "technical_skills": ", ".join(candidate.technical_skills or []) if candidate.technical_skills else "N/A",
            "years_experience": candidate.years_of_experience or "N/A",
            "education": candidate.education_level if hasattr(candidate, 'education_level') else "N/A",
            "languages": str(candidate.languages) if candidate.languages else "N/A",
            "job_context": job_context,
            "screening_context": screening_context,
        })
        
        return result
    
    async def _calculate_lia_score(
        self,
        candidate: Candidate,
        job: JobVacancy | None,
        screening_data: dict | None
    ) -> dict[str, Any]:
        """Calculate the LIA score (overall AI assessment)."""
        scores = {
            "profile_completeness": self._calculate_profile_completeness(candidate),
            "skills_match": 0,
            "experience_relevance": 0,
            "screening_score": 0,
        }
        
        if job and hasattr(candidate, 'technical_skills') and candidate.technical_skills:
            job_skills = job.required_skills if hasattr(job, 'required_skills') and job.required_skills else []
            if job_skills:
                matched = len(set(candidate.technical_skills) & set(job_skills))
                scores["skills_match"] = min(100, int((matched / len(job_skills)) * 100))
        
        if candidate.years_of_experience:
            scores["experience_relevance"] = min(100, candidate.years_of_experience * 10)
        
        if screening_data and screening_data.get("overall_score"):
            scores["screening_score"] = screening_data["overall_score"]
        
        weights = {
            "profile_completeness": 0.15,
            "skills_match": 0.35,
            "experience_relevance": 0.20,
            "screening_score": 0.30,
        }
        
        if not screening_data:
            weights["screening_score"] = 0
            weights["skills_match"] = 0.45
            weights["experience_relevance"] = 0.25
            weights["profile_completeness"] = 0.30
        
        overall = sum(scores[k] * weights[k] for k in scores)
        
        return {
            "overall": round(overall, 1),
            "breakdown": scores,
            "confidence": 0.85 if screening_data else 0.60,
        }
    
    def _calculate_profile_completeness(self, candidate: Candidate) -> int:
        """Calculate how complete the candidate profile is."""
        fields = [
            candidate.name,
            candidate.email,
            candidate.current_title,
            candidate.current_company,
            candidate.location_city,
            candidate.technical_skills,
            candidate.years_of_experience,
            candidate.linkedin_url,
        ]
        
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)
    
    async def generate_comparison_report(
        self,
        db: AsyncSession,
        candidate_ids: list[str],
        job_id: str
    ) -> dict[str, Any]:
        """
        Generate a comparison report for multiple candidates.
        
        Args:
            db: Database session
            candidate_ids: List of candidate IDs to compare
            job_id: Job vacancy ID for context
            
        Returns:
            Comparison report data
        """
        if len(candidate_ids) < 2:
            raise ValueError("Need at least 2 candidates to compare")
        
        candidates_data = []
        for cid in candidate_ids:
            report = await self.generate_parecer(
                db=db,
                candidate_id=cid,
                job_id=job_id,
            )
            candidates_data.append(report)
        
        candidates_data.sort(
            key=lambda x: x["recommendation"].get("score", 0), 
            reverse=True
        )
        
        comparison = {
            "id": f"comparison_{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "candidates": candidates_data,
            "ranking": [
                {
                    "rank": i + 1,
                    "candidate_id": c["candidate"]["id"],
                    "candidate_name": c["candidate"]["name"],
                    "recommendation_level": c["recommendation"]["level"],
                    "score": c["recommendation"].get("score", 0),
                    "completeness_score": c["completeness_score"],
                }
                for i, c in enumerate(candidates_data)
            ],
            "summary": await self._generate_comparison_summary(candidates_data),
        }
        
        return comparison
    
    async def _generate_comparison_summary(self, candidates_data: list[dict]) -> str:
        """Generate a summary comparing the candidates."""
        if not candidates_data:
            return "Nenhum candidato para comparar."
        
        best = candidates_data[0]
        score = best["recommendation"].get("score", 0)
        summary = f"Após análise comparativa, {best['candidate']['name']} apresenta o melhor fit geral para a posição "
        summary += f"com score de {score:.1f}/100 e nível de recomendação {best['recommendation']['level']}. "
        
        if len(candidates_data) > 1:
            runner_up = candidates_data[1]
            runner_score = runner_up["recommendation"].get("score", 0)
            diff = score - runner_score
            summary += f"A diferença para o segundo colocado ({runner_up['candidate']['name']}) é de {diff:.1f} pontos."
        
        return summary


candidate_report_service = CandidateReportService()
