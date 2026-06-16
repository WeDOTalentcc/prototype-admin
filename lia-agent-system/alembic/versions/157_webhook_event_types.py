"""Create webhook_event_types + seed master canonical events.

Audit 2026-05-20 Sprint 5 (catalogos dinamicos):
substitui catalogo hardcoded em frontend (`webhook-types.ts:WEBHOOK_EVENTS`)
+ backend (`app/schemas/webhook.py:ALLOWED_EVENTS`,
`libs/models/lia_models/webhook.py:WebhookEvent` enum,
`libs/models/lia_models/webhook_registration.py:JOB_STATUS_WEBHOOK_EVENTS`).

Schema canonical:
- is_master_template=True: items curados pela WeDOTalent (NULL company_id)
- is_master_template=False: customs por company (company_id NOT NULL)
- parent_template_id: NOT NULL quando custom é cópia de master (canonical A1)
- soft-delete via deleted_at

Schema do `data` JSONB (per Sprint 5 brief):
  - event_type (slug canonical, namespace.action)
  - label (display name)
  - category (candidates | jobs | interviews | offers | ats | agents | system)
  - description
  - payload_schema (JSONSchema do payload, opcional)
  - deprecated (bool)
  - metadata (dict, opcional)

Revision ID: 157_webhook_event_types
Revises: 153_eligibility_question_templates
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "157_webhook_event_types"
down_revision: Union[str, None] = "153_eligibility_question_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Master canonical events derivados de:
# 1) WebhookEvent enum (webhook.py): 7 eventos agent.* + candidate.enriched
# 2) JOB_STATUS_WEBHOOK_EVENTS (webhook_registration.py): 4 eventos job.*
# 3) Brief Sprint 5 exemplo: candidate.created (categoria candidates)
MASTER_EVENTS = [
    # ── Agents (Studio webhooks) ──────────────────────────────────────────────
    {
        "event_type": "agent.execution.completed",
        "label": "Execução de agente concluída",
        "category": "agents",
        "description": "Disparado quando um agente do Studio finaliza execução com sucesso.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "execution_id", "completed_at"],
            "properties": {
                "event": {"type": "string", "const": "agent.execution.completed"},
                "agent_id": {"type": "string", "format": "uuid"},
                "execution_id": {"type": "string", "format": "uuid"},
                "completed_at": {"type": "string", "format": "date-time"},
                "result": {"type": "object"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    {
        "event_type": "agent.execution.failed",
        "label": "Execução de agente falhou",
        "category": "agents",
        "description": "Disparado quando um agente do Studio termina com erro.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "execution_id", "failed_at", "error"],
            "properties": {
                "event": {"type": "string", "const": "agent.execution.failed"},
                "agent_id": {"type": "string", "format": "uuid"},
                "execution_id": {"type": "string", "format": "uuid"},
                "failed_at": {"type": "string", "format": "date-time"},
                "error": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    {
        "event_type": "agent.deployment.created",
        "label": "Deployment de agente criado",
        "category": "agents",
        "description": "Disparado quando um novo deployment de agente é criado.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "deployment_id", "created_at"],
            "properties": {
                "event": {"type": "string", "const": "agent.deployment.created"},
                "agent_id": {"type": "string", "format": "uuid"},
                "deployment_id": {"type": "string", "format": "uuid"},
                "created_at": {"type": "string", "format": "date-time"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    {
        "event_type": "agent.deployment.paused",
        "label": "Deployment de agente pausado",
        "category": "agents",
        "description": "Disparado quando um deployment de agente é pausado.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "deployment_id", "paused_at"],
            "properties": {
                "event": {"type": "string", "const": "agent.deployment.paused"},
                "agent_id": {"type": "string", "format": "uuid"},
                "deployment_id": {"type": "string", "format": "uuid"},
                "paused_at": {"type": "string", "format": "date-time"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    {
        "event_type": "agent.approval.requested",
        "label": "Aprovação de agente solicitada",
        "category": "agents",
        "description": "Disparado quando um agente solicita aprovação humana (HITL).",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "approval_id", "requested_at"],
            "properties": {
                "event": {"type": "string", "const": "agent.approval.requested"},
                "agent_id": {"type": "string", "format": "uuid"},
                "approval_id": {"type": "string", "format": "uuid"},
                "requested_at": {"type": "string", "format": "date-time"},
                "reason": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    {
        "event_type": "agent.approval.reviewed",
        "label": "Aprovação de agente revisada",
        "category": "agents",
        "description": "Disparado quando uma solicitação de aprovação de agente é revisada (aprovada ou rejeitada).",
        "payload_schema": {
            "type": "object",
            "required": ["event", "agent_id", "approval_id", "reviewed_at", "decision"],
            "properties": {
                "event": {"type": "string", "const": "agent.approval.reviewed"},
                "agent_id": {"type": "string", "format": "uuid"},
                "approval_id": {"type": "string", "format": "uuid"},
                "reviewed_at": {"type": "string", "format": "date-time"},
                "decision": {"type": "string", "enum": ["approved", "rejected"]},
                "reviewer_id": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    # ── Candidates ───────────────────────────────────────────────────────────
    {
        "event_type": "candidate.created",
        "label": "Candidato criado",
        "category": "candidates",
        "description": "Disparado quando candidato é criado.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "candidate_id", "created_at"],
            "properties": {
                "event": {"type": "string", "const": "candidate.created"},
                "candidate_id": {"type": "string", "format": "uuid"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "platform_core"},
    },
    {
        "event_type": "candidate.enriched",
        "label": "Candidato enriquecido",
        "category": "candidates",
        "description": "Disparado quando dados de um candidato são enriquecidos (CV parsing, LinkedIn lookup, etc).",
        "payload_schema": {
            "type": "object",
            "required": ["event", "candidate_id", "enriched_at"],
            "properties": {
                "event": {"type": "string", "const": "candidate.enriched"},
                "candidate_id": {"type": "string", "format": "uuid"},
                "enriched_at": {"type": "string", "format": "date-time"},
                "source": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "studio_webhooks"},
    },
    # ── Jobs ────────────────────────────────────────────────────────────────
    {
        "event_type": "job.created",
        "label": "Vaga criada",
        "category": "jobs",
        "description": "Disparado quando uma nova vaga é criada.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "job_id", "title", "status", "created_at"],
            "properties": {
                "event": {"type": "string", "const": "job.created"},
                "job_id": {"type": "string", "format": "uuid"},
                "title": {"type": "string"},
                "status": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "job_status_webhooks"},
    },
    {
        "event_type": "job.status_changed",
        "label": "Status de vaga alterado",
        "category": "jobs",
        "description": "Disparado quando o status de uma vaga muda.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "job_id", "old_status", "new_status", "changed_at"],
            "properties": {
                "event": {"type": "string", "const": "job.status_changed"},
                "job_id": {"type": "string", "format": "uuid"},
                "old_status": {"type": "string"},
                "new_status": {"type": "string"},
                "changed_at": {"type": "string", "format": "date-time"},
                "changed_by": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "job_status_webhooks"},
    },
    {
        "event_type": "job.published",
        "label": "Vaga publicada",
        "category": "jobs",
        "description": "Disparado quando uma vaga é publicada (vai ao ar).",
        "payload_schema": {
            "type": "object",
            "required": ["event", "job_id", "title", "published_at"],
            "properties": {
                "event": {"type": "string", "const": "job.published"},
                "job_id": {"type": "string", "format": "uuid"},
                "title": {"type": "string"},
                "published_at": {"type": "string", "format": "date-time"},
                "published_by": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "job_status_webhooks"},
    },
    {
        "event_type": "job.closed",
        "label": "Vaga encerrada",
        "category": "jobs",
        "description": "Disparado quando uma vaga é encerrada ou concluída.",
        "payload_schema": {
            "type": "object",
            "required": ["event", "job_id", "title", "final_status", "closed_at"],
            "properties": {
                "event": {"type": "string", "const": "job.closed"},
                "job_id": {"type": "string", "format": "uuid"},
                "title": {"type": "string"},
                "final_status": {"type": "string"},
                "closed_at": {"type": "string", "format": "date-time"},
                "closed_by": {"type": "string"},
            },
        },
        "deprecated": False,
        "metadata": {"source": "job_status_webhooks"},
    },
]


def upgrade() -> None:
    """Create table + seed master canonical events."""
    op.create_table(
        "webhook_event_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column(
            "is_master_template",
            sa.Boolean,
            nullable=False,
            default=False,
            index=True,
        ),
        sa.Column(
            "parent_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("webhook_event_types.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True, index=True),
    )

    # Composite indexes canonical
    op.create_index(
        "ix_webhook_event_types_company_master",
        "webhook_event_types",
        ["company_id", "is_master_template"],
    )
    op.create_index(
        "ix_webhook_event_types_active",
        "webhook_event_types",
        ["deleted_at", "is_master_template"],
    )

    # Seed master canonical (events curados WeDOTalent)
    import uuid
    import json as _json

    connection = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO webhook_event_types
        (id, company_id, is_master_template, parent_template_id, data, created_at, updated_at, created_by, deleted_at)
        VALUES (:id, NULL, TRUE, NULL, CAST(:data AS JSONB), NOW(), NOW(), 'system-seed-2026-05-21', NULL)
        """
    )
    for item in MASTER_EVENTS:
        new_uuid = str(uuid.uuid4())
        connection.execute(
            insert_sql,
            {"id": new_uuid, "data": _json.dumps(item, ensure_ascii=False)},
        )


def downgrade() -> None:
    """Drop table — DATA LOSS de customs canonical."""
    op.drop_index("ix_webhook_event_types_active", table_name="webhook_event_types")
    op.drop_index(
        "ix_webhook_event_types_company_master", table_name="webhook_event_types"
    )
    op.drop_table("webhook_event_types")
