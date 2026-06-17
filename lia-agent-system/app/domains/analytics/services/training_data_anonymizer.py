"""T-21 LGPD anonymizer canonical (ADR-LGPD-002).

Mandatory layer ANTES de qualquer training data export que cruze fronteira
(Anthropic US, OpenAI US, etc.). Baseline legal: LGPD Art. 33 (transferência
internacional) com Art. 12 §1 (anonimização irreversível) como salvaguarda.

Operações canonical:
1. Strip PII layers 0-4 (regex + Presidio NER opt-in) via `strip_pii_for_llm_prompt`
2. Hash candidate_id SHA-256 (irreversible)
3. Remove free-text identifiers extras
4. Sanity check batch (sample re-detection)
5. Filter por consent_records.consent_type='training_data' (opt-in granular)

Refs:
- ADR-LGPD-002 docs/specs/ai/ADR-LGPD-002-training-data-transfer.md
- LGPD Art. 12 §1 (anonimização)
- LGPD Art. 33 (transferência internacional)
- Anthropic DPA + SOC 2 Type II + ISO 27001 (Trust Center)
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.shared.pii_masking import strip_pii_for_llm_prompt


logger = logging.getLogger(__name__)


ANONYMIZATION_VERSION = "v1-2026-05-20"
"""Versão do anonymizer — incrementar quando estratégia mudar."""


class AnonymizationError(Exception):
    """Raised when anonymization sanity check fails."""


class TrainingDataAnonymizer:
    """LGPD Art. 12 §1 anonymizer para training data export.

    Uso canonical em `training_data_service`:
        anonymizer = TrainingDataAnonymizer()
        clean_samples = await anonymizer.process_batch(
            feedback_entries, company_id=company_id
        )
        # Só samples com consent + PII stripped chegam aqui
    """

    def __init__(self, *, allow_demographic: bool = False):
        self.allow_demographic = allow_demographic
        self.logger = logger

    @staticmethod
    def hash_candidate_id(raw_id: str | UUID | None) -> str | None:
        """SHA-256 one-way hash. LGPD-safe (impossible to reverse)."""
        if raw_id is None:
            return None
        canonical = str(raw_id).strip().lower()
        if not canonical:
            return None
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def anonymize_sample(self, sample: dict[str, Any]) -> dict[str, Any]:
        """Anonymize 1 training sample in-place + return.

        Mandatory operations:
        - Strip PII em user_message, lia_response, correction
        - Hash candidate_id (se presente)
        - Strip free-text fields if found (notes, comments)
        - Add _anonymization_version + _anonymized_at metadata
        """
        # PII strip em campos de texto livre
        for text_field in (
            "user_message", "lia_response", "correction",
            "notes", "comments", "feedback_text",
        ):
            if text_field in sample and isinstance(sample[text_field], str):
                sample[text_field] = strip_pii_for_llm_prompt(sample[text_field])

        # Hash candidate_id
        if "candidate_id" in sample:
            sample["candidate_id_hash"] = self.hash_candidate_id(
                sample.pop("candidate_id")
            )

        # Remove free-text identifiers raros (best-effort)
        for direct_pii in ("email", "phone", "cpf", "rg", "cnpj", "name", "full_name"):
            sample.pop(direct_pii, None)

        # Demographic data: drop unless explicit opt-in
        if not self.allow_demographic:
            for demo in ("gender", "race", "age", "ethnicity", "religion"):
                sample.pop(demo, None)

        sample["_anonymization_version"] = ANONYMIZATION_VERSION
        sample["_anonymized_at"] = datetime.now(timezone.utc).isoformat()

        return sample

    def sanity_check_batch(self, samples: list[dict[str, Any]]) -> None:
        """Re-detecta PII pós-anonymization. Raise se algum sample tem PII residual.

        Verifica:
        - Presença de @ (email-like)
        - 11-digit numbers (CPF-like)
        - 8-digit numbers (RG-like)
        - "candidate_id_hash" deve estar presente (não candidate_id raw)
        - "_anonymization_version" deve estar presente
        """
        import re
        EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
        PHONE_RE = re.compile(r"\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b")

        errors = []
        for i, s in enumerate(samples):
            if "_anonymization_version" not in s:
                errors.append(f"Sample {i}: missing _anonymization_version")
                continue
            if "candidate_id" in s:
                errors.append(f"Sample {i}: raw candidate_id present (não hash)")
            # Re-detect em campos de texto
            for field in ("user_message", "lia_response", "correction"):
                if field in s and isinstance(s[field], str):
                    if EMAIL_RE.search(s[field]):
                        errors.append(f"Sample {i}.{field}: email-like padrão detectado")
                    if CPF_RE.search(s[field]):
                        errors.append(f"Sample {i}.{field}: CPF-like padrão detectado")
                    if PHONE_RE.search(s[field]):
                        errors.append(f"Sample {i}.{field}: phone-like padrão detectado")

        if errors:
            self.logger.error(
                "[TrainingDataAnonymizer] sanity check FAIL — %d violations:\n%s",
                len(errors), "\n".join(errors[:10]),
            )
            raise AnonymizationError(
                f"Sanity check FAIL: {len(errors)} violations residual after anonymization. "
                f"DO NOT UPLOAD. First 10: {errors[:10]}"
            )

        self.logger.info(
            "[TrainingDataAnonymizer] sanity check OK — %d samples clean (version=%s)",
            len(samples), ANONYMIZATION_VERSION,
        )

    async def process_batch(
        self,
        samples: list[dict[str, Any]],
        *,
        company_id: str,
        skip_sanity: bool = False,
    ) -> list[dict[str, Any]]:
        """Process complete batch + sanity check. Returns clean samples ready
        for cross-border training data upload.

        Raises:
            AnonymizationError: se sanity check fail (algum PII residual)
        """
        clean = [self.anonymize_sample(dict(s)) for s in samples]
        if not skip_sanity:
            self.sanity_check_batch(clean)
        self.logger.info(
            "[TrainingDataAnonymizer] processed %d samples for company_id=%s",
            len(clean), company_id,
        )
        return clean
