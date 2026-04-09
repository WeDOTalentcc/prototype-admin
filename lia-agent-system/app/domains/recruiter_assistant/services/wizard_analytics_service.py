"""
LIA Wizard Analytics Service - Status queries and analytical commands for the Job Wizard.

Handles wizard-specific analytical queries:
- "Como está a vaga?" (job status summary)
- "O que falta preencher?" (missing fields)
- "Quanto falta para publicar?" (completion percentage)
- "Resume o que já coletamos" (collected data summary)

Uses LLMProviderFactory for all LLM calls (Task #93 migration).
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

WIZARD_STAGE_NAMES = {
    "input-evaluation": "Informações Básicas",
    "salary": "Remuneração e Benefícios",
    "competencies": "Competências e Skills",
    "wsi-questions": "Perguntas de Triagem WSI",
    "review-publish": "Revisão e Publicação",
}

STAGE_REQUIRED_FIELDS = {
    "input-evaluation": ["title", "department", "seniority_level", "work_model", "location"],
    "salary": ["salary_range"],
    "competencies": ["required_skills"],
    "wsi-questions": [],
    "review-publish": [],
}


class WizardAnalyticsCommandType:
    STATUS_VAGA = "status_vaga"
    CAMPOS_FALTANTES = "campos_faltantes"
    COMPLETUDE = "completude"
    RESUMO_COLETADO = "resumo_coletado"
    SUGESTAO_PROXIMO = "sugestao_proximo"
    ANALISE_GERAL = "analise_geral"


ANALYTICS_KEYWORDS = {
    WizardAnalyticsCommandType.STATUS_VAGA: [
        "como está", "status", "situação", "como vai", "andamento",
    ],
    WizardAnalyticsCommandType.CAMPOS_FALTANTES: [
        "o que falta", "faltando", "missing", "incompleto", "pendente",
    ],
    WizardAnalyticsCommandType.COMPLETUDE: [
        "quanto falta", "percentual", "completude", "progresso", "completion",
    ],
    WizardAnalyticsCommandType.RESUMO_COLETADO: [
        "resumo", "resumir", "o que temos", "coletado", "preenchido",
    ],
    WizardAnalyticsCommandType.SUGESTAO_PROXIMO: [
        "próximo passo", "o que fazer", "sugestão", "recomendação",
    ],
}


def detect_wizard_analytics_command(message: str) -> tuple[str, float] | None:
    msg_lower = message.lower().strip()

    for cmd_type, keywords in ANALYTICS_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                score = len(kw) / max(len(msg_lower), 1)
                confidence = max(0.7, min(score * 3, 0.95))
                return cmd_type, confidence

    return None


class WizardAnalyticsService:
    """Service for analytical queries about the job being created in the wizard."""

    def analyze_completion(
        self,
        collected_data: dict[str, Any],
        current_stage: str,
    ) -> dict[str, Any]:
        all_required = []
        for stage, fields in STAGE_REQUIRED_FIELDS.items():
            all_required.extend(fields)

        filled = [f for f in all_required if collected_data.get(f)]
        missing = [f for f in all_required if not collected_data.get(f)]
        total = max(len(all_required), 1)
        pct = round(len(filled) / total * 100, 1)

        optional_filled = [
            k for k, v in collected_data.items() if k not in all_required and v
        ]

        return {
            "completion_pct": pct,
            "filled_required": filled,
            "missing_required": missing,
            "optional_filled": optional_filled,
            "current_stage": current_stage,
            "current_stage_name": WIZARD_STAGE_NAMES.get(current_stage, current_stage),
            "can_publish": len(missing) == 0,
        }

    def build_status_response(
        self,
        collected_data: dict[str, Any],
        current_stage: str,
        command_type: str,
    ) -> str:
        analysis = self.analyze_completion(collected_data, current_stage)

        if command_type == WizardAnalyticsCommandType.STATUS_VAGA:
            return self._format_status(collected_data, analysis)
        elif command_type == WizardAnalyticsCommandType.CAMPOS_FALTANTES:
            return self._format_missing(analysis)
        elif command_type == WizardAnalyticsCommandType.COMPLETUDE:
            return self._format_completeness(analysis)
        elif command_type == WizardAnalyticsCommandType.RESUMO_COLETADO:
            return self._format_summary(collected_data, analysis)
        elif command_type == WizardAnalyticsCommandType.SUGESTAO_PROXIMO:
            return self._format_next_steps(analysis)
        else:
            return self._format_status(collected_data, analysis)

    def _format_status(self, collected: dict, analysis: dict) -> str:
        title = collected.get("title", "sem título")
        pct = analysis["completion_pct"]

        lines = [
            f"## 📋 Status da Vaga: {title}\n",
            f"**Progresso:** {pct}% completo",
            f"**Etapa atual:** {analysis['current_stage_name']}",
            "",
        ]

        if analysis["can_publish"]:
            lines.append("✅ **Pronta para publicação!**\n")
        else:
            lines.append(f"⚠️ **{len(analysis['missing_required'])} campos obrigatórios faltando**\n")
            for f in analysis["missing_required"]:
                lines.append(f"  - {self._field_label(f)}")

        lines.append(f"\n📊 {len(analysis['filled_required'])} obrigatórios preenchidos | {len(analysis['optional_filled'])} opcionais preenchidos")

        return "\n".join(lines)

    def _format_missing(self, analysis: dict) -> str:
        if not analysis["missing_required"]:
            return "✅ **Todos os campos obrigatórios estão preenchidos!** Você pode publicar a vaga."

        lines = [
            f"## ⚠️ Campos Faltantes ({len(analysis['missing_required'])})\n",
        ]
        for f in analysis["missing_required"]:
            stage = self._field_stage(f)
            lines.append(f"- **{self._field_label(f)}** (etapa: {WIZARD_STAGE_NAMES.get(stage, stage)})")

        lines.append("\n💡 Preencha estes campos para liberar a publicação.")
        return "\n".join(lines)

    def _format_completeness(self, analysis: dict) -> str:
        pct = analysis["completion_pct"]
        bar_len = 20
        filled_len = int(pct / 100 * bar_len)
        bar = "█" * filled_len + "░" * (bar_len - filled_len)

        lines = [
            "## 📊 Completude da Vaga\n",
            f"**{pct}%** `[{bar}]`\n",
            f"- ✅ {len(analysis['filled_required'])} campos obrigatórios preenchidos",
            f"- ❌ {len(analysis['missing_required'])} campos obrigatórios faltando",
            f"- ➕ {len(analysis['optional_filled'])} campos opcionais preenchidos",
        ]

        if analysis["can_publish"]:
            lines.append("\n🚀 **Vaga pronta para publicar!**")
        else:
            lines.append("\n⚠️ Complete os campos faltantes para publicar.")

        return "\n".join(lines)

    def _format_summary(self, collected: dict, analysis: dict) -> str:
        lines = [
            "## 📝 Resumo dos Dados Coletados\n",
        ]

        if not any(v for v in collected.values()):
            return "Ainda não coletamos dados. Vamos começar preenchendo as informações básicas da vaga!"

        field_groups = {
            "Informações Básicas": ["title", "department", "seniority_level", "work_model", "location"],
            "Remuneração": ["salary_range", "benefits"],
            "Competências": ["required_skills", "desired_skills", "responsibilities"],
            "Descrição": ["description", "requirements"],
        }

        for group_name, fields in field_groups.items():
            group_data = {f: collected.get(f) for f in fields if collected.get(f)}
            if group_data:
                lines.append(f"### {group_name}")
                for f, v in group_data.items():
                    if isinstance(v, list):
                        lines.append(f"- **{self._field_label(f)}:** {', '.join(str(x) for x in v[:5])}")
                    elif isinstance(v, dict):
                        lines.append(f"- **{self._field_label(f)}:** {json.dumps(v, ensure_ascii=False)[:100]}")
                    else:
                        lines.append(f"- **{self._field_label(f)}:** {str(v)[:100]}")
                lines.append("")

        lines.append(f"---\n📊 Completude: **{analysis['completion_pct']}%**")
        return "\n".join(lines)

    def _format_next_steps(self, analysis: dict) -> str:
        if analysis["can_publish"]:
            return (
                "## 🚀 Próximos Passos\n\n"
                "Todos os campos obrigatórios estão preenchidos! Você pode:\n"
                "1. **Revisar** os dados da vaga\n"
                "2. **Publicar** a vaga nas plataformas desejadas\n"
                "3. **Adicionar** informações opcionais para melhorar a qualidade"
            )

        lines = [
            "## 🔜 Próximos Passos\n",
            f"Faltam **{len(analysis['missing_required'])} campos** obrigatórios:\n",
        ]

        for i, f in enumerate(analysis["missing_required"][:5], 1):
            lines.append(f"{i}. Preencher **{self._field_label(f)}**")

        lines.append(
            "\n💡 Dica: Você pode me dizer as informações diretamente no chat que eu preencho para você!"
        )
        return "\n".join(lines)

    def _field_label(self, field: str) -> str:
        labels = {
            "title": "Título da Vaga",
            "department": "Departamento",
            "seniority_level": "Senioridade",
            "work_model": "Modelo de Trabalho",
            "location": "Localização",
            "salary_range": "Faixa Salarial",
            "required_skills": "Skills Obrigatórias",
            "desired_skills": "Skills Desejáveis",
            "responsibilities": "Responsabilidades",
            "description": "Descrição da Vaga",
            "requirements": "Requisitos",
            "benefits": "Benefícios",
        }
        return labels.get(field, field.replace("_", " ").title())

    def _field_stage(self, field: str) -> str:
        for stage, fields in STAGE_REQUIRED_FIELDS.items():
            if field in fields:
                return stage
        return "input-evaluation"


wizard_analytics = WizardAnalyticsService()
