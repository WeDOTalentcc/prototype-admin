"""Recruiter Assistant domain repositories (ADR-001 — Repository Pattern).

Sprint 5.4 scaffold (2026-05-07): partial-repo domain. Some
`*_repository.py` may already exist in this folder; check before
adding new ones to avoid duplication.

Top services to migrate (Boy Scout opportunistically):
  1. pipeline_stage_service.py — 8 SQL hits
  2. conversation_manager.py — 7 SQL hits (1504 LOC, biggest in domain)
  3. conversation_memory.py — 4 SQL hits
  4. pipeline_service.py — 3 SQL hits
  5. memory_service.py — 1 SQL hit (start here — easiest)

Cross-domain reads should import canonical repos from other domains:
  - Candidate → `app/domains/cv_screening/repositories/screening_repository.py`
  - JobVacancy → `app/domains/job_management/repositories/job_vacancy_crud_repository.py`

Anatomy reminder (canonical):
    class XRepository:
        def __init__(self, db: AsyncSession):
            self._db = db

        @staticmethod
        def _require_company_id(company_id: str) -> None:
            if not company_id:
                raise ValueError("Multi-tenancy invariant: company_id required")

        async def get_for_company(self, *, company_id: str, ...) -> X | None:
            self._require_company_id(company_id)
            stmt = select(X).where(
                and_(X.company_id == company_id, ...)
            )
            ...
"""
