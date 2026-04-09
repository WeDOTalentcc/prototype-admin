"""Agent Studio Domain - Action definitions."""
from app.domains.base import DomainAction

AGENT_STUDIO_ACTIONS = [
    DomainAction(action_id="create_sourcing_agent", name="Criar Agente de Sourcing", description="Criar agente de sourcing com template de setor", required_params=["agent_name"], optional_params=["sector_template", "job_id", "talent_pool_id"], requires_confirmation=False),
    DomainAction(action_id="calibrate_agent", name="Calibrar Agente", description="Iniciar calibração do agente (avaliar perfis)", required_params=["agent_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="get_agent_status", name="Status do Agente", description="Ver status, estratégia e métricas do agente", required_params=["agent_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="list_agents", name="Listar Agentes", description="Listar agentes de sourcing ativos", required_params=[], optional_params=["job_id", "pool_id"], requires_confirmation=False),
    DomainAction(action_id="recalibrate_agent", name="Recalibrar Agente", description="Recalibrar agente com novo feedback", required_params=["agent_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="pause_agent", name="Pausar Agente", description="Pausar agente de sourcing", required_params=["agent_id"], optional_params=[], requires_confirmation=True),
    DomainAction(action_id="list_sector_templates", name="Ver Templates", description="Listar templates de setor disponíveis", required_params=[], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="run_multi_strategy", name="Busca Multi-Estratégia", description="Executar busca inteligente com 4 estratégias paralelas", required_params=["job_title", "skills"], optional_params=["location", "seniority"], requires_confirmation=False),
]
