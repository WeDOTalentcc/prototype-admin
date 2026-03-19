from __future__ import annotations

from typing import Dict, Any, List

import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "analisar cv": "parse_cv",
    "parse cv": "parse_cv",
    "extrair cv": "parse_cv",
    "currículo": "parse_cv",
    "curriculo": "parse_cv",
    "triagem automática": "auto_screen",
    "triar candidato": "auto_screen",
    "screening": "auto_screen",
    "triagem": "auto_screen",
    "triagem lote": "batch_screen",
    "batch screening": "batch_screen",
    "triagem em massa": "batch_screen",
    "score wsi": "calculate_wsi_score",
    "calcular wsi": "calculate_wsi_score",
    "wsi score": "calculate_wsi_score",
    "pontuação wsi": "calculate_wsi_score",
    "rankear": "rank_candidates",
    "ranking": "rank_candidates",
    "rank candidato": "rank_candidates",
    "ordenar candidatos": "rank_candidates",
    "corte dinâmico": "dynamic_cutoff",
    "top 25": "dynamic_cutoff",
    "dynamic cut": "dynamic_cutoff",
    "red flag": "detect_red_flags",
    "red flags": "detect_red_flags",
    "detectar red flag": "detect_red_flags",
    "risco cv": "detect_red_flags",
    "flag": "detect_red_flags",
    "saturação": "check_saturation",
    "pipeline saturado": "check_saturation",
    "saturation": "check_saturation",
    "bloom": "classify_bloom",
    "taxonomia bloom": "classify_bloom",
    "bloom taxonomy": "classify_bloom",
    "dreyfus": "classify_dreyfus",
    "proficiência": "classify_dreyfus",
    "dreyfus level": "classify_dreyfus",
    "big five": "map_big_five",
    "big5": "map_big_five",
    "personalidade": "map_big_five",
    "comportamental": "map_big_five",
    "cbi": "validate_cbi",
    "competency based": "validate_cbi",
    "competência": "validate_cbi",
    "parecer": "generate_report",
    "relatório candidato": "generate_report",
    "parecer candidato": "generate_report",
    "comparar candidato": "compare_candidates",
    "comparação": "compare_candidates",
    "compare": "compare_candidates",
    "calibrar": "calibrate_model",
    "calibração": "calibrate_model",
    "calibrate": "calibrate_model",
    "feedback modelo": "calibrate_model",
    "explicar score": "explain_score",
    "explainability": "explain_score",
    "como calculou": "explain_score",
    "rubrica": "evaluate_rubric",
    "avaliação rubrica": "evaluate_rubric",
    "rubric evaluation": "evaluate_rubric",
    "pergunta triagem": "generate_questions",
    "screening question": "generate_questions",
    "gerar pergunta": "generate_questions",
    "ajustar pergunta": "adjust_questions",
    "refinar pergunta": "adjust_questions",
    "adjust question": "adjust_questions",
    "voz": "voice_screening",
    "voice screening": "voice_screening",
    "triagem por voz": "voice_screening",
    "normalizar score": "normalize_scores",
    "normalize": "normalize_scores",
    "normalização": "normalize_scores",
    "senioridade": "assess_seniority",
    "seniority": "assess_seniority",
    "nível experiência": "assess_seniority",
    "feedback candidato": "send_feedback",
    "feedback triagem": "send_feedback",
    "enviar feedback": "send_feedback",
    "devolutiva": "send_feedback",
    "feedback ao candidato": "send_feedback",
    "pré-qualificação": "pre_qualify",
    "pre qualify": "pre_qualify",
    "pré-qualificar": "pre_qualify",
}


@register_domain
class CVScreeningDomain(DomainPrompt):
    """Domínio de CV Screening & WSI Assessment da LIA."""

    domain_id = "cv_screening"
    domain_name = "CV Screening & WSI Assessment"
    description = "Triagem curricular, avaliação WSI e scoring de candidatos"

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.cv_screening.actions import CV_SCREENING_ACTIONS
        return CV_SCREENING_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        best_action = "auto_screen"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"cv_screening.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    async def execute_action(
        self, action_id: str, params: Dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de cv screening."
            )

        logger.info(f"Routing cv screening action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.cv_screening.tools import CV_SCREENING_TOOLS, execute_cv_screening_tool

        tool_ids = {t["tool_id"] for t in CV_SCREENING_TOOLS}

        _ACTION_TOOL_MAP: Dict[str, str] = {
            "parse_cv": "parse_cv",
            "auto_screen": "score_cv",
            "calculate_wsi_score": "calculate_wsi",
            "evaluate_rubric": "evaluate_rubric",
            "generate_questions": "generate_wsi_questions",
            "adjust_questions": "adjust_wsi_questions",
            "normalize_scores": "normalize_scores",
            "assess_seniority": "assess_seniority",
            "send_feedback": "send_candidate_feedback",
            "pre_qualify": "pre_qualify_candidate",
            "voice_screening": "run_screening_pipeline",
        }

        mapped_tool = _ACTION_TOOL_MAP.get(action_id)
        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_cv_screening_tool(
                tool_id=mapped_tool,
                params=params,
                tenant_id=context.tenant_id,
            )
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de cv screening.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
