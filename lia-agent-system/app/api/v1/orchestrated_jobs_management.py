"""
Orchestrated Jobs Management Chat API - Routes job portfolio queries through
the Jobs Management Assistant Service with analytical routing and closed-loop execution.

Handles macro-level job management: dashboard, SLA, bottlenecks, department
performance, job comparison, urgency analysis, and actionable job operations.

v2.0: Closed-loop action execution - LIA executes job management actions directly
instead of requiring manual user interaction through UI modals.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.recruiter_assistant.prompts.jobs_management_prompts import (
    JobsManagementCommandType,
    detect_jobs_command_type,
)
from app.domains.recruiter_assistant.services.jobs_management_assistant_service import (
    jobs_management_assistant,
)
from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    action_executor,
    is_confirmation,
    is_rejection,
)
from app.orchestrator.execution.pending_action import PendingActionState, pending_action_store
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

_ANALYTICAL_COMMAND_TYPES = {
    JobsManagementCommandType.VISAO_GERAL.value,
    JobsManagementCommandType.VAGAS_URGENTES.value,
    JobsManagementCommandType.VAGAS_PARADAS.value,
    JobsManagementCommandType.SLA_VENCENDO.value,
    JobsManagementCommandType.PERFORMANCE_DEPARTAMENTO.value,
    JobsManagementCommandType.COMPARAR_VAGAS.value,
    JobsManagementCommandType.GARGALOS_GERAIS.value,
    JobsManagementCommandType.TAXA_PREENCHIMENTO.value,
    JobsManagementCommandType.TEMPO_MEDIO_CONTRATACAO.value,
    JobsManagementCommandType.VAGAS_SEM_CANDIDATOS.value,
    JobsManagementCommandType.PIPELINE_HEALTH.value,
    JobsManagementCommandType.TENDENCIAS.value,
    JobsManagementCommandType.ANALISE_GERAL.value,
}

INTENT_TO_UI_ACTION: dict[str, str] = {
    "criar_vaga": "start_job_wizard",
    "create_job": "start_job_wizard",
    "nova_vaga": "start_job_wizard",
    "pausar_vaga": "pause_job",
    "fechar_vaga": "close_job",
    "duplicar_vaga": "duplicate_job",
    "reabrir_vaga": "reopen_job",
    "filtrar_vagas": "filter_jobs",
}

_JOBS_MGMT_ACTION_KEYWORDS: dict[str, list[str]] = {
    "pausar_vaga": ["pausar vaga", "pause"],
    "fechar_vaga": ["fechar vaga", "encerrar vaga", "close"],
    "duplicar_vaga": ["duplicar vaga", "copiar vaga"],
    "reabrir_vaga": ["reabrir vaga", "reopen"],
}


class OrchestratedJobsManagementRequest(WeDoBaseModel):
    message: str = Field(..., description="User's natural language query")
    jobs_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated job metrics: total, active, paused, completed, urgent, etc.",
    )
    selected_jobs: list[dict[str, Any]] | None = Field(
        None, description="Jobs selected for batch operations"
    )
    top_jobs: list[dict[str, Any]] | None = Field(
        None, description="Top jobs with detailed metrics"
    )
    conversation_history: list[dict[str, str]] | None = Field(
        None, description="Recent conversation messages for context"
    )
    action: str | None = Field(None, description="Pre-detected action/intent from frontend")
    user_id: str | None = Field(default="recruiter", description="User ID")
    conversation_id: str | None = Field(None, description="Conversation ID for multi-turn context")


class OrchestratedJobsManagementResponse(BaseModel):
    success: bool
    content: str = Field(..., description="Formatted markdown response")
    agent_used: str = Field(default="JobsManagementAssistant")
    intent_detected: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., description="Routing confidence")
    structured_data: dict[str, Any] | None = None
    suggested_prompts: list[str] = Field(default_factory=list)
    ui_action: str | None = Field(None, description="Frontend action trigger")
    ui_action_params: dict[str, Any] | None = Field(None, description="Parameters for UI action")
    action_executed: bool = Field(default=False)
    action_result: dict[str, Any] | None = None
    action_type: str | None = None
    needs_confirmation: bool = Field(default=False)
    needs_params: bool = Field(default=False)
    pending_action_id: str | None = None
    conversation_id: str | None = None


def detect_actionable_intent(message: str) -> str | None:
    msg_lower = message.lower().strip()
    action_keywords = {
        "criar_vaga": ["criar vaga", "nova vaga", "abrir vaga", "abrir posição", "create job"],
        "pausar_vaga": ["pausar", "congelar", "pause", "suspender vaga"],
        "fechar_vaga": ["fechar vaga", "encerrar vaga", "close job", "concluir vaga"],
        "duplicar_vaga": ["duplicar", "copiar vaga", "clonar vaga", "duplicate"],
    }
    for intent, keywords in action_keywords.items():
        for kw in keywords:
            if kw in msg_lower:
                return intent
    return None


def _detect_jobs_mgmt_actionable_intent(message: str) -> str | None:
    msg_lower = message.lower().strip()
    for intent, keywords in _JOBS_MGMT_ACTION_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return intent
    return None


def _extract_jobs_mgmt_entities(
    request: "OrchestratedJobsManagementRequest",
) -> dict[str, Any]:
    entities: dict[str, Any] = {}

    if request.selected_jobs and len(request.selected_jobs) > 0:
        first_job = request.selected_jobs[0]
        entities["job_id"] = str(first_job.get("id", first_job.get("job_id", "")))
        entities["job_title"] = first_job.get("title", first_job.get("job_title", ""))

    if not entities.get("job_id"):
        jc = request.jobs_context
        if jc.get("job_id"):
            entities["job_id"] = str(jc["job_id"])
        if jc.get("job_title"):
            entities["job_title"] = jc["job_title"]

    if not entities.get("job_id"):
        msg_lower = request.message.lower()
        if request.top_jobs:
            for job in request.top_jobs:
                job_title = (job.get("title") or job.get("job_title") or "").lower()
                if job_title and job_title in msg_lower:
                    entities["job_id"] = str(job.get("id", job.get("job_id", "")))
                    entities["job_title"] = job.get("title", job.get("job_title", ""))
                    break

    return entities


def _extract_param_value_from_message(
    message: str, param_name: str, request: "OrchestratedJobsManagementRequest",
) -> Any | None:
    msg = message.strip()
    if not msg:
        return None

    if param_name == "job_id":
        if request.selected_jobs and len(request.selected_jobs) > 0:
            first_job = request.selected_jobs[0]
            return str(first_job.get("id", first_job.get("job_id", "")))
        if request.top_jobs:
            msg_lower = msg.lower()
            for job in request.top_jobs:
                job_title = (job.get("title") or job.get("job_title") or "").lower()
                if job_title and job_title in msg_lower:
                    return str(job.get("id", job.get("job_id", "")))
        return None

    if param_name in ("reason", "outcome", "new_title"):
        if len(msg) > 0:
            return msg
        return None

    if len(msg) > 0:
        return msg
    return None


@router.post("/jobs-management", response_model=OrchestratedJobsManagementResponse)
async def orchestrated_jobs_management(request: OrchestratedJobsManagementRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Process job portfolio queries through the Jobs Management Assistant.

    v2.0 Closed-loop flow:
    0. Check for pending multi-turn action (confirmation or parameter collection)
    1. Detect actionable intents for job creation (UI-driven)
    2. Analytical routing through Jobs Management Assistant
    3. ActionExecutor for job management actions (pause, close, duplicate, reopen)
    4. Orchestrator fallback with helpful command listing
    """
    try:
        logger.info(f"[JobsManagement] Processing: {request.message[:100]}...")

        conv_id = request.conversation_id or str(uuid.uuid4())

        # === PHASE 0: Check pending action (multi-turn / confirmation) ===
        pending = pending_action_store.get(conv_id)

        if pending:
            if pending.awaiting_confirmation:
                if is_confirmation(request.message):
                    config = ACTIONABLE_INTENTS.get(pending.intent, {})
                    exec_result = await action_executor._execute_action(
                        pending.intent, config, pending.collected_params,
                        {"conversation_id": conv_id, "user_id": request.user_id}
                    )
                    pending_action_store.remove(conv_id)

                    return OrchestratedJobsManagementResponse(
                        success=True,
                        content=exec_result.message,
                        agent_used="ActionExecutor",
                        intent_detected=pending.intent,
                        confidence=1.0,
                        suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                        conversation_id=conv_id,
                        action_executed=True,
                        action_result=exec_result.data,
                        action_type=exec_result.action_type,
                    )
                elif is_rejection(request.message):
                    pending_action_store.remove(conv_id)
                    return OrchestratedJobsManagementResponse(
                        success=True,
                        content="Ok, ação cancelada. Como posso te ajudar com as vagas?",
                        agent_used="ActionExecutor",
                        intent_detected="cancelamento",
                        confidence=1.0,
                        suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                        conversation_id=conv_id,
                    )
                else:
                    pending_action_store.remove(conv_id)

            elif pending.missing_params:
                next_param = pending.next_missing_param()
                if next_param:
                    extracted_value = _extract_param_value_from_message(
                        request.message, next_param, request
                    )
                    if extracted_value:
                        pending.add_param(next_param, extracted_value)

                        if next_param == "job_id" and request.selected_jobs:
                            first_job = request.selected_jobs[0]
                            pending.collected_params["job_title"] = first_job.get("title", first_job.get("job_title", ""))

                        if pending.is_complete:
                            config = ACTIONABLE_INTENTS.get(pending.intent, {})
                            if config.get("requires_confirmation", False):
                                summary = action_executor._build_confirmation_summary(
                                    pending.intent, config, pending.collected_params
                                )
                                pending.awaiting_confirmation = True
                                pending.confirmation_summary = summary
                                pending_action_store.save(conv_id, pending)

                                return OrchestratedJobsManagementResponse(
                                    success=True,
                                    content=summary["message"],
                                    agent_used="ActionExecutor",
                                    intent_detected=pending.intent,
                                    confidence=1.0,
                                    suggested_prompts=[],
                                    conversation_id=conv_id,
                                    needs_confirmation=True,
                                    pending_action_id=pending.pending_id,
                                )
                            else:
                                exec_result = await action_executor._execute_action(
                                    pending.intent, config, pending.collected_params,
                                    {"conversation_id": conv_id, "user_id": request.user_id}
                                )
                                pending_action_store.remove(conv_id)
                                return OrchestratedJobsManagementResponse(
                                    success=True,
                                    content=exec_result.message,
                                    agent_used="ActionExecutor",
                                    intent_detected=pending.intent,
                                    confidence=1.0,
                                    suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                                    conversation_id=conv_id,
                                    action_executed=True,
                                    action_result=exec_result.data,
                                    action_type=exec_result.action_type,
                                )
                        else:
                            next_param2 = pending.next_missing_param()
                            config = ACTIONABLE_INTENTS.get(pending.intent, {})
                            prompt = config.get("clarification_prompts", {}).get(
                                next_param2, f"Informe: {next_param2}"
                            )
                            pending_action_store.save(conv_id, pending)

                            return OrchestratedJobsManagementResponse(
                                success=True,
                                content=prompt,
                                agent_used="ActionExecutor",
                                intent_detected=pending.intent,
                                confidence=1.0,
                                suggested_prompts=[],
                                conversation_id=conv_id,
                                needs_params=True,
                                pending_action_id=pending.pending_id,
                            )
                    else:
                        pending_action_store.remove(conv_id)

        # === PHASE 1: Detect job creation intent (UI-driven) ===
        # Job creation abre o wizard — trata ANTES do ReAct pois não é query analítica.
        actionable_intent = detect_actionable_intent(request.message)

        if actionable_intent and actionable_intent == "criar_vaga":
            ui_action = INTENT_TO_UI_ACTION.get(actionable_intent)
            logger.info(f"[JobsManagement] Job creation intent: {actionable_intent} -> {ui_action}")

            return OrchestratedJobsManagementResponse(
                success=True,
                content="Entendi! Vou abrir o **assistente de criação de vagas** para você. 🚀",
                intent_detected=actionable_intent,
                confidence=0.95,
                suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                ui_action=ui_action,
                ui_action_params={"initial_message": request.message},
                conversation_id=conv_id,
            )

        # === PHASE 2: JobsManagementReActAgent — ReAct loop com tool calling ao DB ===
        # Caminho principal: agente autônomo com acesso real ao banco de dados.
        try:
            from lia_agents_core.agent_interface import AgentInput as ReactAgentInput

            from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent

            agent_input = ReactAgentInput(
                message=request.message,
                session_id=conv_id,
                company_id=company_id,
                user_id=request.user_id or "recruiter",
                context={
                    "jobs_context": request.jobs_context,
                    "selected_jobs": request.selected_jobs or [],
                    "top_jobs": request.top_jobs or [],
                },
                conversation_history=[
                    {"role": m.get("role", "user"), "content": m.get("content", "")}
                    for m in (request.conversation_history or [])
                ],
            )

            agent = JobsManagementReActAgent()
            output = await agent.process(agent_input)

            return OrchestratedJobsManagementResponse(
                success=True,
                content=output.message,
                agent_used="JobsManagementReActAgent",
                intent_detected="react_agent",
                confidence=output.confidence,
                structured_data=output.state_updates or None,
                suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?", "Compare vagas por departamento"],
                conversation_id=conv_id,
                needs_confirmation=any(a.requires_confirmation for a in output.actions) if output.actions else False,
                action_executed=bool(output.tool_results),
            )
        except Exception as react_error:
            logger.warning(f"[JobsManagement] ReAct agent failed, falling back to legacy: {react_error}")

        # === PHASE 3 (FALLBACK): Analytical routing through Jobs Management Assistant ===
        cmd_type, confidence = detect_jobs_command_type(request.message)
        logger.info(f"[JobsManagement] Fallback analytical command: {cmd_type} (confidence: {confidence:.2f})")

        if cmd_type in _ANALYTICAL_COMMAND_TYPES:
            try:
                result = await jobs_management_assistant.process_command(
                    command=request.message,
                    command_type=cmd_type,
                    jobs_context=request.jobs_context,
                    selected_jobs=request.selected_jobs,
                    top_jobs=request.top_jobs,
                    conversation_history=request.conversation_history,
                )

                return OrchestratedJobsManagementResponse(
                    success=True,
                    content=result["content"],
                    intent_detected=cmd_type,
                    confidence=result.get("confidence", confidence),
                    structured_data=result.get("structured_data"),
                    suggested_prompts=result.get("suggested_prompts", []),
                    ui_action=result.get("ui_action"),
                    ui_action_params=result.get("ui_action_params"),
                    conversation_id=conv_id,
                )
            except Exception as svc_error:
                logger.warning(f"[JobsManagement] Service error: {svc_error}, using fallback")

        # === PHASE 4 (FALLBACK): ActionExecutor for job management actions ===
        jobs_mgmt_intent = _detect_jobs_mgmt_actionable_intent(request.message)

        if jobs_mgmt_intent and jobs_mgmt_intent in ACTIONABLE_INTENTS:
            logger.info(f"[JobsManagement] ActionExecutor intent: {jobs_mgmt_intent}")
            extracted_entities = _extract_jobs_mgmt_entities(request)

            # === BULK: per-job actions with multiple selected_jobs ===
            _PER_JOB_BULK_INTENTS = {"pausar_vaga", "fechar_vaga", "duplicar_vaga", "reabrir_vaga"}
            _INTENT_ACTION_LABEL = {
                "pausar_vaga": "pausada",
                "fechar_vaga": "fechada",
                "duplicar_vaga": "duplicada",
                "reabrir_vaga": "reaberta",
            }
            selected_jobs = request.selected_jobs or []
            if jobs_mgmt_intent in _PER_JOB_BULK_INTENTS and len(selected_jobs) > 1:
                logger.info(
                    f"[JobsManagement] Bulk {jobs_mgmt_intent} over {len(selected_jobs)} jobs"
                )
                succeeded: list[str] = []
                failed: list[str] = []
                ctx = {
                    "conversation_id": conv_id,
                    "user_id": request.user_id,
                    "jobs_context": request.jobs_context,
                }
                for job in selected_jobs:
                    job_id = str(job.get("id", job.get("job_id", "")))
                    job_title = job.get("title", job.get("job_title", job_id))
                    if not job_id:
                        failed.append(job_title or "?")
                        continue
                    bulk_entities = dict(extracted_entities)
                    bulk_entities["job_id"] = job_id
                    bulk_entities["job_title"] = job_title
                    try:
                        r = await action_executor.try_execute(
                            intent=jobs_mgmt_intent,
                            entities=bulk_entities,
                            candidates_data=[],
                            context=ctx,
                        )
                        if r.status == "executed":
                            succeeded.append(job_title)
                        else:
                            failed.append(job_title)
                    except Exception as bulk_err:
                        logger.warning(
                            f"[JobsManagement] Bulk {jobs_mgmt_intent} failed for {job_id}: {bulk_err}"
                        )
                        failed.append(job_title)

                action_label = _INTENT_ACTION_LABEL.get(jobs_mgmt_intent, "processada")
                if succeeded and not failed:
                    msg = f"{len(succeeded)} vaga(s) {action_label}(s) com sucesso: {', '.join(succeeded)}."
                elif succeeded:
                    msg = (
                        f"{len(succeeded)} vaga(s) {action_label}(s) com sucesso: {', '.join(succeeded)}. "
                        f"Falhou: {', '.join(failed)}."
                    )
                else:
                    msg = f"Não foi possível executar a ação nas vagas: {', '.join(failed)}."

                return OrchestratedJobsManagementResponse(
                    success=bool(succeeded),
                    content=msg,
                    agent_used="ActionExecutor",
                    intent_detected=jobs_mgmt_intent,
                    confidence=1.0,
                    suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                    conversation_id=conv_id,
                    action_executed=bool(succeeded),
                    action_result={"succeeded": succeeded, "failed": failed},
                    action_type=INTENT_TO_UI_ACTION.get(jobs_mgmt_intent, jobs_mgmt_intent),
                )

            action_result = await action_executor.try_execute(
                intent=jobs_mgmt_intent,
                entities=extracted_entities,
                candidates_data=[],
                context={
                    "conversation_id": conv_id,
                    "user_id": request.user_id,
                    "jobs_context": request.jobs_context,
                },
            )

            if action_result.status == "executed":
                return OrchestratedJobsManagementResponse(
                    success=True,
                    content=action_result.message,
                    agent_used="ActionExecutor",
                    intent_detected=jobs_mgmt_intent,
                    confidence=1.0,
                    suggested_prompts=["Como estão as vagas?", "Quais vagas precisam de atenção?"],
                    conversation_id=conv_id,
                    action_executed=True,
                    action_result=action_result.data,
                    action_type=action_result.action_type,
                )

            if action_result.status == "needs_confirmation":
                config = ACTIONABLE_INTENTS[jobs_mgmt_intent]
                collected = action_result.data.get("collected_params", {}) if action_result.data else {}
                pending_id = action_result.pending_action_id or str(uuid.uuid4())

                pending_state = PendingActionState(
                    pending_id=pending_id,
                    intent=jobs_mgmt_intent,
                    action_id=config["action_id"],
                    domain_id=config["domain_id"],
                    collected_params=collected,
                    missing_params=[],
                    conversation_id=conv_id,
                    awaiting_confirmation=True,
                    confirmation_summary=action_result.confirmation_summary,
                )
                pending_action_store.save(conv_id, pending_state)

                return OrchestratedJobsManagementResponse(
                    success=True,
                    content=action_result.message,
                    agent_used="ActionExecutor",
                    intent_detected=jobs_mgmt_intent,
                    confidence=1.0,
                    suggested_prompts=[],
                    conversation_id=conv_id,
                    needs_confirmation=True,
                    pending_action_id=pending_id,
                )

            if action_result.status == "needs_params":
                config = ACTIONABLE_INTENTS[jobs_mgmt_intent]
                collected = action_result.data.get("collected_params", {}) if action_result.data else {}
                missing = action_result.missing_params or []
                pending_id = action_result.pending_action_id or str(uuid.uuid4())

                pending_state = PendingActionState(
                    pending_id=pending_id,
                    intent=jobs_mgmt_intent,
                    action_id=config["action_id"],
                    domain_id=config["domain_id"],
                    collected_params=collected,
                    missing_params=missing,
                    conversation_id=conv_id,
                )
                pending_action_store.save(conv_id, pending_state)

                return OrchestratedJobsManagementResponse(
                    success=True,
                    content=action_result.message,
                    agent_used="ActionExecutor",
                    intent_detected=jobs_mgmt_intent,
                    confidence=1.0,
                    suggested_prompts=[],
                    conversation_id=conv_id,
                    needs_params=True,
                    pending_action_id=pending_id,
                )

            if action_result.status == "error":
                logger.warning(f"[JobsManagement] ActionExecutor error: {action_result.error_detail}")

        # === PHASE 5: Orchestrator fallback ===
        fallback_content = _generate_fallback(request.message, request.jobs_context)
        return OrchestratedJobsManagementResponse(
            success=True,
            content=fallback_content,
            intent_detected=cmd_type,
            confidence=0.5,
            suggested_prompts=[
                "Como estão as vagas?",
                "Quais vagas precisam de atenção urgente?",
                "Compare as vagas por departamento",
                "Pausar vaga [nome]",
                "Fechar vaga [nome]",
                "Duplicar vaga [nome]",
                "Reabrir vaga [nome]",
            ],
            conversation_id=conv_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[JobsManagement] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing jobs management chat: {str(e)}",
        )


@router.get("/jobs-management/intents", response_model=None)
async def get_jobs_management_intents(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    return {
        "intents": [
            {
                "id": "visao_geral",
                "description": "Dashboard geral de vagas",
                "keywords": ["visão geral", "resumo", "dashboard", "como estão as vagas"],
            },
            {
                "id": "vagas_urgentes",
                "description": "Vagas com prioridade alta",
                "keywords": ["urgente", "prioridade", "crítica", "atenção"],
            },
            {
                "id": "vagas_paradas",
                "description": "Vagas sem movimentação",
                "keywords": ["parada", "sem movimentação", "estagnada"],
            },
            {
                "id": "sla_vencendo",
                "description": "Vagas com SLA em risco",
                "keywords": ["sla", "prazo", "deadline", "atrasada"],
            },
            {
                "id": "performance_departamento",
                "description": "Análise por departamento",
                "keywords": ["departamento", "área", "setor"],
            },
            {
                "id": "comparar_vagas",
                "description": "Comparar vagas entre si",
                "keywords": ["comparar", "compare", "versus"],
            },
            {
                "id": "gargalos_gerais",
                "description": "Gargalos sistêmicos",
                "keywords": ["gargalo", "bottleneck", "problema"],
            },
            {
                "id": "criar_vaga",
                "description": "Criar nova vaga",
                "keywords": ["criar vaga", "nova vaga", "abrir vaga"],
                "ui_action": "start_job_wizard",
            },
            {
                "id": "pausar_vaga",
                "description": "Pausar uma vaga ativa",
                "keywords": ["pausar vaga", "pause"],
            },
            {
                "id": "fechar_vaga",
                "description": "Fechar/encerrar uma vaga",
                "keywords": ["fechar vaga", "encerrar vaga", "close"],
            },
            {
                "id": "duplicar_vaga",
                "description": "Duplicar uma vaga existente",
                "keywords": ["duplicar vaga", "copiar vaga"],
            },
            {
                "id": "reabrir_vaga",
                "description": "Reabrir uma vaga fechada",
                "keywords": ["reabrir vaga", "reopen"],
            },
        ],
        "context": "jobs_management",
    }


def _generate_fallback(message: str, jobs_context: dict[str, Any]) -> str:
    total = jobs_context.get("total", 0)
    active = jobs_context.get("active", 0)
    urgent = jobs_context.get("urgent", 0)
    without = jobs_context.get("withoutCandidates", 0)

    lines = [
        "## 📊 Resumo das Vagas\n",
        f"Você tem **{total} vagas** no sistema:\n",
        f"- ✅ **{active}** ativas",
    ]
    if urgent > 0:
        lines.append(f"- 🔴 **{urgent}** urgentes")
    if without > 0:
        lines.append(f"- ⚠️ **{without}** sem candidatos")
    lines.append(
        "\nPosso ajudar com análises detalhadas, identificar gargalos, "
        "comparar vagas ou verificar SLA. Também posso **pausar**, **fechar**, "
        "**duplicar** ou **reabrir** vagas. O que deseja fazer?"
    )
    return "\n".join(lines)
