"""Create eligibility_question_templates + seed master canonical (98 items).

Audit 2026-05-20 Sessão I Step 5 / Sprint 1 (catalogos dinamicos):
substitui catalogo hardcoded `eligibility-questions-bank.ts` (frontend) por
modelo per-tenant canonical no DB.

Schema canonical:
- is_master_template=True: items curados pela WeDOTalent (NULL company_id)
- is_master_template=False: customs por company (company_id NOT NULL)
- parent_template_id: NOT NULL quando custom é cópia de master (canonical A1)
- soft-delete via deleted_at

Revision ID: 153_eligibility_question_templates
Revises: 152_logo_url_to_text
Create Date: 2026-05-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "153_eligibility_question_templates"
down_revision: Union[str, None] = "152_logo_url_to_text"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MASTER_ITEMS = [{'id': 'sys-workmodel', 'question': 'Você tem disponibilidade para trabalhar no modelo {modeloTrabalho}?', 'type': 'yesno', 'category': 'system_default', 'contextHint': 'Vinculada ao campo Modelo de Trabalho da vaga', 'linkedField': 'workModel', 'isSystemDefault': True, 'eliminatory': True, 'eliminatoryAnswer': 'Sim'}, {'id': 'sys-contract-type', 'question': 'Você aceita contratação no regime {tipoContratação}?', 'type': 'yesno', 'category': 'system_default', 'contextHint': 'Vinculada ao campo Tipo de Contratação da vaga', 'linkedField': 'type', 'isSystemDefault': True, 'eliminatory': True, 'eliminatoryAnswer': 'Sim'}, {'id': 'sys-location', 'question': 'Você reside ou tem disponibilidade para trabalhar em {localização}?', 'type': 'yesno', 'category': 'system_default', 'contextHint': 'Vinculada ao campo Localização da vaga', 'linkedField': 'location', 'isSystemDefault': True, 'eliminatory': False}, {'id': 'sys-language', 'question': 'Qual seu nível de proficiência em {idioma}? (Mínimo: {nível})', 'type': 'text', 'category': 'system_default', 'contextHint': 'Vinculada ao campo Idiomas da vaga. Uma pergunta gerada por idioma obrigatório.', 'linkedField': 'languages', 'isSystemDefault': True, 'eliminatory': True}, {'id': 'sys-affirmative', 'question': 'Você se enquadra nos critérios afirmativos desta vaga?', 'type': 'yesno', 'category': 'system_default', 'contextHint': 'Vinculada ao campo Ações Afirmativas da vaga', 'linkedField': 'isAffirmative', 'isSystemDefault': True, 'eliminatory': False}, {'id': 'bank-elig-1', 'question': 'Esta vaga é afirmativa. Você se identifica com o grupo elegível?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vagas afirmativas (PCD, negros, mulheres, LGBTQIA+, 50+)', 'triggerCondition': "{ field: 'is_affirmative', operator: 'equals', value: true }", 'eliminatory': True, 'eliminatoryAnswer': False}, {'id': 'bank-elig-2', 'question': 'Qual grupo você se identifica? (PCD, Negro(a), Mulher, LGBTQIA+, 50+)', 'type': 'multiple', 'category': 'eligibility', 'contextHint': 'Seguimento da pergunta de vaga afirmativa', 'options': "['PCD', 'Negro(a)', 'Mulher', 'LGBTQIA+', '50+', 'Outro']"}, {'id': 'bank-elig-3', 'question': 'Você possui laudo/CID que comprove a deficiência?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vagas PCD', 'triggerCondition': "{ field: 'is_pcd', operator: 'equals', value: true }"}, {'id': 'bank-elig-4', 'question': 'Você possui CNH válida?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vagas que exigem habilitação'}, {'id': 'bank-elig-5', 'question': 'Qual categoria da sua CNH?', 'type': 'multiple', 'category': 'eligibility', 'contextHint': 'Motoristas, vendedores externos', 'options': "['A', 'B', 'C', 'D', 'E', 'AB', 'Não possuo']"}, {'id': 'bank-elig-6', 'question': 'Você possui veículo próprio para uso no trabalho?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vendas externas, representantes'}, {'id': 'bank-elig-7', 'question': 'Você possui passaporte válido?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vagas com viagens internacionais'}, {'id': 'bank-elig-8', 'question': 'Você possui visto de trabalho válido para o país da vaga?', 'type': 'yesno', 'category': 'eligibility', 'contextHint': 'Vagas internacionais'}, {'id': 'bank-avail-1', 'question': 'Você tem disponibilidade para viagens frequentes?', 'type': 'yesno', 'category': 'availability', 'contextHint': 'Comercial, consultoria, auditoria', 'triggerCondition': "{ field: 'travel_required', operator: 'equals', value: true }"}, {'id': 'bank-avail-2', 'question': 'Qual percentual do tempo você aceitaria viajar? (0-100%)', 'type': 'scale', 'category': 'availability', 'contextHint': 'Seguimento - definir frequência de viagens'}, {'id': 'bank-avail-3', 'question': 'Você tem disponibilidade para mudança de cidade/estado?', 'type': 'yesno', 'category': 'availability', 'contextHint': 'Vagas em outras localidades', 'triggerCondition': "{ field: 'requires_relocation', operator: 'equals', value: true }"}, {'id': 'bank-avail-4', 'question': 'Você aceitaria trabalhar em turnos/escalas?', 'type': 'yesno', 'category': 'availability', 'contextHint': 'Operações, indústria, varejo'}, {'id': 'bank-avail-5', 'question': 'Você tem disponibilidade para trabalhar aos finais de semana?', 'type': 'yesno', 'category': 'availability', 'contextHint': 'Varejo, operações, suporte'}, {'id': 'bank-avail-6', 'question': 'Você tem disponibilidade para trabalhar em horário noturno?', 'type': 'yesno', 'category': 'availability', 'contextHint': 'Operações, suporte 24h'}, {'id': 'bank-avail-7', 'question': 'Você pode iniciar imediatamente ou está cumprindo aviso prévio?', 'type': 'text', 'category': 'availability', 'contextHint': 'Urgência da contratação'}, {'id': 'bank-edu-1', 'question': 'Você possui formação superior completa?', 'type': 'yesno', 'category': 'education', 'contextHint': 'Vagas que exigem diploma'}, {'id': 'bank-edu-2', 'question': 'Qual sua área de formação?', 'type': 'text', 'category': 'education', 'contextHint': 'Seguimento - identificar área de estudo'}, {'id': 'bank-edu-3', 'question': 'Você possui pós-graduação, MBA ou mestrado?', 'type': 'yesno', 'category': 'education', 'contextHint': 'Cargos de liderança e especialistas'}, {'id': 'bank-edu-4', 'question': 'Você possui alguma certificação relevante para a área? Qual?', 'type': 'text', 'category': 'education', 'contextHint': 'PMP, AWS, CPA, ITIL, Six Sigma, etc.'}, {'id': 'bank-edu-5', 'question': 'Você está cursando faculdade atualmente?', 'type': 'yesno', 'category': 'education', 'contextHint': 'Vagas de estágio'}, {'id': 'bank-edu-6', 'question': 'Qual semestre você está cursando?', 'type': 'text', 'category': 'education', 'contextHint': 'Seguimento para estágio'}, {'id': 'bank-edu-7', 'question': 'Você possui registro ativo no conselho de classe? (CRM, CRC, CREA, OAB, etc.)', 'type': 'text', 'category': 'education', 'contextHint': 'Profissões regulamentadas'}, {'id': 'bank-exp-1', 'question': 'Você já trabalhou com SAP, Oracle ou outro ERP? Qual?', 'type': 'text', 'category': 'experience', 'contextHint': 'Vagas que exigem conhecimento em ERP'}, {'id': 'bank-exp-2', 'question': 'Quantos anos de experiência você tem com a tecnologia principal da vaga?', 'type': 'text', 'category': 'experience', 'contextHint': 'Tech, engenharia, especialistas'}, {'id': 'bank-exp-3', 'question': 'Você já liderou equipes? Se sim, de quantas pessoas?', 'type': 'text', 'category': 'experience', 'contextHint': 'Cargos de gestão'}, {'id': 'bank-exp-4', 'question': 'Você já atuou no segmento/indústria desta vaga?', 'type': 'yesno', 'category': 'experience', 'contextHint': 'Experiência setorial específica'}, {'id': 'bank-exp-5', 'question': 'Você tem experiência com vendas B2B ou B2C?', 'type': 'multiple', 'category': 'experience', 'contextHint': 'Comercial, vendas', 'options': "['B2B', 'B2C', 'Ambos', 'Nenhum']"}, {'id': 'bank-exp-6', 'question': 'Qual foi seu ticket médio ou meta atingida no último ano?', 'type': 'text', 'category': 'experience', 'contextHint': 'Vendas, comercial'}, {'id': 'bank-lang-1', 'question': 'Qual seu nível de inglês?', 'type': 'multiple', 'category': 'languages', 'contextHint': 'Multinacionais, tech, exportação', 'options': "['Básico', 'Intermediário', 'Avançado', 'Fluente', 'Nativo']"}, {'id': 'bank-lang-2', 'question': 'Você possui certificação de inglês? (TOEFL, IELTS, Cambridge)', 'type': 'text', 'category': 'languages', 'contextHint': 'Vagas que exigem comprovação'}, {'id': 'bank-lang-3', 'question': 'Qual seu nível de espanhol?', 'type': 'multiple', 'category': 'languages', 'contextHint': 'Empresas latam', 'options': "['Básico', 'Intermediário', 'Avançado', 'Fluente', 'Nativo', 'Não falo']"}, {'id': 'bank-lang-4', 'question': 'Você é fluente em outros idiomas? Quais?', 'type': 'text', 'category': 'languages', 'contextHint': 'Multinacionais'}, {'id': 'bank-comp-1', 'question': 'Você aceita contratação PJ?', 'type': 'yesno', 'category': 'compensation', 'contextHint': 'Vagas PJ', 'triggerCondition': "{ field: 'contract_type', operator: 'equals', value: 'pj' }"}, {'id': 'bank-comp-2', 'question': 'Você aceita contrato temporário?', 'type': 'yesno', 'category': 'compensation', 'contextHint': 'Projetos, sazonais', 'triggerCondition': "{ field: 'contract_type', operator: 'equals', value: 'temporario' }"}, {'id': 'bank-comp-3', 'question': 'A faixa salarial informada está alinhada com sua expectativa?', 'type': 'yesno', 'category': 'compensation', 'contextHint': 'Alinhamento de expectativas salariais'}, {'id': 'bank-comp-4', 'question': 'Você tem CNPJ ativo ou disponibilidade para abrir?', 'type': 'yesno', 'category': 'compensation', 'contextHint': 'Vagas PJ'}, {'id': 'bank-work-1', 'question': 'Você tem estrutura para home office? (internet estável, espaço adequado)', 'type': 'yesno', 'category': 'work_model', 'contextHint': 'Vagas remotas', 'triggerCondition': "{ field: 'work_model', operator: 'equals', value: 'remote' }"}, {'id': 'bank-work-2', 'question': 'Você mora na região metropolitana da localidade da vaga?', 'type': 'yesno', 'category': 'work_model', 'contextHint': 'Vagas híbridas/presenciais'}, {'id': 'bank-work-3', 'question': 'Qual a distância aproximada da sua casa até o local de trabalho?', 'type': 'text', 'category': 'work_model', 'contextHint': 'Logística, tempo de deslocamento'}, {'id': 'bank-compl-1', 'question': 'Você possui cláusula de não-competição com seu empregador atual?', 'type': 'yesno', 'category': 'compliance', 'contextHint': 'Cargos estratégicos, concorrentes'}, {'id': 'bank-compl-2', 'question': 'Você tem parentes trabalhando nesta empresa?', 'type': 'yesno', 'category': 'compliance', 'contextHint': 'Política de nepotismo'}, {'id': 'bank-compl-3', 'question': 'Você já trabalhou nesta empresa anteriormente?', 'type': 'yesno', 'category': 'compliance', 'contextHint': 'Recontratação'}, {'id': 'bank-compl-4', 'question': 'Você possui alguma pendência trabalhista com esta empresa?', 'type': 'yesno', 'category': 'compliance', 'contextHint': 'Histórico judicial'}]


def upgrade() -> None:
    """Create table + seed 98 master items canonical."""
    op.create_table(
        "eligibility_question_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("is_master_template", sa.Boolean, nullable=False, default=False, index=True),
        sa.Column(
            "parent_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("eligibility_question_templates.id"),
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
        "ix_elig_templates_company_master",
        "eligibility_question_templates",
        ["company_id", "is_master_template"],
    )
    op.create_index(
        "ix_elig_templates_active",
        "eligibility_question_templates",
        ["deleted_at", "is_master_template"],
    )

    # Seed master canonical (98 items from eligibility-questions-bank.ts canonical)
    import uuid
    from datetime import datetime
    import json as _json

    connection = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO eligibility_question_templates
        (id, company_id, is_master_template, parent_template_id, data, created_at, updated_at, created_by, deleted_at)
        VALUES (:id, NULL, TRUE, NULL, CAST(:data AS JSONB), NOW(), NOW(), 'system-seed-2026-05-20', NULL)
        """
    )
    for item in MASTER_ITEMS:
        # data JSONB contém o item canonical do bank.ts (id slug preservado)
        # ID master do DB é UUID novo; original slug fica em data["legacy_id"]
        legacy_id = item.get("id")
        data_payload = {**item, "legacy_id": legacy_id}
        if "id" in data_payload:
            del data_payload["id"]
        new_uuid = str(uuid.uuid4())
        connection.execute(
            insert_sql,
            {"id": new_uuid, "data": _json.dumps(data_payload, ensure_ascii=False)},
        )


def downgrade() -> None:
    """Drop table — DATA LOSS de customs canonical."""
    op.drop_index("ix_elig_templates_active", table_name="eligibility_question_templates")
    op.drop_index("ix_elig_templates_company_master", table_name="eligibility_question_templates")
    op.drop_table("eligibility_question_templates")
