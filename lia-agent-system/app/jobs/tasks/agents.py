"""Celery tasks: agents (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="agents.wizard.process_async", bind=True, max_retries=2, queue="vagas_normal")
def wizard_process_async_task(self, message: str, context: dict, session_id: str, company_id: str, user_id: str) -> dict:
    """
    Processa mensagem do Wizard em background para operações longas.

    Usado quando a criação/atualização de vaga envolve chamadas externas
    (benchmark salarial, busca de templates, geração de JD com LLM).

    Args:
        message: Mensagem do usuário.
        context: Contexto da sessão (stage, collected_data).
        session_id: ID da sessão WS para devolver resultado.
        company_id: ID da empresa.
        user_id: ID do usuário.

    Returns:
        AgentOutput serializado como dict.
    """
    from lia_agents_core.agent_interface import AgentInput

    span = _celery_span("celery.task_start", "agents.wizard.process_async")
    span.set_attribute("company_id", company_id)
    span.set_attribute("session_id", session_id)

    async def _run() -> dict:
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        agent_input = AgentInput(
            message=message,
            context=context,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
        )
        output = await agent.process(agent_input)
        return output.dict()

    try:
        result = asyncio.run(_run())
        try:
            import asyncio as _asyncio

            from app.api.v1.ws_manager import ws_manager
            loop = _asyncio.new_event_loop()
            loop.run_until_complete(ws_manager.send_to_session(session_id, {
                "type": "message",
                "content": result.get("message", ""),
                "confidence": result.get("confidence", 0.7),
                "source": "celery_task",
            }))
            loop.close()
        except Exception:
            pass
        _finish_celery_success(span, "agents.wizard.process_async")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.wizard.process_async", exc)
        logger.error("agents.wizard.process_async falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.wizard.process_async", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.wizard.process_async", exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(base=TenantAwareTask, name="agents.pipeline.transition_async", bind=True, max_retries=2, queue="vagas_normal")
def pipeline_transition_async_task(self, transition_data: dict, session_id: str, company_id: str, user_id: str) -> dict:
    """
    Processa transição de pipeline em background.

    Usado para transições que envolvem ações automáticas complexas
    (geração de feedback, envio de comunicações, atualização de CRM).

    Args:
        transition_data: Dict com candidate_id, job_id, from_stage, to_stage, action_behavior.
        session_id: ID da sessão WS.
        company_id: ID da empresa.
        user_id: ID do usuário.
    """
    from lia_agents_core.agent_interface import AgentInput

    span = _celery_span("celery.task_start", "agents.pipeline.transition_async")
    span.set_attribute("company_id", company_id)
    span.set_attribute("session_id", session_id)

    async def _run() -> dict:
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message=f"Executar transição de {transition_data.get('from_stage')} para {transition_data.get('to_stage')}",
            context=transition_data,
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
        )
        output = await agent.process(agent_input)
        return output.dict()

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.pipeline.transition_async")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.pipeline.transition_async", exc)
        logger.error("agents.pipeline.transition_async falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.pipeline.transition_async", exc, self.request.retries, self.max_retries, 20)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.pipeline.transition_async", exc)
        raise self.retry(exc=exc, countdown=20)

def _build_agent_input(agent_input_dict: dict):
    """Constrói AgentInput a partir de dict serializado."""
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(**agent_input_dict)

async def _publish_response(session_id: str, reply_to: str, output_dict: dict, domain: str) -> None:
    """Publica resultado do agente na fila de resposta (reply_to)."""
    try:
        from app.shared.messaging.rabbitmq_producer import rabbitmq_producer
        await rabbitmq_producer.publish_agent_response(
            response_data={
                "session_id": session_id,
                "content": output_dict.get("message", ""),
                "confidence": output_dict.get("confidence", 0.7),
                "actions": [a if isinstance(a, dict) else a for a in output_dict.get("actions", [])],
                "navigation": output_dict.get("navigation"),
                "state_updates": output_dict.get("state_updates", {}),
                "domain": domain,
                "error": output_dict.get("error"),
                "done": True,
            },
            reply_to=reply_to,
        )
    except Exception as exc:
        logger.warning("_publish_response failed session=%s: %s", session_id, exc)

@celery_app.task(base=TenantAwareTask, name="agents.wizard.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_wizard_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "wizard", reply_to: str = "") -> dict:
    """Executa WizardReActAgent em background (vaga, templates, JD)."""
    span = _celery_span("celery.task_start", "agents.wizard.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.wizard.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.wizard.execute", exc)
        logger.error("agents.wizard.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.wizard.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.wizard.execute", exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(base=TenantAwareTask, name="agents.pipeline.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_pipeline_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "pipeline", reply_to: str = "") -> dict:
    """Executa PipelineReActAgent em background (pipeline, kanban, triagem)."""
    span = _celery_span("celery.task_start", "agents.pipeline.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.pipeline.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.pipeline.execute", exc)
        logger.error("agents.pipeline.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.pipeline.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.pipeline.execute", exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(base=TenantAwareTask, name="agents.sourcing.execute", bind=True, max_retries=2, queue="sourcing_high")
def execute_sourcing_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "sourcing", reply_to: str = "") -> dict:
    """Executa SourcingReActAgent em background (busca Pearch, 30-120s)."""
    span = _celery_span("celery.task_start", "agents.sourcing.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.sourcing.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.sourcing.execute", exc)
        logger.error("agents.sourcing.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.sourcing.execute", exc, self.request.retries, self.max_retries, 45)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.sourcing.execute", exc)
        raise self.retry(exc=exc, countdown=45)

@celery_app.task(base=TenantAwareTask, name="agents.screening.execute", bind=True, max_retries=2, queue="evaluation_normal")
def execute_screening_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "cv_screening", reply_to: str = "") -> dict:
    """Executa triagem curricular / WSI em background."""
    span = _celery_span("celery.task_start", "agents.screening.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
        agent = PipelineReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.screening.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.screening.execute", exc)
        logger.error("agents.screening.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.screening.execute", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.screening.execute", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(base=TenantAwareTask, name="agents.kanban.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_kanban_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "kanban", reply_to: str = "") -> dict:
    """Executa KanbanReActAgent / TalentReActAgent em background."""
    span = _celery_span("celery.task_start", "agents.kanban.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        agent = KanbanReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.kanban.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.kanban.execute", exc)
        logger.error("agents.kanban.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.kanban.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.kanban.execute", exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(base=TenantAwareTask, name="agents.policy.execute", bind=True, max_retries=2, queue="onboarding_low")
def execute_policy_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "hiring_policy", reply_to: str = "") -> dict:
    """Executa PolicyReActAgent em background (compliance, políticas)."""
    span = _celery_span("celery.task_start", "agents.policy.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        agent = PolicyReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.policy.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.policy.execute", exc)
        logger.error("agents.policy.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.policy.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.policy.execute", exc)
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(base=TenantAwareTask, name="agents.automation.execute", bind=True, max_retries=2, queue="vagas_normal")
def execute_automation_task(self, agent_input_dict: dict, session_id: str, company_id: str, domain: str = "automation", reply_to: str = "") -> dict:
    """Executa AutomationReActAgent em background (decomposição de tarefas)."""
    span = _celery_span("celery.task_start", "agents.automation.execute")
    span.set_attribute("company_id", company_id)
    span.set_attribute("domain", domain)

    async def _run() -> dict:
        from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
        agent = AutomationReActAgent()
        output = await agent.process(_build_agent_input(agent_input_dict))
        result = output.dict()
        await _publish_response(session_id, reply_to, result, domain)
        return result

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agents.automation.execute")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agents.automation.execute", exc)
        logger.error("agents.automation.execute falhou session=%s: %s", session_id, exc)
        _emit_celery_retry("agents.automation.execute", exc, self.request.retries, self.max_retries, 30)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("agents.automation.execute", exc)
        raise self.retry(exc=exc, countdown=30)

