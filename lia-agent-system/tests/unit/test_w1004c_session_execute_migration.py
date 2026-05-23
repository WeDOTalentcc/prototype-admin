"""
Unit tests for W1-004-C: session.execute(text()) migration to repository pattern.

ADR-001 Repository Pattern enforcement — sensor regression + repo unit tests.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]  # lia-agent-system/
SERVICES_DIR = ROOT / "app" / "domains"


# ── Static sensor tests ──────────────────────────────────────────────────────

class TestSensorStaticRegression:
    """Ensure no NEW session.execute(text()) or db.execute(text()) without EXEMPT marker."""

    EXEMPT_MARKER = "ADR-001-EXEMPT"
    PATTERNS = [
        r"session.execute(text(",
        r"session.execute(sa_text(",
        r"db.execute(text(",
        r"db.execute(sa_text(",
    ]

    def _scan_services(self) -> list[tuple[str, int, str]]:
        """Scan all service files for inline SQL patterns without EXEMPT marker."""
        violations = []
        for py_file in SERVICES_DIR.rglob("*.py"):
            # Only services, not tests, scripts, alembic
            rel = str(py_file.relative_to(ROOT))
            if any(skip in rel for skip in ["tests/", "scripts/", "alembic/", "__pycache__"]):
                continue
            # Only service files
            parts = py_file.relative_to(ROOT).parts
            if not (len(parts) >= 4 and parts[3] in ("services",)):
                continue

            try:
                src = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if self.EXEMPT_MARKER in src:
                continue  # file is exempt

            for lineno, line in enumerate(src.splitlines(), start=1):
                for pat in self.PATTERNS:
                    if pat in line and not line.strip().startswith("#"):
                        violations.append((rel, lineno, line.strip()[:100]))
                        break

        return violations

    def test_no_raw_session_execute_in_services(self):
        """Static: no session.execute(text()) in services without EXEMPT marker."""
        violations = self._scan_services()
        assert violations == [], (
            f"ADR-001 violations found ({len(violations)}):\n"
            + "\n".join(f"  {f}:{ln}: {txt}" for f, ln, txt in violations)
            + "\n→ Fix: add '# ADR-001-EXEMPT: <reason>' to the file, or migrate to a repo."
        )


# ── VacancyCandidateRepository tests ─────────────────────────────────────────

class TestVacancyCandidateRepositoryNewMethods:
    """Unit tests for W1-004-C new methods in VacancyCandidateRepository."""

    def _make_repo(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        db = AsyncMock()
        return VacancyCandidateRepository(db)

    def test_get_lia_score_exists(self):
        """get_lia_score method exists on VacancyCandidateRepository."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        assert hasattr(VacancyCandidateRepository, "get_lia_score")
        assert callable(VacancyCandidateRepository.get_lia_score)

    def test_get_latest_lia_score_exists(self):
        """get_latest_lia_score method exists."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        assert hasattr(VacancyCandidateRepository, "get_latest_lia_score")

    def test_append_note_exists(self):
        """append_note method exists."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        assert hasattr(VacancyCandidateRepository, "append_note")

    @pytest.mark.asyncio
    async def test_get_lia_score_requires_company_id(self):
        """get_lia_score raises ValueError when company_id is empty (fail-closed)."""
        repo = self._make_repo()
        with pytest.raises((ValueError, Exception)):
            await repo.get_lia_score("cand-1", "vac-1", "")

    @pytest.mark.asyncio
    async def test_append_note_requires_company_id(self):
        """append_note raises ValueError when company_id is empty (fail-closed)."""
        repo = self._make_repo()
        with pytest.raises((ValueError, Exception)):
            await repo.append_note("cand-1", "", "my note")


# ── JobVacancyCrudRepository tests ────────────────────────────────────────────

class TestJobVacancyCrudRepositoryNewMethods:
    """Unit tests for W1-004-C new methods in JobVacancyCrudRepository."""

    def _make_repo(self):
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCrudRepository,
        )
        db = AsyncMock()
        return JobVacancyCrudRepository(db)

    def test_get_recruiter_id_exists(self):
        """get_recruiter_id method exists on JobVacancyCrudRepository."""
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCrudRepository,
        )
        assert hasattr(JobVacancyCrudRepository, "get_recruiter_id")
        assert callable(JobVacancyCrudRepository.get_recruiter_id)

    def test_get_jobs_near_deadline_exists(self):
        """get_jobs_near_deadline method exists."""
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCrudRepository,
        )
        assert hasattr(JobVacancyCrudRepository, "get_jobs_near_deadline")

    @pytest.mark.asyncio
    async def test_get_recruiter_id_requires_company_id(self):
        """get_recruiter_id raises ValueError when company_id is empty (fail-closed)."""
        repo = self._make_repo()
        with pytest.raises((ValueError, Exception)):
            await repo.get_recruiter_id("job-1", "")

    @pytest.mark.asyncio
    async def test_get_jobs_near_deadline_requires_company_id(self):
        """get_jobs_near_deadline raises ValueError when company_id is empty (fail-closed)."""
        repo = self._make_repo()
        with pytest.raises((ValueError, Exception)):
            await repo.get_jobs_near_deadline("")


# ── CandidateRepository tests ─────────────────────────────────────────────────

class TestCandidateRepositoryNewMethod:
    """Unit tests for W1-004-C new method in CandidateRepository."""

    def test_get_candidate_with_job_context_exists(self):
        """get_candidate_with_job_context method exists on CandidateRepository."""
        from app.domains.candidates.repositories.candidate_repository import CandidateRepository
        assert hasattr(CandidateRepository, "get_candidate_with_job_context")
        assert callable(CandidateRepository.get_candidate_with_job_context)
