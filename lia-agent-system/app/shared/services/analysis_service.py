"""
LIA Analysis Service - AI-powered candidate analysis using Claude.
Uses LLMProviderFactory for all LLM calls (Task #93 migration).

Enhanced with BARS rubric evaluation and WSI inferential trait extraction
for unified profile analysis (Task #35).
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "analysis_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import json
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisType,
    CandidateAnalysisResult,
    CandidateInput,
    ScoreBreakdown,
)
from app.shared.prompts.loader import PromptLoader
from app.shared.providers.llm_factory import get_provider_for_tenant

logger = logging.getLogger(__name__)

ARCHETYPES = [
    "Catalisador Visionário",
    "Executor Confiável",
    "Guardião de Clientes",
    "Estrategista Analítico",
    "Mediador Adaptável",
    "Rainmaker Audacioso",
    "Operador Resiliente",
    "Arquiteto Metódico"
]

ARCHETYPE_BIG_FIVE_MAP = {
    "Catalisador Visionário": {"openness": 80, "extraversion": 70, "conscientiousness": 55, "agreeableness": 50, "neuroticism": 35},
    "Executor Confiável": {"conscientiousness": 80, "agreeableness": 70, "openness": 50, "extraversion": 50, "neuroticism": 30},
    "Guardião de Clientes": {"agreeableness": 80, "extraversion": 70, "conscientiousness": 60, "openness": 50, "neuroticism": 35},
    "Estrategista Analítico": {"openness": 75, "conscientiousness": 75, "extraversion": 40, "agreeableness": 50, "neuroticism": 30},
    "Mediador Adaptável": {"agreeableness": 75, "openness": 70, "extraversion": 55, "conscientiousness": 50, "neuroticism": 40},
    "Rainmaker Audacioso": {"extraversion": 80, "openness": 70, "conscientiousness": 60, "agreeableness": 40, "neuroticism": 35},
    "Operador Resiliente": {"conscientiousness": 80, "openness": 45, "extraversion": 45, "agreeableness": 55, "neuroticism": 20},
    "Arquiteto Metódico": {"conscientiousness": 85, "openness": 65, "extraversion": 35, "agreeableness": 50, "neuroticism": 25},
}

WSI_TRAIT_INFERENCE_PROMPT = """Analise o CV/texto abaixo e extraia indicadores comportamentais Big Five (OCEAN) e o arquétipo profissional mais provável.

## CV/Texto do Candidato:
{cv_text}

## Instrução:
Com base APENAS nas evidências textuais do CV, infira:
1. Scores Big Five (0-100 para cada trait)
2. O arquétipo profissional mais provável dentre: {archetypes}
3. Evidências textuais que suportam cada inferência
4. Traits profissionais observáveis

IMPORTANTE: Se o CV tiver menos de 200 palavras, seja conservador nos scores (mais próximos de 50).

Retorne SOMENTE JSON válido:
{{
    "big_five": {{
        "openness": <0-100>,
        "conscientiousness": <0-100>,
        "extraversion": <0-100>,
        "agreeableness": <0-100>,
        "neuroticism": <0-100>
    }},
    "archetype": "<um dos 8 arquétipos>",
    "archetype_confidence": <0.0-1.0>,
    "evidences": ["evidência 1", "evidência 2", "evidência 3"],
    "professional_traits": ["trait 1", "trait 2", "trait 3"],
    "reasoning": "<explicação breve da inferência>"
}}"""

LIA_ANALYSIS_PROMPT = PromptLoader.get_domain_prompt("analysis")


class AnalysisService:
    """Service for AI-powered candidate analysis via LLMProviderFactory."""

    def _is_rate_limit_error(self, exception: BaseException) -> bool:
        """Check if the exception is a rate limit error."""
        error_msg = str(exception)
        return (
            "429" in error_msg
            or "RATELIMIT_EXCEEDED" in error_msg
            or "quota" in error_msg.lower()
            or "rate limit" in error_msg.lower()
            or (hasattr(exception, "status_code") and exception.status_code == 429)
        )
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    async def _analyze_single_candidate(
        self,
        candidate: CandidateInput,
        context: str = ""
    ) -> CandidateAnalysisResult:
        """Analyze a single candidate using Claude AI."""
        
        # SEG-3B: data minimization — remover PII do CV antes de enviar ao LLM (LGPD Art. 12)
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        _cv_text_raw = candidate.cv_text[:3000] if candidate.cv_text else "Não disponível"
        _cv_text_clean = strip_pii_for_llm_prompt(_cv_text_raw)

        prompt = LIA_ANALYSIS_PROMPT.format(
            context=context,
            candidate_name=candidate.name or "Não informado",
            candidate_position=candidate.position or "Não informado",
            candidate_location=candidate.location or "Não informado",
            candidate_company=candidate.company or "Não informado",
            candidate_skills=", ".join(candidate.skills) if candidate.skills else "Não informado",
            experience_years=candidate.experience_years or "Não informado",
            seniority_level=candidate.seniority_level or "Não informado",
            cv_text=_cv_text_clean,
        )
        
        try:
            container = get_provider_for_tenant()
            response_text = await container.generate_with_fallback(prompt, agent_type="AnalysisServiceAgent")
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            result_data = json.loads(response_text)
            
            score_breakdown = None
            if "score_breakdown" in result_data:
                score_breakdown = ScoreBreakdown(**result_data["score_breakdown"])
            
            return CandidateAnalysisResult(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                lia_score=result_data.get("lia_score", 50),
                fit_score=result_data.get("fit_score", 50),
                archetype=result_data.get("archetype", "Executor Confiável"),
                strengths=result_data.get("strengths", []),
                gaps=result_data.get("gaps", []),
                recommendation=result_data.get("recommendation", "Análise pendente"),
                recommendation_level=result_data.get("recommendation_level", "potential"),
                explanation=result_data.get("explanation", ""),
                score_breakdown=score_breakdown,
                potential_roles=result_data.get("potential_roles", [])
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return self._create_fallback_result(candidate)
        except Exception as e:
            logger.error(f"Error analyzing candidate {candidate.id}: {e}")
            raise
    
    def _create_fallback_result(self, candidate: CandidateInput) -> CandidateAnalysisResult:
        """Create a fallback result when AI analysis fails."""
        return CandidateAnalysisResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            lia_score=50,
            fit_score=50,
            archetype="Executor Confiável",
            strengths=["Perfil em análise"],
            gaps=["Informações insuficientes"],
            recommendation="Requer análise manual devido a erro na análise automática",
            recommendation_level="potential",
            explanation="A análise automática não pôde ser completada. Recomendamos revisão manual.",
            score_breakdown=ScoreBreakdown(
                match_tecnico=50,
                fit_personalidade=50,
                relevancia_experiencia=50,
                alinhamento_cultural=50
            ),
            potential_roles=[]
        )
    
    async def analyze_candidates(
        self,
        request: AnalysisRequest
    ) -> AnalysisResponse:
        """Analyze multiple candidates."""
        
        context = ""
        if request.analysis_type == AnalysisType.CONTEXTUAL and request.job_title:
            context = f"""## CONTEXTO DA VAGA:
Título: {request.job_title}
Requisitos: {', '.join(request.job_requirements) if request.job_requirements else 'Não especificado'}
Descrição: {request.job_description[:1500] if request.job_description else 'Não especificado'}

Para esta análise CONTEXTUAL, avalie o candidato em relação a esta vaga específica."""
        else:
            context = """## ANÁLISE GERAL (sem vaga específica):
Avalie o potencial geral do candidato, identificando seu arquétipo, pontos fortes e roles mais adequados."""
        
        results: list[CandidateAnalysisResult] = []
        
        for candidate in request.candidates:
            try:
                result = await self._analyze_single_candidate(candidate, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze candidate {candidate.id}: {e}")
                results.append(self._create_fallback_result(candidate))
        
        total_score = sum(r.lia_score for r in results)
        average_score = total_score / len(results) if results else 0
        
        position_counts: dict = {}
        location_counts: dict = {}
        skill_counts: dict = {}
        
        for i, candidate in enumerate(request.candidates):
            if candidate.position:
                pos = candidate.position
                if pos not in position_counts:
                    position_counts[pos] = {"count": 0, "total_score": 0}
                position_counts[pos]["count"] += 1
                position_counts[pos]["total_score"] += results[i].lia_score
            
            if candidate.location:
                loc = candidate.location
                if loc not in location_counts:
                    location_counts[loc] = {"count": 0, "total_score": 0}
                location_counts[loc]["count"] += 1
                location_counts[loc]["total_score"] += results[i].lia_score
            
            for skill in (candidate.skills or []):
                if skill not in skill_counts:
                    skill_counts[skill] = 0
                skill_counts[skill] += 1
        
        by_position = {
            pos: {"count": data["count"], "avgScore": round(data["total_score"] / data["count"], 1)}
            for pos, data in position_counts.items()
        }
        by_location = {
            loc: {"count": data["count"], "avgScore": round(data["total_score"] / data["count"], 1)}
            for loc, data in location_counts.items()
        }
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        skills_percentage = {skill: round((count / len(request.candidates)) * 100) for skill, count in top_skills}
        
        highly_recommended = sum(1 for r in results if r.recommendation_level == "highly_recommended")
        recommended = sum(1 for r in results if r.recommendation_level == "recommended")
        potential = sum(1 for r in results if r.recommendation_level == "potential")
        
        recommendations = []
        alerts = []
        
        if highly_recommended > 0:
            recommendations.append(f"{highly_recommended} candidatos com score acima de 85% - recomendo contato imediato")
            alerts.append({"type": "success", "message": f"{highly_recommended} candidatos com match perfeito identificados"})
        
        if recommended > 0:
            recommendations.append(f"{recommended} candidatos com potencial alto - considerar para processo seletivo")
        
        if potential > 0:
            recommendations.append(f"{potential} candidatos com potencial - avaliar gaps específicos")
            alerts.append({"type": "info", "message": f"{potential} candidatos com potencial para desenvolvimento"})
        
        alerts.append({"type": "info", "message": f"{len(results)} candidatos analisados com sucesso"})
        
        return AnalysisResponse(
            success=True,
            total_analyzed=len(results),
            average_score=round(average_score, 1),
            results=results,
            insights={
                "byPosition": by_position,
                "byLocation": by_location,
                "skills": skills_percentage
            },
            recommendations=recommendations,
            alerts=alerts
        )

    def _compute_confidence(self, cv_text: str | None) -> str:
        if not cv_text:
            return "low"
        word_count = len(cv_text.split())
        if word_count < 200:
            return "low"
        elif word_count < 500:
            return "medium"
        return "high"

    async def _infer_wsi_traits(self, cv_text: str) -> dict[str, Any]:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        clean_text = strip_pii_for_llm_prompt(cv_text[:4000])

        prompt = WSI_TRAIT_INFERENCE_PROMPT.format(
            cv_text=clean_text,
            archetypes=", ".join(ARCHETYPES),
        )

        try:
            container = get_provider_for_tenant()
            response_text = await container.generate_with_fallback(prompt, agent_type="AnalysisServiceAgent")
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"WSI trait inference failed: {e}", exc_info=True)
            return {
                "big_five": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
                "archetype": "Executor Confiável",
                "archetype_confidence": 0.3,
                "evidences": [],
                "professional_traits": [],
                "reasoning": "Inferência falhou — usando valores padrão.",
            }

    async def _run_bars_evaluation(
        self,
        candidate_data: dict[str, Any],
        vacancy_id: str,
    ) -> dict[str, Any] | None:
        try:
            from uuid import UUID

            from sqlalchemy import select

            from app.core.database import AsyncSessionLocal
            from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
            from lia_models.job_vacancy import JobVacancy
            from lia_models.rubric import JobRequirement
            from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

            async with AsyncSessionLocal() as db:
                req_result = await db.execute(
                    select(JobRequirement).where(
                        JobRequirement.job_vacancy_id == UUID(vacancy_id)
                    )
                )
                db_requirements = req_result.scalars().all()

                if not db_requirements:
                    logger.info(f"No job requirements found for vacancy {vacancy_id}, skipping BARS")
                    return None

                requirements = []
                for req in db_requirements:
                    priority = RequirementPriorityEnum.IMPORTANT
                    if hasattr(req.priority, "value"):
                        try:
                            priority = RequirementPriorityEnum(req.priority.value.lower())
                        except ValueError:
                            pass
                    elif isinstance(req.priority, str):
                        try:
                            priority = RequirementPriorityEnum(req.priority.lower())
                        except ValueError:
                            pass
                    requirements.append(JobRequirementCreate(
                        requirement=req.requirement,
                        description=req.description,
                        priority=priority,
                        category=req.category,
                    ))

                job_result = await db.execute(
                    select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
                )
                job = job_result.scalar_one_or_none()
                job_title = job.title if job else "Vaga"

            evaluation = await rubric_evaluation_service.evaluate_candidate(
                candidate_data=candidate_data,
                requirements=requirements,
            )

            return {
                "bars_score": round(evaluation.score, 2),
                "recommendation": evaluation.recommendation,
                "strengths": evaluation.strengths,
                "concerns": evaluation.concerns,
                "reasoning": evaluation.reasoning,
                "job_title": job_title,
                "evaluations_summary": [
                    {
                        "requirement": e.requirement[:80],
                        "level": e.level.value if hasattr(e.level, "value") else str(e.level),
                        "points": e.points,
                        "weighted_points": e.weighted_points,
                    }
                    for e in evaluation.evaluations[:10]
                ],
            }
        except Exception as e:
            logger.error(f"BARS evaluation failed for vacancy {vacancy_id}: {e}", exc_info=True)
            return None

    async def analyze_profile_enriched(
        self,
        candidate_data: dict[str, Any],
        vacancy_id: str | None = None,
    ) -> dict[str, Any]:
        from datetime import datetime

        candidate_id = str(candidate_data.get("id", ""))
        candidate_name = candidate_data.get("name", "Candidato")
        cv_text = (
            candidate_data.get("resume_text")
            or candidate_data.get("cv_text")
            or candidate_data.get("self_introduction")
            or ""
        )

        confidence = self._compute_confidence(cv_text)
        logger.info(
            f"[ENRICHED_ANALYSIS] Starting for candidate={candidate_id}, "
            f"confidence={confidence}, has_vacancy={bool(vacancy_id)}"
        )

        candidate_input = CandidateInput(
            id=candidate_id,
            name=candidate_name,
            position=candidate_data.get("current_title"),
            location=candidate_data.get("location_city"),
            company=candidate_data.get("current_company"),
            cv_text=cv_text or None,
            skills=candidate_data.get("technical_skills", []),
            experience_years=candidate_data.get("years_of_experience"),
            seniority_level=candidate_data.get("seniority_level"),
        )

        context = ""
        bars_result = None
        if vacancy_id:
            bars_result = await self._run_bars_evaluation(candidate_data, vacancy_id)
            if bars_result:
                context = f"""## CONTEXTO DA VAGA:
Título: {bars_result.get('job_title', 'N/A')}
Score BARS (CV vs requisitos): {bars_result['bars_score']}%
Recomendação BARS: {bars_result['recommendation']}

Para esta análise CONTEXTUAL, avalie o candidato em relação a esta vaga específica."""
            else:
                context = """## ANÁLISE GERAL (sem requisitos formais):
Avalie o potencial geral do candidato."""
        else:
            context = """## ANÁLISE GERAL (sem vaga específica):
Avalie o potencial geral do candidato, identificando seu arquétipo, pontos fortes e roles mais adequados."""

        try:
            lia_result = await self._analyze_single_candidate(candidate_input, context)
        except Exception as e:
            logger.error(f"LIA analysis failed for {candidate_id}: {e}")
            lia_result = self._create_fallback_result(candidate_input)

        wsi_traits = {}
        if cv_text and len(cv_text.strip()) > 50:
            wsi_traits = await self._infer_wsi_traits(cv_text)
        else:
            wsi_traits = {
                "big_five": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
                "archetype": lia_result.archetype,
                "archetype_confidence": 0.2,
                "evidences": [],
                "professional_traits": [],
                "reasoning": "CV insuficiente para inferência de traits.",
            }

        big_five = wsi_traits.get("big_five", {})
        inferred_archetype = wsi_traits.get("archetype", lia_result.archetype)
        archetype_confidence = wsi_traits.get("archetype_confidence", 0.5)

        overall_score = lia_result.lia_score
        if bars_result:
            overall_score = round(lia_result.lia_score * 0.4 + bars_result["bars_score"] * 0.6, 1)

        if overall_score >= 85:
            overall_recommendation = "Altamente Recomendado"
            overall_level = "highly_recommended"
        elif overall_score >= 70:
            overall_recommendation = "Recomendado"
            overall_level = "recommended"
        elif overall_score >= 55:
            overall_recommendation = "Potencial"
            overall_level = "potential"
        elif overall_score >= 40:
            overall_recommendation = "Baixo Match"
            overall_level = "low_match"
        else:
            overall_recommendation = "Não Recomendado"
            overall_level = "not_recommended"

        result = {
            "success": True,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "analyzed_at": datetime.utcnow().isoformat(),
            "confidence": confidence,
            "confidence_note": {
                "low": "CV com menos de 200 palavras — resultados inferidos com baixa confiança. Recomenda-se triagem conversacional (WSI live).",
                "medium": "CV com conteúdo moderado — inferências razoáveis, triagem conversacional pode enriquecer.",
                "high": "CV detalhado — inferências de alta confiança.",
            }[confidence],
            "overall_assessment": {
                "score": overall_score,
                "recommendation": overall_recommendation,
                "recommendation_level": overall_level,
                "methodology": "BARS + WSI Inferential + LIA AI Analysis",
            },
            "technical_fit": {
                "source": "bars" if bars_result else "lia_ai",
                "bars_score": bars_result["bars_score"] if bars_result else None,
                "bars_recommendation": bars_result["recommendation"] if bars_result else None,
                "strengths": bars_result["strengths"] if bars_result else lia_result.strengths,
                "concerns": bars_result["concerns"] if bars_result else lia_result.gaps,
                "evaluations": bars_result.get("evaluations_summary", []) if bars_result else [],
                "job_title": bars_result.get("job_title") if bars_result else None,
                "vacancy_id": vacancy_id,
            },
            "behavioral_profile": {
                "archetype": inferred_archetype,
                "archetype_confidence": archetype_confidence,
                "big_five": big_five,
                "professional_traits": wsi_traits.get("professional_traits", []),
                "evidences": wsi_traits.get("evidences", []),
                "reasoning": wsi_traits.get("reasoning", ""),
                "expected_big_five": ARCHETYPE_BIG_FIVE_MAP.get(inferred_archetype, {}),
            },
            "lia_analysis": {
                "lia_score": lia_result.lia_score,
                "fit_score": lia_result.fit_score,
                "archetype": lia_result.archetype,
                "strengths": lia_result.strengths,
                "gaps": lia_result.gaps,
                "explanation": lia_result.explanation,
                "score_breakdown": lia_result.score_breakdown.dict() if lia_result.score_breakdown else None,
                "potential_roles": lia_result.potential_roles,
            },
        }

        logger.info(
            f"[ENRICHED_ANALYSIS] Completed for candidate={candidate_id}: "
            f"overall={overall_score}, confidence={confidence}, "
            f"archetype={inferred_archetype}, bars={'yes' if bars_result else 'no'}"
        )

        await self._persist_enriched_analysis(candidate_id, vacancy_id, result)

        return result

    async def _persist_enriched_analysis(
        self,
        candidate_id: str,
        vacancy_id: str | None,
        analysis: dict[str, Any],
    ) -> None:
        from uuid import UUID

        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from lia_models.candidate import Candidate, VacancyCandidate

        enriched_payload = {
            "overall_score": analysis.get("overall_assessment", {}).get("score"),
            "recommendation": analysis.get("overall_assessment", {}).get("recommendation"),
            "recommendation_level": analysis.get("overall_assessment", {}).get("recommendation_level"),
            "confidence": analysis.get("confidence"),
            "archetype": analysis.get("behavioral_profile", {}).get("archetype"),
            "big_five": analysis.get("behavioral_profile", {}).get("big_five"),
            "bars_score": analysis.get("technical_fit", {}).get("bars_score"),
            "lia_score": analysis.get("lia_analysis", {}).get("lia_score"),
            "vacancy_id": vacancy_id,
            "analyzed_at": analysis.get("analyzed_at"),
        }

        async with AsyncSessionLocal() as db:
            if vacancy_id:
                try:
                    UUID(vacancy_id)
                except (ValueError, AttributeError):
                    vacancy_id = None

            if vacancy_id:
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        VacancyCandidate.candidate_id == UUID(candidate_id),
                        VacancyCandidate.vacancy_id == UUID(vacancy_id),
                    )
                )
                vc = vc_result.scalar_one_or_none()
                if vc:
                    current = vc.additional_data or {}
                    current["enriched_analysis"] = enriched_payload
                    vc.additional_data = current
                    await db.commit()
                    logger.info(f"[ENRICHED_ANALYSIS] Persisted to VacancyCandidate.additional_data: candidate={candidate_id}, vacancy={vacancy_id}")
                    return

            cand_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            cand = cand_result.scalar_one_or_none()
            if cand:
                current = cand.lia_insights or {}
                current["enriched_analysis"] = enriched_payload
                cand.lia_insights = current
                await db.commit()
                logger.info(f"[ENRICHED_ANALYSIS] Persisted to Candidate.lia_insights: candidate={candidate_id}")


analysis_service = AnalysisService()
