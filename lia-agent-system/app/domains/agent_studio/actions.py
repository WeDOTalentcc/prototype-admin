"""Agent Studio Domain - Action definitions (expanded with Custom Agents & Marketplace)."""
from app.domains.base import DomainAction

AGENT_STUDIO_ACTIONS = [
    DomainAction(action_id="create_sourcing_agent", name="Criar Agente de Sourcing", description="Criar agente de sourcing com template de setor", required_params=["agent_name"], optional_params=["sector_template", "job_id", "talent_pool_id"], requires_confirmation=False),
    DomainAction(action_id="calibrate_agent", name="Calibrar Agente", description="Iniciar calibração do agente (avaliar perfis)", required_params=["agent_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="get_agent_status", name="Status do Agente", description="Ver status, estratégia e métricas do agente", required_params=["agent_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="list_agents", name="Listar Agentes", description="Listar agentes de sourcing ativos", required_params=[], optional_params=["job_id", "pool_id"], requires_confirmation=False),
    DomainAction(action_id="run_multi_strategy", name="Busca Multi-Estratégia", description="Executar busca inteligente com 4 estratégias paralelas", required_params=["job_title", "skills"], optional_params=["location", "seniority"], requires_confirmation=False),
    DomainAction(action_id="create_custom_agent", name="Criar Agente Custom", description="Criar agente customizado com nome, role, prompt e tools", required_params=["name", "role", "system_prompt"], optional_params=["allowed_tools", "domain", "max_steps", "temperature"], requires_confirmation=False),
    DomainAction(action_id="list_custom_agents", name="Listar Agentes Custom", description="Listar agentes customizados da empresa", required_params=[], optional_params=["status", "domain"], requires_confirmation=False),
    DomainAction(action_id="test_custom_agent", name="Testar Agente Custom", description="Testar agente customizado com uma mensagem", required_params=["agent_id", "message"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="execute_custom_agent", name="Executar Agente Custom", description="Executar agente customizado em produção", required_params=["agent_id", "message"], optional_params=["context"], requires_confirmation=False),
    DomainAction(action_id="publish_to_marketplace", name="Publicar no Marketplace", description="Publicar agente no marketplace para outras empresas", required_params=["agent_id", "title"], optional_params=["short_description", "category", "credits_per_execution"], requires_confirmation=True),
    DomainAction(action_id="browse_marketplace", name="Explorar Marketplace", description="Navegar e buscar agentes disponíveis no marketplace", required_params=[], optional_params=["category", "search"], requires_confirmation=False),
    DomainAction(action_id="install_from_marketplace", name="Instalar do Marketplace", description="Instalar agente do marketplace na empresa", required_params=["listing_id"], optional_params=[], requires_confirmation=True),
    DomainAction(action_id="assign_to_crew", name="Atribuir a Crew", description="Atribuir agente custom como role em uma crew", required_params=["agent_id", "crew_id", "role_name"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="get_studio_consumption", name="Consumo do Studio", description="Ver consumo de tokens e créditos dos agentes do Studio", required_params=[], optional_params=["days"], requires_confirmation=False),
    DomainAction(action_id="deactivate_agent", name="Desativar Agente", description="Desativar agente de sourcing ou custom (libera quota)", required_params=["agent_id"], optional_params=["agent_type"], requires_confirmation=True),
    DomainAction(action_id="uninstall_agent", name="Desinstalar Agente", description="Desinstalar agente do marketplace (libera quota)", required_params=["installation_id"], optional_params=[], requires_confirmation=True),
    DomainAction(action_id="explain_agent_studio", name="Explicar Agent Studio", description="Explica o que e o Agent Studio e como funciona", required_params=[], optional_params=[], requires_confirmation=False),
]
