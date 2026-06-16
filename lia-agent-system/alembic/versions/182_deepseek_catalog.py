"""W2-011 · seed DeepSeek master template em integration_catalog_entries

Revision ID: 182_deepseek_catalog
Revises: 181_idempotency_keys
Create Date: 2026-05-23

W2-011 do MASTER_PLAN.md de remediação enterprise.
Tests: tests/unit/test_w2011_deepseek_provider_wire.py
Sensor: scripts/check_deepseek_provider_wired.py

Insere master template (is_master_template=true, company_id=NULL) para
DeepSeek em integration_catalog_entries. Frontend lê dinâmicamente via
GET /api/backend-proxy/integration-catalog e mostra card opt-in.

DeepSeek é OpenAI-compatible (https://api.deepseek.com/v1):
- Provider class: app/shared/providers/llm_deepseek.py
- BYOK form: config_fields=["DEEPSEEK_API_KEY"]
- Status: production (opt-in only — não entra em FALLBACK_ORDER default)
- Models: deepseek-chat (V3) + deepseek-reasoner (R1)

LGPD nota: DeepSeek runs em China (Hangzhou). Provider não expõe header
de data-residency. Cliente que opta aceita ausência de region pinning.
"""
from alembic import op
import sqlalchemy as sa
import json
import uuid
from datetime import datetime


revision = "182_deepseek_catalog"
down_revision = "181_idempotency_keys"
branch_labels = None
depends_on = None


DEEPSEEK_CATALOG_DATA = {
    "label": "DeepSeek",
    "status": "production",
    "category": "ai_models",
    "logo_url": None,
    "metadata": {
        "icon_bg": "bg-blue-500/10",
        "icon_color": "text-blue-600 dark:text-blue-400",
        "icon_letter": "D",
        "capabilities": [
            {
                "name": "Chat & Reasoning",
                "description": "DeepSeek-V3 (chat) e DeepSeek-R1 (reasoning).",
            },
            {
                "name": "Function Calling",
                "description": "Integração com ferramentas da plataforma (compatível OpenAI).",
            },
            {
                "name": "Screening de Candidatos",
                "description": "Análise estruturada de respostas em triagem.",
            },
            {
                "name": "Custo Reduzido",
                "description": "Alternativa econômica vs OpenAI/Claude para workloads compatíveis.",
            },
        ],
        "config_fields": ["DEEPSEEK_API_KEY"],
        "connect_action": "config",
        "is_active_provider": False,
        "opt_in_only": True,
        "data_residency_warning": (
            "DeepSeek opera em data centers na China. Não há suporte a region "
            "pinning (LGPD Art 33). Avaliar antes de ativar para dados sensíveis."
        ),
    },
    "provider": "deepseek",
    "description": "Provedor de IA OpenAI-compatible com custo reduzido (opt-in)",
    "full_description": (
        "DeepSeek é um provedor de IA OpenAI-compatible que oferece DeepSeek-V3 "
        "(general-purpose chat) e DeepSeek-R1 (reasoning model). Não entra na cadeia "
        "de fallback default da LIA — ativação é opt-in por tenant via configuração "
        "BYOK. Útil como alternativa econômica para workloads de chat/screening que "
        "não exigem region pinning ou data-residency BR/EU. Atenção: dados trafegados "
        "vão para data centers da China; avaliar adequação ao tratamento de dados "
        "sensíveis antes de ativar."
    ),
    "industries_recommended": [],
}


def upgrade():
    bind = op.get_bind()
    # Verifica se já existe (idempotency)
    existing = bind.execute(
        sa.text(
            "SELECT id FROM integration_catalog_entries "
            "WHERE is_master_template=true AND data->>'provider'='deepseek'"
        )
    ).first()
    if existing:
        return  # noop — já populado

    bind.execute(
        sa.text(
            "INSERT INTO integration_catalog_entries "
            "(id, company_id, is_master_template, parent_template_id, "
            "data, created_at, updated_at, created_by, deleted_at) "
            "VALUES (:id, 'demo_company', true, NULL, CAST(:data AS jsonb), "
            ":ts, :ts, :creator, NULL)"
        ),
        {
            "id": str(uuid.uuid4()),
            "data": json.dumps(DEEPSEEK_CATALOG_DATA, ensure_ascii=False),
            "ts": datetime.utcnow(),
            "creator": "system:migration:182_deepseek_catalog",
        },
    )


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM integration_catalog_entries "
            "WHERE is_master_template=true AND data->>'provider'='deepseek'"
        )
    )
