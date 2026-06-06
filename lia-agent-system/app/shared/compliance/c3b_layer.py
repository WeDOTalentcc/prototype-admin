"""
C3b Compliance Layer — Strangler pattern for WS/SSE compliance.

Pre-compliance: PII stripping + FairnessGuard L3 for HR-sensitive domains.
Post-compliance: FactChecker + AuditService logging.

Feature flag: LIA_DISABLE_C3B=1 disables both functions (passthrough).
"""
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_C3B_DISABLED = os.environ.get("LIA_DISABLE_C3B", "0") == "1"

# W3-016 (2026-05-23): audit event quando kill-switch ativo em prod/staging.
# Compliance posture: bypass C3b deve ser auditável + visível em alarmes.
_C3B_DISABLED_AUDIT_EMITTED = False


async def _emit_c3b_disabled_audit_once() -> None:
    """Emit audit event uma única vez quando _C3B_DISABLED=True em prod/staging.

    Idempotente · não-bloqueante · fail-safe (audit failure NUNCA crasha c3b).
    """
    global _C3B_DISABLED_AUDIT_EMITTED
    if _C3B_DISABLED_AUDIT_EMITTED or not _C3B_DISABLED:
        return
    env = os.environ.get("APP_ENV", "development")
    if env not in ("production", "prod", "staging"):
        # Dev: warn-only, sem audit cost
        _C3B_DISABLED_AUDIT_EMITTED = True
        logger.warning("[C3b] LIA_DISABLE_C3B=1 em ambiente %s — warn-only", env)
        return
    try:
        from app.shared.compliance.audit_service import audit_service
        await audit_service.log_decision(
            company_id="system",
            agent_name="c3b_layer",
            decision_type="compliance_disabled",
            action="kill_switch_active",
            decision=f"LIA_DISABLE_C3B=1 in {env}",
            reasoning=[
                f"C3b compliance layer DISABLED em ambiente {env!r}",
                "Toda call a pre_compliance/post_compliance vira passthrough",
                "Audit emitido 1x na primeira call após boot (idempotente)",
            ],
            criteria_used=["LIA_DISABLE_C3B", "APP_ENV"],
        )
        logger.warning(
            "[C3b] LIA_DISABLE_C3B=1 em prod/staging · audit event emitido"
        )
    except Exception as exc:
        logger.error("[C3b] Audit emit failed (non-blocking): %s", exc)
    finally:
        _C3B_DISABLED_AUDIT_EMITTED = True

_FAIRNESS_DOMAINS = frozenset({
    "recruitment",
    "talent_ranking",
    "talent_pool",
    "job_scoring",
    "performance",
    "salary_benchmark",
    "job_management",
    "candidate_evaluation",
})


@dataclass
class PreComplianceResult:
    clean_message: str
    original_message: str
    pii_stripped: bool = False
    fairness_blocked: bool = False
    injection_blocked: bool = False  # W1-005 (2026-05-22)
    hate_speech_blocked: bool = False  # W1-007 (2026-05-22)
    block_reason: str = ""
    fairness_flags: list[str] = field(default_factory=list)
    injection_categories: list[str] = field(default_factory=list)
    hate_speech_category: str = ""


@dataclass
class ComplianceContext:
    company_id: str
    user_id: str
    session_id: str
    domain: str
    agent_id: str
    original_message: str
    fairness_flags: list[str] = field(default_factory=list)


async def pre_compliance(
    message: str,
    company_id: str,
    domain: str,
) -> PreComplianceResult:
    if _C3B_DISABLED:
        # W3-016: emit kill-switch audit (once, fail-safe)
        await _emit_c3b_disabled_audit_once()
        return PreComplianceResult(
            clean_message=message,
            original_message=message,
        )

    # W1-007 (2026-05-22) · HateSpeechGuard ANTES de PII strip
    # PII strip pode alterar slur (e.g., CPF mask) e mascarar hate speech.
    # Hate check antes preserva integridade do match adversarial.
    try:
        from app.shared.compliance.hate_speech_guard import HateSpeechGuard
        hs_guard = HateSpeechGuard()
        hs_result = hs_guard.check(message)
        if hs_result.is_blocked:
            logger.warning(
                "[C3b] HateSpeech BLOCKED · company_id=%s domain=%s category=%s adversarial=%s",
                company_id, domain,
                hs_result.category.value if hs_result.category else "unknown",
                hs_result.adversarial_normalization,
            )
            return PreComplianceResult(
                clean_message=message,
                original_message=message,
                hate_speech_blocked=True,
                block_reason=hs_result.educational_message or "Mensagem com conteúdo ofensivo bloqueada.",
                hate_speech_category=hs_result.category.value if hs_result.category else "",
            )
    except Exception as exc:
        logger.warning("[C3b] HateSpeechGuard skipped — input NOT validated: %s", exc)

    clean = message
    pii_stripped = False

    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        # mask_names=False: ambos os callers (chat.py chat-page + agent_chat_ws
        # bolha) sao chat do RECRUTADOR — nome/titulo sao necessarios+autorizados
        # p/ busca por entidade; a Layer 4 NER falso-positivava 'Diretor Juridico'
        # como PERSON. CPF/email/telefone (Layer 1/3) seguem mascarados. Se um
        # caller candidate-facing for adicionado, escopar por `domain` aqui.
        stripped = strip_pii_for_llm_prompt(message, mask_names=False)
        if stripped != message:
            clean = stripped
            pii_stripped = True
    except Exception:
        logger.debug("[C3b] PII strip skipped (silent)")

    # W1-005 (2026-05-22) · PromptInjectionGuard wiring
    # Pre-audit: tests/security/test_red_team_c3b_injection_wiring.py
    # Gap original: c3b nunca chamava injection guard. Plus regex DoS + adversarial bypass.
    injection_blocked = False
    injection_categories: list[str] = []
    try:
        from app.shared.compliance.prompt_injection_guard import PromptInjectionGuard
        guard = PromptInjectionGuard()
        ig_result = guard.check(clean)
        if ig_result.is_blocked:
            injection_blocked = True
            injection_categories = list(ig_result.matched_patterns)
            logger.warning(
                "[C3b] PromptInjection BLOCKED · company_id=%s domain=%s categories=%s risk=%s",
                company_id, domain, injection_categories, ig_result.risk_level,
            )
            return PreComplianceResult(
                clean_message=clean,
                original_message=message,
                pii_stripped=pii_stripped,
                injection_blocked=True,
                block_reason=f"Prompt injection detectado: categorias={injection_categories}, risco={ig_result.risk_level}",
                injection_categories=injection_categories,
            )
    except Exception as exc:
        logger.warning("[C3b] PromptInjectionGuard skipped — input NOT validated: %s", exc)

    fairness_blocked = False
    block_reason = ""
    fairness_flags: list[str] = []

    if domain in _FAIRNESS_DOMAINS:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard()
            result = fg.check(clean)
            if result.soft_warnings:
                fairness_flags = list(result.soft_warnings)
            if result.is_blocked:
                fairness_blocked = True
                block_reason = result.educational_message or "Solicitação bloqueada por critérios de equidade."
                fairness_flags.extend(result.blocked_terms or [])
        except Exception:
            logger.debug("[C3b] FairnessGuard L3 skipped (silent)")

    return PreComplianceResult(
        clean_message=clean,
        original_message=message,
        pii_stripped=pii_stripped,
        fairness_blocked=fairness_blocked,
        injection_blocked=injection_blocked,
        hate_speech_blocked=False,
        block_reason=block_reason,
        fairness_flags=fairness_flags,
        injection_categories=injection_categories,
        hate_speech_category="",
    )


async def post_compliance(response: str, ctx: ComplianceContext) -> str:
    if _C3B_DISABLED:
        # W3-016: emit kill-switch audit (once, fail-safe)
        await _emit_c3b_disabled_audit_once()
        return response

    # W3-015 (2026-05-23): wire FactChecker result em audit metadata + warn
    # quando inaccurate_claims > 0. Antes: result era descartado (só log).
    fc_metadata: dict = {}
    fc_inaccurate = 0
    try:
        from app.shared.compliance.fact_checker import FactChecker
        fc = FactChecker()
        fc_result = fc.check_response(response, {"domain": ctx.domain})
        fc_metadata = fc_result.to_metadata()
        fc_inaccurate = fc_result.inaccurate_claims
        if fc_inaccurate > 0:
            logger.warning(
                "[C3b] FactChecker found %d inaccurate claim(s) in domain=%s",
                fc_inaccurate, ctx.domain,
            )
    except Exception as exc:
        logger.debug("[C3b] FactChecker skipped (silent): %s", exc)

    try:
        from app.shared.compliance.audit_service import audit_service
        await audit_service.log_decision(
            company_id=ctx.company_id,
            agent_name=ctx.agent_id or "c3b_layer",
            decision_type="generate_feedback",
            action=f"c3b_post_compliance:{ctx.domain}",
            decision=(
                f"fact_check_inaccurate={fc_inaccurate}"
                if fc_inaccurate > 0 else "logged"
            ),
            reasoning=[
                "C3b post-compliance audit log",
                *([
                    f"FactChecker flagged {fc_inaccurate} inaccurate claim(s)"
                ] if fc_inaccurate > 0 else []),
            ],
            criteria_used=[ctx.domain],
        )
    except Exception:
        logger.debug("[C3b] AuditService log skipped (silent)")

    return response
