"""
ATS PII Filter — LGPD compliance para sync com ATS externos — UC-P3-12.

PURPOSE (when to use THIS filter vs pii_masking):
  Use ats_pii_filter when you need to:
  - Filter outbound API payloads sent to external ATS systems (Gupy, Pandapé)
    based on candidate consent (ats_sharing flag, D5 granular consent)
  - Sanitize text fields received in ATS webhooks / sync payloads
  - Enforce LGPD Art. 6 (purpose + data minimization) at the ATS boundary

  Use pii_masking (app/shared/pii_masking.py) when:
  - Sanitizing Python log messages / exception text
  - Stripping PII before sending arbitrary text to an LLM prompt
  - Installing a global logging filter across the application

FIELDS COVERED:
  - Outbound (OUTBOUND_SENSITIVE_FIELDS registry in lgpd_field_registry.py):
    social identifiers, race/religion/health fields, salary details, personal address
  - Inbound (text fields per ATS via get_inbound_text_fields):
    free-text notes that may contain CPF, email, phone from recruiter input

OPERATION MODE:
  - filter_outbound: synchronous dict → dict filter, checks has_consent flag
  - filter_sensitive_outbound: async, queries GranularConsentService for ats_sharing purpose
  - filter_inbound_text: synchronous, applies strip_pii_for_llm_prompt to text fields
  All three are fail-safe (return original payload on error).

LGPD Art. 6 (finalidade/necessidade) + Art. 46 (medidas de segurança).
D5 — Consentimento granular: LGPD Art. 7 / EU AI Act Art. 13.
"""
import logging
from typing import Any


from app.domains.ats_integration.services.ats_clients.lgpd_field_registry import (
    OUTBOUND_SENSITIVE_FIELDS,
    get_inbound_text_fields,
)
from app.shared.pii_masking import strip_pii_for_llm_prompt

logger = logging.getLogger("lia.pii.ats")  # R-052: PII filter uses isolated lia.pii.ats logger (separate from root to avoid leaking ATS payload structure)


def filter_outbound(
    payload: dict[str, Any],
    ats_name: str,
    has_consent: bool = True,
) -> dict[str, Any]:
    """Remove campos sensíveis do payload antes de enviar ao ATS externo.

    Args:
        payload: Dicionário de campos no formato WeDOTalent (antes de mapeamento ATS).
        ats_name: Nome do ATS ("gupy", "pandape", etc.) — usado apenas para log.
        has_consent: True se o candidato consentiu compartilhamento de dados (data_sharing).
                     Default True para não quebrar integrações existentes.

    Returns:
        Payload filtrado. Nunca lança exceção — falha silenciosa loga warning.
    """
    if has_consent:
        return payload

    try:
        stripped: dict[str, Any] = {}
        removed: list[str] = []

        for key, value in payload.items():
            if key in OUTBOUND_SENSITIVE_FIELDS:
                removed.append(key)
            else:
                stripped[key] = value

        if removed:
            logger.warning(
                "[ATS-PII] Outbound filter (%s): removidos %d campos sensíveis sem consentimento: %s",
                ats_name,
                len(removed),
                removed,
            )

        return stripped

    except Exception as exc:
        logger.warning("[ATS-PII] filter_outbound falhou (%s): %s — retornando payload original", ats_name, exc)
        return payload


async def filter_sensitive_outbound(
    payload: dict[str, Any],
    ats_name: str,
    candidate_id: str | None = None,
    company_id: str | None = None,
    db=None,
) -> dict[str, Any]:
    """Remove campos sensíveis do payload antes de enviar ao ATS externo.

    Versão async (D5-G2): verifica consentimento granular ``ats_sharing`` via
    GranularConsentService antes de incluir campos sensíveis no payload.

    Args:
        payload: Dicionário de campos no formato WeDOTalent.
        ats_name: Nome do ATS ("gupy", "pandape", etc.) — usado para log.
        candidate_id: ID do candidato para verificação de consentimento.
        company_id: ID da empresa (multi-tenant).
        db: AsyncSession para consulta ao banco. Se None, passa sem verificar.

    Returns:
        Payload filtrado. Nunca lança exceção — fail-open se serviço indisponível.
    """
    has_consent = True

    if candidate_id and company_id and db is not None:
        try:
            from app.shared.services.granular_consent_service import GranularConsentService
            svc = GranularConsentService(db)
            has_consent = await svc.check_purpose(candidate_id, company_id, "ats_sharing")
        except Exception as exc:
            logger.warning(
                "[ATS-PII] D5 consent check falhou (fail-open): candidate=%s exc=%s",
                candidate_id, exc,
            )
            has_consent = True  # fail-open

    return filter_outbound(payload, ats_name, has_consent=has_consent)


def filter_inbound_text(
    payload: dict[str, Any],
    ats_name: str,
) -> dict[str, Any]:
    """Aplica strip_pii em campos de texto livre recebidos do ATS.

    Campos de texto como notas/observações podem conter CPF, e-mail e telefone
    digitados manualmente por recrutadores do ATS externo.

    Args:
        payload: Dados brutos recebidos do ATS.
        ats_name: Nome do ATS para identificar quais campos tratar.

    Returns:
        Payload com texto livre sanitizado. Nunca lança exceção.
    """
    text_fields = get_inbound_text_fields(ats_name)
    if not text_fields:
        return payload

    try:
        result = dict(payload)
        masked_count = 0

        for field in text_fields:
            if field in result and isinstance(result[field], str) and result[field]:
                original = result[field]
                result[field] = strip_pii_for_llm_prompt(original)
                if result[field] != original:
                    masked_count += 1

        if masked_count:
            logger.debug(
                "[ATS-PII] Inbound filter (%s): PII mascarado em %d campo(s) de texto livre",
                ats_name,
                masked_count,
            )

        return result

    except Exception as exc:
        logger.warning("[ATS-PII] filter_inbound_text falhou (%s): %s — retornando payload original", ats_name, exc)
        return payload
