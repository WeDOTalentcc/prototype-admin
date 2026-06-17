"""
Recruitment Stages & Pipeline Management Models.

This module defines the configurable recruitment pipeline:
- RecruitmentStage: Company-specific pipeline stages (Admin > Jornada de Recrutamento)
- RecruitmentSubStatus: Sub-statuses within each stage for granular tracking
- ATSStageMapping: N:1 and 1:N mappings between ATS stages and WedoTalent stages
- CandidateStageHistory: Audit trail for all stage transitions

Design Principles:
1. Stages are company-scoped and configurable
2. Sub-statuses provide granularity without changing the main pipeline
3. ATS mapping supports complex relationships (many ATS stages → one Wedo stage)
4. Every transition is logged for auditing and analytics
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class RecruitmentStage(Base):
    """
    Configurable recruitment pipeline stages per company.
    
    Managed in Admin > Jornada de Recrutamento.
    These are the canonical WedoTalent stages that define the pipeline columns in Kanban.
    
    Example stages:
    - Sourcing (Prospecção)
    - Screening (Triagem)
    - Interview HR (Entrevista RH)
    - Interview Technical (Entrevista Técnica)
    - Interview Manager (Entrevista Gestor)
    - Offer (Proposta)
    - Hired (Contratado)
    - Rejected (Reprovado)
    """
    __tablename__ = "recruitment_stages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    stage_order = Column(Integer, nullable=False, default=0)
    
    color = Column(String(20), nullable=True)
    icon = Column(String(50), nullable=True)
    
    stage_type = Column(String(50), nullable=False, default="active")
    
    is_initial = Column(Boolean, default=False)
    is_final = Column(Boolean, default=False)
    is_rejection = Column(Boolean, default=False)
    is_hired = Column(Boolean, default=False)
    
    # DEPRECATED: Use action_behavior instead. Kept for backward compatibility.
    allowed_transitions = Column(JSON, default=lambda: [])
    
    auto_advance_rules = Column(JSON, nullable=True)
    sla_hours = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    stage_category = Column(String(20), nullable=False, default="custom")
    action_behavior = Column(String(30), nullable=False, default="passive")
    default_channel = Column(String(30), nullable=False, default="email")
    
    stage_metadata = Column(JSON, default=lambda: {})
    data_fields = Column(JSON, default=lambda: [])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'name', name='uq_company_stage_name'),
        Index('ix_recruitment_stages_company_order', 'company_id', 'stage_order'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "stage_order": self.stage_order,
            "color": self.color,
            "icon": self.icon,
            "stage_type": self.stage_type,
            "is_initial": self.is_initial,
            "is_final": self.is_final,
            "is_rejection": self.is_rejection,
            "is_hired": self.is_hired,
            "allowed_transitions": self.allowed_transitions,
            "sla_hours": self.sla_hours,
            "is_active": self.is_active,
            "stage_category": self.stage_category,
            "action_behavior": self.action_behavior,
            "default_channel": self.default_channel,
            "data_fields": self.data_fields or [],
        }
    
    def __repr__(self):
        return f"<RecruitmentStage {self.name} (order={self.stage_order})>"


class RecruitmentSubStatus(Base):
    """
    Sub-statuses within a recruitment stage.
    
    Provides granular tracking without changing the main pipeline stage.
    
    Example for stage "Triagem":
    - contacted_whatsapp: "Contato feito via WhatsApp"
    - awaiting_response: "Aguardando retorno do candidato"
    - scheduled_screening: "Triagem agendada"
    - screening_completed: "Triagem realizada"
    - documents_pending: "Documentos pendentes"
    
    UI Display: "Triagem > Aguardando retorno do candidato"
    """
    __tablename__ = "recruitment_sub_statuses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_stages.id"), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    
    sub_status_order = Column(Integer, nullable=False, default=0)
    
    color = Column(String(20), nullable=True)
    icon = Column(String(50), nullable=True)
    
    is_default = Column(Boolean, default=False)
    
    is_waiting = Column(Boolean, default=False)
    waiting_for = Column(String(100), nullable=True)
    
    sla_hours = Column(Integer, nullable=True)
    
    auto_actions = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    sub_status_metadata = Column(JSON, default=lambda: {})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('stage_id', 'name', name='uq_stage_substatus_name'),
        Index('ix_sub_status_stage_order', 'stage_id', 'sub_status_order'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "stage_id": str(self.stage_id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "sub_status_order": self.sub_status_order,
            "color": self.color,
            "icon": self.icon,
            "is_default": self.is_default,
            "is_waiting": self.is_waiting,
            "waiting_for": self.waiting_for,
            "sla_hours": self.sla_hours,
            "is_active": self.is_active,
        }
    
    def __repr__(self):
        return f"<RecruitmentSubStatus {self.name} (stage={self.stage_id})>"


class ATSStageMapping(Base):
    """
    Mapping between client ATS stages and WedoTalent stages.
    
    Supports:
    - N:1 mapping: Multiple ATS stages → One WedoTalent stage
    - 1:N mapping: One WedoTalent stage → Multiple ATS stages (for sync direction)
    
    Example mappings (Gupy → WedoTalent):
    - "Inscrito" → "sourcing"
    - "Triagem CV" → "screening"
    - "Pré-Entrevista" → "screening"
    - "Entrevista RH" → "interview_hr"
    - "Entrevista Técnica" → "interview_technical"
    - "Entrevista Gestor" → "interview_technical" (same WedoTalent stage)
    - "Teste Técnico" → "interview_technical"
    - "Proposta" → "offer"
    - "Contratado" → "hired"
    - "Reprovado" → "rejected"
    
    Example mappings (WedoTalent → Gupy for sync):
    - "interview_technical" → "Entrevista Gestor" (default for sync)
    """
    __tablename__ = "ats_stage_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    ats_type = Column(String(50), nullable=False, index=True)
    
    ats_stage_id = Column(String(255), nullable=True)
    ats_stage_name = Column(String(255), nullable=False)
    ats_stage_order = Column(Integer, nullable=True)
    
    wedotalent_stage_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_stages.id"), nullable=False, index=True)
    wedotalent_sub_status_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_sub_statuses.id"), nullable=True)
    
    mapping_direction = Column(String(20), nullable=False, default="both")
    
    is_default_for_sync = Column(Boolean, default=False)
    
    ats_stage_group_id = Column(String(255), nullable=True)
    
    priority = Column(Integer, default=0)
    
    transformation_rules = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'ats_type', 'ats_stage_name', name='uq_company_ats_stage'),
        Index('ix_ats_mapping_company_ats', 'company_id', 'ats_type'),
        Index('ix_ats_mapping_wedotalent_stage', 'wedotalent_stage_id'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "ats_type": self.ats_type,
            "ats_stage_id": self.ats_stage_id,
            "ats_stage_name": self.ats_stage_name,
            "wedotalent_stage_id": str(self.wedotalent_stage_id),
            "wedotalent_sub_status_id": str(self.wedotalent_sub_status_id) if self.wedotalent_sub_status_id else None,
            "mapping_direction": self.mapping_direction,
            "is_default_for_sync": self.is_default_for_sync,
            "is_active": self.is_active,
        }
    
    def __repr__(self):
        return f"<ATSStageMapping {self.ats_type}:{self.ats_stage_name} → {self.wedotalent_stage_id}>"


class ScreeningQuestion(Base):
    """
    Screening questions for the recruitment process.
    
    These questions are sent to candidates during the screening phase
    and can be customized per company.
    """
    __tablename__ = "screening_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    question = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="text")
    is_required = Column(Boolean, default=True)
    order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, default=False)
    options = Column(JSON, default=lambda: [])
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_screening_questions_company_order', 'company_id', 'order'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "question": self.question,
            "question_type": self.question_type,
            "is_required": self.is_required,
            "order": self.order,
            "is_default": self.is_default,
            "options": self.options or [],
        }
    
    def __repr__(self):
        return f"<ScreeningQuestion {self.question[:30]}...>"


class CandidateStageHistory(Base):
    """
    Audit trail for all candidate stage transitions.
    
    Records every movement between stages and sub-statuses:
    - Who triggered the change (agent, user, ATS sync)
    - When it happened
    - Previous and new stage/sub-status
    - ATS sync result
    - Additional context (interview feedback, rejection reason, etc.)
    
    Used for:
    - Compliance auditing
    - Analytics (time-in-stage, bottleneck analysis)
    - Debugging sync issues
    - SLA monitoring
    """
    __tablename__ = "candidate_stage_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    vacancy_candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    from_stage_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_stages.id"), nullable=True)
    from_stage_name = Column(String(100), nullable=True)
    from_sub_status_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_sub_statuses.id"), nullable=True)
    from_sub_status_name = Column(String(100), nullable=True)
    
    to_stage_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_stages.id"), nullable=False)
    to_stage_name = Column(String(100), nullable=False)
    to_sub_status_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_sub_statuses.id"), nullable=True)
    to_sub_status_name = Column(String(100), nullable=True)
    
    transition_type = Column(String(50), nullable=False, default="manual")
    
    triggered_by = Column(String(100), nullable=False)
    triggered_by_user_id = Column(String(255), nullable=True)
    source_agent = Column(String(100), nullable=True)
    
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    ats_sync_triggered = Column(Boolean, default=False)
    ats_sync_result = Column(String(50), nullable=True)
    ats_sync_details = Column(JSON, nullable=True)
    
    time_in_previous_stage_hours = Column(Float, nullable=True)
    
    context = Column(JSON, default=lambda: {})
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_stage_history_vacancy_candidate', 'vacancy_candidate_id', 'created_at'),
        Index('ix_stage_history_vacancy', 'vacancy_id', 'created_at'),
        Index('ix_stage_history_candidate', 'candidate_id', 'created_at'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "vacancy_candidate_id": str(self.vacancy_candidate_id),
            "vacancy_id": str(self.vacancy_id),
            "candidate_id": str(self.candidate_id),
            "from_stage": {
                "id": str(self.from_stage_id) if self.from_stage_id else None,
                "name": self.from_stage_name,
                "sub_status_id": str(self.from_sub_status_id) if self.from_sub_status_id else None,
                "sub_status_name": self.from_sub_status_name,
            },
            "to_stage": {
                "id": str(self.to_stage_id),
                "name": self.to_stage_name,
                "sub_status_id": str(self.to_sub_status_id) if self.to_sub_status_id else None,
                "sub_status_name": self.to_sub_status_name,
            },
            "transition_type": self.transition_type,
            "triggered_by": self.triggered_by,
            "source_agent": self.source_agent,
            "reason": self.reason,
            "ats_sync_result": self.ats_sync_result,
            "time_in_previous_stage_hours": self.time_in_previous_stage_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<CandidateStageHistory {self.from_stage_name} → {self.to_stage_name}>"


DEFAULT_RECRUITMENT_STAGES = [
    {
        "name": "sourcing",
        "display_name": "Funil",
        "stage_order": 1,
        "color": "#6366F1",
        "icon": "search",
        "stage_type": "active",
        "is_initial": True,
        "is_final": False,
        "is_system": True,
        "stage_category": "system",
        "action_behavior": "intake",
        "allowed_transitions": ["screening", "rejected"],
    },
    {
        "name": "screening",
        "display_name": "Triagem",
        "stage_order": 2,
        "color": "#8B5CF6",
        "icon": "file-text",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "is_system": True,
        "stage_category": "system",
        "action_behavior": "screening",
        "allowed_transitions": ["long_list", "short_list", "interview_hr", "interview_technical", "rejected"],
    },
    {
        "name": "long_list",
        "display_name": "Long List",
        "stage_order": 3,
        "color": "#C5D9ED",
        "icon": "list",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "passive",
        "allowed_transitions": ["short_list", "interview_hr", "rejected"],
    },
    {
        "name": "short_list",
        "display_name": "Short List",
        "stage_order": 4,
        "color": "#B8C5D0",
        "icon": "list-checks",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "passive",
        "allowed_transitions": ["interview_hr", "interview_technical", "rejected"],
    },
    {
        "name": "interview_hr",
        "display_name": "Entrevista RH",
        "stage_order": 5,
        "color": "#EC4899",
        "icon": "users",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "is_system": True,
        "stage_category": "system",
        "action_behavior": "scheduling",
        "allowed_transitions": ["technical_test", "english_test", "interview_technical", "interview_manager", "rejected"],
    },
    {
        "name": "technical_test",
        "display_name": "Teste Técnico",
        "stage_order": 6,
        "color": "#E8B8B8",
        "icon": "code-2",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "evaluation",
        "allowed_transitions": ["english_test", "interview_technical", "interview_manager", "rejected"],
    },
    {
        "name": "english_test",
        "display_name": "Teste de Inglês",
        "stage_order": 7,
        "color": "#E5C5C5",
        "icon": "languages",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "evaluation",
        "allowed_transitions": ["interview_technical", "interview_manager", "rejected"],
    },
    {
        "name": "interview_technical",
        "display_name": "Entrevista Técnica",
        "stage_order": 8,
        "color": "#F59E0B",
        "icon": "code",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "scheduling",
        "allowed_transitions": ["interview_manager", "interview_final", "offer", "rejected"],
    },
    {
        "name": "interview_manager",
        "display_name": "Entrevista Gestor",
        "stage_order": 9,
        "color": "#10B981",
        "icon": "briefcase",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "scheduling",
        "allowed_transitions": ["interview_final", "offer", "rejected"],
    },
    {
        "name": "interview_final",
        "display_name": "Entrevista Final",
        "stage_order": 10,
        "color": "#D5BFA8",
        "icon": "award",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "scheduling",
        "allowed_transitions": ["references", "offer", "rejected"],
    },
    {
        "name": "references",
        "display_name": "Referências",
        "stage_order": 11,
        "color": "#E8E4E0",
        "icon": "phone",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "custom",
        "action_behavior": "verification",
        "allowed_transitions": ["offer", "rejected"],
    },
    {
        "name": "offer",
        "display_name": "Proposta",
        "stage_order": 12,
        "color": "#3B82F6",
        "icon": "file-check",
        "stage_type": "active",
        "is_initial": False,
        "is_final": False,
        "stage_category": "default",
        "action_behavior": "offer",
        "allowed_transitions": ["hired", "rejected", "offer_declined"],
    },
    {
        "name": "offer_declined",
        "display_name": "Proposta Recusada",
        "stage_order": 13,
        "color": "#F97316",
        "icon": "x",
        "stage_type": "final",
        "is_initial": False,
        "is_final": True,
        "stage_category": "default",
        "action_behavior": "conclusion_declined",
        "allowed_transitions": [],
    },
    {
        "name": "hired",
        "display_name": "Contratado",
        "stage_order": 14,
        "color": "#22C55E",
        "icon": "check-circle",
        "stage_type": "final",
        "is_initial": False,
        "is_final": True,
        "is_hired": True,
        "is_system": True,
        "stage_category": "system",
        "action_behavior": "conclusion_hired",
        "allowed_transitions": [],
    },
    {
        "name": "rejected",
        "display_name": "Reprovado",
        "stage_order": 15,
        "color": "#EF4444",
        "icon": "x-circle",
        "stage_type": "final",
        "is_initial": False,
        "is_final": True,
        "is_rejection": True,
        "is_system": True,
        "stage_category": "system",
        "action_behavior": "conclusion_rejected",
        "allowed_transitions": [],
    },
]


# Canonical sub-status catalog — single source of truth for all stages.
# Mirrors SUB_STATUSES in plataforma-lia/src/lib/recruitment-stages.ts
# Used to seed new companies and as reference for existing ones.
CANONICAL_SUB_STATUSES: dict = {
    "sourcing": [
        {"name": "identified",              "display_name": "Identificado",                  "is_default": True},
        {"name": "researching",             "display_name": "Pesquisando Perfil"},
        {"name": "qualified_to_contact",    "display_name": "Qualificado para Contato"},
        {"name": "contacted_linkedin",      "display_name": "Contatado via LinkedIn"},
        {"name": "contacted_email",         "display_name": "Contatado via Email"},
        {"name": "contacted_whatsapp",      "display_name": "Contatado via WhatsApp"},
        {"name": "contacted_phone",         "display_name": "Contatado via Telefone"},
        {"name": "awaiting_response",       "display_name": "Aguardando Retorno",            "is_waiting": True, "waiting_for": "candidate"},
        {"name": "follow_up_sent",          "display_name": "Follow-up Enviado"},
        {"name": "interested",              "display_name": "Interessado"},
        {"name": "not_interested",          "display_name": "Não Interessado"},
        {"name": "no_response",             "display_name": "Sem Resposta"},
        {"name": "incomplete_data",         "display_name": "Dados Incompletos"},
        {"name": "ready_for_screening",     "display_name": "Pronto para Triagem"},
    ],
    "screening": [
        {"name": "cv_received",                   "display_name": "CV Recebido",                    "is_default": True},
        {"name": "cv_analyzing",                  "display_name": "CV em Análise"},
        {"name": "cv_approved",                   "display_name": "CV Aprovado"},
        {"name": "cv_rejected",                   "display_name": "CV Reprovado"},
        {"name": "awaiting_screening_schedule",   "display_name": "Aguardando Agenda Triagem",      "is_waiting": True, "waiting_for": "candidate"},
        {"name": "screening_scheduled",           "display_name": "Triagem Agendada"},
        {"name": "screening_in_progress",         "display_name": "Triagem em Andamento"},
        {"name": "screening_completed",           "display_name": "Triagem Concluída"},
        {"name": "screening_approved",            "display_name": "Aprovado em Triagem"},
        {"name": "screening_rejected",            "display_name": "Reprovado em Triagem"},
        {"name": "awaiting_documents",            "display_name": "Aguardando Documentos",          "is_waiting": True, "waiting_for": "candidate"},
        {"name": "documents_received",            "display_name": "Documentos Recebidos"},
        {"name": "initial_test_sent",             "display_name": "Teste Inicial Enviado"},
        {"name": "initial_test_received",         "display_name": "Teste Inicial Recebido"},
        {"name": "initial_test_approved",         "display_name": "Teste Inicial Aprovado"},
        {"name": "initial_test_rejected",         "display_name": "Teste Inicial Reprovado"},
    ],
    "long_list": [
        {"name": "added_to_long_list",            "display_name": "Adicionado à Long List",         "is_default": True},
        {"name": "removed_from_long_list",        "display_name": "Removido da Long List"},
        {"name": "awaiting_presentation",         "display_name": "Aguardando Apresentação",        "is_waiting": True, "waiting_for": "hr"},
        {"name": "presented_to_manager",          "display_name": "Apresentado ao Gestor"},
        {"name": "awaiting_manager_evaluation",   "display_name": "Aguardando Avaliação do Gestor", "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager_approved",              "display_name": "Aprovado pelo Gestor"},
        {"name": "manager_rejected",              "display_name": "Reprovado pelo Gestor"},
        {"name": "manager_feedback_received",     "display_name": "Feedback do Gestor Recebido"},
    ],
    "short_list": [
        {"name": "added_to_short_list",           "display_name": "Adicionado à Short List",        "is_default": True},
        {"name": "removed_from_short_list",       "display_name": "Removido da Short List"},
        {"name": "awaiting_presentation",         "display_name": "Aguardando Apresentação",        "is_waiting": True, "waiting_for": "hr"},
        {"name": "presented_to_manager",          "display_name": "Apresentado ao Gestor"},
        {"name": "awaiting_manager_evaluation",   "display_name": "Aguardando Avaliação do Gestor", "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager_approved",              "display_name": "Aprovado pelo Gestor"},
        {"name": "manager_rejected",              "display_name": "Reprovado pelo Gestor"},
    ],
    "interview_hr": [
        {"name": "awaiting_hr_schedule",          "display_name": "Aguardando Agenda RH",           "is_waiting": True, "waiting_for": "hr"},
        {"name": "hr_interview_scheduled",        "display_name": "Entrevista RH Agendada",         "is_default": True},
        {"name": "hr_interview_confirmed",        "display_name": "Entrevista RH Confirmada"},
        {"name": "hr_interview_rescheduled",      "display_name": "Entrevista RH Reagendada"},
        {"name": "hr_interview_in_progress",      "display_name": "Entrevista RH em Andamento"},
        {"name": "hr_interview_completed",        "display_name": "Entrevista RH Realizada"},
        {"name": "hr_interview_no_show",          "display_name": "Não Compareceu RH"},
        {"name": "awaiting_hr_feedback",          "display_name": "Aguardando Parecer RH",          "is_waiting": True, "waiting_for": "interviewer"},
        {"name": "hr_feedback_submitted",         "display_name": "Parecer RH Enviado"},
        {"name": "hr_interview_approved",         "display_name": "Aprovado em Entrevista RH"},
        {"name": "hr_interview_rejected",         "display_name": "Reprovado em Entrevista RH"},
    ],
    "technical_test": [
        {"name": "test_pending",                  "display_name": "Teste Pendente",                 "is_default": True},
        {"name": "test_link_sent",                "display_name": "Link do Teste Enviado"},
        {"name": "test_in_progress",              "display_name": "Teste em Andamento"},
        {"name": "test_submitted",                "display_name": "Teste Submetido"},
        {"name": "awaiting_evaluation",           "display_name": "Aguardando Avaliação",           "is_waiting": True, "waiting_for": "hr"},
        {"name": "test_evaluating",               "display_name": "Teste em Avaliação"},
        {"name": "test_approved",                 "display_name": "Aprovado no Teste"},
        {"name": "test_conditional",              "display_name": "Aprovado com Ressalvas"},
        {"name": "test_rejected",                 "display_name": "Reprovado no Teste"},
        {"name": "test_expired",                  "display_name": "Teste Expirado"},
        {"name": "test_no_show",                  "display_name": "Não Realizou o Teste"},
    ],
    "english_test": [
        {"name": "english_test_pending",          "display_name": "Teste de Inglês Pendente",       "is_default": True},
        {"name": "english_test_link_sent",        "display_name": "Link do Teste Enviado"},
        {"name": "english_test_in_progress",      "display_name": "Teste em Andamento"},
        {"name": "english_test_submitted",        "display_name": "Teste Submetido"},
        {"name": "awaiting_english_evaluation",   "display_name": "Aguardando Avaliação",           "is_waiting": True, "waiting_for": "hr"},
        {"name": "english_level_advanced",        "display_name": "Nível Avançado"},
        {"name": "english_level_intermediate",    "display_name": "Nível Intermediário"},
        {"name": "english_level_basic",           "display_name": "Nível Básico"},
        {"name": "english_test_approved",         "display_name": "Aprovado no Teste"},
        {"name": "english_test_rejected",         "display_name": "Reprovado no Teste"},
        {"name": "english_test_expired",          "display_name": "Teste Expirado"},
    ],
    "interview_technical": [
        {"name": "awaiting_technical_schedule",   "display_name": "Aguardando Agenda Técnica",      "is_waiting": True, "waiting_for": "hr"},
        {"name": "technical_interview_scheduled", "display_name": "Entrevista Técnica Agendada",    "is_default": True},
        {"name": "technical_interview_confirmed", "display_name": "Entrevista Técnica Confirmada"},
        {"name": "technical_interview_completed", "display_name": "Entrevista Técnica Realizada"},
        {"name": "technical_test_sent",           "display_name": "Teste Técnico Enviado"},
        {"name": "technical_test_in_progress",    "display_name": "Teste Técnico em Andamento"},
        {"name": "technical_test_received",       "display_name": "Teste Técnico Recebido"},
        {"name": "technical_test_evaluating",     "display_name": "Teste Técnico em Avaliação"},
        {"name": "awaiting_technical_feedback",   "display_name": "Aguardando Parecer Técnico",     "is_waiting": True, "waiting_for": "interviewer"},
        {"name": "technical_feedback_submitted",  "display_name": "Parecer Técnico Enviado"},
        {"name": "technical_approved",            "display_name": "Aprovado em Técnica"},
        {"name": "technical_rejected",            "display_name": "Reprovado em Técnica"},
    ],
    "interview_manager": [
        {"name": "awaiting_manager1_schedule",    "display_name": "Aguardando Agenda Gestor",       "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager1_interview_scheduled",  "display_name": "Entrevista Gestor Agendada",     "is_default": True},
        {"name": "manager1_interview_confirmed",  "display_name": "Entrevista Gestor Confirmada"},
        {"name": "manager1_interview_rescheduled","display_name": "Entrevista Gestor Reagendada"},
        {"name": "manager1_interview_in_progress","display_name": "Entrevista Gestor em Andamento"},
        {"name": "manager1_interview_completed",  "display_name": "Entrevista Gestor Realizada"},
        {"name": "manager1_interview_no_show",    "display_name": "Não Compareceu Gestor"},
        {"name": "awaiting_manager1_feedback",    "display_name": "Aguardando Parecer Gestor",      "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager1_feedback_submitted",   "display_name": "Parecer Gestor Enviado"},
        {"name": "manager1_interview_approved",   "display_name": "Aprovado por Gestor"},
        {"name": "manager1_interview_rejected",   "display_name": "Reprovado por Gestor"},
    ],
    "interview_manager2": [
        {"name": "awaiting_manager2_schedule",    "display_name": "Aguardando Agenda Gestor 2",     "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager2_interview_scheduled",  "display_name": "Entrevista Gestor 2 Agendada",   "is_default": True},
        {"name": "manager2_interview_confirmed",  "display_name": "Entrevista Gestor 2 Confirmada"},
        {"name": "manager2_interview_completed",  "display_name": "Entrevista Gestor 2 Realizada"},
        {"name": "awaiting_manager2_feedback",    "display_name": "Aguardando Parecer Gestor 2",    "is_waiting": True, "waiting_for": "manager"},
        {"name": "manager2_interview_approved",   "display_name": "Aprovado por Gestor 2"},
        {"name": "manager2_interview_rejected",   "display_name": "Reprovado por Gestor 2"},
    ],
    "interview_final": [
        {"name": "awaiting_final_schedule",       "display_name": "Aguardando Agenda Final",        "is_waiting": True, "waiting_for": "hr"},
        {"name": "final_interview_scheduled",     "display_name": "Entrevista Final Agendada",      "is_default": True},
        {"name": "final_interview_confirmed",     "display_name": "Entrevista Final Confirmada"},
        {"name": "final_interview_completed",     "display_name": "Entrevista Final Realizada"},
        {"name": "awaiting_final_feedback",       "display_name": "Aguardando Parecer Final",       "is_waiting": True, "waiting_for": "manager"},
        {"name": "final_interview_approved",      "display_name": "Aprovado em Entrevista Final"},
        {"name": "final_interview_rejected",      "display_name": "Reprovado em Entrevista Final"},
    ],
    "references": [
        {"name": "references_requested",          "display_name": "Referências Solicitadas",        "is_default": True},
        {"name": "awaiting_references",           "display_name": "Aguardando Referências",         "is_waiting": True, "waiting_for": "candidate"},
        {"name": "references_received",           "display_name": "Referências Recebidas"},
        {"name": "references_approved",           "display_name": "Referências Aprovadas"},
        {"name": "references_concerns",           "display_name": "Referências com Ressalvas"},
        {"name": "references_negative",           "display_name": "Referências Negativas"},
        {"name": "background_check_started",      "display_name": "Background Check Iniciado"},
        {"name": "background_check_approved",     "display_name": "Background Check Aprovado"},
        {"name": "background_check_rejected",     "display_name": "Background Check Reprovado"},
    ],
    "offer": [
        {"name": "awaiting_internal_approval",    "display_name": "Aguardando Aprovação Interna",   "is_waiting": True, "waiting_for": "manager"},
        {"name": "offer_internally_approved",     "display_name": "Proposta Aprovada Internamente"},
        {"name": "preparing_offer",               "display_name": "Preparando Proposta",            "is_default": True},
        {"name": "offer_sent",                    "display_name": "Proposta Enviada"},
        {"name": "offer_viewed",                  "display_name": "Proposta Visualizada"},
        {"name": "negotiating",                   "display_name": "Em Negociação"},
        {"name": "counter_offer_sent",            "display_name": "Contraproposta Enviada"},
        {"name": "awaiting_offer_response",       "display_name": "Aguardando Resposta",            "is_waiting": True, "waiting_for": "candidate"},
        {"name": "offer_accepted",                "display_name": "Proposta Aceita"},
        {"name": "offer_expired",                 "display_name": "Proposta Expirada"},
    ],
    "hired": [
        {"name": "awaiting_admission_docs",       "display_name": "Aguardando Documentos Admissionais", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "admission_docs_received",       "display_name": "Documentos Admissionais Recebidos"},
        {"name": "admission_exam_scheduled",      "display_name": "Exame Admissional Agendado"},
        {"name": "admission_exam_completed",      "display_name": "Exame Admissional Realizado"},
        {"name": "admission_exam_approved",       "display_name": "Exame Admissional Aprovado"},
        {"name": "admission_exam_failed",         "display_name": "Exame Admissional Inapto"},
        {"name": "contract_preparing",            "display_name": "Contrato em Elaboração"},
        {"name": "contract_sent",                 "display_name": "Contrato Enviado"},
        {"name": "contract_signed",               "display_name": "Contrato Assinado"},
        {"name": "onboarding_scheduled",          "display_name": "Onboarding Agendado"},
        {"name": "onboarding_in_progress",        "display_name": "Onboarding em Andamento"},
        {"name": "onboarding_completed",          "display_name": "Onboarding Concluído"},
        {"name": "started_work",                  "display_name": "Iniciou Trabalho"},
    ],
    "offer_declined": [
        {"name": "accepted_other_offer",          "display_name": "Aceitou Proposta de Outra Empresa",       "is_default": True},
        {"name": "salary_below_expectation",      "display_name": "Salário Abaixo do Esperado"},
        {"name": "insufficient_benefits",         "display_name": "Benefícios Insuficientes"},
        {"name": "work_model_not_accepted",       "display_name": "Modelo de Trabalho Não Aceito"},
        {"name": "location_not_accepted",         "display_name": "Localização Não Aceita"},
        {"name": "accepted_counter_offer",        "display_name": "Aceitou Contraproposta do Empregador Atual"},
        {"name": "personal_family_reasons",       "display_name": "Motivos Pessoais/Familiares"},
        {"name": "culture_not_aligned",           "display_name": "Não se Identificou com a Cultura"},
        {"name": "better_career_opportunity",     "display_name": "Melhor Oportunidade de Carreira"},
        {"name": "company_response_timing",       "display_name": "Tempo de Resposta da Empresa"},
        {"name": "personal_plans_changed",        "display_name": "Mudança de Planos Pessoais"},
        {"name": "health_issues",                 "display_name": "Questões de Saúde"},
    ],
    "rejected": [
        # Decisão de negócio
        {"name": "another_candidate_selected",    "display_name": "Outro Candidato Selecionado",             "is_default": True},
        {"name": "position_cancelled",            "display_name": "Vaga Cancelada"},
        {"name": "position_frozen",               "display_name": "Vaga Congelada"},
        {"name": "internal_hire",                 "display_name": "Contratação Interna"},
        {"name": "budget_insufficient",           "display_name": "Budget Insuficiente"},
        {"name": "org_restructuring",             "display_name": "Reestruturação Organizacional"},
        # Qualificação
        {"name": "lacking_experience",            "display_name": "Falta de Experiência"},
        {"name": "under_qualified",               "display_name": "Subqualificado"},
        {"name": "over_qualified",                "display_name": "Sobrequalificado"},
        {"name": "lacking_technical_skills",      "display_name": "Habilidades Técnicas Insuficientes"},
        {"name": "education_mismatch",            "display_name": "Formação Incompatível"},
        {"name": "missing_certification",         "display_name": "Certificação Ausente"},
        {"name": "language_insufficient",         "display_name": "Idioma Insuficiente"},
        {"name": "tools_insufficient",            "display_name": "Conhecimento de Ferramentas Insuficiente"},
        # Cultural / comportamental
        {"name": "cultural_mismatch",             "display_name": "Não Aprovado Culturalmente"},
        {"name": "poor_communication",            "display_name": "Comunicação Inadequada"},
        {"name": "inadequate_attitude",           "display_name": "Postura Inadequada na Entrevista"},
        {"name": "lack_professionalism",          "display_name": "Falta de Profissionalismo"},
        {"name": "lack_of_interest",              "display_name": "Não Demonstrou Interesse"},
        {"name": "misaligned_expectations",       "display_name": "Expectativas Desalinhadas"},
        # Logística
        {"name": "location_mismatch",             "display_name": "Localização Incompatível"},
        {"name": "work_model_mismatch",           "display_name": "Modelo de Trabalho Incompatível"},
        {"name": "visa_required",                 "display_name": "Necessita Visto/Patrocínio"},
        {"name": "start_date_mismatch",           "display_name": "Disponibilidade de Data Incompatível"},
        {"name": "schedule_mismatch",             "display_name": "Horário/Jornada Incompatível"},
        {"name": "travel_requirements_mismatch",  "display_name": "Viagens Incompatíveis"},
        # Remuneração
        {"name": "salary_above_budget",           "display_name": "Expectativa Salarial Acima do Budget"},
        {"name": "benefits_mismatch",             "display_name": "Expectativa de Benefícios Incompatível"},
        {"name": "compensation_not_competitive",  "display_name": "Pacote Total Não Competitivo"},
        # Processo
        {"name": "interview_no_show",             "display_name": "Não Compareceu à Entrevista"},
        {"name": "test_no_show",                  "display_name": "Não Compareceu ao Teste"},
        {"name": "withdrew",                      "display_name": "Desistiu do Processo"},
        {"name": "unresponsive",                  "display_name": "Não Respondeu Tentativas de Contato"},
        {"name": "incomplete_documentation",      "display_name": "Documentação Incompleta"},
        {"name": "failed_technical_test",         "display_name": "Reprovado em Teste Técnico"},
        {"name": "failed_behavioral_test",        "display_name": "Reprovado em Teste Comportamental"},
        {"name": "negative_references",           "display_name": "Referências Negativas"},
        {"name": "failed_background_check",       "display_name": "Background Check Reprovado"},
        {"name": "failed_admission_exam",         "display_name": "Exame Admissional Inapto"},
    ],
    "standby": [
        {"name": "future_talent",                 "display_name": "Talento para Futuro",            "is_default": True},
        {"name": "better_other_role",             "display_name": "Melhor para Outra Vaga"},
        {"name": "awaiting_candidate_availability","display_name": "Aguardando Disponibilidade",    "is_waiting": True, "waiting_for": "candidate"},
        {"name": "paused_by_candidate",           "display_name": "Processo Pausado pelo Candidato"},
        {"name": "paused_by_company",             "display_name": "Processo Pausado pela Empresa"},
        {"name": "reengage_30_days",              "display_name": "Re-engajar em 30 Dias"},
        {"name": "reengage_3_months",             "display_name": "Re-engajar em 3 Meses"},
        {"name": "reengage_6_months",             "display_name": "Re-engajar em 6 Meses"},
        {"name": "awaiting_budget",               "display_name": "Aguardando Orçamento/Headcount"},
    ],
}

# Backward-compatibility alias (kept for any import that still references DEFAULT_SUB_STATUSES)
DEFAULT_SUB_STATUSES = CANONICAL_SUB_STATUSES


GUPY_STAGE_MAPPINGS = [
    {"ats_stage_name": "Inscrito", "wedotalent_stage": "sourcing"},
    {"ats_stage_name": "Triagem de Currículos", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Pré-Entrevista", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Entrevista Online", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista Presencial", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista RH", "wedotalent_stage": "interview_hr", "is_default_for_sync": True},
    {"ats_stage_name": "Teste Técnico", "wedotalent_stage": "interview_technical"},
    {"ats_stage_name": "Entrevista Técnica", "wedotalent_stage": "interview_technical", "is_default_for_sync": True},
    {"ats_stage_name": "Entrevista com Gestor", "wedotalent_stage": "interview_manager", "is_default_for_sync": True},
    {"ats_stage_name": "Proposta", "wedotalent_stage": "offer", "is_default_for_sync": True},
    {"ats_stage_name": "Contratado", "wedotalent_stage": "hired", "is_default_for_sync": True},
    {"ats_stage_name": "Reprovado", "wedotalent_stage": "rejected", "is_default_for_sync": True},
    {"ats_stage_name": "Desistência", "wedotalent_stage": "offer_declined"},
]


PANDAPE_STAGE_MAPPINGS = [
    {"ats_stage_name": "Novo", "wedotalent_stage": "sourcing"},
    {"ats_stage_name": "Triagem", "wedotalent_stage": "screening", "is_default_for_sync": True},
    {"ats_stage_name": "Qualificação", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Entrevista", "wedotalent_stage": "interview_hr", "is_default_for_sync": True},
    {"ats_stage_name": "Avaliação Técnica", "wedotalent_stage": "interview_technical", "is_default_for_sync": True},
    {"ats_stage_name": "Entrevista Final", "wedotalent_stage": "interview_manager", "is_default_for_sync": True},
    {"ats_stage_name": "Oferta", "wedotalent_stage": "offer", "is_default_for_sync": True},
    {"ats_stage_name": "Admitido", "wedotalent_stage": "hired", "is_default_for_sync": True},
    {"ats_stage_name": "Recusado", "wedotalent_stage": "rejected", "is_default_for_sync": True},
    {"ats_stage_name": "Desistiu", "wedotalent_stage": "offer_declined", "is_default_for_sync": True},
]


STANDARD_STAGE_CATALOG = [
    {
        "id": "sourcing",
        "name": "sourcing",
        "display_name": "Funil",
        "description": "Entrada de candidatos no processo seletivo",
        "icon": "search",
        "color": "#6366F1",
        "stage_category": "system",
        "action_behavior": "intake",
        "default_channel": "email",
        "is_system": True,
        "is_initial": True,
        "is_final": False,
        "removable": False,
        "default_sub_statuses": ["novo", "aprovado", "rejeitado"],
    },
    {
        "id": "screening",
        "name": "screening",
        "display_name": "Triagem",
        "description": "Triagem WSI - avaliação automatizada do candidato",
        "icon": "file-text",
        "color": "#8B5CF6",
        "stage_category": "system",
        "action_behavior": "screening",
        "default_channel": "email",
        "is_system": True,
        "is_initial": False,
        "is_final": False,
        "removable": False,
        "default_sub_statuses": ["convite_enviado", "em_andamento", "triagem_completa", "sem_resposta"],
    },
    {
        "id": "long_list",
        "name": "long_list",
        "display_name": "Long List",
        "description": "Lista longa de candidatos pré-selecionados",
        "icon": "list",
        "color": "#C5D9ED",
        "stage_category": "catalog",
        "action_behavior": "passive",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["adicionado"],
    },
    {
        "id": "short_list",
        "name": "short_list",
        "display_name": "Short List",
        "description": "Lista curta de candidatos finalistas",
        "icon": "list-checks",
        "color": "#B8C5D0",
        "stage_category": "catalog",
        "action_behavior": "passive",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["adicionado"],
    },
    {
        "id": "interview_hr",
        "name": "interview_hr",
        "display_name": "Entrevista RH",
        "description": "Entrevista com equipe de Recursos Humanos",
        "icon": "users",
        "color": "#EC4899",
        "stage_category": "catalog",
        "action_behavior": "scheduling",
        "default_channel": "email_whatsapp",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["convite_enviado", "agendada", "confirmada", "realizada", "reagendada", "no_show", "cancelada"],
    },
    {
        "id": "technical_test",
        "name": "technical_test",
        "display_name": "Teste Técnico",
        "description": "Avaliação técnica do candidato",
        "icon": "code-2",
        "color": "#E8B8B8",
        "stage_category": "catalog",
        "action_behavior": "evaluation",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["teste_enviado", "em_andamento", "concluido", "expirado"],
    },
    {
        "id": "english_test",
        "name": "english_test",
        "display_name": "Teste de Inglês",
        "description": "Avaliação de proficiência em inglês",
        "icon": "languages",
        "color": "#E5C5C5",
        "stage_category": "catalog",
        "action_behavior": "evaluation",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["teste_enviado", "em_andamento", "concluido", "expirado"],
    },
    {
        "id": "case_study",
        "name": "case_study",
        "display_name": "Case / Estudo de Caso",
        "description": "Apresentação de case ou estudo de caso",
        "icon": "presentation",
        "color": "#D4A8A8",
        "stage_category": "catalog",
        "action_behavior": "evaluation",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["teste_enviado", "em_andamento", "concluido", "expirado"],
    },
    {
        "id": "interview_technical",
        "name": "interview_technical",
        "display_name": "Entrevista Técnica",
        "description": "Entrevista técnica com time de engenharia",
        "icon": "code",
        "color": "#F59E0B",
        "stage_category": "catalog",
        "action_behavior": "scheduling",
        "default_channel": "email_whatsapp",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["convite_enviado", "agendada", "confirmada", "realizada", "reagendada", "no_show", "cancelada"],
    },
    {
        "id": "interview_manager",
        "name": "interview_manager",
        "display_name": "Entrevista Gestor",
        "description": "Entrevista com gestor direto da posição",
        "icon": "briefcase",
        "color": "#10B981",
        "stage_category": "catalog",
        "action_behavior": "scheduling",
        "default_channel": "email_whatsapp",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["convite_enviado", "agendada", "confirmada", "realizada", "reagendada", "no_show", "cancelada"],
    },
    {
        "id": "interview_final",
        "name": "interview_final",
        "display_name": "Entrevista Final",
        "description": "Entrevista final com diretoria ou comitê",
        "icon": "award",
        "color": "#D5BFA8",
        "stage_category": "catalog",
        "action_behavior": "scheduling",
        "default_channel": "email_whatsapp",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["convite_enviado", "agendada", "confirmada", "realizada", "reagendada", "no_show", "cancelada"],
    },
    {
        "id": "group_dynamics",
        "name": "group_dynamics",
        "display_name": "Dinâmica de Grupo",
        "description": "Dinâmica em grupo com outros candidatos",
        "icon": "users-round",
        "color": "#A78BFA",
        "stage_category": "catalog",
        "action_behavior": "scheduling",
        "default_channel": "email_whatsapp",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["convite_enviado", "agendada", "confirmada", "realizada", "reagendada", "no_show", "cancelada"],
    },
    {
        "id": "references",
        "name": "references",
        "display_name": "Referências",
        "description": "Verificação de referências profissionais",
        "icon": "phone",
        "color": "#E8E4E0",
        "stage_category": "catalog",
        "action_behavior": "verification",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["solicitacao_enviada", "parcialmente_recebido", "documentos_recebidos"],
    },
    {
        "id": "offer",
        "name": "offer",
        "display_name": "Proposta",
        "description": "Envio e negociação de proposta",
        "icon": "file-check",
        "color": "#3B82F6",
        "stage_category": "catalog",
        "action_behavior": "offer",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": False,
        "removable": True,
        "default_sub_statuses": ["proposta_enviada", "contra_proposta", "proposta_aceita"],
    },
    {
        "id": "offer_declined",
        "name": "offer_declined",
        "display_name": "Proposta Recusada",
        "description": "Candidato recusou a proposta",
        "icon": "x",
        "color": "#F97316",
        "stage_category": "catalog",
        "action_behavior": "conclusion_declined",
        "default_channel": "email",
        "is_system": False,
        "is_initial": False,
        "is_final": True,
        "removable": True,
        "default_sub_statuses": ["salario", "outra_proposta", "desistencia", "outro_motivo"],
    },
    {
        "id": "hired",
        "name": "hired",
        "display_name": "Contratado",
        "description": "Candidato contratado",
        "icon": "check-circle",
        "color": "#22C55E",
        "stage_category": "system",
        "action_behavior": "conclusion_hired",
        "default_channel": "email",
        "is_system": True,
        "is_initial": False,
        "is_final": True,
        "removable": False,
        "default_sub_statuses": ["proposta_aceita", "onboarding_pendente", "documentos_pendentes", "onboarding_completo"],
    },
    {
        "id": "rejected",
        "name": "rejected",
        "display_name": "Reprovado",
        "description": "Candidato reprovado no processo",
        "icon": "x-circle",
        "color": "#EF4444",
        "stage_category": "system",
        "action_behavior": "conclusion_rejected",
        "default_channel": "email",
        "is_system": True,
        "is_initial": False,
        "is_final": True,
        "removable": False,
        "default_sub_statuses": ["reprovado_triagem", "reprovado_entrevista", "reprovado_teste", "reprovado_gestor", "reprovado_referencias", "reprovado_outro"],
    },
]


# ─── Onda 2.2 fix (2026-05-23) ────────────────────────────────────────────
# Aliases + catalogos faltantes que stage_transition_automation.py importa.

SUB_STATUSES = CANONICAL_SUB_STATUSES

REJECTION_REASONS: list[dict] = [
    {"code": "reprovado_triagem",      "display_name": "Reprovado em Triagem",      "category": "screening"},
    {"code": "reprovado_entrevista",   "display_name": "Reprovado em Entrevista",   "category": "interview"},
    {"code": "reprovado_teste",        "display_name": "Reprovado em Teste",        "category": "test"},
    {"code": "reprovado_gestor",       "display_name": "Reprovado pelo Gestor",     "category": "manager"},
    {"code": "reprovado_referencias",  "display_name": "Reprovado em Referências",  "category": "references"},
    {"code": "perfil_inadequado",      "display_name": "Perfil Inadequado",         "category": "screening"},
    {"code": "experiencia_insuficiente", "display_name": "Experiência Insuficiente", "category": "screening"},
    {"code": "salario_incompativel",   "display_name": "Salário Incompatível",      "category": "negotiation"},
    {"code": "localizacao_incompativel", "display_name": "Localização Incompatível", "category": "logistics"},
    {"code": "fit_cultural",           "display_name": "Falta de Fit Cultural",     "category": "culture"},
    {"code": "reprovado_outro",        "display_name": "Outro Motivo",              "category": "other"},
]

OFFER_DECLINE_REASONS: list[dict] = [
    {"code": "salario_baixo",            "display_name": "Salário abaixo do esperado"},
    {"code": "beneficios_insuficientes", "display_name": "Pacote de benefícios insuficiente"},
    {"code": "contraproposta_atual",     "display_name": "Contraproposta da empresa atual"},
    {"code": "outra_oferta",             "display_name": "Aceitou outra oferta"},
    {"code": "localizacao",              "display_name": "Localização/Trajeto"},
    {"code": "modelo_trabalho",          "display_name": "Modelo de trabalho (presencial/híbrido/remoto)"},
    {"code": "carreira_diferente",       "display_name": "Mudança de área/carreira"},
    {"code": "questoes_pessoais",        "display_name": "Questões pessoais"},
    {"code": "outro",                    "display_name": "Outro motivo"},
]
