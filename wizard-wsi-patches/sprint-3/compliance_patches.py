"""
Sprint 3.6-3.9 — Compliance & Governance patches.

3.6: PII masking antes de LLM
3.7: Response hashing SHA-256
3.8: EU AI Act disclaimer
3.9: Audit trail para wizard decisions
"""

import hashlib
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# === 3.6: PII Masking Middleware ===
# ONDE APLICAR: app/shared/compliance/pii_masker.py (NOVO)

class PiiMasker:
    """
    Masks PII (email, phone, CPF) before sending to LLM.
    Restores original values in output if needed.

    Usage:
        masker = PiiMasker()
        masked_text, mapping = masker.mask(original_text)
        # Send masked_text to LLM
        restored_text = masker.restore(llm_output, mapping)
    """

    # Patterns
    EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_RE = re.compile(r'\b(?:\+55\s?)?\(?\d{2}\)?\s?\d{4,5}[-.\s]?\d{4}\b')
    CPF_RE = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b')
    NAME_INDICATORS = re.compile(r'\b(?:nome|name|candidato|candidata):\s*([A-Z][a-záàãâéêíóôõú]+(?:\s+[A-Z][a-záàãâéêíóôõú]+){1,4})', re.IGNORECASE)

    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        """Mask PII in text. Returns (masked_text, mapping)."""
        mapping: dict[str, str] = {}
        counter = {"email": 0, "phone": 0, "cpf": 0, "name": 0}

        def replace_match(pattern: re.Pattern, pii_type: str, text: str) -> str:
            def replacer(match: re.Match) -> str:
                original = match.group(0)
                counter[pii_type] += 1
                placeholder = f"[{pii_type.upper()}_{counter[pii_type]}]"
                mapping[placeholder] = original
                return placeholder
            return pattern.sub(replacer, text)

        text = replace_match(self.EMAIL_RE, "email", text)
        text = replace_match(self.PHONE_RE, "phone", text)
        text = replace_match(self.CPF_RE, "cpf", text)

        if mapping:
            logger.info(f"PII masked: {len(mapping)} items ({', '.join(set(k.split('_')[0].strip('[]') for k in mapping))})")

        return text, mapping

    def restore(self, text: str, mapping: dict[str, str]) -> str:
        """Restore original PII values from placeholders."""
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text


# === 3.7: Response Hashing SHA-256 ===
# ONDE APLICAR: app/shared/compliance/response_hasher.py (NOVO)
# Chamar após cada resposta de screening (F8)

def hash_response(
    response_text: str,
    question_id: str,
    candidate_id: str,
    timestamp: str,
) -> str:
    """
    Generate SHA-256 hash of a screening response for audit trail.

    The hash includes the response text + metadata to prevent tampering.
    Store alongside the response in the database.

    Returns: hex digest string
    """
    payload = f"{response_text}|{question_id}|{candidate_id}|{timestamp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_response_integrity(
    response_text: str,
    question_id: str,
    candidate_id: str,
    timestamp: str,
    stored_hash: str,
) -> bool:
    """Verify response hasn't been tampered with."""
    computed = hash_response(response_text, question_id, candidate_id, timestamp)
    return computed == stored_hash


# === 3.8: EU AI Act Disclaimer ===
# ONDE APLICAR: No template de report F11 e no PersonalizedFeedbackService

EU_AI_ACT_DISCLAIMER = {
    "pt": (
        "AVISO DE TRANSPARENCIA — EU AI Act (Regulamento 2024/1689)\n"
        "Esta avaliacao foi realizada por um sistema de IA classificado como alto risco "
        "conforme o Artigo 6 do Regulamento Europeu de Inteligencia Artificial. "
        "O sistema utiliza scoring deterministico (sem IA na decisao final) "
        "e todos os resultados sao auditaveis. "
        "O candidato tem direito a explicacao da decisao conforme LGPD Art. 20."
    ),
    "en": (
        "TRANSPARENCY NOTICE — EU AI Act (Regulation 2024/1689)\n"
        "This assessment was performed by an AI system classified as high-risk "
        "under Article 6 of the European AI Regulation. "
        "The system uses deterministic scoring (no AI in final decision) "
        "and all results are auditable. "
        "The candidate has the right to explanation per LGPD Art. 20."
    ),
}

# Para incluir no report F11:
# report["section_9_auditability"]["eu_ai_act_disclaimer"] = EU_AI_ACT_DISCLAIMER["pt"]
# report["section_9_auditability"]["methodology_version"] = "2.0"
# report["section_9_auditability"]["screening_id"] = str(uuid4())
# report["section_9_auditability"]["evaluation_temperature"] = 0.0
# report["section_9_auditability"]["response_hashes"] = [hash_response(...) for r in responses]


# === 3.9: Audit Trail for Wizard Decisions ===
# ONDE APLICAR: Cada node do wizard deve chamar audit_wizard_decision()
# Integrar com app/shared/compliance/audit_service.py

async def audit_wizard_decision(
    audit_service: Any,
    company_id: int,
    session_id: str,
    stage: str,
    action: str,  # "approve", "reject", "edit", "publish"
    details: dict,
    fairness_flags: list[str] | None = None,
) -> None:
    """
    Log a wizard decision to the audit trail.

    Every stage approval/rejection should be logged for compliance.
    Non-blocking: catches exceptions so wizard continues even if audit fails.
    """
    try:
        await audit_service.log_output(
            company_id=company_id,
            session_id=session_id,
            agent_used="job_creation",
            input_text=f"Wizard {stage}: {action}",
            output_text=str(details)[:8000],
            action_executed=f"wizard_{stage}_{action}",
            candidate_id=None,
            job_vacancy_id=details.get("job_id"),
            fairness_flags=fairness_flags or [],
        )
    except Exception as e:
        logger.warning(f"Audit trail write failed (non-blocking): {e}")


# --- INTEGRAÇÃO EM CADA NODE ---
# No jd_enrichment_node, após aprovação:
#   await audit_wizard_decision(audit_svc, company_id, session_id, "jd_enrichment", "approve", {"quality_score": score})
#
# No wsi_questions_node, após aprovação:
#   await audit_wizard_decision(audit_svc, company_id, session_id, "wsi_questions", "approve", {"question_count": len(questions)})
#
# No publish_node, após publicar:
#   await audit_wizard_decision(audit_svc, company_id, session_id, "publish", "publish", {"job_id": job_id, "platforms": platforms})
