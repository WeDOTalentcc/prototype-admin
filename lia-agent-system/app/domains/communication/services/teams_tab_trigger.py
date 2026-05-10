"""
Teams Tab Trigger Engine.

Evaluates behavioral events from the Teams Tab iframe and sends
proactive Adaptive Card messages when the recruiter attempts a
complex action that is better handled in the full platform.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Complex action registry
# Each key = event_type sent by the frontend tracker
# Value = (title, description, platform_path)
# ------------------------------------------------------------------ #
COMPLEX_ACTIONS: dict[str, tuple[str, str, str]] = {
    "click_create_job": (
        "Criar uma vaga completa",
        "Para criar uma vaga com todos os campos e configurações, use a plataforma completa.",
        "/jobs/new",
    ),
    "click_edit_pipeline": (
        "Configurar etapas do funil",
        "A configuração do pipeline de seleção está disponível na plataforma completa.",
        "/configuracoes/pipeline",
    ),
    "click_job_settings": (
        "Editar detalhes da vaga",
        "Para editar todos os detalhes e configurações da vaga, acesse a plataforma.",
        "/jobs/{id}/edit",
    ),
    "click_edit_candidate": (
        "Editar perfil do candidato",
        "A edição completa do perfil do candidato está disponível na plataforma.",
        "/candidates/{id}",
    ),
    "click_move_stage": (
        "Mover candidato no pipeline",
        "Para gerenciar etapas e avaliações do candidato, use a plataforma completa.",
        "/candidates/{id}",
    ),
    "click_send_feedback": (
        "Enviar feedback ao candidato",
        "O envio de feedback e comunicações está disponível na plataforma completa.",
        "/candidates",
    ),
    "prolonged_stay": (
        "Continuar no ambiente completo",
        "Você está navegando há algum tempo aqui. Prefere usar a plataforma completa?",
        "/",
    ),
    "click_dashboard_drilldown": (
        "Ver análise completa",
        "Para análises detalhadas e dashboards interativos, acesse a plataforma completa.",
        "/",
    ),
}


class TeamsTabTriggerEngine:
    """
    Evaluates iframe events and decides whether to send a proactive
    Teams message redirecting the recruiter to the full platform.
    """

    PLATFORM_URL_DEFAULT = "https://app.wedotalent.com"

    def __init__(self, platform_url: str | None = None):
        import os
        self.platform_url = (
            platform_url
            or os.environ.get("WEDOTALENT_PLATFORM_URL", self.PLATFORM_URL_DEFAULT)
        ).rstrip("/")

    def evaluate(
        self,
        event_type: str,
        entity_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Evaluate an event from the Teams Tab iframe.

        Returns an Adaptive Card payload if a proactive message should be
        sent, or None if no action is needed.
        """
        action = COMPLEX_ACTIONS.get(event_type)
        if not action:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"[TeamsTabTrigger] Event '{event_type}' is not a complex action — ignoring")
            return None

        title, description, path = action

        # Substitute entity_id into path if present (e.g., /jobs/{id}/edit)
        if entity_id and "{id}" in path:
            path = path.replace("{id}", entity_id)

        deep_link = f"{self.platform_url}{path}"

        card = self._build_card(title, description, deep_link)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[TeamsTabTrigger] Triggering proactive card for event='{event_type}', link='{deep_link}'")
        return card

    def _build_card(self, title: str, description: str, deep_link: str) -> dict[str, Any]:
        """Build an Adaptive Card with a deep-link button to the platform."""
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"💼 **{title}**",
                    "weight": "Bolder",
                    "size": "Medium",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": description,
                    "wrap": True,
                    "spacing": "Small",
                    "color": "Default",
                },
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Abrir na plataforma →",
                    "url": deep_link,
                    "style": "positive",
                }
            ],
            "msteams": {"width": "Full"},
        }


# Module-level singleton
_engine: TeamsTabTriggerEngine | None = None


def get_trigger_engine() -> TeamsTabTriggerEngine:
    global _engine
    if _engine is None:
        _engine = TeamsTabTriggerEngine()
    return _engine
