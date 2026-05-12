"""PR4 (Task #1004) — Wrapper canônico de audit log para tools de
``company_settings``.

Inegociável #6 da `lia-compliance` exige que TODA mutação por agente IA
em config corporativa produza um registro durável em ``audit_logs``
(SOX, ISO 27001, EU AI Act). Antes do PR4:

  * 5 das 6 tools de save em ``company_settings`` NÃO chamavam
    ``AuditService.log_decision``.
  * A única que chamava (``import_benefits_from_data``) usava
    ``try/except: pass`` — fire-and-forget, anti-pattern canonical-fix #4.

Este módulo expõe o context manager ``audit_company_change`` em modo
**fail-CLOSED com pattern outbox de duas fases**:

  1. ``__aenter__``: emite uma audit row de INTENT
     (``decision="initiated"``). Se a infraestrutura de audit estiver
     indisponível, o RuntimeError é levantado AQUI — antes do bloco
     protegido executar — então a mutação de negócio nunca acontece.
     Este é o "equivalente outbox/transactional pattern" pedido pelo
     code review do PR4: armazenamento de audit indisponível ⇒ business
     write não acontece.

  2. ``__aexit__``: emite a audit row de OUTCOME
     (``completed``/``failed``/``blocked_fairness``/``exception``/``read``)
     com ``before``/``after``/``target_id`` capturados via setters. Se a
     emissão de outcome falha, levantamos RuntimeError (fail-CLOSED para
     o caller), com Sentry capture best-effort + log CRITICAL — operador
     vê a inconsistência imediatamente.

Trade-off conhecido (documentado): cada save canônico produz **2 audit
rows** (intent + outcome). ISO 27001 / EU AI Act preferem over-audit a
under-audit. As duas rows compartilham ``target_id`` e ``criteria_used``
para facilitar correlação em queries forenses.

Em emergência rollback (storm de erro do DB de audit), a flag
``LIA_DISABLE_COMPANY_AUDIT=1`` desliga as duas emissões;
``app/main.py`` loga CRITICAL + Sentry capture quando ON em
prod/staging (espelha R-007).

Uso canônico:

    async with audit_company_change(
        action="save_company_field",
        company_id=company_id,
        actor=user_id,
        target_table="company_profiles",
        target_id=f"{company_id}::{section}.{field}",
        metadata={"section": section, "field": field},
    ) as audit:
        before = await _read_current(...)
        audit.set_before(before)
        result = await _do_the_save(...)
        audit.set_after({"section": section, "field": field, "value": value})
        audit.set_result(result)
        return result

Outcome derivado de ``result`` em ``__aexit__``:

  * ``success: True`` → ``decision = "completed"``
  * ``success: False, reason: "fairness_violation"`` → ``decision = "blocked_fairness"``
  * ``success: False`` → ``decision = "failed"``
  * Exceção propagada do bloco → ``decision = "exception"``

Para tools read-only (``check_company_completeness``), passar
``read_only=True``: pula a row de INTENT (não há mutação a proteger) e
registra ``decision = "read"`` no exit (auditar acesso a dados
corporativos é exigência LGPD Art. 37 / ISO 27001 A.12.4).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
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


def _serialize_payload(value: Any, limit: int = 1000) -> str:
    """Serializa ``before``/``after`` como JSON compacto. Truncado para
    proteger storage / evitar PII excessivo. Fallback para ``str(value)``
    se não for serializável."""
    try:
        s = json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)
    except Exception:
        s = str(value)
    return s if len(s) <= limit else f"{s[:limit]}…"


class _AuditCtx:
    """Context manager assíncrono outbox-de-duas-fases. Em
    ``__aenter__`` emite uma row ``initiated`` (a falha aborta o bloco
    inteiro). Em ``__aexit__`` emite a row de outcome com
    ``before``/``after``/``target_id``."""

    def __init__(
        self,
        *,
        action: str,
        company_id: str,
        actor: Optional[str],
        target_table: Optional[str],
        target_id: Optional[str],
        metadata: Optional[dict[str, Any]],
        agent_name: str,
        read_only: bool,
    ) -> None:
        self.action = action
        self.company_id = str(company_id) if company_id else ""
        self.actor = actor or "anonymous"
        self.target_table = target_table or "company_settings"
        self.target_id = target_id
        self.metadata = dict(metadata or {})
        self.agent_name = agent_name
        self.read_only = read_only
        self._result: Any = None
        self._before: Any = None
        self._before_set = False
        self._after: Any = None
        self._after_set = False
        # Trace ID compartilhado entre intent e outcome — permite query
        # forense que correlaciona o par.
        self.trace_id = str(uuid.uuid4())

    # ── Setters chamados pelo bloco protegido ────────────────────────
    def set_result(self, result: Any) -> None:
        """Registra o retorno da tool para que ``__aexit__`` derive o
        ``decision`` correto. Chamar ANTES do ``return`` em cada caminho
        de saída."""
        self._result = result

    def set_before(self, before: Any) -> None:
        """Snapshot do estado anterior à mutação (canonical payload do
        audit). Pode ser ``None`` quando não aplicável."""
        self._before = before
        self._before_set = True

    def set_after(self, after: Any) -> None:
        """Snapshot do estado pós-mutação (canonical payload do audit)."""
        self._after = after
        self._after_set = True

    def set_target_id(self, target_id: str) -> None:
        """Override do ``target_id`` se descoberto durante a execução
        (ex.: depois de criar uma row e obter o PK)."""
        self.target_id = str(target_id) if target_id else None

    # ── Emissão de audit rows ────────────────────────────────────────
    async def _emit(self, *, decision: str, exc: Optional[BaseException]) -> None:
        """Persiste uma audit row. Levanta exceção do AuditService — o
        caller (``__aenter__``/``__aexit__``) decide se converte em
        RuntimeError ou loga + propaga original."""
        reasoning: list[str] = [
            f"trace_id={self.trace_id}",
            f"actor={self.actor}",
            f"target_id={self.target_id or '∅'}",
            f"outcome={decision}",
        ]
        if self._before_set:
            reasoning.append(f"before={_serialize_payload(self._before)}")
        if self._after_set:
            reasoning.append(f"after={_serialize_payload(self._after)}")
        for k, v in self.metadata.items():
            reasoning.append(f"{k}={_truncate_str(v)}")
        if exc is not None:
            reasoning.append(f"exception={type(exc).__name__}: {_truncate_str(exc)}")

        criteria = [
            "company_scoped",
            f"target_table:{self.target_table}",
            f"target_id:{self.target_id or '∅'}",
            f"action:{self.action}",
            f"read_only:{self.read_only}",
            f"trace_id:{self.trace_id}",
        ]

        # Import local para evitar ciclo (audit_service usa modelos
        # SQLAlchemy que importam config compartilhada).
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=self.company_id,
            agent_name=self.agent_name,
            decision_type="company_settings_change",
            action=self.action,
            decision=decision,
            reasoning=reasoning,
            criteria_used=criteria,
            job_vacancy_id=None,
            confidence=1.0,
            human_review_required=False,
            criteria_ignored=None,
        )

    # ── CM protocol ──────────────────────────────────────────────────
    async def __aenter__(self) -> "_AuditCtx":
        # Bypass de emergência: pula intent + outcome.
        if is_company_audit_disabled():
            return self

        # Read-only não muta estado → não há nada a "proteger" via
        # outbox; a row de leitura é registrada no __aexit__.
        if self.read_only:
            return self

        # Tenant ausente: AuditService falharia no RLS. Logar e seguir
        # (a tool subjacente provavelmente também vai falhar e deixar
        # rastro). Não levantamos para preservar mensagens de erro de
        # negócio mais úteis.
        if not self.company_id:
            logger.error(
                "[audit_company_change] company_id ausente em action=%s — "
                "intent audit não emitido (RLS impede). Caller deve "
                "garantir tenant.",
                self.action,
            )
            return self

        # Outbox fase 1: emite "initiated". Se a infra de audit estiver
        # indisponível, levantamos AQUI — bloco protegido nunca executa.
        try:
            await self._emit(decision="initiated", exc=None)
        except Exception as audit_exc:
            logger.critical(
                "[audit_company_change] FAIL-CLOSED (intent): AuditService "
                "indisponível para action=%s company=%s — bloco abortado "
                "antes de qualquer mutação de negócio: %s",
                self.action,
                self.company_id,
                audit_exc,
                exc_info=True,
            )
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(audit_exc)
            except Exception:
                pass
            raise RuntimeError(
                f"audit_company_change: storage de audit indisponível "
                f"(intent emit falhou) para action={self.action}; "
                f"mutação de negócio abortada para preservar Inegociável "
                f"#6 (defina LIA_DISABLE_COMPANY_AUDIT=1 só em rollback "
                f"emergencial)"
            ) from audit_exc
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # noqa: D401
        # Bypass de emergência: warn estruturado + sair.
        if is_company_audit_disabled():
            logger.warning(
                "[audit_company_change] BYPASSED (LIA_DISABLE_COMPANY_AUDIT=1) "
                "action=%s company=%s actor=%s outcome=%s trace_id=%s",
                self.action,
                self.company_id,
                self.actor,
                "exception" if exc_type else _derive_outcome(self._result, read_only=self.read_only),
                self.trace_id,
            )
            return False  # NÃO suprime exceção do bloco protegido

        if not self.company_id:
            return False

        outcome = "exception" if exc_type else _derive_outcome(
            self._result, read_only=self.read_only
        )

        try:
            await self._emit(decision=outcome, exc=exc)
        except Exception as audit_exc:
            logger.critical(
                "[audit_company_change] FAIL-CLOSED (outcome): AuditService "
                "falhou para action=%s company=%s outcome=%s trace_id=%s — "
                "intent row já existe (audit inconsistente): %s",
                self.action,
                self.company_id,
                outcome,
                self.trace_id,
                audit_exc,
                exc_info=True,
            )
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(audit_exc)
            except Exception:
                pass
            # Bloco protegido completou sem exceção → converte falha de
            # audit em RuntimeError. Bloco já estava propagando exceção
            # → deixa a original propagar (audit_exc fica em logger).
            if exc_type is None:
                raise RuntimeError(
                    f"audit_company_change: falha ao persistir audit row "
                    f"de outcome para action={self.action} trace_id="
                    f"{self.trace_id} (fail-CLOSED — defina "
                    f"LIA_DISABLE_COMPANY_AUDIT=1 só em rollback "
                    f"emergencial)"
                ) from audit_exc

        return False  # NUNCA suprime exceção do bloco protegido.


def audit_company_change(
    *,
    action: str,
    company_id: str,
    actor: Optional[str] = None,
    target_table: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    agent_name: str = "company_settings_tools",
    read_only: bool = False,
) -> _AuditCtx:
    """Async context manager que envolve uma tool de ``company_settings``
    com audit log canônico (outbox de duas fases). Veja docstring do
    módulo para uso, semântica do ``decision`` e payload canônico
    (``before``/``after``/``target_id``)."""
    return _AuditCtx(
        action=action,
        company_id=company_id,
        actor=actor,
        target_table=target_table,
        target_id=target_id,
        metadata=metadata,
        agent_name=agent_name,
        read_only=read_only,
    )


__all__ = [
    "audit_company_change",
    "is_company_audit_disabled",
]
