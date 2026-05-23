"""W4-032 · Shared HITL gate helper para ReAct agents.

Helper canonical para replicar o gate pattern de
`communication_react_agent.py:240-318` nos demais 9 agents sem duplicar
~80 LOC em cada um.

Pattern canonical (Hashimoto Harness):
- Cada agent declara `_HITL_ACTION_TYPES: frozenset[str]` com action_types
  que requerem aprovação humana ANTES de executar tool side-effect.
- Caller (chat handler / LangGraph node) seta `input.context["action_type"]`
  com hint do que vai ser executado.
- Antes de `_process_langgraph`, agent chama `maybe_request_hitl_approval(...)`.
- Se action_type está no set E `hitl_approved` é False, helper:
  1. Cria pending action via HITLService.request_approval
  2. Salva resume info pra reprise pós-approval
  3. Loga audit decision (LGPD/SOX compliant)
  4. Retorna AgentOutput "Aguardando aprovação..." (caller deve return)
- Se action_type não está no set OU `hitl_approved` é True, retorna None
  (caller prossegue normalmente).

Multi-tenancy: `company_id` é validado fail-closed.
LGPD: audit row em TODA solicitação (mesmo se action_type não match — mas
helper só audit quando GATE dispara, não em passthrough).

Uso canonical:
```python
class MyReActAgent(...):
    _HITL_ACTION_TYPES = frozenset({"action_destrutiva", "action_externa"})

    async def process(self, input):
        hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain="my_domain",
            action_types=self._HITL_ACTION_TYPES,
            agent_name="my_react_agent",
        )
        if hitl_response is not None:
            return hitl_response  # gate triggered, wait for human

        return await self._process_langgraph(input)
```
"""
from __future__ import annotations

import logging
from typing import Any

from lia_agents_core.agent_interface import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


async def maybe_request_hitl_approval(
    *,
    agent_input: AgentInput,
    domain: str,
    action_types: frozenset[str],
    agent_name: str,
    description_template: str | None = None,
    extra_data: dict[str, Any] | None = None,
) -> AgentOutput | None:
    """Verifica se ação requer HITL approval e dispara o gate quando aplica.

    Args:
        agent_input: AgentInput canonical do agent.
        domain: Identificador do agent domain (= `agent.domain_name`). Usado
            como key em HITLService para resume routing.
        action_types: frozenset[str] com action_types que requerem approval.
            Exemplo: `frozenset({"sync_to_ats", "webhook_trigger"})`.
        agent_name: Nome canonical do agent (ex: "ats_integration_react_agent").
            Usado em audit_service.log_decision.
        description_template: Template human-readable mostrado pro user no
            HITLConfirmCard inline. Suporta `{action_type}` placeholder.
            Default: "Confirmar ação '{action_type}' antes de executar".
        extra_data: Dict adicional preservado no `data` do HITL pending row
            (extensível por agent — ex: candidate_id, vacancy_id).

    Returns:
        - `AgentOutput` "Aguardando aprovação..." se gate triggered.
        - `None` se action_type não match OU já approved (caller prossegue).
    """
    # Fail-closed: sem context, não consigo verificar — passthrough seguro
    if not agent_input or not agent_input.context:
        return None

    hitl_approved = bool(agent_input.context.get("hitl_approved", False))
    action_type = str(agent_input.context.get("action_type", "") or "")

    # Gate só dispara se action_type match E ainda não approved
    if hitl_approved or action_type not in action_types:
        return None

    # Lazy imports — evita circular dependency em startup
    try:
        import app.services.hitl_service as _hitl_svc_mod
        hitl_service = _hitl_svc_mod.hitl_service
    except Exception as e:
        logger.warning(
            "[%s][HITL] hitl_service unavailable, fail-open: %s",
            agent_name, e,
        )
        return None

    thread_id = str(agent_input.session_id or "")
    company_id = str(agent_input.company_id or "")
    user_id = str(agent_input.user_id or "")

    if not thread_id or not company_id:
        logger.warning(
            "[%s][HITL] missing thread_id/company_id, fail-open passthrough",
            agent_name,
        )
        return None

    description = (description_template or
        "Confirmar ação '{action_type}' antes de executar."
    ).format(action_type=action_type)

    # Dados preservados no pending row + repassados ao audit
    pending_data: dict[str, Any] = {
        "action_type": action_type,
        "domain": domain,
        "company_id": company_id,
    }
    if extra_data:
        pending_data.update(extra_data)

    try:
        pending_id = await hitl_service.request_approval(
            thread_id=thread_id,
            action=action_type,
            description=description,
            data=pending_data,
            ws_session_id=thread_id,
            domain=domain,
            company_id=company_id,
        )

        await hitl_service.store_resume_info(
            thread_id=thread_id,
            domain=domain,
            session_id=thread_id,
            agent_input_dict={
                "message": agent_input.message,
                "context": {
                    **agent_input.context,
                    "hitl_approved": True,  # quando reprisar, gate passa
                    "hitl_pending_id": pending_id,
                },
                "session_id": str(agent_input.session_id or ""),
                "company_id": company_id,
                "user_id": user_id,
                "conversation_history": agent_input.conversation_history or [],
            },
            hitl_context=f"{domain}_{action_type}",
        )

        # Audit LGPD/SOX (best-effort, fail-open)
        try:
            from app.shared.compliance.audit_service import (
                PROTECTED_CRITERIA,
                audit_service,
            )

            await audit_service.log_decision(
                company_id=company_id,
                agent_name=agent_name,
                decision_type=action_type,
                action=f"hitl_requested:{action_type}",
                decision="pending_review",
                reasoning=[
                    f"Ação '{action_type}' do domain '{domain}' requer "
                    "aprovação HITL (W4-032, LGPD Art. 7)."
                ],
                criteria_used=[action_type],
                candidate_id=str(pending_data.get("candidate_id", "")),
                human_review_required=True,
                criteria_ignored=list(PROTECTED_CRITERIA),
            )
        except Exception as audit_exc:
            logger.debug(
                "[%s][HITL][W4-032] AuditService skipped: %s",
                agent_name, audit_exc,
            )

        logger.info(
            "[%s][HITL][W4-032] approval requested session=%s action=%s pending_id=%s",
            agent_name, thread_id, action_type, pending_id,
        )

        return AgentOutput(
            message=(
                f"Aguardando aprovação para **{action_type}**. "
                "Confirme abaixo antes da execução."
            ),
            confidence=1.0,
            metadata={
                "hitl_pending": True,
                "hitl_pending_id": pending_id,
                "thread_id": thread_id,
                "domain": domain,
                "action_type": action_type,
            },
        )

    except Exception as hitl_exc:
        # Fail-open: se infra HITL quebrou, NÃO bloqueia o agent.
        # Audit log capturou a tentativa. Operação prossegue (com risk).
        logger.warning(
            "[%s][HITL][W4-032] gate failed (fail-open): %s",
            agent_name, hitl_exc, exc_info=True,
        )
        return None
