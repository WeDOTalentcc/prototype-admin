"""
HITL (Human-In-The-Loop) decorator for domain tools.

Generaliza o pattern de approval gate além de feature flags
(`SENSITIVE_FLAGS_REQUIRING_HITL` em lia_assistant_flags.py:72-91).

P1-4 fix (2026-05-10): fecha gap Inegociável #7 (Human override sempre
disponível) — antes só feature flags tinham gate centralizado, domain
tools high-impact ficavam sem.

Uso:

    from app.shared.compliance.safety_category import SafetyCategory
    from app.shared.hitl_decorator import require_hitl

    @require_hitl(safety_category=SafetyCategory.OFFER)
    async def send_offer_action(*, offer_id: str, ws_session_id: str = "",
                                  thread_id: str = "", user_id: str = "",
                                  **kwargs) -> dict:
        ...

Comportamento:

1. **Auto-confirm bypass:** se usuário configurou auto_confirm=True
   para este (domain, action), executa direto sem pausar.

2. **Sem auto-confirm:** cria HITLPendingAction no DB + envia mensagem WS,
   retorna `{"status": "pending_human_approval", "pending_id": ...}`.
   Caller deve pausar e esperar aprovação via
   `POST /api/v1/hitl/{thread_id}/approve`.

3. **Após aprovação:** caller verifica via `hitl_service.is_approved(pending_id)`
   e re-invoca a função quando approved=True.

Notas:
- Esse decorator é COMPATÍVEL com `tool_handler` (de app.shared.tool_handler).
  Ordem: `@require_hitl` ABAIXO de `@tool_handler` (HITL roda DEPOIS de
  tenant check + ContextVar resolution).
- Falha aberta: se HITLService falhar, log warning e prossegue (não bloqueia
  produção por bug em HITL infra).

Skill aplicada: production-quality:canonical-standards (cross-domain pattern).
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Optional

from app.shared.compliance.safety_category import SafetyCategory

logger = logging.getLogger(__name__)


def require_hitl(
    safety_category: SafetyCategory,
    *,
    action: Optional[str] = None,
    description_template: Optional[str] = None,
):
    """Decorator que adiciona HITL gate em domain tools.

    Args:
        safety_category: Categoria de risco (define domain do HITL audit).
        action: Nome da ação para log (default = nome da função).
        description_template: Template f-string com {kwargs} placeholder
            para mensagem do approval card. Default genérica.
    """

    def decorator(func: Callable) -> Callable:
        action_name = action or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.middleware.auth_enforcement import _current_company_id

            company_id = _current_company_id.get("") or kwargs.get("company_id", "") or ""
            ws_session_id = kwargs.get("ws_session_id", "") or ""
            thread_id = kwargs.get("thread_id", "") or kwargs.get("session_id", "") or ""
            user_id = kwargs.get("user_id", "") or ""

            # Sem session/thread = chamada direta (sem WS — sem HITL possível)
            # Fail-open: se não tem WS context, executa direto (test envs, batch jobs).
            if not ws_session_id and not thread_id:
                logger.debug(
                    "[HITL] %s: no ws/thread context, skipping HITL gate",
                    action_name,
                )
                return await func(*args, **kwargs)

            try:
                from app.domains.cv_screening.services.hitl_service import hitl_service

                # Check auto-confirm preference
                auto_confirmed = False
                try:
                    auto_confirmed = await hitl_service._check_auto_confirm(
                        user_id=user_id,
                        company_id=company_id,
                        domain=safety_category.value,
                        action_type=action_name,
                    )
                except Exception as exc:
                    logger.debug(
                        "[HITL] %s: auto_confirm check failed (%s), falling back to manual",
                        action_name, exc,
                    )

                if auto_confirmed:
                    logger.info(
                        "[HITL] %s: auto-confirmed for user=%s domain=%s",
                        action_name, user_id, safety_category.value,
                    )
                    return await func(*args, **kwargs)

                # Manual approval required — create pending action
                description = (
                    description_template.format(**kwargs)
                    if description_template
                    else f"Aprovação necessária para {action_name} ({safety_category.value})"
                )

                pending_id = await hitl_service.request_approval(
                    thread_id=thread_id,
                    action=action_name,
                    description=description,
                    data={k: v for k, v in kwargs.items() if k not in ("password", "secret", "token")},
                    ws_session_id=ws_session_id,
                    domain=safety_category.value,
                    company_id=company_id,
                    user_id=user_id,
                )

                logger.info(
                    "[HITL] %s: pending approval pending_id=%s domain=%s",
                    action_name, pending_id, safety_category.value,
                )

                return {
                    "status": "pending_human_approval",
                    "pending_id": pending_id,
                    "safety_category": safety_category.value,
                    "action": action_name,
                    "description": description,
                    "approve_url": f"/api/v1/hitl/{thread_id}/approve",
                    "reject_url": f"/api/v1/hitl/{thread_id}/reject",
                }

            except Exception as exc:
                # Fail-open: HITL infra failure não pode bloquear produção
                logger.warning(
                    "[HITL] %s: HITLService failed (%s), executing without gate (fail-open)",
                    action_name, exc,
                )
                return await func(*args, **kwargs)

        # Marca decorator como aplicado para sensors detectarem
        wrapper.__hitl_decorated__ = True
        wrapper.__hitl_safety_category__ = safety_category
        wrapper.__hitl_action__ = action_name

        return wrapper

    return decorator
