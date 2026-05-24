"""
Communication Matrix Model - Database-backed communication configuration.

This model stores the communication matrix entries that define:
- What triggers generate communications
- Who receives the communications
- What channels are used
- Whether approval is required
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import List, Dict, Any, Optional

from lia_config.database import Base


class ModuleType(str, enum.Enum):
    """Module types for communication matrix."""
    CANDIDATE_JOURNEY = "candidate_journey"
    PIPELINE = "pipeline"
    GOALS = "goals"
    BRIEFING = "briefing"
    SYSTEM = "system"
    APPROVALS = "approvals"
    WORKFORCE = "workforce"


class RecipientType(str, enum.Enum):
    """Recipient types for communications."""
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    MANAGER = "manager"
    ADMIN = "admin"
    RH = "rh"
    INTERVIEWER = "interviewer"
    STAKEHOLDERS = "stakeholders"


class ChannelType(str, enum.Enum):
    """Available communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    BELL = "bell"
    TEAMS = "teams"
    CHAT = "chat"
    LOG = "log"


class CommunicationMatrixEntry(Base):
    """
    Communication Matrix Entry - Configuration for each communication trigger.
    
    Stores:
    - company_id: Nullable for platform defaults
    - module: Which module this trigger belongs to
    - trigger_name: Unique identifier for the trigger
    - trigger_description: Human-readable description of when/where this happens
    - recipient_type: Who receives the communication
    - channels: List of channels to use
    - is_automatic: Whether this is sent automatically
    - template_id: Reference to email/message template
    - requires_approval: Whether approval is needed before sending
    - is_active: Whether this communication is enabled
    - display_order: For UI ordering
    """
    __tablename__ = "communication_matrix_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: CommunicationMatrixEntry com company_id NULL = template canonical default
    company_id = Column(String(255), nullable=True, index=True)
    
    module = Column(String(50), nullable=False, index=True)
    trigger_name = Column(String(100), nullable=False, index=True)
    trigger_description = Column(Text, nullable=True)
    
    recipient_type = Column(String(50), nullable=False)
    channels = Column(JSON, default=list)
    
    is_automatic = Column(Boolean, default=True)
    template_id = Column(String(100), nullable=True)
    requires_approval = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_matrix_company_module', 'company_id', 'module'),
        Index('idx_matrix_trigger', 'company_id', 'trigger_name'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CommunicationMatrixEntry {self.module}:{self.trigger_name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "module": self.module,
            "trigger_name": self.trigger_name,
            "trigger_description": self.trigger_description,
            "recipient_type": self.recipient_type,
            "channels": self.channels or [],
            "is_automatic": self.is_automatic,
            "template_id": self.template_id,
            "requires_approval": self.requires_approval,
            "is_active": self.is_active,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


DEFAULT_MATRIX_ENTRIES: List[Dict[str, Any]] = [
    # ========================================
    # CANDIDATE JOURNEY - Sourcing e Primeiro Contato
    # ========================================
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "candidato_sourced",
        "trigger_description": "Busca Avançada → Recrutador clica 'Revelar' ou arrasta para vaga",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "chat"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "match_alto_detectado",
        "trigger_description": "Sistema → LIA detecta match >80% ao processar CV ou sync ATS",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "email", "teams"],
        "is_automatic": True,
        "template_id": "high_match_found",
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "convite_triagem",
        "trigger_description": "Kanban/Card do Candidato → Recrutador clica 'Convidar para Triagem'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email", "whatsapp"],
        "is_automatic": False,
        "template_id": "initial_contact",
        "requires_approval": True,
        "display_order": 3,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "candidato_visualizou_vaga",
        "trigger_description": "Sistema → Tracking quando candidato abre link da vaga",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 4,
    },
    # Triagem (Screening)
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "triagem_iniciada",
        "trigger_description": "Sistema → Candidato clica no link e inicia triagem (WhatsApp/Web)",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 5,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "triagem_abandonada",
        "trigger_description": "Sistema/Cron → Job automático detecta triagens não finalizadas após 24h",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": True,
        "template_id": "screening_reminder",
        "requires_approval": False,
        "display_order": 6,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "triagem_concluida",
        "trigger_description": "Sistema → Candidato finaliza última pergunta da triagem",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "chat", "teams"],
        "is_automatic": True,
        "template_id": "screening_passed",
        "requires_approval": False,
        "display_order": 7,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "triagem_aprovado",
        "trigger_description": "Kanban → Recrutador avalia resultado da triagem e clica 'Aprovar'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": True,
        "template_id": "screening_passed",
        "requires_approval": False,
        "display_order": 8,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "triagem_reprovado",
        "trigger_description": "Kanban → Recrutador clica 'Reprovar' ou arrasta para coluna 'Reprovado'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "screening_failed",
        "requires_approval": True,
        "display_order": 9,
    },
    # Entrevistas
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "entrevista_agendada",
        "trigger_description": "Card do Candidato → Recrutador clica 'Agendar Entrevista' via modal",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email", "whatsapp"],
        "is_automatic": True,
        "template_id": "interview_scheduled",
        "requires_approval": False,
        "display_order": 10,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "lembrete_entrevista_24h",
        "trigger_description": "Sistema/Cron → Job automático verifica entrevistas do próximo dia",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email", "whatsapp"],
        "is_automatic": True,
        "template_id": "interview_reminder",
        "requires_approval": False,
        "display_order": 11,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "lembrete_entrevista_1h",
        "trigger_description": "Sistema/Cron → Job automático verifica entrevistas da próxima hora",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["whatsapp"],
        "is_automatic": True,
        "template_id": "interview_reminder_urgent",
        "requires_approval": False,
        "display_order": 12,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "confirmacao_presenca",
        "trigger_description": "Sistema → Candidato clica 'Confirmar' no email/WhatsApp",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": True,
        "template_id": "interview_confirmation",
        "requires_approval": False,
        "display_order": 13,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "entrevista_nao_confirmada",
        "trigger_description": "Sistema/Cron → Job verifica 6h antes se candidato confirmou",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "teams"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 14,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "candidato_nao_compareceu",
        "trigger_description": "Card do Candidato → Entrevistador marca 'Não compareceu'",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "no_show_alert",
        "requires_approval": False,
        "display_order": 15,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "feedback_pendente_48h",
        "trigger_description": "Sistema/Cron → Job verifica entrevistas sem feedback após 48h",
        "recipient_type": RecipientType.INTERVIEWER.value,
        "channels": ["email", "bell"],
        "is_automatic": True,
        "template_id": "feedback_pending",
        "requires_approval": False,
        "display_order": 16,
    },
    # Oferta e Contratação
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "proposta_gerada",
        "trigger_description": "Card do Candidato → Recrutador clica 'Gerar Proposta'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "offer_letter",
        "requires_approval": True,
        "display_order": 17,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "proposta_aceita",
        "trigger_description": "Sistema → Candidato clica 'Aceitar' ou recrutador registra aceite",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email", "teams"],
        "is_automatic": True,
        "template_id": "offer_accepted",
        "requires_approval": False,
        "display_order": 18,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "proposta_recusada",
        "trigger_description": "Sistema → Candidato clica 'Recusar' ou recrutador registra recusa",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "offer_rejected",
        "requires_approval": False,
        "display_order": 19,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "prazo_proposta_proximo",
        "trigger_description": "Sistema/Cron → Job verifica propostas com deadline em 48h",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["whatsapp"],
        "is_automatic": True,
        "template_id": "offer_deadline_reminder",
        "requires_approval": False,
        "display_order": 20,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "contratacao_efetivada",
        "trigger_description": "Kanban → Recrutador arrasta candidato para coluna 'Contratado'",
        "recipient_type": RecipientType.RH.value,
        "channels": ["email", "teams"],
        "is_automatic": True,
        "template_id": "hiring_completed",
        "requires_approval": False,
        "display_order": 21,
    },
    # Pipeline Transitions (Task #7 — disabled by default, companies enable via Matriz de Comunicação)
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "entrada_candidato",
        "trigger_description": "Kanban → Recrutador move candidato para o Funil (sourcing)",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "is_active": False,
        "template_id": None,
        "requires_approval": True,
        "display_order": 22,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "movimentacao",
        "trigger_description": "Kanban → Recrutador move candidato entre colunas (Long List, Short List, Custom)",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": False,
        "is_active": False,
        "template_id": None,
        "requires_approval": False,
        "display_order": 23,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "avaliacao_enviada",
        "trigger_description": "Kanban → Recrutador move candidato para Teste Técnico ou Teste de Inglês",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "is_active": False,
        "template_id": None,
        "requires_approval": True,
        "display_order": 24,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "verificacao_solicitada",
        "trigger_description": "Kanban → Recrutador move candidato para coluna de Referências/Verificação",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "is_active": False,
        "template_id": None,
        "requires_approval": True,
        "display_order": 25,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "standby",
        "trigger_description": "Kanban → Recrutador move candidato para Stand By (banco de talentos)",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "is_active": False,
        "template_id": None,
        "requires_approval": True,
        "display_order": 26,
    },
    # Rejeição e Encerramento
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "processo_fechado",
        "trigger_description": "Página da Vaga → Recrutador clica 'Fechar Vaga'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "process_closed",
        "requires_approval": True,
        "display_order": 27,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "feedback_rejeicao",
        "trigger_description": "Card do Candidato → Recrutador clica 'Reprovar e Enviar Feedback'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "rejection_feedback",
        "requires_approval": True,
        "display_order": 28,
    },
    {
        "module": ModuleType.CANDIDATE_JOURNEY.value,
        "trigger_name": "candidato_quarentena",
        "trigger_description": "Sistema → Automático após 3ª rejeição ou flag manual",
        "recipient_type": RecipientType.ADMIN.value,
        "channels": ["log"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 29,
    },
    # ========================================
    # PIPELINE - Vagas e Pipeline
    # ========================================
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "nova_vaga_criada",
        "trigger_description": "Wizard de Criação de Vaga → Recrutador finaliza e clica 'Publicar'",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "vaga_pausada",
        "trigger_description": "Página da Vaga → Recrutador clica 'Pausar Vaga'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "job_paused",
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "vaga_reativada",
        "trigger_description": "Página da Vaga → Recrutador clica 'Reativar Vaga'",
        "recipient_type": RecipientType.CANDIDATE.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "job_reactivated",
        "requires_approval": False,
        "display_order": 3,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "sla_em_risco",
        "trigger_description": "Sistema/Cron → Job monitora tempo médio vs SLA (80%)",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "teams"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 4,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "sla_violado",
        "trigger_description": "Sistema/Cron → Job detecta etapa que ultrapassou SLA",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email", "teams"],
        "is_automatic": True,
        "template_id": "sla_violated",
        "requires_approval": False,
        "display_order": 5,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "pipeline_vazio",
        "trigger_description": "Sistema/Cron → Job verifica vagas sem candidatos novos por X dias",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "chat"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 6,
    },
    {
        "module": ModuleType.PIPELINE.value,
        "trigger_name": "candidato_parado",
        "trigger_description": "Sistema/Cron → Job verifica candidatos sem movimentação por X dias",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 7,
    },
    # ========================================
    # GOALS - Metas e Performance
    # ========================================
    {
        "module": ModuleType.GOALS.value,
        "trigger_name": "meta_em_risco",
        "trigger_description": "Sistema/Cron → Job calcula progresso vs meta quando faltam 20% do período",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "email", "teams"],
        "is_automatic": True,
        "template_id": "goal_at_risk",
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.GOALS.value,
        "trigger_name": "meta_atingida",
        "trigger_description": "Sistema → Automático ao registrar ação que completa a meta",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "chat"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.GOALS.value,
        "trigger_name": "meta_nao_atingida",
        "trigger_description": "Sistema/Cron → Job verifica metas ao final do período",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "goal_missed",
        "requires_approval": False,
        "display_order": 3,
    },
    {
        "module": ModuleType.GOALS.value,
        "trigger_name": "resumo_semanal",
        "trigger_description": "Sistema/Cron → Job toda segunda-feira 8h",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "weekly_performance",
        "requires_approval": False,
        "display_order": 4,
    },
    {
        "module": ModuleType.GOALS.value,
        "trigger_name": "ranking_atualizado",
        "trigger_description": "Sistema/Cron → Job diário recalcula ranking",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": False,
        "template_id": None,
        "requires_approval": False,
        "display_order": 5,
    },
    # ========================================
    # BRIEFING - Briefing da LIA
    # ========================================
    {
        "module": ModuleType.BRIEFING.value,
        "trigger_name": "briefing_2x_dia",
        "trigger_description": "Sistema/Cron → Job às 8h e 14h gera briefing personalizado",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["chat", "email"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.BRIEFING.value,
        "trigger_name": "briefing_diario",
        "trigger_description": "Sistema/Cron → Job às 8h com resumo completo do dia",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["chat", "email"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.BRIEFING.value,
        "trigger_name": "briefing_semanal",
        "trigger_description": "Sistema/Cron → Job toda segunda 8h com análise da semana",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": None,
        "requires_approval": False,
        "display_order": 3,
    },
    {
        "module": ModuleType.BRIEFING.value,
        "trigger_name": "briefing_mensal",
        "trigger_description": "Sistema/Cron → Job no 1º dia útil do mês",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": None,
        "requires_approval": False,
        "display_order": 4,
    },
    # ========================================
    # SYSTEM - Sistema e Integrações
    # ========================================
    {
        "module": ModuleType.SYSTEM.value,
        "trigger_name": "sync_ats_falhou",
        "trigger_description": "Sistema/Cron → Job de sync com ATS retorna erro",
        "recipient_type": RecipientType.ADMIN.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "ats_sync_failed",
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.SYSTEM.value,
        "trigger_name": "creditos_pearch_baixos",
        "trigger_description": "Sistema → Ao consumir crédito, verifica se saldo < threshold",
        "recipient_type": RecipientType.ADMIN.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "credits_low",
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.SYSTEM.value,
        "trigger_name": "erro_ia",
        "trigger_description": "Sistema → Chamada à API Claude/Gemini falha ou retorna erro",
        "recipient_type": RecipientType.ADMIN.value,
        "channels": ["bell"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 3,
    },
    {
        "module": ModuleType.SYSTEM.value,
        "trigger_name": "novo_usuario_adicionado",
        "trigger_description": "Admin > Equipe → Admin clica 'Adicionar Usuário'",
        "recipient_type": RecipientType.ADMIN.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "welcome_user",
        "requires_approval": False,
        "display_order": 4,
    },
    {
        "module": ModuleType.SYSTEM.value,
        "trigger_name": "senha_alterada",
        "trigger_description": "Perfil do Usuário → Usuário altera senha",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "password_changed",
        "requires_approval": False,
        "display_order": 5,
    },
    # ========================================
    # APPROVALS - Gestores e Aprovações
    # ========================================
    {
        "module": ModuleType.APPROVALS.value,
        "trigger_name": "aprovacao_pendente",
        "trigger_description": "Sistema → Recrutador submete ação que requer aprovação",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email", "teams"],
        "is_automatic": True,
        "template_id": "approval_pending",
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.APPROVALS.value,
        "trigger_name": "aprovacao_concedida",
        "trigger_description": "Admin > Aprovações → Gestor clica 'Aprovar'",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.APPROVALS.value,
        "trigger_name": "aprovacao_negada",
        "trigger_description": "Admin > Aprovações → Gestor clica 'Rejeitar'",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["bell", "chat"],
        "is_automatic": True,
        "template_id": None,
        "requires_approval": False,
        "display_order": 3,
    },
    {
        "module": ModuleType.APPROVALS.value,
        "trigger_name": "aprovacao_expirada",
        "trigger_description": "Sistema/Cron → Job verifica aprovações pendentes há mais de X dias",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "approval_expired",
        "requires_approval": False,
        "display_order": 4,
    },
    {
        "module": ModuleType.APPROVALS.value,
        "trigger_name": "feedback_solicitado",
        "trigger_description": "Card do Candidato → Recrutador clica 'Solicitar Feedback'",
        "recipient_type": RecipientType.MANAGER.value,
        "channels": ["bell", "email"],
        "is_automatic": True,
        "template_id": "feedback_request",
        "requires_approval": False,
        "display_order": 5,
    },
    # ========================================
    # WORKFORCE - Workforce Planning
    # ========================================
    {
        "module": ModuleType.WORKFORCE.value,
        "trigger_name": "variancia_workforce",
        "trigger_description": "Sistema/Cron → Job mensal compara headcount planejado vs real (>20%)",
        "recipient_type": RecipientType.RH.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "workforce_variance",
        "requires_approval": False,
        "display_order": 1,
    },
    {
        "module": ModuleType.WORKFORCE.value,
        "trigger_name": "vagas_planejadas_proximo_mes",
        "trigger_description": "Sistema/Cron → Job 15 dias antes do mês verifica planejamento",
        "recipient_type": RecipientType.RECRUITER.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "upcoming_hires",
        "requires_approval": False,
        "display_order": 2,
    },
    {
        "module": ModuleType.WORKFORCE.value,
        "trigger_name": "forecast_atualizado",
        "trigger_description": "Workforce Planning → Gestor atualiza previsões",
        "recipient_type": RecipientType.STAKEHOLDERS.value,
        "channels": ["email"],
        "is_automatic": False,
        "template_id": "forecast_update",
        "requires_approval": False,
        "display_order": 3,
    },
]


MODULE_LABELS = {
    ModuleType.CANDIDATE_JOURNEY.value: {
        "label": "Jornada do Candidato",
        "description": "Comunicações relacionadas ao fluxo do candidato: sourcing, triagem, entrevistas, oferta e contratação",
        "icon": "users",
    },
    ModuleType.PIPELINE.value: {
        "label": "Vagas e Pipeline",
        "description": "Comunicações sobre vagas, status do pipeline e SLA",
        "icon": "briefcase",
    },
    ModuleType.GOALS.value: {
        "label": "Metas e Performance",
        "description": "Alertas sobre metas, rankings e performance dos recrutadores",
        "icon": "target",
    },
    ModuleType.BRIEFING.value: {
        "label": "Briefing da LIA",
        "description": "Briefings automáticos da LIA: diários, semanais e mensais",
        "icon": "robot",
    },
    ModuleType.SYSTEM.value: {
        "label": "Sistema e Integrações",
        "description": "Alertas técnicos: erros de sync, créditos baixos, etc",
        "icon": "settings",
    },
    ModuleType.APPROVALS.value: {
        "label": "Aprovações",
        "description": "Fluxo de aprovações: pendentes, concedidas, negadas",
        "icon": "check-circle",
    },
    ModuleType.WORKFORCE.value: {
        "label": "Workforce Planning",
        "description": "Planejamento de headcount e previsões de contratação",
        "icon": "trending-up",
    },
}
