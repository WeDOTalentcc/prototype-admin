"""
Explainability Service for AI Governance.

This service generates human-readable explanations of AI decisions,
enabling transparency for candidates and compliance with AI governance requirements.
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "explainability_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import logging
from typing import Any

from sqlalchemy import and_, select

from app.core.database import AsyncSessionLocal
from lia_models.audit_log import AuditLog
from app.shared.services.audit_service import PROTECTED_CRITERIA

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """Service for generating human-readable explanations of AI decisions."""
    
    CRITERIA_LABELS = {
        "skills": "Competências técnicas",
        "experience": "Experiência profissional",
        "wsi_score": "Desempenho na entrevista WSI",
        "screening_responses": "Respostas da triagem",
        "education": "Formação acadêmica",
        "languages": "Idiomas",
        "certifications": "Certificações",
        "soft_skills": "Competências comportamentais",
        "culture_fit": "Adequação cultural",
        "availability": "Disponibilidade",
        "salary_expectation": "Expectativa salarial",
    }
    
    IGNORED_LABELS = {
        "age": "Idade",
        "gender": "Gênero",
        "ethnicity": "Etnia/raça",
        "marital_status": "Estado civil",
        "photo": "Foto/aparência",
        "institution": "Instituição de ensino específica",
        "address": "Endereço/bairro",
        "religion": "Religião",
        "disability": "Condição de deficiência",
        "cv_gaps": "Intervalos no currículo",
        "nationality": "Nacionalidade",
        "political_affiliation": "Filiação política",
    }
    
    async def generate_candidate_explanation(
        self,
        company_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        include_suggestions: bool = True
    ) -> dict[str, Any]:
        """
        Generate a transparent explanation for a candidate about their evaluation.
        
        Args:
            company_id: The company/tenant ID
            candidate_id: The candidate ID
            job_vacancy_id: The job vacancy ID
            include_suggestions: Whether to include improvement suggestions
            
        Returns:
            Dictionary with explanation details
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.company_id == company_id,
                        AuditLog.candidate_id == candidate_id,
                        AuditLog.job_vacancy_id == job_vacancy_id
                    )
                )
                .order_by(AuditLog.created_at.asc())
            )
            
            result = await session.execute(query)
            decisions = result.scalars().all()
            
            if not decisions:
                return {
                    "status": "no_data",
                    "message": "Nenhuma avaliação encontrada para este candidato nesta vaga."
                }
            
            latest_decision = decisions[-1]
            
            evaluation_criteria = []
            criteria_used = latest_decision.criteria_used or []
            for criterion in criteria_used:
                evaluation_criteria.append({
                    "criterion": self.CRITERIA_LABELS.get(criterion, criterion),
                    "key": criterion,
                    "evaluated": True
                })
            
            criteria_ignored = latest_decision.criteria_ignored or []
            
            transparency_note = (
                "Para garantir um processo justo, os seguintes critérios NÃO foram considerados: " +
                ", ".join([self.IGNORED_LABELS.get(c, c) for c in PROTECTED_CRITERIA])
            )
            
            explanation = {
                "status": latest_decision.decision,
                "overall_score": latest_decision.score,
                "confidence": latest_decision.confidence,
                "evaluation_criteria": evaluation_criteria,
                "reasoning": latest_decision.reasoning or [],
                "criteria_evaluated": criteria_used,
                "criteria_not_used": criteria_ignored,
                "transparency_note": transparency_note,
                "decision_history": [
                    {
                        "id": d.id,
                        "agent": d.agent_name,
                        "type": d.decision_type,
                        "decision": d.decision,
                        "score": d.score,
                        "created_at": d.created_at.isoformat() if d.created_at else None
                    }
                    for d in decisions
                ],
                "suggestions": []
            }
            
            if include_suggestions and latest_decision.decision == "rejected":
                explanation["suggestions"] = self._generate_improvement_suggestions(latest_decision)
            
            logger.info(
                f"📝 Generated explanation for candidate {candidate_id} "
                f"on job {job_vacancy_id}: {latest_decision.decision}"
            )
            
            return explanation
    
    def _generate_improvement_suggestions(self, decision: AuditLog) -> list[str]:
        """
        Generate actionable suggestions based on the evaluation.
        
        Args:
            decision: The AuditLog decision to analyze
            
        Returns:
            List of improvement suggestions (max 3)
        """
        suggestions = []
        reasoning = decision.reasoning or []
        
        for reason in reasoning:
            reason_lower = reason.lower()
            
            if "experiência" in reason_lower:
                if "insuficiente" in reason_lower or "falta" in reason_lower or "pouca" in reason_lower:
                    suggestions.append(
                        "Busque projetos práticos ou voluntariado para ganhar mais experiência na área"
                    )
            
            if any(word in reason_lower for word in ["skill", "competência", "técnic"]):
                if any(word in reason_lower for word in ["falta", "insuficiente", "desenvolver", "não possui"]):
                    suggestions.append(
                        "Invista em cursos e certificações nas tecnologias exigidas"
                    )
            
            if any(word in reason_lower for word in ["inglês", "idioma", "língua"]):
                suggestions.append(
                    "Pratique o idioma com foco em vocabulário técnico e conversação"
                )
            
            if any(word in reason_lower for word in ["currículo", "cv", "apresentação"]):
                suggestions.append(
                    "Revise seu currículo destacando projetos relevantes e resultados quantificáveis"
                )
            
            if any(word in reason_lower for word in ["wsi", "entrevista", "comunicação"]):
                suggestions.append(
                    "Prepare-se para entrevistas praticando a articulação de suas experiências"
                )
        
        if not suggestions:
            suggestions = [
                "Revise seu currículo destacando projetos relevantes",
                "Prepare-se melhor para entrevistas técnicas",
                "Mantenha-se atualizado nas tecnologias da sua área"
            ]
        
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:3]
    
    async def format_for_candidate_message(
        self,
        company_id: str,
        candidate_id: str,
        job_vacancy_id: str
    ) -> str:
        """
        Format explanation for sending to candidate via email/WhatsApp.
        
        Args:
            company_id: The company/tenant ID
            candidate_id: The candidate ID
            job_vacancy_id: The job vacancy ID
            
        Returns:
            Formatted message string
        """
        explanation = await self.generate_candidate_explanation(
            company_id=company_id,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            include_suggestions=True
        )
        
        if explanation.get("status") == "no_data":
            return explanation["message"]
        
        message = "Sua candidatura foi analisada com base nos seguintes critérios:\n\n"
        
        for i, criterion in enumerate(explanation.get("evaluation_criteria", []), 1):
            message += f"{i}. {criterion['criterion']}\n"
        
        score = explanation.get("overall_score")
        if score is not None:
            message += f"\nNota geral: {score:.1f}/5.0\n"
        else:
            message += "\nNota geral: N/A\n"
        
        message += f"\n{explanation.get('transparency_note', '')}\n"
        
        if explanation.get("suggestions"):
            message += "\nSugestões para futuras oportunidades:\n"
            for suggestion in explanation["suggestions"]:
                message += f"• {suggestion}\n"
        
        message += "\nAgradecemos seu interesse e desejamos sucesso em sua carreira!"
        
        return message
    
    async def generate_recruiter_summary(
        self,
        company_id: str,
        candidate_id: str,
        job_vacancy_id: str
    ) -> dict[str, Any]:
        """
        Generate a summary for recruiters with decision details.
        
        Args:
            company_id: The company/tenant ID
            candidate_id: The candidate ID
            job_vacancy_id: The job vacancy ID
            
        Returns:
            Dictionary with recruiter-focused summary
        """
        explanation = await self.generate_candidate_explanation(
            company_id=company_id,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            include_suggestions=False
        )
        
        if explanation.get("status") == "no_data":
            return explanation
        
        decision_history = explanation.get("decision_history", [])
        
        agents_involved = list(set(d["agent"] for d in decision_history))
        
        has_human_review = False
        human_overrides = []
        
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.company_id == company_id,
                        AuditLog.candidate_id == candidate_id,
                        AuditLog.job_vacancy_id == job_vacancy_id,
                        AuditLog.human_reviewed_at.isnot(None)
                    )
                )
            )
            result = await session.execute(query)
            reviewed_logs = result.scalars().all()
            
            if reviewed_logs:
                has_human_review = True
                for log in reviewed_logs:
                    if log.human_override:
                        human_overrides.append({
                            "original_decision": log.decision,
                            "override": log.human_override,
                            "reviewed_by": log.human_reviewed_by,
                            "reviewed_at": log.human_reviewed_at.isoformat() if log.human_reviewed_at else None
                        })
        
        return {
            "status": explanation["status"],
            "overall_score": explanation.get("overall_score"),
            "confidence": explanation.get("confidence"),
            "criteria_evaluated": explanation.get("criteria_evaluated", []),
            "criteria_ignored": explanation.get("criteria_not_used", []),
            "reasoning": explanation.get("reasoning", []),
            "agents_involved": agents_involved,
            "total_decisions": len(decision_history),
            "decision_timeline": decision_history,
            "has_human_review": has_human_review,
            "human_overrides": human_overrides,
            "transparency_note": explanation.get("transparency_note"),
        }


explainability_service = ExplainabilityService()
