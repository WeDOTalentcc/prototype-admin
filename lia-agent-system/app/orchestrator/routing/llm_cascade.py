"""
LLM Cascade Router — Tier 3 do Cost Cascade Orchestrator.

Implementa a escada de custo Flash → Pro → Ultra (Gemini-first):
1. Tenta Gemini Flash (mais barato) primeiro
2. Se confiança < LLM_CASCADE_FAST_THRESHOLD, escalona para Gemini Pro / Claude Sonnet
3. Se confiança < LLM_CASCADE_MID_THRESHOLD, escalona para o modelo mais poderoso

O resultado inclui o modelo efetivamente usado e a confiança obtida,
para rastreabilidade de custo por tenant.

Integra com TenantBudget para registrar tokens consumidos por request_id.
"""
import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.domains.ai.services.llm import LLMProvider, llm_service
from lia_audit.audit_callback import _estimate_cost

logger = logging.getLogger(__name__)

# Prompt minimalista de roteamento — otimizado para Haiku (custo mínimo)
_ROUTING_PROMPT = """Você é um roteador de intenções para um sistema de RH.

Analise a mensagem do usuário e retorne um JSON com:
- domain: um de [job_management, sourcing, cv_screening, pipeline, talent,
  kanban_search, kanban_insight, kanban_action,
  pipeline_context, pipeline_decision, pipeline_action,
  sourcing_planner, sourcing_search, sourcing_enrich, sourcing_engagement,
  analytics, communication, automation, recruiter_assistant,
  agent_studio, digital_twin, recruitment_campaign,
  ats_integration, interview_scheduling, hiring_policy, talent_pool]
- confidence: float de 0.0 a 1.0
- reason: explicação curta (max 50 chars)

Guia de domínios sourcing:
  sourcing_planner: definir critérios de busca, sugerir skills, configurar parâmetros
  sourcing_search: buscar/filtrar/ver candidatos, talent pool, boolean search
  sourcing_enrich: analisar perfil, scoring WSI, comparar candidatos, shortlist, ranking
  sourcing_engagement: abordagem (outreach), gerar mensagem personalizada, rastrear resposta

Guia de dominios extras:
  agent_studio: criar/gerenciar agentes IA customizados, marketplace, calibracao
  digital_twin: digital twin do candidato, simulacao de fit cultural
  recruitment_campaign: campanhas de recrutamento, outreach em massa
  ats_integration: integracoes ATS externas, importar/exportar dados
  interview_scheduling: agendar/reagendar entrevistas, disponibilidade
  hiring_policy: politicas de contratacao, compliance, regras de aprovacao
  talent_pool: banco de talentos, pools de candidatos, nurturing

Guia de domínios kanban/pipeline:
  kanban_search: listar/ver candidatos, resumo de pipeline, métricas de etapa
  kanban_insight: gargalos, previsões, candidatos em risco, análise de funil
  kanban_action: mover/aprovar/reprovar candidatos, triagem em lote, relatórios
  pipeline_context: perfil do candidato, scores WSI, salário, disponibilidade
  pipeline_decision: validar transição, sub-status, preferências do recrutador
  pipeline_action: atualizar candidato, cancelar/reagendar entrevista, fairness

Mensagem: {message}

Responda SOMENTE com o JSON, sem texto extra."""


class LLMCascadeRouter:
    """
    Roteador LLM com escada de custo: Gemini Flash → Claude Sonnet → Claude Opus.

    Tenta o modelo mais barato (Gemini Flash) primeiro e escalona apenas se necessário.
    """

    def __init__(self):
        self._fast_threshold = settings.LLM_CASCADE_FAST_THRESHOLD    # 0.80
        self._mid_threshold = settings.LLM_CASCADE_MID_THRESHOLD      # 0.70
        self._fallback_threshold = settings.LLM_CASCADE_FALLBACK_THRESHOLD  # 0.60

    async def route(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        company_id: str | None = None,
        preferred_model: str | None = None,
        system_prompt_override: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Rota a mensagem usando a escada de custo.

        Args:
            message: Mensagem do usuário para roteamento.
            context: Contexto adicional opcional.
            company_id: ID da empresa para registro de tokens.
            preferred_model: Modelo preferido (E5 — Multi-Model). Se fornecido e
                             disponível, usado no tier primário em vez do FAST_MODEL.
                             Fail-safe: se o modelo falhar, a cascata padrão é usada.
            system_prompt_override: A/B testing — override the default routing prompt.
            request_id: Unique per-request identifier for granular cost tracking.

        Returns dict com: domain, confidence, model_used, latency_ms, tokens_est
        """
        total_start = time.time()
        if request_id is None:
            from app.orchestrator.guards.tenant_budget import generate_request_id
            request_id = generate_request_id()

        cost_accumulator: list[tuple[str, int]] = []

        # E5 — Multi-Model: tentar preferred_model antes da cascata padrão
        if preferred_model:
            try:
                result_pref, tokens_pref = await self._call_model(
                    message=message,
                    model_name=preferred_model,
                )
                if result_pref and result_pref.get("confidence", 0) >= self._mid_threshold:
                    result_pref["model_used"] = preferred_model
                    result_pref["tier"] = "preferred"
                    result_pref["tokens_est"] = tokens_pref
                    result_pref["latency_ms"] = (time.time() - total_start) * 1000
                    result_pref["request_id"] = request_id
                    await self._record_tokens(company_id, tokens_pref, model=preferred_model, request_id=request_id)
                    return result_pref
                cost_accumulator.append((preferred_model, tokens_pref))
                logger.debug(
                    "[LLMCascade] preferred_model=%s confidence=%.2f < %.2f, fallback para cascata padrão",
                    preferred_model,
                    result_pref.get("confidence", 0) if result_pref else 0,
                    self._mid_threshold,
                )
            except Exception as exc:
                logger.warning(
                    "[LLMCascade] preferred_model=%s falhou (fail-safe, usando cascata): %s",
                    preferred_model, exc,
                )

        # Tier 3a — Gemini Flash (mais barato)
        result, tokens_flash = await self._call_model(
            message=message,
            model_name=settings.LLM_FAST_MODEL,
            system_prompt_override=system_prompt_override,
        )
        cost_accumulator.append((settings.LLM_FAST_MODEL, tokens_flash))
        if result and result.get("confidence", 0) >= self._fast_threshold:
            tokens_total = sum(t for _, t in cost_accumulator)
            result["model_used"] = settings.LLM_FAST_MODEL
            result["tier"] = "gemini-flash"
            result["tokens_est"] = tokens_total
            result["latency_ms"] = (time.time() - total_start) * 1000
            result["request_id"] = request_id
            await self._record_tokens_multi(company_id, cost_accumulator, request_id=request_id)
            return result

        # Tier 3b — Claude Sonnet (capacidade média)
        logger.debug(
            "[LLMCascade] Gemini Flash confidence=%.2f < %.2f, escalando para Sonnet",
            result.get("confidence", 0) if result else 0,
            self._fast_threshold,
        )
        result_sonnet, tokens_s = await self._call_model(
            message=message,
            model_name=settings.LLM_PRIMARY_MODEL,
            system_prompt_override=system_prompt_override,
        )
        cost_accumulator.append((settings.LLM_PRIMARY_MODEL, tokens_s))
        if result_sonnet and result_sonnet.get("confidence", 0) >= self._mid_threshold:
            tokens_total = sum(t for _, t in cost_accumulator)
            result_sonnet["model_used"] = settings.LLM_PRIMARY_MODEL
            result_sonnet["tier"] = "sonnet"
            result_sonnet["tokens_est"] = tokens_total
            result_sonnet["latency_ms"] = (time.time() - total_start) * 1000
            result_sonnet["request_id"] = request_id
            await self._record_tokens_multi(company_id, cost_accumulator, request_id=request_id)
            return result_sonnet

        # Tier 3c — Claude Opus (mais caro — somente se absolutamente necessário)
        logger.debug(
            "[LLMCascade] Sonnet confidence=%.2f < %.2f, escalando para Opus",
            result_sonnet.get("confidence", 0) if result_sonnet else 0,
            self._mid_threshold,
        )
        result_opus, tokens_o = await self._call_model(
            message=message,
            model_name=settings.LLM_POWERFUL_MODEL,
            system_prompt_override=system_prompt_override,
        )
        cost_accumulator.append((settings.LLM_POWERFUL_MODEL, tokens_o))
        tokens_total = sum(t for _, t in cost_accumulator)
        best = result_opus or result_sonnet or result or {
            "domain": "recruiter_assistant",
            "confidence": 0.3,
            "reason": "fallback",
        }
        best["model_used"] = settings.LLM_POWERFUL_MODEL
        best["tier"] = "opus"
        best["tokens_est"] = tokens_total
        best["latency_ms"] = (time.time() - total_start) * 1000
        best["request_id"] = request_id
        await self._record_tokens_multi(company_id, cost_accumulator, request_id=request_id)
        return best

    @staticmethod
    def _provider_for_model(model_name: str) -> LLMProvider:
        """Deriva o provider (LLMProvider) a partir do nome do modelo.

        Mapeamento:
          gemini-* → "gemini"
          gpt-* / openai-* → "openai"
          deepseek-* → "deepseek"
          qualquer outro (claude-*) → "claude"
        """
        name = model_name.lower()
        if "gemini" in name:
            return "gemini"
        if "gpt" in name or "openai" in name:
            return "openai"
        if "deepseek" in name:
            return "deepseek"
        return "claude"

    async def _call_model(
        self,
        message: str,
        model_name: str,
        system_prompt_override: str | None = None,
    ) -> tuple[dict[str, Any] | None, int]:
        """Chama um modelo específico e retorna (resultado_parseado, tokens_estimados).

        O provider é derivado do nome do modelo via _provider_for_model:
          gemini-* → provider="gemini"
          gpt-* / openai-* → provider="openai"
          deepseek-* → provider="deepseek"
          qualquer outro → provider="claude"
        """
        base_prompt = system_prompt_override or _ROUTING_PROMPT
        prompt = base_prompt.replace("{message}", message[:500])
        tokens_est = len(prompt) // 4
        provider: LLMProvider = self._provider_for_model(model_name)

        try:
            response = await llm_service.generate(
                prompt=prompt,
                provider=provider,
                model=model_name,
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
            logger.debug("[LLMCascade] _call_model(%s, provider=%s) falhou: %s", model_name, provider, exc)
            return None, tokens_est

    async def _record_tokens(
        self,
        company_id: str | None,
        tokens: int,
        model: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Registra uso de tokens no budget do tenant com per-request tracking."""
        if not company_id or tokens <= 0:
            return
        try:
            from app.orchestrator.guards.tenant_budget import tenant_budget
            tokens_in = tokens // 2
            tokens_out = tokens - tokens_in
            cost_usd = _estimate_cost(model, tokens_in, tokens_out)
            allowed, total, warning = await tenant_budget.check_and_record(
                company_id,
                tokens,
                request_id=request_id,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost_usd=cost_usd,
                model=model,
            )
            if warning:
                logger.warning("[LLMCascade] %s", warning)
        except Exception as exc:
            logger.debug("[LLMCascade] record_tokens falhou: %s", exc)

    async def _record_tokens_multi(
        self,
        company_id: str | None,
        attempts: list[tuple[str, int]],
        request_id: str | None = None,
    ) -> None:
        """Record tokens with per-model cost summed across cascade attempts."""
        if not company_id or not attempts:
            return
        try:
            from app.orchestrator.guards.tenant_budget import tenant_budget
            tokens_total = sum(t for _, t in attempts)
            total_cost = 0.0
            for model_name, toks in attempts:
                t_in = toks // 2
                t_out = toks - t_in
                total_cost += _estimate_cost(model_name, t_in, t_out)
            tokens_in = tokens_total // 2
            tokens_out = tokens_total - tokens_in
            final_model = attempts[-1][0] if attempts else None
            allowed, total, warning = await tenant_budget.check_and_record(
                company_id,
                tokens_total,
                request_id=request_id,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost_usd=total_cost,
                model=final_model,
            )
            if warning:
                logger.warning("[LLMCascade] %s", warning)
        except Exception as exc:
            logger.debug("[LLMCascade] record_tokens_multi falhou: %s", exc)


# Singleton compartilhado
llm_cascade_router = LLMCascadeRouter()
