"""triagem: SECURITY DEFINER function to resolve tenant from public token (RLS bypass canonical)

Sprint 4 B.2 — P0 regressão da Sprint 4 B.1 (commit ca62339cb).

Background:
- Sprint 4 B.1 (ca62339cb) tornou rotas /api/v1/triagem/{token}/* PUBLIC via
  PUBLIC_REGEX_PATHS no AuthEnforcementMiddleware (sem JWT).
- triagem_sessions tem FORCE ROW LEVEL SECURITY + politicas que filtram por
  current_setting('app.company_id'). Sem JWT, request.state.company_id = None,
  set_tenant_context NUNCA roda, app.company_id permanece NULL.
- Query SELECT * FROM triagem_sessions WHERE token = X executa sob role
  lia_app (NOBYPASSRLS) com app.company_id NULL → policy filtra → 0 rows → 404.
- Resultado: candidato recebe 404 "Token inválido" em endpoint público
  legitimamente. Triagem em produção quebrada desde Sprint 4 B.1.

Fix canonical:
- Cria função resolve_triagem_session_by_token(text) com SECURITY DEFINER,
  owner = postgres (BYPASSRLS via ownership). Função roda como owner, então
  RLS é bypassed dentro dela. Retorna a row da triagem_sessions.
- TriagemSessionRepository.get_session_by_token usa essa função em vez de
  select(TriagemSession) direto. Depois de resolver, service chama
  set_tenant_context(session.company_id) para queries subsequentes na mesma
  request operarem normalmente sob RLS.

Por que SECURITY DEFINER vs. outras alternativas:
- SET LOCAL row_security = off não bypassa RLS para non-superuser (só muda
  err vs filter behavior). Testado: lia_app continua retornando 0 rows.
- ALTER lia_app BYPASSRLS dissolve o modelo de segurança inteiro
  (toda query de toda request passaria a ignorar RLS).
- Adicionar política "NULL ctx = allow" abre brecha cross-tenant em outras
  queries que esquecerem de setar contexto.
- SECURITY DEFINER é minimal-surface: o bypass é ESCOPADO a 1 função, 1
  query, com 1 parâmetro de input (token). Segurança = scrutinizar 1 função
  vs. revisitar todo o middleware.

Segurança:
- Token é UUID v4 não-guessable (36 chars, ~10^36 espaço).
- Função aceita SOMENTE token-equality lookup (sem LIKE, sem subquery,
  sem chamada recursiva). SQL injection impossível com parameter binding.
- Função NÃO atualiza nada. Read-only.
- GRANT EXECUTE somente para lia_app (não PUBLIC).

Refs:
- AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md
- Sprint 4 B.1 commit ca62339cb (PUBLIC routes declared)
- Decisão Paulo 2026-05-23 — fix P0 production blocker
"""
from alembic import op

revision = "187_triagem_resolve_tenant_secdef"
down_revision = "186_revert_in_app_enabled"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION resolve_triagem_session_by_token(
            p_token text
        )
        RETURNS SETOF triagem_sessions
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = public, pg_temp
        AS $$
            SELECT *
            FROM triagem_sessions
            WHERE token = p_token
            LIMIT 1;
        $$;
        """
    )
    # Owner = postgres (default for current_user during migration).
    # SECURITY DEFINER runs as owner, bypassing RLS.
    op.execute(
        "REVOKE ALL ON FUNCTION resolve_triagem_session_by_token(text) FROM PUBLIC;"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION resolve_triagem_session_by_token(text) TO lia_app;"
    )

    op.execute(
        """
        COMMENT ON FUNCTION resolve_triagem_session_by_token(text) IS
        'Bypassa RLS para resolver triagem_sessions a partir do token público '
        '(UUID v4 não-guessable). Usado APENAS pelo TriagemSessionRepository '
        'em endpoints PUBLIC (candidato sem JWT). Após resolver, caller DEVE '
        'chamar set_tenant_context(session.company_id) para queries subsequentes. '
        'Read-only. Sprint 4 B.2 (P0 fix regressão ca62339cb).';
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS resolve_triagem_session_by_token(text);")
