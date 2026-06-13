"""
ATS-Fairness Policy Models — 3-layer composable fairness policy system.

Tables:
  - fairness_policy_rules: Policy rules (platform-general, platform-domain, tenant)
  - fairness_policy_activations: Which rules are active for which tenant/domain
  - fairness_policy_violations: Log of detected violations

ADR ref: ADR-001 (storage) + §9 Definições Arquiteturais v0.4.1
Compliance: LGPD Art.6/11 + EU AI Act Annex III item 4
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID

from lia_config.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PolicyScope(str, enum.Enum):
    PLATFORM_GENERAL = "platform_general"   # NULL company_id — applies to all
    PLATFORM_DOMAIN = "platform_domain"     # NULL company_id — specific domain
    TENANT = "tenant"                       # NOT NULL company_id — tenant override


class PolicyRuleType(str, enum.Enum):
    BLOCKED_ATTRIBUTE = "blocked_attribute"
    MANDATORY_ANONYMIZATION = "mandatory_anonymization"
    LINGUISTIC_BANLIST = "linguistic_banlist"
    DECISION_THRESHOLD = "decision_threshold"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    AUDIT_REQUIRED_FIELDS = "audit_required_fields"
    PIPELINE_FAIRNESS_METRIC = "pipeline_fairness_metric"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class FairnessPolicyRule(Base):
    """
    Fairness policy rule — a single composable rule in the 3-layer hierarchy.

    Hierarchy:
      Layer 1: scope=platform_general, company_id=NULL, domain=NULL
      Layer 2: scope=platform_domain, company_id=NULL, domain=<domain>
      Layer 3: scope=tenant, company_id=<uuid>, domain=<domain>

    Locked rules (is_locked=True) cannot be softened by tenant overrides.
    """
    __tablename__ = "fairness_policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    scope = Column(String(30), nullable=False)
    domain = Column(String(50), nullable=True)
    rule_type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft")
    is_locked = Column(Boolean, nullable=False, default=True)
    body_json = Column(JSON, nullable=False, default=dict)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_fairness_rules_scope_domain", "scope", "domain"),
        Index("ix_fairness_rules_company_id_status", "company_id", "status"),
    )


class FairnessPolicyActivation(Base):
    """
    Tracks which fairness policy rules are currently active for a tenant/domain.

    Unique constraint prevents duplicate activations of the same rule for the same
    company_id+domain combination.
    """
    __tablename__ = "fairness_policy_activations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    domain = Column(String(50), nullable=False)
    rule_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    activated_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    activated_by = Column(UUID(as_uuid=True), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("company_id", "domain", "rule_id", name="uq_activation_company_domain_rule"),
        Index("ix_activation_company_domain_current", "company_id", "domain", "is_current"),
    )


class FairnessPolicyViolation(Base):
    """
    Immutable audit log of fairness policy violations detected at runtime.

    LGPD compliance: input_snapshot_hash is SHA-256 of masked input (never raw PII).
    decision_context stores non-PII metadata about the decision.
    """
    __tablename__ = "fairness_policy_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(50), nullable=False)
    rule_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    rule_type = Column(String(50), nullable=False)
    violation_type = Column(String(80), nullable=False)
    input_snapshot_hash = Column(String(64), nullable=True)
    decision_context = Column(JSON, nullable=True)
    was_blocked = Column(Boolean, nullable=False, default=True)
    detected_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    correlation_id = Column(String(80), nullable=True, index=True)

    __table_args__ = (
        Index("ix_violations_company_domain_detected", "company_id", "domain", "detected_at"),
    )


# ---------------------------------------------------------------------------
# Default platform rules (seed data)
# ---------------------------------------------------------------------------

DEFAULT_PLATFORM_GENERAL_RULES = [
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "blocked_attribute",
        "is_locked": True,
        "description": "Atributos protegidos proibidos como input de decisão",
        "body_json": {
            "attributes": [
                "gender", "genero", "raca", "race", "religiao", "religion",
                "estado_civil", "marital_status", "idade_exata", "foto", "photo",
            ],
            "action": "reject_input",
        },
    },
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "mandatory_anonymization",
        "is_locked": True,
        "description": "Campos PII que devem ser mascarados antes do LLM",
        "body_json": {
            "fields": [
                "cpf", "rg", "foto", "photo", "nome_completo", "email", "telefone",
                "endereco", "data_nascimento",
            ],
            "strategy": "redact",
        },
    },
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "human_in_the_loop",
        "is_locked": True,
        "description": "Decisões que exigem aprovação humana obrigatória",
        "body_json": {
            "decision_types": ["final_rejection", "offer_extension", "blacklist"],
            "bypass_allowed": False,
        },
    },
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "decision_threshold",
        "is_locked": False,  # tunable — tenant pode subir, não pode baixar
        "description": "Confiança mínima para decisão automática de screening",
        "body_json": {
            "min_confidence": 0.75,
            "applies_to": ["screening_score", "match_score"],
        },
    },
    {
        "scope": "platform_domain",
        "domain": "screening",
        "rule_type": "pipeline_fairness_metric",
        "is_locked": False,
        "description": "Paridade demográfica mínima no funil de screening",
        "body_json": {
            "metric": "demographic_parity",
            "min_ratio": 0.80,
            "protected_attributes": ["gender", "race"],
            "alert_threshold": 0.85,
        },
    },
]
