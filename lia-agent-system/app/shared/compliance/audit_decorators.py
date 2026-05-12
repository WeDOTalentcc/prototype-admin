"""PR4 (Task #1004) — Wrapper canônico de audit log para tools de
``company_settings``.

Inegociável #6 da `lia-compliance` exige que TODA mutação por agente IA
em config corporativa produza um registro durável em ``audit_logs``
(SOX, ISO 27001, EU AI Act). Antes do PR4:

  * 5 das 6 tools de save em ``company_settings`` NÃO chamavam
    ``AuditService.log_decision``.
  * A única que chamava (``import_benefits_from_data``) usava
    ``try/except: pass`` — fire-and-forget, anti-pattern canonical-fix #4.

Este módulo expõe o context manager ``audit_company_change`` — modo
fail-CLOSED por default (falha do AuditService levanta exceção). Em
emergência rollback (storm de erro do DB de audit), a flag
``LIA_DISABLE_COMPANY_AUDIT=1`` desliga a emissão; ``app/main.py`` loga
CRITICAL + Sentry capture quando ON em prod/staging (espelha R-007).

Uso canônico:

    async with audit_company_change(
        action="save_company_field",
        company_id=company_id,
        actor=user_id,
        target_table="company_profiles",
        metadata={"section": section, "field": field},
    ) as _audit:
        result = await _do_the_save(...)
        _audit.set_result(result)
        return result

Outcome derivado de ``result``:

  * ``success: True`` → ``decision = "completed"``
  * ``success: False, reason: "fairness_violation"`` → ``decision = "blocked_fairness"``
  * ``success: False`` → ``decision = "failed"``
  * Exceção propagada do bloco → ``decision = "exception"``

Para tools read-only (``check_company_completeness``), passar
``read_only=True`` registra ``decision = "read"`` (auditar acesso a
dados corporativos é exigência LGPD Art. 37 / ISO 27001 A.12.4).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Flag de emergência. Default OFF — fail-CLOSED.
_DISABLE_FLAG = "LIA_DISABLE_COMPANY_AUDIT"


def is_company_audit_disabled() -> bool:
    """True quando ``LIA_DISABLE_COMPANY_AUDIT=1`` está ativo. Lido a
    cada chamada (não cacheia) para que testes e on-call possam alternar
    sem reboot."""
    return os.getenv(_DISABLE_FLAG, "0") == "1"


def _derive_outcome(result: Any, *, read_only: bool) -> str:
    """Mapeia o retorno da tool para o campo ``decision`` do AuditLog."""
    if read_only:
        return "read"
    if not isinstance(result, dict):
        return "completed"
    if result.get("success") is True:
        return "completed"
    reason = result.get("reason") or result.get("error")
    if reason == "fairness_violation":
        return "blocked_fairness"
    if reason:
        return f"failed:{reason}"[:64]
    return "failed"


def _truncate_str(value: Any, limit: int = 200) -> str:
    s = str(value)
    return s if len(s) <= limit else f"{s[:limit]}…"


class _AuditCtx:
    """Context manager assíncrono. Coleta metadata e emite o audit log
    no ``__aexit__``. Em caso de falha do AuditService, levanta
    ``RuntimeError`` (fail-CLOSED) — exceção do bloco protegido tem
    prioridade e é re-emitida por baixo de uma chained exception se a
    audit também falhar."""

    def __init__(
        self,
        *,
        action: str,
        company_id: str,
        actor: Optional[str],
        target_table: Optional[str],
        metadata: Optional[dict[str, Any]],
        agent_name: str,
        read_only: bool,
    ) -> None:
        self.action = action
        self.company_id = str(company_id) if company_id else ""
        self.actor = actor or "anonymous"
        self.target_table = target_table or "company_settings"
        self.metadata = dict(metadata or {})
        self.agent_name = agent_name
        self.read_only = read_only
        self._result: Any = None

    def set_result(self, result: Any) -> None:
        """Registra o retorno da tool para que ``__aexit__`` derive o
        ``decision`` correto. Chamar ANTES do ``return`` em cada caminho
        de saída."""
        self._result = result

    async def __aenter__(self) -> "_AuditCtx":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # noqa: D401
        # Emergency bypass: pula emissão mas loga warning estruturado.
        if is_company_audit_disabled():
            logger.warning(
                "[audit_company_change] BYPASSED (LIA_DISABLE_COMPANY_AUDIT=1) "
                "action=%s company=%s actor=%s outcome=%s",
                self.action,
                self.company_id,
                self.actor,
                "exception" if exc_type else _derive_outcome(self._result, read_only=self.read_only),
            )
            return False  # NÃO suprime exceção do bloco protegido

        outcome = "exception" if exc_type else _derive_outcome(
            self._result, read_only=self.read_only
        )

        # Tenant ausente → não há como persistir RLS; logar erro e
        # NÃO levantar (caller já vai falhar no save por outro motivo).
        if not self.company_id:
            logger.error(
                "[audit_company_change] company_id ausente em action=%s — "
                "audit não emitido (RLS impede). Caller deve garantir tenant.",
                self.action,
            )
            return False

        reasoning = [f"actor={self.actor}", f"outcome={outcome}"]
        for k, v in self.metadata.items():
            reasoning.append(f"{k}={_truncate_str(v)}")
        if exc_type is not None:
            reasoning.append(f"exception={exc_type.__name__}: {_truncate_str(exc)}")

        criteria = [
            "company_scoped",
            f"target_table:{self.target_table}",
            f"action:{self.action}",
            f"read_only:{self.read_only}",
        ]

        try:
            # Import local para evitar ciclo (audit_service usa modelos
            # SQLAlchemy que importam config compartilhada).
            from app.shared.compliance.audit_service import AuditService

            await AuditService().log_decision(
                company_id=self.company_id,
                agent_name=self.agent_name,
                decision_type="company_settings_change",
                action=self.action,
                decision=outcome,
                reasoning=reasoning,
                criteria_used=criteria,
                job_vacancy_id=None,
                confidence=1.0,
                human_review_required=False,
                criteria_ignored=None,
            )
        except Exception as audit_exc:
            logger.error(
                "[audit_company_change] FAIL-CLOSED: AuditService.log_decision "
                "falhou para action=%s company=%s outcome=%s: %s",
                self.action,
                self.company_id,
                outcome,
                audit_exc,
                exc_info=True,
            )
            try:  # Sentry é best-effort — falha aqui não bloqueia o raise.
                import sentry_sdk

                sentry_sdk.capture_exception(audit_exc)
            except Exception:
                pass
            # Fail-CLOSED: se o bloco protegido completou sem exceção,
            # convertemos a falha do audit em RuntimeError. Se o bloco
            # já estava propagando exceção, deixamos a original
            # propagar (audit_exc fica registrada via logger.error).
            if exc_type is None:
                raise RuntimeError(
                    f"audit_company_change: falha ao persistir audit log "
                    f"para action={self.action} (fail-CLOSED — defina "
                    f"LIA_DISABLE_COMPANY_AUDIT=1 só em rollback emergencial)"
                ) from audit_exc

        return False  # NUNCA suprime exceção do bloco protegido.


def audit_company_change(
    *,
    action: str,
    company_id: str,
    actor: Optional[str] = None,
    target_table: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    agent_name: str = "company_settings_tools",
    read_only: bool = False,
) -> _AuditCtx:
    """Async context manager que envolve uma tool de ``company_settings``
    com audit log canônico. Veja docstring do módulo para uso e
    semântica do ``decision``."""
    return _AuditCtx(
        action=action,
        company_id=company_id,
        actor=actor,
        target_table=target_table,
        metadata=metadata,
        agent_name=agent_name,
        read_only=read_only,
    )


__all__ = [
    "audit_company_change",
    "is_company_audit_disabled",
]
