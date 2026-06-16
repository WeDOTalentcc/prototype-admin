"""
Report Templates for LIA Platform.
HTML templates for daily briefings, weekly reports, and monthly manager reports.
"""
from datetime import datetime
from typing import Any


def _format_number(value: float, decimals: int = 1) -> str:
    """Format number with proper decimal places."""
    if decimals == 0:
        return f"{int(value):,}".replace(",", ".")
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _trend_icon(trend: str) -> str:
    """Get trend icon based on direction."""
    if trend == "up":
        return "↑"
    elif trend == "down":
        return "↓"
    return "→"


def _trend_color(trend: str, positive_is_up: bool = True) -> str:
    """Get trend color based on direction."""
    if trend == "up":
        return "#16a34a" if positive_is_up else "#dc2626"
    elif trend == "down":
        return "#dc2626" if positive_is_up else "#16a34a"
    return "#6b7280"


def _severity_color(severity: str) -> str:
    """Get color based on alert severity."""
    colors = {
        "critical": "#dc2626",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#3b82f6"
    }
    return colors.get(severity, "#6b7280")


class ReportTemplates:
    """HTML templates for reports."""

    @staticmethod
    def daily_briefing_html(data: dict[str, Any]) -> str:
        """
        Generate HTML template for daily briefing email.
        
        Args:
            data: Briefing data containing:
                - greeting: Time-appropriate greeting
                - user_name: Recruiter name
                - generated_at: Generation timestamp
                - summary: Summary counts
                - urgent_actions: List of urgent items
                - pipeline: Pipeline summary
                - schedule: Today's schedule
                - alerts: Active alerts
                - insights: LIA insights
                - company_name: Company name
        """
        user_name = data.get("user_name", "Recrutador")
        greeting = data.get("greeting", "Bom dia")
        generated_at = data.get("generated_at", datetime.now().strftime("%d/%m/%Y às %H:%M"))
        summary = data.get("summary", {})
        urgent_actions = data.get("urgent_actions", [])
        pipeline = data.get("pipeline", {})
        schedule = data.get("schedule", [])
        alerts = data.get("alerts", [])
        insights = data.get("insights", [])
        company_name = data.get("company_name", "Sua Empresa")
        
        urgent_html = ""
        if urgent_actions:
            urgent_items = ""
            for action in urgent_actions[:5]:
                priority_color = _severity_color(action.get("priority", "medium"))
                urgent_items += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {priority_color}; margin-right: 8px;"></span>
                        <strong>{action.get('title', 'Ação pendente')}</strong>
                        <p style="margin: 4px 0 0 16px; color: #6b7280; font-size: 13px;">{action.get('description', '')}</p>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        <span style="background-color: #2563eb; color: white; padding: 6px 12px; border-radius: 4px; font-size: 12px; text-decoration: none;">
                            {action.get('action_label', 'Ver')}
                        </span>
                    </td>
                </tr>
                """
            urgent_html = f"""
            <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                <h3 style="margin: 0 0 12px 0; color: #dc2626;">🚨 Ações Urgentes ({len(urgent_actions)})</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {urgent_items}
                </table>
            </div>
            """
        
        schedule_html = ""
        if schedule:
            schedule_items = ""
            for item in schedule[:6]:
                icon = "📅" if item.get("type") == "interview" else "✅"
                schedule_items += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; width: 60px; font-weight: bold; color: #2563eb;">
                        {item.get('time', '--:--')}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                        {icon} {item.get('title', 'Atividade')}
                    </td>
                </tr>
                """
            schedule_html = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">📆 Agenda do Dia</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #f9fafb; border-radius: 8px;">
                    {schedule_items}
                </table>
            </div>
            """
        else:
            schedule_html = """
            <div style="margin: 20px 0; background-color: #f0fdf4; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="margin: 0; color: #16a34a;">✅ Sem compromissos agendados para hoje</p>
            </div>
            """
        
        stages_html = ""
        stages_summary = pipeline.get("stages_summary", [])
        if stages_summary:
            for stage in stages_summary:
                stages_html += f"""
                <td style="text-align: center; padding: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: #2563eb;">{stage.get('count', 0)}</div>
                    <div style="font-size: 12px; color: #6b7280;">{stage.get('label', '')}</div>
                </td>
                """
        
        insights_html = ""
        if insights:
            insight_items = ""
            for insight in insights[:4]:
                insight_type = insight.get("type", "info")
                bg_color = "#f0f9ff" if insight_type == "info" else "#fef3c7" if insight_type == "attention" else "#f0fdf4" if insight_type == "success" else "#faf5ff"
                border_color = "#3b82f6" if insight_type == "info" else "#f59e0b" if insight_type == "attention" else "#22c55e" if insight_type == "success" else "#8b5cf6"
                insight_items += f"""
                <div style="background-color: {bg_color}; border-left: 3px solid {border_color}; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0;">
                    <strong>{insight.get('title', 'Insight')}</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: #4b5563;">{insight.get('description', '')}</p>
                </div>
                """
            insights_html = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">💡 Insights da LIA</h3>
                {insight_items}
            </div>
            """
        
        alerts_html = ""
        if alerts:
            alert_items = ""
            for alert in alerts[:3]:
                severity_color = _severity_color(alert.get("severity", "medium"))
                alert_items += f"""
                <div style="border-left: 3px solid {severity_color}; padding: 10px 12px; margin: 6px 0; background-color: #fafafa; border-radius: 0 4px 4px 0;">
                    <strong style="color: #1f2937;">{alert.get('title', 'Alerta')}</strong>
                    <p style="margin: 2px 0 0 0; font-size: 12px; color: #6b7280;">{alert.get('message', '')}</p>
                </div>
                """
            alerts_html = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">⚠️ Alertas Ativos</h3>
                {alert_items}
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; max-width: 650px; margin: 0 auto; padding: 20px; background-color: #f3f4f6;">
    <div style="background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 30px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">📋 Briefing Diário</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{generated_at}</p>
        </div>
        
        <div style="padding: 24px;">
            <p style="font-size: 18px; margin-bottom: 20px;">{greeting}, <strong>{user_name}</strong>!</p>
            
            <div style="display: flex; background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="text-align: center; padding: 8px; border-right: 1px solid #e5e7eb;">
                            <div style="font-size: 28px; font-weight: bold; color: #dc2626;">{summary.get('urgent_count', 0)}</div>
                            <div style="font-size: 12px; color: #6b7280;">Urgentes</div>
                        </td>
                        <td style="text-align: center; padding: 8px; border-right: 1px solid #e5e7eb;">
                            <div style="font-size: 28px; font-weight: bold; color: #2563eb;">{summary.get('tasks_today', 0)}</div>
                            <div style="font-size: 12px; color: #6b7280;">Tarefas</div>
                        </td>
                        <td style="text-align: center; padding: 8px; border-right: 1px solid #e5e7eb;">
                            <div style="font-size: 28px; font-weight: bold; color: #16a34a;">{summary.get('interviews_today', 0)}</div>
                            <div style="font-size: 12px; color: #6b7280;">Entrevistas</div>
                        </td>
                        <td style="text-align: center; padding: 8px;">
                            <div style="font-size: 28px; font-weight: bold; color: #f59e0b;">{summary.get('alerts_active', 0)}</div>
                            <div style="font-size: 12px; color: #6b7280;">Alertas</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            {urgent_html}
            
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">📊 Pipeline de Recrutamento</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #f0f9ff; border-radius: 8px;">
                    <tr>
                        {stages_html}
                    </tr>
                </table>
                <p style="text-align: center; font-size: 13px; color: #6b7280; margin-top: 8px;">
                    {pipeline.get('active_jobs', 0)} vagas ativas • {pipeline.get('total_candidates', 0)} candidatos em processo
                </p>
            </div>
            
            {schedule_html}
            
            {insights_html}
            
            {alerts_html}
            
            <div style="text-align: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <a href="#" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                    Abrir WeDOTalent
                </a>
            </div>
        </div>
        
        <div style="background-color: #f9fafb; padding: 16px; text-align: center; font-size: 12px; color: #6b7280;">
            <p style="margin: 0;">Este briefing foi gerado automaticamente pela LIA</p>
            <p style="margin: 4px 0 0 0;">{company_name} • WeDOTalent</p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def weekly_report_html(data: dict[str, Any]) -> str:
        """
        Generate HTML template for weekly performance report.
        
        Args:
            data: Report data containing:
                - period: Report period string
                - generated_at: Generation timestamp
                - kpis: List of KPI indicators
                - funnel: Funnel performance data
                - recruiter_ranking: List of recruiter performance
                - channel_performance: Source channel data
                - weekly_summary: Summary of the week
                - recommendations: LIA recommendations
                - company_name: Company name
        """
        period = data.get("period", "Semana atual")
        generated_at = data.get("generated_at", datetime.now().strftime("%d/%m/%Y"))
        kpis = data.get("kpis", [])
        funnel = data.get("funnel", {})
        recruiter_ranking = data.get("recruiter_ranking", [])
        channel_performance = data.get("channel_performance", [])
        data.get("weekly_summary", {})
        recommendations = data.get("recommendations", [])
        company_name = data.get("company_name", "Sua Empresa")
        
        kpis_html = ""
        for kpi in kpis[:8]:
            trend = kpi.get("trend", "stable")
            trend_pct = kpi.get("trend_percentage", 0)
            trend_color = _trend_color(trend, kpi.get("positive_up", True))
            trend_icon = _trend_icon(trend)
            kpis_html += f"""
            <td style="padding: 12px; text-align: center; border: 1px solid #e5e7eb; width: 25%;">
                <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">{kpi.get('name', '')}</div>
                <div style="font-size: 22px; font-weight: bold; color: #1f2937;">{kpi.get('value', 0)}{kpi.get('unit', '')}</div>
                <div style="font-size: 12px; color: {trend_color};">
                    {trend_icon} {abs(trend_pct):.1f}%
                </div>
            </td>
            """
        
        funnel_html = ""
        stages = funnel.get("stages", [])
        if stages:
            for i, stage in enumerate(stages):
                width_pct = max(20, stage.get("conversion_rate", 0))
                funnel_html += f"""
                <div style="margin: 6px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 13px; color: #374151;">{stage.get('stage_name', '')}</span>
                        <span style="font-size: 13px; font-weight: bold; color: #1f2937;">{stage.get('count', 0)}</span>
                    </div>
                    <div style="background-color: #e5e7eb; height: 24px; border-radius: 4px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #2563eb, #3b82f6); height: 100%; width: {width_pct}%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;">
                            <span style="color: white; font-size: 11px; font-weight: bold;">{stage.get('conversion_rate', 0):.1f}%</span>
                        </div>
                    </div>
                </div>
                """
        
        ranking_html = ""
        for i, recruiter in enumerate(recruiter_ranking[:5]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            ranking_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-size: 16px;">{medal}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{recruiter.get('recruiter_name', 'Recrutador')}</strong>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {recruiter.get('positions_filled', 0)}/{recruiter.get('positions_target', 0)}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {recruiter.get('conversion_rate', 0):.1f}%
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    <span style="background-color: #dbeafe; color: #1d4ed8; padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                        {recruiter.get('quality_score', 0):.1f}
                    </span>
                </td>
            </tr>
            """
        
        channels_html = ""
        for channel in channel_performance[:5]:
            channels_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{channel.get('channel_name', 'Canal')}</strong>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {channel.get('candidates_count', 0)}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {channel.get('conversion_rate', 0):.1f}%
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    R$ {_format_number(channel.get('cost_per_hire', 0), 0)}
                </td>
            </tr>
            """
        
        recommendations_html = ""
        if recommendations:
            rec_items = ""
            for rec in recommendations[:4]:
                rec_items += f"""
                <li style="margin: 8px 0; padding: 8px; background-color: #f0f9ff; border-radius: 4px;">
                    {rec}
                </li>
                """
            recommendations_html = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">🤖 Recomendações da LIA</h3>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    {rec_items}
                </ul>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f3f4f6;">
    <div style="background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%); color: white; padding: 30px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">📊 Relatório Semanal</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{period}</p>
        </div>
        
        <div style="padding: 24px;">
            <div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 12px 0; color: #1f2937;">📈 KPIs da Semana</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        {kpis_html}
                    </tr>
                </table>
            </div>
            
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">🎯 Funil de Conversão</h3>
                {funnel_html}
            </div>
            
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">🏆 Ranking de Recrutadores</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #fafafa; border-radius: 8px;">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 10px; text-align: left; font-size: 12px; color: #6b7280;">#</th>
                            <th style="padding: 10px; text-align: left; font-size: 12px; color: #6b7280;">Recrutador</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Vagas</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Conversão</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ranking_html}
                    </tbody>
                </table>
            </div>
            
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">📣 Performance por Canal</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #fafafa; border-radius: 8px;">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 10px; text-align: left; font-size: 12px; color: #6b7280;">Canal</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Candidatos</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Conversão</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Custo/Hire</th>
                        </tr>
                    </thead>
                    <tbody>
                        {channels_html}
                    </tbody>
                </table>
            </div>
            
            {recommendations_html}
            
            <div style="text-align: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <a href="#" style="display: inline-block; background-color: #7c3aed; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                    Ver Dashboard Completo
                </a>
            </div>
        </div>
        
        <div style="background-color: #f9fafb; padding: 16px; text-align: center; font-size: 12px; color: #6b7280;">
            <p style="margin: 0;">Relatório gerado automaticamente pela LIA • {generated_at}</p>
            <p style="margin: 4px 0 0 0;">{company_name}</p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def monthly_report_html(data: dict[str, Any]) -> str:
        """
        Generate HTML template for monthly manager report.
        
        Args:
            data: Report data containing:
                - period: Report period (month/year)
                - generated_at: Generation timestamp
                - executive_summary: High-level summary
                - kpis: List of strategic KPIs
                - monthly_comparison: Month-over-month comparison
                - department_breakdown: Performance by department
                - cost_analysis: Cost analysis data
                - predictions: AI predictions
                - strategic_recommendations: Strategic recommendations
                - company_name: Company name
        """
        period = data.get("period", "Dezembro 2024")
        generated_at = data.get("generated_at", datetime.now().strftime("%d/%m/%Y"))
        executive_summary = data.get("executive_summary", {})
        kpis = data.get("kpis", [])
        data.get("monthly_comparison", {})
        department_breakdown = data.get("department_breakdown", [])
        data.get("cost_analysis", {})
        predictions = data.get("predictions", [])
        strategic_recommendations = data.get("strategic_recommendations", [])
        company_name = data.get("company_name", "Sua Empresa")
        
        summary_cards = ""
        summary_items = [
            ("Contratações", executive_summary.get("hires", 0), "👥", "#16a34a"),
            ("Vagas Abertas", executive_summary.get("open_positions", 0), "📋", "#2563eb"),
            ("Tempo Médio", f"{executive_summary.get('avg_time_to_hire', 0)} dias", "⏱️", "#f59e0b"),
            ("Custo Total", f"R$ {_format_number(executive_summary.get('total_cost', 0), 0)}", "💰", "#8b5cf6"),
        ]
        for name, value, icon, color in summary_items:
            summary_cards += f"""
            <td style="padding: 16px; text-align: center; background-color: #f9fafb; border-radius: 8px; width: 25%;">
                <div style="font-size: 24px; margin-bottom: 4px;">{icon}</div>
                <div style="font-size: 24px; font-weight: bold; color: {color};">{value}</div>
                <div style="font-size: 12px; color: #6b7280;">{name}</div>
            </td>
            """
        
        kpis_html = ""
        for kpi in kpis[:6]:
            trend = kpi.get("trend", "stable")
            trend_pct = kpi.get("trend_percentage", 0)
            trend_color = _trend_color(trend, kpi.get("positive_up", True))
            target = kpi.get("target")
            target_html = f"<span style='color: #6b7280; font-size: 11px;'>Meta: {target}{kpi.get('unit', '')}</span>" if target else ""
            kpis_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{kpi.get('name', '')}</strong>
                    <br>{target_html}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center; font-size: 18px; font-weight: bold;">
                    {kpi.get('value', 0)}{kpi.get('unit', '')}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center; color: {trend_color};">
                    {_trend_icon(trend)} {abs(trend_pct):.1f}%
                </td>
            </tr>
            """
        
        departments_html = ""
        for dept in department_breakdown[:6]:
            fill_rate = dept.get("fill_rate", 0)
            bar_color = "#16a34a" if fill_rate >= 80 else "#f59e0b" if fill_rate >= 50 else "#dc2626"
            departments_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                    <strong>{dept.get('department', 'Departamento')}</strong>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {dept.get('hires', 0)}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                    {dept.get('open_positions', 0)}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; width: 120px;">
                    <div style="background-color: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background-color: {bar_color}; height: 100%; width: {fill_rate}%;"></div>
                    </div>
                    <span style="font-size: 11px; color: #6b7280;">{fill_rate:.0f}%</span>
                </td>
            </tr>
            """
        
        predictions_html = ""
        if predictions:
            pred_items = ""
            for pred in predictions[:4]:
                confidence = pred.get("confidence", 0) * 100
                trend = pred.get("trend", "stable")
                trend_color = _trend_color(trend)
                pred_items += f"""
                <div style="background-color: #faf5ff; border-left: 3px solid #8b5cf6; padding: 12px; margin: 8px 0; border-radius: 0 6px 6px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>{pred.get('metric_name', 'Métrica')}</strong>
                        <span style="background-color: #8b5cf6; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">
                            {confidence:.0f}% confiança
                        </span>
                    </div>
                    <p style="margin: 4px 0; font-size: 13px; color: #4b5563;">
                        Atual: <strong>{pred.get('current_value', 0)}</strong> → 
                        Previsto: <strong style="color: {trend_color};">{pred.get('predicted_value', 0)}</strong>
                    </p>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280; font-style: italic;">
                        {pred.get('recommendation', '')}
                    </p>
                </div>
                """
            predictions_html = f"""
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">🔮 Previsões da LIA</h3>
                {pred_items}
            </div>
            """
        
        recommendations_html = ""
        if strategic_recommendations:
            rec_items = ""
            for i, rec in enumerate(strategic_recommendations[:5], 1):
                rec_items += f"""
                <div style="display: flex; margin: 10px 0;">
                    <span style="background-color: #1f2937; color: white; min-width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; margin-right: 12px;">
                        {i}
                    </span>
                    <p style="margin: 0; flex: 1;">{rec}</p>
                </div>
                """
            recommendations_html = f"""
            <div style="margin: 24px 0; background-color: #fef3c7; border-radius: 8px; padding: 16px;">
                <h3 style="color: #92400e; margin: 0 0 12px 0;">📌 Recomendações Estratégicas</h3>
                {rec_items}
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; max-width: 750px; margin: 0 auto; padding: 20px; background-color: #f3f4f6;">
    <div style="background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); color: white; padding: 35px; text-align: center;">
            <h1 style="margin: 0; font-size: 26px;">📈 Relatório Mensal Executivo</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 16px;">{period}</p>
            <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 12px;">Gerado em {generated_at}</p>
        </div>
        
        <div style="padding: 24px;">
            <div style="margin-bottom: 24px;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">📋 Resumo Executivo</h3>
                <table style="width: 100%; border-collapse: separate; border-spacing: 8px;">
                    <tr>
                        {summary_cards}
                    </tr>
                </table>
            </div>
            
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">📊 Indicadores Estratégicos</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #fafafa; border-radius: 8px;">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 12px; text-align: left; font-size: 12px; color: #6b7280;">Indicador</th>
                            <th style="padding: 12px; text-align: center; font-size: 12px; color: #6b7280;">Valor</th>
                            <th style="padding: 12px; text-align: center; font-size: 12px; color: #6b7280;">Variação</th>
                        </tr>
                    </thead>
                    <tbody>
                        {kpis_html}
                    </tbody>
                </table>
            </div>
            
            <div style="margin: 24px 0;">
                <h3 style="color: #1f2937; margin-bottom: 12px;">🏢 Performance por Departamento</h3>
                <table style="width: 100%; border-collapse: collapse; background-color: #fafafa; border-radius: 8px;">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 10px; text-align: left; font-size: 12px; color: #6b7280;">Departamento</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Contratações</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Vagas Abertas</th>
                            <th style="padding: 10px; text-align: center; font-size: 12px; color: #6b7280;">Taxa de Fechamento</th>
                        </tr>
                    </thead>
                    <tbody>
                        {departments_html}
                    </tbody>
                </table>
            </div>
            
            {predictions_html}
            
            {recommendations_html}
            
            <div style="text-align: center; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <a href="#" style="display: inline-block; background-color: #1f2937; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-right: 8px;">
                    Ver Analytics Completo
                </a>
                <a href="#" style="display: inline-block; background-color: #f3f4f6; color: #1f2937; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                    Exportar PDF
                </a>
            </div>
        </div>
        
        <div style="background-color: #1f2937; color: white; padding: 16px; text-align: center; font-size: 12px;">
            <p style="margin: 0; opacity: 0.9;">Relatório gerado automaticamente pela LIA - Inteligência Artificial de Recrutamento</p>
            <p style="margin: 4px 0 0 0; opacity: 0.7;">{company_name}</p>
        </div>
    </div>
</body>
</html>
"""


report_templates = ReportTemplates()
