"""
Rubric Dispatch Service — CV match analysis via BARS rubric tool.

Sprint IV da migração V1→V2 (LIA-D06 cleanup). Última extração planejada
no Anexo H do ORCHESTRATOR_MIGRATION_MASTER_PLAN.md.

## O que este service faz

Quando o usuário envia uma mensagem que pede análise de CV/match de candidato
(detectado por `is_cv_matching_request` heuristic), este service:

1. Extrai entidades (candidate_id/name + vacancy_id/title) via LLM (Gemini)
2. Valida que pelo menos candidate foi identificado
3. Executa tool canônica `analyze_cv_match` (BARS deterministic methodology)
4. Retorna structured response (match_score, matched_skills, missing_skills,
   recommendation) — formato C-05

## Por que BARS rubric e não LLM free-text?

BARS = Behaviorally Anchored Rating Scales — methodologia determinística que
garante:
- Reprodutibilidade: mesmo input → mesmo score
- Compliance LGPD: zero atributos protegidos no scoring
- Auditabilidade: cada skill match é justificável

LLM é usado APENAS para entity extraction (não scoring).

## Multi-tenant safety (P0 LGPD)

`context["company_id"]` é obrigatório e propagado ao `ToolExecutionContext`
para isolar tenants. `analyze_cv_match` valida `require_company=True`.

## Reference

ADR-019 — Sprint IV (originalmente Anexo H, mapping `_handle_cv_screening_with_rubric`)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Final

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

ENTITY_EXTRACTION_PROMPT: Final[str] = (
    "Extraia do texto abaixo as informações de candidato e vaga para análise de CV. "
    "Retorne SOMENTE um JSON válido (sem markdown) com as chaves: "
    'candidate_id, candidate_name, vacancy_id, vacancy_title. '
    "Use null quando não encontrar. Não invente IDs — somente use se mencionados "
    "explicitamente como UUID.\n\n"
    "Texto: {message}"
)

# Tool canônica para BARS rubric (registered in app/tools/)
RUBRIC_TOOL_NAME: Final[str] = "analyze_cv_match"

# LLM provider para entity extraction (deterministic — Gemini é cheap + fast)
EXTRACTION_LLM_PROVIDER: Final[str] = "gemini"

# Default agent_type para tool execution
DEFAULT_AGENT_TYPE: Final[str] = "orchestrator"

# Suggested prompts retornados quando match é executado com sucesso (UX hints)
DEFAULT_SUGGESTED_PROMPTS: Final[list[str]] = [
    "Mover candidato para próxima etapa",
    "Ver outros candidatos para esta vaga",
    "Enviar feedback ao candidato",
]


def _empty_result() -> dict[str, Any]:
    """Resposta padrão quando dispatch falha — caller deve fallback to LLM."""
    return {"success": False}


class RubricDispatchService:
    """
    Service canônico para CV match dispatch via BARS rubric tool.

    Substitui `Orchestrator._handle_cv_screening_with_rubric()` (V1 linhas
    429-516) com interface limpa e dependency injection do LLM service.

    ## Usage

        # DI
        service = RubricDispatchService(llm_service=llm_svc)

        # Dispatch
        result = await service.dispatch(
            message="Analise o CV da Maria para a vaga de Dev Backend",
            context={"company_id": "tenant-a", "user_id": "u1"},
        )

        if result["success"]:
            # match_score, matched_skills, missing_skills, recommendation present
            print(result["match_score"])
        else:
            # Falha silenciosa — caller deve usar LLM addendum como fallback
            ...

    ## Reference

    ADR-019 — Sprint IV
    """

    def __init__(self, llm_service: Any) -> None:
        """
        Args:
            llm_service: Service com método `generate(prompt, provider=...)`.
                Tipicamente o `LLMService` do orchestrator V1 ou V2.
        """
        self._llm_service = llm_service

    async def dispatch(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executa o dispatch de CV match via BARS rubric tool.

        Args:
            message: Mensagem do usuário com pedido de análise de CV.
            context: Contexto da request. Deve incluir `company_id`
                (P0 LGPD multi-tenant isolation).

        Returns:
            Dict com shape compatível ao V1._handle_cv_screening_with_rubric:
                - success (bool): True se rubric tool executou e retornou data
                - message (str, opcional): "Análise de CV concluída." ou similar
                - data (dict, opcional): payload completo do tool
                - match_score (int 0-100, opcional)
                - matched_skills (list[str], opcional)
                - missing_skills (list[str], opcional)
                - recommendation (str, opcional): APROVADO/EM_ANALISE/REPROVADO
                - suggested_prompts (list[str], opcional)
                - agent_used (str): "CV Match Tool (BARS Rubric)"
                - agent_type (str): "tool"

            Em qualquer falha (LLM error, JSON parse, no candidate, tool fail),
            retorna `{"success": False}` para que caller use LLM addendum.
        """
        ctx = context or {}

        try:
            # 1. Entity extraction via LLM
            params = await self._extract_entities(message)
            if not params:
                return _empty_result()

            # 2. Validar candidate present (P1: tool requires candidate)
            if not params.get("candidate_id") and not params.get("candidate_name"):
                logger.debug("[cv_screening rubric] No candidate found in message")
                return _empty_result()

            # 3. Execute BARS rubric tool
            return await self._execute_rubric_tool(params, ctx)

        except Exception as exc:
            # P1: graceful — caller usa LLM fallback. Nunca re-raise.
            logger.warning(
                "[cv_screening rubric] Dispatch failed (%s), caller should fallback to LLM",
                exc,
            )
            return _empty_result()

    async def _extract_entities(self, message: str) -> dict[str, Any] | None:
        """
        Usa LLM (Gemini) para extrair candidate/vacancy entities da mensagem.

        Returns:
            Dict de params se JSON parse OK, None se extraction falhou.
        """
        prompt = ENTITY_EXTRACTION_PROMPT.format(message=message)

        try:
            raw = await self._llm_service.generate(
                prompt, provider=EXTRACTION_LLM_PROVIDER
            )
        except Exception as exc:
            logger.debug("[cv_screening rubric] LLM extraction call failed: %s", exc)
            return None

        # Strip potential markdown fences (LLM às vezes wraps JSON em ```)
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")

        # Match first JSON-like object in response
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            logger.debug("[cv_screening rubric] No JSON in extraction response")
            return None

        try:
            params = json.loads(match.group())
        except json.JSONDecodeError as exc:
            logger.debug("[cv_screening rubric] JSON parse failed: %s", exc)
            return None

        # Remove null / empty values (entities not extracted)
        return {k: v for k, v in params.items() if v not in (None, "", "null")}

    async def _execute_rubric_tool(
        self, params: dict[str, Any], ctx: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Executa `analyze_cv_match` tool com params extraídos.

        P0 LGPD: ToolExecutionContext inclui company_id (multi-tenant isolation).
        """
        # Lazy import — evita carregar tools framework em cold path
        from app.tools.executor import ToolExecutionContext, tool_executor

        exec_context = ToolExecutionContext(
            user_id=ctx.get("user_id", "system"),
            company_id=ctx.get("company_id"),
            session_id=ctx.get("session_id"),
        )

        tool_result = await tool_executor.execute(
            tool_name=RUBRIC_TOOL_NAME,
            parameters=params,
            agent_type=DEFAULT_AGENT_TYPE,
            context=exec_context,
        )

        if tool_result.success and tool_result.result:
            return self._build_success_response(tool_result.result)

        logger.warning(
            "[cv_screening rubric] Tool returned failure: %s",
            getattr(tool_result, "error", None),
        )
        return _empty_result()

    @staticmethod
    def _build_success_response(data: dict[str, Any]) -> dict[str, Any]:
        """Build V1-compatible success dict from tool result."""
        return {
            "success": True,
            "message": data.get("message", "Análise de CV concluída."),
            "data": data,
            "requires_user_input": False,
            "suggested_prompts": list(DEFAULT_SUGGESTED_PROMPTS),
            "next_actions": [],
            "agent_used": "CV Match Tool (BARS Rubric)",
            "agent_type": "tool",
            # C-05 structured fields surfaced at top level
            "match_score": data.get("match_score"),
            "matched_skills": data.get("matched_skills", []),
            "missing_skills": data.get("missing_skills", []),
            "recommendation": data.get("recommendation"),
        }
