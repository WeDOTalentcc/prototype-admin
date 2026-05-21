"""Create alert_rule_templates + seed master canonical (10 items).

Audit 2026-05-20 Sessão I / Sprint 3 (catalogos dinamicos):
substitui catalogo hardcoded DEFAULT_ALERTS (CommunicationHub.constants.ts)
por modelo per-tenant canonical no DB.

Schema canonical:
- is_master_template=True: items curados pela WeDOTalent (NULL company_id)
- is_master_template=False: customs por company (company_id NOT NULL)
- parent_template_id: NOT NULL quando custom é cópia de master (canonical A1)
- soft-delete via deleted_at

Revision ID: 155_alert_rule_templates
Revises: 153_eligibility_question_templates
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "155_alert_rule_templates"
down_revision: Union[str, None] = "153_eligibility_question_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed canonical: mapeia DEFAULT_ALERTS hardcoded para schema canonical.
# Schema canonical (decidido Paulo 2026-05-20):
#   event_type: chave estável referenciada pelo pipeline events
#   label: nome humano do alert
#   audience: recruiter|admin|candidate
#   channels: lista canonical (email|in_app|teams|whatsapp)
#   delay_minutes: int — quanto tempo aguardar antes de disparar
#   schedule_lgpd_compliant: bool — respeita horários comerciais (Lei 13.709)
#   rationale: texto explicando o porquê do delay/canal canonical
MASTER_ITEMS = [
    {
        "legacy_id": "1",
        "event_type": "sla_at_risk",
        "label": "SLA Próximo do Vencimento",
        "description": "Alerta quando um candidato está há 80% do SLA na mesma etapa",
        "audience": "recruiter",
        "channels": ["email", "in_app"],
        "delay_minutes": 0,
        "schedule_lgpd_compliant": True,
        "rationale": "SLA alerts são acionáveis imediatamente; canonical recruiter-only",
        "enabled_default": True,
    },
    {
        "legacy_id": "2",
        "event_type": "monthly_goal_at_risk",
        "label": "Meta Mensal em Risco",
        "description": "Notifica quando a meta de contratações do mês pode não ser atingida",
        "audience": "admin",
        "channels": ["email"],
        "delay_minutes": 0,
        "schedule_lgpd_compliant": True,
        "rationale": "Goal alerts são admin-only e enviadas por email durante horário comercial",
        "enabled_default": True,
    },
    {
        "legacy_id": "3",
        "event_type": "candidate_no_interaction",
        "label": "Candidato Sem Interação",
        "description": "Alerta para candidatos sem contato há mais de 5 dias",
        "audience": "recruiter",
        "channels": ["teams"],
        "delay_minutes": 7200,
        "schedule_lgpd_compliant": True,
        "rationale": "5 dias = 7200min; teams canonical para recrutador acionar follow-up",
        "enabled_default": True,
    },
    {
        "legacy_id": "4",
        "event_type": "interview_unconfirmed",
        "label": "Entrevista Não Confirmada",
        "description": "Lembrete 24h antes de entrevistas sem confirmação",
        "audience": "recruiter",
        "channels": ["email", "in_app"],
        "delay_minutes": 1440,
        "schedule_lgpd_compliant": True,
        "rationale": "24h antes (1440min); both channels para garantir entrega",
        "enabled_default": True,
    },
    {
        "legacy_id": "5",
        "event_type": "interview_feedback_pending",
        "label": "Feedback Pendente",
        "description": "Solicita feedback após 48h de entrevista realizada",
        "audience": "recruiter",
        "channels": ["email"],
        "delay_minutes": 2880,
        "schedule_lgpd_compliant": True,
        "rationale": "48h após entrevista (2880min); email canonical para registro auditável",
        "enabled_default": False,
    },
    {
        "legacy_id": "6",
        "event_type": "candidate_rejected",
        "label": "Candidato Rejeitado",
        "description": "Notificação automática ao recrutador quando candidato é rejeitado",
        "audience": "recruiter",
        "channels": ["in_app"],
        "delay_minutes": 60,
        "schedule_lgpd_compliant": True,
        "rationale": "Delay canonical para revisão humana opcional antes do disparo",
        "enabled_default": True,
    },
    {
        "legacy_id": "7",
        "event_type": "ats_sync_failed",
        "label": "Falha na Sincronização ATS",
        "description": "Alerta crítico quando integração com ATS Rails falha",
        "audience": "admin",
        "channels": ["email", "in_app"],
        "delay_minutes": 0,
        "schedule_lgpd_compliant": False,
        "rationale": "Falha técnica admin-only; bypassa horário comercial (operacional 24/7)",
        "enabled_default": True,
    },
    {
        "legacy_id": "8",
        "event_type": "approval_pending",
        "label": "Aprovação Pendente",
        "description": "Notifica aprovador quando aguardando decisão há > 24h",
        "audience": "admin",
        "channels": ["email"],
        "delay_minutes": 1440,
        "schedule_lgpd_compliant": True,
        "rationale": "Aprovações são admin-flow; canonical respeitar horário comercial",
        "enabled_default": True,
    },
    {
        "legacy_id": "9",
        "event_type": "credits_low",
        "label": "Créditos Baixos",
        "description": "Avisa admin quando saldo de créditos cai abaixo de 20%",
        "audience": "admin",
        "channels": ["email", "in_app"],
        "delay_minutes": 0,
        "schedule_lgpd_compliant": True,
        "rationale": "Billing alert canonical; admin-only com canais redundantes",
        "enabled_default": True,
    },
    {
        "legacy_id": "10",
        "event_type": "candidate_application_received",
        "label": "Confirmação de Candidatura ao Candidato",
        "description": "Confirma para o candidato que sua candidatura foi recebida",
        "audience": "candidate",
        "channels": ["email"],
        "delay_minutes": 5,
        "schedule_lgpd_compliant": True,
        "rationale": "Delay 5min canonical para evitar spam burst; horário comercial respeitado (LGPD/Art.7)",
        "enabled_default": True,
    },
]


def upgrade() -> None:
    """Create table + seed 10 master items canonical."""
    op.create_table(
        "alert_rule_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("is_master_template", sa.Boolean, nullable=False, default=False, index=True),
        sa.Column(
            "parent_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alert_rule_templates.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True, index=True),
    )

    # Composite indexes canonical
    op.create_index(
        "ix_alert_rule_templates_company_master",
        "alert_rule_templates",
        ["company_id", "is_master_template"],
    )
    op.create_index(
        "ix_alert_rule_templates_active",
        "alert_rule_templates",
        ["deleted_at", "is_master_template"],
    )

    # Seed master canonical (10 items mapeados de DEFAULT_ALERTS hardcoded)
    import uuid
    import json as _json

    connection = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO alert_rule_templates
        (id, company_id, is_master_template, parent_template_id, data, created_at, updated_at, created_by, deleted_at)
        VALUES (:id, NULL, TRUE, NULL, CAST(:data AS JSONB), NOW(), NOW(), 'system-seed-2026-05-21', NULL)
        """
    )
    for item in MASTER_ITEMS:
        new_uuid = str(uuid.uuid4())
        connection.execute(
            insert_sql,
            {"id": new_uuid, "data": _json.dumps(item, ensure_ascii=False)},
        )


def downgrade() -> None:
    """Drop table — DATA LOSS de customs canonical."""
    op.drop_index("ix_alert_rule_templates_active", table_name="alert_rule_templates")
    op.drop_index("ix_alert_rule_templates_company_master", table_name="alert_rule_templates")
    op.drop_table("alert_rule_templates")
