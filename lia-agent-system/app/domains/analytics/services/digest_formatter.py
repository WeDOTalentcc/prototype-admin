"""
Digest Formatters — Strategy pattern for multi-channel digest delivery.

Each formatter transforms a structured digest dict into the format
required by its target channel:
- TeamsDigestFormatter  → Adaptive Card JSON payload
- ChatDigestFormatter   → Markdown message for ProactiveService
- BellDigestFormatter   → Short title + action_url for bell notification
"""
from abc import ABC, abstractmethod
from typing import Any

from app.shared.pii_masking import get_masked_logger

logger = get_masked_logger(__name__)


class DigestFormatter(ABC):

    @abstractmethod
    def format(self, digest: dict[str, Any]) -> dict[str, Any]:
        ...


class BellDigestFormatter(DigestFormatter):

    def format(self, digest: dict[str, Any]) -> dict[str, Any]:
        pipeline = digest.get("pipeline_health", {})
        at_risk = digest.get("vagas_em_risco", {})
        compliance = digest.get("compliance_summary", {})

        pipeline.get("total_active_jobs", 0)
        screened = pipeline.get("candidates_screened_week", 0)
        risk_count = at_risk.get("count", 0)
        compliance_status = compliance.get("status", "ok")

        parts = []
        if risk_count > 0:
            parts.append(f"{risk_count} vaga(s) precisam de atenção")
        parts.append(f"pipeline com {screened} triados")
        parts.append(f"compliance {'OK' if compliance_status == 'ok' else 'requer atenção'}")

        message = ", ".join(parts) + "."

        return {
            "title": "Resumo Semanal Disponível",
            "message": f"Seu resumo semanal está pronto. {message}",
            "action_url": "/chat",
            "action_label": "Ver no Chat",
        }


class ChatDigestFormatter(DigestFormatter):

    def format(self, digest: dict[str, Any]) -> dict[str, Any]:
        name = digest.get("recruiter_name", "").split()[0] if digest.get("recruiter_name") else "Recrutador"
        period = digest.get("period", {})
        pipeline = digest.get("pipeline_health", {})
        at_risk = digest.get("vagas_em_risco", {})
        compliance = digest.get("compliance_summary", {})
        optimization = digest.get("optimization_insights", {})
        patterns = digest.get("patterns_learned", {})

        lines: list[str] = []
        lines.append(f"Bom dia, {name}. Preparei o resumo da sua semana de recrutamento ({period.get('start', '')} a {period.get('end', '')}).")
        lines.append("")

        lines.append("**Pipeline**")
        active = pipeline.get("total_active_jobs", 0)
        screened = pipeline.get("candidates_screened_week", 0)
        interviews = pipeline.get("interviews_scheduled", 0)
        lines.append(f"- {active} vagas ativas, {screened} candidatos triados, {interviews} entrevistas agendadas")
        conv = pipeline.get("conversion_rate")
        conv_change = pipeline.get("conversion_change")
        if conv is not None and conv_change is not None:
            direction = "subiu" if conv_change > 0 else "caiu"
            lines.append(f"- Taxa de conversão triagem→entrevista {direction} para {conv}%")
        lines.append("")

        risk_jobs = at_risk.get("jobs", [])
        if risk_jobs:
            lines.append(f"**{len(risk_jobs)} vaga(s) precisam de atenção**")
            for job in risk_jobs:
                severity_label = "CRÍTICO" if job.get("severity") == "critical" else "atenção"
                title = job.get("title", "Vaga")
                company = job.get("company", "")
                reason = job.get("reason", "")
                label = f"{title} — {company}" if company else title
                lines.append(f"- [{severity_label}] {label}: {reason}")
            lines.append("")

        lines.append("**Compliance e Fairness**")
        lines.append(f"- {compliance.get('message', 'Sem dados disponíveis.')}")
        lines.append("")

        tests = optimization.get("tests", [])
        if tests:
            lines.append("**Otimização**")
            for t in tests:
                test_name = t.get("test_name", "")
                status = t.get("status", "in_progress")
                if status == "concluded":
                    lines.append(f"- A/B test \"{test_name}\" concluído — variante vencedora: {t.get('winner_variant', '?')}")
                else:
                    obs = t.get("total_observations", 0)
                    lines.append(f"- A/B test \"{test_name}\" em andamento ({obs} observações)")
            lines.append("")

        top_patterns = patterns.get("top_patterns", [])
        if top_patterns:
            total = patterns.get("total_patterns", 0)
            lines.append(f"**Aprendizado** ({total} padrões ativos)")
            for p in top_patterns:
                lines.append(f"- {p.get('type', 'padrão')}: confiança {round(p.get('confidence', 0) * 100)}%, {p.get('sample_size', 0)} amostras")
            lines.append("")

        return {
            "title": "Resumo Semanal — Suas Vagas",
            "message": "\n".join(lines),
        }


class TeamsDigestFormatter(DigestFormatter):

    def format(self, digest: dict[str, Any]) -> dict[str, Any]:
        name = digest.get("recruiter_name", "").split()[0] if digest.get("recruiter_name") else "Recrutador"
        period = digest.get("period", {})
        pipeline = digest.get("pipeline_health", {})
        at_risk = digest.get("vagas_em_risco", {})
        compliance = digest.get("compliance_summary", {})
        optimization = digest.get("optimization_insights", {})

        body: list[dict[str, Any]] = []

        body.append({
            "type": "TextBlock",
            "text": "Resumo Semanal — Suas Vagas",
            "weight": "Bolder",
            "size": "Medium",
        })
        body.append({
            "type": "TextBlock",
            "text": f"Olá {name}, aqui está o panorama da semana ({period.get('start', '')} a {period.get('end', '')}).",
            "wrap": True,
            "spacing": "Small",
        })

        active = pipeline.get("total_active_jobs", 0)
        screened = pipeline.get("candidates_screened_week", 0)
        interviews = pipeline.get("interviews_scheduled", 0)

        body.append({
            "type": "ColumnSet",
            "columns": [
                self._metric_column(str(active), "vagas ativas"),
                self._metric_column(str(screened), "candidatos triados"),
                self._metric_column(str(interviews), "entrevistas"),
            ],
            "spacing": "Medium",
        })

        risk_jobs = at_risk.get("jobs", [])
        if risk_jobs:
            body.append({
                "type": "TextBlock",
                "text": f"⚠️ {len(risk_jobs)} vaga(s) em risco",
                "weight": "Bolder",
                "spacing": "Medium",
                "color": "Attention",
            })
            for job in risk_jobs[:3]:
                title = job.get("title", "Vaga")
                company = job.get("company", "")
                reason = job.get("reason", "")
                severity = job.get("severity", "attention")
                label = f"{title} — {company}" if company else title
                color = "Attention" if severity == "critical" else "Warning"
                body.append({
                    "type": "TextBlock",
                    "text": f"**{label}**  \n{reason}",
                    "wrap": True,
                    "color": color,
                    "spacing": "Small",
                })

        comp_status = compliance.get("status", "ok")
        comp_icon = "✅" if comp_status == "ok" else "⚠️"
        body.append({
            "type": "TextBlock",
            "text": f"{comp_icon} Compliance: {compliance.get('message', 'OK')}",
            "wrap": True,
            "spacing": "Medium",
        })

        tests = optimization.get("tests", [])
        if tests:
            test_lines = []
            for t in tests:
                if t.get("status") == "concluded":
                    test_lines.append(f"- \"{t['test_name']}\" concluído (vencedor: {t.get('winner_variant', '?')})")
                else:
                    test_lines.append(f"- \"{t['test_name']}\" em andamento")
            if test_lines:
                body.append({
                    "type": "TextBlock",
                    "text": "🔬 Otimização\n" + "\n".join(test_lines),
                    "wrap": True,
                    "spacing": "Medium",
                })

        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": body,
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "Ver detalhes completos no Chat LIA →",
                                "url": "https://app.wedotalent.com/chat",
                            }
                        ],
                    },
                }
            ],
        }

        return card

    @staticmethod
    def _metric_column(value: str, label: str) -> dict[str, Any]:
        return {
            "type": "Column",
            "width": "stretch",
            "items": [
                {
                    "type": "TextBlock",
                    "text": value,
                    "weight": "Bolder",
                    "size": "ExtraLarge",
                    "horizontalAlignment": "Center",
                },
                {
                    "type": "TextBlock",
                    "text": label,
                    "size": "Small",
                    "horizontalAlignment": "Center",
                    "isSubtle": True,
                },
            ],
        }
