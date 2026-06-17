"""WT Camada 3 Item 3: add department_id FK to offer_proposals.

Revision ID: 172_offer_proposal_department
Revises: 171_credentials_access_log
Create Date: 2026-05-22

Contexto (Wave 3 Camada 3 backlog 2026-05-22, audit Camada2-D gap)
─────────────────────────────────────────────────────────────────
``OfferService.check_can_send`` (Gate-1 amount-routing) hoje resolve
``department_id`` do proposal via::

    department_id = getattr(proposal, "department_id", None)

…porque ``OfferProposal`` **não tem** o campo. Workaround viola
canonical-fix: o backend depende de uma propriedade fantasma para
rotear amount-threshold para o aprovador correto. Caminho atual:

  Frontend cria offer →
    POST /offers (sem department_id no payload) →
      OfferProposal sem department_id →
        check_can_send faz getattr fallback → None →
          _has_eligible_approver_for_amount busca approvers
          company-wide (não department-specific).

Resultado: per-department approver routing **não funciona** mesmo
após migration 170_approver_department_amount ter wired
``Approver.department_id``. Apenas approvers company-wide
(``department_id IS NULL``) entram no lookup.

Esta migration fecha o gap fazendo OfferProposal carregar
``department_id`` próprio (vindo do job_vacancy ou explicit override
pelo recrutador no OfferForm UI). Pattern canonical (extensão
não-destrutiva, backward-compat):

1. Adicionar coluna ``department_id`` (UUID, nullable, FK →
   ``departments.id`` ``ON DELETE SET NULL``). NULL = offer
   sem associação de departamento (preserva 100% dos offers
   pré-existentes).
2. Índice composto ``(company_id, department_id)`` para acelerar
   approver lookup hot-path.

Idempotência: helper ``_column_exists`` + ``_index_exists``
defensivo (mesma estratégia das migrations 168/169/170).

Sensores associados (commits seguintes):
  - ``tests/contract/test_offer_proposal_department.py``: per-department
    approver routing end-to-end.
  - ``app/domains/offer/services/offer_service.py``: remoção do
    ``getattr(proposal, "department_id", None)`` workaround.

REGRA ZERO observada — migration aplicada SOMENTE no Replit;
canonical GitHub repo intocado.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "172_offer_proposal_department"
down_revision: Union[str, Sequence[str], None] = "171_credentials_access_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns(table_name)}
    return column_name in cols


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    idxs = {idx["name"] for idx in inspector.get_indexes(table_name)}
    return index_name in idxs


def upgrade() -> None:
    # 1) Add column (nullable; existing rows preserve NULL = no department).
    if not _column_exists("offer_proposals", "department_id"):
        op.add_column(
            "offer_proposals",
            sa.Column("department_id", UUID(as_uuid=True), nullable=True),
        )

    # 2) FK constraint ON DELETE SET NULL (safe for department deletion).
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("offer_proposals")}
    if "fk_offer_proposals_department_id" not in existing_fks:
        op.create_foreign_key(
            "fk_offer_proposals_department_id",
            "offer_proposals",
            "departments",
            ["department_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 3) Composite index for approver-lookup hot path.
    if not _index_exists("offer_proposals", "ix_offer_proposals_company_department"):
        op.create_index(
            "ix_offer_proposals_company_department",
            "offer_proposals",
            ["company_id", "department_id"],
        )


def downgrade() -> None:
    if _index_exists("offer_proposals", "ix_offer_proposals_company_department"):
        op.drop_index("ix_offer_proposals_company_department", table_name="offer_proposals")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("offer_proposals")}
    if "fk_offer_proposals_department_id" in existing_fks:
        op.drop_constraint(
            "fk_offer_proposals_department_id",
            "offer_proposals",
            type_="foreignkey",
        )

    if _column_exists("offer_proposals", "department_id"):
        op.drop_column("offer_proposals", "department_id")
