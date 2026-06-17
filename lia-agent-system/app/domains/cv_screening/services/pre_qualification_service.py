"""
Pre-Qualification Service for LIA Platform.

Evaluates candidate adherence to job requirements BEFORE starting the screening process.
Uses humanized messages (no percentages) to inform candidates about their fit.

This service integrates with RubricEvaluationService to calculate adherence scores
and generates appropriate messages based on thresholds.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)
from app.shared.compliance import scoring_safeguards as _ss
from app.shared.compliance.scoring_safeguards import FairnessBlockedError


class PreQualificationResult(StrEnum):
    """Result categories for pre-qualification."""
    ALIGNED = "aligned"
    PARTIAL = "partial"
    DISTANT = "distant"
    VERY_DISTANT = "very_distant"


class PreQualificationDecision(StrEnum):
    """Candidate decision after pre-qualification message."""
    CONTINUE = "continue"
    VIEW_OTHER_JOBS = "view_other_jobs"
    TALENT_POOL = "talent_pool"
    DECLINED = "declined"
    AUTO_ADVANCED = "auto_advanced"


@dataclass
class PreQualificationThresholds:
    """Configurable thresholds for pre-qualification."""
    auto_advance: int = 70
    ask_continue: int = 50
    strong_warning: int = 30
    
    @classmethod
    def from_job_config(cls, job_config: dict[str, Any] | None = None) -> "PreQualificationThresholds":
        """Create thresholds from job screening config."""
        if not job_config:
            return cls()
        
        settings = job_config.get("settings", {})
        return cls(
            auto_advance=settings.get("pre_qual_auto_advance", 70),
            ask_continue=settings.get("pre_qual_ask_threshold", 50),
            strong_warning=settings.get("pre_qual_strong_warning", 30)
        )


@dataclass
class PreQualificationOutput:
    """Output of the pre-qualification evaluation."""
    result: PreQualificationResult
    score: int
    matched_requirements: list[str]
    missing_requirements: list[str]
    message: str
    buttons: list[dict[str, str]]
    should_ask_confirmation: bool


PRE_QUALIFICATION_TEMPLATES = {
    PreQualificationResult.ALIGNED: {
        "opening": "Analisei seu currículo para a vaga de {job_title} na {company_name}.",
        "positive": "Seu perfil está bem alinhado com o que buscamos!",
        "action": "Vamos iniciar algumas perguntas para conhecer melhor sua experiência.",
        "buttons": []
    },
    
    PreQualificationResult.PARTIAL: {
        "opening": "Analisei seu currículo para a vaga de {job_title} na {company_name}.",
        "positive": "Notei que você tem experiência em {matched_skills}, que são importantes para essa posição.",
        "gap": "Porém, a vaga também pede {missing_requirements} — e não encontrei essas informações no seu currículo.",
        "encouragement": "Isso não significa que você não possa participar! A triagem conversacional pode revelar experiências que você não mencionou no documento.",
        "question": "Quer continuar com a triagem?",
        "buttons": [
            {"id": "continue", "title": "Sim, quero continuar"},
            {"id": "decline", "title": "Não, obrigado"}
        ]
    },
    
    PreQualificationResult.DISTANT: {
        "opening": "Analisei seu currículo para a vaga de {job_title} na {company_name}.",
        "transparency": "Quero ser transparente com você: percebi que sua experiência atual não está muito alinhada com o que essa vaga exige.",
        "gap": "A posição pede conhecimento em {key_requirements}, e sua trajetória parece estar mais voltada para outra área.",
        "honesty": "Você pode continuar se quiser, mas prefiro ser honesta: as chances de avançar são menores nesse caso.",
        "alternatives": "O que você prefere fazer?",
        "buttons": [
            {"id": "continue", "title": "Continuar mesmo assim"},
            {"id": "talent_pool", "title": "Banco de talentos"},
            {"id": "decline", "title": "Encerrar"}
        ]
    },
    
    PreQualificationResult.VERY_DISTANT: {
        "opening": "Analisei seu currículo para a vaga de {job_title} na {company_name}.",
        "honesty": "Preciso ser sincera: não encontrei no seu currículo nenhuma das experiências que a vaga exige.",
        "gap": "A posição é para {job_area} com {key_requirements}, e sua experiência parece ser em uma área bem diferente.",
        "care": "Não quero que você perca tempo — processos seletivos podem ser longos e frustrantes quando o perfil não se encaixa.",
        "alternatives": "O que você prefere fazer?",
        "buttons": [
            {"id": "talent_pool", "title": "Banco de talentos"},
            {"id": "continue", "title": "Continuar mesmo assim"},
            {"id": "decline", "title": "Encerrar"}
        ]
    }
}


class PreQualificationService:
    """
    Service to evaluate candidate adherence before screening.
    
    Uses RubricEvaluationService results to determine if candidate should:
    - Auto-advance to screening (aligned profile)
    - Be asked if they want to continue (partial/distant profile)
    - Be offered alternatives (very distant profile)
    
    Messages are humanized and never show percentages to candidates.
    """
    
    def __init__(self):
        self.default_thresholds = PreQualificationThresholds()
    
    def evaluate(
        self,
        adherence_score: float,
        matched_requirements: list[dict[str, Any]],
        missing_requirements: list[dict[str, Any]],
        job_title: str,
        company_name: str,
        job_area: str | None = None,
        thresholds: PreQualificationThresholds | None = None
    ) -> PreQualificationOutput:
        """
        Evaluate candidate pre-qualification based on rubric score.
        
        Args:
            adherence_score: Score from RubricEvaluationService (0-100)
            matched_requirements: Requirements where candidate has MEETS/EXCEEDS
            missing_requirements: Requirements where candidate has MISSING
            job_title: Title of the job vacancy
            company_name: Name of the hiring company
            job_area: General area of the job (e.g., "desenvolvimento de software")
            thresholds: Custom thresholds (optional, uses defaults if not provided)
        
        Returns:
            PreQualificationOutput with result, message, and buttons
        """
        # C3 — Fairness gate (LGPD Art.20 / CLAUDE.md #2/#3).
        _pq_fg, _pq_unavail = _ss.run_fairness_check(job_title or "")
        if _pq_unavail or (_pq_fg and _pq_fg.is_blocked):
            _pq_fg = _pq_fg or type(
                "FR", (), {"is_blocked": True, "category": "unavailable",
                           "educational_message": "fairness guard unavailable"}
            )()
            _ss.schedule_audit_log(_ss.log_scoring_decision(
                company_id=company_name or "unknown",
                agent_name="pre_qualification_service",
                decision_type="fairness_block",
                action="cv_screening.fairness_block",
                decision="blocked",
                reasoning=[f"FairnessGuard blocked job_title: category={_pq_fg.category}",
                            _pq_fg.educational_message or ""],
                criteria_used=["fairness_guard"],
                human_review_required=True,
            ))
            raise FairnessBlockedError(_pq_fg)

        thresholds = thresholds or self.default_thresholds
        
        result = self._determine_result(adherence_score, thresholds)
        
        matched_names = self._extract_requirement_names(matched_requirements)
        missing_names = self._extract_requirement_names(missing_requirements)
        
        message = self._generate_message(
            result=result,
            job_title=job_title,
            company_name=company_name,
            matched_skills=matched_names,
            missing_requirements=missing_names,
            job_area=job_area
        )
        
        template = PRE_QUALIFICATION_TEMPLATES[result]
        buttons = template.get("buttons", [])
        
        should_ask = result != PreQualificationResult.ALIGNED
        
        logger.info(
            f"Pre-qualification result: {result.value} (score: {adherence_score:.1f}%) "
            f"for job '{job_title}' - ask_confirmation: {should_ask}"
        )
        
        return PreQualificationOutput(
            result=result,
            score=int(adherence_score),
            matched_requirements=matched_names,
            missing_requirements=missing_names,
            message=message,
            buttons=buttons,
            should_ask_confirmation=should_ask
        )
    
    def _determine_result(
        self, 
        score: float, 
        thresholds: PreQualificationThresholds
    ) -> PreQualificationResult:
        """Determine the pre-qualification result based on score and thresholds."""
        if score >= thresholds.auto_advance:
            return PreQualificationResult.ALIGNED
        elif score >= thresholds.ask_continue:
            return PreQualificationResult.PARTIAL
        elif score >= thresholds.strong_warning:
            return PreQualificationResult.DISTANT
        else:
            return PreQualificationResult.VERY_DISTANT
    
    def _extract_requirement_names(
        self, 
        requirements: list[dict[str, Any]]
    ) -> list[str]:
        """Extract requirement names from evaluation results."""
        names = []
        for req in requirements:
            name = req.get("requirement") or req.get("name") or req.get("description")
            if name:
                names.append(name)
        return names[:5]
    
    def _generate_message(
        self,
        result: PreQualificationResult,
        job_title: str,
        company_name: str,
        matched_skills: list[str],
        missing_requirements: list[str],
        job_area: str | None = None
    ) -> str:
        """Generate humanized message for the candidate."""
        template = PRE_QUALIFICATION_TEMPLATES[result]
        
        matched_str = self._format_skills_list(matched_skills) if matched_skills else "algumas competências relevantes"
        missing_str = self._format_skills_list(missing_requirements) if missing_requirements else "alguns requisitos específicos"
        key_requirements = self._format_skills_list(missing_requirements[:3]) if missing_requirements else "algumas tecnologias específicas"
        job_area_str = job_area or "a área especificada"
        
        parts = []
        
        for key in ["opening", "positive", "transparency", "honesty", "gap", "encouragement", "care", "alternatives", "question", "action"]:
            if key in template:
                text = template[key]
                text = text.format(
                    job_title=job_title,
                    company_name=company_name,
                    matched_skills=matched_str,
                    missing_requirements=missing_str,
                    key_requirements=key_requirements,
                    job_area=job_area_str
                )
                parts.append(text)
        
        return "\n\n".join(parts)
    
    def _format_skills_list(self, skills: list[str]) -> str:
        """Format a list of skills into readable text."""
        if not skills:
            return ""
        if len(skills) == 1:
            return skills[0]
        if len(skills) == 2:
            return f"{skills[0]} e {skills[1]}"
        return ", ".join(skills[:-1]) + f" e {skills[-1]}"
    
    def generate_existing_candidate_message(
        self,
        candidate_name: str,
        registered_since: datetime,
        job_title: str
    ) -> str:
        """
        Generate message for candidates who already exist in the database.
        
        Args:
            candidate_name: Name of the existing candidate
            registered_since: When the candidate was first registered
            job_title: Title of the job they're applying to
        
        Returns:
            Humanized message acknowledging their existing profile
        """
        since_str = registered_since.strftime("%d/%m/%Y")
        
        return (
            f"Olá {candidate_name}! Vi que você já está cadastrado na nossa "
            f"base desde {since_str}.\n\n"
            f"Vou atualizar seu perfil com as informações do novo currículo "
            f"e seguir com sua candidatura para a vaga de {job_title}.\n\n"
            f"Confere os dados atualizados?"
        )
    
    def generate_confirmation_message(
        self,
        parsed_cv: dict[str, Any],
        is_update: bool = False
    ) -> str:
        """
        Generate message to confirm all extracted CV data with the candidate.
        
        Args:
            parsed_cv: Parsed CV data from CVParserService
            is_update: Whether this is an update to existing profile
        
        Returns:
            Formatted message with all extracted data
        """
        action_word = "atualizados" if is_update else "extraídos"
        
        parts = [f"Dados {action_word} do seu currículo:"]
        parts.append("")
        
        if parsed_cv.get("full_name"):
            parts.append(f"Nome: {parsed_cv['full_name']}")
        if parsed_cv.get("email"):
            parts.append(f"Email: {parsed_cv['email']}")
        if parsed_cv.get("phone"):
            parts.append(f"Telefone: {parsed_cv['phone']}")
        if parsed_cv.get("location"):
            parts.append(f"Localização: {parsed_cv['location']}")
        if parsed_cv.get("current_title"):
            parts.append(f"Cargo atual: {parsed_cv['current_title']}")
        if parsed_cv.get("current_company"):
            parts.append(f"Empresa atual: {parsed_cv['current_company']}")
        if parsed_cv.get("years_of_experience"):
            parts.append(f"Experiência: {parsed_cv['years_of_experience']} anos")
        
        skills = parsed_cv.get("skills") or parsed_cv.get("technical_skills") or []
        if skills:
            parts.append("")
            parts.append(f"Habilidades técnicas: {', '.join(skills[:10])}")
        
        education = parsed_cv.get("education") or []
        if education:
            parts.append("")
            if isinstance(education, list) and len(education) > 0:
                edu = education[0]
                if isinstance(edu, dict):
                    edu_str = f"{edu.get('degree', '')} - {edu.get('institution', '')}".strip(" -")
                    if edu_str:
                        parts.append(f"Formação: {edu_str}")
                elif isinstance(edu, str):
                    parts.append(f"Formação: {edu}")
        
        linkedin = parsed_cv.get("linkedin")
        if linkedin:
            parts.append("")
            parts.append(f"LinkedIn: {linkedin}")
        
        parts.append("")
        parts.append("Os dados estão corretos?")
        
        return "\n".join(parts)


pre_qualification_service = PreQualificationService()
