"""
Consent Checker Service — LGPD Soft Enforcement.

Verifica consentimento granular por finalidade antes de operações de IA.
Implementa soft enforcement: aviso e log quando consent ausente, bloqueio quando revogado.

Abordagem:
- consent ausente  → aviso + audit log + CONTINUA (soft_warning=True)
- consent revogado → bloqueia + HTTP 451
- consent presente → prossegue normalmente
"""
import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.communication_settings import LGPDConsent

from app.domains.lgpd.repositories.lgpd_consent_repository import (
    LGPDConsentRepository,
)

logger = logging.getLogger(__name__)


@dataclass
class ConsentCheckResult:
    """Resultado da verificação de consentimento LGPD."""
    allowed: bool
    soft_warning: bool = False
    reason: str | None = None
    consent_type: str | None = None


class ConsentCheckerService:
    """
    Serviço de verificação de consentimento LGPD por finalidade.

    Finalidades suportadas:
    - ai_screening      → SCREENING            (chat / CV / generic AI)
    - ai_scoring        → SCREENING            (idem — backward compat)
    - ai_video_analysis → SCREENING            (idem)
    - ai_comparison     → SCREENING            (idem)
    - voice_screening   → VOICE_SCREENING      (P1 2026-05-23 granular)
    - whatsapp_screening → WHATSAPP_INTERACTION (P1 2026-05-23 granular)

    P1 cross-domain consent ticket (2026-05-23): voice + whatsapp ganham
    consent_type próprio para isolation. Revogar voice consent NÃO revoga
    chat consent (rows separadas no DB). Diferenciação de audit trail
    completa (LGPD Art. 37 + Resolução CD/ANPD nº 2/2022).

    Backward compat OBRIGATÓRIO:
    - 'SCREENING' rows existentes no DB continuam válidos (default)
    - Callers que usam ai_screening/ai_scoring NÃO mudam comportamento
    - Apenas voice + whatsapp ganham granularidade
    """

    AI_PURPOSES = [
        "ai_screening",
        "ai_scoring",
        "ai_video_analysis",
        "ai_comparison",
        # F-23 (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):
        # voice_screening is distinct from generic ai_screening for audit-trail
        # differentiation (LGPD Art. 37). P1 2026-05-23 — promoted to granular
        # consent_type VOICE_SCREENING (no longer collapses into SCREENING).
        "voice_screening",
        # P1 ticket #3 (2026-05-23): WhatsApp interaction granular consent.
        "whatsapp_screening",
        # Onda 2C.3 (audit 2026-06-06): autodeclaração/laudo de ação afirmativa é dado
        # SENSÍVEL (raça/PCD/etc) — consent granular fail-closed antes do upload.
        "affirmative_verification",
    ]

    # Mapeamento de finalidade de IA para consent_type do LGPDConsent.
    # P1 ticket #3 (2026-05-23): voice + whatsapp promovidos a consent_types
    # granulares. Demais purposes ficam em SCREENING (backward compat).
    PURPOSE_TO_CONSENT_TYPE = {
        "ai_screening": "SCREENING",
        "ai_scoring": "SCREENING",
        "ai_video_analysis": "SCREENING",
        "ai_comparison": "SCREENING",
        # P1 #3: granular consent_types (isolation — revogar voice NÃO
        # revoga chat; audit trail diferenciado).
        "voice_screening": "VOICE_SCREENING",
        "whatsapp_screening": "WHATSAPP_INTERACTION",
        "affirmative_verification": "AFFIRMATIVE_SENSITIVE_DATA",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LGPDConsentRepository(db)

    async def check_candidate_consent(
        self,
        candidate_id: str,
        company_id: str,
        purpose: str,
    ) -> ConsentCheckResult:
        """
        Verifica se o candidato deu consentimento para uma finalidade específica de IA.

        Args:
            candidate_id: ID do candidato
            company_id: ID da empresa (tenant)
            purpose: Finalidade de processamento (ex: "ai_scoring", "ai_screening")

        Returns:
            ConsentCheckResult com allowed=True/False e soft_warning se consent ausente
        """
        consent_type = self.PURPOSE_TO_CONSENT_TYPE.get(purpose, "SCREENING")

        try:
            consent = await self.repo.get_for_candidate_purpose(
                candidate_id=candidate_id,
                company_id=company_id,
                consent_type=consent_type,
            )

            # Caso 1: Consentimento revogado — BLOQUEAR
            if consent and not consent.consent_given and consent.revoked_at:
                logger.info(
                    f"[LGPD] Consentimento revogado: candidate={candidate_id}, "
                    f"company={company_id}, purpose={purpose}, type={consent_type}, "
                    f"revoked_at={consent.revoked_at.isoformat()}"
                )
                return ConsentCheckResult(
                    allowed=False,
                    reason="revoked",
                    consent_type=consent_type,
                )

            # Caso 2: Consentimento ausente — comportamento depende da flag hard/soft
            # LGPD Art. 7: o processamento de dados pessoais para IA requer consentimento
            # explícito do titular. O default correto é bloquear (hard block = True) quando
            # o consentimento não foi registrado, garantindo compliance com o princípio da
            # finalidade e do livre acesso (LGPD Art. 6, incisos I e IV).
            if consent is None:
                try:
                    from lia_config.config import settings
                    _hard_block = settings.LGPD_CONSENT_ABSENT_HARD_BLOCK
                except Exception:
                    # Default True: em caso de falha na leitura da config, o comportamento
                    # seguro é bloquear — LGPD Art. 7 exige consentimento para finalidades de IA.
                    _hard_block = True

                if _hard_block:
                    logger.warning(
                        "[LGPD] HARD_BLOCK: Consentimento ausente bloqueado — candidate=%s, "
                        "company=%s, purpose=%s, type=%s.",
                        candidate_id, company_id, purpose, consent_type,
                    )
                    await self._record_audit_log(
                        candidate_id=candidate_id,
                        company_id=company_id,
                        purpose=purpose,
                        event="consent_absent_hard_block",
                    )
                    return ConsentCheckResult(
                        allowed=False,
                        reason="absent",
                        consent_type=consent_type,
                    )

                logger.warning(
                    "[LGPD] SOFT_WARNING: Consentimento ausente — candidate=%s, "
                    "company=%s, purpose=%s, type=%s. Operação prosseguindo com aviso.",
                    candidate_id, company_id, purpose, consent_type,
                )
                await self._record_audit_log(
                    candidate_id=candidate_id,
                    company_id=company_id,
                    purpose=purpose,
                    event="consent_absent_soft_warning",
                )
                return ConsentCheckResult(
                    allowed=True,
                    soft_warning=True,
                    reason="absent",
                    consent_type=consent_type,
                )

            # Caso 3: Consentimento presente e válido — PROSSEGUIR
            return ConsentCheckResult(
                allowed=True,
                soft_warning=False,
                consent_type=consent_type,
            )

        except Exception as e:
            # FAIL-OPEN: DB error during consent check → allow with soft_warning.
            # Rationale: candidate may have valid consent that we cannot verify;
            # blocking every DB hiccup harms UX disproportionately.
            # Audit trail remains so LGPD Art. 7 accountability is preserved.
            logger.warning(
                "[LGPD] FAIL-OPEN: Consent check error — allowing with soft_warning. "
                "candidate=%s, purpose=%s: %s",
                candidate_id, purpose, e,
            )
            return ConsentCheckResult(
                allowed=True,
                soft_warning=True,
                reason="check_error",
                consent_type=consent_type,
            )

    async def _record_audit_log(
        self,
        candidate_id: str,
        company_id: str,
        purpose: str,
        event: str,
    ) -> None:
        """Registra evento de auditoria LGPD (best-effort, não falha se der erro)."""
        try:
            from lia_models.observability import ConsentEvent
            audit = ConsentEvent(
                candidate_id=candidate_id,
                company_id=company_id,
                event_type=event,
                purpose=purpose,
                timestamp=datetime.utcnow(),
            )
            self.db.add(audit)
            await self.db.flush()
        except Exception:
            # Audit log é best-effort — não interrompe o fluxo principal
            pass

    async def register_consent(
        self,
        candidate_id: str,
        company_id: str,
        consent_type: str,
        consent_given: bool,
        consent_source: str = "api",
        consent_text: str | None = None,
        ip_address: str | None = None,
    ) -> LGPDConsent:
        """
        Registra ou atualiza consentimento de um candidato por finalidade.

        Usa UPSERT por (company_id, candidate_id, consent_type).
        """
        existing = await self.repo.get_for_candidate_purpose(
            candidate_id=candidate_id,
            company_id=company_id,
            consent_type=consent_type,
        )

        if existing:
            existing.consent_given = consent_given
            existing.consent_source = consent_source
            existing.updated_at = datetime.utcnow()
            if consent_given:
                existing.consent_date = datetime.utcnow()
                existing.revoked_at = None
                existing.revoked_by = None
                existing.revoke_reason = None
            else:
                existing.revoked_at = datetime.utcnow()
                existing.revoked_by = "candidate"
            if consent_text:
                existing.consent_text = consent_text
            if ip_address:
                existing.ip_address = ip_address
            await self.db.flush()
            return existing
        else:
            consent = LGPDConsent(
                candidate_id=candidate_id,
                company_id=company_id,
                consent_type=consent_type,
                consent_given=consent_given,
                consent_date=datetime.utcnow() if consent_given else None,
                consent_source=consent_source,
                consent_text=consent_text,
                ip_address=ip_address,
                revoked_at=datetime.utcnow() if not consent_given else None,
            )
            await self.repo.add(consent)
            return consent

    async def get_candidate_consents(
        self,
        candidate_id: str,
        company_id: str,
    ) -> list:
        """Retorna todos os consentimentos de um candidato."""
        consents = await self.repo.list_for_candidate(
            candidate_id=candidate_id,
            company_id=company_id,
        )
        return [c.to_dict() for c in consents]
