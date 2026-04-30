"""
Compensation Policy model — Politica de Remuneracao Variavel (PRV).

Schema-alvo: 1:1 com Rails canonical
(ats-api-copia/db/migrate/20250715000009_create_compensation_policies.rb,
23 colunas) + updated_by (auditabilidade) + timestamps = 26 colunas.

Multi-tenancy: scoping por company_id (UUID FK to company_profiles); RLS
sera aplicada via migration alembic 102.

Schema da `variable_compensation` jsonb (verbas tipadas com kind discriminator):
    {
      "items": [
        {"kind": "plr", "name": "PLR Anual 2026", "base": "salary_anual",
         "value_pct": 15, "frequency": "annual",
         "trigger": "goal_achievement", "trigger_details": {...},
         "applicable_seniority": ["senior","staff"]},
        {"kind": "ppr", "name": "PPR Lei 10.101/2000", "base": "result", ...},
        {"kind": "bonus", "name": "Bonus Meta", "base": "salary_mensal",
         "min_pct": 0, "max_pct": 30, "frequency": "quarterly", ...},
        {"kind": "commission", "name": "Comissao Vendas", "base": "revenue",
         "tiers": [{"from_pct": 0, "to_pct": 80, "commission_pct": 2}, ...]},
        {"kind": "spot_bonus", ...},
        {"kind": "equity", ...}
      ]
    }

Schema da `salary_bands` jsonb:
    [
      {"level": "junior", "min": 5000, "mid": 7000, "max": 9000, "currency": "BRL"},
      {"level": "pleno", ...},
      {"level": "senior", ...}
    ]

Best practices: ver docs/COMPENSATION_BEST_PRACTICES.md (a2b209c91).

LGPD/Fairness:
- approved_by, created_by, updated_by armazenados como user_id (UUID).
- // TODO(FAIRNESS:001) — fairness guard em applicable_departments[],
  applicable_seniority[], applicable_roles[] (Fase 2.4 router).
- // TODO(LGPD:001) — masking de approved_by em logs de offer (Fase 4).

Refs:
- Plan: ~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md (Fase 2.2)
- Best practices: docs/COMPENSATION_BEST_PRACTICES.md
- Rails canonical: ats-api-copia/db/migrate/20250715000009_create_compensation_policies.rb (READ-ONLY)
"""
from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class CompensationPolicy(Base):
    """
    Politica de remuneracao por empresa.

    Suporta:
      - Bandas salariais (salary_bands jsonb): faixas Min/Mid/Max por nivel.
      - Verbas variaveis (variable_compensation jsonb): PLR, PPR, Bonus,
        Comissao, Spot Bonus, Equity — tipadas com `kind` discriminator.
      - Elegibilidade: applicable_departments[] x applicable_seniority[] x
        applicable_roles[].
      - Versionamento + aprovacao + vigencia.
    """

    __tablename__ = "compensation_policies"

    # --- Chaves ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("company_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Identificacao ---
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=True)  # ex: hierarchical_bands | mixed | variable_only
    currency = Column(String(10), nullable=False, default="BRL")

    # --- Estrutura (jsonb) — verbas tipadas ---
    salary_bands = Column(JSONB, nullable=False, server_default="[]")
    bonus_structure = Column(JSONB, nullable=False, server_default="{}")
    equity_rules = Column(JSONB, nullable=False, server_default="{}")
    benefits_package = Column(JSONB, nullable=False, server_default="{}")
    variable_compensation = Column(JSONB, nullable=False, server_default="{}")

    # --- Elegibilidade (Postgres arrays) ---
    applicable_departments = Column(ARRAY(String), nullable=False, server_default="{}")
    applicable_seniority = Column(ARRAY(String), nullable=False, server_default="{}")
    applicable_roles = Column(ARRAY(String), nullable=False, server_default="{}")

    # --- Estado ---
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)

    # --- Vigencia + Aprovacao ---
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)  # user_id (UUID-like string)
    approved_at = Column(DateTime, nullable=True)

    # --- Versionamento + Audit ---
    version = Column(Integer, nullable=False, default=1)
    revision_history = Column(JSONB, nullable=False, server_default="[]")
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)  # extra vs Rails: auditabilidade

    # --- Timestamps ---
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    company = relationship(
        "CompanyProfile",
        back_populates="compensation_policies",
        foreign_keys=[company_id],
    )

    def __repr__(self):
        return (
            f"<CompensationPolicy {self.id} name={self.name!r} "
            f"v{self.version} active={self.is_active}>"
        )


# ---------------------------------------------------------------------------
# Constantes auxiliares — schema interno de variable_compensation.items[].kind
# ---------------------------------------------------------------------------

VARIABLE_COMP_KINDS = (
    "plr",          # Participacao nos Lucros e Resultados (Lei 10.101/2000)
    "ppr",          # Participacao nos Resultados (variante PLR vinculada a metas)
    "bonus",        # Bonus por meta/desempenho
    "commission",   # Comissao sobre vendas/revenue
    "spot_bonus",   # Bonus pontual / discrecionario
    "equity",       # Stock options, RSUs, phantom shares
)

VARIABLE_COMP_BASES = (
    "salary_anual",   # % do salario anual
    "salary_mensal",  # % do salario mensal
    "revenue",        # % da receita atribuida
    "result",         # vinculado a resultado financeiro (PPR)
    "custom",         # logica custom no campo trigger_details
)

VARIABLE_COMP_FREQUENCIES = (
    "monthly",
    "quarterly",
    "annual",
    "biannual",
    "one_off",
    "on_target_achievement",
)


# Default templates Brasileiros — usados pelo seed em
# CompensationPolicyRepository.seed_defaults() (Fase 2.4).
DEFAULT_BR_COMPENSATION_TEMPLATES = [
    {
        "name": "PLR Anual Padrao",
        "description": "Participacao nos Lucros e Resultados conforme Lei 10.101/2000.",
        "policy_type": "variable_only",
        "currency": "BRL",
        "salary_bands": [],
        "variable_compensation": {
            "items": [
                {
                    "kind": "plr",
                    "name": "PLR Anual",
                    "base": "salary_anual",
                    "value_pct": 8.33,  # 1/12 — ate 1 salario anual
                    "frequency": "annual",
                    "trigger": "goal_achievement",
                    "trigger_details": {"metric": "EBITDA", "threshold_pct": 80},
                    "applicable_seniority": ["all"],
                }
            ]
        },
        "applicable_seniority": ["all"],
        "is_default": True,
    },
    {
        "name": "Bonus Comercial — Vendas",
        "description": "Bonus quadrimestral por atingimento de metas de vendas.",
        "policy_type": "variable_only",
        "currency": "BRL",
        "salary_bands": [],
        "variable_compensation": {
            "items": [
                {
                    "kind": "bonus",
                    "name": "Bonus Meta Trimestral",
                    "base": "salary_mensal",
                    "min_pct": 0,
                    "max_pct": 30,
                    "frequency": "quarterly",
                    "trigger": "kpi",
                    "trigger_details": {"kpi": "team_okr_score", "threshold": 0.7},
                }
            ]
        },
        "applicable_departments": ["comercial", "vendas"],
        "is_default": False,
    },
]
