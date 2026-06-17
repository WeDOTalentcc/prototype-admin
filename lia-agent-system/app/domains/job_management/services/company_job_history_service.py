"""
CompanyJobHistoryService — Onda 4 (Frente F).

Consulta o histórico de vagas encerradas/preenchidas de uma empresa
para inferir salary_band, recurring_skills e evidence_count úteis ao
wizard de criação de nova vaga.

Filtro de similaridade: Jaccard sobre tokens do título
(sim ≥ 0.3 → match). Threshold baixo intencional — inclui variações
de título ("Dev Python" vs "Python Developer").

Multi-tenancy: todas as queries passam company_id. ✅
LGPD: não armazena dados pessoais; opera apenas em campos de vaga. ✅
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_MIN_SIMILARITY: float = 0.3  # Jaccard threshold


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class VacancyMatch:
    """Representa uma vaga histórica similar."""
    title: str
    seniority: str
    similarity_score: float
    salary_min: float | None = None
    salary_max: float | None = None
    skills: list[str] = field(default_factory=list)


@dataclass
class JobHistoryInsights:
    """Agregado de insights derivados das vagas históricas similares."""
    evidence_count: int
    confidence: str  # "high" | "medium" | "low"
    salary_band: dict[str, float] | None
    recurring_skills: list[str]
    matches: list[VacancyMatch] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation (sem objetos aninhados)."""
        return {
            "evidence_count": self.evidence_count,
            "confidence": self.confidence,
            "salary_band": self.salary_band,
            "recurring_skills": self.recurring_skills,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jaccard_similarity(a: str, b: str) -> float:
    """Jaccard similarity between space-tokenized lowercase strings."""
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _infer_confidence(count: int) -> str:
    if count >= 5:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class CompanyJobHistoryService:
    """Infere insights de salary/skills a partir do histórico de vagas da empresa."""

    def __init__(self, db: Any) -> None:
        self._db = db

    async def get_similar_vacancies_by_role_seniority(
        self,
        company_id: str,
        role: str,
        seniority: str,
    ) -> JobHistoryInsights:
        """
        Retorna JobHistoryInsights para uma combinação de role + seniority.

        Args:
            company_id: UUID da empresa — obrigatório (multi-tenancy).
            role: título do cargo desejado (ex: "Engenheiro Python").
            seniority: nível de senioridade (ex: "Pleno").

        Raises:
            ValueError: se company_id for vazio.
        """
        if not company_id:
            raise ValueError("company_id is required for CompanyJobHistoryService")

        all_vacancies = await self._fetch_vacancies(company_id)
        matches = self._score_and_filter(all_vacancies, role, seniority)

        salary_band = self._compute_salary_band(matches)
        recurring_skills = self._compute_recurring_skills(matches)
        evidence_count = len(matches)

        return JobHistoryInsights(
            evidence_count=evidence_count,
            confidence=_infer_confidence(evidence_count),
            salary_band=salary_band,
            recurring_skills=recurring_skills,
            matches=matches,
        )

    # ── private ──────────────────────────────────────────────────────────────

    async def _fetch_vacancies(self, company_id: str) -> list[Any]:
        """Fetch up to 50 vacancies for company; swallows DB errors (degraded mode)."""
        try:
            from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                JobVacancyCRUDRepository,
            )
            return await JobVacancyCRUDRepository(self._db).list_for_company_history(
                company_id, limit=50
            )
        except Exception as exc:
            logger.warning(
                "[CompanyJobHistoryService] DB error (degraded mode): %s", exc
            )
            return []

    @staticmethod
    def _build_stmt(company_id: str):
        """Deprecated — kept for backwards compat with tests that monkeypatch.

        New code path uses JobVacancyCRUDRepository.list_for_company_history.
        """
        return None

    def _score_and_filter(
        self, vacancies: list[Any], role: str, seniority: str
    ) -> list[VacancyMatch]:
        matches: list[VacancyMatch] = []
        for v in vacancies:
            title = getattr(v, "title", "") or ""
            sim = _jaccard_similarity(role, title)
            if sim < _MIN_SIMILARITY:
                continue
            skills = [
                s["name"]
                for s in (getattr(v, "skills_required", None) or [])
                if isinstance(s, dict) and s.get("name")
            ]
            matches.append(
                VacancyMatch(
                    title=title,
                    seniority=getattr(v, "seniority_level", seniority) or seniority,
                    similarity_score=sim,
                    salary_min=getattr(v, "salary_min", None),
                    salary_max=getattr(v, "salary_max", None),
                    skills=skills,
                )
            )
        return matches

    @staticmethod
    def _compute_salary_band(
        matches: list[VacancyMatch],
    ) -> dict[str, float] | None:
        mins = [m.salary_min for m in matches if m.salary_min is not None]
        maxs = [m.salary_max for m in matches if m.salary_max is not None]
        if not mins or not maxs:
            return None
        return {
            "min": sum(mins) / len(mins),
            "max": sum(maxs) / len(maxs),
        }

    @staticmethod
    def _compute_recurring_skills(matches: list[VacancyMatch]) -> list[str]:
        counter: Counter[str] = Counter()
        for m in matches:
            for skill in m.skills:
                counter[skill] += 1
        return [s for s, _ in counter.most_common(3)]
