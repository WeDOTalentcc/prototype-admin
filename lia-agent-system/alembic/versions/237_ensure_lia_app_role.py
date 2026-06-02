"""Migration 237 -- Ensure lia_app RLS role exists (idempotent).

Background:
    The application enforces tenant isolation by running every tenant-scoped
    request under the non-login PostgreSQL role ``lia_app`` (``SET ROLE lia_app``
    in ``app/core/database.py::get_tenant_db``). That role is originally created
    by migration 068.

    Roles are *cluster-level* objects, not schema objects. They are therefore
    NOT carried over by logical schema copies / ``pg_dump`` restores (which omit
    roles and role grants by default). A production database that was restored
    from such a dump keeps ``alembic_version`` at head but loses the ``lia_app``
    role, so ``alembic upgrade head`` becomes a no-op and never recreates it.
    Every authenticated request then fails with::

        role "lia_app" does not exist -> RuntimeError("RLS role enforcement failed")

    This migration re-asserts the role and its grants idempotently so a fresh
    ``alembic upgrade head`` (run by the deployment build) repairs any database
    that is missing the role. It mirrors the role section of migration 068 and
    is a safe no-op where the role already exists (e.g. development).

Revision ID: 237
Revises: 236
Create Date: 2026-06-02
"""
revision = "237"
down_revision = "236"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lia_app') THEN
                CREATE ROLE lia_app NOLOGIN NOSUPERUSER;
            END IF;
        END $$;
        """
    )

    op.execute("GRANT USAGE ON SCHEMA public TO lia_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lia_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lia_app;")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_current_company_id') THEN
                EXECUTE 'GRANT EXECUTE ON FUNCTION app_current_company_id() TO lia_app';
            END IF;
        END $$;
        """
    )

    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lia_app;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO lia_app;"
    )

    # The connecting application user must be a member of lia_app so that it can
    # ``SET ROLE lia_app`` at request time.
    op.execute(
        """
        DO $$
        DECLARE
            app_user TEXT := current_user;
        BEGIN
            EXECUTE format('GRANT lia_app TO %I', app_user);
        END $$;
        """
    )


def downgrade() -> None:
    # Intentionally a no-op: ``lia_app`` is required for the application to
    # function and may be shared by other sessions/grants. Dropping it here
    # would break tenant isolation enforcement. Role lifecycle is owned by
    # migration 068.
    pass
