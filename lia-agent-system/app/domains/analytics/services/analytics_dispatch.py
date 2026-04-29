"""
Analytics Dispatch Service — proxy para job_analytics_prompt_service.

Sprint IV (extra) — extração de `Orchestrator.process_analytics_request()`
do V1 para service canônico em domain analytics.

## O que este service faz

Recebe um command (string) e contexto, decide se é template (COMMAND_TEMPLATES)
ou natural query, e delega para o `job_analytics_prompt_service`. Retorna
shape canônico V1-compatible.

## Por que extrair?

V1 mantinha esse método inline (~17 LoC) sem separação clara de
responsabilidade. Extrair canonicaliza:
- Easier testing (DI do analytics_service)
- V2 pode usar diretamente sem passar por V1
- State manager update fica responsabilidade do caller (V1 ou V2)

## Multi-tenant safety (P0 LGPD)

Context é repassado direto ao `job_analytics_prompt_service`. Esse service
deve validar `company_id` em suas tools. Service **não** valida tenant
isolation diretamente — é proxy puro.

## Reference

ADR-019 — extração planejada como follow-up
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnalyticsDispatchService:
    """
    Service canônico para dispatch de analytics requests.

    Substitui `Orchestrator.process_analytics_request()` (V1 linhas 507-523)
    com interface limpa via DI do analytics_service.

    ## Usage

        # DI
        from app.services import job_analytics_prompt_service, COMMAND_TEMPLATES
        service = AnalyticsDispatchService(
            analytics_service=job_analytics_prompt_service,
            command_templates=COMMAND_TEMPLATES,
        )

        # Dispatch
        result = await service.dispatch(
            command="analyze hiring funnel",
            context={"company_id": "tenant-a"},
        )

        if result["success"]:
            # response, data, charts, suggestions, metadata present
            ...
    """

    def __init__(
        self,
        analytics_service: Any,
        command_templates: Any,
    ) -> None:
        """
        Args:
            analytics_service: Service com `execute_command(cmd, ctx)` e
                `analyze_natural_query(query, ctx)`. Tipicamente
                `job_analytics_prompt_service`.
            command_templates: Container com __contains__ para checagem
                "command in templates". Tipicamente `COMMAND_TEMPLATES` dict.
        """
        self._service = analytics_service
        self._templates = command_templates

    async def dispatch(
        self,
        command: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executa analytics dispatch (template ou natural query).

        Args:
            command: Comando ou natural query.
            context: Contexto da request (deve incluir `company_id`).

        Returns:
            Dict V1-compatible:
            - success (bool)
            - command (str): comando processado
            - agent_used (str)
            - response (str): resposta human-readable
            - data (dict)
            - charts (list)
            - suggestions (list)
            - metadata (dict)

            Em exception: `{"success": False, "error": str(e)}`.
        """
        try:
            if command in self._templates:
                result = await self._service.execute_command(command, context)
            else:
                result = await self._service.analyze_natural_query(command, context)

            return {
                "success": True,
                "command": result.command,
                "agent_used": result.agent_used,
                "response": result.response,
                "data": result.data,
                "charts": result.charts,
                "suggestions": result.suggestions,
                "metadata": result.metadata,
            }
        except Exception as e:
            # P1 graceful: nunca propaga exception para caller
            logger.error("Analytics request failed: %s", e)
            return {"success": False, "error": str(e)}

    def is_template_command(self, command: str) -> bool:
        """
        Helper para inspeção: True se command está em COMMAND_TEMPLATES.

        Útil para debug e logging — caller pode logar se é template ou natural.
        """
        return command in self._templates
