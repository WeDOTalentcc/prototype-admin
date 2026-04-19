"""
PreConditionChecker — D10 Proactive Contextual Assistance.

Detects missing pre-conditions that block or degrade the recruiter's workflow
and surfaces them as ProactiveHints so the orchestrator can:
  - navigate the user to the right settings page
  - offer to auto-fix (ask permission first)
  - include a proactive suggestion in LIA's response

Checks run BEFORE the LLM is invoked. They are fail-open — a check that
crashes does not block the request.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProactiveHint:
    """A hint surfaced to the LIA orchestrator for proactive assistance."""

    type: str
    message: str
    action: str | None = None
    severity: str = "info"  # "info" | "warning" | "critical"
    metadata: dict[str, Any] = field(default_factory=dict)


class PreConditionChecker:
    """Runs pre-condition checks and returns a list of ProactiveHints."""

    async def check(self, ctx: Any) -> list[ProactiveHint]:
        """
        Run all checks against the orchestration context. Always returns a
        list; individual failures are logged and do not propagate.
        """
        hints: list[ProactiveHint] = []

        # --- Check 1: company_id empty/missing ---
        try:
            company_id = getattr(ctx, "company_id", None) or ""
            if not company_id:
                hints.append(ProactiveHint(
                    type="missing_company_id",
                    message=(
                        "Notei que seu perfil de empresa ainda nao esta configurado. "
                        "Isso limita buscas de candidatos e triagens. "
                        "Quer que eu te leve ate Configuracoes agora?"
                    ),
                    action="navigate_to_settings",
                    severity="warning",
                    metadata={"target_page": "settings"},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] company_id check failed: %s", exc)

        # --- Check 2: company profile incomplete (name, sector, size missing) ---
        if getattr(ctx, "company_id", None):
            try:
                missing_fields = await self._check_company_profile_completeness(ctx.company_id)
                if missing_fields:
                    hints.append(ProactiveHint(
                        type="incomplete_company_profile",
                        message=(
                            f"Seu perfil de empresa esta incompleto (faltam: {', '.join(missing_fields)}). "
                            "Isso reduz a precisao das recomendacoes. "
                            "Posso te ajudar a completar em Configuracoes."
                        ),
                        action="navigate_to_settings",
                        severity="info",
                        metadata={"target_page": "settings", "missing_fields": missing_fields},
                    ))
            except Exception as exc:
                logger.debug("[PreConditionChecker] profile completeness check failed: %s", exc)

        # --- Check 3: intent=screening but vacancy has no screening questions ---
        try:
            intent = (getattr(ctx, "intent", "") or "").lower()
            if intent in ("screening", "wsi", "tria", "triagem"):
                vacancy_id = getattr(ctx, "vacancy_id", None) or getattr(ctx, "job_id", None)
                if vacancy_id and await self._vacancy_has_no_questions(ctx.company_id, vacancy_id):
                    hints.append(ProactiveHint(
                        type="vacancy_no_screening_questions",
                        message=(
                            "Essa vaga nao tem perguntas de triagem cadastradas. "
                            "Posso sugerir um conjunto de perguntas baseado na descricao da vaga?"
                        ),
                        action="suggest_screening_questions",
                        severity="warning",
                        metadata={"vacancy_id": str(vacancy_id)},
                    ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] screening precondition check failed: %s", exc)

        return hints

    async def _check_company_profile_completeness(self, company_id: str) -> list[str]:
        """Return list of missing fields in the company profile. Empty if complete."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                # Lightweight read — fields that signal a "minimum viable profile"
                row = (await session.execute(
                    text("SELECT name, industry, size FROM companies WHERE id = :cid LIMIT 1"),
                    {"cid": company_id},
                )).first()
                if row is None:
                    return ["nome", "setor", "tamanho"]
                missing: list[str] = []
                if not row[0]:
                    missing.append("nome")
                if not row[1]:
                    missing.append("setor")
                if not row[2]:
                    missing.append("tamanho")
                return missing
        except Exception as exc:
            logger.debug("[PreConditionChecker] profile read failed: %s", exc)
            return []

    async def _vacancy_has_no_questions(self, company_id: str, vacancy_id: str) -> bool:
        """Return True if the vacancy has zero screening questions configured."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                result = (await session.execute(
                    text(
                        "SELECT COUNT(*) FROM screening_questions "
                        "WHERE vacancy_id = :vid AND company_id = :cid"
                    ),
                    {"vid": str(vacancy_id), "cid": company_id},
                )).scalar()
                return (result or 0) == 0
        except Exception as exc:
            logger.debug("[PreConditionChecker] vacancy question check failed: %s", exc)
            return False


# Module-level singleton
precondition_checker = PreConditionChecker()
