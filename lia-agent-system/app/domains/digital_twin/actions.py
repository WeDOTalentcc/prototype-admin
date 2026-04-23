"""Digital Twin Domain - Action definitions."""
from app.domains.base import DomainAction

DIGITAL_TWIN_ACTIONS = [
    DomainAction(action_id="create_twin", name="Criar Digital Twin", description="Criar twin de um especialista", required_params=["twin_name"], optional_params=["sme_user_id", "specialties"], requires_confirmation=False),
    DomainAction(action_id="evaluate_with_twin", name="Avaliar com Twin", description="Avaliar candidato usando raciocínio do twin", required_params=["twin_id", "candidate_id"], optional_params=["job_id"], requires_confirmation=False),
    DomainAction(action_id="list_twins", name="Listar Twins", description="Listar Digital Twins disponíveis", required_params=[], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="index_twin_audio", name="Treinar Twin com Áudio", description="Indexar entrevista gravada com o especialista", required_params=["twin_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="deactivate_twin", name="Desativar Twin", description="Desativar Digital Twin (libera quota)", required_params=["twin_id"], optional_params=[], requires_confirmation=True),
]
