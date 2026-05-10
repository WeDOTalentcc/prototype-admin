"""
Tenant-related exceptions — fail-closed canônico para multi-tenancy.

Herdam de ``LIATenantError`` (``app.shared.errors``) para integrar com o
exception handler global e o error code registry. Substituem o degrade
silencioso (``"sua empresa"`` / ``"geral"`` / ``workspace_id=0``) por
falhas visíveis e auditáveis.

Ver:
    - ``app/shared/value_objects/company_id.py`` — origem de InvalidCompanyIdError
    - ``app/shared/agents/tenant_aware_agent.py`` — origem de MissingTenantContextError
    - threat_model.md (Tampering / Elevation of Privilege) — porquê fail-closed
"""
from __future__ import annotations

from typing import Any

from app.shared.errors import LIATenantError


class InvalidCompanyIdError(LIATenantError):
    """``company_id`` recebido em formato inválido / proibido / vazio.

    Levantada por ``CompanyId.parse(raw)`` quando a entrada não é UUID v4 nem
    slug válido (``^[a-z][a-z0-9_-]{2,63}$``), ou é literal reservado
    (``"default"``, ``"none"``, ...).

    O payload ``details`` carrega ``company_id_raw`` (repr da entrada bruta —
    seguro pra log porque o valor JÁ é considerado inválido) e ``reason``.
    """

    def __init__(
        self,
        message: str = "company_id inválido",
        code: str = "INVALID_COMPANY_ID",
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details or {},
            recoverable=False,
            **kwargs,
        )


class MissingTenantContextError(LIATenantError):
    """Agente foi invocado sem tenant context resolvível.

    Levantada por ``TenantAwareAgentMixin._get_tenant_context_snippet`` quando
    ``LIA_AGENT_TENANT_STRICT=true`` (default em prod/staging) e o
    ``TenantContextService`` não conseguiu resolver o tenant para um snippet
    não-vazio (ou ``CompanyId.parse`` falhou na entrada).

    Substitui o degrade silencioso para ``"sua empresa"``/``"geral"`` que
    fazia a LIA perguntar "qual é o ID da empresa?" no chat. Ver
    ``.local/tasks/canonical-tenant-aware-agent-infra.md``.

    Payload ``details`` carrega:
        - ``tenant_source``: como o caller obteve o ``company_id`` (ex.:
          ``"jwt"``, ``"agent_input"``, ``"context_var"``)
        - ``agent``: ``domain_name`` do agente que falhou
        - ``company_id_raw``: valor bruto recebido (pode ser ``None``)
    """

    def __init__(
        self,
        message: str = "Tenant context ausente — agente não pode operar fail-closed",
        code: str = "MISSING_TENANT_CONTEXT",
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details or {},
            recoverable=False,
            **kwargs,
        )
