"""Recruitment Campaign Domain - Action definitions."""
from app.domains.base import DomainAction

CAMPAIGN_ACTIONS = [
    DomainAction(action_id="create_campaign", name="Criar Campanha", description="Criar campanha de recrutamento para vaga ou pool", required_params=["name"], optional_params=["job_id", "talent_pool_id", "automation_level"], requires_confirmation=False),
    DomainAction(action_id="get_campaign_progress", name="Progresso da Campanha", description="Ver estágio atual e próximos passos", required_params=["campaign_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="advance_campaign", name="Avançar Campanha", description="Avançar para próximo estágio", required_params=["campaign_id"], optional_params=[], requires_confirmation=True),
    DomainAction(action_id="list_campaigns", name="Listar Campanhas", description="Listar campanhas ativas", required_params=[], optional_params=["job_id", "status"], requires_confirmation=False),
]
