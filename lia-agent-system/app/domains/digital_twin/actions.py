"""Digital Twin Domain - Action definitions."""
from app.domains.base import DomainAction

DIGITAL_TWIN_ACTIONS = [
    DomainAction(action_id="create_twin", name="Criar Digital Twin", description="Cria Digital Twin de um especialista da empresa para replicar seu raciocínio de avaliação de candidatos. Aciona quando empresa quer escalar conhecimento de especialista para avaliações consistentes.", required_params=["twin_name"], optional_params=["sme_user_id", "specialties"], requires_confirmation=False),
    DomainAction(action_id="evaluate_with_twin", name="Avaliar com Twin", description="Avalia candidato usando o raciocínio replicado do Digital Twin do especialista para decisão de fit. Aciona como etapa avançada de avaliação de candidatos finalistas quando Twin está disponível.", required_params=["twin_id", "candidate_id"], optional_params=["job_id"], requires_confirmation=False),
    DomainAction(action_id="list_twins", name="Listar Twins", description="Lista Digital Twins disponíveis na empresa com especialidade e status de treinamento. Aciona quando recruiter quer escolher qual Twin usar ou verificar quais estão prontos.", required_params=[], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="index_twin_audio", name="Treinar Twin com Áudio", description="Treina o Digital Twin indexando gravação de entrevista realizada pelo especialista para aprender seu padrão de avaliação. Aciona durante calibração do Twin com novas entrevistas do especialista.", required_params=["twin_id"], optional_params=[], requires_confirmation=False),
    DomainAction(action_id="deactivate_twin", name="Desativar Twin", description="Desativa Digital Twin liberando quota da empresa. Requer confirmação. Aciona quando especialista saiu da empresa ou Twin não é mais utilizado.", required_params=["twin_id"], optional_params=[], requires_confirmation=True),
]
