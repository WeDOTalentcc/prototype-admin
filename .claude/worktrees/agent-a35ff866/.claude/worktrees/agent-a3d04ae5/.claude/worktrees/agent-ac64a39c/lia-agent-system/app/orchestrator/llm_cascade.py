"""
LLM Cascade Router — Tier 3 do Cost Cascade Orchestrator.

Implementa a escada de custo Haiku → Sonnet → Opus:
1. Tenta Haiku (mais barato) primeiro
2. Se confiança < LLM_CASCADE_FAST_THRESHOLD, escalona para Sonnet
3. Se confiança < LLM_CASCADE_MID_THRESHOLD, escalona para Opus (somente se configurado)

O resultado inclui o modelo efetivamente usado e a confiança obtida,
para rastreabilidade de custo por tenant.

Integra com TenantBudget para registrar tokens consumidos.
"""
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

# Prompt minimalista de roteamento — otimizado para Haiku (custo mínimo)
_ROUTING_PROMPT = """Você é um roteador de intenções para um sistema de RH.

Analise a mensagem do usuário e retorne um JSON com:
- domain: um de [job_management, sourcing, cv_screening, pipeline, talent, kanban, analytics, communication, automation, recruiter_assistant]
- confidence: float de 0.0 a 1.0
- reason: explicação curta (max 50 chars)

Mensagem: {message}

Responda SOMENTE com o JSON, sem texto extra."""


class LLMCascadeRouter:
    """
    Roteador LLM com escada de custo: Haiku → Sonnet → Opus.

    Tenta o modelo mais barato primeiro e escalona apenas se necessário.
    """

    def __init__(self):
        self._fast_threshold = settings.LLM_CASCADE_FAST_THRESHOLD    # 0.80
        self._mid_threshold = settings.LLM_CASCADE_MID_THRESHOLD      # 0.70
        self._fallback_threshold = settings.LLM_CASCADE_FALLBACK_THRESHOLD  # 0.60

    async def route(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        company_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rota a mensagem usando a escada de custo.

        Returns dict com: domain, confidence, model_used, latency_ms, tokens_est
        """
        total_start = time.time()

        # Tier 3a — Haiku (mais barato)
        result, tokens = await self._call_model(
            message=message,
            model_name=settings.LLM_FAST_MODEL,
        )
        if result and result.get("confidence", 0) >= self._fast_threshold:
            result["model_used"] = settings.LLM_FAST_MODEL
            result["tier"] = "haiku"
            result["tokens_est"] = tokens
            result["latency_ms"] = (time.time() - total_start) * 1000
            await self._record_tokens(company_id, tokens)
            return result

        # Tier 3b — Sonnet (capacidade média)
        logger.debug(
            "[LLMCascade] Haiku confidence=%.2f < %.2f, escalando para Sonnet",
            result.get("confidence", 0) if result else 0,
            self._fast_threshold,
        )
        result_sonnet, tokens_s = await self._call_model(
            message=message,
            model_name=settings.LLM_PRIMARY_MODEL,
        )
        tokens += tokens_s
        if result_sonnet and result_sonnet.get("confidence", 0) >= self._mid_threshold:
            result_sonnet["model_used"] = settings.LLM_PRIMARY_MODEL
            result_sonnet["tier"] = "sonnet"
            result_sonnet["tokens_est"] = tokens
            result_sonnet["latency_ms"] = (time.time() - total_start) * 1000
            await self._record_tokens(company_id, tokens)
            return result_sonnet

        # Tier 3c — Opus (mais caro — somente se absolutamente necessário)
        logger.debug(
            "[LLMCascade] Sonnet confidence=%.2f < %.2f, escalando para Opus",
            result_sonnet.get("confidence", 0) if result_sonnet else 0,
            self._mid_threshold,
        )
        result_opus, tokens_o = await self._call_model(
            message=message,
            model_name=settings.LLM_POWERFUL_MODEL,
        )
        tokens += tokens_o
        best = result_opus or result_sonnet or result or {
            "domain": "recruiter_assistant",
            "confidence": 0.3,
            "reason": "fallback",
        }
        best["model_used"] = settings.LLM_POWERFUL_MODEL
        best["tier"] = "opus"
        best["tokens_est"] = tokens
        best["latency_ms"] = (time.time() - total_start) * 1000
        await self._record_tokens(company_id, tokens)
        return best

    async def _call_model(
        self, message: str, model_name: str
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        """Chama um modelo específico e retorna (resultado_parseado, tokens_estimados)."""
        prompt = _ROUTING_PROMPT.format(message=message[:500])
        tokens_est = len(prompt) // 4

        try:
            response = await llm_service.generate(
                prompt=prompt,
                provider="claude",
                temperature=settings.LLM_ROUTER_TEMPERATURE,
            )
            tokens_est += len(response) // 4

            # Parse JSON
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text)
            return parsed, tokens_est

        except Exception as exc:
            logger.debug("[LLMCascade] _call_model(%s) falhou: %s", model_name, exc)
            return None, tokens_est

    async def _record_tokens(self, company_id: Optional[str], tokens: int) -> None:
        """Registra uso de tokens no budget do tenant (best-effort)."""
        if not company_id or tokens <= 0:
            return
        try:
            from app.orchestrator.tenant_budget import tenant_budget
            allowed, total, warning = await tenant_budget.check_and_record(company_id, tokens)
            if warning:
                logger.warning("[LLMCascade] %s", warning)
        except Exception as exc:
            logger.debug("[LLMCascade] record_tokens falhou: %s", exc)


# Singleton compartilhado
llm_cascade_router = LLMCascadeRouter()
