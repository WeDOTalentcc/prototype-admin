"""
VoiceChannelAdapter.check_status canonical contract — P1 backlog ticket.

Sprint 3.4 entregou check_status como placeholder retornando sempre QUEUED
(vide tests/contract/test_voice_channel_adapter.py:test_check_status_returns_queued_baseline).
Esta sprint substitui a baseline por real implementation: lê
VoiceSessionRedisRepository e mapeia session.status interno -> DeliveryStatus
canonical.

Mapping canonical (status interno do VoiceScreeningSession + valores
forward-compat do canonical voice core):
    pending           -> QUEUED   (session criada, ainda nao iniciada)
    consent_pending   -> QUEUED   (forward-compat com canonical voice core)
    initiated         -> SENT     (call dispatched ao provider)
    ringing           -> SENT     (forward-compat)
    ready             -> DELIVERED (Gemini Live conectado)
    in_progress       -> DELIVERED (forward-compat)
    active            -> DELIVERED (forward-compat)
    analyzing         -> DELIVERED (audio captured, em transcribe/scoring)
    completed         -> READ      (terminou com sucesso)
    finalized         -> READ      (forward-compat)
    failed            -> FAILED
    analysis_failed   -> FAILED    (capturou mas falhou analise)
    fallback          -> FAILED    (Gemini indisponivel, foi pra chat)
    <unknown>         -> QUEUED    (defensive default)

Multi-tenancy: company_id resolvido via find_company_id_for_session (reverse
index), nunca confiado em input externo.

Graceful degradation: qualquer exception interna -> FAILED + log warning.
Session expired ou nao encontrado -> FAILED.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.shared.channels.adapters.voice_adapter import VoiceChannelAdapter
from app.shared.channels.channel_adapter import DeliveryStatus


@pytest.fixture
def adapter() -> VoiceChannelAdapter:
    return VoiceChannelAdapter()


class TestCheckStatusMappings:
    """Para cada status interno conhecido, verifica mapeamento canonical."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "internal_status,expected_delivery",
        [
            # current values in VoiceScreeningSession
            ("pending", DeliveryStatus.QUEUED),
            ("initiated", DeliveryStatus.SENT),
            ("ready", DeliveryStatus.DELIVERED),
            ("analyzing", DeliveryStatus.DELIVERED),
            ("completed", DeliveryStatus.READ),
            ("analysis_failed", DeliveryStatus.FAILED),
            ("failed", DeliveryStatus.FAILED),
            ("fallback", DeliveryStatus.FAILED),
            # forward-compat canonical values (voice core)
            ("consent_pending", DeliveryStatus.QUEUED),
            ("ringing", DeliveryStatus.SENT),
            ("in_progress", DeliveryStatus.DELIVERED),
            ("active", DeliveryStatus.DELIVERED),
            ("finalized", DeliveryStatus.READ),
        ],
    )
    async def test_status_mapping(
        self,
        adapter: VoiceChannelAdapter,
        internal_status: str,
        expected_delivery: DeliveryStatus,
    ) -> None:
        """Cada status interno conhecido mapeia para o DeliveryStatus canonical."""
        session_id = "sess-test-123"
        company_id = "company-abc"

        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value=company_id)
            mock_repo.load_session_state = AsyncMock(
                return_value={"status": internal_status, "session_id": session_id}
            )
            mock_factory.return_value = mock_repo

            result = await adapter.check_status(session_id)
            assert result == expected_delivery


class TestCheckStatusEdgeCases:
    @pytest.mark.asyncio
    async def test_session_unknown_returns_failed(self, adapter: VoiceChannelAdapter) -> None:
        """Reverse index vazio (session expirou ou nunca existiu) -> FAILED."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value=None)
            mock_factory.return_value = mock_repo

            result = await adapter.check_status("expired-session-id")
            assert result == DeliveryStatus.FAILED

    @pytest.mark.asyncio
    async def test_session_state_none_returns_failed(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """Reverse index aponta company mas load_session_state retorna None
        (race entre reverse index + state TTL) -> FAILED."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value="company-x")
            mock_repo.load_session_state = AsyncMock(return_value=None)
            mock_factory.return_value = mock_repo

            result = await adapter.check_status("race-session-id")
            assert result == DeliveryStatus.FAILED

    @pytest.mark.asyncio
    async def test_unknown_internal_status_defaults_to_queued(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """Status interno desconhecido (e.g., novo state vindo de versao futura)
        -> QUEUED defensivo, nao FAILED, pra nao mascarar bug de propagacao."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value="company-x")
            mock_repo.load_session_state = AsyncMock(
                return_value={"status": "novo_estado_nao_mapeado"}
            )
            mock_factory.return_value = mock_repo

            result = await adapter.check_status("future-session-id")
            assert result == DeliveryStatus.QUEUED

    @pytest.mark.asyncio
    async def test_state_without_status_key_defaults_to_queued(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """State dict carregado mas sem chave 'status' (bug de serializacao
        antiga) -> QUEUED defensivo."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value="company-x")
            mock_repo.load_session_state = AsyncMock(
                return_value={"session_id": "sess-x"}  # no status key
            )
            mock_factory.return_value = mock_repo

            result = await adapter.check_status("malformed-session")
            assert result == DeliveryStatus.QUEUED

    @pytest.mark.asyncio
    async def test_exception_returns_failed_gracefully(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """Qualquer excecao interna (Redis down, etc) -> FAILED + log, nao
        propaga pro caller."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(
                side_effect=RuntimeError("redis connection refused")
            )
            mock_factory.return_value = mock_repo

            result = await adapter.check_status("any-id")
            assert result == DeliveryStatus.FAILED

    @pytest.mark.asyncio
    async def test_empty_message_id_returns_failed(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """message_id vazio -> FAILED imediato, sem hit no Redis."""
        result = await adapter.check_status("")
        assert result == DeliveryStatus.FAILED


class TestCheckStatusMultiTenancyInvariant:
    """company_id deve vir do reverse index (Redis), NUNCA de input externo."""

    @pytest.mark.asyncio
    async def test_company_id_resolved_via_reverse_index_only(
        self, adapter: VoiceChannelAdapter
    ) -> None:
        """check_status nao aceita company_id como parametro; resolve sempre
        via find_company_id_for_session. Isso previne cross-tenant lookup."""
        with patch(
            "app.shared.channels.adapters.voice_adapter.get_voice_session_repository"
        ) as mock_factory:
            mock_repo = AsyncMock()
            mock_repo.find_company_id_for_session = AsyncMock(return_value="tenant-A")
            mock_repo.load_session_state = AsyncMock(
                return_value={"status": "completed"}
            )
            mock_factory.return_value = mock_repo

            await adapter.check_status("sess-cross-tenant-attempt")

            # find_company_id_for_session deve ter sido chamado com session_id apenas
            mock_repo.find_company_id_for_session.assert_awaited_once_with(
                session_id="sess-cross-tenant-attempt"
            )
            # load_session_state recebeu o company_id RETORNADO pelo repo (autoritativo)
            mock_repo.load_session_state.assert_awaited_once_with(
                company_id="tenant-A",
                session_id="sess-cross-tenant-attempt",
            )
