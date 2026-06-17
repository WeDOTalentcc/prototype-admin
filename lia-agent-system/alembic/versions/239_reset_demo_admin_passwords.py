"""Migration 239 -- One-time password (re)set for the demo admin accounts.

Background:
    The production database already contains the admin accounts
    ``admindemo@wedotalent.cc`` and ``demo@wedotalent.cc`` (role=admin, active)
    but their current passwords were unknown to the operator (the ``demo@``
    password was last set by migration 238; ``admindemo@`` came from another
    origin). The deployment build (``alembic upgrade head``) is the only write
    path into the production database, so this one-time migration sets a known
    bcrypt hash for both accounts so the operator can sign in.

    Only the *one-way* bcrypt hash is stored here (never the plaintext). It was
    generated with the same primitive the app uses to verify logins
    (``bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())`` /
    ``bcrypt.checkpw`` in ``app/auth/security.py``). The operator should change
    this password after first login.

    Idempotent / safe: alembic runs each migration exactly once per database, so
    this will not clobber a later password change on subsequent deploys. The
    UPDATE matches each account by plaintext email (the production row stores the
    email in plaintext, ``email_hash`` is NULL) and also by ``email_hash`` for
    robustness. On databases without these accounts the UPDATE simply affects
    zero rows.

Revision ID: 239
Revises: 238
Create Date: 2026-06-02
"""
revision = "239"
down_revision = "238"
branch_labels = None
depends_on = None

from alembic import op

# bcrypt hash of the operator-chosen password (one-way; plaintext never stored).
_DEMO_PASSWORD_HASH = "$2b$12$xMaSnM98LHtzXELfo9uzaev955kj8SIPJvb11ZvdxopA13jgkhWd."

# (email, email_hash) pairs for the two demo admin accounts being reset.
_DEMO_ACCOUNTS = (
    (
        "admindemo@wedotalent.cc",
        "027a7ce2097e933d92a7d4b62e16a6e83fd80143b85915c41100097f295f4806",
    ),
    (
        "demo@wedotalent.cc",
        "78628824b7080e91539e2c8158557597fe2fc5dbad322b535bffd1dce98dec49",
    ),
)


def upgrade() -> None:
    for email, email_hash in _DEMO_ACCOUNTS:
        op.execute(
            "UPDATE users SET password_hash = '{pw}' "
            "WHERE email = '{email}' OR email_hash = '{ehash}'".format(
                pw=_DEMO_PASSWORD_HASH,
                email=email,
                ehash=email_hash,
            )
        )


def downgrade() -> None:
    # Intentionally a no-op: we do not restore the previous (unknown) passwords.
    pass
