"""
Task Planner - Decomposes complex multi-step workflows into atomic tasks

For requests that require multiple agents, creates execution plan with:
- Ordered task sequence
- Agent assignments  
- Dependencies between tasks
- Success criteria

Architecture v2.2: 9 agents (1 orchestrator + 8 specialized)
"""

import logging
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.shared.agents.agent_types import AgentType

logger = logging.getLogger(__name__)



# UC-P3-14: TaskPlanner is gated by LIA_V2_USE_PLAN_SERVICE feature flag.
# Promotion to production without flag: 2026-07-01
# To promote: set LIA_V2_USE_PLAN_SERVICE=true in production env
# and remove this gate once stable for 2 weeks.
# See: app/orchestrator/main_orchestrator._is_plan_service_enabled()
#
# Usage pattern:
#   from app.orchestrator.execution.main_orchestrator import _is_plan_service_enabled
#   if _is_plan_service_enabled():
#       plan = task_planner.plan(request)
#   else:
#       # use legacy planner
class TaskPlanner:
    """Plans multi-step workflows by decomposing into atomic tasks."""
    
    AGENT_TYPE_MAPPING = {
        "Job Planner Agent": AgentType.JOB_PLANNER,
        "Sourcing Agent": AgentType.SOURCING,
        "CV Screening Agent": AgentType.CV_SCREENING,
        "Interviewer Agent": AgentType.INTERVIEWER,
        "WSI Evaluator Agent": AgentType.WSI_EVALUATOR,
        "Scheduling Agent": AgentType.SCHEDULING,
        "Analyst & Feedback Agent": AgentType.ANALYST_FEEDBACK,
        "ATS Integrator Agent": AgentType.ATS_INTEGRATOR,
        "Recruiter Assistant": AgentType.RECRUITER_ASSISTANT,
    }
    
    def __init__(self, llm_service):
        """Initialize Task Planner with LLM service."""
        self.llm = llm_service.get_audited_model()
        self.planning_prompt = self._create_planning_prompt()
        
    def _create_planning_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for task planning."""
        system_message = """Você é o Task Planner da LIA, responsável por decompor requisições complexas de recrutamento em tarefas atômicas executáveis.

## AGENTES DISPONÍVEIS (Arquitetura v2.2)

| Agente | Responsabilidades |
|--------|-------------------|
| **Job Planner Agent** | Criar/editar vagas, extrair JD, gerar perguntas WSI |
| **Sourcing Agent** | Buscar candidatos, boolean strings, outreach |
| **CV Screening Agent** | Parse CV, triagem automática, score inicial |
| **Interviewer Agent** | Entrevistas WSI (voz/WhatsApp), transcrição |
| **WSI Evaluator Agent** | Scores Bloom/Dreyfus/Big Five, pareceres, ranking |
| **Scheduling Agent** | Agendar entrevistas, calendário Microsoft |
| **Analyst & Feedback Agent** | KPIs, relatórios, feedback, comunicação massa |
| **ATS Integrator Agent** | Sync Gupy/Pandapé, import/export, LGPD |
| **Recruiter Assistant** | Briefing diário, tarefas, assistência geral |

## WORKFLOWS COMUNS

### Pipeline Completo de Recrutamento:
1. Job Planner → Criar vaga com perfil
2. Sourcing → Buscar candidatos
3. CV Screening → Triagem inicial
4. Interviewer → Entrevistas WSI
5. WSI Evaluator → Avaliação final
6. Scheduling → Agendar entrevistas finais
7. Analyst & Feedback → Relatório e feedback

### Busca e Triagem Rápida:
1. Sourcing → Buscar candidatos
2. CV Screening → Triagem automática
3. WSI Evaluator → Ranking

### Comunicação em Massa:
1. Analyst & Feedback → Preparar comunicação
2. (Loop) Enviar emails/WhatsApp

## INSTRUÇÕES

1. Analise a requisição do usuário
2. Identifique TODAS as tarefas necessárias
3. Ordene por dependências (qual precisa do resultado da anterior)
4. Atribua cada tarefa ao agente correto
5. Defina critérios de sucesso mensuráveis

## FORMATO DE RESPOSTA

```json
{{
  "plan": [
    {{
      "step": 1,
      "description": "Descrição clara da tarefa",
      "agent": "Nome do Agente",
      "agent_type": "job_planner|sourcing|cv_screening|interviewer|wsi_evaluator|scheduling|analyst_feedback|ats_integrator",
      "dependencies": [],
      "success_criteria": "Critério mensurável",
      "estimated_duration_seconds": 30,
      "can_run_parallel": false
    }}
  ],
  "estimated_steps": 2,
  "estimated_total_duration_seconds": 60,
  "requires_user_confirmation": false
}}
```

**can_run_parallel = true** quando a tarefa não depende de nenhuma outra e pode rodar simultaneamente."""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Requisição do usuário: {message}
Intent detectado: {intent}
Contexto: {context}

Crie um plano de execução detalhado em JSON.""")
        ])
    
    async def create_plan(
        self, 
        message: str, 
        intent: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create execution plan for multi-step workflow.
        
        Args:
            message: User request
            intent: Detected intent from router
            context: Optional context (current job, candidate, etc)
            
        Returns:
            Dict with execution plan (steps, agents, dependencies)
        """
        try:
            context_str = ""
            if context:
                if "current_job" in context:
                    context_str += f"Vaga atual: {context['current_job']}\n"
                if "current_candidate" in context:
                    context_str += f"Candidato: {context['current_candidate']}\n"
                if "candidates_found" in context:
                    context_str += f"Candidatos encontrados: {context['candidates_found']}\n"
            
            chain = self.planning_prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "message": message,
                "intent": intent,
                "context": context_str or "Nenhum contexto adicional"
            })
            
            plan = result.get("plan", [])
            estimated_steps = result.get("estimated_steps", len(plan))
            total_duration = result.get("estimated_total_duration_seconds", 0)
            requires_confirmation = result.get("requires_user_confirmation", False)
            
            for step in plan:
                agent_name = step.get("agent", "")
                if agent_name in self.AGENT_TYPE_MAPPING:
                    step["agent_type_enum"] = self.AGENT_TYPE_MAPPING[agent_name]
            
            parallel_steps = [s for s in plan if s.get("can_run_parallel", False)]
            
            logger.info(
                f"📋 Task plan created:\n"
                f"   Steps: {estimated_steps}\n"
                f"   Parallel steps: {len(parallel_steps)}\n"
                f"   Estimated duration: {total_duration}s\n"
                f"   Agents involved: {set([step['agent'] for step in plan])}"
            )
            
            return {
                "plan": plan,
                "estimated_steps": estimated_steps,
                "estimated_total_duration_seconds": total_duration,
                "requires_orchestration": len(plan) > 1,
                "requires_user_confirmation": requires_confirmation,
                "parallel_steps_count": len(parallel_steps)
            }
            
        except Exception as e:
            logger.error(f"❌ Task planning failed: {e}")
            return {
                "plan": [{
                    "step": 1,
                    "description": message,
                    "agent": "Recruiter Assistant",
                    "agent_type": "recruiter_assistant",
                    "dependencies": [],
                    "success_criteria": "Complete request",
                    "estimated_duration_seconds": 30,
                    "can_run_parallel": False
                }],
                "estimated_steps": 1,
                "estimated_total_duration_seconds": 30,
                "requires_orchestration": False,
                "requires_user_confirmation": False,
                "parallel_steps_count": 0
            }
    
    async def validate_plan(self, plan: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """
        Validate a plan for correctness.
        
        Checks:
        - All dependencies reference valid steps
        - No circular dependencies
        - All agents are valid
        
        Returns:
            Dict with: valid (bool), errors (list)
        """
        if plan is None:
            plan = []
        errors = []
        step_numbers = [s["step"] for s in plan]
        
        for step in plan:
            for dep in step.get("dependencies", []):
                if dep not in step_numbers:
                    errors.append(f"Step {step['step']} has invalid dependency: {dep}")
                if dep >= step["step"]:
                    errors.append(f"Step {step['step']} depends on future step: {dep}")
            
            if step.get("agent") not in self.AGENT_TYPE_MAPPING and step.get("agent") != "Recruiter Assistant":
                errors.append(f"Step {step['step']} has unknown agent: {step.get('agent')}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
