"""Communication ReAct Agent — Stage Context.

Defines execution stages for the communication workflow and their associated tools.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, Any] = {
    "intent-detection": {
        "description": (
            "Entender qual comunicação o usuário deseja enviar: canal, destinatário, "
            "tipo de mensagem. Verificar histórico e rate limit antes de avançar."
        ),
        "tools": ["get_communication_history", "check_rate_limit", "suggest_communication_policy", "suggest_alert_rule_templates", "apply_alert_rule_template", "create_custom_alert_rule_template"],
        "next_stages": ["content-preparation", "delivery"],
    },
    "content-preparation": {
        "description": (
            "Rascunhar e validar o conteúdo da mensagem. Confirmar que o envio ainda "
            "é permitido após checar novamente rate limit e histórico recente."
        ),
        "tools": ["check_rate_limit", "get_communication_history", "suggest_alert_rule_templates", "apply_alert_rule_template", "create_custom_alert_rule_template"],
        "next_stages": ["delivery"],
    },
    "delivery": {
        "description": (
            "Enviar ou agendar a mensagem após todas as validações de conformidade. "
            "Todos os canais estão disponíveis nesta etapa."
        ),
        "tools": [
            "send_email",
            "send_whatsapp",
            "schedule_message",
            "check_rate_limit",
            "get_communication_history",
        ],
        "next_stages": [],
    },
}


def get_stage_context(stage: str) -> dict[str, Any]:
    return STAGE_DEFINITIONS.get(stage, STAGE_DEFINITIONS["intent-detection"])


def get_stage_tools(stage: str) -> list[str]:
    return get_stage_context(stage).get("tools", [])


def get_transition_prompt(from_stage: str, to_stage: str) -> str:
    prompts = {
        ("intent-detection", "content-preparation"): (
            "Intenção identificada. Preparando conteúdo da mensagem..."
        ),
        ("intent-detection", "delivery"): (
            "Intenção e conteúdo confirmados. Realizando envio..."
        ),
        ("content-preparation", "delivery"): (
            "Conteúdo validado. Realizando envio ou agendamento..."
        ),
    }
    return prompts.get(
        (from_stage, to_stage),
        f"Avançando de '{from_stage}' para '{to_stage}'.",
    )
