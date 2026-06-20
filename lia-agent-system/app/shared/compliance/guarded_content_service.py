"""
GuardedCandidateContentService — caminho canonico para geracao de conteudo SOBRE candidato.

C4 P0 #1 (2026-06-20): toda surface que gera conteudo influenciando decisao
sobre pessoa DEVE passar por este servico.

Enforça em ordem:
  1. company_id fail-closed (obrigatorio, nao pode ser None)
  2. FairnessGuard Layer 1 (vies explicito) -> bloqueia/substitui
  3. FairnessGuard Layer 2 (vies implicito) -> emite warnings
  4. Provenance fields: is_ai_generated=True, generated_by canonical

Surfaces migradas:
  - wsi_service/report_generator.py :: generate_report (C4 P0 #1)
  - wsi_service/report_generator.py :: generate_feedback (C4 P0 #1)

Surfaces pendentes (sensor check_c4_guarded_generation.py monitora):
  - feedback_generator_service.py (C4 P0 #2)
  - strategic_opinion / rubric / cv_scoring / cultural_fit (cards seguintes)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Singleton do guard — instanciar uma vez por processo (compilacao de regex e custosa)
_guard_instance = None


def _get_fairness_guard():
    """Lazy singleton do FairnessGuard (strict=False em dev)."""
    global _guard_instance
    if _guard_instance is None:
        from app.shared.compliance.fairness_guard import FairnessGuard
        # strict=False: dev/test nao falha se protected_attributes.yaml ausente.
        # Em production, APP_ENV=production faz strict=True automaticamente no __init__.
        _guard_instance = FairnessGuard()
    return _guard_instance


@dataclass
class GuardedContentResult:
    """Resultado de uma geracao passada pelo caminho canonico."""
    content: str
    is_ai_generated: bool = True
    generated_by: str = "lia_guarded"
    content_type: str = ""
    fairness_passed: bool = True
    fairness_blocked: bool = False
    fairness_warnings: list = field(default_factory=list)
    needs_manual_review: bool = False
    # Para auditoria: por qual surface foi gerado
    company_id: str = ""


# Mensagem canonica substituida quando FairnessGuard bloqueia
_BLOCKED_REPORT_CONTENT = (
    "[Conteudo em revisao — identificado para verificacao de compliance LGPD/fairness. "
    "Por favor, revise e edite manualmente antes de utilizar.]"
)


class GuardedCandidateContentService:
    """
    Caminho canonico para geracao de conteudo SOBRE candidato.

    Toda surface que gera texto influenciando decisao sobre pessoa (parecer,
    feedback, fit rationale, strategic opinion, rubric evaluation) DEVE chamar
    `guard_generated_content()` antes de retornar o conteudo ao caller.

    Uso canonico:
        service = GuardedCandidateContentService()
        result = service.guard_generated_content(
            content=llm_generated_text,
            company_id=company_id,      # fail-closed: None -> ValueError
            content_type="wsi_report",
        )
        if result.needs_manual_review:
            # surface deve sinalizar para recrutador revisar
            ...
        return result.content
    """

    def __init__(self):
        pass  # guard e lazy singleton

    def guard_generated_content(
        self,
        content: str,
        company_id: str,
        content_type: str = "",
    ) -> GuardedContentResult:
        """
        Verifica conteudo gerado por LLM contra FairnessGuard.

        Args:
            content: Texto gerado pelo LLM sobre o candidato.
            company_id: Obrigatorio. Falha fechado (ValueError) se None/vazio.
            content_type: Identificador da surface (ex: 'wsi_report', 'candidate_feedback').

        Returns:
            GuardedContentResult com conteudo (sanitizado se necessario) e flags.

        Raises:
            ValueError: Se company_id for None ou vazio (fail-closed).
        """
        # 1. company_id fail-closed
        if not company_id:
            raise ValueError(
                "GuardedCandidateContentService requer company_id. "
                "Multi-tenancy fail-closed: nunca gere conteudo sobre candidato "
                "sem company_id verificado via JWT."
            )

        if not content or not content.strip():
            return GuardedContentResult(
                content=content,
                content_type=content_type,
                company_id=company_id,
                fairness_passed=True,
                fairness_blocked=False,
            )

        guard = _get_fairness_guard()

        # 2. Layer 1 — vies explicito (hard block)
        check_result = guard.check(content)
        fairness_warnings: list = []

        if check_result.is_blocked:
            logger.warning(
                "[GuardedCandidateContentService] FairnessGuard Layer 1 BLOCKED: "
                "content_type=%s company_id=%s category=%s terms=%s",
                content_type,
                company_id,
                check_result.category,
                check_result.blocked_terms,
            )
            return GuardedContentResult(
                content=_BLOCKED_REPORT_CONTENT,
                content_type=content_type,
                company_id=company_id,
                fairness_passed=False,
                fairness_blocked=True,
                fairness_warnings=check_result.blocked_terms,
                needs_manual_review=True,
            )

        # 3. Layer 2 — vies implicito (soft warning, nao bloqueia)
        # check_implicit_bias retorna list[str] (nao FairnessCheckResult)
        implicit_warnings = guard.check_implicit_bias(content)
        if implicit_warnings:
            fairness_warnings.extend(implicit_warnings)
            logger.info(
                "[GuardedCandidateContentService] FairnessGuard Layer 2 soft warnings: "
                "content_type=%s company_id=%s warnings=%s",
                content_type,
                company_id,
                implicit_warnings,
            )

        # 4. Conteudo passou — retorna com provenance
        return GuardedContentResult(
            content=content,
            content_type=content_type,
            company_id=company_id,
            fairness_passed=True,
            fairness_blocked=False,
            fairness_warnings=fairness_warnings,
            needs_manual_review=False,
        )


# Singleton do service — instanciar uma vez por modulo
_guarded_service = GuardedCandidateContentService()


def get_guarded_content_service() -> GuardedCandidateContentService:
    """Factory canonical — retorna singleton do GuardedCandidateContentService."""
    return _guarded_service
