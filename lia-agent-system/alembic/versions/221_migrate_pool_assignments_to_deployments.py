"""C1.5.1 — data migration: pool_agent_assignments -> agent_deployments.

Revision ID: 221
Revises: 220
Create Date: 2026-05-29

Context (Fase 2.5 Onda C1.5 — Opção A canonical):
  agent_deployments é a junction canonical agente<->surface (job / talent_pool /
  pipeline_stage / candidate_list). A tabela legada pool_agent_assignments cobre
  só talent_pool. Esta migration COPIA cada assignment -> deployment equivalente
  (target_type='talent_pool') e VINCULA os runs históricos (pool_agent_runs.
  deployment_id) — fechando o backfill que a migration 218 (C1.4) deixou pendente.

DECISÃO DE INTEGRIDADE (registrada 2026-05-29):
  agent_deployments.company_id tem FK -> companies.id (ON DELETE CASCADE, migration
  219 / C2.1). pool_agent_assignments NÃO tem essa FK, então pode conter company_id
  que não existe em companies (fixtures de teste do Sprint 7C: prefixo 'test-7c-*').
  Inserir esses fixtures violaria a FK e abortaria a migration inteira.

  Canonical-fix + multi-tenancy fail-closed: SÓ migramos assignments cujo company_id
  EXISTE em companies. Criar um deployment apontando pra um tenant inexistente seria
  lixo de integridade. Assignments órfãos (sem company real) são CONTADOS e LOGADOS,
  não migrados. Quando assignments de produção reais (com company real) existirem,
  serão migrados normalmente — o filtro é por integridade, não por origem.

  Estado dev em 2026-05-29: 32 assignments, TODAS fixtures (0 com company real,
  todas on_demand/active). Logo esta migration migra 0 rows em dev — comportamento
  correto e documentado. Em prod, migra as reais.

MAPEAMENTO schedule_type -> trigger_mode:
  on_demand    -> manual          (canonical talent_pool)
  cron         -> scheduled       (legacy alias de on_schedule; aceito pelo CHECK
                                    ck_agent_deployments_trigger_mode E escaneado por
                                    scan_agent_deployment_cron_schedules)
  event_driven -> on_new_candidate (legacy alias de on_create; aceito pelo CHECK)

  NOTA: usamos os aliases LEGACY (scheduled/on_new_candidate) e NÃO os canonical
  (on_schedule/on_create) porque o CHECK ck_agent_deployments_trigger_mode ainda só
  aceita o enum legado {manual,on_new_candidate,on_stage_change,scheduled}. Quando
  C2/Onda futura ampliar o CHECK pros nomes canonical, uma migration de dados pode
  renomear. Ambos os aliases são reconhecidos por app/shared/trigger_mode_validation
  (LEGACY_TRIGGER_MODES) e pelo scheduler.

IDEMPOTÊNCIA:
  INSERT ... ON CONFLICT (agent_id, target_type, target_id) DO NOTHING
  (constraint uq_agent_deployment_agent_target). Rodar 2x não duplica.

RLS: a migration roda como owner (postgres, superuser -> BYPASSRLS), então o
  FORCE ROW LEVEL SECURITY de agent_deployments não bloqueia o INSERT.

Refs:
  - AGENT_STUDIO_FASE2.5_PLANO_CONSOLIDACAO.md §Onda C1.5
  - alembic/versions/218_pool_agent_runs_cross_target.py (C1.4 — pendência backfill)
  - alembic/versions/219_fk_agent_studio_tenant_tables.py (FK company_id)
  - app/shared/trigger_mode_validation.py (matriz canonical + LEGACY_TRIGGER_MODES)
"""
from alembic import op

revision = "221"
down_revision = "220"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # -------------------------------------------------------------------------
    # 1) INSERT deployments equivalentes — só pra assignments com company REAL.
    #    Idempotente via ON CONFLICT no unique (agent_id, target_type, target_id).
    # -------------------------------------------------------------------------
    insert_sql = """
        INSERT INTO agent_deployments (
            id, agent_id, company_id,
            target_type, target_id, target_name,
            trigger_mode, schedule_cron,
            is_active, config_overrides,
            execution_count, candidates_processed,
            created_by, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            a.custom_agent_id,
            a.company_id,
            'talent_pool',
            a.talent_pool_id,
            tp.name,
            CASE a.schedule_type
                WHEN 'cron'         THEN 'scheduled'
                WHEN 'event_driven' THEN 'on_new_candidate'
                ELSE 'manual'
            END,
            NULLIF(a.schedule_config->>'cron', ''),
            (a.status = 'active'),
            COALESCE(a.config_overrides, '{}'::jsonb),
            0,
            0,
            a.created_by,
            a.created_at,
            a.updated_at
        FROM pool_agent_assignments a
        JOIN companies c ON c.id = a.company_id
        LEFT JOIN talent_pools tp ON tp.id = a.talent_pool_id
        ON CONFLICT (agent_id, target_type, target_id) DO NOTHING
    """
    res = bind.exec_driver_sql(insert_sql)
    inserted = res.rowcount if res.rowcount is not None else -1

    # -------------------------------------------------------------------------
    # 2) Backfill pool_agent_runs.deployment_id dos runs históricos cujos
    #    assignments foram migrados. Preserva o histórico (last_execution_id passa
    #    a funcionar pro deployment). Só vincula runs ainda sem deployment_id.
    # -------------------------------------------------------------------------
    backfill_sql = """
        UPDATE pool_agent_runs r
        SET deployment_id = d.id
        FROM pool_agent_assignments a
        JOIN agent_deployments d
          ON d.agent_id = a.custom_agent_id
         AND d.target_type = 'talent_pool'
         AND d.target_id = a.talent_pool_id
        WHERE r.assignment_id = a.id
          AND r.deployment_id IS NULL
    """
    res2 = bind.exec_driver_sql(backfill_sql)
    linked = res2.rowcount if res2.rowcount is not None else -1

    # -------------------------------------------------------------------------
    # 3) Contagem de órfãos (company inexistente) — LOG, não falha (REGRA 4: é um
    #    estado conhecido/documentado, não um erro silencioso).
    # -------------------------------------------------------------------------
    orphans = bind.exec_driver_sql(
        """
        SELECT count(*) FROM pool_agent_assignments a
        WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.id = a.company_id)
        """
    ).scalar()

    print(
        f"[migration 221] deployments inseridos={inserted} | "
        f"runs vinculados={linked} | "
        f"assignments orfaos (company inexistente, NAO migrados)={orphans}"
    )

    # -------------------------------------------------------------------------
    # 4) Validação fail-closed: todo assignment ATIVO com company REAL tem
    #    deployment correspondente. Se faltar algum, a migration aborta (REGRA 4).
    # -------------------------------------------------------------------------
    missing = bind.exec_driver_sql(
        """
        SELECT count(*) FROM pool_agent_assignments a
        JOIN companies c ON c.id = a.company_id
        WHERE a.status = 'active'
          AND NOT EXISTS (
              SELECT 1 FROM agent_deployments d
              WHERE d.agent_id = a.custom_agent_id
                AND d.target_type = 'talent_pool'
                AND d.target_id = a.talent_pool_id
          )
        """
    ).scalar()
    if missing and missing > 0:
        raise RuntimeError(
            f"[migration 221] FALHA: {missing} assignment(s) ativo(s) com company "
            f"real ficaram sem deployment correspondente. Migration abortada "
            f"(fail-closed)."
        )


def downgrade() -> None:
    bind = op.get_bind()
    # Desvincular runs que apontavam pros deployments migrados de talent_pool, e
    # remover os deployments criados por esta migration. Heurística canonical: um
    # deployment é "migrado" quando existe um assignment com o mesmo
    # (agent, talent_pool). A CHECK chk_par_source_present garante que esses runs
    # ainda têm assignment_id (nunca ficam órfãos após o UPDATE).
    bind.exec_driver_sql(
        """
        UPDATE pool_agent_runs r
        SET deployment_id = NULL
        FROM agent_deployments d
        JOIN pool_agent_assignments a
          ON a.custom_agent_id = d.agent_id
         AND a.talent_pool_id = d.target_id
        WHERE r.deployment_id = d.id
          AND d.target_type = 'talent_pool'
          AND r.assignment_id IS NOT NULL
        """
    )
    bind.exec_driver_sql(
        """
        DELETE FROM agent_deployments d
        USING pool_agent_assignments a
        WHERE d.target_type = 'talent_pool'
          AND d.agent_id = a.custom_agent_id
          AND d.target_id = a.talent_pool_id
        """
    )
