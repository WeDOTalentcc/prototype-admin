"""TDD: RLS deny-by-default on `search_feedbacks` table (Onda A.2).

Migration 222 adds company_id + RLS to search_feedbacks. Antes dela a tabela
nao tinha company_id nem RLS — isolamento entre empresas inexistente (o comentario
"Task #1143 RLS" em app/api/v1/search_feedback.py era aspiracional). Este sensor pina:
  1. RLS habilitado (rowsecurity = true)
  2. SET app.company_id ISOLA — SELECT cross-tenant retorna vazio
  3. INSERT com company_id divergente e rejeitado (WITH CHECK policy)
  4. Operacoes same-tenant funcionam

RED ate migration 222 ser aplicada (alembic upgrade head); GREEN apos.
Espelha tests/integration/test_rls_candidates.py (padrao 118_rls_candidates).
psycopg2 sync (RLS e SQL puro, sem valor async).

Skill: tdd-workflow + harness-engineering (sensor computacional).
"""
from __future__ import annotations

import os
import uuid

import pytest

try:
    import psycopg2  # type: ignore[import-not-found]
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


pytestmark = pytest.mark.skipif(
    not HAS_PSYCOPG2 or not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL or psycopg2 not available",
)

TABLE = "search_feedbacks"


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _set_tenant(cur, company_id: str) -> None:
    cur.execute("SET ROLE lia_app")
    cur.execute("SET LOCAL app.company_id = %s", (company_id,))


@pytest.fixture
def two_tenants():
    """Insere 2 feedbacks de 2 tenants (como superuser, bypassa RLS). Limpa depois."""
    tenant_a = f"test_rls_a_{uuid.uuid4().hex[:8]}"
    tenant_b = f"test_rls_b_{uuid.uuid4().hex[:8]}"
    fb_a_id = str(uuid.uuid4())
    fb_b_id = str(uuid.uuid4())

    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for fid, tid, cand in (
                (fb_a_id, tenant_a, "cand_a"),
                (fb_b_id, tenant_b, "cand_b"),
            ):
                cur.execute(
                    f"""
                    INSERT INTO {TABLE}
                        (id, company_id, candidate_id, user_id, feedback_type, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'like', NOW(), NOW())
                    """,
                    (fid, tid, cand, "test_user"),
                )
    finally:
        conn.close()

    yield {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "fb_a": fb_a_id,
        "fb_b": fb_b_id,
    }

    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} WHERE company_id = ANY(%s)",
                ([tenant_a, tenant_b],),
            )
    finally:
        conn.close()


def test_search_feedbacks_rls_is_enabled():
    """Pin: migration 222 habilitou RLS em search_feedbacks."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT rowsecurity FROM pg_tables WHERE tablename = '{TABLE}'"
            )
            row = cur.fetchone()
            assert row is not None and row[0] is True, (
                "RLS nao habilitado em search_feedbacks — migration 222 nao aplicada"
            )
    finally:
        conn.close()


def test_search_feedbacks_rls_blocks_cross_tenant_select(two_tenants):
    """Sessao do tenant A nao pode ver feedback do tenant B."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                f"SELECT id FROM {TABLE} WHERE id = %s", (two_tenants["fb_b"],)
            )
            assert cur.fetchone() is None, "RLS vazou feedback cross-tenant no SELECT"
            # mas enxerga o proprio
            cur.execute(
                f"SELECT id FROM {TABLE} WHERE id = %s", (two_tenants["fb_a"],)
            )
            assert cur.fetchone() is not None, "RLS bloqueou o proprio tenant"
    finally:
        conn.rollback()
        conn.close()


def test_search_feedbacks_rls_blocks_cross_tenant_insert(two_tenants):
    """INSERT com company_id de outro tenant deve ser rejeitado pela WITH CHECK."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            with pytest.raises(psycopg2.errors.lookup("42501")):  # insufficient_privilege / RLS violation
                cur.execute(
                    f"""
                    INSERT INTO {TABLE}
                        (id, company_id, candidate_id, user_id, feedback_type, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'like', NOW(), NOW())
                    """,
                    (str(uuid.uuid4()), two_tenants["tenant_b"], "x", "u", ),
                )
    finally:
        conn.rollback()
        conn.close()


def test_search_feedbacks_same_tenant_insert_works(two_tenants):
    """INSERT com company_id == app.company_id funciona."""
    conn = _conn()
    new_id = str(uuid.uuid4())
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                f"""
                INSERT INTO {TABLE}
                    (id, company_id, candidate_id, user_id, feedback_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'dislike', NOW(), NOW())
                """,
                (new_id, two_tenants["tenant_a"], "candx", "u"),
            )
        conn.commit()
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(f"SELECT id FROM {TABLE} WHERE id = %s", (new_id,))
            assert cur.fetchone() is not None
    finally:
        conn.rollback()
        # cleanup
        c2 = _conn(); c2.autocommit = True
        with c2.cursor() as cur:
            cur.execute(f"DELETE FROM {TABLE} WHERE id = %s", (new_id,))
        c2.close()
        conn.close()
