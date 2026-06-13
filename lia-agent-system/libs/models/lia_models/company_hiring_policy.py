"""
CompanyHiringPolicy Model — Company-specific hiring rules and automation configuration.

Stores all hiring policies for a company in 5 JSON blocks:
- pipeline_rules: Min interviews, approval rules, SLA per stage
- scheduling_rules: Allowed days/hours, duration, self-scheduling
- communication_rules: Feedback, channels, tone
- screening_rules: Salary filter, experience policy, default questions
- automation_rules: Auto-screening, auto-scheduling, autonomy level

Plus:
- pipeline_templates: Templates for different job types
- learned_patterns: Auto-filled by LIA over time (never by form)

One record per company (company_id is unique).
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Float, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

from lia_config.database import Base


PIPELINE_RULES_DEFAULTS = {
    "min_interviews_before_offer": 2,
    "manager_approval_for_offer": True,
    "manager_approval_sla_hours": 24,   # P3a — reclassificado de narrativo
    "vacancy_approval_required": False,  # P3a — reclassificado de narrativo
    "max_days_in_stage": {},
}

SCHEDULING_RULES_DEFAULTS = {
    "allowed_days": ["mon", "tue", "wed", "thu", "fri"],
    "allowed_hours": {"start": "09:00", "end": "18:00"},
    "default_duration_minutes": 60,
    "self_scheduling_enabled": False,
}

COMMUNICATION_RULES_DEFAULTS = {
    "auto_rejection_feedback": False,
    "rejection_feedback_deadline_hours": 48,
    "preferred_channel": "whatsapp",
    "lia_tone": "professional",
    "briefing_frequency": "daily",   # B1 canonical — lido por briefing_dispatch.py
    "digest_enabled": True,           # B2 opt-in digest — gated em WeeklyDigestService
    "show_wedotalent_branding": True,   # Phase 1a: "Powered by WeDOTalent" footer in InterviewLobby
    "preferred_data_channel": "email",   # Fase 7: canal padrão de coleta de dados do candidato (email/web/whatsapp/voice)
}

SCREENING_RULES_DEFAULTS = {
    "experience_policy": "per_job",
    "minimum_compatibility_score": 0,   # P3a — reclassificado de narrativo (0 = sem corte)
    "default_screening_questions": [],
    # Thresholds de aprovação automática — None = usa padrão da plataforma (fairness_policy_rules)
    # Tenant pode configurar valor >= ao mínimo da plataforma (nunca abaixo)
    # auto_approve_threshold: 0.0-1.0 (equivalente a score/100)
    # review_threshold: 0.0-1.0 — candidatos entre review e auto_approve vão para revisão humana
    "auto_approve_threshold": None,   # None → usa fairness_policy_rules decision_threshold
    "review_threshold": None,         # None → usa 73% do auto_approve_threshold
    "sector": None,                   # setor da empresa (tech/varejo/financeiro/saude/logistica/rpo)
}

AUTOMATION_RULES_DEFAULTS = {
    "auto_screening": False,
    "auto_scheduling": False,
    "auto_stage_advance": False,
    "autonomy_level": "low",
    # Sprint B Phase 1+ — Learning Loops toggles (LGPD opt-in for sensitive ones)
    "learning_loops": {
        "enabled": True,                       # master switch
        "bigfive_company_culture": True,       # Phase 2 — DNA cultural estatico, default ON
        "bigfive_department_history": False,   # Phase 2 — 2026-05-24: alinhado com UI requiresDisclosure=true. Opt-in LGPD via disclosure modal canonical (reverte D2 2026-05-10).
        "wsi_question_effectiveness": False,   # Phase 3 — opt-in
        "jd_similar_suggestion": True,         # Phase 1 — baixo risco, default ON
    },
}


OFFER_RULES_DEFAULTS = {
    "allowed_start_day_of_month": [1, 15],
    "onboarding_blackout_periods": [],
    "min_notice_days": 30,
    "negotiation_enabled": False,
    "salary_flex_pct_max": 0,
    "benefits_flex_items": [],
    "negotiation_hitl_threshold_pct": 5,
    "counter_proposal_max_rounds": 2,
}

ALL_DEFAULTS = {
    "pipeline_rules": PIPELINE_RULES_DEFAULTS,
    "scheduling_rules": SCHEDULING_RULES_DEFAULTS,
    "communication_rules": COMMUNICATION_RULES_DEFAULTS,
    "screening_rules": SCREENING_RULES_DEFAULTS,
    "automation_rules": AUTOMATION_RULES_DEFAULTS,
    "offer_rules": OFFER_RULES_DEFAULTS,
    "pipeline_templates": [],
    "learned_patterns": [],
}


class CompanyHiringPolicy(Base):
    """
    Company-specific hiring policies and automation configuration.
    One record per company (company_id is unique).
    """
    __tablename__ = "company_hiring_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, unique=True, index=True)

    pipeline_rules = Column(JSON, default=lambda: PIPELINE_RULES_DEFAULTS.copy())
    scheduling_rules = Column(JSON, default=lambda: SCHEDULING_RULES_DEFAULTS.copy())
    communication_rules = Column(JSON, default=lambda: COMMUNICATION_RULES_DEFAULTS.copy())
    screening_rules = Column(JSON, default=lambda: SCREENING_RULES_DEFAULTS.copy())
    automation_rules = Column(JSON, default=lambda: AUTOMATION_RULES_DEFAULTS.copy())

    # Per-role PII visibility defaults (2026-06-06): {role: {field: bool}}.
    pii_visibility_defaults = Column(JSON, default=lambda: {})

    # N2/N3 offer configuration block — negociação, dias de início, aviso prévio
    offer_rules = Column(JSONB, default=lambda: OFFER_RULES_DEFAULTS.copy())
    # P3b (2026-06-01): instruções narrativas do recrutador por conceito de
    # política (texto livre que orienta a LIA). SEPARADO dos 5 blocos de gate —
    # nunca alimenta um if/gate, só o system prompt. Invariante de segurança.
    policy_instructions = Column(JSON, default=lambda: {})

    pipeline_templates = Column(JSON, default=lambda: [])
    learned_patterns = Column(JSON, default=lambda: [])

    answered_questions = Column(JSON, default=lambda: [])

    setup_progress = Column(Integer, default=0)
    setup_completed_at = Column(DateTime, nullable=True)

    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_chp_company_id', 'company_id'),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<CompanyHiringPolicy company={self.company_id} progress={self.setup_progress}%>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "pipeline_rules": self.pipeline_rules or PIPELINE_RULES_DEFAULTS,
            "scheduling_rules": self.scheduling_rules or SCHEDULING_RULES_DEFAULTS,
            "communication_rules": self.communication_rules or COMMUNICATION_RULES_DEFAULTS,
            "screening_rules": self.screening_rules or SCREENING_RULES_DEFAULTS,
            "automation_rules": self.automation_rules or AUTOMATION_RULES_DEFAULTS,
            "policy_instructions": self.policy_instructions or {},
            "pipeline_templates": self.pipeline_templates or [],
            "learned_patterns": self.learned_patterns or [],
            "answered_questions": self.answered_questions or [],
            "offer_rules": self.offer_rules or OFFER_RULES_DEFAULTS,
            "setup_progress": self.setup_progress or 0,
            "setup_completed_at": self.setup_completed_at.isoformat() if self.setup_completed_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_rule(self, block: str, key: str, default=None):
        """Get a specific rule value with fallback to defaults."""
        block_data = getattr(self, block, None)
        if block_data and key in block_data:
            return block_data[key]
        block_defaults = ALL_DEFAULTS.get(block, {})
        if isinstance(block_defaults, dict):
            return block_defaults.get(key, default)
        return default
