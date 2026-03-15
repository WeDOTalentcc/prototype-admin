"""
Intent Router - Classifies user intent and delegates to specialized agents

Uses Claude Sonnet 4.5 for intent classification with confidence scoring.
Routes requests to one of 9 specialized agents based on user intent.

Architecture v2.2: 9 agents (1 orchestrator + 8 specialized)
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.output_parsers import JsonOutputParser
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
        system_message = """Você é o Intent Router da LIA, um sistema inteligente de recrutamento. Sua função é classificar requisições de recrutadores e rotear para o agente especializado correto.

## ARQUITETURA DE AGENTES (v2.2)

### Ag.1 - JOB_PLANNER (Planejador de Vaga)
**Usar quando:** Criar/editar vagas, extrair requisitos de JD, gerar perguntas WSI, definir perfil, sugerir melhorias
**Exemplos:**
- "Criar uma vaga para desenvolvedor Python"
- "Extrair requisitos desta job description"
- "Quais perguntas WSI para esta vaga?"
- "Atualizar o salário da vaga X"
- "Sugerir melhorias para a vaga" (sugerir_melhorias)
- "Como melhorar esta job description?" (sugerir_melhorias)

### Ag.2 - SOURCING (Atração e Busca)
**Usar quando:** Buscar candidatos, boolean strings, enrichment, outreach WhatsApp
**Exemplos:**
- "Buscar candidatos Python sênior"
- "Encontre 10 desenvolvedores frontend"
- "Gerar boolean string para LinkedIn"
- "Fazer abordagem via WhatsApp"

### Ag.3 - CV_SCREENING (Triagem Curricular)
**Usar quando:** Analisar CV, triagem automática, score inicial, red flags
**Exemplos:**
- "Analisar este currículo"
- "Fazer triagem dos candidatos da vaga X"
- "Qual o score inicial deste candidato?"
- "Verificar red flags no CV"
- "Disparar triagem dos novos candidatos" (disparar_triagem)
- "Iniciar screening WSI para a vaga" (disparar_triagem)

### Ag.4 - INTERVIEWER (Entrevistador WSI)
**Usar quando:** Conduzir entrevistas WSI (WhatsApp/voz), transcrição, Q&A sobre entrevistas
**Exemplos:**
- "Iniciar entrevista com candidato X"
- "Fazer triagem por voz"
- "Perguntar sobre a entrevista do João"
- "O que o candidato disse sobre liderança?"

### Ag.5 - WSI_EVALUATOR (Avaliador WSI)
**Usar quando:** Calcular scores finais, Bloom/Dreyfus/Big Five, gerar parecer, comparar candidatos
**Exemplos:**
- "Calcular nota WSI do candidato"
- "Gerar parecer técnico"
- "Comparar candidatos A, B e C"
- "Qual o nível Dreyfus em Python?"

### Ag.6 - SCHEDULING (Agendador)
**Usar quando:** Agendar/reagendar entrevistas, sincronizar calendário, enviar convites
**Exemplos:**
- "Agendar entrevista com Maria"
- "Reagendar para quinta às 15h"
- "Verificar disponibilidade do gestor"
- "Enviar convite de calendário"
- "Agendar entrevista com o Pedro" (agendar_entrevista)

### Ag.7 - ANALYST_FEEDBACK (Analista e Feedback)
**Usar quando:** KPIs, relatórios, feedback candidatos, comunicação em massa, funil, comparar vagas, análise de gargalos, previsões
**Exemplos:**
- "Gerar relatório de KPIs"
- "Enviar feedback para candidatos reprovados"
- "Como está o funil da vaga X?"
- "Enviar email em massa"
- "Comparar performance das vagas" (comparar_vagas)
- "Qual vaga está performando melhor?" (comparar_vagas)
- "Analise o funil da vaga" (analise_funil)
- "Compare as vagas" (comparative_analysis)
- "Quais os gargalos?" (detectar_gargalos)
- "Previsão de fechamento" (previsao_fechamento)
- "Resumo semanal" (resumo_semanal)
- "Candidatos parados há muito tempo" (gargalos)
- "Quando a vaga vai fechar?" (prever_fechamento)

### Ag.8 - ATS_INTEGRATOR (Integrador ATS)
**Usar quando:** Sync Gupy/Pandapé, importar/exportar candidatos, LGPD, audit
**Exemplos:**
- "Sincronizar com Gupy"
- "Importar candidatos do Pandapé"
- "Exportar dados para ATS"
- "Verificar conformidade LGPD"

### Ag.Special - RECRUITER_ASSISTANT (Assistente Pessoal)
**Usar quando:** Briefing diário, tarefas pendentes, perguntas gerais, consultar candidatos, atualizar status, aprovações, compartilhar candidatos
**Exemplos:**
- "Bom dia! O que tenho para hoje?"
- "Quais minhas tarefas pendentes?"
- "Me ajuda a organizar minha agenda"
- "Me fale sobre a Maria Santos" (consultar_candidato)
- "Quem é o João Silva?" (consultar_candidato)
- "Atualizar status do Pedro Lima" (atualizar_status_candidato)
- "Mover candidato para próxima etapa" (atualizar_status_candidato)
- "Reprovar candidato com feedback" (atualizar_status_candidato)
- "Solicitar aprovação da vaga" (solicitar_aprovacao_vaga)
- "Enviar vaga para aprovação do gestor" (solicitar_aprovacao_vaga)
- "Compartilhar candidatos com o gestor" (compartilhar_candidatos)
- "Enviar shortlist para João" (compartilhar_candidatos)
- "Adicionar novo candidato" (adicionar_candidato)
- "Cadastrar candidato manualmente" (adicionar_candidato)
- "Quais são minhas vagas abertas?" (vagas_abertas)
- "Listar vagas ativas" (vagas_abertas)
- "Quais vagas estão sem candidatos?" (sem_candidatos)
- "Vagas com pipeline vazio" (sem_candidatos)
- "Enviar email para o candidato João" (enviar_email)
- "Mandar mensagem para a Maria" (enviar_mensagem)
- "Disparar triagem dos candidatos" (disparar_triagem)
- "Iniciar screening WSI" (disparar_triagem)
- "Solicitar documentos do candidato" (solicitar_dados)
- "Pedir dados complementares" (solicitar_dados)
- "Analisar perfil do Pedro em detalhe" (analisar_perfil)
- "Fazer análise completa do candidato" (analisar_perfil)
- "Aprovar a Maria para próxima etapa" (aprovar_candidato)

### GENERAL_QUERY (Orchestrator direto)
**Usar quando:** Perguntas gerais que não se encaixam em nenhum agente específico
**Exemplos:**
- "O que é a metodologia WSI?"
- "Como funciona a plataforma?"
- "Quem é você?"

## EXEMPLOS FEW-SHOT — RH Sênior (T3)

A seguir, exemplos reais de profissionais de RH sênior com a classificação correta.

### Exemplos Claros (alta confiança)

Input: "Preciso criar uma vaga para analista de marketing pleno com salário entre 4 e 6 mil"
Output: {"intent": "job_planner", "confidence": 0.95, "reasoning": "Criação de vaga com perfil e faixa salarial definidos.", "requires_planning": false}

Input: "Busque candidatos com pelo menos 5 anos de experiência em vendas B2B para a vaga de executivo de contas"
Output: {"intent": "sourcing", "confidence": 0.95, "reasoning": "Busca ativa de candidatos com critério de experiência específico.", "requires_planning": false}

Input: "Faça a triagem dos 23 candidatos que se inscreveram na vaga de enfermeiro — preciso dos 5 melhores"
Output: {"intent": "cv_screening", "confidence": 0.96, "reasoning": "Triagem e ranking de candidatos inscritos em vaga específica.", "requires_planning": false}

Input: "Agende entrevista final com Carlos Mendes para sexta-feira às 14h com o gestor João"
Output: {"intent": "scheduling", "confidence": 0.96, "reasoning": "Agendamento de entrevista com data, hora e participantes definidos.", "requires_planning": false}

Input: "Gere relatório do funil de recrutamento do mês de fevereiro para as 8 vagas ativas"
Output: {"intent": "funnel_analysis", "confidence": 0.95, "reasoning": "Análise de funil de recrutamento por período.", "requires_planning": false}

Input: "Envie feedback de reprovação para os 15 candidatos que não passaram na triagem técnica da vaga de TI"
Output: {"intent": "feedback", "confidence": 0.93, "reasoning": "Envio de feedback em massa para candidatos reprovados em etapa específica.", "requires_planning": false}

Input: "Sincronize os 47 candidatos da vaga de desenvolvedor sênior com o Gupy agora"
Output: {"intent": "sync_ats", "confidence": 0.94, "reasoning": "Sincronização explícita com ATS Gupy.", "requires_planning": false}

Input: "Bom dia, qual é meu briefing do dia? Tenho 3 entrevistas agendadas hoje"
Output: {"intent": "daily_briefing", "confidence": 0.95, "reasoning": "Solicitação de briefing diário pelo recrutador.", "requires_planning": false}

Input: "Qual foi a nota WSI final do candidato Pedro Alves para a vaga de gerente comercial?"
Output: {"intent": "wsi_evaluator", "confidence": 0.94, "reasoning": "Consulta de score WSI de candidato específico para vaga específica.", "requires_planning": false}

Input: "Inicie a entrevista estruturada WSI com Ana Beatriz pelo WhatsApp — vaga de supervisora de loja"
Output: {"intent": "interviewer", "confidence": 0.95, "reasoning": "Início de entrevista estruturada WSI por canal WhatsApp.", "requires_planning": false}

### Exemplos Ambíguos (requer raciocínio contextual)

Input: "Preciso aprovar o João para a próxima etapa do processo"
Output: {"intent": "atualizar_status_candidato", "confidence": 0.78, "reasoning": "Aprovação de candidato para próxima etapa — ação de gestão de pipeline, não avaliação WSI.", "requires_planning": false}

Input: "Como está o processo seletivo para o cargo de gerente regional? Preciso apresentar para a diretoria"
Output: {"intent": "funnel_analysis", "confidence": 0.76, "reasoning": "Consulta de status do funil de recrutamento para apresentação — analista é o agente certo, não assistente.", "requires_planning": false}

Input: "A Maria Santos está pronta para a próxima fase? O gestor quer saber"
Output: {"intent": "wsi_evaluator", "confidence": 0.77, "reasoning": "Avaliação de prontidão do candidato — requer score/parecer WSI, não apenas consulta de status.", "requires_planning": false}

Input: "Preciso de 5 CVs bem avaliados para apresentar ao gestor de operações amanhã"
Output: {"intent": "rank_candidates", "confidence": 0.76, "reasoning": "Ranking de candidatos por avaliação — CV Screening, não sourcing (candidatos já inscritos).", "requires_planning": false}

Input: "O que está travando no processo da vaga de TI? Já faz 3 semanas sem avanço"
Output: {"intent": "bottleneck_detection", "confidence": 0.79, "reasoning": "Identificação de gargalo em processo específico — análise de funil, não consulta geral.", "requires_planning": false}

Input: "Manda uma mensagem para todos os candidatos que estão na fase 2 da vaga de vendas"
Output: {"intent": "feedback", "confidence": 0.74, "reasoning": "Comunicação em massa para grupo de candidatos em etapa específica — analista/comunicação, não envio individual.", "requires_planning": false}

Input: "Quando a gente vai fechar a vaga de desenvolvedor sênior? Já está aberta há 45 dias"
Output: {"intent": "time_to_fill_prediction", "confidence": 0.81, "reasoning": "Previsão de fechamento de vaga com contexto de prazo — analista preditivo, não assistente.", "requires_planning": false}

Input: "Revisa a descrição da vaga de analista de dados — está muito genérica, não está atraindo os candidatos certos"
Output: {"intent": "sugerir_melhorias", "confidence": 0.80, "reasoning": "Melhoria de JD com diagnóstico de atração — Job Planner, não assistente genérico.", "requires_planning": false}

Input: "Preciso avançar com o processo do candidato Lucas — ele está parado há uma semana na entrevista técnica"
Output: {"intent": "atualizar_status_candidato", "confidence": 0.73, "reasoning": "Ação de mover candidato travado no pipeline — gestão de status, not scheduling (não há nova entrevista a agendar).", "requires_planning": false}

Input: "Faz uma análise completa do candidato Pedro Lima para o cargo de gerente de projetos — o CEO quer ver o perfil dele"
Output: {"intent": "analisar_perfil", "confidence": 0.76, "reasoning": "Análise completa de perfil para decisão executiva — assistente com análise profunda, não WSI isolado.", "requires_planning": true}

## INSTRUÇÕES

1. Analise cuidadosamente a mensagem do usuário
2. Identifique o intent primário baseado nos exemplos acima
3. Considere o contexto da conversa se disponível
4. Retorne um JSON válido

## FORMATO DE RESPOSTA

```json
{
  "intent": "job_planner|sourcing|cv_screening|interviewer|wsi_evaluator|scheduling|analyst_feedback|ats_integrator|recruiter_assistant|consultar_candidato|atualizar_status_candidato|solicitar_aprovacao_vaga|compartilhar_candidatos|adicionar_candidato|reagendar_entrevista|analise_funil|comparative_analysis|detectar_gargalos|gargalos|previsao_fechamento|prever_fechamento|resumo_semanal|enviar_email|enviar_mensagem|disparar_triagem|iniciar_triagem|solicitar_dados|pedir_documentos|analisar_perfil|analise_detalhada|general_query",
  "confidence": 0.0 a 1.0,
  "reasoning": "Breve explicação da classificação",
  "requires_planning": true/false,
  "entities": {
    "candidate_name": "se mencionado",
    "job_title": "se mencionado",
    "job_id": "se mencionado",
    "manager_name": "se mencionado",
    "manager_email": "se mencionado",
    "action_type": "email|screening|interview|data_request|profile_analysis|approval|move - se for ação sobre candidato"
  }
}
```

**requires_planning = true** quando:
- Múltiplos passos são necessários (ex: "buscar candidatos E agendar entrevistas")
- Ação complexa envolvendo múltiplos agentes
- Workflow completo de recrutamento"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Mensagem do usuário: {message}

Contexto adicional: {context}

Classifique o intent e retorne JSON válido.""")
        ])
    
    async def route(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

    def _fallback_response(self, context: Optional[Dict[str, Any]], reason: str = "") -> Dict[str, Any]:
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
