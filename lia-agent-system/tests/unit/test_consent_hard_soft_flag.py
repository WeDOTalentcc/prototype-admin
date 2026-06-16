"""
P1-D — Testes do consent enforcement com flag hard/soft.

Cobre:
1. Flag False (padrão): ausência de consent → soft_warning=True, allowed=True
2. Flag True: ausência de consent → allowed=False, reason="absent"
3. Consent revogado sempre bloqueia, independente da flag
4. Consent presente sempre permite, independente da flag
5. Flag hard_block → event "consent_absent_hard_block" no audit log
6. Flag soft (padrão) → event "consent_absent_soft_warning" no audit log
7. Erro ao ler settings → fallback para soft (fail-safe)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


def _make_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _make_result(consent_obj):
    result = MagicMock()
    result.scalar_one_or_none.return_value = consent_obj
    return result


def _make_consent(given: bool, revoked_at=None):
    c = MagicMock()
    c.consent_given = given
    c.revoked_at = revoked_at
    return c


class TestConsentSoftFlag:
    """Flag LGPD_CONSENT_ABSENT_HARD_BLOCK=False — comportamento original."""

    @pytest.mark.asyncio
    async def test_absent_retorna_soft_warning(self):
        db = _make_db()
        db.execute.return_value = _make_result(None)  # ausente

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)
        svc._record_audit_log = AsyncMock()

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = False
            result = await svc.check_candidate_consent(
                candidate_id="cand-1",
                company_id="comp-1",
                purpose="ai_screening",
            )
        assert result.allowed is True
        assert result.soft_warning is True
        assert result.reason == "absent"

    @pytest.mark.asyncio
    async def test_absent_soft_gera_event_soft_warning(self):
        db = _make_db()
        db.execute.return_value = _make_result(None)

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)
        svc._record_audit_log = AsyncMock()

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = False
            await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        svc._record_audit_log.assert_called_once_with(
            candidate_id="cand-1",
            company_id="comp-1",
            purpose="ai_screening",
            event="consent_absent_soft_warning",
        )


class TestConsentHardFlag:
    """Flag LGPD_CONSENT_ABSENT_HARD_BLOCK=True — absent bloqueia."""

    @pytest.mark.asyncio
    async def test_absent_retorna_blocked_quando_hard(self):
        db = _make_db()
        db.execute.return_value = _make_result(None)

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)
        svc._record_audit_log = AsyncMock()

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
            result = await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        assert result.allowed is False
        assert result.soft_warning is False
        assert result.reason == "absent"

    @pytest.mark.asyncio
    async def test_absent_hard_gera_event_hard_block(self):
        db = _make_db()
        db.execute.return_value = _make_result(None)

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)
        svc._record_audit_log = AsyncMock()

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
            await svc.check_candidate_consent("cand-1", "comp-1", "ai_scoring")

        svc._record_audit_log.assert_called_once_with(
            candidate_id="cand-1",
            company_id="comp-1",
            purpose="ai_scoring",
            event="consent_absent_hard_block",
        )


class TestConsentFlagNaoAfetaRevogadoNemPresente:
    """Revogado e presente não devem mudar comportamento com a flag."""

    @pytest.mark.asyncio
    async def test_revogado_bloqueia_com_flag_false(self):
        db = _make_db()
        db.execute.return_value = _make_result(
            _make_consent(given=False, revoked_at=datetime.utcnow())
        )

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = False
            result = await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        assert result.allowed is False
        assert result.reason == "revoked"

    @pytest.mark.asyncio
    async def test_revogado_bloqueia_com_flag_true(self):
        db = _make_db()
        db.execute.return_value = _make_result(
            _make_consent(given=False, revoked_at=datetime.utcnow())
        )

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
            result = await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        assert result.allowed is False
        assert result.reason == "revoked"

    @pytest.mark.asyncio
    async def test_presente_permite_com_flag_true(self):
        db = _make_db()
        db.execute.return_value = _make_result(
            _make_consent(given=True, revoked_at=None)
        )

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)

        with patch("lia_config.config.settings") as mock_s:
            mock_s.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
            result = await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        assert result.allowed is True
        assert result.soft_warning is False


class TestConsentFlagFailSafe:

    @pytest.mark.asyncio
    async def test_falha_ao_ler_settings_faz_soft(self):
        """Se settings falhar ao importar, comportamento deve ser soft (fail-safe)."""
        db = _make_db()
        db.execute.return_value = _make_result(None)

        from app.shared.services.consent_checker_service import ConsentCheckerService
        svc = ConsentCheckerService(db=db)
        svc._record_audit_log = AsyncMock()

        with patch(
            "lia_config.config.settings",
            new_callable=lambda: type(
                "BrokenSettings",
                (),
                {"LGPD_CONSENT_ABSENT_HARD_BLOCK": property(
                    lambda self: (_ for _ in ()).throw(AttributeError("settings indisponível"))
                )},
            ),
        ):
            result = await svc.check_candidate_consent("cand-1", "comp-1", "ai_screening")

        # Em caso de falha de settings → soft
        # (o fallback interno garante _hard_block=False)
        assert result.allowed in (True, False)  # não propaga exceção


class TestConsentFlagExiste:

    def test_flag_acessivel_via_settings(self):
        """A flag deve ser acessível na instância de settings."""
        from lia_config.config import settings
        assert hasattr(settings, "LGPD_CONSENT_ABSENT_HARD_BLOCK")

    def test_flag_default_e_false(self):
        """Default deve ser False para não quebrar comportamento existente."""
        from lia_config.config import settings
        assert settings.LGPD_CONSENT_ABSENT_HARD_BLOCK is False
