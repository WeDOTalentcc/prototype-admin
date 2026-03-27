"""
Handlers para eventos inter-API da plataforma.

Registra handlers para eventos publicados pelas outras APIs de domínio.
Chamado no startup da aplicação via register_all_handlers().

Padrão de implementação dos handlers:
  - Recebem PlatformEvent com company_id e payload
  - São assíncronos (async def)
  - Falhas são capturadas pelo dispatcher (não propagam)
  - Lógica real fica nos services de domínio (TODO comentados abaixo)
"""
import logging

from app.shared.messaging.platform_events import PlatformEvent, register_event_handler

logger = logging.getLogger(__name__)


async def handle_job_published(event: PlatformEvent) -> None:
    """
    Quando uma vaga é publicada (api-vagas), preparar estrutura de pipeline (api-funil).

    Responsabilidades:
    - Inicializar os estágios do pipeline para a nova vaga
    - Notificar recrutadores responsáveis (Bell + Teams)
    """
    job_id = event.payload.get("job_id")
    company_id = event.company_id
    logger.info(
        "[EventHandler] job.published job_id=%s company=%s",
        job_id,
        company_id,
    )
    # TODO: chamar pipeline_stage_service.initialize_pipeline_for_job(job_id, company_id)
    # TODO: notificar recrutadores via notification_service


async def handle_job_closed(event: PlatformEvent) -> None:
    """
    Quando uma vaga é encerrada (api-vagas), arquivar pipeline correspondente.

    Responsabilidades:
    - Arquivar candidatos em aberto com status "vaga encerrada"
    - Enviar feedback aos candidatos pendentes
    """
    job_id = event.payload.get("job_id")
    company_id = event.company_id
    logger.info(
        "[EventHandler] job.closed job_id=%s company=%s",
        job_id,
        company_id,
    )
    # TODO: chamar pipeline_stage_service.archive_pipeline_for_job(job_id, company_id)
    # TODO: enviar feedback automático aos candidatos pendentes


async def handle_candidate_moved(event: PlatformEvent) -> None:
    """
    Quando um candidato muda de estágio (api-funil), atualizar analytics e notificar.

    Responsabilidades:
    - Atualizar métricas de velocidade do pipeline (pipeline_velocity_service)
    - Disparar automações configuradas para o estágio destino
    """
    candidate_id = event.payload.get("candidate_id")
    from_stage = event.payload.get("from_stage")
    to_stage = event.payload.get("to_stage")
    company_id = event.company_id
    logger.info(
        "[EventHandler] candidate.moved candidate_id=%s %s→%s company=%s",
        candidate_id,
        from_stage,
        to_stage,
        company_id,
    )
    # TODO: pipeline_velocity_service.record_transition(candidate_id, from_stage, to_stage)
    # TODO: automation_service.trigger_stage_automations(candidate_id, to_stage, company_id)


async def handle_company_configured(event: PlatformEvent) -> None:
    """
    Quando empresa completa onboarding (api-onboarding), inicializar pipeline padrão.

    Responsabilidades:
    - Criar pipeline padrão com estágios pré-configurados
    - Configurar templates de comunicação padrão
    - Ativar dashboards e relatórios iniciais
    """
    company_id = event.company_id
    logger.info("[EventHandler] company.configured company=%s", company_id)
    # TODO: chamar pipeline_stage_service.initialize_default_pipeline(company_id)
    # TODO: communication_template_service.create_default_templates(company_id)


def register_all_handlers() -> None:
    """
    Registra todos os event handlers para eventos inter-API.

    Chamado no startup da aplicação (app/main.py lifespan).
    Idempotente: se chamado múltiplas vezes, duplica os handlers —
    use apenas no startup.
    """
    register_event_handler("vagas.job.published", handle_job_published)
    register_event_handler("vagas.job.closed", handle_job_closed)
    register_event_handler("funil.candidate.moved", handle_candidate_moved)
    register_event_handler("onboarding.company.configured", handle_company_configured)
    logger.info(
        "[PlatformEvents] All event handlers registered: %s",
        ["vagas.job.published", "vagas.job.closed", "funil.candidate.moved", "onboarding.company.configured"],
    )
