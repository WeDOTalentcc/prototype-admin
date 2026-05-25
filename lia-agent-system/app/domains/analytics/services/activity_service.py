"""
Activity Feed Service

Manages activity feed creation and retrieval for the recruitment system.
Tracks voice screenings, emails, interviews, approvals, tests, and other activities.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, or_, select

from app.core.database import AsyncSessionLocal
from app.domains.analytics.repositories.activity_feed_repository import (
    ActivityFeedRepository,
)
from app.models import ActivityFeed

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for managing activity feed"""
    
    async def create_activity(
        self,
        activity_type: str,
        title: str,
        description: str | None = None,
        summary: str | None = None,
        actor_id: str | None = None,
        actor_name: str | None = None,
        actor_type: str | None = None,
        target_id: str | None = None,
        target_name: str | None = None,
        target_type: str | None = None,
        extra_data: dict[str, Any] | None = None,
        priority: str = "normal",
        category: str | None = None,
        action_url: str | None = None,
        action_label: str | None = None,
        visible_to: list[str] | None = None,
        created_by: str | None = None,
        legal_basis: str | None = "legitimate_interests",
        decision_type: str | None = None,
        retention_days: int | None = 730,
    ) -> ActivityFeed:
        """
        Create a new activity in the feed.
        
        Args:
            activity_type: Type of activity (voice_screening, email_sent, etc.)
            title: Activity title (e.g., "Voice Screening Completado")
            description: Longer description (optional)
            summary: Short summary for cards (optional)
            actor_id: ID of who performed the action (user_id, "system", "lia")
            actor_name: Display name of actor
            actor_type: Type of actor (recruiter, system, candidate, ai)
            target_id: ID of what/who was affected (candidate_id, job_id, etc.)
            target_name: Display name of target
            target_type: Type of target (candidate, job, email, test)
            extra_data: Activity-specific data (JSON)
            priority: urgent, normal, low (default: normal)
            category: screening, hiring, communication, testing
            action_url: URL for CTA button
            action_label: Label for CTA button
            visible_to: List of user_ids who can see this (empty = visible to all)
            created_by: User who triggered this activity
            
        Returns:
            Created ActivityFeed instance
        """
        async with AsyncSessionLocal() as session:
            _retention = (
                datetime.utcnow() + timedelta(days=retention_days)
                if retention_days is not None else None
            )
            activity = ActivityFeed(
                activity_type=activity_type,
                title=title,
                description=description,
                summary=summary,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_type=actor_type,
                target_id=target_id,
                target_name=target_name,
                target_type=target_type,
                extra_data=extra_data or {},
                priority=priority,
                category=category,
                action_url=action_url,
                action_label=action_label,
                is_visible=True,
                visible_to=visible_to or [],
                created_by=created_by,
                legal_basis=legal_basis,
                decision_type=decision_type,
                retention_expires_at=_retention,
            )
            
            session.add(activity)
            await session.commit()
            await session.refresh(activity)
            
            logger.info(f"✅ Activity created: {activity_type} - {title}")
            return activity
    
    async def list_activities(
        self,
        activity_type: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        candidate_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List activities with optional filters.
        
        Args:
            activity_type: Filter by activity type
            priority: Filter by priority (urgent, normal, low)
            category: Filter by category
            candidate_id: Filter by candidate (target_id or actor_id)
            limit: Max number of results (default: 50)
            offset: Offset for pagination (default: 0)
            
        Returns:
            Dict with activities list and total count
        """
        from sqlalchemy import func
        
        async with AsyncSessionLocal() as session:
            # Build WHERE conditions (reusable for both queries)
            where_conditions = [ActivityFeed.is_visible]
            
            if activity_type:
                where_conditions.append(ActivityFeed.activity_type == activity_type)
            
            if priority:
                where_conditions.append(ActivityFeed.priority == priority)
            
            if category:
                where_conditions.append(ActivityFeed.category == category)
            
            if candidate_id:
                # Filter by candidate as target OR actor
                where_conditions.append(
                    or_(
                        ActivityFeed.target_id == candidate_id,
                        ActivityFeed.actor_id == candidate_id
                    )
                )
            
            repo = ActivityFeedRepository(session)
            activities, total = await repo.list_with_filters(
                where_conditions=where_conditions,
                limit=limit,
                offset=offset,
            )
            
            logger.info(f"📋 Retrieved {len(activities)} activities (total: {total})")
            
            return {
                "activities": [activity.to_dict() for activity in activities],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
    
    async def get_activity_by_id(self, activity_id: str) -> ActivityFeed | None:
        """
        Get a single activity by ID.
        
        Args:
            activity_id: Activity UUID
            
        Returns:
            ActivityFeed instance or None if not found
        """
        async with AsyncSessionLocal() as session:
            repo = ActivityFeedRepository(session)
            activity = await repo.get_by_id(activity_id)
            
            if activity:
                logger.info(f"📋 Retrieved activity: {activity.title}")
            else:
                logger.warning(f"⚠️  Activity not found: {activity_id}")
            
            return activity
    
    async def get_urgent_count(self, user_id: str | None = None) -> int:
        """
        Get count of urgent unread activities.
        Used for header badge notification count.
        
        Args:
            user_id: Optional user_id to filter visible_to
            
        Returns:
            Count of urgent activities
        """
        async with AsyncSessionLocal() as session:
            repo = ActivityFeedRepository(session)
            activities = await repo.list_urgent_visible()
            
            logger.info(f"🔔 {len(activities)} urgent activities")
            return len(activities)
    
    # ========== HELPER METHODS FOR COMMON ACTIVITY TYPES ==========
    
    async def create_interview_scheduled(
        self,
        candidate_id: str,
        candidate_name: str,
        job_title: str,
        interviewer_name: str,
        interview_date: datetime,
        interview_type: str = "technical",
        scheduled_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for scheduled interview.
        Type: entrevista (mockup)
        """
        return await self.create_activity(
            activity_type="interview_scheduled",
            title=f"Entrevista Agendada - {candidate_name}",
            description=f"{job_title} • {interview_type.title()}",
            summary=f"Entrevista com {interviewer_name} em {interview_date.strftime('%d/%m às %H:%M')}",
            actor_id=scheduled_by or "system",
            actor_name=interviewer_name,
            actor_type="recruiter",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "interview_date": interview_date.isoformat(),
                "interview_type": interview_type,
                "interviewer_name": interviewer_name,
                "job_title": job_title,
            },
            priority="high" if (interview_date - datetime.utcnow()).days <= 1 else "normal",
            category="hiring",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Detalhes",
            created_by=scheduled_by,
        )
    
    async def create_email_sent(
        self,
        recipient_id: str,
        recipient_name: str,
        recipient_type: str,
        email_subject: str,
        email_type: str = "notification",
        sent_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for email sent.
        Type: email (mockup)
        """
        return await self.create_activity(
            activity_type="email_sent",
            title=f"Email Enviado - {email_subject}",
            description=f"{recipient_name} • {email_type.title()}",
            summary=f"Email '{email_subject}' enviado para {recipient_name}",
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="system" if not sent_by else "recruiter",
            target_id=recipient_id,
            target_name=recipient_name,
            target_type=recipient_type,
            extra_data={
                "email_subject": email_subject,
                "email_type": email_type,
            },
            priority="normal",
            category="communication",
            action_url=f"/{recipient_type}s/{recipient_id}",
            action_label="Ver Perfil",
            created_by=sent_by,
        )
    
    async def create_offer_sent(
        self,
        candidate_id: str,
        candidate_name: str,
        job_title: str,
        salary_range: str | None = None,
        sent_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for job offer sent.
        Type: oferta (mockup)
        """
        description = job_title
        if salary_range:
            description += f" • {salary_range}"
        
        return await self.create_activity(
            activity_type="offer_sent",
            title=f"Proposta Enviada - {candidate_name}",
            description=description,
            summary=f"Oferta de {job_title} enviada para {candidate_name}",
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "job_title": job_title,
                "salary_range": salary_range,
            },
            priority="urgent",
            category="hiring",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Proposta",
            created_by=sent_by,
        )
    
    async def create_approval_pending(
        self,
        item_type: str,
        item_id: str,
        item_name: str,
        approval_type: str,
        requested_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for pending approval.
        Type: minha (mockup - user action required)
        """
        return await self.create_activity(
            activity_type="approval_pending",
            title=f"Aprovação Pendente - {approval_type.title()}",
            description=f"{item_name} • Aguardando aprovação",
            summary=f"Aprovação necessária para {item_name}",
            actor_id=requested_by or "system",
            actor_name=requested_by or "Sistema",
            actor_type="recruiter" if requested_by else "system",
            target_id=item_id,
            target_name=item_name,
            target_type=item_type,
            extra_data={
                "approval_type": approval_type,
            },
            priority="high",
            category="hiring",
            action_url=f"/{item_type}s/{item_id}",
            action_label="Revisar e Aprovar",
            created_by=requested_by,
        )
    
    async def create_candidate_moved(
        self,
        candidate_id: str,
        candidate_name: str,
        from_stage: str,
        to_stage: str,
        job_title: str,
        moved_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for candidate pipeline movement.
        Type: ia (if LIA) or minha (if recruiter)
        """
        is_lia = moved_by == "lia"
        
        return await self.create_activity(
            activity_type="candidate_moved",
            title=f"Candidato Movido - {candidate_name}",
            description=f"{job_title} • {from_stage} → {to_stage}",
            summary=f"{candidate_name} movido de {from_stage} para {to_stage}",
            actor_id=moved_by or "system",
            actor_name="LIA" if is_lia else (moved_by or "Sistema"),
            actor_type="ai" if is_lia else ("recruiter" if moved_by else "system"),
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "from_stage": from_stage,
                "to_stage": to_stage,
                "job_title": job_title,
            },
            priority="normal",
            category="screening",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Candidato",
            created_by=moved_by,
        )
    
    async def create_lia_suggestion(
        self,
        suggestion_type: str,
        target_id: str,
        target_name: str,
        target_type: str,
        suggestion_text: str,
        priority: str = "normal",
    ) -> ActivityFeed:
        """
        Create activity for LIA AI suggestion.
        Type: ia (mockup - LIA suggestions)
        """
        return await self.create_activity(
            activity_type="lia_suggestion",
            title=f"Sugestão LIA - {suggestion_type.title()}",
            description=f"{target_name} • {suggestion_text}",
            summary=suggestion_text,
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=target_id,
            target_name=target_name,
            target_type=target_type,
            extra_data={
                "suggestion_type": suggestion_type,
                "suggestion_text": suggestion_text,
            },
            priority=priority,
            category="screening",
            action_url=f"/{target_type}s/{target_id}",
            action_label="Revisar Sugestão",
            created_by="lia",
        )
    
    # ========== CANDIDATE SEARCH ACTIVITIES ==========
    
    async def create_candidate_search_completed(
        self,
        search_query: str,
        local_count: int,
        total_count: int,
        used_global: bool = False,
        credits_consumed: int = 0,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for candidate search completion.
        Type: candidate_search_completed
        """
        source_label = "Banco Proprietário" if not used_global else "Banco Global"
        if used_global and local_count > 0:
            source_label = "Banco Proprietário + Global"
        
        title = "Busca de Candidatos Realizada"
        if used_global:
            description = f"{total_count} candidatos encontrados • {source_label} ({credits_consumed} créditos)"
        else:
            description = f"{total_count} candidatos encontrados • {source_label} (gratuito)"
        
        summary = f"'{search_query}' - {total_count} resultados"
        
        return await self.create_activity(
            activity_type="candidate_search_completed",
            title=title,
            description=description,
            summary=summary,
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=conversation_id,
            target_name=search_query,
            target_type="search",
            extra_data={
                "search_query": search_query,
                "local_count": local_count,
                "total_count": total_count,
                "used_global": used_global,
                "credits_consumed": credits_consumed,
                "source": "global" if used_global else "local",
            },
            priority="normal",
            category="screening",
            action_url=f"/chat/{conversation_id}" if conversation_id else "/chat",
            action_label="Ver Resultados",
            created_by=user_id or "lia",
        )
    
    async def create_global_search_suggested(
        self,
        search_query: str,
        local_count: int,
        estimated_credits: int,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity when LIA suggests global search.
        Type: global_search_suggested
        """
        return await self.create_activity(
            activity_type="global_search_suggested",
            title="LIA Sugeriu Busca Global",
            description=f"Apenas {local_count} candidatos locais • Busca global estimada em {estimated_credits} créditos",
            summary=f"'{search_query}' - Expandir para banco global?",
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=conversation_id,
            target_name=search_query,
            target_type="search",
            extra_data={
                "search_query": search_query,
                "local_count": local_count,
                "estimated_credits": estimated_credits,
            },
            priority="normal",
            category="screening",
            action_url=f"/chat/{conversation_id}" if conversation_id else "/chat",
            action_label="Revisar Sugestão",
            created_by=user_id or "lia",
        )
    
    async def create_global_search_authorized(
        self,
        search_query: str,
        credits_consumed: int,
        results_count: int,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity when user authorizes global search.
        Type: global_search_authorized
        """
        return await self.create_activity(
            activity_type="global_search_authorized",
            title="Busca Global Autorizada",
            description=f"{results_count} candidatos encontrados • {credits_consumed} créditos consumidos",
            summary=f"'{search_query}' - Banco Global ({credits_consumed} créditos)",
            actor_id=user_id or "system",
            actor_name=user_id or "Usuário",
            actor_type="recruiter",
            target_id=conversation_id,
            target_name=search_query,
            target_type="search",
            extra_data={
                "search_query": search_query,
                "credits_consumed": credits_consumed,
                "results_count": results_count,
            },
            priority="normal",
            category="screening",
            action_url=f"/chat/{conversation_id}" if conversation_id else "/chat",
            action_label="Ver Resultados",
            created_by=user_id,
        )
    
    # ========== COMMUNICATION TRACKING ACTIVITIES ==========
    
    async def create_whatsapp_sent(
        self,
        candidate_id: str,
        candidate_name: str,
        message_preview: str,
        sent_by: str | None = None,
        job_title: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for WhatsApp message sent to candidate.
        Type: whatsapp_sent
        """
        description = f"{candidate_name} • WhatsApp"
        if job_title:
            description = f"{job_title} • {candidate_name}"
        
        return await self.create_activity(
            activity_type="whatsapp_sent",
            title=f"WhatsApp Enviado - {candidate_name}",
            description=description,
            summary=message_preview[:100] + "..." if len(message_preview) > 100 else message_preview,
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "message_preview": message_preview,
                "job_title": job_title,
                "channel": "whatsapp",
            },
            priority="normal",
            category="communication",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Candidato",
            created_by=sent_by,
        )
    
    async def create_triagem_invite_sent(
        self,
        candidate_id: str,
        candidate_name: str,
        channel: str,
        job_title: str,
        sent_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for screening invitation sent.
        Type: triagem_invite_sent
        Channel: 'email' | 'whatsapp'
        """
        channel_label = "Email" if channel == "email" else "WhatsApp"
        
        return await self.create_activity(
            activity_type="triagem_invite_sent",
            title=f"Convite de Triagem Enviado - {candidate_name}",
            description=f"{job_title} • via {channel_label}",
            summary=f"Convite para triagem de {job_title} enviado via {channel_label}",
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "job_title": job_title,
                "channel": channel,
            },
            priority="normal",
            category="screening",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Candidato",
            created_by=sent_by,
        )
    
    async def create_agendamento_invite_sent(
        self,
        candidate_id: str,
        candidate_name: str,
        channel: str,
        job_title: str,
        interview_type: str,
        sent_by: str | None = None,
        interview_date: datetime | None = None,
    ) -> ActivityFeed:
        """
        Create activity for interview scheduling invitation sent.
        Type: agendamento_invite_sent
        Priority: "high" if interview date is within 2 days, otherwise "normal"
        """
        channel_label = "Email" if channel == "email" else "WhatsApp"
        
        description = f"{job_title} • {interview_type.title()} via {channel_label}"
        summary = f"Convite para agendamento de entrevista ({interview_type}) enviado via {channel_label}"
        
        if interview_date:
            description += f" • {interview_date.strftime('%d/%m às %H:%M')}"
            summary = f"Entrevista {interview_type} agendada para {interview_date.strftime('%d/%m às %H:%M')}"
        
        priority = "normal"
        if interview_date:
            days_until = (interview_date - datetime.utcnow()).days
            if days_until <= 2:
                priority = "high"
        
        return await self.create_activity(
            activity_type="agendamento_invite_sent",
            title=f"Convite de Agendamento Enviado - {candidate_name}",
            description=description,
            summary=summary,
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "job_title": job_title,
                "channel": channel,
                "interview_type": interview_type,
                "interview_date": interview_date.isoformat() if interview_date else None,
            },
            priority=priority,
            category="hiring",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Agendamento",
            created_by=sent_by,
        )
    
    async def create_feedback_sent(
        self,
        candidate_id: str,
        candidate_name: str,
        feedback_type: str,
        job_title: str,
        sent_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for feedback message sent.
        Type: feedback_sent
        Feedback types: 'positivo' | 'construtivo' | 'outro'
        """
        feedback_labels = {
            "positivo": "Positivo",
            "construtivo": "Construtivo",
            "outro": "Outro",
        }
        feedback_label = feedback_labels.get(feedback_type, feedback_type.title())
        
        return await self.create_activity(
            activity_type="feedback_sent",
            title=f"Feedback Enviado - {candidate_name}",
            description=f"{job_title} • Feedback {feedback_label}",
            summary=f"Feedback {feedback_label.lower()} enviado para {candidate_name}",
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "job_title": job_title,
                "feedback_type": feedback_type,
            },
            priority="normal",
            category="communication",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Candidato",
            created_by=sent_by,
        )
    
    async def create_communication_logged(
        self,
        candidate_id: str,
        candidate_name: str,
        communication_type: str,
        channel: str,
        sent_by: str | None = None,
        subject: str | None = None,
        job_title: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> ActivityFeed:
        """
        Create activity for generic communication logging.
        Type: communication_logged
        Use this for any communication that doesn't fit other specific types.
        """
        channel_label = channel.title() if channel else "Desconhecido"
        type_label = communication_type.replace("_", " ").title()
        
        description = f"{type_label} via {channel_label}"
        if job_title:
            description = f"{job_title} • {description}"
        
        summary = f"{type_label} enviado para {candidate_name}"
        if subject:
            summary = f"{subject} - {candidate_name}"
        
        activity_extra_data = {
            "communication_type": communication_type,
            "channel": channel,
            "subject": subject,
            "job_title": job_title,
        }
        if extra_data:
            activity_extra_data.update(extra_data)
        
        return await self.create_activity(
            activity_type="communication_logged",
            title=f"Comunicação Registrada - {candidate_name}",
            description=description,
            summary=summary,
            actor_id=sent_by or "system",
            actor_name=sent_by or "Sistema",
            actor_type="recruiter" if sent_by else "system",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data=activity_extra_data,
            priority="normal",
            category="communication",
            action_url=f"/candidates/{candidate_id}",
            action_label="Ver Candidato",
            created_by=sent_by,
        )
    
    async def create_rubric_evaluation_activity(
        self,
        candidate_id: str,
        candidate_name: str,
        job_id: str,
        job_title: str,
        job_code: str | None = None,
        score: float = 0.0,
        score_label: str = "Não Avaliado",
        evaluations: list[dict[str, Any]] | None = None,
        summary: str | None = None,
        recommendation: str = "review",
        strengths: list[str] | None = None,
        concerns: list[str] | None = None,
        created_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for rubric evaluation (CV vs Job analysis).
        Type: rubric_evaluation
        
        This activity tracks when a candidate's CV is evaluated against job requirements
        using the structured rubric methodology (BARS).
        
        Args:
            candidate_id: ID of the candidate being evaluated
            candidate_name: Name of the candidate
            job_id: ID of the job vacancy
            job_title: Title of the job vacancy
            job_code: Optional job code/reference
            score: Evaluation score (0-100)
            score_label: Human-readable score label (Forte, Médio, Fraco, etc.)
            evaluations: List of individual requirement evaluations
            summary: Brief summary of the evaluation
            recommendation: Recommended action (interview, review, reject)
            strengths: List of identified strengths
            concerns: List of identified concerns
            created_by: ID of who triggered the evaluation
            
        Returns:
            Created ActivityFeed instance
        """
        description = f"{job_title}"
        if job_code:
            description = f"{job_code} • {job_title}"
        description += f" • Score: {score:.0f}%"
        
        if not summary:
            if score >= 85:
                summary = f"Candidato altamente recomendado para {job_title}. Score: {score:.0f}%"
            elif score >= 70:
                summary = f"Candidato recomendado para {job_title}. Score: {score:.0f}%"
            elif score >= 55:
                summary = f"Candidato com potencial para {job_title}. Score: {score:.0f}%"
            else:
                summary = f"Baixo match com {job_title}. Score: {score:.0f}%"
        
        priority = "normal"
        if score >= 85:
            priority = "urgent"
        elif score >= 70:
            priority = "normal"
        else:
            priority = "low"
        
        return await self.create_activity(
            activity_type="rubric_evaluation",
            title=f"Análise CV vs Vaga: {job_title}",
            description=description,
            summary=summary,
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "job_id": job_id,
                "job_title": job_title,
                "job_code": job_code,
                "score": score,
                "score_label": score_label,
                "evaluations": evaluations or [],
                "summary": summary,
                "recommendation": recommendation,
                "strengths": strengths or [],
                "concerns": concerns or [],
            },
            priority=priority,
            category="screening",
            action_url=f"/vagas/{job_id}/candidatos/{candidate_id}",
            action_label="Ver Análise Completa",
            created_by=created_by or "lia",
        )
    
    async def create_screening_analysis_activity(
        self,
        candidate_id: str,
        candidate_name: str,
        analysis_type: str = "curricular",
        overall_score: float = 0.0,
        experience_quality: str | None = None,
        career_trajectory: str | None = None,
        red_flags: list[str] | None = None,
        green_flags: list[str] | None = None,
        experience_gaps: list[dict[str, Any]] | None = None,
        education_analysis: dict[str, Any] | None = None,
        skills_analysis: dict[str, Any] | None = None,
        recommendation: str = "review",
        summary: str | None = None,
        detailed_reasoning: str | None = None,
        created_by: str | None = None,
    ) -> ActivityFeed:
        """
        Create activity for detailed screening analysis (independent of job).
        Type: screening_analysis
        
        This activity tracks when a candidate's profile is analyzed in detail,
        independent of a specific job vacancy. It focuses on overall profile quality,
        career patterns, red flags, and general employability assessment.
        
        Args:
            candidate_id: ID of the candidate being analyzed
            candidate_name: Name of the candidate
            analysis_type: Type of analysis (curricular, behavioral, technical)
            overall_score: Overall profile quality score (0-100)
            experience_quality: Quality assessment of work experience
            career_trajectory: Pattern analysis of career progression
            red_flags: List of identified concerns or risks
            green_flags: List of positive indicators
            experience_gaps: List of employment gaps with details
            education_analysis: Education quality and relevance assessment
            skills_analysis: Skills depth and relevance assessment
            recommendation: Recommended action (advance, review, reject)
            summary: Brief summary of the analysis
            detailed_reasoning: Full reasoning behind the analysis
            created_by: ID of who triggered the analysis
            
        Returns:
            Created ActivityFeed instance
        """
        analysis_type_labels = {
            "curricular": "Curricular",
            "behavioral": "Comportamental",
            "technical": "Técnica",
        }
        type_label = analysis_type_labels.get(analysis_type, "Detalhada")
        
        clamped_score = max(0.0, min(100.0, overall_score or 0.0))
        
        if clamped_score >= 85:
            score_label = "Excelente"
            priority = "urgent"
        elif clamped_score >= 70:
            score_label = "Bom"
            priority = "normal"
        elif clamped_score >= 55:
            score_label = "Regular"
            priority = "normal"
        else:
            score_label = "Fraco"
            priority = "low"
        
        description = f"Análise {type_label} • Score: {clamped_score:.0f}% ({score_label})"
        
        if not summary:
            red_flag_count = len(red_flags) if red_flags else 0
            green_flag_count = len(green_flags) if green_flags else 0
            
            if red_flag_count == 0 and clamped_score >= 70:
                summary = f"Perfil de alta qualidade. Score: {clamped_score:.0f}%"
            elif red_flag_count > 2:
                summary = f"Atenção: {red_flag_count} pontos de atenção identificados. Score: {clamped_score:.0f}%"
            else:
                summary = f"Análise concluída. {green_flag_count} pontos positivos, {red_flag_count} pontos de atenção."
        
        return await self.create_activity(
            activity_type="screening_analysis",
            title=f"Análise de Triagem {type_label}: {candidate_name}",
            description=description,
            summary=summary,
            actor_id="lia",
            actor_name="LIA",
            actor_type="ai",
            target_id=candidate_id,
            target_name=candidate_name,
            target_type="candidate",
            extra_data={
                "analysis_type": analysis_type,
                "overall_score": clamped_score,
                "score_label": score_label,
                "experience_quality": experience_quality,
                "career_trajectory": career_trajectory,
                "red_flags": red_flags or [],
                "green_flags": green_flags or [],
                "experience_gaps": experience_gaps or [],
                "education_analysis": education_analysis or {},
                "skills_analysis": skills_analysis or {},
                "recommendation": recommendation,
                "summary": summary,
                "detailed_reasoning": detailed_reasoning,
            },
            priority=priority,
            category="screening",
            action_url=f"/funil-de-talentos/candidato/{candidate_id}",
            action_label="Ver Análise Completa",
            created_by=created_by or "lia",
        )


activity_service = ActivityService()

# FastAPI dependency injection factory
def get_activity_service() -> "ActivityService":
    return activity_service

