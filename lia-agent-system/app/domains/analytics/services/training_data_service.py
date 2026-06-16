"""
Training Data Service - Export training data for LLM fine-tuning.

Enables model improvement by:
- Exporting high-quality interaction data in various formats
- Curating samples based on feedback quality
- Generating DPO preference pairs from corrections
- Providing statistics for training data management
"""
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.repositories.feedback_repository import FeedbackRepository
from lia_models.feedback import InteractionFeedback

logger = logging.getLogger(__name__)

# Fixed, versioned persona for training consistency (not from dynamic YAML)
from app.shared.prompts.training_persona import TRAINING_PERSONA

SYSTEM_PROMPT_FOR_TRAINING = TRAINING_PERSONA

ERROR_PATTERNS = [
    "erro",
    "error",
    "exception",
    "falha",
    "não foi possível",
    "desculpe, algo deu errado",
    "tente novamente",
]


class TrainingDataService:
    """
    Service for exporting training data for model fine-tuning.
    
    Features:
    - Export in OpenAI, Anthropic, and DPO formats
    - Quality-based filtering of samples
    - Automatic curation of best samples
    - Statistics and metrics for training data
    """
    
    MIN_RESPONSE_LENGTH = 50
    MIN_CONFIDENCE_SCORE = 0.7
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _is_quality_response(self, feedback: InteractionFeedback) -> bool:
        """
        Check if a feedback entry meets quality criteria for training.
        
        Quality criteria:
        - Rating >= 4 OR thumbs == 'up'
        - Response length > 50 characters
        - No error messages in response
        - Confidence score >= 0.7 (if available)
        """
        if not feedback.lia_response or len(feedback.lia_response) < self.MIN_RESPONSE_LENGTH:
            return False
        
        is_positive_feedback = (
            feedback.thumbs == "up" or
            (feedback.rating is not None and feedback.rating >= 4)
        )
        if not is_positive_feedback:
            return False
        
        response_lower = feedback.lia_response.lower()
        for pattern in ERROR_PATTERNS:
            if pattern in response_lower:
                return False
        
        if feedback.confidence_score is not None and feedback.confidence_score < self.MIN_CONFIDENCE_SCORE:
            return False
        
        return True
    
    async def _get_quality_feedback(
        self,
        company_id: str,
        min_rating: int = 4,
        limit: int = 1000,
        require_correction: bool = False
    ) -> list[InteractionFeedback]:
        """Get feedback entries that meet quality criteria."""
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            self.logger.warning(f"Invalid company_id: {company_id}")
            return []
        
        repo = FeedbackRepository(self.db)
        all_feedback = await repo.list_quality_feedback(
            company_id=company_uuid,
            min_rating=min_rating,
            limit=limit * 2,
            require_correction=require_correction,
            min_response_length=self.MIN_RESPONSE_LENGTH,
        )
        
        quality_feedback = []
        for feedback in all_feedback:
            if require_correction or self._is_quality_response(feedback):
                # P1-W4-13: per-candidate training_data consent gate (LGPD Art. 7).
                # Company-level already gated in FeedbackRepository (CompanyTrainingConsent).
                # Here we apply AND: company-level=true AND per-candidate=true.
                # Fail-closed: if consent check raises, skip candidate.
                _candidate_id = str(getattr(feedback, "candidate_id", None) or "")
                if _candidate_id:
                    try:
                        from app.domains.lgpd.services.granular_consent_consumers import (
                            check_training_data_granular,
                        )
                        _td_consent = await check_training_data_granular(
                            candidate_id=_candidate_id,
                            company_id=company_id,
                            db=self.db,
                        )
                        if not _td_consent:
                            self.logger.debug(
                                "[P1-W4-13] training_data consent blocked: "
                                "candidate_id=%s company_id=%s",
                                _candidate_id, company_id,
                            )
                            continue
                    except Exception as _consent_err:
                        self.logger.warning(
                            "[P1-W4-13] consent check error (fail-closed, skip): %s",
                            _consent_err,
                        )
                        continue
                quality_feedback.append(feedback)
                if len(quality_feedback) >= limit:
                    break
        
        return quality_feedback
    
    async def _anonymize_feedback_batch(
        self,
        feedback_entries: list[InteractionFeedback],
        company_id: str,
    ) -> list[dict[str, Any]]:
        """T-21b LGPD anonymization (ADR-LGPD-002).

        Converts ORM InteractionFeedback rows into dict samples and routes
        through the canonical ``TrainingDataAnonymizer`` (Art. 12 §1) before
        any cross-border export. Single source of truth for PII stripping
        lives in ``app/domains/analytics/services/training_data_anonymizer.py``.

        Pipeline per row:
          1. ORM -> dict serialization (only attrs needed for export)
          2. PII strip layers 0-4 in free-text fields via canonical anonymizer
          3. SHA-256 hash of candidate_id (irreversible)
          4. Drop direct PII fields (email/phone/cpf/name)
          5. Batch sanity check (raises AnonymizationError on residual PII)

        Args:
            feedback_entries: ORM rows from ``_get_quality_feedback``.
            company_id: Tenant UUID (audit log + telemetry only — does NOT
                grant cross-tenant access; rows were already filtered by
                ``_get_quality_feedback`` using JWT-scoped company_id).

        Returns:
            list of clean dict samples with ``_anonymization_version``
            metadata, ready for OpenAI/Anthropic/DPO packers.
        """
        from app.domains.analytics.services.training_data_anonymizer import (
            TrainingDataAnonymizer,
        )

        # ORM -> dict (canonical projection used by all 3 export packers)
        samples: list[dict[str, Any]] = []
        for fb in feedback_entries:
            samples.append({
                "user_message": getattr(fb, "user_message", None),
                "lia_response": getattr(fb, "lia_response", None),
                "correction": getattr(fb, "correction", None),
                "feedback_text": getattr(fb, "feedback_text", None),
                "candidate_id": getattr(fb, "candidate_id", None),
                "intent": getattr(fb, "intent", None),
                "stage": getattr(fb, "stage", None),
                "rating": getattr(fb, "rating", None),
            })

        if not samples:
            return []

        anonymizer = TrainingDataAnonymizer()
        clean = await anonymizer.process_batch(
            samples, company_id=company_id
        )
        self.logger.info(
            f"[T-21b] Anonymized {len(clean)} feedback samples for "
            f"company_id={company_id} (canonical TrainingDataAnonymizer)"
        )
        return clean
    
    async def export_openai_format(
        self,
        company_id: str,
        min_rating: int = 4,
        min_thumbs_ratio: float = 0.8,
        limit: int = 1000
    ) -> list[dict[str, Any]]:
        """
        Export training data in OpenAI fine-tuning format.
        
        Format:
        {"messages": [
            {"role": "system", "content": "<persona from lia_persona.yaml>"},
            {"role": "user", "content": "user message"},
            {"role": "assistant", "content": "good response"}
        ]}
        
        Args:
            company_id: Company UUID as string
            min_rating: Minimum rating for quality samples (default 4)
            min_thumbs_ratio: Minimum thumbs up ratio (not currently used)
            limit: Maximum number of samples to export
            
        Returns:
            List of training examples in OpenAI format
        """
        feedback_entries = await self._get_quality_feedback(
            company_id=company_id,
            min_rating=min_rating,
            limit=limit
        )
        
        # T-21b WIRE canonical: anonimização ANTES de empacotar (ADR-LGPD-002)
        anonymized = await self._anonymize_feedback_batch(
            feedback_entries, company_id=company_id
        )

        training_data = []
        for sample in anonymized:
            if not sample.get("user_message") or not sample.get("lia_response"):
                continue

            example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_FOR_TRAINING},
                    {"role": "user", "content": sample["user_message"]},
                    {"role": "assistant", "content": sample["lia_response"]},
                ],
                "_anonymization_version": sample.get("_anonymization_version"),
            }
            training_data.append(example)

        self.logger.info(
            f"Exported {len(training_data)} samples in OpenAI format for company {company_id} "
            f"(anonymized=TrainingDataAnonymizer canonical)"
        )

        return training_data
    
    async def export_anthropic_format(
        self,
        company_id: str,
        min_rating: int = 4,
        limit: int = 1000
    ) -> list[dict[str, Any]]:
        """
        Export training data in Anthropic format.
        
        Format:
        {"prompt": "\n\nHuman: user message\n\nAssistant:", "completion": " good response"}
        
        Args:
            company_id: Company UUID as string
            min_rating: Minimum rating for quality samples (default 4)
            limit: Maximum number of samples to export
            
        Returns:
            List of training examples in Anthropic format
        """
        feedback_entries = await self._get_quality_feedback(
            company_id=company_id,
            min_rating=min_rating,
            limit=limit
        )
        
        # T-21b WIRE canonical: anonimização ANTES de empacotar (ADR-LGPD-002)
        anonymized = await self._anonymize_feedback_batch(
            feedback_entries, company_id=company_id
        )

        training_data = []
        for sample in anonymized:
            if not sample.get("user_message") or not sample.get("lia_response"):
                continue

            prompt = f"\n\nHuman: {sample['user_message']}\n\nAssistant:"

            example = {
                "prompt": prompt,
                "completion": f" {sample['lia_response']}",
                "_anonymization_version": sample.get("_anonymization_version"),
            }
            training_data.append(example)

        self.logger.info(
            f"Exported {len(training_data)} samples in Anthropic format for company {company_id} "
            f"(anonymized=TrainingDataAnonymizer canonical)"
        )

        return training_data
    
    async def export_dpo_pairs(
        self,
        company_id: str,
        limit: int = 500
    ) -> list[dict[str, Any]]:
        """
        Export DPO (Direct Preference Optimization) training pairs.
        Uses corrections to create chosen/rejected pairs.
        
        Format:
        {"prompt": "user message", "chosen": "correction", "rejected": "original response"}
        
        Args:
            company_id: Company UUID as string
            limit: Maximum number of pairs to export
            
        Returns:
            List of DPO training pairs
        """
        feedback_entries = await self._get_quality_feedback(
            company_id=company_id,
            min_rating=1,
            limit=limit,
            require_correction=True
        )
        
        # T-21b WIRE canonical: anonimização ANTES de empacotar (ADR-LGPD-002)
        anonymized = await self._anonymize_feedback_batch(
            feedback_entries, company_id=company_id
        )

        dpo_pairs = []
        for sample in anonymized:
            if (
                not sample.get("user_message")
                or not sample.get("lia_response")
                or not sample.get("correction")
            ):
                continue

            if len(sample["correction"].strip()) < self.MIN_RESPONSE_LENGTH:
                continue

            pair = {
                "prompt": sample["user_message"],
                "chosen": sample["correction"],
                "rejected": sample["lia_response"],
                "_anonymization_version": sample.get("_anonymization_version"),
            }
            dpo_pairs.append(pair)

        self.logger.info(
            f"Exported {len(dpo_pairs)} DPO pairs for company {company_id} "
            f"(anonymized=TrainingDataAnonymizer canonical)"
        )

        return dpo_pairs
    
    async def get_export_statistics(
        self,
        company_id: str
    ) -> dict[str, Any]:
        """
        Get statistics about available training data.
        
        Args:
            company_id: Company UUID as string
            
        Returns:
            Dictionary with statistics about training data availability
        """
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return {"error": f"Invalid company_id: {company_id}"}
        
        base_filter = InteractionFeedback.company_id == company_uuid
        
        total_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(base_filter)
        )
        total_interactions = total_result.scalar() or 0
        
        with_response_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(
                and_(
                    base_filter,
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > self.MIN_RESPONSE_LENGTH
                )
            )
        )
        with_response = with_response_result.scalar() or 0
        
        thumbs_up_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(
                and_(base_filter, InteractionFeedback.thumbs == "up")
            )
        )
        thumbs_up = thumbs_up_result.scalar() or 0
        
        thumbs_down_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(
                and_(base_filter, InteractionFeedback.thumbs == "down")
            )
        )
        thumbs_down = thumbs_down_result.scalar() or 0
        
        high_rating_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(
                and_(base_filter, InteractionFeedback.rating >= 4)
            )
        )
        high_rating = high_rating_result.scalar() or 0
        
        corrections_result = await self.db.execute(
            select(func.count(InteractionFeedback.id)).where(
                and_(base_filter, InteractionFeedback.correction.isnot(None))
            )
        )
        corrections = corrections_result.scalar() or 0
        
        quality_feedback = await self._get_quality_feedback(
            company_id=company_id,
            min_rating=4,
            limit=10000
        )
        quality_samples = len(quality_feedback)
        
        dpo_pairs = await self.export_dpo_pairs(company_id=company_id, limit=10000)
        dpo_pair_count = len(dpo_pairs)
        
        openai_ready = quality_samples
        anthropic_ready = quality_samples
        
        return {
            "company_id": company_id,
            "total_interactions": total_interactions,
            "interactions_with_response": with_response,
            "thumbs_up_count": thumbs_up,
            "thumbs_down_count": thumbs_down,
            "high_rating_count": high_rating,
            "corrections_count": corrections,
            "quality_samples_available": quality_samples,
            "dpo_pairs_available": dpo_pair_count,
            "export_ready": {
                "openai_format": openai_ready,
                "anthropic_format": anthropic_ready,
                "dpo_pairs": dpo_pair_count
            },
            "quality_criteria": {
                "min_rating": 4,
                "min_response_length": self.MIN_RESPONSE_LENGTH,
                "min_confidence_score": self.MIN_CONFIDENCE_SCORE,
                "excludes_error_responses": True
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def curate_high_quality_samples(
        self,
        company_id: str,
        target_count: int = 500
    ) -> list[str]:
        """
        Automatically curate the best samples for training.
        Returns list of feedback IDs that meet quality criteria.
        
        Prioritizes samples with:
        1. Rating of 5 (highest priority)
        2. Rating of 4
        3. Thumbs up with high confidence scores
        
        Args:
            company_id: Company UUID as string
            target_count: Target number of samples to curate
            
        Returns:
            List of feedback IDs meeting quality criteria
        """
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            self.logger.warning(f"Invalid company_id: {company_id}")
            return []
        
        curated_ids = []
        
        repo = FeedbackRepository(self.db)
        rating_5_entries = await repo.list_feedback_by_rating(
            company_id=company_uuid,
            rating=5,
            limit=target_count,
            min_response_length=self.MIN_RESPONSE_LENGTH,
        )
        
        for entry in rating_5_entries:
            if self._is_quality_response(entry):
                curated_ids.append(str(entry.id))
        
        if len(curated_ids) >= target_count:
            self.logger.info(f"Curated {len(curated_ids)} samples (rating 5) for company {company_id}")
            return curated_ids[:target_count]
        
        remaining = target_count - len(curated_ids)
        rating_4_entries = await repo.list_feedback_by_rating(
            company_id=company_uuid,
            rating=4,
            limit=remaining * 2,
            min_response_length=self.MIN_RESPONSE_LENGTH,
        )
        
        for entry in rating_4_entries:
            if len(curated_ids) >= target_count:
                break
            if str(entry.id) not in curated_ids and self._is_quality_response(entry):
                curated_ids.append(str(entry.id))
        
        if len(curated_ids) >= target_count:
            self.logger.info(f"Curated {len(curated_ids)} samples (rating 4-5) for company {company_id}")
            return curated_ids[:target_count]
        
        remaining = target_count - len(curated_ids)
        thumbs_up_entries = await repo.list_feedback_thumbs_up(
            company_id=company_uuid,
            limit=remaining * 2,
            min_response_length=self.MIN_RESPONSE_LENGTH,
        )
        
        for entry in thumbs_up_entries:
            if len(curated_ids) >= target_count:
                break
            if str(entry.id) not in curated_ids and self._is_quality_response(entry):
                curated_ids.append(str(entry.id))
        
        self.logger.info(f"Curated {len(curated_ids)} samples for company {company_id}")
        return curated_ids[:target_count]
    
    def to_jsonl(self, data: list[dict[str, Any]]) -> str:
        """
        Convert a list of dictionaries to JSONL format.
        
        Args:
            data: List of dictionaries to convert
            
        Returns:
            JSONL formatted string (one JSON object per line)
        """
        lines = []
        for item in data:
            lines.append(json.dumps(item, ensure_ascii=False))
        return "\n".join(lines)
