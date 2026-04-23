"""Talent Pool Domain - Action definitions."""
from app.domains.base import DomainAction

TALENT_POOL_ACTIONS = [
    DomainAction(action_id="create_talent_pool", name="Criar Banco de Talentos", description="Criar novo banco de talentos vivo com arquétipo", required_params=["name"], optional_params=["archetype_id", "description"], requires_confirmation=False),
    DomainAction(action_id="list_talent_pools", name="Listar Bancos de Talentos", description="Listar bancos de talentos ativos", required_params=[], optional_params=["status"], requires_confirmation=False),
    DomainAction(action_id="add_to_pool", name="Adicionar ao Pool", description="Adicionar candidatos ao banco de talentos", required_params=["pool_id", "candidate_ids"], optional_params=["origin"], requires_confirmation=False),
    DomainAction(action_id="move_pool_to_job", name="Mover para Vaga", description="Migrar candidatos do pool para uma vaga", required_params=["pool_id", "job_id", "candidate_ids", "target_stage"], optional_params=[], requires_confirmation=True),
    DomainAction(action_id="get_pool_candidates", name="Ver Candidatos do Pool", description="Listar candidatos de um banco de talentos com estágios", required_params=["pool_id"], optional_params=["stage", "limit"], requires_confirmation=False),
    DomainAction(action_id="create_job_from_pool", name="Criar Vaga do Pool", description="Criar vaga a partir de um banco de talentos (herda arquétipo)", required_params=["pool_id"], optional_params=[], requires_confirmation=True),
]
