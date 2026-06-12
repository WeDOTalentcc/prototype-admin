"""Guard canonico de conformidade de feedback ao candidato (auditoria 2026-06-10).

Fonte unica de "este feedback pode ser enviado?": combina
  (1) fairness/LGPD L1 explicito (computacional, via fairness_guard_middleware)
  (2) PII de documento — CPF/CNPJ/RG (computacional) — sem motivo legitimo num feedback
  (3) LLM-as-judge (inferencial) — DORMENTE por flag FEEDBACK_LLM_JUDGE

Usado pelo dispatch de transicao e pelo send-email (texto editavel). Fail-safe.
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

# PII de documento: alto sinal, sem razao legitima de aparecer num feedback.
# (email/telefone NAO entram — contato da empresa e legitimo -> falso positivo.)
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
_RG = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]\b")

_JUDGE_TRUTHY = frozenset({"1", "true", "on", "yes"})


def detect_pii(text: str | None) -> list[str]:
    """Retorna tipos de PII de documento encontrados no texto (CPF/CNPJ/RG)."""
    if not text:
        return []
    found = []
    # CNPJ antes de CPF (CNPJ e mais especifico).
    if _CNPJ.search(text):
        found.append("cnpj")
    if _CPF.search(text):
        found.append("cpf")
    if _RG.search(text) and "rg" not in found:
        # RG so se nao for ja capturado como CPF (heuristica simples)
        if not _CPF.search(text):
            found.append("rg")
    return found


def feedback_block_reason(text: str | None, company_id: str = "") -> str | None:
    """Checagem COMPUTACIONAL (fairness L1 + PII de documento). Sincrona.

    Retorna um motivo (str) se o feedback deve ser BLOQUEADO, senao None.
    """
    if not text or not str(text).strip():
        return None
    try:
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        f = check_fairness(
            texts={"feedback": str(text)},
            context="candidate_rejection_feedback",
            company_id=company_id or "",
        )
        if f.is_blocked:
            cat = getattr(f.blocked_result, "category", None)
            return f"fairness:{cat}"
    except Exception as e:
        logger.warning("[feedback_guard] fairness check falhou (fail-soft): %s", e)
    pii = detect_pii(str(text))
    if pii:
        return f"pii:{','.join(pii)}"
    return None


def llm_judge_enabled() -> bool:
    return os.environ.get("FEEDBACK_LLM_JUDGE", "").strip().lower() in _JUDGE_TRUTHY


async def feedback_llm_judge_reason(text: str | None, company_id: str = "") -> str | None:
    """2a linha INFERENCIAL (LLM-as-judge). DORMENTE por flag FEEDBACK_LLM_JUDGE.

    Pergunta ao modelo se o feedback expoe motivo sensivel, promete algo, julga
    carater, discrimina ou vaza dado de terceiro. Retorna motivo se bloquear.
    Fail-soft: erro/flag-off -> None (nao bloqueia).
    """
    if not text or not llm_judge_enabled():
        return None
    try:
        from app.shared.providers.llm_client import get_anthropic_client, is_llm_available
        if not is_llm_available():
            return None
        container = get_anthropic_client()
        prompt = (
            "Voce e um auditor de conformidade. Avalie o FEEDBACK abaixo (enviado a "
            "um candidato reprovado). Ele contem ALGUM destes problemas? "
            "(a) expoe motivo sensivel/juridico (referencias negativas, background check, "
            "exame admissional); (b) promete vaga/oportunidade futura; (c) julga carater "
            "ou personalidade; (d) linguagem discriminatoria (classe protegida); "
            "(e) dado pessoal de terceiro. Responda APENAS JSON: "
            '{\"block\": true|false, \"reason\": \"curto\"}.\n\nFEEDBACK:\n' + str(text)
        )
        resp = await container.generate_with_fallback(prompt, agent_type="FeedbackComplianceJudge")
        import json
        m = re.search(r"\{[\s\S]*\}", resp or "")
        if not m:
            return None
        data = json.loads(m.group())
        if data.get("block"):
            return f"llm_judge:{str(data.get('reason', 'risco'))[:80]}"
    except Exception as e:
        logger.warning("[feedback_guard] LLM judge falhou (fail-soft): %s", e)
    return None


async def feedback_block_reason_full(text: str | None, company_id: str = "") -> str | None:
    """Computacional (fairness+PII) + inferencial (LLM-judge dormente). Async."""
    reason = feedback_block_reason(text, company_id)
    if reason:
        return reason
    return await feedback_llm_judge_reason(text, company_id)
