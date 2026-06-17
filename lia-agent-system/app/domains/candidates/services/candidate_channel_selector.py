"""
Candidate Channel Selector — N3.

Seleciona os canais de comunicação efetivos para um candidato considerando:
1. preferred_channels do candidato (lista ordenada de preferências)
2. Consentimento LGPD por canal (LGPDConsent)
3. channel_opt_out do candidato
4. Canais solicitados pela communication matrix da empresa

Retorna a intersecção dos canais válidos, respeitando as preferências do candidato.
Fallback: ["email"] se a lista resultante for vazia.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate
from lia_models.communication_settings import LGPDConsent

logger = logging.getLogger(__name__)

# Mapeamento de canal para consent_type LGPD
CHANNEL_CONSENT_MAP = {
    "email": "EMAIL_MARKETING",
    "whatsapp": "WHATSAPP",
    "sms": "SMS",
}

# Canais transacionais que não precisam de consent de marketing
TRANSACTIONAL_CHANNELS = {"email"}  # Email transacional sempre permitido se não houve opt-out

FALLBACK_CHANNEL = ["email"]


class CandidateChannelSelector:
    """
    Seleciona canais de comunicação válidos para um candidato.

    Leva em conta:
    - Preferências do candidato (preferred_channels)
    - Opt-outs do candidato (channel_opt_out)
    - Consentimento LGPD por canal (LGPDConsent)
    - Canais requisitados pela communication matrix

    Mensagens transacionais (confirmações, status) têm regras mais permissivas.
    Mensagens de marketing seguem LGPD estritamente.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def select_channels(
        self,
        candidate_id: str,
        company_id: str,
        requested_channels: list[str],
        message_type: str = "transactional",  # "transactional" | "marketing"
    ) -> list[str]:
        """
        Retorna os canais efetivos para enviar mensagem a um candidato.

        Args:
            candidate_id: ID do candidato
            company_id: ID da empresa (tenant)
            requested_channels: Canais solicitados pela communication matrix
            message_type: "transactional" (status/notificações) ou "marketing" (abordagem/divulgação)

        Returns:
            Lista de canais válidos, em ordem de preferência do candidato.
            Retorna ["email"] como fallback se lista vazia.
        """
        if not requested_channels:
            return FALLBACK_CHANNEL

        # 1. Buscar dados do candidato
        candidate = await self._get_candidate(candidate_id)
        preferred = list(candidate.preferred_channels or ["email"]) if candidate else ["email"]
        opt_out = set(candidate.channel_opt_out or []) if candidate else set()

        # 2. Buscar consentimentos LGPD do candidato
        consented_channels = await self._get_consented_channels(candidate_id, company_id)

        # 3. Filtrar canais válidos
        valid_channels = []
        for channel in preferred:
            # Só considerar canais que foram solicitados pela matrix
            if channel not in requested_channels:
                continue

            # Remover canais em opt-out
            if channel in opt_out:
                logger.info(
                    f"[CHANNEL_SELECTOR] Canal '{channel}' ignorado por opt-out: candidate={candidate_id}"
                )
                continue

            # Verificar consentimento LGPD para marketing
            if message_type == "marketing":
                consent_type = CHANNEL_CONSENT_MAP.get(channel)
                if consent_type and channel not in consented_channels:
                    logger.info(
                        f"[CHANNEL_SELECTOR] Canal '{channel}' ignorado por falta de consent LGPD "
                        f"(type={consent_type}): candidate={candidate_id}"
                    )
                    continue

            valid_channels.append(channel)

        # 4. Fallback se lista vazia
        if not valid_channels:
            logger.warning(
                f"[CHANNEL_SELECTOR] Nenhum canal válido para candidate={candidate_id} "
                f"(requested={requested_channels}, preferred={preferred}, opt_out={opt_out}). "
                f"Usando fallback: {FALLBACK_CHANNEL}"
            )
            return FALLBACK_CHANNEL

        return valid_channels

    async def _get_candidate(self, candidate_id: str) -> Candidate | None:
        """Busca candidato por ID."""
        try:
            from uuid import UUID
            from app.domains.candidates.repositories.candidate_repository import (
                CandidateRepository,
            )
            repo = CandidateRepository(self.db)
            return await repo.get_by_id(UUID(candidate_id))
        except Exception as e:
            logger.warning(f"[CHANNEL_SELECTOR] Erro ao buscar candidato {candidate_id}: {e}")
            return None

    async def _get_consented_channels(self, candidate_id: str, company_id: str) -> set:
        """
        Retorna o conjunto de canais para os quais o candidato deu consentimento ativo.
        """
        consented = set()
        try:
            from app.domains.lgpd.repositories.lgpd_consent_repository import (
                LGPDConsentRepository,
            )
            consent_repo = LGPDConsentRepository(self.db)
            consents = await consent_repo.list_active_for_candidate(
                candidate_id=candidate_id, company_id=company_id
            )

            for consent in consents:
                # Mapear consent_type de volta para canal
                for channel, consent_type in CHANNEL_CONSENT_MAP.items():
                    if consent.consent_type == consent_type:
                        consented.add(channel)
        except Exception as e:
            logger.warning(f"[CHANNEL_SELECTOR] Erro ao buscar consents de {candidate_id}: {e}")

        return consented
