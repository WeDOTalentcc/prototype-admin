"""
PipelineTransitionDomain - Exposes pipeline transitions as agent-callable tools.
Part of the domain-driven architecture for agent orchestration.
"""
import logging
from pathlib import Path
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

DOMAIN_NAME = "pipeline_transition"
DOMAIN_DESCRIPTION = "Gerencia movimentação de candidatos no pipeline de recrutamento"

DOMAIN_TOOLS = [
    {
        "name": "move_candidate",
        "description": "Move um candidato para uma nova etapa do pipeline de recrutamento",
        "parameters": {
            "vacancy_candidate_id": {"type": "string", "required": True, "description": "ID do candidato na vaga"},
            "to_stage": {"type": "string", "required": True, "description": "Etapa destino"},
            "from_stage": {"type": "string", "required": False, "description": "Etapa origem"},
            "sub_status": {"type": "string", "required": False, "description": "Sub-status na etapa destino"},
            "prompt": {"type": "string", "required": False, "description": "Instrução em linguagem natural"},
            "channel": {"type": "string", "required": False, "description": "Canal de comunicação (email/whatsapp)"},
        },
    },
    {
        "name": "interpret_context",
        "description": "Interpreta o contexto de uma transição usando IA para extrair preferências e sugerir ações",
        "parameters": {
            "candidate_id": {"type": "string", "required": True},
            "candidate_name": {"type": "string", "required": False},
            "job_title": {"type": "string", "required": False},
            "from_stage": {"type": "string", "required": True},
            "to_stage": {"type": "string", "required": True},
            "action_behavior": {"type": "string", "required": True},
            "prompt": {"type": "string", "required": False},
        },
    },
    {
        "name": "predict_sub_status",
        "description": "Prediz o sub-status mais adequado para um candidato em uma etapa",
        "parameters": {
            "vacancy_candidate_id": {"type": "string", "required": True},
            "from_stage": {"type": "string", "required": True},
            "to_stage": {"type": "string", "required": True},
        },
    },
    {
        "name": "suggest_next_action",
        "description": "Sugere a próxima ação para um candidato baseado no contexto do pipeline",
        "parameters": {
            "vacancy_candidate_id": {"type": "string", "required": True},
            "current_stage": {"type": "string", "required": True},
        },
    },
    {
        "name": "list_pipeline_stages",
        "description": "Lista todas as etapas do pipeline de recrutamento de uma empresa",
        "parameters": {
            "company_id": {"type": "string", "required": True},
        },
    },
]

DOMAIN_INTENTS = [
    "mover_candidato",
    "agendar_entrevista",
    "enviar_teste",
    "rejeitar_candidato",
    "contratar_candidato",
    "verificar_pipeline",
    "sugerir_acao",
]

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="pipeline_transition")



@register_domain
class PipelineTransitionDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'rejection'}
    domain_id = "pipeline_transition"
    domain_name = "Pipeline Transition"
    description = DOMAIN_DESCRIPTION
    version = "1.0.0"

    def get_allowed_actions(self) -> list[DomainAction]:
        return [
            DomainAction(
                action_id="move_candidate",
                name="Mover Candidato",
                description="Move um candidato para uma nova etapa do pipeline",
                required_params=["vacancy_candidate_id", "to_stage"],
                optional_params=["from_stage", "sub_status", "prompt", "channel"],
                requires_confirmation=True,
                tags=["pipeline", "transition"],
                is_async=True,
            ),
            DomainAction(
                action_id="interpret_context",
                name="Interpretar Contexto",
                description="Interpreta o contexto de uma transição usando IA",
                required_params=["candidate_id", "from_stage", "to_stage", "action_behavior"],
                optional_params=["candidate_name", "job_title", "prompt"],
                tags=["pipeline", "ai", "context"],
                is_async=True,
            ),
            DomainAction(
                action_id="predict_sub_status",
                name="Predizer Sub-Status",
                description="Prediz o sub-status mais adequado para um candidato",
                required_params=["vacancy_candidate_id", "from_stage", "to_stage"],
                tags=["pipeline", "prediction"],
                is_async=True,
            ),
            DomainAction(
                action_id="suggest_next_action",
                name="Sugerir Próxima Ação",
                description="Sugere a próxima ação para um candidato no pipeline",
                required_params=["vacancy_candidate_id", "current_stage"],
                tags=["pipeline", "suggestion"],
                is_async=True,
            ),
            DomainAction(
                action_id="list_pipeline_stages",
                name="Listar Etapas",
                description="Lista todas as etapas do pipeline de recrutamento",
                required_params=["company_id"],
                tags=["pipeline", "stages"],
                is_async=True,
            ),
        ]

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="suggest_next_action")
                return IntentResult(
                    intent_id=f"pipeline.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to regex loop on error)
        try:
            match = _matcher.match(query, default_action="suggest_next_action")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for pipeline_transition: %s", query[:60])
            return IntentResult(
                intent_id=f"pipeline_transition_{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            import re
            query_lower = query.lower().strip()
            best_action = None
            best_confidence = 0.0
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query_lower, re.UNICODE):
                    confidence = 0.85
                    if best_confidence < confidence:
                        best_action = action_id
                        best_confidence = confidence
            if not best_action:
                best_action = "suggest_next_action"
                best_confidence = 0.4
            return IntentResult(
                intent_id=f"pipeline_transition_{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={},
                reasoning=f"Matched pipeline action: {best_action}",
            )

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        tool_context = {
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
            "auth_token": context.metadata.get("auth_token"),
        }
        result = await handle_tool_call(action_id, params, tool_context)

        if result.get("success"):
            return DomainResponse.success_response(
                message=result.get("message", "Ação executada com sucesso"),
                data=result,
                domain_id=self.domain_id,
                action_id=action_id,
            )
        return DomainResponse.error_response(
            error=result.get("error", "Erro desconhecido"),
            domain_id=self.domain_id,
            action_id=action_id,
        )

    def get_suggestions(self, context: DomainContext) -> list[str]:
        return [
            "Mover candidato para próxima etapa",
            "Ver etapas do pipeline",
            "Sugerir próxima ação para candidato",
        ]


async def handle_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        if tool_name == "move_candidate":
            return await _handle_move_candidate(parameters, context)
        elif tool_name == "interpret_context":
            return await _handle_interpret_context(parameters, context)
        elif tool_name == "predict_sub_status":
            return await _handle_predict_sub_status(parameters, context)
        elif tool_name == "suggest_next_action":
            return await _handle_suggest_next_action(parameters, context)
        elif tool_name == "list_pipeline_stages":
            return await _handle_list_stages(parameters, context)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[PIPELINE-DOMAIN] Tool {tool_name} failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def _handle_move_candidate(params: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    try:
        import httpx

        payload = {
            "vacancy_candidate_id": params["vacancy_candidate_id"],
            "to_stage": params["to_stage"],
            "from_stage": params.get("from_stage"),
            "sub_status": params.get("sub_status"),
            "prompt": params.get("prompt"),
            "channel": params.get("channel", "email"),
            "action_behavior": params.get("action_behavior"),
        }

        import os
        # P2-W1-10: porta canonica FastAPI = 8001 no Replit. Configurar LIA_BACKEND_URL=http://localhost:8001
        base_url = os.environ.get("LIA_BACKEND_URL", "http://localhost:8001")
        async with httpx.AsyncClient(base_url=base_url) as client:
            headers = {}
            if context and context.get("auth_token"):
                headers["Authorization"] = f"Bearer {context['auth_token']}"

            response = await client.post("/api/v1/pipeline/transition/execute", json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": result.get("message", "Candidato movido com sucesso"),
                    "new_stage": result.get("new_stage"),
                    "new_sub_status": result.get("new_sub_status"),
                    "ai_personalized": any(
                        d.get("ai_personalized") for d in (result.get("dispatch_results") or [])
                    ),
                }
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"[PIPELINE-DOMAIN] move_candidate failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def _handle_interpret_context(params: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    try:
        from app.domains.communication.services.interpret_context_llm_service import interpret_with_llm

        result = await interpret_with_llm(
            prompt=params.get("prompt", ""),
            candidate_name=params.get("candidate_name"),
            job_title=params.get("job_title"),
            from_stage=params.get("from_stage", ""),
            to_stage=params.get("to_stage", ""),
            action_behavior=params.get("action_behavior", ""),
        )

        if result:
            return {"success": True, **result}
        return {"success": False, "error": "LLM interpretation unavailable"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _handle_predict_sub_status(params: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    try:
        import os

        import httpx

        payload = {
            "vacancy_candidate_id": params["vacancy_candidate_id"],
            "from_stage": params["from_stage"],
            "to_stage": params["to_stage"],
        }

        # P2-W1-10: porta canonica FastAPI = 8001 no Replit. Configurar LIA_BACKEND_URL=http://localhost:8001
        base_url = os.environ.get("LIA_BACKEND_URL", "http://localhost:8001")
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            headers = {}
            if context and context.get("auth_token"):
                headers["Authorization"] = f"Bearer {context['auth_token']}"

            response = await client.post(
                "/api/v1/pipeline/transition/bulk-predict-substatus",
                json={"candidates": [payload]},
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()
                predictions = result.get("predictions", [])
                if predictions:
                    pred = predictions[0]
                    return {
                        "success": True,
                        "predicted_sub_status": pred.get("predicted_sub_status"),
                        "confidence": pred.get("confidence", 0.0),
                        "reasoning": pred.get("reasoning", ""),
                    }
                return {"success": True, "message": "No prediction available for this candidate"}
            else:
                logger.warning(f"Sub-status prediction API returned {response.status_code}")
                return {
                    "success": False,
                    "error": f"Prediction API returned status {response.status_code}",
                    "hint": "Use /transition/execute endpoint for full pipeline context.",
                }
    except Exception as e:
        logger.error(f"[PIPELINE-DOMAIN] predict_sub_status bridge failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "hint": "SubStatus prediction requires API access. Use /transition/execute endpoint.",
        }


async def _handle_suggest_next_action(params: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    try:
        from app.domains.communication.services.infer_behavior_service import infer_behavior_auto

        current_stage = params.get("current_stage", "")
        result = await infer_behavior_auto(current_stage)

        suggestions = {
            "screening": "Iniciar triagem WSI com o candidato",
            "scheduling": "Agendar entrevista com o candidato",
            "evaluation": "Enviar teste técnico ou avaliação",
            "verification": "Solicitar documentos ou referências",
            "offer": "Preparar e enviar proposta salarial",
            "conclusion_hired": "Finalizar contratação",
            "conclusion_rejected": "Enviar feedback construtivo",
            "passive": "Nenhuma ação automática necessária",
        }

        behavior = result.get("suggested_behavior", "passive")

        return {
            "success": True,
            "current_stage": current_stage,
            "suggested_behavior": behavior,
            "suggested_action": suggestions.get(behavior, "Avaliar manualmente"),
            "confidence": result.get("confidence", 0.5),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _handle_list_stages(params: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    from app.models.recruitment_stages import STANDARD_STAGE_CATALOG

    stages = []
    for stage in STANDARD_STAGE_CATALOG:
        stages.append({
            "id": stage.get("id", ""),
            "name": stage.get("name", ""),
            "action_behavior": stage.get("action_behavior", "passive"),
        })

    return {"success": True, "stages": stages}


def get_domain_config() -> dict[str, Any]:
    return {
        "name": DOMAIN_NAME,
        "description": DOMAIN_DESCRIPTION,
        "tools": DOMAIN_TOOLS,
        "intents": DOMAIN_INTENTS,
        "handler": handle_tool_call,
    }
