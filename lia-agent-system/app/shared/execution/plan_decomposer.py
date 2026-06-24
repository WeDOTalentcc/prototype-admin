"""
PlanDecomposer — LLM-based multi-step intent decomposition.

Replaces the regex-based PlanDetector with intelligent decomposition:
1. Fast heuristic pre-filter (< 1ms) — skips LLM for simple messages
2. LLM structured output — decomposes compound requests into domain actions
3. Registry validation — every step verified against real DomainRegistry
4. ExecutionPlan assembly — same output format as PlanDetector

The downstream PlanExecutor, DomainWorkflow, and SSE progress events
remain unchanged — this module is a drop-in replacement for PlanDetector.detect().
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from pydantic import BaseModel, Field

from app.domains.base import DomainAction
from app.domains.registry import DomainRegistry
from app.shared.execution.execution_plan import AgentTask, ExecutionPlan
from app.shared.execution.plan_detector import (
    JOB_CREATION_ACTION_IDS,
    PlanDetector,
)

logger = logging.getLogger(__name__)

MAX_PLAN_STEPS = 5
_DECOMPOSE_MAX_TOKENS = 512
_DECOMPOSE_PROVIDER = "gemini"
_CONFIDENCE_THRESHOLD = 0.6


# ── Pydantic models for structured LLM output ───────────────────────────────


class DecomposedStep(BaseModel):
    """A single step in a multi-step plan."""

    domain_id: str = Field(description="ID do domínio (ex: sourcing, cv_screening)")
    action_id: str = Field(description="ID da ação dentro do domínio (ex: search_candidates)")
    description: str = Field(description="Breve descrição do que este passo faz")
    context_from_previous: bool = Field(
        default=False,
        description="True se este passo usa o resultado do passo anterior como input",
    )


class DecompositionResult(BaseModel):
    """LLM output: whether the query is multi-step and how to decompose it."""

    is_multi_step: bool = Field(
        description="True se o pedido contém MÚLTIPLAS ações distintas que devem ser executadas em sequência"
    )
    confidence: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="Confiança na decomposição (0-1)",
    )
    steps: list[DecomposedStep] = Field(
        default_factory=list,
        description="Lista ordenada de passos. Vazia se is_multi_step=false.",
    )
    reasoning: str = Field(
        default="",
        description="Breve justificativa da decisão (1-2 frases)",
    )


# ── Heuristic pre-filter ────────────────────────────────────────────────────

_MULTI_STEP_SIGNALS = re.compile(
    r"("
    # Explicit sequencing words
    r",\s*(?:e\s+)?(?:depois|então|aí|em seguida)\b"
    r"|\be\s+(?:depois|então|também|aí|em seguida)\b"
    r"|\bprimeiro\b.{3,80}\bdepois\b"
    # Two verbs (infinitive OR conjugated) joined by "e"
    # Covers: "buscar X e comparar Y", "busca X e compara Y", "encontre X e avalie Y"
    r"|\b\w{3,}(?:ar|er|ir|a|e)\b.{1,60}\be\s+\w{3,}(?:ar|er|ir|a|e)\b"
    # Comma + verb pattern: "busca X, avalia Y e agenda Z"
    r"|,\s*\w{3,}(?:ar|er|ir|a|e)\b"
    # Numbered lists (1. faz X 2. faz Y)
    r"|\b[12]\.\s*\w"
    r")",
    re.IGNORECASE,
)

_SINGLE_INTENT_SIGNALS = re.compile(
    r"^("
    r"oi\b|olá\b|bom dia\b|boa tarde\b|boa noite\b"
    r"|como\s+(vai|está|tá|anda)\b"
    r"|obrigad[oa]\b|valeu\b|blz\b"
    r"|o que é\b|me explica\b|qual\b"
    r"|sim\b|não\b|ok\b|tá\b|entendi\b"
    r")",
    re.IGNORECASE,
)


def _passes_heuristic(query: str) -> bool:
    """Fast pre-filter: True if query MIGHT be multi-step (worth calling LLM)."""
    clean = query.strip()
    if len(clean) < 15:
        return False
    if _SINGLE_INTENT_SIGNALS.search(clean):
        return False
    return bool(_MULTI_STEP_SIGNALS.search(clean))


# ── Action catalog builder ───────────────────────────────────────────────────


def _build_action_catalog(registry: DomainRegistry) -> str:
    """Build a compact text catalog of all domain actions for the LLM prompt."""
    all_actions = registry.get_all_actions()
    lines: list[str] = []
    for domain_id in sorted(all_actions):
        actions = all_actions[domain_id]
        if not actions:
            continue
        lines.append(f"\n## {domain_id}")
        for a in actions:
            aid = a.action_id or a.id
            if not aid:
                continue
            desc = a.description or a.name or aid
            lines.append(f"  - {aid}: {desc}")
    return "\n".join(lines)


# ── System prompt ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """\
Você é o planejador de tarefas da LIA, assistente de recrutamento da WeDOTalent.

## Sua função

Analise a mensagem do recrutador e determine se contém MÚLTIPLAS ações distintas \
que devem ser executadas em sequência. Se sim, decomponha em passos ordenados \
usando EXCLUSIVAMENTE as ações do catálogo abaixo.

## Regras

1. Se a mensagem é conversa normal, pergunta simples, ou UMA ÚNICA ação → \
   retorne is_multi_step=false, steps vazio.
2. Se a mensagem pede 2 ou mais ações distintas em sequência → retorne \
   is_multi_step=true com os steps ordenados.
3. NUNCA invente domain_id ou action_id — use EXATAMENTE os valores do catálogo.
4. Máximo {max_steps} steps por plano.
5. Se um passo usa o resultado do anterior (ex: "busca candidatos e compara OS RESULTADOS"), \
   marque context_from_previous=true no segundo passo.
6. PROIBIDO criar vagas (create_job, create_job_vacancy, etc.) — criação de vaga é \
   exclusiva do wizard. Se o recrutador pedir para criar vaga E fazer algo, \
   retorne is_multi_step=false.
7. Prefira a ação mais específica disponível. Ex: se existe "rank_candidates", \
   use em vez de "search_candidates" para ranquear.

## Catálogo de ações disponíveis
{catalog}

## Exemplos

Mensagem: "busca desenvolvedores Python e compara os perfis"
→ is_multi_step=true, steps=[sourcing.search_candidates, cv_screening.compare_candidates]

Mensagem: "encontra designers, avalia contra a vaga e agenda entrevista"
→ is_multi_step=true, steps=[sourcing.search_candidates, cv_screening.score_cv, \
interview_scheduling.scheduling_schedule_interview]

Mensagem: "como está a vaga de dev senior?"
→ is_multi_step=false (pergunta simples, uma ação)

Mensagem: "cria uma vaga de dev e busca candidatos"
→ is_multi_step=false (criação de vaga é proibida no Plan&Execute)
"""


# ── PlanDecomposer ───────────────────────────────────────────────────────────


class PlanDecomposer:
    """LLM-based multi-step intent decomposition with registry validation."""

    _catalog_cache: str | None = None

    def __init__(
        self,
        registry: DomainRegistry | None = None,
        fallback_detector: PlanDetector | None = None,
    ):
        self._registry = registry or DomainRegistry()
        self._fallback = fallback_detector

    async def decompose(
        self,
        *,
        user_message: str,
        enriched_context: str,
        company_id: str | None = None,
    ) -> ExecutionPlan | None:
        """
        Decompose a user query into a multi-step ExecutionPlan.

        Args:
            user_message: The original recruiter message (no history prefix).
                          Used for heuristic pre-filter and regex fast-path.
            enriched_context: The full enriched string with conversation history
                              and entity hints. Sent to LLM for richer decomposition.
            company_id: Tenant ID for audit/logging.

        Returns None if the query is single-step or conversational.
        Falls back gracefully on any LLM error.
        """
        t0 = time.perf_counter()

        # ── Fast path: regex fallback (0ms, covers existing patterns) ────
        if self._fallback:
            regex_plan = self._fallback.detect(user_message)
            if regex_plan and len(regex_plan.tasks) >= 2:
                elapsed = (time.perf_counter() - t0) * 1000
                logger.info(
                    "[PlanDecomposer] regex fast-path matched pattern=%s (%.0fms)",
                    regex_plan.detected_pattern,
                    elapsed,
                )
                return regex_plan

        # ── Heuristic pre-filter ─────────────────────────────────────────
        if not _passes_heuristic(user_message):
            logger.info(
                "[PlanDecomposer] heuristic: no multi-step signal in: %.80s",
                user_message,
            )
            return None
        logger.info(
            "[PlanDecomposer] heuristic passed, calling LLM for: %.80s",
            user_message,
        )

        # ── LLM decomposition ───────────────────────────────────────────
        try:
            result = await self._call_llm(enriched_context)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.warning(
                "[PlanDecomposer] LLM call failed (%.0fms, fail-open): %s",
                elapsed,
                exc,
            )
            return None

        elapsed = (time.perf_counter() - t0) * 1000

        if not result.is_multi_step or result.confidence < _CONFIDENCE_THRESHOLD:
            logger.info(
                "[PlanDecomposer] LLM says single-step (confidence=%.2f, %.0fms)",
                result.confidence,
                elapsed,
            )
            return None

        if len(result.steps) < 2:
            logger.info("[PlanDecomposer] LLM returned < 2 steps, skipping")
            return None

        # ── Validate and build plan ──────────────────────────────────────
        plan = self._validate_and_build_plan(result, enriched_context)

        if plan:
            logger.info(
                "[PlanDecomposer] LLM decomposed into %d steps (confidence=%.2f, %.0fms): %s",
                len(plan.tasks),
                result.confidence,
                elapsed,
                ", ".join(f"{t.domain_id}.{t.action_id}" for t in plan.tasks),
            )
        else:
            logger.info(
                "[PlanDecomposer] validation reduced to <2 valid steps (%.0fms)",
                elapsed,
            )

        return plan

    async def _call_llm(self, enriched_context: str) -> DecompositionResult:
        """Call LLM with structured output to decompose the query."""
        from app.domains.ai.services.llm import LLMService

        catalog = self._get_catalog()
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            catalog=catalog,
            max_steps=MAX_PLAN_STEPS,
        )

        logger.info(
            "[PlanDecomposer] calling LLM (provider=%s, max_tokens=%d)",
            _DECOMPOSE_PROVIDER,
            _DECOMPOSE_MAX_TOKENS,
        )
        llm = LLMService()
        result: DecompositionResult = await llm.generate_structured(
            messages=[{"role": "user", "content": enriched_context}],
            output_model=DecompositionResult,
            provider=_DECOMPOSE_PROVIDER,
            system_prompt=system_prompt,
            max_tokens=_DECOMPOSE_MAX_TOKENS,
        )
        logger.info(
            "[PlanDecomposer] LLM result: is_multi_step=%s confidence=%.2f steps=%d reasoning=%.60s",
            result.is_multi_step,
            result.confidence,
            len(result.steps),
            result.reasoning,
        )
        return result

    def _get_catalog(self) -> str:
        """Get or build the action catalog (cached after first call)."""
        if PlanDecomposer._catalog_cache is None:
            PlanDecomposer._catalog_cache = _build_action_catalog(self._registry)
        return PlanDecomposer._catalog_cache

    def _validate_and_build_plan(
        self,
        result: DecompositionResult,
        original_query: str,
    ) -> ExecutionPlan | None:
        """Validate LLM steps against DomainRegistry and build ExecutionPlan."""
        valid_steps: list[DecomposedStep] = []

        for step in result.steps[:MAX_PLAN_STEPS]:
            domain = self._registry.get_instance(step.domain_id)
            if not domain:
                logger.debug(
                    "[PlanDecomposer] dropping step: domain '%s' not registered",
                    step.domain_id,
                )
                continue

            domain_actions = domain.get_allowed_actions()
            action_ids = {(a.action_id or a.id) for a in domain_actions}
            if step.action_id not in action_ids:
                logger.debug(
                    "[PlanDecomposer] dropping step: action '%s' not in domain '%s' (available: %s)",
                    step.action_id,
                    step.domain_id,
                    sorted(action_ids)[:10],
                )
                continue

            if step.action_id in JOB_CREATION_ACTION_IDS:
                logger.warning(
                    "[PlanDecomposer] BLOCKED job creation action '%s' in plan (INVIOLABLE)",
                    step.action_id,
                )
                return None

            valid_steps.append(step)

        if len(valid_steps) < 2:
            return None

        plan = ExecutionPlan()
        plan.original_query = original_query
        plan.detected_pattern = f"llm_decomposed:{result.reasoning[:60]}"

        for i, step in enumerate(valid_steps):
            context_mappings: dict[str, str] = {}
            depends_on: list[str] = []

            if i > 0 and step.context_from_previous:
                prev_id = f"task_{i - 1}"
                depends_on = [prev_id]
                context_mappings = {
                    "previous_result": f"{prev_id}.result",
                    "previous_data": f"{prev_id}.data",
                }
            elif i > 0:
                depends_on = [f"task_{i - 1}"]

            task = AgentTask(
                task_id=f"task_{i}",
                domain_id=step.domain_id,
                action_id=step.action_id,
                params={},
                depends_on=depends_on,
                context_mappings=context_mappings,
            )
            plan.add_task(task)

        return plan

    def get_catalog_summary(self) -> dict[str, int]:
        """Return domain → action count for diagnostics."""
        all_actions = self._registry.get_all_actions()
        return {d: len(acts) for d, acts in sorted(all_actions.items())}
