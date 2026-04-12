import json
import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback_learning import (
    JobOutcome,
    JobOutcomeType,
    SuggestionFeedback,
    WizardFeedback,
)

logger = logging.getLogger(__name__)


class FineTuningExportService:

    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    PHONE_PATTERN = re.compile(r'\(?\d{2}\)?\s?\d{4,5}[-.\s]?\d{4}')
    CPF_PATTERN = re.compile(r'\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}')
    NAME_PATTERN = re.compile(
        r'\b[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+'
        r'(?:\s+(?:de|da|do|dos|das|e)\s+)?'
        r'(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+){1,4}\b'
    )

    TECHNICAL_TERMS = {
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node", "docker", "kubernetes", "aws", "azure", "gcp", "sql", "nosql",
        "mongodb", "postgresql", "redis", "kafka", "rabbitmq", "elasticsearch",
        "machine learning", "deep learning", "data science", "devops", "ci/cd",
        "agile", "scrum", "kanban", "product manager", "tech lead", "backend",
        "frontend", "fullstack", "mobile", "ios", "android", "flutter", "react native",
        "senior", "junior", "pleno", "estagiário", "analista", "coordenador",
        "gerente", "diretor", "vp", "cto", "ceo", "cfo", "coo",
    }

    async def mask_pii(self, text: str) -> str:
        if not text:
            return text

        masked = self.EMAIL_PATTERN.sub('[EMAIL]', text)
        masked = self.PHONE_PATTERN.sub('[PHONE]', masked)
        masked = self.CPF_PATTERN.sub('[CPF]', masked)

        def replace_name(match):
            name = match.group(0)
            if name.lower() in self.TECHNICAL_TERMS:
                return name
            return '[NAME]'

        masked = self.NAME_PATTERN.sub(replace_name, masked)
        return masked

    def _format_value_as_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    async def export_wizard_interactions(
        self,
        company_id: str,
        db: AsyncSession,
        format: str = 'jsonl',
        min_quality_score: float = 0.7,
    ) -> list[str]:
        try:
            filled_job_ids = set()
            try:
                outcome_result = await db.execute(
                    select(JobOutcome.job_id).where(
                        and_(
                            JobOutcome.company_id == company_id,
                            JobOutcome.outcome == JobOutcomeType.FILLED,
                        )
                    )
                )
                filled_job_ids = {str(row) for row in outcome_result.scalars().all()}
            except Exception:
                pass

            wizard_result = await db.execute(
                select(WizardFeedback).where(
                    and_(
                        WizardFeedback.company_id == company_id,
                        WizardFeedback.corrected_value.isnot(None),
                    )
                ).order_by(WizardFeedback.created_at)
            )
            wizard_feedbacks = wizard_result.scalars().all()

            suggestion_result = await db.execute(
                select(SuggestionFeedback).where(
                    and_(
                        SuggestionFeedback.company_id == company_id,
                        SuggestionFeedback.accepted == 1,
                    )
                ).order_by(SuggestionFeedback.created_at)
            )
            suggestion_feedbacks = suggestion_result.scalars().all()

            training_examples = []

            for wf in wizard_feedbacks:
                if filled_job_ids and str(wf.job_id) not in filled_job_ids:
                    if min_quality_score > 0.5:
                        continue

                self._format_value_as_text(wf.original_value)
                corrected_text = self._format_value_as_text(wf.corrected_value)

                from app.shared.prompts.training_persona import TRAINING_PERSONA
                system_content = TRAINING_PERSONA

                context_parts = []
                if wf.role:
                    context_parts.append(f"Role: {wf.role}")
                if wf.seniority:
                    context_parts.append(f"Seniority: {wf.seniority}")
                if wf.department:
                    context_parts.append(f"Department: {wf.department}")
                if wf.location:
                    context_parts.append(f"Location: {wf.location}")

                context_str = ", ".join(context_parts) if context_parts else "General context"

                user_content = await self.mask_pii(
                    f"Suggest a value for the field '{wf.field_corrected}' "
                    f"given the following context: {context_str}."
                )

                assistant_content = await self.mask_pii(corrected_text)

                example = {
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_content},
                    ]
                }

                training_examples.append(json.dumps(example, ensure_ascii=False))

            for sf in suggestion_feedbacks:
                value_text = self._format_value_as_text(
                    sf.actual_value if sf.actual_value else sf.suggested_value
                )

                from app.shared.prompts.training_persona import TRAINING_PERSONA
                system_content = TRAINING_PERSONA

                context_info = ""
                if sf.context and isinstance(sf.context, dict):
                    ctx_parts = []
                    for k, v in sf.context.items():
                        if v:
                            ctx_parts.append(f"{k}: {v}")
                    context_info = ", ".join(ctx_parts) if ctx_parts else "General"
                else:
                    context_info = "General"

                user_content = await self.mask_pii(
                    f"Suggest a value for '{sf.field_name}'. Context: {context_info}."
                )

                assistant_content = await self.mask_pii(value_text)

                example = {
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_content},
                    ]
                }

                training_examples.append(json.dumps(example, ensure_ascii=False))

            return training_examples

        except Exception as e:
            logger.error(f"Error exporting wizard interactions: {e}")
            return []

    async def export_to_file(
        self,
        company_id: str,
        db: AsyncSession,
        output_format: str = 'claude',
    ) -> str:
        examples = await self.export_wizard_interactions(company_id, db)

        metadata = {
            "metadata": {
                "company_id": company_id,
                "export_date": datetime.utcnow().isoformat(),
                "sample_count": len(examples),
                "quality_threshold": 0.7,
                "format": output_format,
            }
        }

        lines = [json.dumps(metadata, ensure_ascii=False)]

        if output_format == 'gpt':
            for example_line in examples:
                example = json.loads(example_line)
                lines.append(json.dumps(example, ensure_ascii=False))
        else:
            for example_line in examples:
                example = json.loads(example_line)
                lines.append(json.dumps(example, ensure_ascii=False))

        return "\n".join(lines)

    async def get_export_stats(
        self,
        company_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        try:
            wizard_total = await db.execute(
                select(func.count(WizardFeedback.id)).where(
                    WizardFeedback.company_id == company_id
                )
            )
            total_wizard = wizard_total.scalar() or 0

            suggestion_total = await db.execute(
                select(func.count(SuggestionFeedback.id)).where(
                    SuggestionFeedback.company_id == company_id
                )
            )
            total_suggestion = suggestion_total.scalar() or 0

            wizard_with_correction = await db.execute(
                select(func.count(WizardFeedback.id)).where(
                    and_(
                        WizardFeedback.company_id == company_id,
                        WizardFeedback.corrected_value.isnot(None),
                    )
                )
            )
            quality_wizard = wizard_with_correction.scalar() or 0

            accepted_suggestions = await db.execute(
                select(func.count(SuggestionFeedback.id)).where(
                    and_(
                        SuggestionFeedback.company_id == company_id,
                        SuggestionFeedback.accepted == 1,
                    )
                )
            )
            quality_suggestion = accepted_suggestions.scalar() or 0

            field_breakdown_result = await db.execute(
                select(
                    WizardFeedback.field_corrected,
                    func.count(WizardFeedback.id),
                ).where(
                    WizardFeedback.company_id == company_id
                ).group_by(WizardFeedback.field_corrected)
            )
            field_breakdown = {
                row[0]: row[1] for row in field_breakdown_result.all()
            }

            suggestion_field_result = await db.execute(
                select(
                    SuggestionFeedback.field_name,
                    func.count(SuggestionFeedback.id),
                ).where(
                    SuggestionFeedback.company_id == company_id
                ).group_by(SuggestionFeedback.field_name)
            )
            for row in suggestion_field_result.all():
                key = f"suggestion_{row[0]}"
                field_breakdown[key] = row[1]

            filled_count = await db.execute(
                select(func.count(JobOutcome.id)).where(
                    and_(
                        JobOutcome.company_id == company_id,
                        JobOutcome.outcome == JobOutcomeType.FILLED,
                    )
                )
            )
            total_filled = filled_count.scalar() or 0

            total_interactions = total_wizard + total_suggestion
            quality_interactions = quality_wizard + quality_suggestion

            if total_interactions > 0:
                quality_ratio = quality_interactions / total_interactions
                filled_bonus = min(0.2, (total_filled / max(total_interactions, 1)) * 0.2)
                estimated_quality = min(1.0, quality_ratio * 0.8 + filled_bonus + 0.1)
            else:
                estimated_quality = 0.0

            return {
                "company_id": company_id,
                "total_interactions": total_interactions,
                "total_wizard_feedback": total_wizard,
                "total_suggestion_feedback": total_suggestion,
                "quality_filtered_count": quality_interactions,
                "filled_positions": total_filled,
                "field_breakdown": field_breakdown,
                "estimated_training_quality": round(estimated_quality, 3),
                "export_ready": quality_interactions >= 10,
            }

        except Exception as e:
            logger.error(f"Error getting export stats: {e}")
            return {
                "company_id": company_id,
                "total_interactions": 0,
                "quality_filtered_count": 0,
                "field_breakdown": {},
                "estimated_training_quality": 0.0,
                "export_ready": False,
                "error": str(e),
            }


finetuning_export_service = FineTuningExportService()


