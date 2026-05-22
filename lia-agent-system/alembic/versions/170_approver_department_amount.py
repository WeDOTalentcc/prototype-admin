"""WT-P0.D2 (Wave 2 audit 2026-05-22): add department_id + can_approve_above_amount to approvers.

Revision ID: 170_approver_department_amount
Revises: 169_encrypt_billing_document, 169_twin_decisions_candidate_fk
Create Date: 2026-05-22

Contexto (Wave 2 audit 2026-05-21, ApproverSection ghost-setting fix)
─────────────────────────────────────────────────────────────────────
Audit Wave 2 + Approver wire (commit ``6f4afbde5``) identificou que o
modelo ``Approver`` em ``libs/models/lia_models/company.py:553`` **não
tinha**:

  - ``department_id`` (FK → departments) — gate hoje é company-wide, mas
    ApproverSection UI já promete granularidade per-department.
  - ``can_approve_above_amount`` (Numeric) — sem isso, amount-threshold
    routing não funciona; recrutador customiza valor de threshold via UI
    futura mas DB não persiste = ghost setting parcial.

Pattern canonical (extension não-destrutiva, backward-compat):
─────────────────────────────────────────────────────────────
1. Adicionar coluna ``department_id`` (UUID, nullable, FK →
   ``departments.id`` ``ON DELETE SET NULL``). NULL = approver
   company-wide (preserva comportamento atual).
2. Adicionar coluna ``can_approve_above_amount`` (Numeric(12, 2),
   nullable). NULL = approver pode aprovar qualquer valor (preserva
   comportamento atual).
3. Adicionar índice composto ``ix_approvers_company_department`` para
   acelerar ``list_for_department`` query (filter company_id +
   department_id IS NULL OR = X).
4. Adicionar CHECK constraint ``ck_approver_amount_nonneg`` (defense-
   in-depth DB-level: rejeita valores negativos mesmo se camada Python
   bypass).

Idempotência: cada ``ADD COLUMN`` / ``CREATE INDEX`` / ``ADD CONSTRAINT``
é guardado por checks em information_schema. Re-run da migration é
no-op safe.

Multi-head merge: esta revision junta os dois 169 heads
(``169_encrypt_billing_document`` + ``169_twin_decisions_candidate_fk``)
em uma única linha de história, eliminando a divergência sem migration
de merge dedicada.

LGPD note: ``can_approve_above_amount`` não é PII. ``department_id`` é
FK para ``departments`` (também não-PII). Sem implicações LGPD.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "170_approver_department_amount"
down_revision: Union[str, Sequence[str], None] = (
    "169_encrypt_billing_document",
    "169_twin_decisions_candidate_fk",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    )
    return result.scalar() is not None


def _index_exists(conn, index_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1 FROM pg_indexes WHERE indexname = :name
            """
        ),
        {"name": index_name},
    )
    return result.scalar() is not None


def _constraint_exists(conn, constraint_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1 FROM pg_constraint WHERE conname = :name
            """
        ),
        {"name": constraint_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. department_id (UUID, nullable, FK -> departments.id)
    # ------------------------------------------------------------------
    if not _column_exists(conn, "approvers", "department_id"):
        op.add_column(
            "approvers",
            sa.Column("department_id", UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_approvers_department_id",
            "approvers",
            "departments",
            ["department_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ------------------------------------------------------------------
    # 2. can_approve_above_amount (Numeric(12, 2), nullable)
    # ------------------------------------------------------------------
    if not _column_exists(conn, "approvers", "can_approve_above_amount"):
        op.add_column(
            "approvers",
            sa.Column(
                "can_approve_above_amount", sa.Numeric(12, 2), nullable=True
            ),
        )

    # ------------------------------------------------------------------
    # 3. Composite index ix_approvers_company_department
    # ------------------------------------------------------------------
    if not _index_exists(conn, "ix_approvers_company_department"):
        op.create_index(
            "ix_approvers_company_department",
            "approvers",
            ["company_id", "department_id"],
        )

    # ------------------------------------------------------------------
    # 4. CHECK constraint ck_approver_amount_nonneg (defense-in-depth)
    # ------------------------------------------------------------------
    if not _constraint_exists(conn, "ck_approver_amount_nonneg"):
        op.create_check_constraint(
            "ck_approver_amount_nonneg",
            "approvers",
            "can_approve_above_amount IS NULL OR can_approve_above_amount >= 0",
        )


def downgrade() -> None:
    # Drop in reverse order. Constraints/indexes first, then columns/FKs.
    conn = op.get_bind()

    if _constraint_exists(conn, "ck_approver_amount_nonneg"):
        op.drop_constraint(
            "ck_approver_amount_nonneg", "approvers", type_="check"
        )

    if _index_exists(conn, "ix_approvers_company_department"):
        op.drop_index("ix_approvers_company_department", table_name="approvers")

    if _column_exists(conn, "approvers", "can_approve_above_amount"):
        op.drop_column("approvers", "can_approve_above_amount")

    if _column_exists(conn, "approvers", "department_id"):
        # FK is dropped automatically with column.
        op.drop_column("approvers", "department_id")
