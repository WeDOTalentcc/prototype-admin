"""
Policy Gate Service — canonical wrapper sobre PolicyEngine.

Sprint II.5 da migração V1→V2 (LIA-D06 cleanup). Cria abstração canônica
para validação de policies usada pelo V2 MainOrchestrator (Sprint III+).

## WT-2022 P3.1 — V1→V2 migration (2026-05-21)

Antes (Sprint II.5): wrappava `PolicyEngine` V1 (`app/orchestrator/policy_engine.py`)
com `validate_request/validate_search/...` coordinator-style + DEFAULT_POLICIES
hardcoded.

Agora (P3.1 canonical, 2026-05-21): wrappa `PolicyEngineService` V2
(`app/domains/policy/services/policy_engine_service.py`) com generic
`evaluate/check_rate_limit/...` que lê 3 tabelas canônicas
(business_rules + rate_limit_rules + escalation_rules). Mapeamento de intent →
action é interno (V1→V2 compat adapter).

Decisão Paulo 2026-05-21: V1 PolicyEngine fica em runtime path APENAS
para callers legacy (orchestrator.py, tests, job_creation/policy_gate.py).
Toda nova validação canonical roda via V2.

## Por que esta camada?

- `PolicyEngineService` V2 retorna `EvaluationResult` rico (matching_rule,
  evaluation_time_ms, requires_approval) — `PolicyGateService` adapta pro
  formato compacto `PolicyResult` que o orchestrator espera.
- `PolicyGateService` oferece:
  1. Type-safe `PolicyResult` dataclass (em vez de dict ambíguo)
  2. Tracing-friendly span attributes ready (P1 LGPD multi-tenant)
  3. Dependency injection (engine V2 é injetado, não instanciado)
  4. Async-first API consistente com V2
  5. Fail-safe: V2 retornando exception → PolicyResult com allowed=False+reason

## Taxonomia harness-engineering

`[guide]` — decide se request é permitido (feedforward). Bloqueia execução
quando policy negada.

## Reference

- ADR-019 — Orchestrator V1→V2 Consolidation, Sprint II.5
- WT-2022 P3.1 — V1→V2 PolicyEngine migration, 2026-05-21
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Final

logger = logging.getLogger(__name__)

# WT-2022 P3.1: V2 canonical engine. Não importamos V1 PolicyEngine no top —
# import lazy só no compat path (deprecated) para evitar instanciação acidental.
try:
    from app.domains.policy.services.policy_engine_service import (
        EvaluationResult as _V2EvaluationResult,
        PolicyEngineService,
    )
    _V2_AVAILABLE = True
except Exception as _e:
    logger.warning(
        "[P3.1] PolicyEngineService V2 import failed (%s); PolicyGateService "
        "will fall back to allow-all with reason='engine_unavailable'.",
        _e,
    )
    PolicyEngineService = None  # type: ignore[assignment,misc]
    _V2EvaluationResult = None  # type: ignore[assignment,misc]
    _V2_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Result types — type-safe vs dict[str, Any] do V1
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PolicyResult:
    """
    Resultado canônico de validação de policy.

    Substitui o dict[str, Any] retornado pelo PolicyEngine.validate_request,
    com type safety e API previsível.

    Attributes:
        allowed: True se request pode prosseguir.
        reason: Mensagem human-readable da decisão (vazia se allowed=True
            sem constraints).
        constraints: Constraints adicionais (e.g., requires_approval,
            usage_remaining). Sempre dict (nunca None) para evitar None checks.
        intent: Intent que foi avaliado.
        user_id: User cuja request foi avaliada.
    """

    allowed: bool
    reason: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)
    intent: str = ""
    user_id: str = ""

    @classmethod
    def from_legacy_dict(
        cls, legacy: dict[str, Any], *, intent: str, user_id: str
    ) -> PolicyResult:
        """
        Converte retorno legado do PolicyEngine.validate_request para PolicyResult.

        Mantém backward compatibility durante Sprint III canary.
        """
        return cls(
            allowed=bool(legacy.get("allowed", False)),
            reason=str(legacy.get("reason", "")),
            constraints=dict(legacy.get("constraints", {})),
            intent=intent,
            user_id=user_id,
        )

    @property
    def requires_approval(self) -> bool:
        """Helper: shortcut para constraints.requires_approval (HITL gate)."""
        return bool(self.constraints.get("requires_approval", False))

    def to_legacy_dict(self) -> dict[str, Any]:
        """
        Converte de volta para dict legado — usado quando service precisa
        retornar resposta no formato esperado pelo V1 ou main_orchestrator.

        Garante zero quebra de contrato durante a migração.
        """
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "constraints": dict(self.constraints),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Default constraints — quando context não fornece info, defaults são seguros
# ─────────────────────────────────────────────────────────────────────────────

# Intent que sempre são permitidos sem checagem de quotas (read-only operations)
SAFE_INTENTS: Final[frozenset[str]] = frozenset({
    "general_chat",
    "navigation",
    "help",
    "feedback",
})


# WT-2022 P3.1: mapeamento intent (V1 coordinator-style) → action (V2 generic).
# V2 PolicyEngineService.evaluate(action, context, ...) recebe action canonical
# (string que casa com BusinessRule.actions[]). Mantemos esse map central para
# o boundary V1→V2 ficar previsível.
_INTENT_TO_V2_ACTION: Final[dict[str, str]] = {
    "candidate_search": "candidate_search",
    "candidate_screening": "candidate_screening",
    "communication": "send_communication",
    "voice_screening": "voice_screening",
    "bulk_email": "send_bulk_communication",
    "interview_schedule": "schedule_interview",
}


class PolicyGateService:
    """
    Canonical service para policy validation no orchestrator pipeline (V2).

    WT-2022 P3.1 (2026-05-21): wrappa `PolicyEngineService` V2 com adapter que:
    1. Mapeia intent → action via `_INTENT_TO_V2_ACTION`
    2. Converte `EvaluationResult` (V2) → `PolicyResult` (compact, retro-compat)
    3. Fail-safe: exceção → PolicyResult(allowed=False) com reason

    Usado pelo V2 MainOrchestrator (Sprint III+) como Phase 0.5 (gate logic
    after PendingAction, before ActionExecutor).

    ## Usage

        # Initialize — V2 engine é stateless (cache interno)
        from app.domains.policy.services.policy_engine_service import (
            PolicyEngineService,
        )
        gate = PolicyGateService(policy_engine=PolicyEngineService())

        # Validate
        result = await gate.validate(
            intent="candidate_search",
            user_id="user-123",
            context={"company_id": "tenant-a", "credits": 100},
        )
        if not result.allowed:
            return {"error": result.reason, "approval": result.requires_approval}

    ## Multi-tenant safety (P0 LGPD)

    Toda chamada exige `context["company_id"]` para tenant isolation. V2
    PolicyEngineService propaga `company_id` para o repository que faz
    company-scoped query. Se ausente, fallback para regras globais (V2 behavior).

    ## Compat shim — legacy callers

    O construtor aceita também V1 `PolicyEngine` (deprecated). Quando V1 é
    passado, emite warning e roteia via `_validate_via_v1_legacy_compat`.
    Manter por 1-2 sprints até zerar callers V1 — depois remover.

    ## Reference

    - ADR-019 — Sprint II.5
    - WT-2022 P3.1 — V1→V2 migration (2026-05-21)
    """

    def __init__(self, policy_engine: Any = None):
        """
        Args:
            policy_engine: instância de `PolicyEngineService` (V2 canonical) OU
                `PolicyEngine` (V1 legacy, deprecated). Se None, cria V2 default.
        """
        if policy_engine is None:
            if not _V2_AVAILABLE:
                logger.error(
                    "[P3.1] PolicyGateService initialized but neither "
                    "PolicyEngineService V2 nor explicit engine available. "
                    "All validate() calls will return allow-all."
                )
                self._engine = None
                self._engine_version = "none"
            else:
                self._engine = PolicyEngineService()
                self._engine_version = "v2"
        else:
            # Detect engine version pela presença de método canonical V2
            if hasattr(policy_engine, "evaluate") and not hasattr(
                policy_engine, "validate_request"
            ):
                self._engine = policy_engine
                self._engine_version = "v2"
            elif hasattr(policy_engine, "validate_request"):
                logger.warning(
                    "[P3.1 DEPRECATED] PolicyGateService received V1 PolicyEngine "
                    "instance. Migration to PolicyEngineService V2 pending. "
                    "Callers should pass V2 engine (see ADR-WT-2022)."
                )
                self._engine = policy_engine
                self._engine_version = "v1"
            else:
                logger.error(
                    "[P3.1] PolicyGateService received unrecognized engine type %s; "
                    "treating as no-op (allow-all).",
                    type(policy_engine).__name__,
                )
                self._engine = None
                self._engine_version = "none"

    async def validate(
        self,
        intent: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> PolicyResult:
        """
        Valida request contra policies do tenant.

        Fast-path para SAFE_INTENTS — não chama engine para intents read-only.
        Demais intents: V2 generic `evaluate(action, context, ...)` ou V1
        coordinator-style fallback.

        Args:
            intent: Intent classificado (e.g., "candidate_search",
                "general_chat", "communication").
            user_id: ID do usuário (para audit + rate limiting).
            context: Contexto adicional. Deve incluir `company_id` para
                multi-tenant isolation.

        Returns:
            PolicyResult com allowed/reason/constraints. Nunca lança exceção.
        """
        # Fast-path: intents seguros não precisam de validation engine
        if intent in SAFE_INTENTS:
            return PolicyResult(
                allowed=True,
                reason="",
                constraints={},
                intent=intent,
                user_id=user_id,
            )

        if self._engine is None:
            return PolicyResult(
                allowed=True,
                reason="Policy engine unavailable — allow-all fallback (P3.1)",
                constraints={"engine_unavailable": True},
                intent=intent,
                user_id=user_id,
            )

        try:
            if self._engine_version == "v2":
                return await self._validate_via_v2(intent, user_id, context)
            else:  # v1 legacy compat (deprecated)
                return await self._validate_via_v1_legacy_compat(
                    intent, user_id, context
                )
        except Exception as e:
            # Fail-safe: nunca lança para o caller — retorna denied com reason
            logger.warning(
                "[PolicyGate] %s engine raised %s: %s",
                self._engine_version, type(e).__name__, e,
            )
            return PolicyResult(
                allowed=False,
                reason=f"Policy validation error: {type(e).__name__}: {e}",
                constraints={"error": True},
                intent=intent,
                user_id=user_id,
            )

    async def _validate_via_v2(
        self,
        intent: str,
        user_id: str,
        context: dict[str, Any] | None,
    ) -> PolicyResult:
        """
        WT-2022 P3.1: roteia validate() via V2 PolicyEngineService.evaluate.

        Mapeia intent → action canonical, e converte EvaluationResult rica do
        V2 para PolicyResult compact que o orchestrator consome.
        """
        ctx = dict(context or {})
        company_id = ctx.get("company_id") or ctx.get("tenant_id")
        action = _INTENT_TO_V2_ACTION.get(intent, intent)

        # V2 evaluate é generic — context passa direto, action é mapeada
        eval_result = await self._engine.evaluate(
            action=action,
            context=ctx,
            agent_name=ctx.get("agent_name"),
            company_id=str(company_id) if company_id else None,
            user_id=user_id,
            check_rate_limit=True,
            dry_run=False,
        )

        # EvaluationResult → PolicyResult adapter
        constraints: dict[str, Any] = {}
        if eval_result.requires_approval:
            constraints["requires_approval"] = True
        if eval_result.approval_config:
            constraints["approval_config"] = eval_result.approval_config
        if eval_result.rate_limit_status:
            constraints["rate_limit_status"] = eval_result.rate_limit_status
        if eval_result.matching_rule is not None:
            constraints["matching_rule_id"] = getattr(
                eval_result.matching_rule, "id", None
            )

        return PolicyResult(
            allowed=bool(eval_result.allowed),
            reason=eval_result.reason or "",
            constraints=constraints,
            intent=intent,
            user_id=user_id,
        )

    async def _validate_via_v1_legacy_compat(
        self,
        intent: str,
        user_id: str,
        context: dict[str, Any] | None,
    ) -> PolicyResult:
        """
        WT-2022 P3.1 DEPRECATED compat shim — só roda quando V1 PolicyEngine é
        injetado explicitamente. Será removido quando todos os callers migrarem
        para V2 (ETA: próxima sprint).
        """
        legacy_result = await self._engine.validate_request(
            intent=intent,
            user_id=user_id,
            context=context,
        )
        return PolicyResult.from_legacy_dict(
            legacy_result, intent=intent, user_id=user_id
        )

    def record_usage(
        self, tenant_id: str, usage_type: str = "chat_requests"
    ) -> None:
        """
        Registra uso (rate limiting tracking).

        V2: rate limit tracking acontece dentro de `evaluate()` automaticamente
        via `check_rate_limit=True`. Mantemos este método como no-op (V2) ou
        delega para V1 legacy (compat) — preservar contrato para callers
        existentes.

        Args:
            tenant_id: ID do tenant (company_id) para rate limiting tracking.
            usage_type: Tipo de uso. Default: "chat_requests".
        """
        if self._engine_version == "v1" and hasattr(self._engine, "record_usage"):
            self._engine.record_usage(
                tenant_id=tenant_id, usage_type=usage_type
            )
        # V2: no-op — rate limit é tracked dentro de evaluate() (canonical)

    @property
    def underlying_engine(self) -> Any:
        """Acesso ao engine subjacente (V1 ou V2 — para tests e casos especiais)."""
        return self._engine

    @property
    def engine_version(self) -> str:
        """'v1' (deprecated), 'v2' (canonical) ou 'none' (fallback allow-all)."""
        return self._engine_version
