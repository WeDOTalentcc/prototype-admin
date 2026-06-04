"""
Feedback Service - Captures and processes user feedback on LIA interactions.

Enables continuous learning by:
- Recording thumbs up/down, ratings, and corrections
- Processing feedback to extract learning patterns
- Retrieving relevant patterns for response generation
- Providing feedback metrics for analysis
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.analytics.repositories.feedback_repository import FeedbackRepository
from lia_models.feedback import InteractionFeedback, LearningPattern

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Service for capturing and processing user feedback on LIA interactions.
    
    Features:
    - Record various types of feedback (thumbs, ratings, corrections)
    - Process feedback batches to extract learning patterns
    - Retrieve relevant patterns for response generation
    - Track feedback metrics over time
    """
    
    MIN_SAMPLES_FOR_PATTERN = 5
    HIGH_CONFIDENCE_THRESHOLD = 20
    MEDIUM_CONFIDENCE_THRESHOLD = 10
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def record_feedback(
        self,
        session_id: str,
        company_id: str,
        user_id: str,
        feedback_type: str,
        feedback_value: Any,
        message_context: dict,
        db: AsyncSession | None = None
    ) -> InteractionFeedback:
        """
        Record user feedback on a LIA interaction.
        
        Args:
            session_id: Session identifier
            company_id: Company UUID as string
            user_id: User identifier
            feedback_type: Type of feedback ('thumbs', 'rating', 'correction')
            feedback_value: The feedback value (depends on type)
            message_context: Context about the message being rated
            db: Optional database session
        
        Returns:
            Created InteractionFeedback record
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            feedback = InteractionFeedback(
                id=uuid4(),
                session_id=session_id,
                company_id=UUID(company_id),
                user_id=user_id,
                message_id=message_context.get("message_id"),
                user_message=message_context.get("user_message"),
                lia_response=message_context.get("lia_response"),
                intent=message_context.get("intent"),
                stage=message_context.get("stage"),
                response_time_ms=message_context.get("response_time_ms"),
                tools_used=message_context.get("tools_used", []),
                confidence_score=message_context.get("confidence_score"),
            )
            
            if feedback_type == "thumbs":
                feedback.thumbs = feedback_value
            elif feedback_type == "rating":
                if isinstance(feedback_value, dict):
                    feedback.rating = feedback_value.get("rating")
                    feedback.feedback_text = feedback_value.get("feedback_text")
                    feedback.feedback_category = feedback_value.get("category")
                else:
                    feedback.rating = feedback_value
            elif feedback_type == "correction":
                feedback.correction = feedback_value
            
            db.add(feedback)
            await db.commit()
            await db.refresh(feedback)
            
            self.logger.info(
                f"Recorded {feedback_type} feedback for session {session_id}, "
                f"message_id={message_context.get('message_id')}"
            )
            
            await self._update_patterns_from_feedback(feedback, db)
            
            return feedback
            
        except Exception as e:
            if db:
                await db.rollback()
            self.logger.error(f"Error recording feedback: {e}")
            raise
        finally:
            if should_close and db:
                await db.close()
    
    async def record_implicit_negative(
        self,
        session_id: str,
        company_id: str,
        user_id: str,
        signal_type: str,
        message_context: dict,
        db: AsyncSession | None = None,
    ) -> InteractionFeedback:
        """Task #1299: persist an IMPLICIT negative signal into the SAME
        ``interaction_feedback`` table + learning-pattern path used by the
        explicit thumbs/rating/correction loop, WITHOUT setting ``thumbs`` /
        ``rating`` (so explicit satisfaction metrics stay clean).

        The row is tagged ``feedback_category="implicit_<signal_type>"`` for
        analytics buckets, and a transient ``_implicit_negative`` marker makes
        ``_update_patterns_from_feedback`` demote the matching pattern
        (``negative_feedback_count`` + ``example_bad_responses``).

        Args:
            signal_type: "regeneration" | "correction_delta" | "abandonment".
            message_context: same shape as ``record_feedback`` (carries
                message_id / user_message / lia_response / intent / stage).

        Returns:
            The created InteractionFeedback row.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            feedback = InteractionFeedback(
                id=uuid4(),
                session_id=session_id,
                company_id=UUID(company_id),
                user_id=user_id,
                message_id=message_context.get("message_id"),
                user_message=message_context.get("user_message"),
                lia_response=message_context.get("lia_response"),
                intent=message_context.get("intent"),
                stage=message_context.get("stage"),
                response_time_ms=message_context.get("response_time_ms"),
                tools_used=message_context.get("tools_used", []),
                confidence_score=message_context.get("confidence_score"),
                feedback_category=f"implicit_{signal_type}",
            )
            # Transient marker (NOT a column) → _update_patterns_from_feedback
            # treats this as a negative without touching thumbs/rating.
            feedback._implicit_negative = True

            db.add(feedback)
            await db.commit()
            await db.refresh(feedback)
            # refresh() reloads from DB and drops the transient attribute — re-set it.
            feedback._implicit_negative = True

            self.logger.info(
                "Recorded implicit negative (%s) for session %s message_id=%s",
                signal_type, session_id, message_context.get("message_id"),
            )

            await self._update_patterns_from_feedback(feedback, db)
            return feedback
        except Exception as e:
            if db:
                await db.rollback()
            self.logger.error(f"Error recording implicit negative: {e}")
            raise
        finally:
            if should_close and db:
                await db.close()

    async def _update_patterns_from_feedback(
        self,
        feedback: InteractionFeedback,
        db: AsyncSession
    ) -> None:
        """Update learning patterns based on new feedback.

        Task #1297: o early-return original ``if not feedback.intent: return``
        matava 100% da aprendizagem do chat — os polegares 👍/👎 não carregam
        ``intent`` no contexto, então NENHUM padrão era gerado (tabela
        ``learning_patterns`` vazia apesar de 14k+ mensagens). Agora geramos
        o padrão mesmo sem intent: ``_generate_pattern_key`` já degrada para
        ``"general"``, criando um sinal agregado por tenant que ainda captura
        bons/maus exemplos de resposta. Mantém-se a granularidade por intent
        quando o contexto o fornece.
        """
        try:
            pattern_key = self._generate_pattern_key(feedback)
            company_id = feedback.company_id
            
            repo = FeedbackRepository(db)
            pattern = await repo.find_active_pattern(company_id, pattern_key)
            
            is_positive = (
                feedback.thumbs == "up" or 
                (feedback.rating is not None and feedback.rating >= 4)
            )
            is_negative = (
                feedback.thumbs == "down" or 
                (feedback.rating is not None and feedback.rating <= 2) or
                feedback.correction is not None or
                # Task #1299: implicit negative signals (regeneration /
                # correction-delta) carry no thumbs/rating — they tag a
                # transient marker so they still demote the pattern WITHOUT
                # polluting the explicit thumbs/satisfaction metrics.
                getattr(feedback, "_implicit_negative", False)
            )
            
            if pattern:
                if is_positive:
                    pattern.positive_feedback_count += 1
                    if feedback.lia_response and pattern.example_good_responses is not None:
                        examples = list(pattern.example_good_responses)
                        if len(examples) < 5:
                            examples.append(feedback.lia_response)
                            pattern.example_good_responses = examples
                elif is_negative:
                    pattern.negative_feedback_count += 1
                    if feedback.lia_response and pattern.example_bad_responses is not None:
                        examples = list(pattern.example_bad_responses)
                        if len(examples) < 5:
                            examples.append(feedback.lia_response)
                            pattern.example_bad_responses = examples
                
                pattern.calculate_success_rate()
                pattern.update_confidence()
                pattern.updated_at = datetime.utcnow()
                
            else:
                pattern = LearningPattern(
                    id=uuid4(),
                    company_id=company_id,
                    pattern_type="intent",
                    pattern_key=pattern_key,
                    trigger_phrases=[feedback.user_message] if feedback.user_message else [],
                    positive_feedback_count=1 if is_positive else 0,
                    negative_feedback_count=1 if is_negative else 0,
                    example_good_responses=[feedback.lia_response] if is_positive and feedback.lia_response else [],
                    example_bad_responses=[feedback.lia_response] if is_negative and feedback.lia_response else [],
                )
                pattern.calculate_success_rate()
                pattern.update_confidence()
                db.add(pattern)
            
            await db.commit()
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Error updating patterns from feedback: {e}")
    
    def _generate_pattern_key(self, feedback: InteractionFeedback) -> str:
        """Generate a unique pattern key from feedback context."""
        parts = []
        if feedback.intent:
            parts.append(feedback.intent)
        if feedback.stage:
            parts.append(feedback.stage)
        return "_".join(parts) if parts else "general"
    
    async def process_feedback_batch(
        self,
        db: AsyncSession | None = None
    ) -> dict:
        """
        Process unprocessed feedback to extract and update learning patterns.
        
        Returns:
            Dictionary with processing statistics
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            repo = FeedbackRepository(db)
            unprocessed = await repo.list_unprocessed_feedback(limit=100)
            
            processed_count = 0
            patterns_updated = 0
            
            for feedback in unprocessed:
                try:
                    await self._update_patterns_from_feedback(feedback, db)
                    feedback.processed = True
                    processed_count += 1
                    patterns_updated += 1
                except Exception as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    self.logger.error(f"Error processing feedback {feedback.id}: {e}")
            
            await db.commit()
            
            self.logger.info(
                f"Processed {processed_count} feedback items, "
                f"updated {patterns_updated} patterns"
            )
            
            return {
                "processed_count": processed_count,
                "patterns_updated": patterns_updated,
                "remaining": len(unprocessed) - processed_count
            }
            
        except Exception as e:
            if db:
                await db.rollback()
            self.logger.error(f"Error processing feedback batch: {e}")
            raise
        finally:
            if should_close and db:
                await db.close()
    
    async def get_relevant_patterns(
        self,
        intent: str,
        user_message: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> list[LearningPattern]:
        """
        Get learning patterns relevant to the current context.
        
        Args:
            intent: Classified user intent
            user_message: The user's message
            company_id: Company UUID as string
        
        Returns:
            List of relevant LearningPattern objects
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                self.logger.warning(f"Invalid company_id: {company_id}")
                return []
            
            repo = FeedbackRepository(db)
            all_patterns = await repo.list_active_patterns_min_confidence(
                company_uuid, min_confidence=0.5
            )
            
            relevant = []
            for pattern in all_patterns:
                # Task #1297: padrões "general" (feedback sem intent explícito —
                # o caso comum dos polegares no chat) são sempre relevantes;
                # representam preferência agregada do tenant aplicável a
                # qualquer turno conversacional.
                if (pattern.pattern_key or "") == "general":
                    relevant.append(pattern)
                    continue

                if pattern.pattern_type == "intent" and intent and intent in (pattern.pattern_key or ""):
                    relevant.append(pattern)
                    continue
                
                trigger_phrases = pattern.trigger_phrases or []
                for phrase in trigger_phrases:
                    if phrase and phrase.lower() in user_message.lower():
                        relevant.append(pattern)
                        break
            
            self.logger.debug(
                f"Found {len(relevant)} relevant patterns for intent={intent}, "
                f"company={company_id}"
            )
            
            return relevant
            
        except Exception as e:
            self.logger.error(f"Error getting relevant patterns: {e}")
            return []
        finally:
            if should_close and db:
                await db.close()
    
    async def update_pattern_from_feedback(
        self,
        pattern_id: str,
        feedback: InteractionFeedback,
        db: AsyncSession | None = None
    ) -> None:
        """
        Update a specific pattern based on feedback.
        
        Args:
            pattern_id: UUID of the pattern to update
            feedback: The feedback to incorporate
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            try:
                pattern_uuid = UUID(pattern_id)
            except ValueError:
                self.logger.warning(f"Invalid pattern_id: {pattern_id}")
                return
            
            repo = FeedbackRepository(db)
            pattern = await repo.find_pattern_by_id(pattern_uuid)
            
            if not pattern:
                self.logger.warning(f"Pattern not found: {pattern_id}")
                return
            
            is_positive = (
                feedback.thumbs == "up" or 
                (feedback.rating is not None and feedback.rating >= 4)
            )
            
            if is_positive:
                pattern.positive_feedback_count += 1
            else:
                pattern.negative_feedback_count += 1
            
            pattern.calculate_success_rate()
            pattern.update_confidence()
            pattern.updated_at = datetime.utcnow()
            
            await db.commit()
            
            self.logger.info(f"Updated pattern {pattern_id} from feedback")
            
        except Exception as e:
            if db:
                await db.rollback()
            self.logger.error(f"Error updating pattern from feedback: {e}")
        finally:
            if should_close and db:
                await db.close()
    
    async def get_feedback_metrics(
        self,
        company_id: str,
        days: int = 30,
        db: AsyncSession | None = None
    ) -> dict:
        """
        Get aggregated feedback metrics for a company.
        
        Args:
            company_id: Company UUID as string
            days: Number of days to analyze
        
        Returns:
            Dictionary with aggregated metrics
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            try:
                company_uuid = UUID(company_id)
            except ValueError:
                return {"error": f"Invalid company_id: {company_id}"}
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            base_filter = and_(
                InteractionFeedback.company_id == company_uuid,
                InteractionFeedback.created_at >= cutoff_date
            )
            
            total_result = await db.execute(
                select(func.count(InteractionFeedback.id)).where(base_filter)
            )
            total_feedback = total_result.scalar() or 0
            
            thumbs_up_result = await db.execute(
                select(func.count(InteractionFeedback.id)).where(
                    and_(base_filter, InteractionFeedback.thumbs == "up")
                )
            )
            thumbs_up = thumbs_up_result.scalar() or 0
            
            thumbs_down_result = await db.execute(
                select(func.count(InteractionFeedback.id)).where(
                    and_(base_filter, InteractionFeedback.thumbs == "down")
                )
            )
            thumbs_down = thumbs_down_result.scalar() or 0
            
            avg_rating_result = await db.execute(
                select(func.avg(InteractionFeedback.rating)).where(
                    and_(base_filter, InteractionFeedback.rating.isnot(None))
                )
            )
            avg_rating = avg_rating_result.scalar()
            
            corrections_result = await db.execute(
                select(func.count(InteractionFeedback.id)).where(
                    and_(base_filter, InteractionFeedback.correction.isnot(None))
                )
            )
            corrections = corrections_result.scalar() or 0
            
            intent_result = await db.execute(
                select(
                    InteractionFeedback.intent,
                    func.count(InteractionFeedback.id).label("count")
                ).where(
                    and_(base_filter, InteractionFeedback.intent.isnot(None))
                ).group_by(InteractionFeedback.intent)
                .order_by(func.count(InteractionFeedback.id).desc())
                .limit(10)
            )
            intent_distribution = {
                row.intent: row.count for row in intent_result.all()
            }
            
            pattern_result = await db.execute(
                select(func.count(LearningPattern.id)).where(
                    and_(
                        LearningPattern.company_id == company_uuid,
                        LearningPattern.is_active
                    )
                )
            )
            active_patterns = pattern_result.scalar() or 0
            
            high_conf_result = await db.execute(
                select(func.count(LearningPattern.id)).where(
                    and_(
                        LearningPattern.company_id == company_uuid,
                        LearningPattern.is_active,
                        LearningPattern.confidence >= 0.7
                    )
                )
            )
            high_confidence_patterns = high_conf_result.scalar() or 0
            
            total_thumbs = thumbs_up + thumbs_down
            satisfaction_rate = (thumbs_up / total_thumbs * 100) if total_thumbs > 0 else None
            
            return {
                "period_days": days,
                "total_feedback": total_feedback,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "satisfaction_rate": round(satisfaction_rate, 2) if satisfaction_rate else None,
                "average_rating": round(avg_rating, 2) if avg_rating else None,
                "corrections_count": corrections,
                "intent_distribution": intent_distribution,
                "active_patterns": active_patterns,
                "high_confidence_patterns": high_confidence_patterns,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting feedback metrics: {e}")
            return {"error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def get_pattern_context_for_response(
        self,
        intent: str,
        user_message: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict:
        """
        Get pattern context to include in response generation prompts.
        
        Args:
            intent: Classified user intent
            user_message: The user's message
            company_id: Company UUID as string
        
        Returns:
            Dictionary with pattern context for prompts
        """
        patterns = await self.get_relevant_patterns(
            intent=intent,
            user_message=user_message,
            company_id=company_id,
            db=db
        )
        
        if not patterns:
            return {"has_patterns": False}
        
        good_examples = []
        bad_examples = []
        response_hints = []
        
        for pattern in patterns[:3]:
            if pattern.example_good_responses:
                good_examples.extend(pattern.example_good_responses[:2])
            if pattern.example_bad_responses:
                bad_examples.extend(pattern.example_bad_responses[:2])
            if pattern.expected_response_style:
                response_hints.append(pattern.expected_response_style)
        
        return {
            "has_patterns": True,
            "pattern_count": len(patterns),
            "good_response_examples": good_examples[:3],
            "bad_response_examples": bad_examples[:3],
            "response_style_hints": response_hints[:2],
            "average_success_rate": sum(p.success_rate for p in patterns) / len(patterns),
        }

    async def get_learned_examples_block(
        self,
        intent: str,
        user_message: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> str:
        """Task #1297: formata os exemplos bons/ruins aprendidos do feedback
        real do tenant numa seção de prompt pronta para injeção.

        Fecha o gap "padrões aprendidos só consumidos pelo wizard": este bloco
        é injetado pelo helper canônico ``build_system_prompt_with_persona``,
        então TODOS os caminhos de chat (geral + agentes ReAct) passam a
        respeitar o feedback do recrutador, não só o wizard de criação de vaga.

        Fail-open: retorna ``""`` em qualquer erro ou ausência de padrões —
        nunca bloqueia a geração de resposta.
        """
        try:
            context = await self.get_pattern_context_for_response(
                intent=intent or "",
                user_message=user_message or "",
                company_id=company_id,
                db=db,
            )
        except Exception as e:
            self.logger.warning(f"get_learned_examples_block failed: {e}")
            return ""

        if not context.get("has_patterns"):
            return ""

        good = context.get("good_response_examples") or []
        bad = context.get("bad_response_examples") or []
        hints = context.get("response_style_hints") or []
        if not (good or bad or hints):
            return ""

        lines: list[str] = [
            "\n## Aprendizado do Feedback do Recrutador",
            "Estes exemplos vêm do feedback real (👍/👎/correção) deste cliente. "
            "Use-os para calibrar o estilo e o conteúdo da sua resposta.",
        ]
        if good:
            lines.append("\n### Respostas bem avaliadas (espelhe o estilo):")
            lines.extend(f"- {ex}" for ex in good)
        if bad:
            lines.append("\n### Respostas mal avaliadas (evite este padrão):")
            lines.extend(f"- {ex}" for ex in bad)
        if hints:
            lines.append("\n### Preferências de estilo:")
            lines.extend(f"- {h}" for h in hints)
        return "\n".join(lines)


feedback_service = FeedbackService()
