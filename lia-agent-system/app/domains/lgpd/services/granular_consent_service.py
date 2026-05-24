"""
Granular Consent Service — D5 (LGPD Art. 7 / EU AI Act Art. 13)

Expande o ConsentCheckerService para consentimentos granulares por finalidade:
cada finalidade de IA tem seu próprio consent_type distinto (não todos mapeados
para SCREENING como no legado).

Finalidades → Consent Types:
  ai_screening   → SCREENING
  ai_scoring     → AI_SCORING
  ai_video       → AI_VIDEO_ANALYSIS
  ai_comparison  → AI_COMPARISON
  data_retention → DATA_RETENTION
  marketing      → MARKETING
  analytics      → ANALYTICS

Referências:
- LGPD Art. 7 (base legal: consentimento)
- LGPD Art. 8 (consentimento inequívoco)
- EU AI Act Art. 13 (transparência e granularidade)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.lgpd.repositories.lgpd_consent_repository import (
    LGPDConsentRepository,
)
from app.shared.observability.canary_metrics import (
    inc_granular_consent_revoke,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento granular: finalidade → consent_type único
# ---------------------------------------------------------------------------

GRANULAR_PURPOSE_MAP: dict[str, str] = {
    "ai_screening": "SCREENING",
    "ai_scoring": "AI_SCORING",
    "ai_video_analysis": "AI_VIDEO_ANALYSIS",
    "ai_comparison": "AI_COMPARISON",
    "data_retention": "DATA_RETENTION",
    "marketing": "MARKETING",
    "analytics": "ANALYTICS",
    # T-11 B.1.1: training_data purpose canonical (ADR-RLHF-001)
    # Used by training_data_service.export_* (T-21b wired anonymizer)
    # Cross-border via AWS Bedrock fine-tune (Claude 3 Haiku custom)
    "training_data": "TRAINING_DATA",
    # WT-2022 P4.2: ats_sharing purpose adicionado para evitar collapse em SCREENING default
    # Usado por ats_pii_filter.check_purpose("ats_sharing") — bloqueia PII em payload ATS externo
    "ats_sharing": "ATS_SHARING",
}

# Finalidades que BLOQUEIAM processamento quando revogadas (críticas LGPD)
# T-11 B.1.1: training_data is BLOCKING — revoke cascata erasure cross-border
BLOCKING_PURPOSES = {
    "ai_screening", "ai_scoring", "ai_video_analysis", "ai_comparison",
    "training_data",  # T-11 B.1.1: blocking pra impedir export pos-revoke
    "ats_sharing",  # WT-2022 P4.2: blocking pra impedir PII export ATS externo pos-revoke
}

# Todas as finalidades suportadas
ALL_PURPOSES = list(GRANULAR_PURPOSE_MAP.keys())


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass
class GranularConsentStatus:
    """Status de consentimento por finalidade."""
    purpose: str
    consent_type: str
    given: bool
    revoked: bool
    consent_date: datetime | None = None
    revoked_at: datetime | None = None
    source: str | None = None


@dataclass
class GranularConsentSummary:
    """Resumo de todos os consentimentos de um candidato."""
    candidate_id: str
    company_id: str
    consents: list[GranularConsentStatus] = field(default_factory=list)
    all_blocking_given: bool = False  # True se todas as finalidades BLOCKING_PURPOSES estão ok

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "company_id": self.company_id,
            "all_blocking_given": self.all_blocking_given,
            "consents": [
                {
                    "purpose": c.purpose,
                    "consent_type": c.consent_type,
                    "given": c.given,
                    "revoked": c.revoked,
                    "consent_date": c.consent_date.isoformat() if c.consent_date else None,
                    "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                    "source": c.source,
                }
                for c in self.consents
            ],
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GranularConsentService:
    """
    Gerencia consentimentos LGPD granulares por finalidade.

    Diferença do ConsentCheckerService legado: cada finalidade tem seu próprio
    consent_type, em vez de todas mapearem para SCREENING.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LGPDConsentRepository(db)

    def _consent_type_for(self, purpose: str) -> str:
        """Retorna consent_type granular para a finalidade. Default: SCREENING."""
        return GRANULAR_PURPOSE_MAP.get(purpose, "SCREENING")

    async def get_summary(
        self,
        candidate_id: str,
        company_id: str,
    ) -> GranularConsentSummary:
        """
        Retorna resumo de todos os consentimentos do candidato.

        Constrói um status para cada finalidade suportada, mesmo que o registro
        não exista no banco (nesse caso: given=False, revoked=False, absent=True).
        """
        # Busca todos os registros do candidato de uma vez
        records = await self.repo.list_for_candidate(
            candidate_id=candidate_id,
            company_id=company_id,
        )
        db_consents = {c.consent_type: c for c in records}

        statuses: list[GranularConsentStatus] = []
        for purpose, ctype in GRANULAR_PURPOSE_MAP.items():
            record = db_consents.get(ctype)
            if record is None:
                statuses.append(GranularConsentStatus(
                    purpose=purpose,
                    consent_type=ctype,
                    given=False,
                    revoked=False,
                ))
            else:
                is_revoked = bool(record.revoked_at and not record.consent_given)
                statuses.append(GranularConsentStatus(
                    purpose=purpose,
                    consent_type=ctype,
                    given=bool(record.consent_given),
                    revoked=is_revoked,
                    consent_date=record.consent_date,
                    revoked_at=record.revoked_at,
                    source=record.consent_source,
                ))

        blocking_ok = all(
            s.given and not s.revoked
            for s in statuses
            if s.purpose in BLOCKING_PURPOSES
        )

        return GranularConsentSummary(
            candidate_id=candidate_id,
            company_id=company_id,
            consents=statuses,
            all_blocking_given=blocking_ok,
        )

    async def bulk_update(
        self,
        candidate_id: str,
        company_id: str,
        updates: dict[str, bool],
        source: str = "api",
        ip_address: str | None = None,
    ) -> list[GranularConsentStatus]:
        """
        Atualiza múltiplos consentimentos em lote.

        Args:
            candidate_id: ID do candidato
            company_id: ID da empresa
            updates: {purpose: True/False} — True=conceder, False=revogar
            source: origem do consentimento (api, form, portal, etc.)
            ip_address: IP do solicitante (para rastreabilidade LGPD)

        Returns:
            Lista de GranularConsentStatus atualizados.
        """
        from lia_models.communication_settings import LGPDConsent

        now = datetime.utcnow()
        updated: list[GranularConsentStatus] = []

        for purpose, given in updates.items():
            ctype = self._consent_type_for(purpose)

            record = await self.repo.get_for_candidate_purpose(
                candidate_id=candidate_id,
                company_id=company_id,
                consent_type=ctype,
            )

            if record is None:
                record = LGPDConsent(
                    candidate_id=candidate_id,
                    company_id=company_id,
                    consent_type=ctype,
                    consent_given=given,
                    consent_date=now if given else None,
                    consent_source=source,
                    ip_address=ip_address,
                    revoked_at=now if not given else None,
                )
                self.db.add(record)
            else:
                record.consent_given = given
                record.consent_source = source
                record.updated_at = now
                if given:
                    record.consent_date = now
                    record.revoked_at = None
                    record.revoked_by = None
                else:
                    record.revoked_at = now
                    record.revoked_by = "candidate"
                if ip_address:
                    record.ip_address = ip_address

            updated.append(GranularConsentStatus(
                purpose=purpose,
                consent_type=ctype,
                given=given,
                revoked=not given,
                consent_date=now if given else None,
                revoked_at=now if not given else None,
                source=source,
            ))

            # Hardening C.3 -- canary signal per-purpose revoke (LGPD UX trust).
            # Incrementa apenas em revoke (given=False) pra alarme baseado em
            # spike de revogacao. Purpose passa por whitelist em canary_metrics
            # pra prevenir cardinality explosion via typos.
            if not given:
                inc_granular_consent_revoke(purpose)

        await self.db.flush()
        return updated

    async def check_purpose(
        self,
        candidate_id: str,
        company_id: str,
        purpose: str,
    ) -> bool:
        """
        Verificação rápida: candidato consentiu com finalidade?

        Retorna True se consent_given=True e não revogado. Fail-open: True em caso de erro.
        """
        try:
            ctype = self._consent_type_for(purpose)
            record = await self.repo.get_for_candidate_purpose(
                candidate_id=candidate_id,
                company_id=company_id,
                consent_type=ctype,
            )
            if record is None:
                return False
            return bool(record.consent_given) and not bool(record.revoked_at)
        except Exception as exc:
            # P0-W4-09: fail-closed para BLOCKING purposes — exception nao permite processamento sob incerteza
            if purpose in BLOCKING_PURPOSES:
                logger.error(
                    "[GranularConsent] check_purpose error -- purpose=%s is BLOCKING: fail-closed (LGPD Art. 7). %s",
                    purpose, exc,
                )
                return False
            logger.warning("[GranularConsent] check_purpose error (fail-open for non-blocking): %s", exc)
            return True
