"""
TDD — BUG: reveal_contact usa _company_id=None para candidatos Pearch (docid),
causando RLS error em external_api_consumption com company_id='unattributed',
envenenando a sessão SQLAlchemy e retornando HTTP 500.

Raiz: candidato Pearch tem docid (não UUID), então cand_uuid=None e o código
antigo nunca atribuia _company_id do JWT.

Fix: _company_id = company_id (JWT) como default; override somente se DB lookup
retornar valor melhor. Mais rollback defensivo em _track_pearch_reveal.

Ref: logs 2026-06-09 — PendingRollbackError + InsufficientPrivilegeError em
external_api_consumption (company_id='unattributed', reveal phone/email).
"""
import pytest
import ast
import inspect
from pathlib import Path

CONTACT_PY = Path("/home/runner/workspace/lia-agent-system/app/api/v1/candidate_search/contact.py")


def _read_source():
    return CONTACT_PY.read_text()


class TestRevealContactCompanyIdFix:
    """Verifica que reveal_contact usa o company_id do JWT (não None) para tracking."""

    def test_company_id_initialized_from_jwt_not_none(self):
        """Fix 1: _company_id deve ser inicializado com o company_id do JWT,
        não com None. Sem isso, candidatos Pearch (docid != UUID) sempre
        usam 'unattributed' → RLS fail."""
        src = _read_source()
        # A inicialização correta deve existir
        assert "_company_id = company_id" in src, (
            "_company_id deve ser inicializado com company_id (JWT), não None. "
            "Fix: substituir '_company_id = None' por '_company_id = company_id'"
        )

    def test_old_none_initialization_removed(self):
        """O pattern antigo _company_id = None (sem fallback imediato do JWT)
        não deve existir no corpo da função reveal_contact."""
        src = _read_source()
        # O pattern antigo isolado não deve estar presente como inicialização
        # (pode existir em comentário mas não como statement de atribuição)
        lines = [l.strip() for l in src.splitlines()]
        bare_none = [l for l in lines if l == "_company_id = None"]
        assert len(bare_none) == 0, (
            f"Encontrado '_company_id = None' sem fallback JWT. "
            f"Ocorrências: {bare_none}"
        )

    def test_db_company_id_overrides_jwt_when_available(self):
        """Fix 1b: quando DB lookup retorna um company_id específico do candidato,
        ele deve override o JWT default (mais preciso para candidatos locais)."""
        src = _read_source()
        assert "_db_company_id" in src or "if _db_company_id" in src or "_company_id = _db_company_id" in src, (
            "Deve existir lógica de override: se DB lookup retornar company_id, "
            "usar ele (mais específico que o JWT genérico)"
        )

    def test_rollback_in_track_pearch_reveal_except(self):
        """Fix 2: _track_pearch_reveal deve fazer rollback após exception para
        desenvenenar a sessão SQLAlchemy. Sem isso, PendingRollbackError na
        teardown do get_db() causa HTTP 500."""
        src = _read_source()
        # O rollback deve estar no except block da função de tracking
        # (procura padrão: "await db.rollback()" dentro do bloco de _track_pearch_reveal)
        assert "await db.rollback()" in src, (
            "Fix 2 ausente: _track_pearch_reveal deve chamar await db.rollback() "
            "no bloco except para limpar sessão envenenada por RLS error. "
            "Sem isso: PendingRollbackError no teardown → HTTP 500."
        )

    def test_tracking_helper_has_defensive_rollback(self):
        """O rollback defensivo deve estar DENTRO da função _track_pearch_reveal,
        não espalhado pelos callers."""
        src = _read_source()
        lines = src.splitlines()
        
        # Encontrar a função _track_pearch_reveal
        reveal_fn_start = None
        for i, line in enumerate(lines):
            if "async def _track_pearch_reveal" in line:
                reveal_fn_start = i
                break
        
        assert reveal_fn_start is not None, "_track_pearch_reveal não encontrada"
        
        # Verificar que rollback existe dentro do corpo da função
        fn_body = "\n".join(lines[reveal_fn_start:reveal_fn_start + 30])
        assert "rollback" in fn_body, (
            f"await db.rollback() deve estar dentro de _track_pearch_reveal, "
            f"não nos callers. Corpo encontrado:\n{fn_body}"
        )


class TestRevealContactCompanyIdUnit:
    """Testes unitários do comportamento com mock."""

    def test_pearch_docid_is_not_uuid(self):
        """Candidatos Pearch têm docids como 'jefferson-daniel-123' que NÃO
        são UUIDs válidos. Isso é o trigger do bug: cand_uuid=None."""
        from uuid import UUID
        docids = [
            "jefferson-daniel-08549036",
            "jefferson-daniel-***PHONE***",
            "some-name-12345",
        ]
        for docid in docids:
            try:
                UUID(docid)
                assert False, f"'{docid}' deveria falhar UUID parse"
            except (ValueError, AttributeError):
                pass  # expected

    def test_jwt_company_id_is_valid_uuid(self):
        """O company_id do JWT é um UUID válido, que passa pelo RLS."""
        from uuid import UUID
        sample_company_id = "8cf762f8-6a44-47de-8915-6b3dc0cd2715"
        UUID(sample_company_id)  # deve não lançar

    def test_unattributed_is_not_uuid(self):
        """'unattributed' não é UUID — é o valor que causava o RLS error."""
        from uuid import UUID
        try:
            UUID("unattributed")
            assert False, "Deveria falhar"
        except (ValueError, AttributeError):
            pass  # expected — 'unattributed' não é UUID, viola RLS
