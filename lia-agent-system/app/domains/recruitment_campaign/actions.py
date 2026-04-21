"""Recruitment Campaign Domain - Action definitions."""
from app.domains.base import DomainAction

CAMPAIGN_ACTIONS = [
    DomainAction(action_id="create_campaign", name="Criar Campanha", description="Cria campanha de recrutamento estruturada para vaga ou pool de talentos com etapas, automações e nível de autonomia configurados. Aciona quando recruiter inicia processo estruturado de atração de candidatos.", required_params=["name"], optional_params=["job_id", "talent_pool_id", "automation_level"], requires_confirmation=False, examples=('cria campanha', 'quero uma campanha')),
    DomainAction(action_id="get_campaign_progress", name="Progresso da Campanha", description="Obtém estágio atual da campanha com métricas de progresso, próximos passos e alertas de desvio. Aciona para acompanhar andamento da campanha ou quando recruiter pede status.", required_params=["campaign_id"], optional_params=[], requires_confirmation=False, examples=('mostra campanha', 'quero ver campanha')),
    DomainAction(action_id="advance_campaign", name="Avançar Campanha", description="Avança campanha para próximo estágio após validação dos critérios de entrada. Requer confirmação. Aciona quando etapa atual está concluída e recruiter confirma avanço para fase seguinte.", required_params=["campaign_id"], optional_params=[], requires_confirmation=True, examples=('avança campanha', 'move campanha adiante')),
    DomainAction(action_id="list_campaigns", name="Listar Campanhas", description="Lista campanhas de recrutamento ativas e recentes com status, vagas vinculadas e métricas resumidas. Aciona quando recruiter quer gerenciar campanhas em andamento.", required_params=[], optional_params=["job_id", "status"], requires_confirmation=False, examples=('lista campanha', 'mostra campanha ativas')),
]
