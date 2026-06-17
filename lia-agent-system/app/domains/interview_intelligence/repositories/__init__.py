"""Interview Intelligence domain repositories (ADR-001 — Repository Pattern).

Sprint 5.4 scaffold (2026-05-07): zero-repo domain.

Top services to migrate (Boy Scout opportunistically):
  1. comparative_analysis_service.py — 8 SQL hits
  2. transcription_service.py — 2 SQL hits (start here — smallest)
  3. strategic_opinion_service.py — 1 SQL hit
  4. interview_wsi_service.py — 1 SQL hit
  5. feedback_generator_service.py — 1 SQL hit

Cross-domain reads should import canonical repos:
  - Interview / interview_feedbacks — likely needs new repo here
  - Candidate → `app/domains/cv_screening/repositories/`
  - WSI session/result → check `app/domains/job_creation/` or wsi-api domain

Anatomy reminder (canonical):
    class InterviewRepository:
        def __init__(self, db: AsyncSession):
            self._db = db

        @staticmethod
        def _require_company_id(company_id: str) -> None:
            if not company_id:
                raise ValueError("Multi-tenancy invariant: company_id required")

        async def list_for_company(self, *, company_id: str, ...) -> list[Interview]:
            self._require_company_id(company_id)
            stmt = select(Interview).where(Interview.company_id == company_id)
            ...
"""
