from app.shared.compliance import scoring_safeguards as _ss
from app.shared.compliance.scoring_safeguards import FairnessBlockedError
"""
Eligibility Verification Service

Handles eliminatory questions with humanized reconsideration flow.
Instead of auto-rejecting, gives candidates a chance to reconsider their answers.

Flow:
1. Candidate answers an eliminatory question
2. If answer doesn't match expected → trigger reconsideration
3. Candidate can: keep answer (→ talent pool) or reconsider (→ continue)
4. Max 2 reconsiderations per conversation to avoid loops
"""

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any


class ReconsiderationResult(StrEnum):
    PASSED = "passed"
    NEEDS_RECONSIDERATION = "needs_reconsideration"
    KEPT_INCOMPATIBLE = "kept_incompatible"
    RECONSIDERED_PASSED = "reconsidered_passed"
    MAX_RECONSIDERATIONS_REACHED = "max_reconsiderations_reached"


@dataclass
class EligibilityQuestion:
    id: str
    question_text: str
    question_type: str
    options: list[str] | None
    is_eliminatory: bool
    expected_answer: str | None
    category: str


@dataclass
class ReconsiderationContext:
    question_id: str
    original_answer: str
    expected_answer: str
    question_text: str
    attempt_count: int


RECONSIDERATION_TEMPLATES = {
    "work_model": {
        "warning": (
            "Entendi! 😊 Preciso te avisar que para essa vaga específica, "
            "o modelo de trabalho {expected} é um requisito obrigatório da empresa.\n\n"
            "Você gostaria de:\n"
            "1️⃣ Manter sua resposta ({original}) - vou te adicionar ao nosso banco de talentos "
            "para futuras oportunidades compatíveis\n"
            "2️⃣ Reconsiderar - tenho interesse nessa vaga e posso avaliar o modelo {expected}"
        ),
        "confirmation": (
            "Ótimo! Confirmando então: você tem disponibilidade para trabalho {expected}?"
        ),
        "talent_pool": (
            "Sem problemas! 👍 Vou adicionar seu perfil ao nosso banco de talentos. "
            "Assim que surgir uma oportunidade com modelo {original}, entraremos em contato!\n\n"
            "Obrigada pelo interesse e até breve! 🙂"
        )
    },
    "location": {
        "warning": (
            "Entendi! 😊 Essa vaga é para atuação em {expected}, que é um requisito "
            "obrigatório da empresa.\n\n"
            "Você gostaria de:\n"
            "1️⃣ Manter sua resposta - vou te adicionar ao nosso banco de talentos "
            "para futuras oportunidades na sua região\n"
            "2️⃣ Reconsiderar - tenho interesse nessa vaga e posso avaliar a mudança/deslocamento"
        ),
        "confirmation": (
            "Ótimo! Confirmando: você tem disponibilidade para atuar em {expected}?"
        ),
        "talent_pool": (
            "Sem problemas! 👍 Vou adicionar seu perfil ao nosso banco de talentos. "
            "Assim que surgir uma oportunidade na sua região, entraremos em contato!\n\n"
            "Obrigada pelo interesse e até breve! 🙂"
        )
    },
    "availability": {
        "warning": (
            "Entendi! 😊 Essa vaga precisa de início {expected}, que é um requisito "
            "da empresa para esse momento.\n\n"
            "Você gostaria de:\n"
            "1️⃣ Manter sua disponibilidade - vou te adicionar ao nosso banco de talentos "
            "para oportunidades futuras\n"
            "2️⃣ Reconsiderar - tenho interesse nessa vaga e posso avaliar antecipar"
        ),
        "confirmation": (
            "Ótimo! Confirmando: você tem disponibilidade para início {expected}?"
        ),
        "talent_pool": (
            "Sem problemas! 👍 Vou guardar seu perfil e quando surgir uma oportunidade "
            "alinhada com sua disponibilidade, entro em contato!\n\n"
            "Obrigada pelo interesse e até breve! 🙂"
        )
    },
    "legal": {
        "warning": (
            "Entendi! 😊 Para essa vaga, {expected} é um requisito obrigatório "
            "para a função.\n\n"
            "Você gostaria de:\n"
            "1️⃣ Manter sua resposta - vou te adicionar ao nosso banco de talentos "
            "para vagas que não exijam esse requisito\n"
            "2️⃣ Reconsiderar - posso providenciar/já possuo esse requisito"
        ),
        "confirmation": (
            "Ótimo! Confirmando: você possui/pode providenciar {expected}?"
        ),
        "talent_pool": (
            "Sem problemas! 👍 Vou adicionar seu perfil ao nosso banco de talentos "
            "para oportunidades que não exijam esse requisito.\n\n"
            "Obrigada pelo interesse e até breve! 🙂"
        )
    },
    "default": {
        "warning": (
            "Entendi! 😊 Preciso te avisar que \"{expected}\" é um requisito "
            "obrigatório para essa vaga.\n\n"
            "Você gostaria de:\n"
            "1️⃣ Manter sua resposta - vou te adicionar ao nosso banco de talentos "
            "para futuras oportunidades compatíveis\n"
            "2️⃣ Reconsiderar - tenho interesse nessa vaga e posso me adequar"
        ),
        "confirmation": (
            "Ótimo! Confirmando então: {question_text}"
        ),
        "talent_pool": (
            "Sem problemas! 👍 Vou adicionar seu perfil ao nosso banco de talentos. "
            "Assim que surgir uma oportunidade compatível, entraremos em contato!\n\n"
            "Obrigada pelo interesse e até breve! 🙂"
        )
    }
}

MAX_RECONSIDERATIONS = 2


class EligibilityVerificationService:
    """
    Service to verify eligibility questions with humanized reconsideration flow.
    """
    
    def __init__(self):
        self.templates = RECONSIDERATION_TEMPLATES
    
    def check_answer(
        self,
        question: EligibilityQuestion,
        answer: str,
        reconsideration_count: int = 0
    ) -> tuple[ReconsiderationResult, str | None]:
        """
        Check if the answer matches the expected answer for eliminatory questions.
        
        Returns:
            Tuple of (result, message)
        """
        # C4 — Fairness gate (LGPD Art.20 / CLAUDE.md #2/#3).
        _ev_fg, _ev_unavail = _ss.run_fairness_check(question.question_text or "")
        if _ev_unavail or (_ev_fg and _ev_fg.is_blocked):
            _ev_fg = _ev_fg or type(
                "FR", (), {"is_blocked": True, "category": "unavailable",
                           "educational_message": "fairness guard unavailable"}
            )()
            _ss.schedule_audit_log(_ss.log_scoring_decision(
                company_id="unknown",
                agent_name="eligibility_verification_service",
                decision_type="fairness_block",
                action="cv_screening.fairness_block",
                decision="blocked",
                reasoning=[f"FairnessGuard blocked question: category={_ev_fg.category}",
                            _ev_fg.educational_message or ""],
                criteria_used=["fairness_guard"],
                human_review_required=True,
            ))
            raise FairnessBlockedError(_ev_fg)

        if not question.is_eliminatory:
            return ReconsiderationResult.PASSED, None
        
        if not question.expected_answer:
            return ReconsiderationResult.PASSED, None
        
        if self._answers_match(answer, question.expected_answer, question.question_type):
            return ReconsiderationResult.PASSED, None
        
        if reconsideration_count >= MAX_RECONSIDERATIONS:
            message = self._get_talent_pool_message(question.category, answer, question.expected_answer)
            return ReconsiderationResult.MAX_RECONSIDERATIONS_REACHED, message
        
        message = self._get_warning_message(
            question.category,
            answer,
            question.expected_answer,
            question.question_text
        )
        return ReconsiderationResult.NEEDS_RECONSIDERATION, message
    
    def _answers_match(
        self,
        given_answer: str,
        expected_answer: str,
        question_type: str
    ) -> bool:
        """Check if the given answer matches the expected answer."""
        given_normalized = given_answer.strip().lower()
        expected_normalized = expected_answer.strip().lower()
        
        if question_type == "yes_no":
            yes_variants = {"sim", "yes", "s", "y", "1", "true", "positivo"}
            no_variants = {"não", "nao", "no", "n", "0", "false", "negativo"}
            
            given_is_yes = given_normalized in yes_variants
            given_is_no = given_normalized in no_variants
            expected_is_yes = expected_normalized in yes_variants
            expected_is_no = expected_normalized in no_variants
            
            if expected_is_yes:
                return given_is_yes
            if expected_is_no:
                return given_is_no
        
        if question_type == "single_choice":
            return given_normalized == expected_normalized or given_normalized in expected_normalized
        
        return given_normalized == expected_normalized
    
    def process_reconsideration_response(
        self,
        response: str,
        context: ReconsiderationContext
    ) -> tuple[ReconsiderationResult, str | None]:
        """
        Process the candidate's response to a reconsideration prompt.
        
        Args:
            response: "1" to keep answer, "2" to reconsider
            context: The reconsideration context
        
        Returns:
            Tuple of (result, message)
        """
        response_normalized = response.strip().lower()
        
        keep_variants = {"1", "1️⃣", "manter", "keep", "primeira", "primeiro"}
        reconsider_variants = {"2", "2️⃣", "reconsiderar", "segunda", "segundo", "interesse"}
        
        if any(variant in response_normalized for variant in keep_variants):
            message = self._get_talent_pool_message(
                self._infer_category_from_question(context.question_text),
                context.original_answer,
                context.expected_answer
            )
            return ReconsiderationResult.KEPT_INCOMPATIBLE, message
        
        if any(variant in response_normalized for variant in reconsider_variants):
            category = self._infer_category_from_question(context.question_text)
            message = self._get_confirmation_message(
                category,
                context.expected_answer,
                context.question_text
            )
            return ReconsiderationResult.RECONSIDERED_PASSED, message
        
        return ReconsiderationResult.NEEDS_RECONSIDERATION, (
            "Desculpe, não entendi sua resposta. Por favor, responda:\n"
            "1️⃣ para manter sua resposta original\n"
            "2️⃣ para reconsiderar"
        )
    
    def process_confirmation_response(
        self,
        response: str,
        expected_answer: str,
        question_type: str
    ) -> tuple[bool, str | None]:
        """
        Process the candidate's response to a confirmation question.
        
        Returns:
            Tuple of (passed, talent_pool_message_if_failed)
        """
        if self._answers_match(response, expected_answer, question_type):
            return True, None
        
        return False, self._get_talent_pool_message("default", response, expected_answer)
    
    def _get_warning_message(
        self,
        category: str,
        original_answer: str,
        expected_answer: str,
        question_text: str
    ) -> str:
        """Get the warning message for a mismatched eliminatory answer."""
        template_set = self.templates.get(category, self.templates["default"])
        template = template_set["warning"]
        
        return template.format(
            original=original_answer,
            expected=expected_answer,
            question_text=question_text
        )
    
    def _get_confirmation_message(
        self,
        category: str,
        expected_answer: str,
        question_text: str
    ) -> str:
        """Get the confirmation message after reconsideration."""
        template_set = self.templates.get(category, self.templates["default"])
        template = template_set["confirmation"]
        
        return template.format(
            expected=expected_answer,
            question_text=question_text
        )
    
    def _get_talent_pool_message(
        self,
        category: str,
        original_answer: str,
        expected_answer: str
    ) -> str:
        """Get the talent pool message for candidates who keep incompatible answers."""
        template_set = self.templates.get(category, self.templates["default"])
        template = template_set["talent_pool"]
        
        return template.format(
            original=original_answer,
            expected=expected_answer
        )
    
    def _infer_category_from_question(self, question_text: str) -> str:
        """Infer the category from question text for template selection."""
        question_lower = question_text.lower()
        
        if any(word in question_lower for word in ["presencial", "remoto", "híbrido", "modelo"]):
            return "work_model"
        if any(word in question_lower for word in ["cidade", "estado", "localização", "região", "mudança"]):
            return "location"
        if any(word in question_lower for word in ["início", "disponibilidade", "quando", "imediato"]):
            return "availability"
        if any(word in question_lower for word in ["cnh", "habilitação", "certificação", "inglês", "idioma"]):
            return "legal"
        
        return "default"
    
    def create_reconsideration_context(
        self,
        question: EligibilityQuestion,
        original_answer: str,
        attempt_count: int = 0
    ) -> ReconsiderationContext:
        """Create a context object for tracking reconsideration state."""
        return ReconsiderationContext(
            question_id=question.id,
            original_answer=original_answer,
            expected_answer=question.expected_answer or "",
            question_text=question.question_text,
            attempt_count=attempt_count + 1
        )
    
    def get_eligibility_questions_from_job(
        self,
        job_data: dict[str, Any]
    ) -> list[EligibilityQuestion]:
        """Extract eligibility questions from job vacancy data."""
        questions: list[EligibilityQuestion] = []

        # canonical-fix (Epico Elegibilidade 2026-06-03): parse UNICO via
        # EligibilityQuestionItem, que normaliza os 4 shapes historicos
        # (wizard required_answer / job-edit disqualify_on_fail /
        # catalogo eliminatory|eliminatoryAnswer / legado question_text).
        from app.schemas.eligibility_question_item import EligibilityQuestionItem

        eligibility_data = job_data.get("eligibility_questions", []) or []

        for q in eligibility_data:
            if not isinstance(q, dict):
                continue
            item = EligibilityQuestionItem(**q)
            if not item.question:
                continue
            questions.append(EligibilityQuestion(
                id=item.id,
                question_text=item.question,
                question_type=item.question_type,
                options=item.options,
                is_eliminatory=item.is_eliminatory,
                expected_answer=item.expected_answer,
                category=item.category,
            ))

        return questions


eligibility_service = EligibilityVerificationService()
