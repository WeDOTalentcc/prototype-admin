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
    # -----------------------------------------------------------------------
    # REGRA 1: blocked_attribute — todos os atributos protegidos (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "blocked_attribute",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "Atributos protegidos proibidos como input de decisão de IA (LGPD Art.11 + CF Art.5º + EU AI Act Annex III)",
        "body_json": {
            "attributes": [
                # Gênero/Sexo
                "gender", "genero", "gênero", "sex", "sexo",
                # Raça/Etnia
                "race", "raca", "raça", "ethnicity", "etnia", "cor", "cor_pele", "skin_color",
                # Idade
                "age", "idade", "birth_date", "data_nascimento",
                # Religião
                "religion", "religiao", "religião", "credo",
                # Orientação sexual
                "orientacao_sexual", "sexual_orientation",
                # Estado civil / maternidade
                "marital_status", "estado_civil", "filhos", "maternidade", "paternidade", "gravidez",
                # Deficiência
                "disability", "deficiencia", "deficiência", "pcd", "pne",
                # Nacionalidade
                "nationality", "nacionalidade",
                # Antecedentes criminais
                "antecedentes_criminais", "criminal_records", "ficha_criminal",
                # Saúde
                "saude", "health", "doenca", "hiv", "aids",
                # Filiação sindical
                "filiacao_sindical", "union_membership",
                # Aparência física
                "aparencia_fisica", "physical_appearance", "altura", "peso", "estatura",
            ],
            "action": "reject_input",
            "legal_bases": ["LGPD Art.11", "CF Art.5º", "CLT Art.373-A", "Lei 9.029/95", "EU AI Act Annex III item 4"]
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 2: mandatory_anonymization — PII antes do LLM (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "mandatory_anonymization",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "Campos PII que DEVEM ser mascarados antes de qualquer prompt de LLM (LGPD Art.12)",
        "body_json": {
            "fields": [
                "cpf", "rg", "foto", "photo", "nome_completo", "full_name",
                "email", "telefone", "phone", "endereco", "address",
                "data_nascimento", "birth_date", "foto_perfil", "profile_photo"
            ],
            "strategy": "redact",
            "legal_basis": "LGPD Art.12 §1 — anonimização antes de processamento por IA"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 3: human_in_the_loop — decisões que exigem aprovação humana (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "human_in_the_loop",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "Tipos de decisão que NUNCA podem ser tomados automaticamente sem aprovação humana (EU AI Act Art.14)",
        "body_json": {
            "decision_types": ["final_rejection", "offer_extension", "blacklist", "offer_send"],
            "bypass_allowed": False,
            "legal_basis": "EU AI Act Art.14 (human oversight) + CLT Art.373-A"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 4: decision_threshold — confiança mínima padrão (tunable — tenant pode subir)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "decision_threshold",
        "is_locked": False,
        "status": "published",
        "version": 1,
        "description": "Confiança mínima para decisão automática de IA. Tenant pode aumentar (nunca diminuir).",
        "body_json": {
            "min_confidence": 0.75,
            "applies_to": ["screening_score", "match_score", "cv_score"],
            "note": "Baseado em ALPHA1_SECTOR_RULES default (varejo/logistica=0.80, financeiro/saude=0.90)"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 5: linguistic_banlist PT-BR — 13 categorias discriminatórias (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "linguistic_banlist",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "13 categorias de termos discriminatórios PT-BR extraídas do FairnessGuard (regex Layer 1)",
        "body_json": {
            "language": "pt-BR",
            "detection_mode": "regex_hard_block",
            "categories": {
                "genero": {"legal_basis": "CLT Art.5º, Lei 9.029/95, CRFB/88 Art.5º"},
                "raca_etnia": {"legal_basis": "CF Art.5º, Lei 7.716/89"},
                "idade": {"legal_basis": "Lei 10.741/03, CLT"},
                "religiao": {"legal_basis": "CF Art.5º VI"},
                "orientacao_sexual": {"legal_basis": "STF ADO 26"},
                "estado_civil": {"legal_basis": "CLT Art.373-A"},
                "deficiencia": {"legal_basis": "Lei 8.213/91, Lei 13.146/15, CRPD"},
                "maternidade_paternidade": {"legal_basis": "CLT Art.373-A, Lei 9.029/95"},
                "nacionalidade": {"legal_basis": "CF Art.5º"},
                "antecedentes_criminais": {"legal_basis": "CNJ Res.65/08, Lei 7.210/84"},
                "saude_doenca": {"legal_basis": "Lei 9.029/95, Lei 9.313/96"},
                "filiacao_sindical": {"legal_basis": "CLT Art.543, CF Art.8º"},
                "aparencia_fisica": {"legal_basis": "Lei 9.029/95, jurisprudência TST"},
            },
            "source": "app/shared/compliance/fairness_guard.py::DISCRIMINATORY_CATEGORIES",
            "total_categories": 13,
            "action": "block"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 6: linguistic_banlist EN — categorias inglês (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "linguistic_banlist",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "Categorias de termos discriminatórios em inglês extraídas do FairnessGuard",
        "body_json": {
            "language": "en",
            "detection_mode": "regex_hard_block",
            "categories": {
                "appearance_en": {"legal_basis": "Lei 9.029/95, anti-discrimination law"},
                "gender_en": {"legal_basis": "Lei 9.029/95, Title VII, EU Directive 2006/54"},
                "race_en": {"legal_basis": "Lei 7.716/89, CRFB/88 Art.5"},
                "age_en": {"legal_basis": "ADEA, EU Directive 2000/78, Lei 9.029/95"},
                "religion_en": {"legal_basis": "Title VII, EU Directive 2000/78, CRFB/88 Art.5 VI"},
                "disability_en": {"legal_basis": "ADA, CRPD, Lei 13.146/15"},
                "socioeconomic_en": {"legal_basis": "anti-discrimination law"},
            },
            "source": "app/shared/compliance/fairness_guard.py::DISCRIMINATORY_CATEGORIES_EN",
            "total_categories": 7,
            "action": "block"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 7: linguistic_banlist — termos implícitos de viés (warn, não block)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "linguistic_banlist",
        "is_locked": False,
        "status": "published",
        "version": 1,
        "description": "Termos com viés implícito (soft warnings, não bloqueiam mas alertam). Tunable — tenant pode adicionar termos.",
        "body_json": {
            "language": "pt-BR+en",
            "detection_mode": "substring_warn",
            "action": "warn",
            "terms_pt": [
                "boa aparencia", "bairros nobres", "regiao nobre", "universidades de primeira linha",
                "faculdade de ponta", "escola particular", "clube social", "perfil adequado",
                "apresentacao pessoal", "morar proximo", "zona rural", "periferia",
                "interior do estado", "suburbio", "sem adaptacoes", "sem necessidade de acessibilidade",
                "sem restricoes fisicas", "espirita", "candomble", "umbanda", "valores cristaos",
                "principios religiosos", "sem obrigacoes", "disponibilidade total",
                "sem compromissos pessoais", "mae solo", "alto potencial de crescimento rapido",
                "energia jovem"
            ],
            "terms_en": [
                "young and dynamic", "young blood", "energetic", "digital native", "recent graduate",
                "culture fit", "prestigious university", "ivy league", "top school", "right neighborhood",
                "proper background", "clean-cut", "good looking", "presentable", "native speaker",
                "traditional values", "religious requirements", "church-going", "faith-based values",
                "sunday availability", "christian values", "religious affiliation", "worship attendance",
                "god-fearing", "without restrictions", "fully able", "no disabilities", "physically fit",
                "able-bodied", "from a good family", "private school", "affluent area", "low-income",
                "no family obligations", "available at all times"
            ],
            "source": "app/shared/compliance/fairness_guard.py::IMPLICIT_BIAS_TERMS + IMPLICIT_BIAS_TERMS_EN",
            "total_terms_pt": 28,
            "total_terms_en": 35
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 8: pipeline_fairness_metric — screening (tunable)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_domain",
        "domain": "screening",
        "rule_type": "pipeline_fairness_metric",
        "is_locked": False,
        "status": "published",
        "version": 1,
        "description": "Paridade demográfica mínima monitorada no funil de screening",
        "body_json": {
            "metric": "demographic_parity",
            "min_ratio": 0.80,
            "protected_attributes": ["gender", "race"],
            "alert_threshold": 0.85,
            "monitor_at_stages": ["shortlist", "interview", "offer"],
            "legal_basis": "EU AI Act Art.10(2) + LGPD Art.6 VII (não-discriminação)"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 9: decision_threshold por setor — thresholds extraídos de ALPHA1_SECTOR_RULES
    # -----------------------------------------------------------------------
    {
        "scope": "platform_domain",
        "domain": "screening",
        "rule_type": "decision_threshold",
        "is_locked": False,
        "status": "published",
        "version": 1,
        "description": "Thresholds de aprovação automática por setor (ALPHA1_SECTOR_RULES). Tenant pode aumentar.",
        "body_json": {
            "sectors": {
                "tech":       {"auto_approve_threshold": 0.85, "hitl_threshold": 0.65, "max_pipeline_days": 30},
                "varejo":     {"auto_approve_threshold": 0.80, "hitl_threshold": 0.70, "max_pipeline_days": 21},
                "logistica":  {"auto_approve_threshold": 0.80, "hitl_threshold": 0.70, "max_pipeline_days": 14},
                "financeiro": {"auto_approve_threshold": 0.90, "hitl_threshold": 0.80, "max_pipeline_days": 45},
                "saude":      {"auto_approve_threshold": 0.90, "hitl_threshold": 0.80, "max_pipeline_days": 45},
                "rpo":        {"auto_approve_threshold": 0.82, "hitl_threshold": 0.60, "max_pipeline_days": 25},
                "default":    {"auto_approve_threshold": 0.75, "hitl_threshold": 0.65, "max_pipeline_days": 30},
            },
            "source": "app/domains/policy/services/policy_engine_service.py::ALPHA1_SECTOR_RULES",
            "note": "Tenant pode subir os thresholds nunca diminuir"
        }
    },

    # -----------------------------------------------------------------------
    # REGRA 10: audit_required_fields — campos obrigatórios no log de decisões (locked)
    # -----------------------------------------------------------------------
    {
        "scope": "platform_general",
        "domain": None,
        "rule_type": "audit_required_fields",
        "is_locked": True,
        "status": "published",
        "version": 1,
        "description": "Campos obrigatórios em cada registro de decisão de IA para auditoria regulatória",
        "body_json": {
            "required_fields": [
                "tenant_id", "domain", "decision_type", "confidence_score",
                "policy_version_id", "correlation_id", "agent_name",
                "input_hash", "detected_at"
            ],
            "legal_basis": "EU AI Act Art.12 (record-keeping) + LGPD Art.37 V (registro de operações)"
        }
    },
]
