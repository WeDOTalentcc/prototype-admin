"""
Intent Router - Classifies user intent and delegates to specialized agents

Uses Claude Sonnet 4.5 for intent classification with confidence scoring.
Routes requests to one of 9 specialized agents based on user intent.

Architecture v2.2: 9 agents (1 orchestrator + 8 specialized)
"""

import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.agents.base_agent import AgentType

logger = logging.getLogger(__name__)


class IntentRouter:
    """Routes user requests to appropriate specialized agents based on intent classification."""
    
    INTENT_TO_AGENT_TYPE = {
        "job_planner": AgentType.JOB_PLANNER,
        "create_job": AgentType.JOB_PLANNER,
        "update_job": AgentType.JOB_PLANNER,
        "create_job_vacancy": AgentType.JOB_PLANNER,
        "extract_jd": AgentType.JOB_PLANNER,
        
        "sourcing": AgentType.SOURCING,
        "search_candidates": AgentType.SOURCING,
        "buscar_candidatos": AgentType.SOURCING,
        "find_candidates": AgentType.SOURCING,
        "boolean_search": AgentType.SOURCING,
        
        "cv_screening": AgentType.CV_SCREENING,
        "triagem_curricular": AgentType.CV_SCREENING,
        "analisar_cv": AgentType.CV_SCREENING,
        "parse_cv": AgentType.CV_SCREENING,
        "screen_candidate": AgentType.CV_SCREENING,
        "rank_candidates": AgentType.CV_SCREENING,
        "detect_red_flags": AgentType.CV_SCREENING,
        "calculate_score": AgentType.CV_SCREENING,
        
        "interviewer": AgentType.INTERVIEWER,
        "entrevista": AgentType.INTERVIEWER,
        "conduct_interview": AgentType.INTERVIEWER,
        "transcribe_interview": AgentType.INTERVIEWER,
        
        "wsi_evaluator": AgentType.WSI_EVALUATOR,
        "avaliador_wsi": AgentType.WSI_EVALUATOR,
        "evaluate_candidate": AgentType.WSI_EVALUATOR,
        "compare_candidates": AgentType.WSI_EVALUATOR,
        
        "scheduling": AgentType.SCHEDULING,
        "agendar_entrevista": AgentType.SCHEDULING,
        "schedule_interview": AgentType.SCHEDULING,
        
        "analyst_feedback": AgentType.ANALYST_FEEDBACK,
        "analytics": AgentType.ANALYST_FEEDBACK,
        "kpis": AgentType.ANALYST_FEEDBACK,
        "reports": AgentType.ANALYST_FEEDBACK,
        "feedback": AgentType.ANALYST_FEEDBACK,
        
        # Job Analytics intents
        "funnel_analysis": AgentType.ANALYST_FEEDBACK,
        "analise_funil": AgentType.ANALYST_FEEDBACK,
        "analisar_funil": AgentType.ANALYST_FEEDBACK,
        "comparative_analysis": AgentType.ANALYST_FEEDBACK,
        "bottleneck_detection": AgentType.ANALYST_FEEDBACK,
        "detectar_gargalos": AgentType.ANALYST_FEEDBACK,
        "gargalos": AgentType.ANALYST_FEEDBACK,
        "time_to_fill_prediction": AgentType.ANALYST_FEEDBACK,
        "previsao_fechamento": AgentType.ANALYST_FEEDBACK,
        "prever_fechamento": AgentType.ANALYST_FEEDBACK,
        "weekly_summary": AgentType.ANALYST_FEEDBACK,
        "resumo_semanal": AgentType.ANALYST_FEEDBACK,
        
        "ats_integrator": AgentType.ATS_INTEGRATOR,
        "sync_ats": AgentType.ATS_INTEGRATOR,
        "gupy": AgentType.ATS_INTEGRATOR,
        "pandape": AgentType.ATS_INTEGRATOR,
        
        "recruiter_assistant": AgentType.RECRUITER_ASSISTANT,
        "assistant": AgentType.RECRUITER_ASSISTANT,
        "help": AgentType.RECRUITER_ASSISTANT,
        "daily_briefing": AgentType.RECRUITER_ASSISTANT,
        
        # New conversational intents for RecruiterAssistant
        "consultar_candidato": AgentType.RECRUITER_ASSISTANT,
        "query_candidate": AgentType.RECRUITER_ASSISTANT,
        "fale_sobre_candidato": AgentType.RECRUITER_ASSISTANT,
        "informacoes_candidato": AgentType.RECRUITER_ASSISTANT,
        
        "atualizar_status_candidato": AgentType.RECRUITER_ASSISTANT,
        "update_candidate_status": AgentType.RECRUITER_ASSISTANT,
        "mover_candidato": AgentType.RECRUITER_ASSISTANT,
        "reprovar_candidato": AgentType.RECRUITER_ASSISTANT,
        "aprovar_candidato": AgentType.RECRUITER_ASSISTANT,
        
        "solicitar_aprovacao_vaga": AgentType.RECRUITER_ASSISTANT,
        "request_job_approval": AgentType.RECRUITER_ASSISTANT,
        "enviar_aprovacao": AgentType.RECRUITER_ASSISTANT,
        
        "compartilhar_candidatos": AgentType.RECRUITER_ASSISTANT,
        "share_candidates": AgentType.RECRUITER_ASSISTANT,
        "enviar_candidatos_gestor": AgentType.RECRUITER_ASSISTANT,
        
        "adicionar_candidato": AgentType.RECRUITER_ASSISTANT,
        "add_candidate": AgentType.RECRUITER_ASSISTANT,
        "cadastrar_candidato": AgentType.RECRUITER_ASSISTANT,
        
        "reagendar_entrevista": AgentType.RECRUITER_ASSISTANT,
        "reschedule_interview": AgentType.RECRUITER_ASSISTANT,
        
        "enviar_email": AgentType.RECRUITER_ASSISTANT,
        "send_email": AgentType.RECRUITER_ASSISTANT,
        "enviar_mensagem": AgentType.RECRUITER_ASSISTANT,
        
        "disparar_triagem": AgentType.CV_SCREENING,
        "start_screening": AgentType.CV_SCREENING,
        "iniciar_triagem": AgentType.CV_SCREENING,
        
        "solicitar_dados": AgentType.RECRUITER_ASSISTANT,
        "request_data": AgentType.RECRUITER_ASSISTANT,
        "pedir_documentos": AgentType.RECRUITER_ASSISTANT,
        
        "analisar_perfil": AgentType.RECRUITER_ASSISTANT,
        "analyze_profile": AgentType.RECRUITER_ASSISTANT,
        "analise_detalhada": AgentType.RECRUITER_ASSISTANT,
        
        # Suggestion intents for quick actions
        "vagas_abertas": AgentType.RECRUITER_ASSISTANT,
        "listar_vagas": AgentType.RECRUITER_ASSISTANT,
        "open_jobs": AgentType.RECRUITER_ASSISTANT,
        
        "sem_candidatos": AgentType.RECRUITER_ASSISTANT,
        "vagas_sem_candidatos": AgentType.RECRUITER_ASSISTANT,
        "empty_pipeline": AgentType.RECRUITER_ASSISTANT,
        
        "sugerir_melhorias": AgentType.JOB_PLANNER,
        "melhorar_vaga": AgentType.JOB_PLANNER,
        "improve_job": AgentType.JOB_PLANNER,
        
        "comparar_vagas": AgentType.ANALYST_FEEDBACK,
        "compare_jobs": AgentType.ANALYST_FEEDBACK,
        
        "general_query": AgentType.ORCHESTRATOR,
    }
    
    AGENT_TYPE_TO_NAME = {
        AgentType.ORCHESTRATOR: "LIA Orchestrator",
        AgentType.JOB_PLANNER: "Job Planner Agent",
        AgentType.SOURCING: "Sourcing Agent",
        AgentType.CV_SCREENING: "CV Screening Agent",
        AgentType.INTERVIEWER: "Interviewer Agent",
        AgentType.WSI_EVALUATOR: "WSI Evaluator Agent",
        AgentType.SCHEDULING: "Scheduling Agent",
        AgentType.ANALYST_FEEDBACK: "Analyst & Feedback Agent",
        AgentType.ATS_INTEGRATOR: "ATS Integrator Agent",
        AgentType.RECRUITER_ASSISTANT: "Recruiter Assistant",
    }
    
    def __init__(self, llm_service):
        """Initialize Intent Router with LLM service."""
        self.llm = llm_service.claude
        self._llm_service = llm_service
        self.intent_prompt = self._create_intent_prompt()
        
    def _create_intent_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for intent classification."""
        system_message = PromptLoader.get_domain_prompt("orchestrator")
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Mensagem do usuário: {message}

Contexto adicional: {context}

Classifique o intent e retorne JSON válido.""")
        ])
    
    async def route(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Route user message to appropriate agent using confidence cascade.

        Tenta Haiku primeiro (mais barato), escala para Sonnet e Opus se a
        confidence da classificação for insuficiente. Thresholds configurados
        em settings (LLM_CASCADE_*_THRESHOLD).

        Args:
            message: User input message
            context: Optional context (conversation history, current state)

        Returns:
            Dict with: intent, target_agent, agent_type, confidence, reasoning,
                       requires_planning, model_used
        """
        import json as _json

        from app.core.config import settings

        context_str = ""
        if context:
            if "last_agent" in context:
                context_str += f"Último agente usado: {context['last_agent']}\n"
            if "current_job" in context:
                context_str += f"Vaga atual: {context['current_job']}\n"
            if "current_candidate" in context:
                context_str += f"Candidato atual: {context['current_candidate']}\n"

        # Monta o prompt completo para o cascade
        system_message = self.intent_prompt.messages[0].prompt.template  # type: ignore[attr-defined]
        human_template = (
            f"Mensagem do usuário: {message}\n\n"
            f"Contexto adicional: {context_str or 'Nenhum contexto adicional'}\n\n"
            "Classifique o intent e retorne JSON válido."
        )

        try:
            cascade_result = await self._llm_service.generate_with_cascade(
                prompt=human_template,
                system_prompt=system_message,
            )

            if cascade_result.requires_human or not cascade_result.content:
                logger.warning(
                    f"⚠️  Cascade esgotado para '{message[:80]}' — usando fallback recruiter_assistant"
                )
                return self._fallback_response(context, reason="cascade_exhausted")

            # Parse do JSON retornado pelo cascade
            try:
                result = _json.loads(cascade_result.content)
            except Exception:
                # Tenta extrair JSON embutido no texto
                import re
                m = re.search(r'\{.*\}', cascade_result.content, re.DOTALL)
                if m:
                    result = _json.loads(m.group())
                else:
                    raise ValueError(f"Cascade retornou resposta não-JSON: {cascade_result.content[:200]}")

            intent = result.get("intent", "general_query")
            confidence = float(result.get("confidence", cascade_result.confidence))
            reasoning = result.get("reasoning", "")
            requires_planning = result.get("requires_planning", False)
            entities = result.get("entities", {})

            agent_type = self.INTENT_TO_AGENT_TYPE.get(intent, AgentType.ORCHESTRATOR)
            target_agent = self.AGENT_TYPE_TO_NAME.get(agent_type, "LIA Orchestrator")

            if confidence < settings.ROUTER_FAST_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"⚠️  Low confidence intent routing:\n"
                    f"   Message: {message[:100]}\n"
                    f"   Intent: {intent} | Confidence: {confidence:.2f} | Model: {cascade_result.model_used}\n"
                    f"   Reasoning: {reasoning}"
                )
            else:
                logger.info(
                    f"✅ Intent routed: {intent} → {target_agent} "
                    f"(conf={confidence:.2f}, model={cascade_result.model_used})"
                )

            return {
                "intent": intent,
                "target_agent": target_agent,
                "agent_type": agent_type,
                "confidence": confidence,
                "reasoning": reasoning,
                "requires_planning": requires_planning,
                "entities": entities,
                "context": context or {},
                "model_used": cascade_result.model_used,
            }

        except Exception as e:
            logger.error(f"❌ Intent routing failed: {e}")
            return self._fallback_response(context, reason=str(e))

    def _fallback_response(self, context: dict[str, Any] | None, reason: str = "") -> dict[str, Any]:
        return {
            "intent": "recruiter_assistant",
            "target_agent": "Recruiter Assistant",
            "agent_type": AgentType.RECRUITER_ASSISTANT,
            "confidence": 0.3,
            "reasoning": f"Routing failed, using fallback: {reason}",
            "requires_planning": False,
            "entities": {},
            "context": context or {},
            "model_used": "fallback",
        }
    
    def get_agent_type_for_intent(self, intent: str) -> AgentType:
        """Get AgentType enum for a given intent string."""
        return self.INTENT_TO_AGENT_TYPE.get(intent, AgentType.ORCHESTRATOR)
    
    def get_agent_name(self, agent_type: AgentType) -> str:
        """Get human-readable name for an agent type."""
        return self.AGENT_TYPE_TO_NAME.get(agent_type, "Unknown Agent")
