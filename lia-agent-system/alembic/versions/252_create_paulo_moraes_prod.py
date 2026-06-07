"""Migration 252 -- Create paulo.moraes@wedotalent.cc in production.

Background:
    The production database does not contain paulo.moraes@wedotalent.cc; the
    account only exists in the development (heliumdb) database.  This migration
    creates the account with role=admin, company_id matching the canonical demo
    tenant, and a known bcrypt hash so the operator can sign in and then change
    the password via the platform UI or via the forgot-password flow.

    Only the one-way bcrypt hash is stored here (never the plaintext).  The
    operator should change this password immediately after first login.

    Idempotent: the INSERT uses WHERE NOT EXISTS so re-running on a database
    that already has the account (by email) is a safe no-op.  A fresh UUID is
    used for the production row to avoid primary-key collision with the
    development database record.

Revision ID: 252
Revises: 251
Create Date: 2026-06-07
"""
revision = "252"
down_revision = "251"
branch_labels = None
depends_on = None

from alembic import op

# bcrypt hash of the temporary operator password (plaintext never stored).
# Change this password immediately after first login.
_PASSWORD_HASH = "$2b$12$o3EDljyYp7WFiTScUC6kre87sD9DhSmpRDAqpNczSMOn1LscG6bc."

_EMAIL = "paulo.moraes@wedotalent.cc"
_EMAIL_HASH = "eaeb7f8b56e2e421c3045feef2a87e7a37c0f9274ed7ce357cde4cd249841584"
_COMPANY_ID = "00000000-0000-4000-a000-000000000001"
# Fresh UUID for the production row (different from the dev-database record
# bc72a128-c7b1-408d-b30d-34887ac412f7 to avoid any PK collision).
_USER_ID = "cfe5c93e-eda9-44c8-958e-c711e27f4d30"


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO users (
            id, email, email_hash, password_hash, name, role,
            company_id, is_active, permissions, email_verified,
            can_view_salary, can_view_sensitive_pii,
            created_at, updated_at
        )
        SELECT
            '{uid}', '{email}', '{ehash}', '{pw}', 'Paulo Moraes', 'admin',
            '{company}', TRUE, '{{}}', TRUE,
            FALSE, TRUE,
            NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM users
            WHERE email = '{email}' OR email_hash = '{ehash}'
        )
        """.format(
            uid=_USER_ID,
            email=_EMAIL,
            ehash=_EMAIL_HASH,
            pw=_PASSWORD_HASH,
            company=_COMPANY_ID,
        )
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users WHERE email = '{email}'".format(email=_EMAIL)
    )
