"""Sourcing domain repositories (ADR-001 — Repository Pattern).

Sprint 5.4 scaffold (2026-05-07): zero-repo domain — services were
performing raw SQL inline / direct `select(Model)`. ADR-001 sensors
(`check_no_sql_inline_in_services.py` + `check_no_select_in_services.py`)
warn-only since Sprint 5.1.

Top services to migrate (Boy Scout opportunistically):
  1. sourcing_pipeline_service.py — 12 SQL hits
  2. sourcing_pipeline.py — 12 SQL hits
  3. pearch_service.py — 9 SQL hits
  4. evaluation_criteria.py — 4 SQL hits
  5. vacancy_search.py — 2 SQL hits (start here — smallest)

Cross-domain reads should import canonical repos from other domains:
  - JobVacancy → `app/domains/job_management/repositories/job_vacancy_crud_repository.py`
  - Candidate → check `app/domains/cv_screening/repositories/`

Anatomy reminder (canonical):
    class XRepository:
        def __init__(self, db: AsyncSession):
            self._db = db

        @staticmethod
        def _require_company_id(company_id: str) -> None:
            if not company_id:
                raise ValueError("Multi-tenancy invariant: company_id required")

        async def list_for_company(self, *, company_id: str, ...) -> list[X]:
            self._require_company_id(company_id)
            stmt = select(X).where(X.company_id == company_id)
            ...
"""
