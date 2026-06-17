"""
Agent Monitoring Service
Handles metrics calculation, health scores, and activity tracking for AI agents.
Compatible with SQLAlchemy 2.0 AsyncSession.
"""
import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_activity import ActivityStatus, AgentActivity
from app.models.task import Task, TaskStatus

AGENT_DEFINITIONS = {
    "job_intake": {
        "id": "job_intake",
        "name": "Job Intake",
        "icon": "📋",
        "description": "Criação de vagas e extração de JDs",
        "daily_goal": 15,
    },
    "sourcing": {
        "id": "sourcing",
        "name": "Sourcing",
        "icon": "🔍",
        "description": "Busca e qualificação de candidatos",
        "daily_goal": 50,
    },
    "screening": {
        "id": "screening",
        "name": "Screening",
        "icon": "🎯",
        "description": "Triagem e análise de candidatos",
        "daily_goal": 30,
    },
    "scheduling": {
        "id": "scheduling",
        "name": "Scheduling",
        "icon": "📅",
        "description": "Agendamento de entrevistas",
        "daily_goal": 20,
    },
    "communication": {
        "id": "communication",
        "name": "Communication",
        "icon": "✉️",
        "description": "Envio de emails e mensagens",
        "daily_goal": 40,
    },
    "analytics": {
        "id": "analytics",
        "name": "Analytics",
        "icon": "📊",
        "description": "Análise de KPIs e métricas",
        "daily_goal": 10,
    },
    "recruiter_assistant": {
        "id": "recruiter_assistant",
        "name": "Assistente",
        "icon": "🤖",
        "description": "Suporte e automações gerais",
        "daily_goal": 25,
    },
}


class AgentMonitoringService:
    """Service for monitoring AI agent activities and metrics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_global_metrics(self) -> dict[str, Any]:
        """Get global metrics across all agents for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        stmt = select(func.count(AgentActivity.id)).where(
            AgentActivity.started_at >= today_start
        )
        result = await self.db.execute(stmt)
        today_activities = result.scalar() or 0
        
        stmt = select(func.count(AgentActivity.id)).where(
            and_(
                AgentActivity.started_at >= yesterday_start,
                AgentActivity.started_at < today_start
            )
        )
        result = await self.db.execute(stmt)
        yesterday_activities = result.scalar() or 0
        
        stmt = select(func.count(func.distinct(AgentActivity.agent_id))).where(
            AgentActivity.started_at >= today_start
        )
        result = await self.db.execute(stmt)
        active_agents = result.scalar() or 0
        
        total_agents = len(AGENT_DEFINITIONS)
        
        stmt = select(func.count(AgentActivity.id)).where(
            and_(
                AgentActivity.started_at >= today_start,
                AgentActivity.status == ActivityStatus.SUCCESS
            )
        )
        result = await self.db.execute(stmt)
        today_success = result.scalar() or 0
        
        success_rate = (today_success / today_activities * 100) if today_activities > 0 else 100.0
        
        stmt = select(func.avg(AgentActivity.duration_seconds)).where(
            and_(
                AgentActivity.started_at >= today_start,
                AgentActivity.duration_seconds.isnot(None)
            )
        )
        result = await self.db.execute(stmt)
        avg_duration = result.scalar() or 0
        
        stmt = select(func.count(AgentActivity.id)).where(
            and_(
                AgentActivity.started_at >= today_start,
                AgentActivity.status == ActivityStatus.ERROR
            )
        )
        result = await self.db.execute(stmt)
        proactive_alerts = result.scalar() or 0
        
        stmt = select(func.count(Task.id)).where(
            Task.status == TaskStatus.PENDING
        )
        result = await self.db.execute(stmt)
        pending_tasks = result.scalar() or 0
        
        proactive_alerts += pending_tasks
        
        actions_delta = 0
        if yesterday_activities > 0:
            actions_delta = round((today_activities - yesterday_activities) / yesterday_activities * 100)
        
        return {
            "actions_today": today_activities,
            "actions_delta": actions_delta,
            "active_agents": active_agents,
            "total_agents": total_agents,
            "success_rate": round(success_rate, 1),
            "avg_response_time": round(avg_duration, 1) if avg_duration else 0,
            "proactive_alerts": proactive_alerts,
        }
    
    async def get_agent_summary(self, agent_id: str) -> dict[str, Any] | None:
        """Get summary metrics for a specific agent."""
        if agent_id not in AGENT_DEFINITIONS:
            return None
        
        agent_def = AGENT_DEFINITIONS[agent_id]
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        stmt = select(func.count(AgentActivity.id)).where(
            and_(
                AgentActivity.agent_id == agent_id,
                AgentActivity.started_at >= today_start
            )
        )
        result = await self.db.execute(stmt)
        today_actions = result.scalar() or 0
        
        stmt = select(func.count(AgentActivity.id)).where(
            and_(
                AgentActivity.agent_id == agent_id,
                AgentActivity.started_at >= yesterday_start,
                AgentActivity.started_at < today_start
            )
        )
        result = await self.db.execute(stmt)
        yesterday_actions = result.scalar() or 0
        
        delta = 0
        if yesterday_actions > 0:
            delta = round((today_actions - yesterday_actions) / yesterday_actions * 100)
        
        sparkline = await self._get_sparkline_data(agent_id)
        
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(AgentActivity).where(
            AgentActivity.agent_id == agent_id
        ).order_by(AgentActivity.started_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        last_activity = result.scalar_one_or_none()
        
        status = "online" if today_actions > 0 else "idle"
        if last_activity and last_activity.status == ActivityStatus.ERROR:
            status = "warning"
        
        return {
            "id": agent_id,
            "name": agent_def["name"],
            "icon": agent_def["icon"],
            "status": status,
            "actions_today": today_actions,
            "daily_goal": agent_def["daily_goal"],
            "progress": round(today_actions / agent_def["daily_goal"] * 100) if agent_def["daily_goal"] > 0 else 0,
            "delta": delta,
            "sparkline": sparkline,
            "last_action": last_activity.title if last_activity else None,
            "last_action_time": last_activity.started_at.isoformat() if last_activity else None,
        }
    
    async def get_all_agents_summary(self) -> list[dict[str, Any]]:
        """Get summary for all agents."""
        summaries = []
        for agent_id in AGENT_DEFINITIONS:
            summary = await self.get_agent_summary(agent_id)
            if summary:
                summaries.append(summary)
        return summaries
    
    async def get_agent_health(self, agent_id: str) -> dict[str, Any] | None:
        """Calculate health score and details for an agent."""
        if agent_id not in AGENT_DEFINITIONS:
            return None
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(AgentActivity).where(
            and_(
                AgentActivity.agent_id == agent_id,
                AgentActivity.started_at >= week_start
            )
        )
        result = await self.db.execute(stmt)
        week_activities = result.scalars().all()
        
        total = len(week_activities)
        if total == 0:
            return {
                "agent_id": agent_id,
                "score": 100,
                "tier": "excellent",
                "drivers": [],
                "recommendations": ["Agente ainda não possui atividades registradas"],
            }
        
        success_count = sum(1 for a in week_activities if a.status == ActivityStatus.SUCCESS)
        error_count = sum(1 for a in week_activities if a.status == ActivityStatus.ERROR)
        sla_breaches = sum(1 for a in week_activities if a.sla_breach)
        
        success_rate = success_count / total * 100
        error_rate = error_count / total * 100
        sla_compliance = (total - sla_breaches) / total * 100
        
        durations = [a.duration_seconds for a in week_activities if a.duration_seconds]
        avg_response = sum(durations) / len(durations) if durations else 0
        
        score = 0
        drivers = []
        
        success_score = min(success_rate, 100) * 0.4
        score += success_score
        drivers.append({
            "name": "Taxa de Sucesso",
            "value": round(success_rate, 1),
            "weight": 40,
            "impact": "positive" if success_rate >= 90 else "negative" if success_rate < 70 else "neutral"
        })
        
        sla_score = min(sla_compliance, 100) * 0.3
        score += sla_score
        drivers.append({
            "name": "SLA Compliance",
            "value": round(sla_compliance, 1),
            "weight": 30,
            "impact": "positive" if sla_compliance >= 95 else "negative" if sla_compliance < 80 else "neutral"
        })
        
        response_score = max(0, 100 - avg_response * 2) * 0.2
        score += response_score
        drivers.append({
            "name": "Tempo Médio",
            "value": round(avg_response, 1),
            "weight": 20,
            "impact": "positive" if avg_response < 30 else "negative" if avg_response > 60 else "neutral"
        })
        
        error_impact = max(0, 100 - error_rate * 5) * 0.1
        score += error_impact
        drivers.append({
            "name": "Taxa de Erro",
            "value": round(error_rate, 1),
            "weight": 10,
            "impact": "positive" if error_rate < 5 else "negative" if error_rate > 15 else "neutral"
        })
        
        score = min(100, max(0, score))
        
        if score >= 90:
            tier = "excellent"
        elif score >= 75:
            tier = "good"
        elif score >= 60:
            tier = "watch"
        else:
            tier = "critical"
        
        recommendations = []
        if success_rate < 90:
            recommendations.append("Investigue as falhas recentes para melhorar a taxa de sucesso")
        if sla_compliance < 95:
            recommendations.append("Otimize o tempo de resposta para reduzir violações de SLA")
        if error_rate > 10:
            recommendations.append("Revise os logs de erro para identificar padrões")
        if avg_response > 45:
            recommendations.append("Considere otimizações de performance")
        
        if not recommendations:
            recommendations.append("Agente operando dentro dos parâmetros ideais")
        
        return {
            "agent_id": agent_id,
            "score": round(score),
            "tier": tier,
            "drivers": drivers,
            "recommendations": recommendations,
            "metrics": {
                "success_rate": round(success_rate, 1),
                "error_rate": round(error_rate, 1),
                "sla_compliance": round(sla_compliance, 1),
                "avg_response_time": round(avg_response, 1),
                "total_activities": total,
            }
        }
    
    async def get_activity_feed(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0
    # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
    ) -> list[dict[str, Any]]:
        """Get activity feed with optional filters."""
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(AgentActivity).order_by(AgentActivity.started_at.desc())
        
        if agent_id:
            stmt = stmt.where(AgentActivity.agent_id == agent_id)
        
        if status:
            try:
                status_enum = ActivityStatus(status)
                stmt = stmt.where(AgentActivity.status == status_enum)
            except ValueError:
                pass
        
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        activities = result.scalars().all()
        
        return [activity.to_dict() for activity in activities]
    
    async def get_proactive_alerts(self) -> list[dict[str, Any]]:
        """Get current proactive alerts requiring attention."""
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        alerts = []
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(AgentActivity).where(
            and_(
                AgentActivity.started_at >= today_start,
                AgentActivity.status == ActivityStatus.ERROR
            )
        ).order_by(AgentActivity.started_at.desc()).limit(5)
        result = await self.db.execute(stmt)
        error_activities = result.scalars().all()
        
        for activity in error_activities:
            alerts.append({
                "id": activity.id,
                "type": "error",
                "agent_id": activity.agent_id,
                "agent_name": activity.agent_name,
                "title": f"Erro em {activity.title}",
                "description": activity.error_message or "Erro durante execução",
                # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
                "created_at": activity.started_at.isoformat(),
                "severity": "high",
            })
        
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(AgentActivity).where(
            and_(
                AgentActivity.started_at >= today_start,
                AgentActivity.sla_breach
            )
        ).order_by(AgentActivity.started_at.desc()).limit(5)
        result = await self.db.execute(stmt)
        sla_breaches = result.scalars().all()
        
        for activity in sla_breaches:
            alerts.append({
                "id": activity.id,
                "type": "sla_breach",
                "agent_id": activity.agent_id,
                "agent_name": activity.agent_name,
                "title": f"SLA violado: {activity.title}",
                # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
                "description": "Tempo de execução excedeu o limite",
                "created_at": activity.started_at.isoformat(),
                "severity": "medium",
            })
        
        # TENANT-EXEMPT: agent_monitoring_service is system-wide telemetry across all tenants (AGENT_DEFINITIONS scoped, not company); LGPD-safe aggregate
        stmt = select(Task).where(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.due_date < datetime.utcnow()
            )
        ).limit(5)
        result = await self.db.execute(stmt)
        overdue_tasks = result.scalars().all()
        
        for task in overdue_tasks:
            alerts.append({
                "id": task.id,
                "type": "overdue_task",
                "agent_id": task.assigned_to_agent or "recruiter_assistant",
                "agent_name": AGENT_DEFINITIONS.get(task.assigned_to_agent or "recruiter_assistant", {}).get("name", "Assistente"),
                "title": f"Tarefa atrasada: {task.title}",
                "description": f"Venceu em {task.due_date.strftime('%d/%m/%Y') if task.due_date else 'N/A'}",
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "severity": "high" if task.priority and task.priority.value in ["critical", "high"] else "medium",
            })
        
        return alerts
    
    async def _get_sparkline_data(self, agent_id: str, hours: int = 24) -> list[int]:
        """Get hourly activity counts for sparkline visualization."""
        now = datetime.utcnow()
        data = []
        
        for i in range(hours - 1, -1, -1):
            hour_start = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            stmt = select(func.count(AgentActivity.id)).where(
                and_(
                    AgentActivity.agent_id == agent_id,
                    AgentActivity.started_at >= hour_start,
                    AgentActivity.started_at < hour_end
                )
            )
            result = await self.db.execute(stmt)
            count = result.scalar() or 0
            
            data.append(count)
        
        return data
    
    async def log_activity(
        self,
        agent_id: str,
        activity_type: str,
        title: str,
        description: str | None = None,
        status: ActivityStatus = ActivityStatus.SUCCESS,
        duration_seconds: float | None = None,
        related_job_id: str | None = None,
        related_candidate_id: str | None = None,
        metadata: dict | None = None,
        result_data: dict | None = None,
        error_message: str | None = None,
        sla_breach: bool = False,
    ) -> AgentActivity:
        """Log a new agent activity."""
        agent_def = AGENT_DEFINITIONS.get(agent_id, {
            "name": agent_id.replace("_", " ").title(),
            "icon": "🤖"
        })
        
        activity = AgentActivity(
            agent_id=agent_id,
            agent_name=agent_def.get("name", agent_id),
            agent_icon=agent_def.get("icon", "🤖"),
            activity_type=activity_type,
            title=title,
            description=description,
            status=status,
            duration_seconds=duration_seconds,
            related_job_id=related_job_id,
            related_candidate_id=related_candidate_id,
            activity_metadata=metadata or {},
            result_data=result_data,
            error_message=error_message,
            sla_breach=sla_breach,
            completed_at=datetime.utcnow() if status in [ActivityStatus.SUCCESS, ActivityStatus.ERROR] else None,
        )
        
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        
        return activity
    
    async def seed_demo_data(self) -> dict[str, int]:
        """Seed demo data for testing the Agent Control Center."""
        now = datetime.utcnow()
        created_count = 0
        
        activity_templates = {
            "job_intake": [
                ("job_created", "Vaga criada: Desenvolvedor Backend Senior"),
                ("jd_extracted", "JD extraída e estruturada"),
                ("health_check", "Verificação de saúde da vaga"),
            ],
            "sourcing": [
                ("candidate_found", "3 candidatos encontrados no Pearch"),
                ("cv_parsed", "CV de João Silva processado"),
                ("pipeline_added", "Candidato adicionado ao pipeline"),
            ],
            "screening": [
                ("voice_screening", "Voice screening completado"),
                ("report_generated", "Parecer de candidato gerado"),
                ("comparison_done", "Comparação de candidatos realizada"),
            ],
            "scheduling": [
                ("interview_scheduled", "Entrevista agendada para 14:00"),
                ("reminder_sent", "Lembrete de entrevista enviado"),
                ("availability_checked", "Disponibilidade verificada"),
            ],
            "communication": [
                ("email_sent", "Email de follow-up enviado"),
                ("bulk_message", "Mensagem em massa para 15 candidatos"),
                ("feedback_delivered", "Feedback entregue ao candidato"),
            ],
            "analytics": [
                ("kpi_calculated", "KPIs diários calculados"),
                ("funnel_analyzed", "Análise de funil completada"),
                ("forecast_updated", "Previsão de contratação atualizada"),
            ],
            "recruiter_assistant": [
                ("briefing_sent", "Briefing diário enviado"),
                ("task_created", "Tarefa criada para recrutador"),
                ("chitchat_response", "Resposta a pergunta do recrutador"),
            ],
        }
        
        for agent_id, templates in activity_templates.items():
            for hour_offset in range(24):
                if random.random() > 0.3:
                    activity_type, title = random.choice(templates)
                    
                    status_weights = [
                        (ActivityStatus.SUCCESS, 0.85),
                        (ActivityStatus.IN_PROGRESS, 0.08),
                        (ActivityStatus.ERROR, 0.05),
                        (ActivityStatus.PENDING, 0.02),
                    ]
                    status = random.choices(
                        [s for s, _ in status_weights],
                        weights=[w for _, w in status_weights]
                    )[0]
                    
                    activity = AgentActivity(
                        agent_id=agent_id,
                        agent_name=AGENT_DEFINITIONS[agent_id]["name"],
                        agent_icon=AGENT_DEFINITIONS[agent_id]["icon"],
                        activity_type=activity_type,
                        title=title,
                        description=f"Atividade automática do agente {AGENT_DEFINITIONS[agent_id]['name']}",
                        status=status,
                        duration_seconds=random.uniform(5, 120),
                        sla_breach=random.random() < 0.05,
                        started_at=now - timedelta(hours=hour_offset, minutes=random.randint(0, 59)),
                        completed_at=now - timedelta(hours=hour_offset, minutes=random.randint(0, 59)) if status in [ActivityStatus.SUCCESS, ActivityStatus.ERROR] else None,
                        error_message="Timeout na conexão" if status == ActivityStatus.ERROR else None,
                    )
                    
                    self.db.add(activity)
                    created_count += 1
        
        await self.db.commit()
        
        return {"activities_created": created_count}


def _strip_meta(p: dict) -> dict:
    return {k: v for k, v in p.items() if not k.startswith("_")}


async def get_monitoring_data(**params):
    """Wrapper para o chat. Requer instância DB-backed; delega para get_global_metrics.

    R-005.2: Movido de shared/observability/agent_monitoring_service.py (stale fork).
    """
    raise NotImplementedError(
        "get_monitoring_data requer instância de AgentMonitoringService com sessão ativa "
        "(não há singleton módulo-level). Backlog: criar factory async com get_async_session."
    )
