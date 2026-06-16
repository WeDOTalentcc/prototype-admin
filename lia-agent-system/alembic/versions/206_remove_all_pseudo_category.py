"""remove "all" pseudo-category from agent_categories

Revision ID: 206
Revises: 205
Create Date: 2026-05-26

Contexto Paulo 2026-05-26:
A categoria "all" foi seedada em 199_seed_agent_template_catalog.py como pseudo-categoria
("Todos" / "All") com sort_order=0. Frontend (TemplateGallery.tsx) já hardcoded "Todos"
como primeiro chip filter — resultado: DUPLICATE KEY warning em React render porque
2 chips com id="all" eram criados.

Decisao canonical: "all" nao e categoria real, e UX filter. Single source of truth:
- Backend NAO seeda "all".
- Frontend mantem "Todos" hardcoded como primeiro chip (UX intent original).

Esta migration apaga a row "all" das categorias seedadas.
"""
from alembic import op

revision = "206"
down_revision = "205"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM agent_categories WHERE id = 'all'")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO agent_categories (id, label_pt, label_en, icon, sort_order, is_active)
        VALUES ('all', 'Todos', 'All', 'LayoutGrid', 0, true)
        ON CONFLICT (id) DO NOTHING
        """
    )
