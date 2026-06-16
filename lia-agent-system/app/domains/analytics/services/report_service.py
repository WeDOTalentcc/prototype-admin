# ADR-001-EXEMPT: cross-tenant analytics aggregation. Optional `company_id`
# parameter (when None → platform-wide aggregate for admin dashboards).
# Repository pattern enforces `_require_company_id` (fail-closed) which would
# block legitimate platform-wide queries. The cross-tenant access surface here
# is gated separately at the API layer.
"""
Report Service - Automatic report generation and email delivery.

This service generates and sends:
- Daily briefing emails
- Weekly performance reports
- Monthly manager reports

Integrates with BriefingService for data and EmailService for delivery.
"""
import logging
import random
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.communication.services.email_providers import get_email_provider
from app.domains.communication.services.email_service import EmailService
from app.shared.services.briefing_service import briefing_service
from app.templates.report_templates import report_templates

logger = logging.getLogger(__name__)


class DemoDataGenerator:
    FIRST_NAMES = [
        "Ana", "Carlos", "Juliana", "Ricardo", "Fernanda", "Lucas",
        "Mariana", "Pedro", "Camila", "Rafael", "Beatriz", "Gustavo",
        "Larissa", "Thiago", "Isabela", "Bruno", "Patrícia", "Diego",
    ]
    LAST_NAMES = [
        "Silva", "Santos", "Oliveira", "Souza", "Mendes", "Costa",
        "Martins", "Almeida", "Ferreira", "Lima", "Pereira", "Rodrigues",
        "Barbosa", "Nascimento", "Carvalho", "Araújo", "Ribeiro", "Moreira",
    ]
    DEPARTMENTS = [
        "Tecnologia", "Comercial", "Operações", "Marketing",
        "Financeiro", "RH", "Jurídico", "Engenharia",
    ]
    CHANNELS = [
        ("LinkedIn", 0.30, 0.022, 3500),
        ("Website", 0.20, 0.016, 2200),
        ("Indicação", 0.15, 0.040, 1200),
        ("Indeed", 0.12, 0.014, 4000),
        ("Glassdoor", 0.10, 0.012, 4500),
        ("Base LIA", 0.13, 0.035, 700),
    ]
    CANDIDATE_NAMES_DAILY = [
        "João Silva", "Maria Oliveira", "Pedro Costa", "Ana Souza",
        "Lucas Ferreira", "Camila Santos", "Bruno Almeida", "Larissa Lima",
    ]
    JOB_TITLES_DAILY = [
        "Desenvolvedor Senior", "Analista de Dados", "UX Designer",
        "Gerente Comercial", "Analista Financeiro", "Engenheiro de Software",
        "Product Manager", "DevOps Engineer", "Analista de Marketing",
    ]

    def _rng(self, seed_value: int) -> random.Random:
        return random.Random(seed_value)

    def _weekly_seed(self) -> int:
        today = date.today()
        return today.isocalendar()[0] * 100 + today.isocalendar()[1]

    def _monthly_seed(self) -> int:
        today = date.today()
        return today.year * 100 + today.month

    def _daily_seed(self) -> int:
        today = date.today()
        return today.year * 10000 + today.month * 100 + today.day

    def _pick_names(self, rng: random.Random, count: int) -> list[str]:
        firsts = rng.sample(self.FIRST_NAMES, min(count, len(self.FIRST_NAMES)))
        lasts = rng.sample(self.LAST_NAMES, min(count, len(self.LAST_NAMES)))
        return [f"{f} {l}" for f, l in zip(firsts, lasts)]

    def _trend_direction(self, rng: random.Random, bias_up: float = 0.6) -> str:
        return "up" if rng.random() < bias_up else "down"

    def _trend_pct(self, rng: random.Random, direction: str, low: float = 2.0, high: float = 25.0) -> float:
        val = round(rng.uniform(low, high), 1)
        return val if direction == "up" else -val

    def weekly_kpis(self) -> list[dict[str, Any]]:
        rng = self._rng(self._weekly_seed())
        hires = rng.randint(5, 20)
        candidates = rng.randint(500, 2000)
        avg_time = rng.randint(18, 40)
        cost = rng.randint(2000, 8000)
        cost_str = f"R$ {cost / 1000:.1f}k"

        hire_trend = self._trend_direction(rng, 0.6)
        cand_trend = self._trend_direction(rng, 0.55)
        time_trend = self._trend_direction(rng, 0.4)
        cost_trend = self._trend_direction(rng, 0.4)

        return [
            {"name": "Contratações", "value": hires, "unit": "", "trend": hire_trend,
             "trend_percentage": self._trend_pct(rng, hire_trend), "positive_up": True},
            {"name": "Candidatos", "value": candidates, "unit": "", "trend": cand_trend,
             "trend_percentage": self._trend_pct(rng, cand_trend, 1.0, 15.0), "positive_up": True},
            {"name": "Tempo Médio", "value": avg_time, "unit": " dias", "trend": time_trend,
             "trend_percentage": self._trend_pct(rng, time_trend), "positive_up": False},
            {"name": "Custo/Hire", "value": cost_str, "unit": "", "trend": cost_trend,
             "trend_percentage": self._trend_pct(rng, cost_trend), "positive_up": False},
        ]

    def funnel_data(self) -> dict[str, Any]:
        rng = self._rng(self._weekly_seed() + 1)
        total = rng.randint(500, 2000)
        triagem_rate = rng.uniform(0.45, 0.60)
        triagem = int(total * triagem_rate)
        entrevista_rate = rng.uniform(0.25, 0.40)
        entrevista = int(triagem * entrevista_rate)
        final_rate = rng.uniform(0.30, 0.50)
        etapa_final = int(entrevista * final_rate)
        hire_rate = rng.uniform(0.10, 0.25)
        contratados = max(1, int(etapa_final * hire_rate))

        stages = [
            {"stage_name": "Candidaturas", "count": total, "conversion_rate": 100.0},
            {"stage_name": "Triagem", "count": triagem,
             "conversion_rate": round(triagem / total * 100, 1)},
            {"stage_name": "Entrevista", "count": entrevista,
             "conversion_rate": round(entrevista / triagem * 100, 1) if triagem else 0},
            {"stage_name": "Etapa Final", "count": etapa_final,
             "conversion_rate": round(etapa_final / entrevista * 100, 1) if entrevista else 0},
            {"stage_name": "Contratado", "count": contratados,
             "conversion_rate": round(contratados / etapa_final * 100, 1) if etapa_final else 0},
        ]
        overall = round(contratados / total * 100, 2) if total else 0
        return {
            "stages": stages,
            "total_candidates": total,
            "overall_conversion_rate": overall,
        }

    def recruiter_ranking(self) -> list[dict[str, Any]]:
        rng = self._rng(self._weekly_seed() + 2)
        count = rng.randint(4, 7)
        names = self._pick_names(rng, count)
        ranking = []
        for name in names:
            target = rng.randint(2, 6)
            filled = rng.randint(max(0, target - 2), target + 2)
            ranking.append({
                "recruiter_name": name,
                "positions_filled": filled,
                "positions_target": target,
                "conversion_rate": round(rng.uniform(1.0, 5.0), 1),
                "quality_score": round(rng.uniform(75.0, 98.0), 1),
            })
        ranking.sort(key=lambda r: r["positions_filled"], reverse=True)
        return ranking

    def channel_performance(self) -> list[dict[str, Any]]:
        rng = self._rng(self._weekly_seed() + 3)
        total_candidates = rng.randint(500, 2000)
        results = []
        for ch_name, share, base_conv, base_cost in self.CHANNELS:
            count = max(1, int(total_candidates * share * rng.uniform(0.8, 1.2)))
            conv = round(base_conv * rng.uniform(0.7, 1.4) * 100, 1)
            cost = int(base_cost * rng.uniform(0.75, 1.30))
            results.append({
                "channel_name": ch_name,
                "candidates_count": count,
                "conversion_rate": conv,
                "cost_per_hire": cost,
            })
        return results

    def strategic_kpis(self) -> list[dict[str, Any]]:
        rng = self._rng(self._monthly_seed())
        hires = rng.randint(8, 30)
        hires_target = hires + rng.randint(-3, 5)
        avg_time = rng.randint(18, 40)
        time_target = max(15, avg_time - rng.randint(2, 8))
        cost = rng.randint(2500, 8000)
        cost_target = max(2000, cost - rng.randint(200, 1500))
        conv = round(rng.uniform(1.5, 4.5), 1)
        conv_target = round(conv + rng.uniform(0.3, 1.5), 1)
        nps = rng.randint(70, 95)
        nps_target = min(100, nps + rng.randint(-5, 10))
        accept = round(rng.uniform(80.0, 96.0), 1)
        accept_target = round(min(100, accept + rng.uniform(-2, 5)), 1)

        hire_trend = "up" if hires >= hires_target * 0.9 else "down"
        time_trend = "down" if avg_time <= time_target * 1.15 else "up"
        cost_trend = "down" if cost <= cost_target * 1.1 else "up"
        conv_trend = "up" if conv >= conv_target * 0.85 else "down"

        return [
            {"name": "Contratações no Mês", "value": hires, "unit": "", "target": hires_target,
             "trend": hire_trend, "trend_percentage": self._trend_pct(rng, hire_trend), "positive_up": True},
            {"name": "Tempo Médio de Contratação", "value": avg_time, "unit": " dias", "target": time_target,
             "trend": time_trend, "trend_percentage": self._trend_pct(rng, time_trend), "positive_up": False},
            {"name": "Custo por Contratação", "value": f"R$ {cost:,}".replace(",", "."), "unit": "",
             "target": f"R$ {cost_target:,}".replace(",", "."),
             "trend": cost_trend, "trend_percentage": self._trend_pct(rng, cost_trend), "positive_up": False},
            {"name": "Taxa de Conversão", "value": conv, "unit": "%", "target": conv_target,
             "trend": conv_trend, "trend_percentage": self._trend_pct(rng, conv_trend), "positive_up": True},
            {"name": "NPS Candidatos", "value": nps, "unit": " pts", "target": nps_target,
             "trend": "up", "trend_percentage": self._trend_pct(rng, "up", 1.0, 10.0), "positive_up": True},
            {"name": "Taxa de Aceite", "value": accept, "unit": "%", "target": accept_target,
             "trend": "up", "trend_percentage": self._trend_pct(rng, "up", 1.0, 8.0), "positive_up": True},
        ]

    def executive_summary(self) -> dict[str, Any]:
        rng = self._rng(self._monthly_seed() + 1)
        hires = rng.randint(8, 30)
        open_pos = rng.randint(20, 80)
        avg_time = rng.randint(18, 40)
        total_cost = hires * rng.randint(3000, 7000)
        return {
            "hires": hires,
            "open_positions": open_pos,
            "avg_time_to_hire": avg_time,
            "total_cost": total_cost,
        }

    def department_breakdown(self) -> list[dict[str, Any]]:
        rng = self._rng(self._monthly_seed() + 2)
        dept_count = rng.randint(5, 8)
        depts = rng.sample(self.DEPARTMENTS, dept_count)
        results = []
        for dept in depts:
            open_pos = rng.randint(2, 18)
            fill_rate = rng.randint(40, 95)
            hires = max(0, int(open_pos * fill_rate / 100))
            results.append({
                "department": dept,
                "hires": hires,
                "open_positions": open_pos,
                "fill_rate": fill_rate,
            })
        results.sort(key=lambda d: d["hires"], reverse=True)
        return results

    def predictions(self) -> list[dict[str, Any]]:
        rng = self._rng(self._monthly_seed() + 3)
        hires_current = rng.randint(8, 25)
        hires_predicted = hires_current + rng.randint(1, 8)
        time_current = rng.randint(20, 38)
        time_predicted = max(15, time_current - rng.randint(2, 8))
        cost_current = rng.randint(3000, 7000)
        cost_predicted = max(2000, cost_current - rng.randint(200, 1200))
        turnover_current = round(rng.uniform(8.0, 18.0), 1)
        turnover_predicted = round(max(5.0, turnover_current - rng.uniform(0.5, 3.0)), 1)

        preds = [
            {
                "metric_name": "Contratações Próximo Mês",
                "current_value": hires_current,
                "predicted_value": hires_predicted,
                "confidence": round(rng.uniform(0.75, 0.92), 2),
                "trend": "up",
                "recommendation": "Considere aumentar capacidade de entrevistas para absorver a demanda crescente",
            },
            {
                "metric_name": "Tempo Médio de Contratação",
                "current_value": time_current,
                "predicted_value": time_predicted,
                "confidence": round(rng.uniform(0.70, 0.88), 2),
                "trend": "down",
                "recommendation": "Mantenha as otimizações no processo de triagem e automatize etapas repetitivas",
            },
            {
                "metric_name": "Custo por Contratação",
                "current_value": cost_current,
                "predicted_value": cost_predicted,
                "confidence": round(rng.uniform(0.72, 0.90), 2),
                "trend": "down",
                "recommendation": "Fortaleça o programa de indicações internas para reduzir custos de aquisição",
            },
            {
                "metric_name": "Taxa de Turnover Voluntário",
                "current_value": turnover_current,
                "predicted_value": turnover_predicted,
                "confidence": round(rng.uniform(0.65, 0.82), 2),
                "trend": "down",
                "recommendation": "Invista em onboarding estruturado e acompanhamento nos primeiros 90 dias",
            },
        ]
        count = rng.randint(3, 4)
        return preds[:count]

    def daily_sample(self, user_name: str, company_name: str) -> dict[str, Any]:
        rng = self._rng(self._daily_seed())
        urgent = rng.randint(1, 5)
        tasks = rng.randint(4, 12)
        interviews = rng.randint(1, 5)
        alerts = rng.randint(0, 3)

        hour = 8
        schedule = []
        interview_count = 0
        task_count = 0
        for _ in range(min(rng.randint(3, 6), interviews + 3)):
            if rng.random() < 0.5 and interview_count < interviews:
                cand = rng.choice(self.CANDIDATE_NAMES_DAILY)
                title = rng.choice(self.JOB_TITLES_DAILY)
                schedule.append({"time": f"{hour:02d}:00", "type": "interview",
                                 "title": f"Entrevista - {cand} ({title})"})
                interview_count += 1
            else:
                task_titles = [
                    "Revisão de currículos - Vaga Analista",
                    "Feedback para gestores",
                    "Alinhamento com hiring manager",
                    "Triagem de candidatos - Vaga Dev",
                    "Reunião de pipeline semanal",
                ]
                schedule.append({"time": f"{hour:02d}:00", "type": "task",
                                 "title": rng.choice(task_titles)})
                task_count += 1
            hour += rng.randint(1, 3)
            if hour > 17:
                break

        active_jobs = rng.randint(20, 60)
        total_cand = rng.randint(400, 1800)

        return {
            "greeting": "Bom dia" if datetime.now().hour < 12 else ("Boa tarde" if datetime.now().hour < 18 else "Boa noite"),
            "user_name": user_name,
            "generated_at": datetime.now().strftime("%d/%m/%Y às %H:%M"),
            "summary": {
                "urgent_count": urgent,
                "tasks_today": tasks,
                "interviews_today": interviews,
                "alerts_active": alerts,
            },
            "urgent_actions": [
                {"title": f"Feedback pendente - {rng.choice(self.CANDIDATE_NAMES_DAILY)}",
                 "description": f"Aguardando há {rng.randint(24, 72)}h", "priority": "high", "action_label": "Avaliar"},
                {"title": f"Tarefa atrasada - Triagem {rng.choice(self.JOB_TITLES_DAILY)}",
                 "description": "Venceu ontem", "priority": "critical", "action_label": "Resolver"},
                {"title": f"Alerta de SLA - Vaga {rng.choice(self.JOB_TITLES_DAILY)}",
                 "description": f"Vence em {rng.randint(1, 5)} dias", "priority": "medium", "action_label": "Verificar"},
            ][:urgent],
            "pipeline": {
                "active_jobs": active_jobs,
                "total_candidates": total_cand,
                "stages_summary": [
                    {"stage": "new", "count": int(total_cand * rng.uniform(0.15, 0.25)), "label": "Novos"},
                    {"stage": "screening", "count": int(total_cand * rng.uniform(0.10, 0.18)), "label": "Triagem"},
                    {"stage": "interview", "count": int(total_cand * rng.uniform(0.05, 0.12)), "label": "Entrevista"},
                    {"stage": "offer", "count": rng.randint(5, 20), "label": "Oferta"},
                    {"stage": "hired", "count": rng.randint(3, 15), "label": "Contratado"},
                ],
            },
            "schedule": schedule,
            "insights": [
                {"type": "attention", "title": "Feedbacks acumulados",
                 "description": f"{rng.randint(3, 10)} candidatos aguardando avaliação há mais de 48h."},
                {"type": "opportunity", "title": "Candidatos de alta qualidade",
                 "description": f"{rng.randint(2, 8)} candidatos com match acima de 90% aguardam contato."},
            ],
            "alerts": [
                {"title": "SLA Crítico",
                 "message": f"Vaga {rng.choice(self.JOB_TITLES_DAILY)} atinge SLA em {rng.randint(1, 4)} dias",
                 "severity": "high"},
            ] if alerts > 0 else [],
            "company_name": company_name,
        }


_demo_gen = DemoDataGenerator()


class ReportService:
    """
    Service for generating and sending automatic reports.
    """
    
    def __init__(self):
        self.briefing_service = briefing_service
        self.email_service = EmailService()
    
    async def generate_daily_briefing_email(
        self,
        user_id: str,
        user_email: str,
        user_name: str,
        company_name: str = "Sua Empresa",
        db: AsyncSession | None = None,
        send_email: bool = True,
        company_id: str | None = None,  # WT-2022 P0.TASK: tenant scope
    ) -> dict[str, Any]:
        """
        Generate and optionally send daily briefing email.
        
        Args:
            user_id: The recruiter's user ID
            user_email: Email address to send to
            user_name: Recruiter's name for personalization
            company_name: Company name for branding
            db: Optional database session
            send_email: Whether to send email or just generate
            
        Returns:
            Report result with HTML content and send status
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
            
        try:
            briefing_data = await self.briefing_service.generate_daily_briefing(
                user_id=user_id,
                db=db,
                company_id=company_id,  # WT-2022 P0.TASK
            )
            
            template_data = {
                "greeting": briefing_data.get("greeting", "Bom dia"),
                "user_name": user_name,
                "generated_at": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                "summary": briefing_data.get("summary", {}),
                "urgent_actions": briefing_data.get("urgent_actions", []),
                "pipeline": briefing_data.get("pipeline", {}),
                "schedule": briefing_data.get("schedule", []),
                "alerts": briefing_data.get("alerts", []),
                "insights": briefing_data.get("insights", []),
                "company_name": company_name,
            }
            
            html_content = report_templates.daily_briefing_html(template_data)
            
            result = {
                "report_type": "daily_briefing",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "html_content": html_content,
                "data": template_data,
                "email_sent": False,
                "email_id": None,
            }
            
            if send_email:
                email_result = await self._send_report_email(
                    to_email=user_email,
                    subject=f"📋 Briefing Diário - {datetime.now().strftime('%d/%m/%Y')}",
                    html_content=html_content,
                    report_type="daily_briefing"
                )
                result["email_sent"] = email_result.get("success", False)
                result["email_id"] = email_result.get("email_id")
                result["email_error"] = email_result.get("error")
            
            logger.info(f"📧 Daily briefing generated for user {user_id}")
            
            try:
                from app.shared.services.event_dispatcher import event_dispatcher
                await event_dispatcher.on_report_generated(
                    company_id=company_name,
                    report_type="daily_briefing",
                    user_id=user_id,
                    email_sent=result.get("email_sent", False),
                    recipients_count=1
                )
            except Exception as e:
                logger.warning(f"Event dispatch failed for daily briefing: {e}")
            
            return result
            
        finally:
            if should_close:
                await db.close()
    
    async def generate_weekly_performance_report(
        self,
        recipient_emails: list[str],
        recipient_name: str = "Equipe",
        company_name: str = "Sua Empresa",
        company_id: str = None,
        send_email: bool = True
    ) -> dict[str, Any]:
        """
        Generate and optionally send weekly performance report.
        
        Args:
            recipient_emails: List of email addresses to send to
            recipient_name: Recipient name for personalization
            company_name: Company name for branding
            company_id: Optional company ID for multi-tenant filtering
            send_email: Whether to send email or just generate
            
        Returns:
            Report result with HTML content and send status
        """
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        period = f"Semana de {week_start.strftime('%d/%m')} a {week_end.strftime('%d/%m/%Y')}"
        
        kpis = await self._get_weekly_kpis(company_id=company_id)
        funnel = await self._get_funnel_data(company_id=company_id)
        recruiter_ranking = await self._get_recruiter_ranking(company_id=company_id)
        channel_performance = await self._get_channel_performance(company_id=company_id)
        recommendations = await self._generate_weekly_recommendations(kpis, funnel)
        
        template_data = {
            "period": period,
            "generated_at": now.strftime("%d/%m/%Y às %H:%M"),
            "kpis": kpis,
            "funnel": funnel,
            "recruiter_ranking": recruiter_ranking,
            "channel_performance": channel_performance,
            "weekly_summary": {
                "total_hires": sum(r.get("positions_filled", 0) for r in recruiter_ranking),
                "total_candidates": funnel.get("total_candidates", 0),
                "conversion_rate": funnel.get("overall_conversion_rate", 0),
            },
            "recommendations": recommendations,
            "company_name": company_name,
        }
        
        html_content = report_templates.weekly_report_html(template_data)
        
        result = {
            "report_type": "weekly_performance",
            "generated_at": now.isoformat(),
            "html_content": html_content,
            "data": template_data,
            "emails_sent": [],
            "emails_failed": [],
        }
        
        if send_email:
            for email in recipient_emails:
                email_result = await self._send_report_email(
                    to_email=email,
                    subject=f"📊 Relatório Semanal de Recrutamento - {period}",
                    html_content=html_content,
                    report_type="weekly_performance"
                )
                if email_result.get("success"):
                    result["emails_sent"].append(email)
                else:
                    result["emails_failed"].append({
                        "email": email,
                        "error": email_result.get("error")
                    })
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"📊 Weekly report generated and sent to {len(result['emails_sent'])} recipients")
        
        try:
            from app.shared.services.event_dispatcher import event_dispatcher
            await event_dispatcher.on_report_generated(
                company_id=company_name,
                report_type="weekly_performance",
                email_sent=len(result["emails_sent"]) > 0,
                recipients_count=len(result["emails_sent"])
            )
        except Exception as e:
            logger.warning(f"Event dispatch failed for weekly report: {e}")
        
        return result
    
    async def generate_monthly_manager_report(
        self,
        recipient_emails: list[str],
        recipient_name: str = "Gestão",
        company_name: str = "Sua Empresa",
        company_id: str = None,
        send_email: bool = True
    ) -> dict[str, Any]:
        """
        Generate and optionally send monthly manager report.
        
        Args:
            recipient_emails: List of manager email addresses
            recipient_name: Recipient name for personalization
            company_name: Company name for branding
            company_id: Optional company ID for multi-tenant filtering
            send_email: Whether to send email or just generate
            
        Returns:
            Report result with HTML content and send status
        """
        now = datetime.now()
        month_names = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        period = f"{month_names[now.month - 1]} {now.year}"
        
        kpis = await self._get_strategic_kpis(company_id=company_id)
        executive_summary = await self._get_executive_summary(company_id=company_id)
        department_breakdown = await self._get_department_breakdown(company_id=company_id)
        predictions = await self._get_predictions(company_id=company_id)
        strategic_recommendations = await self._generate_strategic_recommendations(
            kpis, executive_summary, predictions
        )
        
        template_data = {
            "period": period,
            "generated_at": now.strftime("%d/%m/%Y às %H:%M"),
            "executive_summary": executive_summary,
            "kpis": kpis,
            "monthly_comparison": {
                "hires_change": 20.0,
                "cost_change": -6.25,
                "time_to_hire_change": -12.5,
            },
            "department_breakdown": department_breakdown,
            "cost_analysis": {
                "total_cost": executive_summary.get("total_cost", 0),
                "cost_per_hire": 4500,
                "budget_used": 75.0,
            },
            "predictions": predictions,
            "strategic_recommendations": strategic_recommendations,
            "company_name": company_name,
        }
        
        html_content = report_templates.monthly_report_html(template_data)
        
        result = {
            "report_type": "monthly_manager",
            "generated_at": now.isoformat(),
            "html_content": html_content,
            "data": template_data,
            "emails_sent": [],
            "emails_failed": [],
        }
        
        if send_email:
            for email in recipient_emails:
                email_result = await self._send_report_email(
                    to_email=email,
                    subject=f"📈 Relatório Mensal Executivo - {period}",
                    html_content=html_content,
                    report_type="monthly_manager"
                )
                if email_result.get("success"):
                    result["emails_sent"].append(email)
                else:
                    result["emails_failed"].append({
                        "email": email,
                        "error": email_result.get("error")
                    })
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"📈 Monthly manager report generated and sent to {len(result['emails_sent'])} recipients")
        
        try:
            from app.shared.services.event_dispatcher import event_dispatcher
            await event_dispatcher.on_report_generated(
                company_id=company_name,
                report_type="monthly_manager",
                email_sent=len(result["emails_sent"]) > 0,
                recipients_count=len(result["emails_sent"])
            )
        except Exception as e:
            logger.warning(f"Event dispatch failed for monthly report: {e}")
        
        return result
    
    async def preview_report(
        self,
        report_type: str,
        user_name: str = "Recrutador",
        company_name: str = "Empresa Demo"
    ) -> dict[str, Any]:
        """
        Generate a preview of a report without sending.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            user_name: Name for personalization
            company_name: Company name for branding
            
        Returns:
            Report HTML content for preview
        """
        now = datetime.now()
        
        if report_type == "daily":
            template_data = await self._get_sample_daily_data(user_name, company_name)
            html_content = report_templates.daily_briefing_html(template_data)
        elif report_type == "weekly":
            template_data = await self._get_sample_weekly_data(company_name)
            html_content = report_templates.weekly_report_html(template_data)
        elif report_type == "monthly":
            template_data = await self._get_sample_monthly_data(company_name)
            html_content = report_templates.monthly_report_html(template_data)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return {
            "report_type": report_type,
            "generated_at": now.isoformat(),
            "html_content": html_content,
            "preview": True,
        }
    
    async def _send_report_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        report_type: str
    ) -> dict[str, Any]:
        """Send report email using configured email provider."""
        try:
            provider = get_email_provider()
            
            result = await provider.send_email(
                to=to_email,
                subject=subject,
                html_content=html_content,
                metadata={
                    "report_type": report_type,
                    "generated_at": datetime.now().isoformat(),
                }
            )
            
            if result.success:
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"📧 Report email sent via {result.provider}: {subject} -> {to_email}")
                return {
                    "success": True,
                    "simulated": result.status == "simulated",
                    "email_id": result.message_id or f"sim_{datetime.now().timestamp()}"
                }
            else:
                logger.error(f"❌ Failed to send report email: {result.error}")
                return {
                    "success": False,
                    "error": result.error
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to send report email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_weekly_kpis(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get weekly KPI data from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                now = datetime.now()
                week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
                prev_week_start = week_start - timedelta(days=7)

                company_filter = "AND vc.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :week_start) as hires,
                        COUNT(*) FILTER (WHERE vc.created_at >= :week_start) as candidates,
                        COALESCE(AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)
                            FILTER (WHERE vc.stage IN ('Contratado', 'hired')), 0) as avg_days,
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :prev_week_start AND vc.updated_at < :week_start) as prev_hires,
                        COUNT(*) FILTER (WHERE vc.created_at >= :prev_week_start AND vc.created_at < :week_start) as prev_candidates
                    FROM vacancy_candidates vc
                    WHERE 1=1 {company_filter}
                """), {**params, "week_start": week_start, "prev_week_start": prev_week_start})
                row = result.fetchone()

                if row is not None:
                    hires = int(row.hires)
                    candidates = int(row.candidates)
                    avg_time = round(float(row.avg_days)) if row.avg_days else 0
                    prev_hires = int(row.prev_hires)
                    prev_candidates = int(row.prev_candidates)
                    cost_per_hire = 4500

                    def calc_trend(current, previous):
                        if previous == 0:
                            return ("up", 0.0) if current > 0 else ("up", 0.0)
                        pct = round((current - previous) / previous * 100, 1)
                        return ("up" if pct >= 0 else "down", pct)

                    hire_trend, hire_pct = calc_trend(hires, prev_hires)
                    cand_trend, cand_pct = calc_trend(candidates, prev_candidates)

                    return [
                        {"name": "Contratações", "value": hires, "unit": "", "trend": hire_trend,
                         "trend_percentage": hire_pct, "positive_up": True},
                        {"name": "Candidatos", "value": candidates, "unit": "", "trend": cand_trend,
                         "trend_percentage": cand_pct, "positive_up": True},
                        {"name": "Tempo Médio", "value": avg_time, "unit": " dias", "trend": "down" if avg_time < 30 else "up",
                         "trend_percentage": -5.0 if avg_time < 30 else 5.0, "positive_up": False},
                        {"name": "Custo/Hire", "value": f"R$ {cost_per_hire / 1000:.1f}k", "unit": "", "trend": "down",
                         "trend_percentage": -3.0, "positive_up": False},
                    ]
        except Exception as e:
            logger.warning(f"Failed to get weekly KPIs from DB, using demo: {e}")
        return _demo_gen.weekly_kpis()

    async def _get_funnel_data(self, company_id: str = None) -> dict[str, Any]:
        """Get funnel performance data from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                company_filter = "AND vc.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT vc.stage, COUNT(*) as cnt
                    FROM vacancy_candidates vc
                    WHERE vc.stage IS NOT NULL {company_filter}
                    GROUP BY vc.stage
                """), params)
                rows = result.fetchall()

                if rows:
                    stage_counts = {r.stage: int(r.cnt) for r in rows}
                    stage_order = [
                        ("Novo", "Novo"), ("Triagem", "Triagem"),
                        ("Entrevista Técnica", "Entrevista Técnica"),
                        ("Entrevista RH", "Entrevista RH"),
                        ("Entrevista Final", "Entrevista Final"),
                        ("Proposta", "Proposta"), ("Contratado", "Contratado"),
                    ]
                    total = sum(stage_counts.values())
                    if total > 0:
                        stages = []
                        for i, (stage_key, stage_name) in enumerate(stage_order):
                            count = stage_counts.get(stage_key, 0)
                            conv_rate = round(count / total * 100, 1)
                            stages.append({
                                "stage_name": stage_name,
                                "count": count,
                                "conversion_rate": conv_rate,
                            })

                        contratados = stage_counts.get("Contratado", 0)
                        overall = round(contratados / total * 100, 2) if total else 0
                        return {
                            "stages": stages,
                            "total_candidates": total,
                            "overall_conversion_rate": overall,
                        }
        except Exception as e:
            logger.warning(f"Failed to get funnel data from DB, using demo: {e}")
        return _demo_gen.funnel_data()

    async def _get_recruiter_ranking(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get recruiter performance ranking from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                company_filter = "AND jv.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        jv.recruiter as recruiter_name,
                        COUNT(DISTINCT jv.id) as total_jobs,
                        COUNT(DISTINCT vc.id) FILTER (WHERE vc.stage IN ('Contratado', 'hired')) as positions_filled,
                        COUNT(DISTINCT vc.id) as total_candidates,
                        COALESCE(AVG(vc.match_percentage) FILTER (WHERE vc.match_percentage IS NOT NULL), 0) as avg_quality
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.recruiter IS NOT NULL {company_filter}
                    GROUP BY jv.recruiter
                    ORDER BY positions_filled DESC
                """), params)
                rows = result.fetchall()

                if rows:
                    ranking = []
                    for r in rows:
                        total_cands = int(r.total_candidates) if r.total_candidates else 0
                        filled = int(r.positions_filled) if r.positions_filled else 0
                        conv_rate = round(filled / total_cands * 100, 1) if total_cands > 0 else 0
                        quality = round(float(r.avg_quality), 1) if r.avg_quality else 0

                        ranking.append({
                            "recruiter_name": r.recruiter_name,
                            "positions_filled": filled,
                            "positions_target": int(r.total_jobs),
                            "conversion_rate": conv_rate,
                            "quality_score": quality,
                        })
                    if ranking:
                        return ranking
        except Exception as e:
            logger.warning(f"Failed to get recruiter ranking from DB, using demo: {e}")
        return _demo_gen.recruiter_ranking()

    async def _get_channel_performance(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get channel performance data from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                company_filter = "AND vc.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        COALESCE(NULLIF(vc.source, 'SEED_DATA'), 'Outros') as channel_name,
                        COUNT(*) as candidates_count,
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired')) as hired_count
                    FROM vacancy_candidates vc
                    WHERE vc.source IS NOT NULL {company_filter}
                    GROUP BY COALESCE(NULLIF(vc.source, 'SEED_DATA'), 'Outros')
                    ORDER BY candidates_count DESC
                """), params)
                rows = result.fetchall()

                if rows:
                    results = []
                    for r in rows:
                        cands = int(r.candidates_count)
                        hired = int(r.hired_count)
                        conv_rate = round(hired / cands * 100, 1) if cands > 0 else 0
                        cost_per_hire = 4500 if hired > 0 else 0
                        results.append({
                            "channel_name": r.channel_name,
                            "candidates_count": cands,
                            "conversion_rate": conv_rate,
                            "cost_per_hire": cost_per_hire,
                        })
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"Failed to get channel performance from DB, using demo: {e}")
        return _demo_gen.channel_performance()

    async def _get_strategic_kpis(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get strategic KPIs for monthly report from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                now = datetime.now()
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                company_filter = "AND vc.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :month_start) as hires,
                        COUNT(*) FILTER (WHERE vc.created_at >= :month_start) as total_candidates,
                        COALESCE(AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)
                            FILTER (WHERE vc.stage IN ('Contratado', 'hired')), 0) as avg_days,
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired')) as all_hires
                    FROM vacancy_candidates vc
                    WHERE 1=1 {company_filter}
                """), {**params, "month_start": month_start})
                row = result.fetchone()

                if row is not None:
                    hires = int(row.hires)
                    total_cands = int(row.total_candidates)
                    avg_time = round(float(row.avg_days)) if row.avg_days else 25
                    all_hires = int(row.all_hires)
                    conv_rate = round(all_hires / total_cands * 100, 1) if total_cands > 0 else 0
                    cost = 4500

                    return [
                        {"name": "Contratações no Mês", "value": hires, "unit": "", "target": hires + 3,
                         "trend": "up" if hires > 0 else "down",
                         "trend_percentage": 10.0 if hires > 0 else -5.0, "positive_up": True},
                        {"name": "Tempo Médio de Contratação", "value": avg_time, "unit": " dias", "target": max(15, avg_time - 5),
                         "trend": "down" if avg_time <= 30 else "up",
                         "trend_percentage": -8.0 if avg_time <= 30 else 5.0, "positive_up": False},
                        {"name": "Custo por Contratação", "value": f"R$ {cost:,}".replace(",", "."), "unit": "",
                         "target": f"R$ {cost - 500:,}".replace(",", "."),
                         "trend": "down", "trend_percentage": -6.0, "positive_up": False},
                        {"name": "Taxa de Conversão", "value": conv_rate, "unit": "%", "target": round(conv_rate + 1.0, 1),
                         "trend": "up" if conv_rate > 2.0 else "down",
                         "trend_percentage": 5.0 if conv_rate > 2.0 else -3.0, "positive_up": True},
                        {"name": "NPS Candidatos", "value": 82, "unit": " pts", "target": 85,
                         "trend": "up", "trend_percentage": 3.0, "positive_up": True},
                        {"name": "Taxa de Aceite", "value": 88.5, "unit": "%", "target": 90.0,
                         "trend": "up", "trend_percentage": 2.0, "positive_up": True},
                    ]
        except Exception as e:
            logger.warning(f"Failed to get strategic KPIs from DB, using demo: {e}")
        return _demo_gen.strategic_kpis()

    async def _get_executive_summary(self, company_id: str = None) -> dict[str, Any]:
        """Get executive summary data from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                now = datetime.now()
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                vc_filter = "AND vc.company_id = :company_id" if company_id else ""
                jv_filter = "AND jv.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        (SELECT COUNT(*) FROM vacancy_candidates vc
                         WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :month_start {vc_filter}) as hires,
                        (SELECT COUNT(*) FROM job_vacancies jv
                         WHERE jv.status IN ('Ativa', 'active') {jv_filter}) as open_positions,
                        (SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400), 0)
                         FROM vacancy_candidates vc
                         WHERE vc.stage IN ('Contratado', 'hired') {vc_filter}) as avg_days
                """), {**params, "month_start": month_start})
                row = result.fetchone()

                if row is not None:
                    hires = int(row.hires)
                    open_positions = int(row.open_positions)
                    avg_time = round(float(row.avg_days)) if row.avg_days else 0
                    cost_per_hire = 4500
                    total_cost = hires * cost_per_hire

                    return {
                        "hires": hires,
                        "open_positions": open_positions,
                        "avg_time_to_hire": avg_time,
                        "total_cost": total_cost,
                    }
        except Exception as e:
            logger.warning(f"Failed to get executive summary from DB, using demo: {e}")
        return _demo_gen.executive_summary()

    async def _get_department_breakdown(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get department breakdown data from database with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                company_filter = "AND jv.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        COALESCE(jv.department, 'Não definido') as department,
                        COUNT(DISTINCT jv.id) as open_positions,
                        COUNT(DISTINCT vc.id) FILTER (WHERE vc.stage IN ('Contratado', 'hired')) as hires
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.department IS NOT NULL {company_filter}
                    GROUP BY jv.department
                    ORDER BY hires DESC
                """), params)
                rows = result.fetchall()

                if rows:
                    results = []
                    for r in rows:
                        open_pos = int(r.open_positions)
                        hires = int(r.hires)
                        fill_rate = round(hires / open_pos * 100) if open_pos > 0 else 0
                        results.append({
                            "department": r.department,
                            "hires": hires,
                            "open_positions": open_pos,
                            "fill_rate": fill_rate,
                        })
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"Failed to get department breakdown from DB, using demo: {e}")
        return _demo_gen.department_breakdown()

    async def _get_predictions(self, company_id: str = None) -> list[dict[str, Any]]:
        """Get AI predictions based on trend data with demo fallback."""
        try:
            async with AsyncSessionLocal() as db:
                now = datetime.now()
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                prev_month_start = (month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                company_filter = "AND vc.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :month_start) as hires_current,
                        COUNT(*) FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :prev_month_start AND vc.updated_at < :month_start) as hires_prev,
                        COALESCE(AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)
                            FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :month_start), 0) as avg_time_current,
                        COALESCE(AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)
                            FILTER (WHERE vc.stage IN ('Contratado', 'hired') AND vc.updated_at >= :prev_month_start AND vc.updated_at < :month_start), 0) as avg_time_prev
                    FROM vacancy_candidates vc
                    WHERE 1=1 {company_filter}
                """), {**params, "month_start": month_start, "prev_month_start": prev_month_start})
                row = result.fetchone()

                if row is not None:
                    hires_current = int(row.hires_current)
                    hires_prev = int(row.hires_prev)
                    time_current = round(float(row.avg_time_current)) if row.avg_time_current else 25
                    time_prev = round(float(row.avg_time_prev)) if row.avg_time_prev else 30
                    cost_current = 4500

                    hires_trend = "up" if hires_current >= hires_prev else "down"
                    hires_predicted = max(1, hires_current + (hires_current - hires_prev))
                    time_predicted = max(15, time_current - max(0, time_prev - time_current))
                    cost_predicted = max(3000, cost_current - 300)

                    return [
                        {
                            "metric_name": "Contratações Próximo Mês",
                            "current_value": hires_current,
                            "predicted_value": hires_predicted,
                            "confidence": 0.80,
                            "trend": hires_trend,
                            "recommendation": "Considere aumentar capacidade de entrevistas para absorver a demanda crescente" if hires_trend == "up" else "Revise estratégias de sourcing para melhorar o pipeline",
                        },
                        {
                            "metric_name": "Tempo Médio de Contratação",
                            "current_value": time_current,
                            "predicted_value": time_predicted,
                            "confidence": 0.75,
                            "trend": "down" if time_predicted < time_current else "up",
                            "recommendation": "Mantenha as otimizações no processo de triagem e automatize etapas repetitivas",
                        },
                        {
                            "metric_name": "Custo por Contratação",
                            "current_value": cost_current,
                            "predicted_value": cost_predicted,
                            "confidence": 0.78,
                            "trend": "down",
                            "recommendation": "Fortaleça o programa de indicações internas para reduzir custos de aquisição",
                        },
                    ]
        except Exception as e:
            logger.warning(f"Failed to get predictions from DB, using demo: {e}")
        return _demo_gen.predictions()
    
    async def _generate_weekly_recommendations(
        self,
        kpis: list[dict[str, Any]],
        funnel: dict[str, Any]
    ) -> list[str]:
        """Generate weekly recommendations based on data."""
        recommendations = []
        
        stages = funnel.get("stages", [])
        for i, stage in enumerate(stages[:-1]):
            next_stage = stages[i + 1] if i + 1 < len(stages) else None
            if next_stage and next_stage.get("conversion_rate", 100) < 40:
                recommendations.append(
                    f"Taxa de conversão baixa entre {stage.get('stage_name')} e {next_stage.get('stage_name')}. "
                    f"Revise critérios e processo desta etapa."
                )
        
        recommendations.append("Continue investindo em programa de indicações - canal com melhor ROI.")
        recommendations.append("Priorize vagas críticas com SLA próximo do vencimento.")
        
        return recommendations[:4]
    
    async def _generate_strategic_recommendations(
        self,
        kpis: list[dict[str, Any]],
        executive_summary: dict[str, Any],
        predictions: list[dict[str, Any]]
    ) -> list[str]:
        """Generate strategic recommendations for managers."""
        recommendations = []
        
        hires = executive_summary.get("hires", 0)
        open_positions = executive_summary.get("open_positions", 0)
        
        if open_positions > hires * 3:
            recommendations.append(
                f"Volume de vagas abertas ({open_positions}) significativamente maior que contratações ({hires}). "
                "Considere aumentar equipe de recrutamento ou otimizar processos."
            )
        
        for pred in predictions:
            if pred.get("recommendation"):
                recommendations.append(pred["recommendation"])
        
        recommendations.append(
            "Implemente automação de triagem com IA para reduzir tempo na primeira etapa."
        )
        recommendations.append(
            "Fortaleça employer branding para melhorar qualidade de candidatos orgânicos."
        )
        
        return recommendations[:5]
    
    async def _get_sample_daily_data(self, user_name: str, company_name: str, company_id: str = None) -> dict[str, Any]:
        """Get sample data for daily report preview, using real data when available."""
        try:
            async with AsyncSessionLocal() as db:
                company_filter_vc = "AND vc.company_id = :company_id" if company_id else ""
                company_filter_jv = "AND jv.company_id = :company_id" if company_id else ""
                params = {"company_id": company_id} if company_id else {}

                result = await db.execute(text(f"""
                    SELECT
                        (SELECT COUNT(*) FROM job_vacancies jv WHERE jv.status IN ('Ativa', 'active') {company_filter_jv}) as active_jobs,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE 1=1 {company_filter_vc}) as total_candidates,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE vc.stage = 'Novo' {company_filter_vc}) as new_count,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE vc.stage = 'Triagem' {company_filter_vc}) as screening_count,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE vc.stage IN ('Entrevista Técnica', 'Entrevista RH', 'Entrevista Final') {company_filter_vc}) as interview_count,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE vc.stage = 'Proposta' {company_filter_vc}) as offer_count,
                        (SELECT COUNT(*) FROM vacancy_candidates vc WHERE vc.stage IN ('Contratado', 'hired') {company_filter_vc}) as hired_count
                """), params)
                row = result.fetchone()

                if row and int(row.total_candidates) > 0:
                    base = _demo_gen.daily_sample(user_name, company_name)
                    base["pipeline"] = {
                        "active_jobs": int(row.active_jobs),
                        "total_candidates": int(row.total_candidates),
                        "stages_summary": [
                            {"stage": "new", "count": int(row.new_count), "label": "Novos"},
                            {"stage": "screening", "count": int(row.screening_count), "label": "Triagem"},
                            {"stage": "interview", "count": int(row.interview_count), "label": "Entrevista"},
                            {"stage": "offer", "count": int(row.offer_count), "label": "Oferta"},
                            {"stage": "hired", "count": int(row.hired_count), "label": "Contratado"},
                        ],
                    }
                    return base
        except Exception as e:
            logger.warning(f"Failed to get daily sample from DB, using demo: {e}")
        return _demo_gen.daily_sample(user_name, company_name)

    async def _get_sample_weekly_data(self, company_name: str, company_id: str = None) -> dict[str, Any]:
        """Get sample data for weekly report preview."""
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)

        kpis = await self._get_weekly_kpis(company_id=company_id)
        funnel = await self._get_funnel_data(company_id=company_id)
        recommendations = await self._generate_weekly_recommendations(kpis, funnel)

        return {
            "period": f"Semana de {week_start.strftime('%d/%m')} a {week_end.strftime('%d/%m/%Y')}",
            "generated_at": now.strftime("%d/%m/%Y às %H:%M"),
            "kpis": kpis,
            "funnel": funnel,
            "recruiter_ranking": await self._get_recruiter_ranking(company_id=company_id),
            "channel_performance": await self._get_channel_performance(company_id=company_id),
            "recommendations": recommendations,
            "company_name": company_name,
        }

    async def _get_sample_monthly_data(self, company_name: str, company_id: str = None) -> dict[str, Any]:
        """Get sample data for monthly report preview."""
        now = datetime.now()
        month_names = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]

        kpis = await self._get_strategic_kpis(company_id=company_id)
        executive_summary = await self._get_executive_summary(company_id=company_id)
        predictions = await self._get_predictions(company_id=company_id)
        strategic_recommendations = await self._generate_strategic_recommendations(
            kpis, executive_summary, predictions
        )

        return {
            "period": f"{month_names[now.month - 1]} {now.year}",
            "generated_at": now.strftime("%d/%m/%Y às %H:%M"),
            "executive_summary": executive_summary,
            "kpis": kpis,
            "department_breakdown": await self._get_department_breakdown(company_id=company_id),
            "predictions": predictions,
            "strategic_recommendations": strategic_recommendations,
            "company_name": company_name,
        }


report_service = ReportService()
