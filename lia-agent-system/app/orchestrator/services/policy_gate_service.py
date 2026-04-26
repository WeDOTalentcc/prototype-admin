"""
Policy Gate Service — canonical wrapper sobre PolicyEngine.

Sprint II.5 da migração V1→V2 (LIA-D06 cleanup). Cria abstração canônica
para validação de policies que será usada pelo V2 MainOrchestrator a partir
do Sprint III, sem alterar `policy_engine.py` (que continua sendo usado pelo
V1 deprecated).

## Por que esta camada?

- `PolicyEngine` (`app/orchestrator/policy_engine.py`) tem API legada com
  `dict[str, Any]` como retorno e dependências de DB direta — adequado ao V1
  mas não ideal para V2.
- `PolicyGateService` oferece:
  1. Type-safe `PolicyResult` dataclass (em vez de dict ambíguo)
  2. Tracing-friendly span attributes ready (P1 LGPD multi-tenant)
  3. Dependency injection (PolicyEngine é injetado, não instanciado)
  4. Async-first API consistente com V2

## Taxonomia harness-engineering

`[guide]` — decide se request é permitido (feedforward). Bloqueia execução
quando policy negada.

## Reference

ADR-019 — Orchestrator V1→V2 Consolidation, Sprint II.5
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

from app.orchestrator.policy_engine import PolicyEngine


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


class PolicyGateService:
    """
    Canonical service para policy validation no orchestrator pipeline.

    Wraps PolicyEngine com API type-safe + dependency injection. Usado pelo
    V2 MainOrchestrator (a partir do Sprint III) como Phase 0.5 (gate logic
    after PendingAction, before ActionExecutor).

    ## Usage

        # Initialize via factory ou DI
        engine = PolicyEngine(db_service=db)
        gate = PolicyGateService(policy_engine=engine)

        # Validate
        result = await gate.validate(
            intent="candidate_search",
            user_id="user-123",
            context={"company_id": "tenant-a", "credits": 100},
        )
        if not result.allowed:
            return {"error": result.reason, "approval": result.requires_approval}

    ## Multi-tenant safety (P0 LGPD)

    Toda chamada exige `context["company_id"]` para tenant isolation. Se ausente,
    retorna `allowed=False` com reason explanatório. Comportamento idêntico ao
    PolicyEngine (que já valida internamente).

    ## Reference

    ADR-019 — Sprint II.5
    """

    def __init__(self, policy_engine: PolicyEngine):
        """
        Args:
            policy_engine: instância configurada de PolicyEngine
                (recomenda-se DI via factory).
        """
        self._engine = policy_engine

    async def validate(
        self,
        intent: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> PolicyResult:
        """
        Valida request contra policies do tenant.

        Fast-path para SAFE_INTENTS — não chama PolicyEngine para intents
        read-only. Para outros intents, delega ao PolicyEngine e converte
        retorno legado para PolicyResult.

        Args:
            intent: Intent classificado (e.g., "candidate_search",
                "general_chat", "screening_request").
            user_id: ID do usuário fazendo a request (para audit + rate limiting).
            context: Contexto adicional. Deve incluir `company_id` para
                multi-tenant isolation.

        Returns:
            PolicyResult com allowed/reason/constraints. Nunca lança exceção
            (em caso de erro interno, retorna allowed=False com reason).
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

        # Delega para PolicyEngine canonical (Sprint III mantém este caminho)
        try:
            legacy_result = await self._engine.validate_request(
                intent=intent,
                user_id=user_id,
                context=context,
            )
            return PolicyResult.from_legacy_dict(
                legacy_result, intent=intent, user_id=user_id
            )
        except Exception as e:
            # Fail-safe: nunca lança para o caller — retorna denied com reason
            return PolicyResult(
                allowed=False,
                reason=f"Policy validation error: {type(e).__name__}: {e}",
                constraints={"error": True},
                intent=intent,
                user_id=user_id,
            )

    def record_usage(
        self, tenant_id: str, usage_type: str = "chat_requests"
    ) -> None:
        """
        Delega ao PolicyEngine para registrar uso (rate limiting tracking).

        Sync method — não async pois PolicyEngine.record_usage é sync.
        Usar após validate() em produção quando request é executada.

        Args:
            tenant_id: ID do tenant (company_id) para rate limiting tracking.
            usage_type: Tipo de uso ("chat_requests", "action_executions",
                "llm_calls"). Default: "chat_requests".
        """
        self._engine.record_usage(tenant_id=tenant_id, usage_type=usage_type)

    @property
    def underlying_engine(self) -> PolicyEngine:
        """Acesso ao PolicyEngine subjacente (para casos especiais e testes)."""
        return self._engine
