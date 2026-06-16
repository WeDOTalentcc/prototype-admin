
from fastapi import Request

"""
Database setup and session management.

Core session management (engine, Base, AsyncSessionLocal, get_db) moved to
libs/config (lia_config.database). Migration helpers remain here.
"""
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sqlalchemy as sa

# Core session management — real implementation in libs/config
from lia_config.database import (  # noqa: F401
    AsyncSessionLocal,
    Base,
    async_session_factory,
    engine,
    get_db,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def set_tenant_context(db: AsyncSession, company_id: str) -> None:
    """Inject company_id into the PostgreSQL session for RLS policies.

    Behavior:
        - Issues `SET LOCAL app.company_id = :cid` via set_config(is_local=true).
        - Records company_id in db.info["company_id"] so commit_keeping_tenant
          can re-inject after explicit commit() calls (since is_local=true is
          transaction-scoped).

    Canonical contract:
        - Called once at session setup by get_tenant_db.
        - Called again by commit_keeping_tenant after each commit().
        - Direct callers (rare) should prefer commit_keeping_tenant.

    See ADR-RLS-002 (pending) + commit 996f50d9 (V4 anti-pattern) +
    V5 commit (this canonical fix).
    """
    try:
        await db.execute(
            sa.text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": str(company_id)},
        )
        # Persist for after-commit re-injection.
        db.info["company_id"] = str(company_id)
    except Exception as exc:
        logger.warning("[RLS] Falha ao definir company_id na sessão: %s", exc)


async def commit_keeping_tenant(db: AsyncSession) -> None:
    """Canonical commit helper for handlers that read after commit.

    Problem this solves:
        set_config('app.company_id', :cid, true) is TRANSACTION-scoped
        (is_local=true). An explicit `await db.commit()` in a handler ends
        the current transaction. The next implicit transaction loses
        app.company_id, so app_current_company_id() returns NULL, and the
        RLS SELECT policy `company_id = app_current_company_id()` blocks
        any subsequent read on the same session. SQLAlchemy surfaces this
        as `InvalidRequestError: Could not refresh instance` — the row
        exists but is invisible to the now-tenant-less session.

    Canonical usage:
        # ❌ ANTI-PATTERN (commit 996f50d9 surfaced this):
        await db.commit()
        await db.refresh(obj)  # may fail: row invisible to new tx

        # ✅ CANONICAL (this V5 commit):
        from app.core.database import commit_keeping_tenant
        await commit_keeping_tenant(db)
        await db.refresh(obj)  # safe: tenant context restored

    Requires:
        set_tenant_context was called earlier on the same session
        (populates db.info["company_id"]). If not, this helper degrades
        gracefully to a plain commit() — no-op for sessions that don't
        carry tenant context (e.g., system tables, admin scripts).

    See ADR-RLS-002 (pending) for the full architectural rationale.
    """
    await db.commit()
    cid = db.info.get("company_id")
    if cid:
        try:
            await db.execute(
                sa.text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": str(cid)},
            )
        except Exception as exc:
            logger.warning(
                "[RLS] Falha ao re-injetar company_id após commit: %s", exc,
            )


async def get_tenant_db(request: "Request") -> AsyncGenerator[AsyncSession, None]:
    """
    Tenant-aware DB dependency: injects company_id into PostgreSQL session
    so that RLS policies enforce tenant isolation automatically.

    Uses company_id from request.state (set by AuthEnforcementMiddleware).

    Usage:
        @app.get("/items")
        async def get_items(
            request: Request,
            db: AsyncSession = Depends(get_tenant_db),
        ):
            # All queries are automatically scoped to the user's tenant
            ...
    """
    async with AsyncSessionLocal() as session:
        _role_set = False
        try:
            try:
                await session.execute(sa.text("SET ROLE lia_app"))
                _role_set = True
            except Exception as role_err:
                logger.error("[RLS] SET ROLE lia_app failed in get_tenant_db: %s — request blocked", role_err)
                raise RuntimeError("RLS role enforcement failed") from role_err
            company_id = getattr(request.state, "company_id", None)
            if company_id:
                await set_tenant_context(session, company_id)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if _role_set:
                try:
                    await session.execute(sa.text("RESET ROLE"))
                except Exception:
                    pass
            await session.close()

async def add_task_lifecycle_columns():
    """
    Add task lifecycle columns if they don't exist.
    Uses PostgreSQL's ADD COLUMN IF NOT EXISTS syntax.
    """
    columns_to_add = [
        ("confirmed_by", "VARCHAR"),
        ("confirmed_at", "TIMESTAMP"),
        ("rejected_by", "VARCHAR"),
        ("rejected_at", "TIMESTAMP"),
        ("rejection_reason", "TEXT"),
        ("escalated_to", "VARCHAR"),
        ("escalated_at", "TIMESTAMP"),
        ("escalation_reason", "TEXT"),
        ("escalation_level", "INTEGER DEFAULT 0"),
        ("reminder_sent", "BOOLEAN DEFAULT FALSE"),
        ("reminder_count", "INTEGER DEFAULT 0"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE tasks ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column tasks.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add column {column_name}: {e}")
    
    logger.info("Task lifecycle columns verified/added successfully")


async def add_notification_columns():
    """
    Add notification table columns if they don't exist.
    Uses PostgreSQL's ADD COLUMN IF NOT EXISTS syntax.
    """
    notification_columns = [
        ("proactive_type", "VARCHAR(50)"),
        ("priority", "VARCHAR(20) DEFAULT 'normal'"),
        ("channels_sent", "JSON DEFAULT '[]'::json"),
    ]
    
    chat_notification_columns = [
        ("proactive_type", "VARCHAR(50)"),
        ("priority", "VARCHAR(20) DEFAULT 'normal'"),
        ("thread_id", "VARCHAR"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in notification_columns:
            try:
                await conn.execute(
                    text(f"ALTER TABLE notifications ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column notifications.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add notifications column {column_name}: {e}")
        
        for column_name, column_type in chat_notification_columns:
            try:
                await conn.execute(
                    text(f"ALTER TABLE chat_notifications ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column chat_notifications.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add chat_notifications column {column_name}: {e}")
    
    logger.info("Notification columns verified/added successfully")


async def add_approval_workflow_columns():
    """
    Add approval workflow columns to job_vacancies table if they don't exist.
    """
    columns_to_add = [
        ("approval_requested_at", "TIMESTAMP"),
        ("approval_requested_by", "VARCHAR(255)"),
        ("approved_by", "VARCHAR(255)"),
        ("approved_at", "TIMESTAMP"),
        ("rejection_reason", "TEXT"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column job_vacancies.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add job_vacancies column {column_name}: {e}")
    
    logger.info("Approval workflow columns verified/added successfully")


async def ensure_default_company():
    """Ensure the canonical Demo Company row exists with rich metadata.

    Task #969 / T-C: this used to inline `CREATE TABLE IF NOT EXISTS
    companies` and INSERT a `demo_company` slug row on every boot
    (canonical-fix anti-pattern #7 — schema-as-runtime). It re-created
    the legacy slug row that Alembic migration 080 had just removed,
    re-introducing the cross-row tenant split documented in #969.

    The fix:
    - The schema lives in Alembic (`127_enrich_companies_schema` plus
      every prior migration that touches `companies`). If the table is
      missing here, that is a deployment bug and we want to surface it,
      not paper over it.
    - The seed lives in `scripts/seeds/demo_company.py` (idempotent
      UPSERT at the canonical UUID with concrete sector/plan/timezone).
    - This function only invokes the seed; it never DDLs and never
      touches the legacy slug literal.
    """
    try:
        from scripts.seeds.demo_company import (
            seed_demo_company,
            CANONICAL_DEMO_UUID,
        )
    except Exception as exc:  # pragma: no cover — import-time misconfiguration
        # pii-logs ok: nome de modulo nao e PII per LGPD Art.5 V.
        logger.warning(
            "Could not import canonical Demo Company seed (%s); "
            "skipping default-company bootstrap. Run "
            "`scripts/migrate_demo_company_consolidation.py` manually.",
            exc,
        )
        return

    async with engine.begin() as conn:
        try:
            await seed_demo_company(conn)
            # pii-logs ok: tenant id nao e PII per LGPD Art.5 V.
            logger.info(
                "Default company verified/created at canonical UUID %s",
                CANONICAL_DEMO_UUID,
            )
        except Exception as exc:
            # pii-logs ok: tenant id nao e PII per LGPD Art.5 V.
            logger.warning(
                "Could not upsert canonical Demo Company (id=%s): %s",
                CANONICAL_DEMO_UUID, exc,
            )


async def migrate_default_company_ids():
    """
    Migrate legacy 'default' company_id values to 'demo_company'.
    This is a data hygiene operation to ensure all records have valid company references.
    
    Updates the following tables:
    - users
    - job_vacancies
    - vacancy_candidates

    Task #969 / T-C: target id is now the canonical Demo Company UUID
    instead of the legacy `demo_company` slug literal — keeps this code
    aligned with `ensure_default_company` and migration 080.
    """
    from scripts.seeds.demo_company import CANONICAL_DEMO_UUID

    tables_to_update = ["users", "job_vacancies", "vacancy_candidates"]

    async with engine.begin() as conn:
        for table_name in tables_to_update:
            try:
                result = await conn.execute(text(f"""
                    UPDATE {table_name}
                    SET company_id = :canonical
                    WHERE company_id = 'default'
                """), {"canonical": CANONICAL_DEMO_UUID})
                if result.rowcount > 0:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"Migrated {result.rowcount} records in {table_name} from 'default' to canonical Demo Company UUID")
                else:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.debug(f"No records to migrate in {table_name}")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not migrate company_id in {table_name}: {e}")
    
    logger.info("Company ID migration completed")


async def create_audit_logs_table():
    """
    Create the audit_logs table for AI governance and explainability.
    
    This table tracks all AI decisions made by LIA agents, including:
    - What decision was made and by which agent
    - The reasoning behind each decision
    - Criteria used and explicitly ignored (for anti-bias compliance)
    - Human review and override tracking
    - LGPD-compliant retention periods
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id VARCHAR(255) PRIMARY KEY,
                    company_id VARCHAR(255) NOT NULL,
                    agent_name VARCHAR(255) NOT NULL,
                    decision_type VARCHAR(100) NOT NULL,
                    action VARCHAR(255) NOT NULL,
                    candidate_id VARCHAR(255),
                    job_vacancy_id VARCHAR(255),
                    decision VARCHAR(100) NOT NULL,
                    score FLOAT,
                    confidence FLOAT,
                    reasoning JSON NOT NULL DEFAULT '[]',
                    criteria_used JSON NOT NULL DEFAULT '[]',
                    criteria_ignored JSON NOT NULL DEFAULT '[]',
                    human_review_required BOOLEAN DEFAULT FALSE,
                    human_reviewed_by VARCHAR(255),
                    human_reviewed_at TIMESTAMP,
                    human_override VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retention_until TIMESTAMP
                )
            """))
            logger.debug("Ensured audit_logs table exists")
        except Exception as e:
            logger.warning(f"Could not create audit_logs table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_company ON audit_logs(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_candidate ON audit_logs(candidate_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_job ON audit_logs(job_vacancy_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_agent ON audit_logs(agent_name)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_decision_type ON audit_logs(decision_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"
            ))
            logger.debug("Ensured audit_logs indexes exist")
        except Exception as e:
            logger.warning(f"Could not create audit_logs indexes: {e}")
    
    logger.info("Audit logs table verified/created successfully")


async def add_audit_logs_output_columns():
    """
    Add the 5 columns from migration 052 to audit_logs if they are missing.

    Alembic reports 052 as applied but the columns were never actually created.
    Uses ADD COLUMN IF NOT EXISTS so this is safe to run repeatedly.
    """
    columns_to_add = [
        ("session_id", "VARCHAR(255)"),
        ("agent_used", "VARCHAR(255)"),
        ("input_text", "TEXT"),
        ("output_text", "TEXT"),
        ("fairness_flags", "JSON"),
    ]

    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column audit_logs.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add audit_logs column {column_name}: {e}")

        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_audit_logs_session_id ON audit_logs(session_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_audit_logs_company_created ON audit_logs(company_id, created_at)"
            ))
            logger.debug("Ensured audit_logs output indexes exist")
        except Exception as e:
            logger.warning(f"Could not create audit_logs output indexes: {e}")

    logger.info("Audit logs output columns (migration 052) verified/added successfully")


async def create_candidate_lists_tables():
    """
    Create the candidate_lists and candidate_list_members tables.
    These tables support organizing candidates into custom collections/lists.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS candidate_lists (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    color VARCHAR(20),
                    created_by VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """))
            logger.debug("Ensured candidate_lists table exists")
        except Exception as e:
            logger.warning(f"Could not create candidate_lists table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS candidate_list_members (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    list_id UUID NOT NULL REFERENCES candidate_lists(id) ON DELETE CASCADE,
                    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                    added_by VARCHAR(255) NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    source VARCHAR(50) DEFAULT 'manual',
                    CONSTRAINT uq_list_candidate UNIQUE (list_id, candidate_id)
                )
            """))
            logger.debug("Ensured candidate_list_members table exists")
        except Exception as e:
            logger.warning(f"Could not create candidate_list_members table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_candidate_lists_company ON candidate_lists(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_candidate_lists_company_name ON candidate_lists(company_id, name)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_list_members_list ON candidate_list_members(list_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_list_members_candidate ON candidate_list_members(candidate_id)"
            ))
            logger.debug("Ensured candidate_lists indexes exist")
        except Exception as e:
            logger.warning(f"Could not create candidate_lists indexes: {e}")
    
    logger.info("Candidate lists tables verified/created successfully")


async def add_email_template_columns():
    """
    Add new columns to email_templates table for template inheritance tracking and metadata.
    """
    columns_to_add = [
        ("origin_template_id", "UUID"),
        ("trigger_type", "VARCHAR(20) DEFAULT 'manual'"),
        ("used_in", "JSONB DEFAULT '[]'::jsonb"),
        ("priority", "VARCHAR(10) DEFAULT 'medium'"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE email_templates ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column email_templates.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add email_templates column {column_name}: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_templates_origin ON email_templates(origin_template_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_templates_trigger_type ON email_templates(trigger_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_templates_priority ON email_templates(priority)"
            ))
            logger.debug("Ensured email_templates indexes exist")
        except Exception as e:
            logger.warning(f"Could not create email_templates indexes: {e}")
    
    logger.info("Email template columns verified/added successfully")


async def create_profile_analyses_table():
    """
    Create the lia_profile_analyses table for storing AI-generated candidate summaries.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lia_profile_analyses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    candidate_id VARCHAR(255) NOT NULL,
                    analysis_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    candidate_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255),
                    company_id VARCHAR(100) NOT NULL DEFAULT 'default'
                )
            """))
            logger.debug("Ensured lia_profile_analyses table exists")
        except Exception as e:
            logger.warning(f"Could not create lia_profile_analyses table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_profile_analyses_candidate ON lia_profile_analyses(candidate_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_profile_analyses_company ON lia_profile_analyses(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_profile_analyses_type ON lia_profile_analyses(analysis_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_profile_analyses_active ON lia_profile_analyses(is_active)"
            ))
            logger.debug("Ensured lia_profile_analyses indexes exist")
        except Exception as e:
            logger.warning(f"Could not create lia_profile_analyses indexes: {e}")
    
    logger.info("Profile analyses table verified/created successfully")


async def add_workos_columns():
    """
    Add WorkOS SSO/SCIM columns to users table.
    Supports enterprise authentication and directory sync.
    """
    columns_to_add = [
        ("workos_id", "VARCHAR(255) UNIQUE"),
        ("workos_directory_id", "VARCHAR(255)"),
        ("workos_organization_id", "VARCHAR(255)"),
        ("sso_provider", "VARCHAR(100)"),
        ("is_scim_managed", "BOOLEAN DEFAULT FALSE"),
        ("last_sso_login_at", "TIMESTAMP"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column users.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add users column {column_name}: {e}")
        
        try:
            # idx_users_workos_id removido: duplicata de users_workos_id_key (unique constraint).
            # Limpeza em alembic 251_drop_duplicate_indexes.
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_users_workos_directory ON users(workos_directory_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_users_workos_org ON users(workos_organization_id)"
            ))
            logger.debug("Ensured WorkOS indexes exist")
        except Exception as e:
            logger.warning(f"Could not create WorkOS indexes: {e}")
        
        try:
            await conn.execute(text(
                "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"
            ))
            logger.debug("Made password_hash nullable for SSO users")
        except Exception as e:
            logger.debug(f"password_hash already nullable or could not alter: {e}")
    
    logger.info("WorkOS columns verified/added successfully")


async def create_workos_groups_tables():
    """
    Create WorkOS SCIM groups tables for directory sync.
    
    Tables:
    - workos_groups: Stores SCIM group information synced from WorkOS
    - workos_group_memberships: Tracks which users belong to which groups
    - workos_group_role_mappings: Maps WorkOS groups to application roles/permissions
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workos_groups (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    workos_id VARCHAR(255) UNIQUE NOT NULL,
                    directory_id VARCHAR(255),
                    name VARCHAR(255) NOT NULL,
                    raw_attributes JSON DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured workos_groups table exists")
        except Exception as e:
            logger.warning(f"Could not create workos_groups table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workos_group_memberships (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    group_id UUID NOT NULL REFERENCES workos_groups(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by VARCHAR(255),
                    CONSTRAINT uq_workos_group_membership UNIQUE (group_id, user_id)
                )
            """))
            logger.debug("Ensured workos_group_memberships table exists")
        except Exception as e:
            logger.warning(f"Could not create workos_group_memberships table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workos_group_role_mappings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) NOT NULL,
                    workos_group_id UUID NOT NULL REFERENCES workos_groups(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    permissions TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255),
                    CONSTRAINT uq_workos_group_role_mapping UNIQUE (company_id, workos_group_id)
                )
            """))
            logger.debug("Ensured workos_group_role_mappings table exists")
        except Exception as e:
            logger.warning(f"Could not create workos_group_role_mappings table: {e}")
        
        try:
            # idx_workos_groups_workos_id removido: duplicata de workos_groups_workos_id_key (unique constraint).
            # Limpeza em alembic 251_drop_duplicate_indexes.
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_groups_directory ON workos_groups(directory_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_groups_active ON workos_groups(is_active)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_group_memberships_group ON workos_group_memberships(group_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_group_memberships_user ON workos_group_memberships(user_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_group_role_mappings_company ON workos_group_role_mappings(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_workos_group_role_mappings_group ON workos_group_role_mappings(workos_group_id)"
            ))
            logger.debug("Ensured WorkOS groups indexes exist")
        except Exception as e:
            logger.warning(f"Could not create WorkOS groups indexes: {e}")
    
    logger.info("WorkOS groups tables verified/created successfully")


async def create_company_workos_config_table():
    """
    Create table for mapping companies to their WorkOS configuration.
    This ensures tenant isolation by validating directory access.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS company_workos_config (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) UNIQUE NOT NULL,
                    workos_organization_id VARCHAR(255),
                    workos_directory_id VARCHAR(255),
                    sso_connection_id VARCHAR(255),
                    sso_enabled BOOLEAN DEFAULT FALSE,
                    scim_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured company_workos_config table exists")
        except Exception as e:
            logger.warning(f"Could not create company_workos_config table: {e}")
        
        try:
            # idx_company_workos_config_company removido: duplicata de ix_company_workos_config_company_id (unique).
            # Limpeza em alembic 251_drop_duplicate_indexes.
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_company_workos_config_directory ON company_workos_config(workos_directory_id)"
            ))
            logger.debug("Ensured company_workos_config indexes exist")
        except Exception as e:
            logger.warning(f"Could not create company_workos_config indexes: {e}")
    
    logger.info("Company WorkOS config table verified/created successfully")


async def create_sso_audit_logs_table():
    """
    Create the sso_audit_logs table for SSO/SCIM event tracking.
    
    This table tracks all SSO and SCIM events for security auditing:
    - SSO login events
    - SCIM user provisioning/deprovisioning
    - SCIM group changes
    - Directory sync events
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sso_audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    actor_id VARCHAR(255),
                    actor_email VARCHAR(255),
                    target_id VARCHAR(255),
                    target_email VARCHAR(255),
                    source_ip VARCHAR(45),
                    user_agent TEXT,
                    workos_event_id VARCHAR(255),
                    payload JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured sso_audit_logs table exists")
        except Exception as e:
            logger.warning(f"Could not create sso_audit_logs table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_company ON sso_audit_logs(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_event_type ON sso_audit_logs(event_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_actor ON sso_audit_logs(actor_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_created_at ON sso_audit_logs(created_at)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_target ON sso_audit_logs(target_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_sso_audit_logs_workos_event ON sso_audit_logs(workos_event_id)"
            ))
            logger.debug("Ensured sso_audit_logs indexes exist")
        except Exception as e:
            logger.warning(f"Could not create sso_audit_logs indexes: {e}")
    
    logger.info("SSO audit logs table verified/created successfully")


async def add_client_user_invitation_columns():
    """
    Add invitation token columns to client_users table if they don't exist.
    These columns support the user invitation workflow with token-based acceptance.
    """
    columns_to_add = [
        ("invitation_token", "VARCHAR(255)"),
        ("invitation_expires_at", "TIMESTAMP"),
    ]
    
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE client_users ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.debug(f"Ensured column client_users.{column_name} exists")
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add client_users column {column_name}: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_client_users_invitation_token ON client_users(invitation_token)"
            ))
            logger.debug("Ensured client_users invitation_token index exists")
        except Exception as e:
            logger.warning(f"Could not create invitation_token index: {e}")
    
    logger.info("Client user invitation columns verified/added successfully")


async def create_feedback_learning_tables():
    """
    Create the wizard_feedback and job_outcomes tables for LIA learning.
    
    These tables enable LIA to learn from:
    - Recruiter corrections during the wizard flow (wizard_feedback)
    - Final job outcomes for success pattern analysis (job_outcomes)
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wizard_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id VARCHAR(255),
                    company_id VARCHAR(255) NOT NULL,
                    field_corrected VARCHAR(100) NOT NULL,
                    original_value JSON,
                    corrected_value JSON,
                    stage INTEGER,
                    role VARCHAR(255),
                    seniority VARCHAR(100),
                    department VARCHAR(255),
                    location VARCHAR(255),
                    correction_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255)
                )
            """))
            logger.debug("Ensured wizard_feedback table exists")
        except Exception as e:
            logger.warning(f"Could not create wizard_feedback table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS job_outcomes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id VARCHAR(255) NOT NULL,
                    company_id VARCHAR(255) NOT NULL,
                    outcome VARCHAR(50) NOT NULL,
                    time_to_fill_days INTEGER,
                    salary_initial_min DECIMAL,
                    salary_initial_max DECIMAL,
                    salary_final DECIMAL,
                    candidate_count_total INTEGER,
                    candidate_count_screened INTEGER,
                    candidate_count_interviewed INTEGER,
                    candidate_count_offered INTEGER,
                    satisfaction_score DECIMAL,
                    role VARCHAR(255),
                    seniority VARCHAR(100),
                    department VARCHAR(255),
                    location VARCHAR(255),
                    work_model VARCHAR(100),
                    skills_used JSON DEFAULT '[]',
                    notes TEXT,
                    closed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255)
                )
            """))
            logger.debug("Ensured job_outcomes table exists")
        except Exception as e:
            logger.warning(f"Could not create job_outcomes table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_company ON wizard_feedback(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_job ON wizard_feedback(job_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_field ON wizard_feedback(field_corrected)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_role ON wizard_feedback(role)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_seniority ON wizard_feedback(seniority)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_wizard_feedback_created_at ON wizard_feedback(created_at)"
            ))
            logger.debug("Ensured wizard_feedback indexes exist")
        except Exception as e:
            logger.warning(f"Could not create wizard_feedback indexes: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_job_outcomes_company ON job_outcomes(company_id)"
            ))
            # idx_job_outcomes_job removido: duplicata de idx_job_outcomes_job_unique (unique em job_id).
            # Limpeza em alembic 251_drop_duplicate_indexes.
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_job_outcomes_outcome ON job_outcomes(outcome)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_job_outcomes_role ON job_outcomes(role)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_job_outcomes_seniority ON job_outcomes(seniority)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_job_outcomes_created_at ON job_outcomes(created_at)"
            ))
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_job_outcomes_job_unique ON job_outcomes(job_id)"
            ))
            logger.debug("Ensured job_outcomes indexes exist")
        except Exception as e:
            logger.warning(f"Could not create job_outcomes indexes: {e}")
    
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS interaction_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id VARCHAR(100) NOT NULL,
                    company_id UUID NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    message_id VARCHAR(100),
                    user_message TEXT,
                    lia_response TEXT,
                    intent VARCHAR(50),
                    stage VARCHAR(50),
                    rating INTEGER,
                    thumbs VARCHAR(10),
                    correction TEXT,
                    feedback_text TEXT,
                    feedback_category VARCHAR(50),
                    response_time_ms INTEGER,
                    tools_used JSON DEFAULT '[]',
                    confidence_score FLOAT,
                    processed BOOLEAN DEFAULT FALSE,
                    incorporated_to_rag BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured interaction_feedback table exists")
        except Exception as e:
            logger.warning(f"Could not create interaction_feedback table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID NOT NULL,
                    pattern_type VARCHAR(50) NOT NULL,
                    pattern_key VARCHAR(255) NOT NULL,
                    trigger_phrases JSON DEFAULT '[]',
                    expected_response_style TEXT,
                    preferred_tools JSON DEFAULT '[]',
                    example_good_responses JSON DEFAULT '[]',
                    example_bad_responses JSON DEFAULT '[]',
                    positive_feedback_count INTEGER DEFAULT 0,
                    negative_feedback_count INTEGER DEFAULT 0,
                    success_rate FLOAT DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT TRUE,
                    confidence FLOAT DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured learning_patterns table exists")
        except Exception as e:
            logger.warning(f"Could not create learning_patterns table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_interaction_feedback_session ON interaction_feedback(session_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_interaction_feedback_company ON interaction_feedback(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_interaction_feedback_user ON interaction_feedback(user_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_interaction_feedback_created_at ON interaction_feedback(created_at)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_company ON learning_patterns(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_learning_patterns_key ON learning_patterns(pattern_key)"
            ))
            logger.debug("Ensured interaction_feedback and learning_patterns indexes exist")
        except Exception as e:
            logger.warning(f"Could not create interaction_feedback/learning_patterns indexes: {e}")
    
    logger.info("Feedback learning tables (wizard_feedback, job_outcomes, interaction_feedback, learning_patterns) verified/created successfully")


async def add_job_draft_affirmative_columns():
    """Add affirmative action columns to job_drafts table."""
    columns_to_add = [
        ("is_affirmative", "BOOLEAN DEFAULT FALSE"),
        ("affirmative_criteria_primary", "VARCHAR(100)"),
        ("affirmative_criteria_secondary", "VARCHAR(100)"),
        ("manager", "VARCHAR(255)"),
        ("manager_email", "VARCHAR(255)"),
    ]
    async with engine.begin() as conn:
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE job_drafts ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
            except Exception as e:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Could not add column {column_name} to job_drafts: {e}")
    logger.info("Job draft affirmative columns verified/added successfully")


async def setup_pgvector():
    """
    Setup pgvector extension and create indexes for vector similarity search.
    Required for the RAG memory system.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not create pgvector extension: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS conversation_memories (
                    id UUID PRIMARY KEY,
                    company_id UUID NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured conversation_memories table exists")
        except Exception as e:
            logger.warning(f"Could not create conversation_memories table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id UUID PRIMARY KEY,
                    company_id UUID NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    source VARCHAR(255),
                    chunk_index VARCHAR(50),
                    parent_id UUID,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured knowledge_base table exists")
        except Exception as e:
            logger.warning(f"Could not create knowledge_base table: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_conversation_memories_company_id ON conversation_memories(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_conversation_memories_session_id ON conversation_memories(session_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_conversation_memories_user_id ON conversation_memories(user_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_conversation_memories_company_session ON conversation_memories(company_id, session_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_conversation_memories_created_at ON conversation_memories(created_at)"
            ))
            logger.debug("Ensured conversation_memories indexes exist")
        except Exception as e:
            logger.warning(f"Could not create conversation_memories indexes: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_base_company_id ON knowledge_base(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_base_document_type ON knowledge_base(document_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_base_parent_id ON knowledge_base(parent_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_base_company_type ON knowledge_base(company_id, document_type)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_base_created_at ON knowledge_base(created_at)"
            ))
            logger.debug("Ensured knowledge_base indexes exist")
        except Exception as e:
            logger.warning(f"Could not create knowledge_base indexes: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_conversation_memories_embedding 
                ON conversation_memories 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """))
            logger.debug("Ensured conversation_memories vector index exists")
        except Exception as e:
            logger.warning(f"Could not create conversation_memories vector index: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_knowledge_base_embedding 
                ON knowledge_base 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """))
            logger.debug("Ensured knowledge_base vector index exists")
        except Exception as e:
            logger.warning(f"Could not create knowledge_base vector index: {e}")
    
    logger.info("pgvector setup completed for RAG memory system")


async def create_background_jobs_tables():
    """
    Create tables for the Autonomous Agent System.
    
    Creates:
    - background_jobs: For scheduled and one-time background tasks
    - proactive_actions: For LIA's proactive suggestions and notifications
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS background_jobs (
                    id UUID PRIMARY KEY,
                    company_id UUID NOT NULL,
                    job_type VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    config JSON DEFAULT '{}',
                    schedule VARCHAR(100),
                    result JSON,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    next_run_at TIMESTAMP,
                    last_run_at TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured background_jobs table exists")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_background_jobs_company_id 
                ON background_jobs (company_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_background_jobs_status 
                ON background_jobs (status)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_background_jobs_job_type 
                ON background_jobs (job_type)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_background_jobs_next_run_at 
                ON background_jobs (next_run_at)
            """))
            
        except Exception as e:
            logger.warning(f"Could not create background_jobs table: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS proactive_actions (
                    id UUID PRIMARY KEY,
                    company_id UUID NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    priority VARCHAR(20) DEFAULT 'normal',
                    related_job_id UUID,
                    related_candidate_id UUID,
                    trigger_reason TEXT,
                    suggested_action JSON DEFAULT '{}',
                    auto_executable BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'pending',
                    accepted_by VARCHAR(100),
                    accepted_at TIMESTAMP,
                    executed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """))
            logger.debug("Ensured proactive_actions table exists")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_proactive_actions_company_id 
                ON proactive_actions (company_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_proactive_actions_status 
                ON proactive_actions (status)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_proactive_actions_related_job_id 
                ON proactive_actions (related_job_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_proactive_actions_related_candidate_id 
                ON proactive_actions (related_candidate_id)
            """))
            
        except Exception as e:
            logger.warning(f"Could not create proactive_actions table: {e}")
    
    logger.info("Background jobs tables created/verified successfully")


async def ensure_job_templates_indexes():
    """Ensure job_templates indexes exist (table created by SQLAlchemy Base.metadata.create_all)."""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_company ON job_templates(company_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_category ON job_templates(category)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_subcategory ON job_templates(subcategory)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_seniority ON job_templates(seniority)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_is_system ON job_templates(is_system)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_is_active ON job_templates(is_active)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_title_normalized ON job_templates(title_normalized)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_popularity ON job_templates(popularity_score DESC)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_templates_created_at ON job_templates(created_at)"))
        except Exception as e:
            logger.warning(f"Could not create job_templates indexes: {e}")
        
    logger.info("Job templates indexes verified successfully")


async def ensure_lia_app_role():
    """Ensure the non-login RLS role ``lia_app`` exists with its grants (idempotent).

    Every tenant-scoped request runs under ``SET ROLE lia_app`` (see
    ``get_tenant_db``). That role is a *cluster-level* object, not a schema
    object: it is created by migrations 068/237 but is NOT carried over by
    logical restores / branch operations (``pg_dump`` omits roles and their
    grants). A production database restored from such a dump keeps
    ``alembic_version`` at head yet loses the role, so ``alembic upgrade head``
    becomes a no-op and never recreates it — and every authenticated request
    then fails with ``role "lia_app" does not exist``.

    Re-asserting the role on every startup makes the application self-heal
    regardless of how the database was provisioned, instead of relying on a
    one-time migration that cannot re-run. It is a safe no-op where the role
    already exists (e.g. development). Requires the connecting user to have
    CREATEROLE (``neondb_owner`` in prod, ``postgres`` in dev both qualify).
    """
    async with engine.begin() as conn:
        # Race-safe across simultaneously-starting instances: if two replicas
        # both pass the existence check, the loser would otherwise abort with
        # duplicate_object — swallow it so every replica boots cleanly.
        await conn.execute(text(
            """
            DO $$
            BEGIN
                CREATE ROLE lia_app NOLOGIN NOSUPERUSER;
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        ))
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO lia_app"))
        await conn.execute(text(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lia_app"
        ))
        await conn.execute(text(
            "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lia_app"
        ))
        await conn.execute(text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_current_company_id') THEN
                    EXECUTE 'GRANT EXECUTE ON FUNCTION app_current_company_id() TO lia_app';
                END IF;
            END $$;
            """
        ))
        await conn.execute(text(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lia_app"
        ))
        await conn.execute(text(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT USAGE, SELECT ON SEQUENCES TO lia_app"
        ))
        # The connecting application user must be a member of lia_app so it can
        # ``SET ROLE lia_app`` at request time.
        await conn.execute(text(
            """
            DO $$
            DECLARE
                app_user TEXT := current_user;
            BEGIN
                EXECUTE format('GRANT lia_app TO %I', app_user);
            END $$;
            """
        ))
    logger.info("RLS role lia_app verified/created successfully")


async def init_db():
    """Initialize database tables."""
    # Re-assert the RLS role FIRST so tenant-scoped requests can SET ROLE lia_app
    # even on a database that lost the cluster-level role (e.g. after a restore).
    await ensure_lia_app_role()

    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not create pgvector extension: {e}")
        
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            logger.info("unaccent extension enabled")
        except Exception as e:
            logger.warning(f"Could not create unaccent extension: {e}")
        
        await conn.run_sync(Base.metadata.create_all)
    
    await setup_pgvector()
    await add_task_lifecycle_columns()
    await add_notification_columns()
    await add_approval_workflow_columns()
    await ensure_default_company()
    await migrate_default_company_ids()
    await create_audit_logs_table()
    await add_audit_logs_output_columns()
    await create_candidate_lists_tables()
    await add_email_template_columns()
    await create_profile_analyses_table()
    await add_workos_columns()
    await create_workos_groups_tables()
    await create_sso_audit_logs_table()
    await create_company_workos_config_table()
    await add_client_user_invitation_columns()
    await create_feedback_learning_tables()
    await add_job_draft_affirmative_columns()
    await create_background_jobs_tables()
    await ensure_job_templates_indexes()
    await add_wsi_session_version_columns()
    await create_company_hiring_policies_table()
    await create_agent_long_term_memory_table()


async def create_agent_long_term_memory_table():
    """
    Create the agent_long_term_memory table for cross-session agent learning.

    This table stores patterns, preferences, learnings and outcomes that
    agents accumulate over multiple sessions for the same company.
    """
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_long_term_memory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) NOT NULL,
                    domain VARCHAR(100) NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    memory_key VARCHAR(255) NOT NULL,
                    memory_value JSONB DEFAULT '{}'::jsonb,
                    context_tags JSONB DEFAULT '[]'::jsonb,
                    usage_count INTEGER DEFAULT 0,
                    relevance_score FLOAT DEFAULT 1.0,
                    source_session_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMPTZ
                )
            """))
            logger.debug("Ensured agent_long_term_memory table exists")
        except Exception as e:
            logger.warning(f"Could not create agent_long_term_memory table: {e}")

        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_agent_ltm_company ON agent_long_term_memory(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_agent_ltm_domain ON agent_long_term_memory(domain)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_agent_ltm_memory_key ON agent_long_term_memory(memory_key)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_agent_ltm_memory_type ON agent_long_term_memory(memory_type)"
            ))
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_ltm_company_domain_key ON agent_long_term_memory(company_id, domain, memory_key)"
            ))
            logger.debug("Ensured agent_long_term_memory indexes exist")
        except Exception as e:
            logger.warning(f"Could not create agent_long_term_memory indexes: {e}")

    logger.info("Agent long-term memory table verified/created successfully")


async def create_company_hiring_policies_table():
    """Create the company_hiring_policies table for storing per-company hiring rules."""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS company_hiring_policies (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id VARCHAR(255) NOT NULL UNIQUE,
                    pipeline_rules JSON DEFAULT '{}',
                    scheduling_rules JSON DEFAULT '{}',
                    communication_rules JSON DEFAULT '{}',
                    screening_rules JSON DEFAULT '{}',
                    automation_rules JSON DEFAULT '{}',
                    pipeline_templates JSON DEFAULT '[]',
                    learned_patterns JSON DEFAULT '[]',
                    setup_progress INTEGER DEFAULT 0,
                    setup_completed_at TIMESTAMP,
                    created_by VARCHAR(255),
                    updated_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("Ensured company_hiring_policies table exists")
        except Exception as e:
            logger.warning(f"Could not create company_hiring_policies table: {e}")

        try:
            # idx_chp_company_id removido: duplicata de ix_company_hiring_policies_company_id (unique do modelo).
            # Limpeza em alembic 251_drop_duplicate_indexes.
            logger.debug("Ensured company_hiring_policies indexes exist")
        except Exception as e:
            logger.warning(f"Could not create company_hiring_policies indexes: {e}")

    logger.info("Company hiring policies table verified/created successfully")


async def add_wsi_session_version_columns():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE wsi_sessions ADD COLUMN IF NOT EXISTS question_set_version INTEGER"))
            await conn.execute(text("ALTER TABLE wsi_sessions ADD COLUMN IF NOT EXISTS question_set_id VARCHAR(255)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wsi_sessions_qsv ON wsi_sessions(job_vacancy_id, question_set_version)"))
        except Exception as e:
            logger.warning(f"Could not add wsi_sessions version columns: {e}")


@asynccontextmanager
async def tenant_session(company_id: str) -> "AsyncGenerator":
    """Sessao async com contexto RLS (app.company_id) JA setado.

    USE em tools/jobs/loops que rodam FORA de um request HTTP (onde o middleware
    nao roda). Sem isso, RLS — habilitado e FORCED em ~241 tabelas — ve
    app_current_company_id()=NULL e BLOQUEIA todas as linhas (retorna 0) mesmo
    com dados no banco. Foi a root cause do "chat nao ve vagas/candidatos"
    (agentic loop LIA-A04, 2026-06-03).

    Padrao canonical (espelha get_tenant_db, mas parametrizado por company_id):
        async with tenant_session(company_id) as db:
            rows = (await db.execute(select(Model))).scalars().all()

    Se company_id vier vazio, abre sessao sem setar contexto (RLS continua
    bloqueando — fail-closed, nunca vaza cross-tenant).
    """
    async with AsyncSessionLocal() as session:
        if company_id:
            await set_tenant_context(session, str(company_id))
        yield session
