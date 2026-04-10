"""
Sprint 1A.6 — Adicionar publish_job ao _ACTION_TOOL_MAP.

ONDE APLICAR: app/domains/job_creation/domain.py (ou jobs/domain.py)
AÇÃO: Adicionar "publish_job" ao tool map para que o agente autônomo possa publicar.
"""

# Encontrar _ACTION_TOOL_MAP no domain.py e adicionar:

PUBLISH_JOB_TOOL = {
    "publish_job": {
        "name": "publish_job",
        "description": (
            "Publica uma vaga criada pelo wizard WSI. "
            "Cria o job no Rails, ativa screening automático, "
            "e retorna link de compartilhamento."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["linkedin", "indeed", "website"]},
                    "description": "Plataformas para publicar a vaga",
                },
                "auto_screen": {
                    "type": "boolean",
                    "description": "Ativar screening automático após publicar",
                    "default": True,
                },
                "sourcing_mode": {
                    "type": "string",
                    "enum": ["local", "global", "hybrid"],
                    "description": "Modo de sourcing de candidatos",
                    "default": "local",
                },
            },
            "required": ["platforms"],
        },
    }
}

# --- TAMBÉM ---
# No _ACTION_TOOL_MAP do domain de jobs (se existir), adicionar referência:
#
# "publish_job": {
#     "handler": "job_creation.publish_node",
#     "requires_wizard": True,
# }
