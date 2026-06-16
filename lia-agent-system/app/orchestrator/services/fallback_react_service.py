"""
Fallback ReAct Service — LIA-A04 last-resort handler.

Sprint II.2 da migração V1→V2 (LIA-D06 cleanup). Extrai a lógica core do
`Orchestrator._handle_directly()` (V1 linhas 426-507) para service canônico,
preservando comportamento exato.

## O que este service faz

Quando nenhum agent específico (CV screening, sourcing, kanban, etc.) é
acionado pelo CascadedRouter, este é o "modo último recurso":
1. Constrói system prompt orchestrator-style com tenant context + entities
2. Injeta histórico de conversa (últimas 10 mensagens) como turns reais
3. Adiciona structured-output addenda per intent (C-05/C-06 fixes)
4. Invoca LLM com tools binding opcional (LIA_FALLBACK_BIND_TOOLS env flag)
5. Extrai content + tool_calls da resposta
6. Graceful error handling com mensagem amigável ao usuário

## O que NÃO está aqui

- **CV screening rubric pre-flight** — fica no caller (V1 ou V2 Sprint III).
  Esta separação de concerns simplifica testes e evita coupling entre o
  fallback ReAct e o domain-specific cv_screening service.

## Taxonomia harness-engineering

`[guide]` — decide via LLM ReAct loop (feedforward + tool call orchestration).

## Reference

ADR-019 — Sprint II.2
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Final

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
from app.shared.constants.prompt_constants import SALARY_BENCHMARK_ADDENDUM
from app.shared.agents.tenant_aware_agent import resolve_tenant_snippet_for_non_react

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Structured-output addenda — fix C-05 / C-06
# Injected per intent into system prompt to enforce response format.
# ─────────────────────────────────────────────────────────────────────────────
STRUCTURED_INTENT_ADDENDA: Final[dict[str, str]] = {
    "cv_screening": (
        "\n\nRegra de saída estruturada (C-05): sempre que responder a uma análise de "
        "compatibilidade ou match de CV, inclua ao final da resposta um bloco JSON no formato:\n"
        "```json\n"
        '{"match_score": <0-100>, "matched_skills": ["skill1", "skill2"], '
        '"missing_skills": ["skill3"], "recommendation": "APROVADO|EM_ANALISE|REPROVADO"}\n'
        "```\n"
        "O match_score deve ser um número inteiro de 0 a 100."
    ),
    "salary_benchmark": SALARY_BENCHMARK_ADDENDUM,  # R-039
}


# ─────────────────────────────────────────────────────────────────────────────
# Configuration constants
# ─────────────────────────────────────────────────────────────────────────────
MAX_HISTORY_MESSAGES: Final[int] = 10
TOOL_BIND_ENV_VAR: Final[str] = "LIA_FALLBACK_BIND_TOOLS"  # R-044: verified-active — controls bind_tools in fallback ReAct path
AGENT_USED_LABEL: Final[str] = "LIA Orchestrator"
AGENT_TYPE_LABEL: Final[str] = "orchestrator"


def _is_tool_binding_enabled() -> bool:
    """
    Lê env var LIA_FALLBACK_BIND_TOOLS — true por default.

    Permite desligar tool binding em produção via env var sem deploy de código.
    """
    raw = os.environ.get(TOOL_BIND_ENV_VAR, "true").lower()
    return raw in ("1", "true", "yes")


class FallbackReActService:
    """
    Service canônico para LIA-A04 fallback ReAct path.

    Substitui `Orchestrator._handle_directly()` (linhas 426-507 do V1) com
    interface limpa, dependency injection do LLM service, e separação de
    CV screening rubric (que fica com o caller).

    ## Multi-tenant safety (P0 LGPD)

    `context["tenant_context_snippet"]`, `context["user_name"]` e outros
    metadados são injetados no system prompt via SystemPromptBuilder. Não
    inclui atributos protegidos (race, religion, gender, ethnicity, etc.) —
    SystemPromptBuilder é responsável por filtrar.

    ## Reference

    ADR-019 — Sprint II.2
    """

    def __init__(
        self,
        llm_service: Any,
        structured_addenda: dict[str, str] | None = None,
    ) -> None:
        """
        Args:
            llm_service: Service com método `get_audited_model()` que retorna
                LangChain BaseChatModel. Tipicamente o `LLMService` injetado
                no Orchestrator V1 ou V2.
            structured_addenda: Mapping intent → addendum to append to system
                prompt. Default: STRUCTURED_INTENT_ADDENDA (C-05/C-06).
        """
        self._llm_service = llm_service
        self._structured_addenda = structured_addenda or STRUCTURED_INTENT_ADDENDA

    async def handle_directly(
        self,
        intent: str,
        message: str,
        entities: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executa o fallback ReAct LLM com optional tool binding.

        Args:
            intent: Intent classificado (usado para selecionar structured addenda).
            message: Mensagem do usuário.
            entities: Entidades extraídas (passadas ao SystemPromptBuilder).
            context: Contexto da request (tenant info, user info, history).

        Returns:
            Dict com shape compatível ao V1._handle_directly:
                - message (str): Resposta do LLM (string content)
                - success (bool): True (mesmo em erro — UX-friendly degradation)
                - data (dict, opcional): inclui tool_calls_requested se houver
                - requires_user_input (bool): True (espera próxima mensagem)
                - suggested_prompts (list): vazio (fallback não sugere)
                - next_actions (list): vazio
                - agent_used (str): "LIA Orchestrator"
                - agent_type (str): "orchestrator"
        """
        ctx = context or {}

        try:
            return await self._invoke_llm(intent, message, entities, ctx)
        except asyncio.CancelledError:
            # P1: respeitar cancelamento (não capturar) — propaga para caller
            raise
        except Exception:
            # P1 graceful degradation — usuário sempre recebe resposta amigável.
            # CancelledError é re-raised acima para preservar semantica asyncio.
            logger.exception("[LIA-A04] FallbackReActService.handle_directly failed")
            return self._build_error_response(ctx)

    async def _invoke_llm(
        self,
        intent: str,
        message: str,
        entities: dict[str, Any],
        ctx: dict[str, Any],
    ) -> dict[str, Any]:
        """Constrói prompt + invoca LLM (com optional tool binding) + extrai resposta."""
        # Lazy import — evita custo em cold path quando service não é usado
        from langchain_core.prompts import ChatPromptTemplate

        # 1. Build system prompt with intent-specific addenda
        # R2 (Task T-F): canonical tenant snippet resolver — emite
        # telemetria `lia_agent_tenant_context_resolved_total{agent="fallback_react"}`
        # e levanta MissingTenantContextError em strict-mode (mesmo contrato
        # do TenantAwareAgentMixin, fechando o ponto cego do CascadedRouter
        # fallback path que destruiu T-D/T-E).
        extra = self._structured_addenda.get(intent, "")
        _tenant_snippet = resolve_tenant_snippet_for_non_react(
            ctx,
            agent_name="fallback_react",
            company_id_raw=ctx.get("company_id"),
        )
        _persona_cid = ctx.get("company_id")
        if _persona_cid:
            from app.shared.prompts.persona_aware_prompt import (
                build_system_prompt_with_persona,
            )
            from lia_config.database import AsyncSessionLocal
            async with AsyncSessionLocal() as _persona_db:
                system_prompt = await build_system_prompt_with_persona(
                    company_id=str(_persona_cid),
                    db=_persona_db,
                    agent_type=AGENT_TYPE_LABEL,
                    tenant_context_snippet=_tenant_snippet,
                    user_name=ctx.get("user_name", ""),
                    user_role=ctx.get("user_role", ""),
                    conversation_summary=ctx.get("conversation_summary", ""),
                    conversation_history=ctx.get("conversation_history"),
                    context_page=ctx.get("context_page", "general"),
                    entity_type=ctx.get("entity_type"),
                    intent=intent,
                    entities=entities,
                    extra_instructions=extra,
                )
        else:
            system_prompt = SystemPromptBuilder.build(
                ai_persona=None,
                agent_type=AGENT_TYPE_LABEL,
                tenant_context_snippet=_tenant_snippet,
                user_name=ctx.get("user_name", ""),
                user_role=ctx.get("user_role", ""),
                conversation_summary=ctx.get("conversation_summary", ""),
                conversation_history=ctx.get("conversation_history"),
                context_page=ctx.get("context_page", "general"),
                entity_type=ctx.get("entity_type"),
                intent=intent,
                entities=entities,
                extra_instructions=extra,
            )

        # 2. LIA-M03: Include conversation history as real message turns (last 10)
        messages: list[tuple[str, str]] = [("system", system_prompt)]
        history = ctx.get("conversation_history", [])
        if history and isinstance(history, list):
            recent = history[-MAX_HISTORY_MESSAGES:]
            for msg in recent:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(("human", content))
                elif role == "assistant":
                    messages.append(("ai", content))

        messages.append(("human", "{message}"))
        prompt = ChatPromptTemplate.from_messages(messages)

        # 3. LIA-A04: bind tools in fallback path (controlled by env var)
        llm = self._llm_service.get_audited_model()
        if _is_tool_binding_enabled():
            llm = self._try_bind_tools(llm)

        # 4. Invoke LLM
        chain = prompt | llm
        response = await chain.ainvoke({"message": message})

        # 5. Extract content + tool_calls
        return self._build_success_response(response)

    def _try_bind_tools(self, llm: Any) -> Any:
        """
        Tenta bind_tools no LLM. Em erro, retorna LLM original (graceful degradation).

        Env var LIA_FALLBACK_BIND_TOOLS controla ativação.
        """
        try:
            from app.tools import get_all_tool_schemas

            tool_schemas = get_all_tool_schemas(
                agent_type=AGENT_TYPE_LABEL, format="claude"
            )
            if tool_schemas:
                bound = llm.bind_tools(tool_schemas)
                logger.debug(
                    "[LIA-A04] _handle_directly bound %d tools", len(tool_schemas)
                )
                return bound
        except Exception as exc:
            logger.warning(
                "[LIA-A04] bind_tools failed (continuing without): %s", exc
            )
        return llm

    @staticmethod
    def _build_success_response(response: Any) -> dict[str, Any]:
        """Extrai content + tool_calls do retorno do LangChain LLM."""
        # Content extraction — handle None content (some LLMs return None when only tool_calls)
        # P1 fix: response.content can legitimately be None — fallback to str(response).
        raw_content = response.content if hasattr(response, "content") else None
        response_content = raw_content if raw_content else str(response)

        # Tool calls extraction (LangChain returns them in response.tool_calls)
        # P1 fix: filter out empty/None names to avoid corrupted tool list.
        response_tools_used: list[str] = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                name = (
                    tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                )
                if name:  # filter empty string and None
                    response_tools_used.append(name)
            if response_tools_used:
                logger.info(
                    "[LIA-A04] _handle_directly LLM requested %d tool(s): %s",
                    len(response_tools_used),
                    response_tools_used,
                )

        return {
            "message": response_content,
            "success": True,
            "data": {"tool_calls_requested": response_tools_used},
            "requires_user_input": True,
            "suggested_prompts": [],
            "next_actions": [],
            "agent_used": AGENT_USED_LABEL,
            "agent_type": AGENT_TYPE_LABEL,
        }

    @staticmethod
    def _build_error_response(ctx: dict[str, Any]) -> dict[str, Any]:
        """Resposta padrão em caso de erro — UX friendly, sempre `success=True`."""
        user_name = ctx.get("user_name", "")
        error_msg = SystemPromptBuilder.build_error_response(user_name=user_name)
        return {
            "message": error_msg,
            "success": True,
            "requires_user_input": True,
            "suggested_prompts": [],
            "agent_used": AGENT_USED_LABEL,
            "agent_type": AGENT_TYPE_LABEL,
        }
