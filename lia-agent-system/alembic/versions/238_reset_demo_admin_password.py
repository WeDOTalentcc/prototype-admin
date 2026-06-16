"""Migration 238 -- One-time password (re)set for the demo admin account.

Background:
    The production database already contains the admin account
    ``demo@wedotalent.cc`` (role=admin, active) but its password was unknown to
    the operator. The deployment build (``alembic upgrade head``) is the only
    write path into the production database, so this one-time migration sets a
    known bcrypt hash for that account so the operator can sign in.

    Only the *one-way* bcrypt hash is stored here (never the plaintext). It was
    generated with the same primitive the app uses to verify logins
    (``bcrypt.checkpw`` in ``app/auth/security.py``). The operator should change
    this password after first login.

    Idempotent / safe: alembic runs each migration exactly once per database, so
    this will not clobber a later password change on subsequent deploys. The
    UPDATE matches the account by plaintext email (the production row stores the
    email in plaintext, ``email_hash`` is NULL) and also by ``email_hash`` for
    robustness. On databases without that account the UPDATE simply affects zero
    rows.

Revision ID: 238
Revises: 237
Create Date: 2026-06-02
"""
revision = "238"
down_revision = "237"
branch_labels = None
depends_on = None

from alembic import op

# bcrypt hash of the operator-chosen password (one-way; plaintext never stored).
_DEMO_ADMIN_EMAIL = "demo@wedotalent.cc"
_DEMO_ADMIN_EMAIL_HASH = "78628824b7080e91539e2c8158557597fe2fc5dbad322b535bffd1dce98dec49"
_DEMO_ADMIN_PASSWORD_HASH = "$2b$12$gyV49VOv2jL3kgK/Vvrn3uFKOV1lWQz1Mit/3WNo6P2v9FND2bDeK"


def upgrade() -> None:
    op.execute(
        "UPDATE users SET password_hash = '{pw}' "
        "WHERE email = '{email}' OR email_hash = '{ehash}'".format(
            pw=_DEMO_ADMIN_PASSWORD_HASH,
            email=_DEMO_ADMIN_EMAIL,
            ehash=_DEMO_ADMIN_EMAIL_HASH,
        )
    )


def downgrade() -> None:
    # Intentionally a no-op: we do not restore the previous (unknown) password.
    pass
