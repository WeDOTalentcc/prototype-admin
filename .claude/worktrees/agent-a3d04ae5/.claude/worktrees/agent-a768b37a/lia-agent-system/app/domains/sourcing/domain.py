from __future__ import annotations

from typing import Dict, Any, List

import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "search": "search_candidates",
    "buscar": "search_candidates",
    "busca": "search_candidates",
    "candidato": "search_candidates",
    "global": "global_search",
    "semantic": "semantic_search",
    "semântic": "semantic_search",
    "boolean": "generate_boolean",
    "booleana": "generate_boolean",
    "cv": "parse_cv",
    "currículo": "parse_cv",
    "curriculo": "parse_cv",
    "analisar cv": "parse_cv",
    "adicionar": "add_candidate",
    "cadastrar": "add_candidate",
    "sugerir": "suggest_candidates",
    "suggest": "suggest_candidates",
    "sugestão": "suggest_candidates",
    "match": "match_candidates",
    "compatibilidade": "match_candidates",
    "enriquecer": "enrich_profile",
    "enrich": "enrich_profile",
    "pipeline": "auto_source",
    "automático": "auto_source",
    "auto_source": "auto_source",
    "volume": "check_volume",
    "proativ": "proactive_suggest",
    "filtrar": "filter_candidates",
    "filtro": "filter_candidates",
    "rankear": "rank_candidates",
    "rank": "rank_candidates",
    "comparar": "compare_candidates",
    "talent pool": "talent_pool_search",
    "pool": "talent_pool_search",
    "pearch": "pearch_search",
    "estratégia": "build_search_strategy",
    "strategy": "build_search_strategy",
    "resultado": "analyze_search_results",
    "feedback": "feedback_search",
    "expandir": "expand_search",
    "ampliar": "expand_search",
    "contatar": "contact_candidates",
    "outreach": "contact_candidates",
    "triagem": "screen_candidates",
    "screening": "screen_candidates",
    "mercado": "assess_market",
    "exportar": "export_candidates",
    "importar": "import_candidates",
    "dedup": "dedup_candidates",
    "duplica": "dedup_candidates",
    "tag": "tag_candidates",
    "taguear": "tag_candidates",
    "engagement": "engagement_pipeline",
    "agendar": "schedule_outreach",
}


@register_domain
class SourcingDomain(DomainPrompt):
    """Domínio de Sourcing & Busca de Talentos da LIA."""

    domain_id = "sourcing"
    domain_name = "Sourcing & Talent Search"
    description = "Busca, identificação e gestão de candidatos em múltiplas fontes"

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.sourcing.actions import SOURCING_ACTIONS
        return SOURCING_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        best_action = "search_candidates"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = 0.85 if len(keyword) > 4 else 0.7
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"sourcing.{best_action}",
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
                error=f"Ação '{action_id}' não encontrada no domínio de sourcing."
            )

        logger.info(f"Routing sourcing action '{action_id}' (tenant={context.tenant_id})")

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de sourcing.",
            data={"action_id": action_id, "params": params},
            domain_id=self.domain_id,
            action_id=action_id,
        )
