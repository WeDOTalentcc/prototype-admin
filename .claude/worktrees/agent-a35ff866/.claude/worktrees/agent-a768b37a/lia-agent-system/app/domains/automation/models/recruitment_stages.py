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

from app.core.database import Base


class RecruitmentStage(Base):
    """
    Configurable recruitment pipeline stages per company.
    
    Managed in Admin > Jornada de Recrutamento.
    These are the canonical WedoTalent stages that define the pipeline columns in Kanban.
    
    Example stages:
    - Funnel (Funil) [Sistema]
    - Screening (Triagem) [Sistema]
    - Interview HR (Entrevista RH) [Sistema]
    - Interview Manager (Entrevista Gestor) [Padrão]
    - Offer (Proposta) [Padrão]
    - Approved (Aprovado) [Sistema]
    - Rejected (Reprovado) [Sistema]
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
    
    stage_metadata = Column(JSON, default=lambda: {})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'name', name='uq_company_stage_name'),
        Index('ix_recruitment_stages_company_order', 'company_id', 'stage_order'),
    )
    
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
    )
    
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
    - "Inscrito" → "funnel"
    - "Triagem CV" → "screening"
    - "Pré-Entrevista" → "screening"
    - "Entrevista RH" → "interview_hr"
    - "Teste Técnico" → "interview_hr"
    - "Entrevista Técnica" → "interview_manager"
    - "Entrevista Gestor" → "interview_manager"
    - "Proposta" → "offer"
    - "Contratado" → "approved"
    - "Reprovado" → "rejected"
    
    Example mappings (WedoTalent → Gupy for sync):
    - "interview_manager" → "Entrevista com Gestor" (default for sync)
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
    )
    
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
    )
    
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
    )
    
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


DEFAULT_SUB_STATUSES = {
    "sourcing": [
        {"name": "novo", "display_name": "Novo", "is_default": True},
        {"name": "aprovado", "display_name": "Aprovado"},
        {"name": "rejeitado", "display_name": "Rejeitado"},
    ],
    "screening": [
        {"name": "convite_enviado", "display_name": "Convite Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "em_andamento", "display_name": "Em Andamento", "is_waiting": True, "waiting_for": "candidate"},
        {"name": "triagem_completa", "display_name": "Triagem Completa"},
        {"name": "sem_resposta", "display_name": "Sem Resposta"},
    ],
    "interview_hr": [
        {"name": "convite_enviado", "display_name": "Convite Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "agendada", "display_name": "Agendada"},
        {"name": "confirmada", "display_name": "Confirmada"},
        {"name": "realizada", "display_name": "Realizada"},
        {"name": "reagendada", "display_name": "Reagendada"},
        {"name": "no_show", "display_name": "Não Compareceu"},
        {"name": "cancelada", "display_name": "Cancelada"},
    ],
    "technical_test": [
        {"name": "teste_enviado", "display_name": "Teste Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "em_andamento", "display_name": "Em Andamento", "is_waiting": True, "waiting_for": "candidate"},
        {"name": "concluido", "display_name": "Concluído"},
        {"name": "expirado", "display_name": "Expirado"},
    ],
    "english_test": [
        {"name": "teste_enviado", "display_name": "Teste Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "em_andamento", "display_name": "Em Andamento", "is_waiting": True, "waiting_for": "candidate"},
        {"name": "concluido", "display_name": "Concluído"},
        {"name": "expirado", "display_name": "Expirado"},
    ],
    "interview_technical": [
        {"name": "convite_enviado", "display_name": "Convite Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "agendada", "display_name": "Agendada"},
        {"name": "confirmada", "display_name": "Confirmada"},
        {"name": "realizada", "display_name": "Realizada"},
        {"name": "reagendada", "display_name": "Reagendada"},
        {"name": "no_show", "display_name": "Não Compareceu"},
        {"name": "cancelada", "display_name": "Cancelada"},
    ],
    "interview_manager": [
        {"name": "convite_enviado", "display_name": "Convite Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "agendada", "display_name": "Agendada"},
        {"name": "confirmada", "display_name": "Confirmada"},
        {"name": "realizada", "display_name": "Realizada"},
        {"name": "reagendada", "display_name": "Reagendada"},
        {"name": "no_show", "display_name": "Não Compareceu"},
        {"name": "cancelada", "display_name": "Cancelada"},
    ],
    "interview_final": [
        {"name": "convite_enviado", "display_name": "Convite Enviado", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "agendada", "display_name": "Agendada"},
        {"name": "confirmada", "display_name": "Confirmada"},
        {"name": "realizada", "display_name": "Realizada"},
        {"name": "reagendada", "display_name": "Reagendada"},
        {"name": "no_show", "display_name": "Não Compareceu"},
        {"name": "cancelada", "display_name": "Cancelada"},
    ],
    "long_list": [
        {"name": "adicionado", "display_name": "Adicionado", "is_default": True},
    ],
    "short_list": [
        {"name": "adicionado", "display_name": "Adicionado", "is_default": True},
    ],
    "references": [
        {"name": "solicitacao_enviada", "display_name": "Solicitação Enviada", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "parcialmente_recebido", "display_name": "Parcialmente Recebido", "is_waiting": True, "waiting_for": "candidate"},
        {"name": "documentos_recebidos", "display_name": "Documentos Recebidos"},
    ],
    "offer": [
        {"name": "proposta_enviada", "display_name": "Proposta Enviada", "is_default": True, "is_waiting": True, "waiting_for": "candidate"},
        {"name": "contra_proposta", "display_name": "Contra-proposta"},
        {"name": "proposta_aceita", "display_name": "Proposta Aceita"},
    ],
    "offer_declined": [
        {"name": "salario", "display_name": "Recusou: Salário", "is_default": True},
        {"name": "outra_proposta", "display_name": "Recusou: Outra Proposta"},
        {"name": "desistencia", "display_name": "Recusou: Desistência"},
        {"name": "outro_motivo", "display_name": "Recusou: Outro Motivo"},
    ],
    "hired": [
        {"name": "proposta_aceita", "display_name": "Proposta Aceita", "is_default": True},
        {"name": "onboarding_pendente", "display_name": "Onboarding Pendente"},
        {"name": "documentos_pendentes", "display_name": "Documentos Pendentes", "is_waiting": True, "waiting_for": "candidate"},
        {"name": "onboarding_completo", "display_name": "Onboarding Completo"},
    ],
    "rejected": [
        {"name": "reprovado_triagem", "display_name": "Reprovado: Triagem", "is_default": True},
        {"name": "reprovado_entrevista", "display_name": "Reprovado: Entrevista"},
        {"name": "reprovado_teste", "display_name": "Reprovado: Teste"},
        {"name": "reprovado_gestor", "display_name": "Reprovado: Gestor"},
        {"name": "reprovado_referencias", "display_name": "Reprovado: Referências"},
        {"name": "reprovado_outro", "display_name": "Reprovado: Outro"},
    ],
}


GUPY_STAGE_MAPPINGS = [
    {"ats_stage_name": "Inscrito", "wedotalent_stage": "sourcing"},
    {"ats_stage_name": "Triagem de Currículos", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Pré-Entrevista", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Entrevista Online", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista Presencial", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista RH", "wedotalent_stage": "interview_hr", "is_default_for_sync": True},
    {"ats_stage_name": "Teste Técnico", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista Técnica", "wedotalent_stage": "interview_manager"},
    {"ats_stage_name": "Entrevista com Gestor", "wedotalent_stage": "interview_manager", "is_default_for_sync": True},
    {"ats_stage_name": "Proposta", "wedotalent_stage": "offer", "is_default_for_sync": True},
    {"ats_stage_name": "Contratado", "wedotalent_stage": "hired", "is_default_for_sync": True},
    {"ats_stage_name": "Reprovado", "wedotalent_stage": "rejected", "is_default_for_sync": True},
]


PANDAPE_STAGE_MAPPINGS = [
    {"ats_stage_name": "Novo", "wedotalent_stage": "sourcing"},
    {"ats_stage_name": "Triagem", "wedotalent_stage": "screening", "is_default_for_sync": True},
    {"ats_stage_name": "Qualificação", "wedotalent_stage": "screening"},
    {"ats_stage_name": "Entrevista", "wedotalent_stage": "interview_hr", "is_default_for_sync": True},
    {"ats_stage_name": "Avaliação Técnica", "wedotalent_stage": "interview_hr"},
    {"ats_stage_name": "Entrevista Final", "wedotalent_stage": "interview_manager", "is_default_for_sync": True},
    {"ats_stage_name": "Oferta", "wedotalent_stage": "offer", "is_default_for_sync": True},
    {"ats_stage_name": "Admitido", "wedotalent_stage": "hired", "is_default_for_sync": True},
    {"ats_stage_name": "Recusado", "wedotalent_stage": "rejected", "is_default_for_sync": True},
]
