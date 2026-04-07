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

from lia_models.feedback import InteractionFeedback

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_FOR_TRAINING = '''Você é LIA, uma assistente inteligente especializada em recrutamento e seleção.

Você ajuda recrutadores a:
- Criar vagas de emprego completas e atrativas
- Definir competências e requisitos adequados
- Analisar faixas salariais do mercado
- Gerar descrições de cargo profissionais

Responda sempre em português brasileiro, de forma clara e objetiva.
Seja proativa em fazer perguntas para coletar informações necessárias.
Demonstre expertise em RH e recrutamento.'''

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
        
        base_conditions = [
            InteractionFeedback.company_id == company_uuid,
            InteractionFeedback.user_message.isnot(None),
            InteractionFeedback.lia_response.isnot(None),
            func.length(InteractionFeedback.lia_response) > self.MIN_RESPONSE_LENGTH,
        ]
        
        if require_correction:
            base_conditions.append(InteractionFeedback.correction.isnot(None))
        else:
            quality_conditions = or_(
                InteractionFeedback.thumbs == "up",
                InteractionFeedback.rating >= min_rating
            )
            base_conditions.append(quality_conditions)
        
        result = await self.db.execute(
            select(InteractionFeedback)
            .where(and_(*base_conditions))
            .order_by(InteractionFeedback.created_at.desc())
            .limit(limit * 2)
        )
        all_feedback = result.scalars().all()
        
        quality_feedback = []
        for feedback in all_feedback:
            if require_correction or self._is_quality_response(feedback):
                quality_feedback.append(feedback)
                if len(quality_feedback) >= limit:
                    break
        
        return quality_feedback
    
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
            {"role": "system", "content": "You are LIA..."},
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
        
        training_data = []
        for feedback in feedback_entries:
            if not feedback.user_message or not feedback.lia_response:
                continue
            
            example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_FOR_TRAINING},
                    {"role": "user", "content": feedback.user_message},
                    {"role": "assistant", "content": feedback.lia_response}
                ]
            }
            training_data.append(example)
        
        self.logger.info(
            f"Exported {len(training_data)} samples in OpenAI format for company {company_id}"
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
        
        training_data = []
        for feedback in feedback_entries:
            if not feedback.user_message or not feedback.lia_response:
                continue
            
            prompt = f"\n\nHuman: {feedback.user_message}\n\nAssistant:"
            
            example = {
                "prompt": prompt,
                "completion": f" {feedback.lia_response}"
            }
            training_data.append(example)
        
        self.logger.info(
            f"Exported {len(training_data)} samples in Anthropic format for company {company_id}"
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
        
        dpo_pairs = []
        for feedback in feedback_entries:
            if not feedback.user_message or not feedback.lia_response or not feedback.correction:
                continue
            
            if len(feedback.correction.strip()) < self.MIN_RESPONSE_LENGTH:
                continue
            
            pair = {
                "prompt": feedback.user_message,
                "chosen": feedback.correction,
                "rejected": feedback.lia_response
            }
            dpo_pairs.append(pair)
        
        self.logger.info(
            f"Exported {len(dpo_pairs)} DPO pairs for company {company_id}"
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
        
        rating_5_result = await self.db.execute(
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.company_id == company_uuid,
                    InteractionFeedback.rating == 5,
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > self.MIN_RESPONSE_LENGTH
                )
            )
            .order_by(InteractionFeedback.created_at.desc())
            .limit(target_count)
        )
        rating_5_entries = rating_5_result.scalars().all()
        
        for entry in rating_5_entries:
            if self._is_quality_response(entry):
                curated_ids.append(str(entry.id))
        
        if len(curated_ids) >= target_count:
            self.logger.info(f"Curated {len(curated_ids)} samples (rating 5) for company {company_id}")
            return curated_ids[:target_count]
        
        remaining = target_count - len(curated_ids)
        rating_4_result = await self.db.execute(
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.company_id == company_uuid,
                    InteractionFeedback.rating == 4,
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > self.MIN_RESPONSE_LENGTH
                )
            )
            .order_by(InteractionFeedback.created_at.desc())
            .limit(remaining * 2)
        )
        rating_4_entries = rating_4_result.scalars().all()
        
        for entry in rating_4_entries:
            if len(curated_ids) >= target_count:
                break
            if str(entry.id) not in curated_ids and self._is_quality_response(entry):
                curated_ids.append(str(entry.id))
        
        if len(curated_ids) >= target_count:
            self.logger.info(f"Curated {len(curated_ids)} samples (rating 4-5) for company {company_id}")
            return curated_ids[:target_count]
        
        remaining = target_count - len(curated_ids)
        thumbs_up_result = await self.db.execute(
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.company_id == company_uuid,
                    InteractionFeedback.thumbs == "up",
                    InteractionFeedback.lia_response.isnot(None),
                    func.length(InteractionFeedback.lia_response) > self.MIN_RESPONSE_LENGTH
                )
            )
            .order_by(
                InteractionFeedback.confidence_score.desc().nullslast(),
                InteractionFeedback.created_at.desc()
            )
            .limit(remaining * 2)
        )
        thumbs_up_entries = thumbs_up_result.scalars().all()
        
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
