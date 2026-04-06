"""
Teams Adaptive Card Renderer.
Converts LIA orchestrator responses into rich Adaptive Cards for Microsoft Teams.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# LIA brand color
LIA_COLOR = "#6366F1"
# Platform base URL for deep links — set WEDOTALENT_PLATFORM_URL env var in production
import os as _os

PLATFORM_URL = _os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com").rstrip("/")
SUCCESS_COLOR = "#22C55E"
WARNING_COLOR = "#F59E0B"
ERROR_COLOR = "#EF4444"
NEUTRAL_COLOR = "#6B7280"


class TeamsCardRenderer:
    """
    Renders orchestrator results as Teams Adaptive Cards.
    Provides the same richness as the web UI but in card format.
    """

    def render(self, result: dict[str, Any], source_text: str = "", deep_link_path: str = "") -> dict[str, Any] | None:
        """
        Main entry point. Returns Adaptive Card JSON or None for plain text.
        """
        try:
            # Execution plan response (multi-step plan)
            if result.get("execution_plan"):
                return self._render_plan_card(result)

            # CV screening result
            if result.get("agent_type") == "cv_screening" or result.get("candidate_id"):
                return self._render_cv_screening_card(result)

            # Candidate list in structured_data or result.data
            candidates = self._extract_candidates(result)
            if candidates:
                return self._render_candidates_card(result, candidates)

            # Confirmation needed
            if result.get("requires_user_input") or result.get("needs_confirmation"):
                return self._render_confirmation_card(result)

            # Default: rich text card (better than plain text)
            message = result.get("message") or result.get("response") or result.get("content", "")
            if message:
                return self._render_text_card(message, result.get("suggested_prompts") or result.get("next_actions") or [], deep_link_path=deep_link_path)

            return None

        except Exception as e:
            logger.error(f"[TeamsCardRenderer] Render error: {e}", exc_info=True)
            return None

    # --- Card builders -------------------------------------------------------

    def _render_text_card(
        self,
        text: str,
        suggestions: list = [],
        deep_link_path: str = "",
        show_feedback: bool = True,
    ) -> dict[str, Any]:
        """Rich text response card with follow-up suggestion buttons + 👍👎 feedback + deep link."""
        body = [
            {
                "type": "TextBlock",
                "text": text,
                "wrap": True,
                "size": "Default",
            }
        ]

        actions = []
        for s in suggestions[:3]:
            label = s if isinstance(s, str) else s.get("label", str(s))
            value = s if isinstance(s, str) else s.get("action", str(s))
            actions.append({
                "type": "Action.Submit",
                "title": label[:40],
                "data": {"message": value},
            })

        # Feedback buttons (👍👎)
        if show_feedback:
            actions.append({
                "type": "Action.Submit",
                "title": "👍 Útil",
                "style": "positive",
                "data": {"feedback": "positive", "feedback_text": text[:100]},
            })
            actions.append({
                "type": "Action.Submit",
                "title": "👎 Melhorar",
                "data": {"feedback": "negative", "feedback_text": text[:100]},
            })

        # Deep link to platform
        if deep_link_path:
            full_url = f"{PLATFORM_URL}{deep_link_path}"
            actions.append({
                "type": "Action.OpenUrl",
                "title": "🔗 Ver na plataforma",
                "url": full_url,
            })

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
        if actions:
            card["actions"] = actions
        return card

    def _render_plan_card(self, result: dict[str, Any]) -> dict[str, Any]:
        """Multi-step plan execution card — mirrors PlanProgressCard from web UI."""
        plan = result.get("execution_plan", {})
        steps = plan.get("steps", [])
        status = plan.get("status", "completed")
        plan.get("pattern", "")
        message = result.get("message") or result.get("response", "Plano executado.")

        status_emoji = {"completed": "✅", "partial": "⚠️", "failed": "❌"}.get(status, "✅")

        body = [
            {
                "type": "TextBlock",
                "text": f"{status_emoji} **Plano executado**",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Accent",
            },
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True,
                "spacing": "Small",
            },
        ]

        if steps:
            body.append({
                "type": "TextBlock",
                "text": "**Etapas:**",
                "weight": "Bolder",
                "spacing": "Medium",
            })
            for step in steps:
                step_status = step.get("status", "completed")
                icon = {"completed": "✅", "failed": "❌", "skipped": "⏭️", "running": "⏳"}.get(step_status, "✅")
                action_id = step.get("action_id", "")
                body.append({
                    "type": "TextBlock",
                    "text": f"{icon} {self._action_label(action_id)}",
                    "wrap": True,
                    "spacing": "Small",
                    "isSubtle": step_status == "skipped",
                })
                if step.get("skip_reason"):
                    body.append({
                        "type": "TextBlock",
                        "text": f"  ↳ {step['skip_reason']}",
                        "isSubtle": True,
                        "size": "Small",
                        "spacing": "None",
                    })

        # Summary facts
        completed = sum(1 for s in steps if s.get("status") == "completed")
        skipped = sum(1 for s in steps if s.get("status") == "skipped")
        failed = sum(1 for s in steps if s.get("status") == "failed")

        facts = [{"title": "Concluídas", "value": str(completed)}]
        if skipped:
            facts.append({"title": "Puladas", "value": str(skipped)})
        if failed:
            facts.append({"title": "Falhas", "value": str(failed)})

        if facts:
            body.append({
                "type": "FactSet",
                "facts": facts,
                "spacing": "Medium",
            })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }

    def _render_candidates_card(self, result: dict[str, Any], candidates: list[dict]) -> dict[str, Any]:
        """Candidate list card with scores and action buttons."""
        message = result.get("message") or result.get("response") or result.get("content", "")

        body: list[dict] = []

        if message:
            body.append({
                "type": "TextBlock",
                "text": message[:300],
                "wrap": True,
            })

        body.append({
            "type": "TextBlock",
            "text": f"**{len(candidates)} candidato(s) encontrado(s)**",
            "weight": "Bolder",
            "spacing": "Medium",
        })

        for i, c in enumerate(candidates[:5]):
            name = c.get("name") or c.get("candidate_name", f"Candidato {i+1}")
            score = c.get("score") or c.get("match_score") or c.get("bars_score", 0)
            stage = c.get("stage") or c.get("current_stage", "")
            skills = c.get("skills") or []
            skills_text = ", ".join(skills[:3]) if skills else ""

            score_bar = self._score_bar(score) if score else ""
            subtitle_parts = []
            if score:
                subtitle_parts.append(f"Score: {score:.0f}% {score_bar}")
            if stage:
                subtitle_parts.append(f"Etapa: {stage}")
            if skills_text:
                subtitle_parts.append(f"Skills: {skills_text}")

            body.append({
                "type": "Container",
                "style": "emphasis" if i == 0 else "default",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"**{i+1}. {name}**",
                                        "weight": "Bolder",
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": " | ".join(subtitle_parts) if subtitle_parts else "",
                                        "isSubtle": True,
                                        "size": "Small",
                                        "spacing": "None",
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "spacing": "Small",
            })

        actions = [
            {
                "type": "Action.Submit",
                "title": "Ver detalhes",
                "data": {"message": "mostre detalhes dos candidatos encontrados"},
            },
            {
                "type": "Action.Submit",
                "title": "Comparar perfis",
                "data": {"message": "compare os perfis em detalhes"},
            },
        ]
        if len(candidates) > 0:
            actions.append({
                "type": "Action.Submit",
                "title": "Agendar entrevistas",
                "data": {"message": "agende entrevistas com os top candidatos"},
            })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
            "actions": actions,
        }

    def _render_cv_screening_card(self, result: dict[str, Any]) -> dict[str, Any]:
        """CV screening result card with score bar and actions."""
        candidate_name = result.get("candidate_name") or result.get("name", "Candidato")
        job_title = result.get("job_title") or result.get("vacancy_title", "")
        match_score = result.get("match_score") or 0
        recommendation = result.get("recommendation") or ""
        message = result.get("message") or ""
        candidate_id = result.get("candidate_id") or ""
        success = result.get("success", True)


        body = [
            {
                "type": "TextBlock",
                "text": f"📋 **Triagem de CV — {candidate_name}**",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Accent",
            },
        ]

        if job_title:
            body.append({
                "type": "TextBlock",
                "text": f"Vaga: **{job_title}**",
                "spacing": "Small",
                "isSubtle": True,
            })

        if match_score:
            body.append({
                "type": "FactSet",
                "facts": [
                    {"title": "Score de match", "value": f"{match_score:.0f}% {self._score_bar(match_score)}"},
                    {"title": "Recomendação", "value": recommendation or "—"},
                ],
                "spacing": "Medium",
            })

        if message:
            body.append({
                "type": "TextBlock",
                "text": message[:500],
                "wrap": True,
                "spacing": "Medium",
            })

        actions = []
        if success and candidate_id:
            actions = [
                {
                    "type": "Action.Submit",
                    "title": "✅ Avançar candidato",
                    "style": "positive",
                    "data": {
                        "action": "advance_candidate",
                        "candidate_id": candidate_id,
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "📅 Agendar entrevista",
                    "data": {
                        "message": f"agende uma entrevista com {candidate_name}",
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Reprovar",
                    "style": "destructive",
                    "data": {
                        "action": "reject_candidate",
                        "candidate_id": candidate_id,
                    },
                },
            ]

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
        if actions:
            card["actions"] = actions
        return card

    def _render_confirmation_card(self, result: dict[str, Any]) -> dict[str, Any]:
        """Confirmation request card with Confirm/Cancel buttons."""
        message = result.get("message") or result.get("confirmation_message", "Confirma a ação?")
        pending_id = result.get("pending_action_id") or ""

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ **Confirmação necessária**",
                    "weight": "Bolder",
                    "color": "Warning",
                },
                {
                    "type": "TextBlock",
                    "text": message,
                    "wrap": True,
                    "spacing": "Medium",
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Confirmar",
                    "style": "positive",
                    "data": {"message": "confirmar", "pending_action_id": pending_id},
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Cancelar",
                    "style": "destructive",
                    "data": {"message": "cancelar", "pending_action_id": pending_id},
                },
            ],
        }

    def render_notification_card(
        self,
        title: str,
        body_text: str,
        actions: list[dict] = [],
        color: str = "Accent",
        emoji: str = "🔔",
        deep_link_path: str = "",
    ) -> dict[str, Any]:
        """Generic proactive notification card."""
        body_items = [
            {
                "type": "TextBlock",
                "text": f"{emoji} **{title}**",
                "weight": "Bolder",
                "size": "Medium",
                "color": color,
            },
            {
                "type": "TextBlock",
                "text": body_text,
                "wrap": True,
                "spacing": "Small",
            },
        ]

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body_items,
        }
        if actions:
            card["actions"] = actions
        return card

    def render_new_candidate_card(
        self,
        candidate_name: str,
        job_title: str,
        candidate_id: str,
        vacancy_id: str,
        estimated_score: float | None = None,
        deep_link_path: str = "",
    ) -> dict[str, Any]:
        """Proactive card: new candidate applied."""
        score_text = f" | Score estimado: **{estimated_score:.0f}%** {self._score_bar(estimated_score)}" if estimated_score else ""
        return self.render_notification_card(
            title="Novo candidato",
            body_text=f"**{candidate_name}** aplicou para **{job_title}**{score_text}",
            emoji="👤",
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "🔍 Analisar CV",
                    "style": "positive",
                    "data": {
                        "message": f"analise o CV de {candidate_name} para a vaga de {job_title}",
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "⚡ Triagem WSI",
                    "data": {
                        "action": "run_wsi",
                        "candidate_id": candidate_id,
                        "vacancy_id": vacancy_id,
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "👁️ Ver perfil",
                    "data": {
                        "message": f"mostre o perfil completo de {candidate_name}",
                    },
                },
            ],
        )

    def render_stalled_pipeline_card(
        self,
        vacancy_title: str,
        candidates_count: int,
        days_stalled: int,
        vacancy_id: str,
        deep_link_path: str = "",
    ) -> dict[str, Any]:
        """Proactive card: pipeline stalled."""
        return self.render_notification_card(
            title="Pipeline parado",
            body_text=(
                f"A vaga **{vacancy_title}** tem **{candidates_count} candidato(s)** "
                f"sem movimentação há **{days_stalled} dias**.\n\n"
                f"Quer que eu faça a triagem automática e traga os melhores para revisão?"
            ),
            emoji="⏸️",
            color="Warning",
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "🔄 Triar automaticamente",
                    "style": "positive",
                    "data": {"message": f"faça triagem automática dos candidatos da vaga {vacancy_title}"},
                },
                {
                    "type": "Action.Submit",
                    "title": "📋 Ver candidatos",
                    "data": {"message": f"liste os candidatos parados da vaga {vacancy_title}"},
                },
                {
                    "type": "Action.Submit",
                    "title": "🔕 Adiar 3 dias",
                    "data": {"action": "snooze", "vacancy_id": vacancy_id, "days": 3},
                },
            ],
        )

    def render_deadline_card(
        self,
        vacancy_title: str,
        days_remaining: int,
        candidates_in_pipeline: int,
        vacancy_id: str,
        deep_link_path: str = "",
    ) -> dict[str, Any]:
        """Proactive card: vacancy deadline approaching."""
        urgency = "🔴" if days_remaining <= 3 else "🟡"
        return self.render_notification_card(
            title=f"Prazo se aproximando — {vacancy_title}",
            body_text=(
                f"{urgency} **{days_remaining} dia(s)** restante(s) para encerrar a vaga.\n\n"
                f"**{candidates_in_pipeline}** candidato(s) ainda no pipeline.\n\n"
                f"Precisa de ajuda para acelerar o processo?"
            ),
            emoji="⏰",
            color="Attention" if days_remaining <= 3 else "Warning",
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "📊 Ver status completo",
                    "data": {"message": f"mostre o status completo da vaga {vacancy_title}"},
                },
                {
                    "type": "Action.Submit",
                    "title": "🚀 Acelerar processo",
                    "data": {"message": f"o que posso fazer para acelerar o fechamento da vaga {vacancy_title}"},
                },
            ],
        )

    def render_screening_complete_card(
        self,
        candidate_name: str,
        job_title: str,
        match_score: float,
        recommendation: str,
        candidate_id: str,
        deep_link_path: str = "",
    ) -> dict[str, Any]:
        """Proactive card: WSI/BARS screening completed."""
        score_bar = self._score_bar(match_score)
        result_emoji = "✅" if match_score >= 70 else "⚠️" if match_score >= 40 else "❌"
        return self.render_notification_card(
            title=f"Triagem concluída — {candidate_name}",
            body_text=(
                f"{result_emoji} Score: **{match_score:.0f}%** {score_bar}\n"
                f"Vaga: **{job_title}**\n"
                f"Recomendação: **{recommendation}**"
            ),
            emoji="🧪",
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "✅ Avançar",
                    "style": "positive",
                    "data": {"action": "advance_candidate", "candidate_id": candidate_id},
                },
                {
                    "type": "Action.Submit",
                    "title": "📋 Ver relatório",
                    "data": {"message": f"mostre o relatório de triagem de {candidate_name}"},
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Reprovar",
                    "style": "destructive",
                    "data": {"action": "reject_candidate", "candidate_id": candidate_id},
                },
            ],
        )

    # --- Helpers -------------------------------------------------------------

    def _extract_candidates(self, result: dict[str, Any]) -> list[dict]:
        """Extract candidate list from various result structures."""
        # Try structured_data
        sd = result.get("structured_data") or {}
        if isinstance(sd, dict):
            for key in ("candidates", "top_candidates", "results", "matches"):
                if key in sd and isinstance(sd[key], list):
                    return sd[key]

        # Try result.data
        data = (result.get("result") or {}).get("data") or {}
        if isinstance(data, dict):
            for key in ("candidates", "search_results", "top_candidates"):
                if key in data and isinstance(data[key], list):
                    return data[key]

        # Try direct search_results
        sr = result.get("search_results") or []
        if sr:
            return sr

        return []

    def _score_bar(self, score: float) -> str:
        """Visual score bar using unicode blocks."""
        if not score:
            return ""
        filled = round(score / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

    def _action_label(self, action_id: str) -> str:
        """Human-readable label for action IDs."""
        labels = {
            "search_candidates": "Buscar candidatos",
            "compare_candidates": "Comparar perfis",
            "run_wsi_screening": "Triagem WSI",
            "run_bars_scoring": "Score BARS",
            "add_candidate_to_vacancy": "Adicionar à vaga",
            "add_to_vacancy": "Adicionar à vaga",
            "parse_and_create_candidate": "Cadastrar candidato",
            "create_and_screen_candidate": "Triagem completa",
            "schedule_interview": "Agendar entrevista",
            "send_notification": "Enviar notificação",
            "generate_report": "Gerar relatório",
            "analyze_cv_match": "Analisar match",
        }
        return labels.get(action_id, action_id.replace("_", " ").title())


    # -------------------------------------------------------------------------
    # Context-aware greeting card (Notion AI-style)
    # -------------------------------------------------------------------------

    _TEAMS_SUGGESTIONS = {
        "vaga": [
            ("Buscar candidatos", "Busca os melhores candidatos para esta vaga"),
            ("Saude do pipeline", "Como esta o pipeline desta vaga?"),
            ("Benchmark salarial", "Qual o benchmark salarial para esta posicao?"),
            ("Relatorio da vaga", "Gera um relatorio completo desta vaga"),
        ],
        "candidato": [
            ("Comparar candidatos", "Compara este candidato com os outros finalistas"),
            ("Gerar parecer", "Gera um parecer tecnico completo deste candidato"),
            ("Disparar triagem", "Dispara a triagem WSI para este candidato"),
            ("Agendar entrevista", "Quero agendar uma entrevista com este candidato"),
        ],
        "pipeline": [
            ("Vagas travadas", "Quais vagas estao travadas no pipeline?"),
            ("Taxa de conversao", "Qual a taxa de conversao entre as etapas?"),
            ("Candidatos prontos", "Quais candidatos estao prontos para avancar?"),
        ],
        "home": [
            ("Resumo do dia", "Me de um resumo das atividades de hoje"),
            ("Vagas criticas", "Quais vagas estao em estado critico?"),
            ("Pipeline geral", "Como esta a saude do pipeline?"),
            ("Criar vaga", "Quero criar uma nova vaga com a LIA"),
        ],
    }

    _PAGE_ICONS = {
        "vaga": "Briefcase", "candidato": "User", "pipeline": "GitBranch",
        "triagem": "ClipboardCheck", "relatorios": "BarChart2", "home": "Home",
    }
    _PAGE_NAMES = {
        "vaga": "Vaga", "candidato": "Candidato", "pipeline": "Pipeline",
        "triagem": "Triagem", "relatorios": "Relatorios", "home": "Painel",
    }

    def render_context_greeting_card(
        self,
        page: str = "home",
        entity_name: str | None = None,
        user_name: str | None = None,
    ) -> dict[str, Any]:
        from datetime import datetime as _dt
        hour = _dt.now().hour
        greeting = "Bom dia" if hour < 12 else ("Boa tarde" if hour < 18 else "Boa noite")
        if user_name:
            greeting = f"{greeting}, {user_name.split()[0]}"

        page_key = page.lower().strip()
        page_label = self._PAGE_NAMES.get(page_key, page_key.capitalize())
        badge_text = page_label + (f": {entity_name}" if entity_name else "")

        suggestions = self._TEAMS_SUGGESTIONS.get(page_key, self._TEAMS_SUGGESTIONS["home"])

        body = [
            {
                "type": "TextBlock",
                "text": f"**{greeting}**",
                "size": "Medium",
                "weight": "Bolder",
                "color": "Accent",
            },
            {
                "type": "Container",
                "style": "emphasis",
                "bleed": True,
                "items": [{
                    "type": "TextBlock",
                    "text": badge_text,
                    "size": "Small",
                    "weight": "Bolder",
                    "spacing": "None",
                }],
                "padding": {"top": "Small", "bottom": "Small", "left": "Small", "right": "Small"},
            },
            {
                "type": "TextBlock",
                "text": "O que voce quer fazer?",
                "size": "Default",
                "spacing": "Medium",
                "wrap": True,
            },
        ]

        actions = [
            {
                "type": "Action.Submit",
                "title": label[:30],
                "data": {"message": prompt},
            }
            for label, prompt in suggestions[:4]
        ]

        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": body,
            "actions": actions,
            "msteams": {"width": "Full"},
        }


teams_card_renderer = TeamsCardRenderer()
