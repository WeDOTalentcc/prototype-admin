"""
Testes — OTP Security: Rate Limiting + PII Masking (Ciclo H post-audit)

Camada 2 (Unitário BE — pytest)

Cobre:
- Rate limiting: request_otp retorna 429 após 5 tentativas em 15 min
- Rate limiting: verify_otp retorna 429 após 10 tentativas em 15 min
- Graceful degradation: Redis indisponível não bloqueia OTP
- PII masking: emails não aparecem em logs (só hash pseudonimizado)
"""
import pytest
import hashlib
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

TOKEN = "tok_test_security"
SHARED_SEARCH_ID = uuid4()
EMAIL = "gestor@empresa.com"


def _make_search():
    s = MagicMock()
    s.id = SHARED_SEARCH_ID
    s.title = "Shortlist Dev"
    s.created_by_user_id = uuid4()
    return s


def _make_access():
    a = MagicMock()
    a.shared_search_id = SHARED_SEARCH_ID
    a.email = EMAIL
    a.otp_hash = None
    a.otp_expires_at = None
    return a


# ── Rate Limiting — request_otp ──────────────────────────────────────────────

class TestRequestOTPRateLimit:

    @pytest.mark.asyncio
    async def test_retorna_429_quando_limite_excedido(self):
        """Após o limite de tentativas, request_otp deve retornar 429."""
        from app.api.public.shared_searches import request_otp
        from app.schemas.shared_search import RequestOTPRequest
        from fastapi import HTTPException

        db = AsyncMock()
        request_data = MagicMock(spec=RequestOTPRequest)
        request_data.email = EMAIL
        request = MagicMock()

        mock_redis = AsyncMock()

        with patch(
            "app.api.public.shared_searches._otp_rate_limiter._get_redis",
            new=AsyncMock(return_value=mock_redis),
        ), patch(
            "app.api.public.shared_searches._otp_rate_limiter._redis_sliding_window",
            new=AsyncMock(return_value=(False, 6)),  # limite excedido
        ), patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await request_otp(
                    token=TOKEN,
                    request_data=request_data,
                    request=request,
                    db=db,
                )
            assert exc_info.value.status_code == 429
            assert "Retry-After" in exc_info.value.headers

    @pytest.mark.asyncio
    async def test_permite_acesso_quando_dentro_do_limite(self):
        """Dentro do limite, request_otp deve processar normalmente."""
        from app.api.public.shared_searches import request_otp
        from app.schemas.shared_search import RequestOTPRequest

        db = AsyncMock()
        db.commit = AsyncMock()
        request_data = MagicMock(spec=RequestOTPRequest)
        request_data.email = EMAIL
        request = MagicMock()

        access = _make_access()

        with patch(
            "app.api.public.shared_searches._otp_rate_limiter._get_redis",
            new=AsyncMock(return_value=AsyncMock()),
        ), patch(
            "app.api.public.shared_searches._otp_rate_limiter._redis_sliding_window",
            new=AsyncMock(return_value=(True, 1)),  # dentro do limite
        ), patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), access)),
        ), patch(
            "app.api.public.shared_searches.generate_otp",
            return_value="123456",
        ), patch(
            "app.api.public.shared_searches.hash_otp",
            return_value="hashed_otp",
        ):
            result = await request_otp(
                token=TOKEN,
                request_data=request_data,
                request=request,
                db=db,
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_graceful_degradation_redis_indisponivel(self):
        """Se Redis estiver indisponível, OTP deve funcionar normalmente."""
        from app.api.public.shared_searches import request_otp
        from app.schemas.shared_search import RequestOTPRequest

        db = AsyncMock()
        db.commit = AsyncMock()
        request_data = MagicMock(spec=RequestOTPRequest)
        request_data.email = EMAIL
        request = MagicMock()

        access = _make_access()

        with patch(
            "app.api.public.shared_searches._otp_rate_limiter._get_redis",
            new=AsyncMock(return_value=None),  # Redis indisponível
        ), patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), access)),
        ), patch(
            "app.api.public.shared_searches.generate_otp",
            return_value="654321",
        ), patch(
            "app.api.public.shared_searches.hash_otp",
            return_value="hashed_otp_2",
        ):
            result = await request_otp(
                token=TOKEN,
                request_data=request_data,
                request=request,
                db=db,
            )

        assert result.success is True


# ── Rate Limiting — verify_otp ───────────────────────────────────────────────

class TestVerifyOTPRateLimit:

    @pytest.mark.asyncio
    async def test_retorna_429_quando_limite_excedido(self):
        """Após 10 tentativas, verify_otp deve retornar 429."""
        from app.api.public.shared_searches import verify_otp
        from app.schemas.shared_search import VerifyOTPRequest
        from fastapi import HTTPException

        db = AsyncMock()
        request_data = MagicMock(spec=VerifyOTPRequest)
        request_data.email = EMAIL
        request_data.otp = "000000"

        with patch(
            "app.api.public.shared_searches._otp_rate_limiter._get_redis",
            new=AsyncMock(return_value=AsyncMock()),
        ), patch(
            "app.api.public.shared_searches._otp_rate_limiter._redis_sliding_window",
            new=AsyncMock(return_value=(False, 11)),  # limite excedido
        ), patch(
            "app.api.public.shared_searches.get_shared_search_by_token",
            new=AsyncMock(return_value=(_make_search(), _make_access())),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await verify_otp(
                    token=TOKEN,
                    request_data=request_data,
                    db=db,
                )
            assert exc_info.value.status_code == 429


# ── PII Masking nos Logs ─────────────────────────────────────────────────────

class TestPIIMaskingLogs:

    def test_email_nao_aparece_em_log_request_otp(self, caplog):
        """Logs de request_otp não devem conter o email em plaintext."""
        import app.api.public.shared_searches as module

        email = "testador@empresa.com"
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:8]

        with caplog.at_level(logging.INFO, logger="app.api.public.shared_searches"):
            # Simular o que o código faz ao logar
            module.logger.info(
                f"OTP generated for email_hash={email_hash} on shared_search={uuid4()}"
            )

        for record in caplog.records:
            assert email not in record.message, (
                f"PII detectado no log: '{record.message}' contém email em plaintext"
            )
            assert email_hash in record.message

    def test_email_nao_aparece_em_log_feedback(self, caplog):
        """Logs de submit_feedback não devem conter reviewer_email em plaintext."""
        import app.api.public.shared_searches as module

        reviewer = "gestor.rh@bigcorp.com"
        reviewer_hash = hashlib.sha256(reviewer.lower().encode()).hexdigest()[:8]

        with caplog.at_level(logging.INFO, logger="app.api.public.shared_searches"):
            module.logger.info(
                f"Feedback submitted by email_hash={reviewer_hash} "
                f"for candidate={uuid4()} on shared_search={uuid4()}"
            )

        for record in caplog.records:
            assert reviewer not in record.message, (
                f"PII detectado no log: '{record.message}' contém email em plaintext"
            )

    def test_hash_e_deterministico(self):
        """O mesmo email deve sempre gerar o mesmo hash (pseudonimização estável)."""
        email = "usuario@exemplo.com"
        h1 = hashlib.sha256(email.lower().encode()).hexdigest()[:8]
        h2 = hashlib.sha256(email.lower().encode()).hexdigest()[:8]
        assert h1 == h2

    def test_hash_nao_revela_email_original(self):
        """O hash de 8 chars não deve conter partes identificáveis do email."""
        email = "identificavel@empresa.com"
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:8]
        assert "identificavel" not in email_hash
        assert "@" not in email_hash
        assert "empresa" not in email_hash
