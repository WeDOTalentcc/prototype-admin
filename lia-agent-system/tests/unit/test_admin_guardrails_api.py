"""
Testes unitários para a API de Guardrails — Sprint I1.

Cobertura:
- GuardrailRepository.soft_delete() — retorna True/False corretamente
- Seed defaults — idempotência (não duplica)
- DELETE endpoint — soft delete via repository
- POST /seed-defaults — cria primários e secundários
- updated_at presente na resposta
- Guardrails padrão cobrem anti-discriminação e privacidade
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_guardrail(
    id="uuid-1",
    level="primary",
    rule="Regra de teste",
    blocking_message="Bloqueado",
    domain=None,
    is_active=True,
    company_id=None,
):
    g = MagicMock()
    g.id = id
    g.level = level
    g.rule = rule
    g.blocking_message = blocking_message
    g.domain = domain
    g.node = None
    g.tool = None
    g.is_active = is_active
    g.company_id = company_id
    g.updated_by = "system"
    g.updated_at = datetime(2026, 3, 9, 12, 0, 0)
    g.created_at = datetime(2026, 3, 9, 12, 0, 0)
    return g


# ---------------------------------------------------------------------------
# GuardrailRepository.soft_delete
# ---------------------------------------------------------------------------

class TestSoftDelete:

    @pytest.mark.asyncio
    async def test_soft_delete_existing_returns_true(self):
        from app.shared.compliance.guardrail_repository import GuardrailRepository

        db = AsyncMock()
        guardrail = _make_guardrail(is_active=True)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = guardrail
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        result = await GuardrailRepository.soft_delete(db, "uuid-1")

        assert result is True
        assert guardrail.is_active is False
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent_returns_false(self):
        from app.shared.compliance.guardrail_repository import GuardrailRepository

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        result = await GuardrailRepository.soft_delete(db, "nao-existe")

        assert result is False
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_data(self):
        """Soft delete deve apenas mudar is_active, não deletar o registro."""
        from app.shared.compliance.guardrail_repository import GuardrailRepository

        db = AsyncMock()
        guardrail = _make_guardrail(rule="Regra importante", is_active=True)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = guardrail
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()

        await GuardrailRepository.soft_delete(db, "uuid-1")

        # Dado preservado — apenas is_active muda
        assert guardrail.rule == "Regra importante"
        assert guardrail.is_active is False
        db.delete.assert_not_called()  # NUNCA chama delete real


# ---------------------------------------------------------------------------
# Guardrails padrão — conteúdo e cobertura
# ---------------------------------------------------------------------------

class TestDefaultGuardrails:

    def _get_defaults(self):
        from app.api.v1.guardrails import DEFAULT_PRIMARY_GUARDRAILS, DEFAULT_SECONDARY_GUARDRAILS
        return DEFAULT_PRIMARY_GUARDRAILS, DEFAULT_SECONDARY_GUARDRAILS

    def test_primary_guardrails_count(self):
        primaries, _ = self._get_defaults()
        assert len(primaries) == 5

    def test_secondary_guardrails_count(self):
        _, secondaries = self._get_defaults()
        assert len(secondaries) == 4

    def test_all_defaults_have_required_fields(self):
        primaries, secondaries = self._get_defaults()
        for item in primaries + secondaries:
            assert "level" in item
            assert "rule" in item
            assert "blocking_message" in item
            assert len(item["rule"]) > 10

    def test_primaries_have_level_primary(self):
        primaries, _ = self._get_defaults()
        for item in primaries:
            assert item["level"] == "primary"

    def test_secondaries_have_domain(self):
        _, secondaries = self._get_defaults()
        for item in secondaries:
            assert "domain" in item
            assert item["domain"] is not None

    def test_anti_discrimination_rule_present(self):
        primaries, _ = self._get_defaults()
        rules = [item["rule"] for item in primaries]
        assert any("discriminar" in r.lower() or "discriminação" in r.lower() for r in rules)

    def test_privacy_rule_present(self):
        primaries, _ = self._get_defaults()
        rules = [item["rule"] for item in primaries]
        assert any("dados pessoais" in r.lower() or "privacidade" in r.lower() for r in rules)

    def test_ai_disclosure_rule_present(self):
        primaries, _ = self._get_defaults()
        rules = [item["rule"] for item in primaries]
        assert any("ia" in r.lower() or "inteligência artificial" in r.lower() for r in rules)

    def test_secondaries_cover_required_domains(self):
        _, secondaries = self._get_defaults()
        domains = {item["domain"] for item in secondaries}
        assert "cv_screening" in domains
        assert "communication" in domains
        assert "sourcing" in domains
        assert "job_management" in domains


# ---------------------------------------------------------------------------
# Seed defaults — idempotência
# ---------------------------------------------------------------------------

class TestSeedDefaults:

    @pytest.mark.asyncio
    async def test_seed_creates_all_when_empty(self):
        from app.api.v1.guardrails import seed_default_guardrails

        db = AsyncMock()
        # Nenhum guardrail existente — scalar_one_or_none retorna None
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.api.v1.guardrails.GuardrailRepository.upsert",
            new_callable=AsyncMock,
            return_value=_make_guardrail(),
        ):
            from unittest.mock import MagicMock as MM
            request = MM()
            response = await seed_default_guardrails(company_id=None, db=db)

        # 5 primários + 4 secundários = 9 total
        assert response.total == 9
        assert response.created == 9
        assert response.skipped == 0

    @pytest.mark.asyncio
    async def test_seed_skips_existing(self):
        from app.api.v1.guardrails import seed_default_guardrails

        db = AsyncMock()
        # Todos já existem
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = _make_guardrail()
        db.execute = AsyncMock(return_value=result_mock)

        with patch("app.api.v1.guardrails.GuardrailRepository.upsert", new_callable=AsyncMock) as mock_upsert:
            response = await seed_default_guardrails(company_id=None, db=db)

        assert response.skipped == 9
        assert response.created == 0
        mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_seed_partial_existing(self):
        from app.api.v1.guardrails import seed_default_guardrails

        db = AsyncMock()
        call_count = 0

        async def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            # Primeiros 5 existem, últimos 4 não
            result.scalar_one_or_none.return_value = _make_guardrail() if call_count <= 5 else None
            return result

        db.execute = execute_side_effect

        with patch(
            "app.api.v1.guardrails.GuardrailRepository.upsert",
            new_callable=AsyncMock,
            return_value=_make_guardrail(),
        ):
            response = await seed_default_guardrails(company_id=None, db=db)

        assert response.created == 4
        assert response.skipped == 5
        assert response.total == 9


# ---------------------------------------------------------------------------
# GuardrailResponse — updated_at presente
# ---------------------------------------------------------------------------

class TestGuardrailResponseSchema:

    def test_response_includes_updated_at(self):
        from app.api.v1.guardrails import GuardrailResponse

        guardrail = _make_guardrail()
        response = GuardrailResponse.from_orm(guardrail)

        assert response.updated_at is not None
        assert isinstance(response.updated_at, datetime)

    def test_response_updated_at_none_allowed(self):
        """updated_at pode ser None para registros antigos sem esse campo."""
        from app.api.v1.guardrails import GuardrailResponse

        guardrail = _make_guardrail()
        guardrail.updated_at = None
        response = GuardrailResponse.from_orm(guardrail)

        assert response.updated_at is None
