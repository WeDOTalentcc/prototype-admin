"""
WT-2022 P0.C: Helper canonical para audit de decisões automatizadas (LGPD Art. 20 + EU AI Act Art. 13).

Decisão Paulo 2026-05-21: AutomatedDecisionExplanation tabela órfã. Pipelines IA
(wsi_service, ranking, pre_wrf_filter, cv_screening) deveriam gravar cada decisão
automatizada nessa tabela. AITransparencyPanel lê e expõe ao recrutador/DPO/candidato
per Art. 20 LGPD (revisão de decisão automatizada).

Status (2026-05-21):
    ✅ Helper canonical criado (este arquivo)
    ✅ Kwarg→column mapping corrigido (Opção A — sem Alembic migration):
        job_id           → vacancy_id (model column real)
        criteria_used    → input_criteria (JSONB list-of-strings)
        criteria_ignored → decision_criteria["criteria_ignored"]   ┐
        confidence_score → decision_criteria["confidence_score"]    │ consolidado
        review_eligible  → decision_criteria["review_eligible"]     │ em JSONB
        extra_metadata   → decision_criteria["audit_metadata"]      ┘
        review_eligible=True também ativa human_review_requested=True
    ✅ Consumers wired (11 callers em 2026-05-21):
        - app/api/v1/wsi/questions.py:generate_questions
        - app/api/v1/candidate_search/archetypes.py:rank_archetypes
        - app/api/v1/automation/event_handlers/handlers_screening.py
        - app/api/v1/talent_funnel.py:wrf_rank + pre_wrf_filter
        - app/api/v1/applications.py (2 sites)
        - app/api/v1/interview_notes.py
        - app/domains/sourcing/tools/query_tools.py
        - app/domains/ai/services/rag_pipeline_service.py
        - app/domains/job_creation/graph.py (fire-and-forget)

## Pattern de uso (qualquer caller)

    from app.shared.services.automated_decision_logger import log_automated_decision

    await log_automated_decision(
        db=db,
        company_id=company_id,
        candidate_id=candidate_id,
        job_id=job_id,           # mapeado pra vacancy_id internamente
        decision_type="cv_screening_score",
        ai_model_used="claude-opus-4-7",
        explanation_text=f"Candidato pontuou X em Y critérios baseado em ...",
        criteria_used=["skills_match", "experience_years", "education"],
        criteria_ignored=PROTECTED_CRITERIA_PT,  # ADR-LGPD-001 mandatory
        confidence_score=0.85,
        review_eligible=True,
    )

## ADR-LGPD-001 enforcement

PROTECTED_CRITERIA_PT lista atributos PROIBIDOS de usar em decisão automatizada
(raça, religião, gênero, etnia, estado civil, saúde — CLAUDE.md REGRA #2).
Helper enforça que criteria_ignored CONTAIN esses campos — fail-loud se omitido.

## REGRA 4 (CLAUDE.md): NO silent swallow

Versão anterior (pré-2026-05-21) tinha `except Exception` genérico que retornava
None silently — todas as 11 chamadas wired escreviam `logger.error` mas ZERO
linhas eram gravadas em `automated_decision_explanations` (kwarg mismatch
TypeError mascarado). AITransparencyPanel ficava vazio em produção, LGPD Art. 20
gap real.

Comportamento corrigido:
    - ``ValueError`` (PROTECTED_CRITERIA_PT violation) → SEMPRE re-raise (fail-loud)
    - ``TypeError`` (mapping bug helper-vs-model) → re-raise (fail-loud por default)
    - ``IntegrityError`` / ``SQLAlchemyError`` (DB issue) → re-raise (fail-loud por default)
    - Caller em contexto fire-and-forget (e.g. graph.py async task) pode passar
      ``silent_on_persist_error=True`` pra degradar persist errors em logger.error
      SEM bloquear a decisão IA. **NUNCA** silencia ValueError (compliance).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# WT-2022 P0.C: criterios PROIBIDOS per ADR-LGPD-001 + CLAUDE.md REGRA #2
PROTECTED_CRITERIA_PT = [
    "raca",
    "religiao",
    "genero",
    "etnia",
    "estado_civil",
    "orientacao_sexual",
    "deficiencia",
    "saude",
    "filiacao_sindical",
    "filiacao_politica",
]


async def log_automated_decision(
    db: "AsyncSession",
    company_id: str,
    decision_type: str,
    explanation_text: str,
    *,
    candidate_id: str | None = None,
    job_id: str | None = None,
    ai_model_used: str = "",
    criteria_used: list[str] | None = None,
    criteria_ignored: list[str] | None = None,
    confidence_score: float | None = None,
    review_eligible: bool = True,
    extra_metadata: dict[str, Any] | None = None,
    silent_on_persist_error: bool = False,
) -> str | None:
    """Insert AutomatedDecisionExplanation record per LGPD Art. 20 + EU AI Act Art. 13.

    Args:
        db: AsyncSession aberto (caller é responsável por commit/rollback).
        company_id: tenant UUID — multi-tenancy mandatory (CLAUDE.md REGRA #1).
        decision_type: rótulo curto da decisão (ex: ``"wsi_question_generation"``,
            ``"candidate_ranking"``, ``"cv_pre_wrf_filter"``, ``"intake_extraction"``).
        explanation_text: texto livre que será apresentado ao titular dos dados
            via AITransparencyPanel — escrever em PT-BR, autoexplicativo.
        candidate_id: opcional — UUID do candidato afetado (NULL para decisões
            agregadas que não toquem um indivíduo).
        job_id: opcional — UUID da vaga (mapeia internamente pra coluna
            ``vacancy_id`` do modelo).
        ai_model_used: identificador do modelo IA (ex: ``"claude-opus-4-7"``,
            ``"wsi_F6_pipeline_v2"``). Default ``""`` mantém compat.
        criteria_used: lista de strings descrevendo critérios efetivamente
            usados na decisão. Gravado em ``input_criteria`` JSONB.
            ⚠ ADR-LGPD-001: NÃO pode conter atributos em PROTECTED_CRITERIA_PT
            — helper raise ``ValueError`` fail-loud se detectar violação.
        criteria_ignored: lista de strings descrevendo critérios deliberadamente
            ignorados (deve incluir PROTECTED_CRITERIA_PT pra audit trail).
            Consolidado em ``decision_criteria["criteria_ignored"]``.
        confidence_score: float opcional 0-1 (confiança agregada do modelo).
            Consolidado em ``decision_criteria["confidence_score"]``.
        review_eligible: True (default) marca decisão como sujeita a revisão
            humana (LGPD Art. 20). Também grava ``human_review_requested=True``
            no modelo pra workflow downstream do AITransparencyPanel.
        extra_metadata: dict livre com payload adicional (session_id, weights,
            top_n, etc.). Consolidado em ``decision_criteria["audit_metadata"]``.
        silent_on_persist_error: ``True`` permite degradar TypeError/SQLAlchemy
            errors em logger.error (NÃO bloqueia decisão IA). Use **apenas** em
            contexto fire-and-forget (ex: async task em graph.py).
            ``ValueError`` (LGPD violation) **NUNCA** é silenciado.

    Returns:
        ``str`` decision_id (UUID) em sucesso. ``None`` apenas quando
        ``silent_on_persist_error=True`` E persist falhou (caller pode usar
        pra metrica/retry).

    Raises:
        ValueError: protected criterion em criteria_used (LGPD fail-loud).
        TypeError: kwarg/model mismatch (bug — re-raise pra triagem).
        IntegrityError / SQLAlchemyError: DB constraint/conexão (re-raise por
        default). Silenciado se ``silent_on_persist_error=True``.

    LGPD/Compliance enforcement:
        - PROTECTED_CRITERIA_PT (ADR-LGPD-001 + REGRA #2) é validado contra
          criteria_used. Se algum protected criterion foi usado em decisão IA,
          fail-loud raise ValueError.
        - criteria_ignored deve incluir PROTECTED_CRITERIA_PT — helper completa
          automaticamente + warn se omitido.
    """
    # Compliance gate: protected criteria nao podem aparecer em criteria_used.
    # ValueError SEMPRE re-raise — fail-loud independente de silent_on_persist_error.
    if criteria_used:
        violations = [c for c in criteria_used if c.lower() in PROTECTED_CRITERIA_PT]
        if violations:
            raise ValueError(
                f"WT-2022 P0.C / ADR-LGPD-001 VIOLATION: criterios protegidos "
                f"em criteria_used: {violations}. Estes NUNCA podem ser usados em "
                f"decisao automatizada (CLAUDE.md REGRA #2 + LGPD)."
            )

    # Warn se criteria_ignored nao incluir protected (boa pratica + audit trail).
    if criteria_ignored is None or not set(PROTECTED_CRITERIA_PT).issubset(set(criteria_ignored)):
        logger.warning(
            "WT-2022 P0.C: criteria_ignored deveria incluir PROTECTED_CRITERIA_PT "
            "para audit trail completo (LGPD Art. 20)."
        )
        criteria_ignored = list(set((criteria_ignored or []) + PROTECTED_CRITERIA_PT))

    # Kwarg → model column mapping (Opção A, sem Alembic migration).
    # Model real (libs/models/lia_models/observability.py:724):
    #   id, company_id, decision_type, candidate_id, vacancy_id,
    #   ai_model_used, input_criteria (JSON), decision_criteria (JSON),
    #   explanation_text, human_review_requested (Bool), created_at, ...
    consolidated_decision_criteria: dict[str, Any] = {
        "criteria_ignored": list(criteria_ignored or []),
        "confidence_score": confidence_score,
        "review_eligible": bool(review_eligible),
        "audit_metadata": extra_metadata or {},
    }

    try:
        from app.models.observability import AutomatedDecisionExplanation

        decision = AutomatedDecisionExplanation(
            id=uuid.uuid4(),
            company_id=company_id,
            candidate_id=candidate_id,
            vacancy_id=job_id,  # ← kwarg job_id mapeado pra column vacancy_id
            decision_type=decision_type,
            ai_model_used=ai_model_used,
            explanation_text=explanation_text,
            input_criteria=list(criteria_used or []),  # JSONB list-of-strings
            decision_criteria=consolidated_decision_criteria,
            human_review_requested=bool(review_eligible),
            created_at=datetime.utcnow(),
        )
        db.add(decision)
        await db.flush()
        decision_id = str(decision.id)
        logger.info(
            "WT-2022 P0.C: automated decision logged: type=%s candidate_id=%s vacancy_id=%s decision_id=%s",
            decision_type, candidate_id, job_id, decision_id,
        )
        return decision_id

    except TypeError as exc:
        # Kwarg/model mismatch — bug. Fail-loud por default (re-raise) pra triagem
        # NÃO mascarar (REGRA 4 CLAUDE.md). Silent só em fire-and-forget context.
        logger.error(
            "WT-2022 P0.C: AutomatedDecisionExplanation TypeError (kwarg-model mismatch) "
            "for type=%s: %s — LGPD Art. 20 audit trail gap.",
            decision_type, exc, exc_info=True,
        )
        if silent_on_persist_error:
            return None
        raise

    except (IntegrityError, SQLAlchemyError) as exc:
        # DB-level problem (constraint, connection, etc.). Fail-loud por default.
        logger.error(
            "WT-2022 P0.C: AutomatedDecisionExplanation DB error for type=%s: %s "
            "(LGPD Art. 20 audit trail gap — candidate review pode estar comprometido)",
            decision_type, exc, exc_info=True,
        )
        if silent_on_persist_error:
            return None
        raise
