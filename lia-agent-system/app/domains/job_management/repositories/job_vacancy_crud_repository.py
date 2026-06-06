from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import uuid as uuid_lib
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy


# -- P1-2: classificacao de funil (pura, testavel) --------------------------
# Mapeia o ``stage`` de vacancy_candidates para o bucket do funil consumido
# pelo FE ({screening, interview, final, hired}). Stages de sourcing/rejected
# ficam só no ``total``. Sensor: tests/unit/test_funnel_stage_classification.py
_FUNNEL_SCREENING_STAGES = {"screening", "triagem"}
_FUNNEL_FINAL_STAGES = {"offer", "final", "oferta"}
_FUNNEL_HIRED_STAGES = {"hired", "contratado"}


def classify_funnel_stage(stage):
    """stage (str|None) -> 'screening'|'interview'|'final'|'hired'|None."""
    s = (stage or "").strip().lower()
    if s in _FUNNEL_SCREENING_STAGES:
        return "screening"
    if s == "entrevista" or s.startswith("interview"):
        return "interview"
    if s in _FUNNEL_FINAL_STAGES:
        return "final"
    if s in _FUNNEL_HIRED_STAGES:
        return "hired"
    return None


class JobVacancyCRUDRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Search ────────────────────────────────────────────────────────────────

    async def search_count(self, search_filter) -> int:
        # TENANT-EXEMPT: dynamic builder — caller composes ``search_filter``
        # always with JobVacancy.company_id == X; AST sensor cannot trace.
        count_stmt = select(func.count(JobVacancy.id)).where(search_filter)
        count_result = await self.db.execute(count_stmt)
        return count_result.scalar() or 0

    async def count_by_status(self, company_id: str) -> dict[str, int]:
        """Contagem ACURADA de vagas por status (company-scoped). A IA narrava
        números ERRADOS (ex: '2 ativas' em vez de 6) porque contava da lista
        TRUNCADA por limit; este breakdown vem de um GROUP BY real. Bug live
        Paulo 2026-06-06 (103 total vs UI 50; ativas 2 vs 6)."""
        if not company_id:
            return {}
        stmt = (
            select(JobVacancy.status, func.count(JobVacancy.id))
            .where(JobVacancy.company_id == company_id)
            .group_by(JobVacancy.status)
        )
        result = await self.db.execute(stmt)
        return {str(st): int(ct) for st, ct in result.all() if st}

    async def search_vacancies(self, search_filter, offset: int, page_size: int):
        # TENANT-EXEMPT: dynamic builder — see search_count above.
        stmt = (
            select(
                JobVacancy.id,
                JobVacancy.job_id,
                JobVacancy.title,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.description
            )
            .where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.all()

    # ── Archetypes ────────────────────────────────────────────────────────────

    async def get_completed_vacancies(self, company_id):
        result = await self.db.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "Concluída")
            .where(JobVacancy.company_id == company_id)
            .order_by(JobVacancy.closed_at.desc())
        )
        return result.scalars().all()

    # ── Get one ───────────────────────────────────────────────────────────────

    async def get_vacancy_by_id_and_company(self, job_vacancy_id: UUID, company_id):
        result = await self.db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_vacancy_id,
                JobVacancy.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def get_vacancy_by_id(self, job_vacancy_id):
        """Get vacancy by id without company filter.

        Used by app/domains/sourcing/services/sourcing_pipeline_service.py
        (Sprint Q2 ADR-001 cross-domain cleanup). The sourcing pipeline runs
        in system context (background scheduler) without a per-request
        company_id. Caller is responsible for any tenant scoping required.
        """
        # TENANT-EXEMPT: system-context (sourcing background scheduler);
        # caller is responsible for any tenant scoping required.
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_vacancy_id)
        )
        return result.scalar_one_or_none()

    async def list_by_statuses(self, statuses: list[str], limit: int = 50):
        """List vacancies whose status is in the given set, ordered by created_at desc.

        Used by sourcing pipeline (system context, no company filter).
        """
        # TENANT-EXEMPT: system-context (sourcing background scheduler);
        # walks all tenants to drive sourcing pipeline.
        result = await self.db.execute(
            select(JobVacancy)
            .where(JobVacancy.status.in_(statuses))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_paginated_no_tenant(self, limit: int = 30, offset: int = 0):
        """Paginated list across all tenants — used by Rails-adapter local
        fallback only. Caller is responsible for any tenancy check.

        ADR-001 cross-domain read: integration layer fallback when Rails
        is unavailable; Rails owns tenancy at the API gateway.
        """
        # TENANT-EXEMPT: Rails-adapter fallback; Rails owns tenancy at the
        # API gateway when the integration is healthy.
        result = await self.db.execute(
            select(JobVacancy).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_vacancies(
        self,
        company_id,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        skip: int = 0,
        limit: int = 500,
    ):
        query = select(JobVacancy).where(JobVacancy.company_id == company_id)
        if status:
            query = query.where(JobVacancy.status == status)
        if visibility:
            query = query.where(JobVacancy.visibility == visibility)
        query = query.offset(skip).limit(limit).order_by(JobVacancy.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_vacancy(self, job_vacancy: JobVacancy) -> JobVacancy:
        self.db.add(job_vacancy)
        await self.db.flush()
        await self.db.refresh(job_vacancy)
        return job_vacancy

    # ── Update ────────────────────────────────────────────────────────────────

    async def flush_and_refresh(self, obj) -> Any:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    # ── Session passthrough (for services that still take db) ────────────────

    def get_session(self) -> AsyncSession:
        return self.db

    async def search_by_query(self, company_id, query: str, offset: int, page_size: int):
        from sqlalchemy import func, select
        from app.models.job_vacancy import JobVacancy
        base_filter = JobVacancy.company_id == company_id
        if query and len(query) >= 2:
            search_term = f"%{query}%"
            search_filter = and_(
                base_filter,
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.job_id.ilike(search_term)
                )
            )
        else:
            search_filter = base_filter
        # TENANT-EXEMPT: dynamic builder — base_filter always carries
        # JobVacancy.company_id == company_id (line above).
        count_result = await self.db.execute(
            select(func.count()).select_from(JobVacancy).where(search_filter)
        )
        total = count_result.scalar() or 0
        # TENANT-EXEMPT: dynamic builder — base_filter always carries
        # JobVacancy.company_id == company_id.
        rows_result = await self.db.execute(
            select(JobVacancy).where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset).limit(page_size)
        )
        rows = list(rows_result.scalars().all())
        return total, rows


    async def search_for_summary_by_criteria(
        self,
        company_id,
        criteria: dict,
        limit: int = 10,
    ):
        """Search vacancies by sourcing-style criteria dict.

        Used by app/domains/sourcing/services/vacancy_search.py
        (Sprint Q2 ADR-001 cross-domain cleanup). Recognizes keys:
          cargo, gestor, area, senioridade, modelo_trabalho, localizacao, ano

        Returns ORM rows; caller is responsible for shaping VacancySummary.
        """
        from datetime import datetime
        from sqlalchemy import and_, or_, select
        from app.models.job_vacancy import JobVacancy

        valid_statuses = [
            "Concluída", "Fechada", "Filled", "Closed", "Cancelada", "Cancelled",
            "Ativa", "Active", "Open", "Em Andamento", "active", "ativa", "open",
        ]
        conditions = [
            JobVacancy.company_id == company_id,
            JobVacancy.status.in_(valid_statuses),
        ]

        if criteria.get("cargo"):
            conditions.append(JobVacancy.title.ilike(f"%{criteria['cargo']}%"))
        if criteria.get("gestor"):
            conditions.append(JobVacancy.manager.ilike(f"%{criteria['gestor']}%"))
        if criteria.get("area"):
            conditions.append(JobVacancy.department.ilike(f"%{criteria['area']}%"))
        if criteria.get("senioridade"):
            conditions.append(JobVacancy.seniority_level.ilike(f"%{criteria['senioridade']}%"))
        if criteria.get("modelo_trabalho"):
            conditions.append(JobVacancy.work_model.ilike(f"%{criteria['modelo_trabalho']}%"))
        if criteria.get("localizacao"):
            conditions.append(JobVacancy.location.ilike(f"%{criteria['localizacao']}%"))
        if criteria.get("ano"):
            year = int(criteria["ano"])
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31, 23, 59, 59)
            conditions.append(
                or_(
                    and_(JobVacancy.closed_at >= year_start, JobVacancy.closed_at <= year_end),
                    and_(JobVacancy.created_at >= year_start, JobVacancy.created_at <= year_end),
                )
            )

        # TENANT-EXEMPT: dynamic builder — conditions[0] is always
        # JobVacancy.company_id == company_id (composed above).
        result = await self.db.execute(
            select(JobVacancy)
            .where(and_(*conditions))
            .order_by(JobVacancy.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


    # ── Lookup helpers (Sprint Q2 ADR-001 — job_clone_service) ────────────────

    async def get_by_job_id_and_company(self, job_id: str, company_id):
        result = await self.db.execute(
            select(JobVacancy).where(
                JobVacancy.job_id == job_id,
                JobVacancy.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def owned_by_company(self, identifier: str, company_id) -> bool:
        """True se existe vaga desta company cujo id (UUID) OU job_id casa com identifier.

        Gate de ownership para writes que recebem o identificador do payload
        (ex: POST /wsi/questions/save). job_screening_questions e
        screening_question_sets nao tem RLS — este e o ponto canonico de
        validacao multi-tenant (audit 2026-06-05, P0 cross-tenant write).
        """
        conditions = [JobVacancy.job_id == identifier]
        try:
            conditions.append(JobVacancy.id == UUID(str(identifier)))
        except (ValueError, AttributeError, TypeError):
            pass
        result = await self.db.execute(
            select(JobVacancy.id)
            .where(JobVacancy.company_id == company_id, or_(*conditions))
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def search_by_title_ilike(self, title_pattern: str, company_id):
        result = await self.db.execute(
            select(JobVacancy).where(
                JobVacancy.title.ilike(f"%{title_pattern}%"),
                JobVacancy.company_id == company_id,
            )
        )
        return list(result.scalars().all())

    async def get_vacancy_by_id_only(self, job_vacancy_id: UUID):
        """Used by job_clone_service.get_job_summary_for_clone — caller scopes."""
        # TENANT-EXEMPT: caller (job_clone_service) verifies tenant
        # ownership before invoking; legacy compat surface.
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_vacancy_id)
        )
        return result.scalar_one_or_none()


    async def list_for_company_history(self, company_id: str, *, limit: int = 50):
        """Used by CompanyJobHistoryService — inference window of recent vacancies."""
        result = await self.db.execute(
            select(JobVacancy)
            .where(JobVacancy.company_id == company_id)
            .limit(limit)
        )
        return list(result.scalars().all())


    async def list_active_for_company(
        self,
        company_id: str,
        *,
        statuses: list[str] | None = None,
    ) -> list:
        """List active vacancies for a company.

        P1-6 (Fase B 2026-05-23): canonical method consumed by
        ``/lia/suggestions`` endpoint. Antes este SQL vivia inline no endpoint
        (violando ADR-001). Statuses canonical (mistura legacy PT/EN porque
        DB convive com ambos): open, active, Open, Active, Em Andamento.

        Multi-tenancy: filtro mandatorio por company_id (NUNCA trust payload).
        """
        from sqlalchemy import and_ as _and_

        if statuses is None:
            statuses = ["open", "active", "Open", "Active", "Em Andamento"]

        result = await self.db.execute(
            select(JobVacancy).where(
                _and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status.in_(statuses),
                )
            )
        )
        return list(result.scalars().all())


    async def list_indeed_published_active(self, company_id):
        """Used by job_board_service Indeed XML feed export."""
        from sqlalchemy import and_ as _and_
        result = await self.db.execute(
            select(JobVacancy).where(
                _and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.published_indeed,
                    JobVacancy.status.in_(["Ativa", "Publicada"]),
                )
            )
        )
        return list(result.scalars().all())


    async def get_by_id_strict_company(self, job_id, company_id):
        """Strict id+company lookup used by report/insights services."""
        from sqlalchemy import and_ as _and_
        result = await self.db.execute(
            select(JobVacancy).where(
                _and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()


    async def get_by_id_only_uuid(self, job_uuid: UUID):
        """Used by outcome_tracker._fetch_job — system context."""
        # TENANT-EXEMPT: outcome_tracker runs in system-context
        # (background scheduler), no per-request company_id.
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_uuid)
        )
        return result.scalar_one_or_none()


    async def search_by_conditions(self, conditions: list, *, limit: int = 50):
        """Generic conditions-based search used by vacancy_search_service."""
        from sqlalchemy import and_ as _and_
        # TENANT-EXEMPT: dynamic builder — caller (vacancy_search_service)
        # composes ``conditions`` always starting with
        # JobVacancy.company_id == X; AST sensor cannot trace.
        result = await self.db.execute(
            select(JobVacancy)
            .where(_and_(*conditions))
            .order_by(JobVacancy.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())



    # ── Multi-tenancy fail-closed helper ──────────────────────────────────────

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        """Fail-closed multi-tenancy gate. Raises if company_id is empty/None."""
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy invariant fail-closed)"
            )
        return company_id

    # ── ADR-001 W1-004-B: methods migrated from jobs_mgmt_tool_registry ──────

    async def get_recruitment_benchmarks(
        self,
        company_id: str,
        period_days: int = 90,
    ) -> dict:
        """Aggregated hiring stats: avg TTF, fill rate, active/total/filled counts.

        Returns dict with keys: avg_ttf_days, fill_rate, active_jobs,
        total_jobs, filled_jobs.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
                SELECT
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)
                        AS avg_ttf,
                    COUNT(*) FILTER (WHERE status = 'closed') AS filled,
                    COUNT(*) FILTER (WHERE status = 'active') AS active,
                    COUNT(*) AS total
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """),
            {"company_id": cid, "days": period_days},
        )
        row = result.mappings().first() or {}
        ttf = round(float(row.get("avg_ttf") or 0), 1)
        filled = int(row.get("filled") or 0)
        active = int(row.get("active") or 0)
        total = int(row.get("total") or 0)
        fill_rate = round((filled / total * 100) if total > 0 else 0, 1)
        return {
            "avg_ttf_days": ttf,
            "fill_rate": fill_rate,
            "active_jobs": active,
            "total_jobs": total,
            "filled_jobs": filled,
        }

    async def list_jobs_with_candidate_count(
        self,
        company_id: str,
        status: str = "all",
        department: str = "all",
        limit: int = 30,
    ) -> dict:
        """Vacancy list with candidate counts per stage.

        Returns dict with keys: jobs (list), total.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            _text("""
                SELECT id, title, status, priority, department, location,
                       created_at, deadline, company_id,
                       (SELECT COUNT(*) FROM vacancy_candidates vc
                        WHERE vc.vacancy_id = jv.id) AS candidate_count,
                       EXTRACT(DAY FROM NOW() - created_at)::int AS days_open
                FROM job_vacancies jv
                WHERE (:status = 'all' OR status ILIKE :status_val)
                  AND (:dept = 'all' OR department ILIKE :dept_val)
                  AND company_id = :company_id
                ORDER BY
                    CASE status
                        WHEN 'Ativa' THEN 1 WHEN 'Aprovada' THEN 2
                        WHEN 'Rascunho' THEN 3 WHEN 'Concluída' THEN 4
                        WHEN 'Arquivada' THEN 5 ELSE 6 END,
                    CASE priority WHEN 'alta' THEN 1 WHEN 'média' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT :lim
            """),
            {
                "status": status,
                "status_val": f"%{status}%",
                "dept": department,
                "dept_val": f"%{department}%",
                "company_id": cid,
                "lim": limit,
            },
        )
        jobs = []
        for row in rows.mappings():
            jobs.append({
                "id": str(row["id"]),
                "title": row["title"],
                "status": row["status"],
                "priority": row["priority"],
                "department": row["department"],
                "location": row["location"],
                "candidate_count": int(row["candidate_count"] or 0),
                "days_open": int(row["days_open"] or 0),
                "deadline": str(row["deadline"]) if row["deadline"] else None,
            })
        count_row = await self.db.execute(
            _text("""
                SELECT COUNT(*) AS total FROM job_vacancies
                WHERE (:status = 'all' OR status ILIKE :status_val)
                  AND (:dept = 'all' OR department ILIKE :dept_val)
                  AND company_id = :company_id
            """),
            {
                "status": status,
                "status_val": f"%{status}%",
                "dept": department,
                "dept_val": f"%{department}%",
                "company_id": cid,
            },
        )
        total = int((count_row.mappings().first() or {}).get("total", len(jobs)))
        return {"jobs": jobs, "total": total}

    async def get_job_details_with_days_open(
        self,
        job_id: str,
        company_id: str,
    ) -> dict | None:
        """Single job details including days_open + candidate counts by status.

        Returns None if not found. Otherwise returns dict with job fields +
        candidates_total + candidates_by_status.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        row_result = await self.db.execute(
            _text("""
                SELECT id, title, status, priority, department, location,
                       description, requirements, technical_requirements,
                       salary_range, benefits, created_at, deadline,
                       recruiter, manager, company_id,
                       EXTRACT(DAY FROM NOW() - created_at)::int AS days_open
                FROM job_vacancies
                WHERE id = :job_id AND company_id = :company_id
            """),
            {"job_id": job_id, "company_id": cid},
        )
        data = row_result.mappings().first()
        if not data:
            return None
        counts = await self.db.execute(
            _text("""
                SELECT status, COUNT(*) AS cnt
                FROM vacancy_candidates
                WHERE vacancy_id = :job_id AND company_id = :company_id
                GROUP BY status
            """),
            {"job_id": job_id, "company_id": cid},
        )
        by_status = {r["status"]: int(r["cnt"]) for r in counts.mappings()}
        total_candidates = sum(by_status.values())
        return {
            "job_id": str(data["id"]),
            "title": data["title"],
            "status": data["status"],
            "priority": data["priority"],
            "department": data["department"],
            "location": data["location"],
            "description": (data["description"] or "")[:500],
            "technical_requirements": data["technical_requirements"],
            "salary_range": data["salary_range"],
            "recruiter": data["recruiter"],
            "manager": data["manager"],
            "deadline": str(data["deadline"]) if data["deadline"] else None,
            "days_open": int(data["days_open"] or 0),
            "candidates_total": total_candidates,
            "candidates_by_status": by_status,
        }

    async def get_portfolio_metrics(
        self,
        company_id: str,
        period_days: int = 30,
    ) -> dict:
        """Aggregate portfolio health metrics.

        Returns dict with keys: total_active, total_paused, total_closed,
        total_draft, total, avg_time_to_hire, fill_rate.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        row_result = await self.db.execute(
            _text("""
                SELECT
                    COUNT(*) FILTER (WHERE status ILIKE '%ativa%' OR status ILIKE '%active%')
                        AS total_active,
                    COUNT(*) FILTER (WHERE status ILIKE '%pausada%' OR status ILIKE '%paused%')
                        AS total_paused,
                    COUNT(*) FILTER (WHERE status ILIKE '%conclu%' OR status ILIKE '%closed%')
                        AS total_closed,
                    COUNT(*) FILTER (WHERE status ILIKE '%rascunho%' OR status ILIKE '%draft%')
                        AS total_draft,
                    COUNT(*) AS total,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)
                        FILTER (WHERE status ILIKE '%conclu%' OR status ILIKE '%closed%')
                        AS avg_ttf
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """),
            {"company_id": cid, "days": period_days},
        )
        data = row_result.mappings().first() or {}
        total = int(data.get("total") or 0)
        closed = int(data.get("total_closed") or 0)
        return {
            "total_active": int(data.get("total_active") or 0),
            "total_paused": int(data.get("total_paused") or 0),
            "total_closed": closed,
            "total_draft": int(data.get("total_draft") or 0),
            "total": total,
            "avg_time_to_hire": round(float(data.get("avg_ttf") or 0), 1),
            "fill_rate": round(closed / total * 100, 1) if total > 0 else 0.0,
        }

    async def aggregate_list_metrics(
        self,
        vacancy_ids: list[str],
        company_id: str,
    ) -> dict[str, dict]:
        """P1-2: métricas reais por vaga para a lista de Gestão de Vagas.

        Substitui ``generate_lia_metrics`` (que FABRICAVA números com
        ``random.uniform`` — proibido pela regra de proveniência honesta do
        CLAUDE.md). Agrega 3 fontes canônicas company-scoped, cada uma em UMA
        query GROUP BY (sem N+1):
          - ``vacancy_candidates`` por stage  -> candidates_count + funnel_data
          - ``wsi_sessions``       por status -> triagens_*/sem_resposta
          - ``interviews``         por status -> entrevistas_agendadas

        Retorna ``{vacancy_id: {candidates_count, funnel_data, lia_metrics}}``.
        Vaga sem dados -> ausente do dict (caller usa defaults zerados).

        Multi-tenancy: company_id validado via _require_company_id fail-closed.
        ``wsi_sessions`` não tem company_id -> JOIN job_vacancies p/ escopar.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        if not vacancy_ids:
            return {}

        def _blank() -> dict:
            return {
                "candidates_count": 0,
                "funnel_data": {
                    "total": 0, "screening": 0, "interview": 0,
                    "final": 0, "hired": 0,
                },
                "lia_metrics": {
                    "pipeline_lia": 0,
                    "triagens_agendadas": 0,
                    "triagens_realizadas": 0,
                    "sem_resposta": 0,
                    "entrevistas_agendadas": 0,
                },
            }

        out: dict[str, dict] = {}

        # (1) vacancy_candidates -> candidates_count + funnel buckets (por stage)
        vc_rows = await self.db.execute(
            _text("""
                SELECT CAST(vacancy_id AS text) AS vid, stage, COUNT(*) AS cnt
                FROM vacancy_candidates
                WHERE vacancy_id = ANY(CAST(:ids AS uuid[]))
                  AND company_id = :cid
                GROUP BY vacancy_id, stage
            """),
            {"ids": vacancy_ids, "cid": cid},
        )
        for r in vc_rows.mappings():
            vid = str(r["vid"])
            cnt = int(r["cnt"] or 0)
            entry = out.setdefault(vid, _blank())
            entry["candidates_count"] += cnt
            entry["funnel_data"]["total"] += cnt
            entry["lia_metrics"]["pipeline_lia"] += cnt
            bucket = classify_funnel_stage(r["stage"])
            if bucket:
                entry["funnel_data"][bucket] += cnt

        # (2) wsi_sessions -> triagens agendadas/realizadas + sem_resposta
        wsi_rows = await self.db.execute(
            _text("""
                SELECT CAST(s.job_vacancy_id AS text) AS vid, s.status, COUNT(*) AS cnt
                FROM wsi_sessions s
                JOIN job_vacancies jv ON jv.id = s.job_vacancy_id
                WHERE s.job_vacancy_id = ANY(CAST(:ids AS uuid[]))
                  AND jv.company_id = :cid
                GROUP BY s.job_vacancy_id, s.status
            """),
            {"ids": vacancy_ids, "cid": cid},
        )
        for r in wsi_rows.mappings():
            vid = str(r["vid"])
            status = (r["status"] or "").lower()
            cnt = int(r["cnt"] or 0)
            lm = out.setdefault(vid, _blank())["lia_metrics"]
            if status == "completed":
                lm["triagens_realizadas"] += cnt
                lm["triagens_agendadas"] += cnt
            elif status == "in_progress":
                lm["triagens_agendadas"] += cnt
            elif status == "cancelled":
                lm["sem_resposta"] += cnt

        # (3) interviews -> entrevistas agendadas (scheduled = não-cancelada)
        iv_rows = await self.db.execute(
            _text("""
                SELECT CAST(job_vacancy_id AS text) AS vid, COUNT(*) AS cnt
                FROM interviews
                WHERE job_vacancy_id = ANY(CAST(:ids AS uuid[]))
                  AND company_id = :cid
                  AND (status IS NULL OR status <> 'cancelled')
                GROUP BY job_vacancy_id
            """),
            {"ids": vacancy_ids, "cid": cid},
        )
        for r in iv_rows.mappings():
            vid = str(r["vid"])
            cnt = int(r["cnt"] or 0)
            out.setdefault(vid, _blank())["lia_metrics"]["entrevistas_agendadas"] += cnt

        return out

    async def compare_jobs_by_ids(
        self,
        job_ids: list[str],
        company_id: str,
    ) -> list[dict]:
        """Side-by-side job comparison with candidate stats.

        Returns list of dicts with id, title, status, priority, department,
        days_open, candidate_count, avg_lia_score, rejected_count.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        if not job_ids:
            return []
        rows = await self.db.execute(
            _text("""
                SELECT jv.id, jv.title, jv.status, jv.priority, jv.department,
                       jv.created_at, jv.deadline,
                       EXTRACT(DAY FROM NOW() - jv.created_at)::int AS days_open,
                       COUNT(vc.id) AS candidate_count,
                       AVG(vc.lia_score) AS avg_score,
                       COUNT(vc.id) FILTER (WHERE vc.status = 'rejected') AS rejected_count
                FROM job_vacancies jv
                LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                      AND vc.company_id = :company_id
                WHERE jv.id = ANY(:ids::uuid[])
                  AND jv.company_id = :company_id
                GROUP BY jv.id
                ORDER BY jv.created_at DESC
            """),
            {"ids": job_ids, "company_id": cid},
        )
        result = []
        for row in rows.mappings():
            result.append({
                "id": str(row["id"]),
                "title": row["title"],
                "status": row["status"],
                "priority": row["priority"],
                "department": row["department"],
                "days_open": int(row["days_open"] or 0),
                "candidate_count": int(row["candidate_count"] or 0),
                "avg_lia_score": round(float(row["avg_score"] or 0), 1),
                "rejected_count": int(row["rejected_count"] or 0),
            })
        return result

    async def get_sla_status(
        self,
        company_id: str,
        job_id: str = "",
    ) -> dict:
        """SLA compliance status for active jobs.

        Returns dict with keys: overdue_jobs, at_risk_jobs, compliant_count,
        overall_status.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            _text("""
                SELECT id, title, status, deadline,
                       EXTRACT(DAY FROM NOW() - created_at)::int AS days_open,
                       EXTRACT(DAY FROM deadline - NOW())::int AS days_to_deadline
                FROM job_vacancies
                WHERE (status ILIKE '%ativa%' OR status ILIKE '%active%')
                  AND (:jid = '' OR id::text = :jid)
                  AND company_id = :company_id
            """),
            {"jid": job_id, "company_id": cid},
        )
        overdue_jobs: list[dict] = []
        at_risk_jobs: list[dict] = []
        compliant_count = 0
        for row in rows.mappings():
            dtd = row["days_to_deadline"]
            entry = {
                "id": str(row["id"]),
                "title": row["title"],
                "days_open": int(row["days_open"] or 0),
                "days_to_deadline": int(dtd) if dtd is not None else None,
            }
            if dtd is not None and dtd < 0:
                overdue_jobs.append({**entry, "overdue_days": abs(int(dtd))})
            elif dtd is not None and dtd <= 7:
                at_risk_jobs.append({**entry, "urgency": "high"})
            elif dtd is not None and dtd <= 14:
                at_risk_jobs.append({**entry, "urgency": "medium"})
            else:
                compliant_count += 1
        overall = (
            "overdue" if overdue_jobs
            else ("at_risk" if at_risk_jobs else "compliant")
        )
        return {
            "overdue_jobs": overdue_jobs,
            "at_risk_jobs": at_risk_jobs,
            "compliant_count": compliant_count,
            "overall_status": overall,
        }

    async def get_bottleneck_analysis(
        self,
        company_id: str,
        department: str = "all",
    ) -> list[dict]:
        """Stage bottleneck analysis: stagnant candidates, long-open jobs, low scores.

        Returns list of dicts with job_id, title, department, days_open,
        total_candidates, issues.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            _text("""
                SELECT jv.id, jv.title, jv.department,
                       EXTRACT(DAY FROM NOW() - jv.created_at)::int AS days_open,
                       COUNT(vc.id) AS total_candidates,
                       COUNT(vc.id) FILTER (
                           WHERE vc.updated_at < NOW() - INTERVAL '14 days'
                       ) AS stagnant_count,
                       AVG(vc.lia_score) AS avg_score
                FROM job_vacancies jv
                LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                WHERE (jv.status ILIKE '%ativa%' OR jv.status ILIKE '%active%')
                  AND (:dept = 'all' OR jv.department ILIKE :dept_val)
                  AND jv.company_id = :company_id
                GROUP BY jv.id
                HAVING COUNT(vc.id) > 0
                ORDER BY stagnant_count DESC, days_open DESC
                LIMIT 20
            """),
            {"dept": department, "dept_val": f"%{department}%", "company_id": cid},
        )
        bottlenecks = []
        for row in rows.mappings():
            stagnant = int(row["stagnant_count"] or 0)
            total = int(row["total_candidates"] or 0)
            days = int(row["days_open"] or 0)
            issues: list[dict] = []
            if stagnant > 0 and total > 0:
                pct = stagnant / total * 100
                if pct > 30:
                    issues.append({
                        "type": "high_stagnation",
                        "severity": "high",
                        "detail": (
                            f"{stagnant}/{total} candidatos parados >14 dias "
                            f"({pct:.0f}%)"
                        ),
                    })
            if days > 60:
                issues.append({
                    "type": "long_time_open",
                    "severity": "medium",
                    "detail": f"Vaga aberta ha {days} dias (benchmark: 35 dias)",
                })
            avg_score = round(float(row["avg_score"] or 0), 1)
            if 0 < avg_score < 3.0:
                issues.append({
                    "type": "low_quality_pool",
                    "severity": "high",
                    "detail": f"Score medio baixo ({avg_score}/5)",
                })
            if issues:
                bottlenecks.append({
                    "job_id": str(row["id"]),
                    "title": row["title"],
                    "department": row["department"],
                    "days_open": days,
                    "total_candidates": total,
                    "issues": issues,
                })
        return bottlenecks

    async def get_report_summary(
        self,
        company_id: str,
        period_days: int = 30,
    ) -> dict:
        """Comprehensive report data: total, active, closed, avg TTF.

        Returns dict with keys: total_jobs, active, closed, avg_ttf_days.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        row_result = await self.db.execute(
            _text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status ILIKE '%ativa%') AS active,
                    COUNT(*) FILTER (WHERE status ILIKE '%conclu%') AS closed,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)
                        FILTER (WHERE status ILIKE '%conclu%') AS avg_ttf
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND created_at > NOW() - MAKE_INTERVAL(days => :days)
            """),
            {"company_id": cid, "days": period_days},
        )
        data = row_result.mappings().first() or {}
        return {
            "total_jobs": int(data.get("total") or 0),
            "active": int(data.get("active") or 0),
            "closed": int(data.get("closed") or 0),
            "avg_ttf_days": round(float(data.get("avg_ttf") or 0), 1),
        }

    async def update_priority(
        self,
        job_id: str,
        company_id: str,
        priority: str,
    ) -> dict | None:
        """Update job priority. Returns previous+new priority or None if not found.

        Returns dict with previous_priority and new_priority, or None.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        prev = await self.db.execute(
            _text(
                "SELECT priority FROM job_vacancies "
                "WHERE id = :job_id AND company_id = :company_id"
            ),
            {"job_id": job_id, "company_id": cid},
        )
        prev_row = prev.mappings().first()
        if not prev_row:
            return None
        await self.db.execute(
            _text(
                "UPDATE job_vacancies SET priority = :priority, updated_at = NOW() "
                "WHERE id = :job_id AND company_id = :company_id"
            ),
            {"priority": priority, "job_id": job_id, "company_id": cid},
        )
        return {
            "previous_priority": prev_row["priority"],
            "new_priority": priority,
        }

    async def update_status(
        self,
        job_id: str,
        company_id: str,
        new_status: str,
    ) -> bool:
        """Update job status. Returns True if row found and updated, False otherwise.

        Used by jobs_mgmt_tool_registry for pause/reopen/close.
        """
        from sqlalchemy import text as _text

        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
                UPDATE job_vacancies SET status = :new_status, updated_at = NOW()
                WHERE id = :job_id AND company_id = :company_id
                RETURNING status
            """),
            {"new_status": new_status, "job_id": job_id, "company_id": cid},
        )
        return result.fetchone() is not None


    # ── ADR-001 W1-004-C: new methods migrated from recruiter_assistant services ──

    async def get_recruiter_id(self, job_id: str, company_id: str) -> "str | None":
        """Retorna recruiter_id de uma vaga (para notificacoes).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as _text
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            _text(
                "SELECT recruiter_id FROM job_vacancies "
                "WHERE id::text = :jid AND company_id = :company_id LIMIT 1"
            ),
            {"jid": job_id, "company_id": cid},
        )
        row = result.fetchone()
        return str(row[0]) if row and row[0] else None

    async def get_jobs_near_deadline(self, company_id: str, days_ahead: int = 7) -> "list[dict]":
        """Vagas com deadline nos proximos N dias.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as _text
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
            SELECT id, title, deadline,
                   EXTRACT(DAY FROM deadline - NOW())::int AS days_remaining
            FROM job_vacancies
            WHERE company_id = :company_id
              AND status NOT IN ('fechada', 'cancelada')
              AND deadline IS NOT NULL
              AND deadline < NOW() + INTERVAL '1 day' * :days_ahead
              AND deadline > NOW()
            ORDER BY deadline ASC
            """),
            {"company_id": cid, "days_ahead": days_ahead}
        )
        return [dict(r) for r in result.mappings().fetchall()]


    async def update_fields(
        self,
        vacancy_id: str,
        company_id: str,
        fields: dict,
    ) -> bool:
        """Update arbitrary JSONB/scalar fields on a job vacancy.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        Used by wizard tools (update_competencies) to persist confirmed
        competency lists without a full draft save cycle.

        Args:
            vacancy_id: UUID of the job vacancy.
            company_id: Company scope (from JWT context).
            fields: Dict of column_name -> value to update.
                    Allowed columns whitelist enforced server-side.

        Returns:
            True if the row was found and updated, False otherwise.
        """
        import json as _json
        from sqlalchemy import text as _text

        _ALLOWED_FIELDS = frozenset({
            "confirmed_technical_competencies",
            "confirmed_behavioral_competencies",
            "competency_tree",
            "question_distribution",
        })

        safe_fields = {k: v for k, v in fields.items() if k in _ALLOWED_FIELDS}
        if not safe_fields:
            return False

        cid = self._require_company_id(company_id)

        # Build SET clause dynamically (only whitelisted fields)
        set_clauses = ", ".join(f"{col} = :{col}" for col in safe_fields)
        params = {"vacancy_id": vacancy_id, "company_id": cid}
        for col, val in safe_fields.items():
            # Serialize lists/dicts to JSON string for JSONB columns
            params[col] = _json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else val

        result = await self.db.execute(
            _text(
                f"UPDATE job_vacancies SET {set_clauses}, updated_at = NOW() "
                "WHERE id = :vacancy_id AND company_id = :company_id "
                "RETURNING id"
            ),
            params,
        )
        return result.fetchone() is not None

# Backwards-compatible alias: callers in app/domains/analytics + app/domains/sourcing
# import "JobVacancyCrudRepository" (PascalCase) — pre-existing in the codebase.
# Real class name is JobVacancyCRUDRepository (all-caps CRUD). Alias avoids
# breaking those imports while keeping a single canonical class.
JobVacancyCrudRepository = JobVacancyCRUDRepository
