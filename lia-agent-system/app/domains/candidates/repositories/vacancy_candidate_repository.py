"""
VacancyCandidateRepository — session-in-constructor pattern.
Covers all VacancyCandidate DB operations from app/api/v1/candidates.py.
"""
import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import VacancyCandidate

logger = logging.getLogger(__name__)


class VacancyCandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_vacancy_and_candidate(
        self,
        vacancy_id: str | UUID,
        candidate_id: str | UUID,
        company_id: str | None = None,
    ) -> VacancyCandidate | None:
        """Lookup VacancyCandidate by composite (vacancy_id, candidate_id).

        Both ids accept str | UUID for caller convenience (HTTP payloads
        send strings; service callers may have UUIDs). Returns None when
        the str fails UUID parsing — same null semantics as a not-found row,
        which is what every caller already handles.

        Multi-tenancy defense-in-depth: pass company_id quando caller souber
        (REGRA ZERO + harness B.1 fail-closed). Postgres RLS via get_tenant_db
        continua filtrando quando omitido.
        """
        try:
            vacancy_uuid = (
                uuid.UUID(str(vacancy_id)) if isinstance(vacancy_id, str) else vacancy_id
            )
            candidate_uuid = (
                uuid.UUID(str(candidate_id)) if isinstance(candidate_id, str) else candidate_id
            )
        except (ValueError, TypeError):
            return None

        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(VacancyCandidate).where(
            VacancyCandidate.vacancy_id == vacancy_uuid,
            VacancyCandidate.candidate_id == candidate_uuid,
        )
        if company_id:
            query = query.where(VacancyCandidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_most_recent_for_candidate(
        self,
        candidate_id: str | UUID,
        company_id: str | None = None,
    ) -> VacancyCandidate | None:
        """Get most recent VacancyCandidate for candidate.

        Multi-tenancy defense-in-depth via company_id filter (REGRA ZERO + B.1).
        """
        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = (
            select(VacancyCandidate)
            .where(
                VacancyCandidate.candidate_id == (
                    uuid.UUID(str(candidate_id)) if isinstance(candidate_id, str) else candidate_id
                )
            )
            .order_by(VacancyCandidate.updated_at.desc())
            .limit(1)
        )
        if company_id:
            query = query.where(VacancyCandidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_candidate_and_job(
        self,
        candidate_id: str,
        job_vacancy_id: str | None,
        company_id: str | None = None,
    ) -> VacancyCandidate | None:
        """
        Find VacancyCandidate by candidate + optional job.
        Falls back to most-recent if job_vacancy_id is None or invalid UUID.

        Multi-tenancy defense-in-depth via company_id filter (REGRA ZERO + B.1).
        """
        if job_vacancy_id:
            try:
                vacancy_uuid = uuid.UUID(str(job_vacancy_id))
                vc = await self.get_by_vacancy_and_candidate(
                    vacancy_uuid, candidate_id, company_id=company_id
                )
                if vc:
                    return vc
            except ValueError:
                logger.warning(
                    f"Invalid job_vacancy_id format: {job_vacancy_id} — falling back to most recent"
                )
        return await self.get_most_recent_for_candidate(
            candidate_id, company_id=company_id
        )

    async def update(self, vacancy_candidate: VacancyCandidate) -> VacancyCandidate:
        await self.db.commit()
        await self.db.refresh(vacancy_candidate)
        return vacancy_candidate

    # ── Cross-domain reads (used by automation_handlers — ADR-001) ──────────

    async def get_by_vacancy_candidate_and_company(
        self,
        vacancy_id: str | UUID,
        candidate_id: str | UUID,
        company_id: str | UUID,
    ) -> VacancyCandidate | None:
        """Multi-tenant lookup of a VacancyCandidate triple.

        Used by automation handlers' multi-tenancy validation.
        """
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.candidate_id == candidate_id,
                VacancyCandidate.vacancy_id == vacancy_id,
                VacancyCandidate.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_eligibility_rejected(
        self,
        candidate_id: str | UUID,
        vacancy_id: str | UUID,
        company_id: str | UUID,
        reason: str = "eligibility_failed",
    ) -> bool:
        """Talent pool: marca o VacancyCandidate como rejected quando o candidato
        reprova pergunta eliminatoria de elegibilidade. Idempotente."""
        vc = await self.get_by_vacancy_candidate_and_company(
            vacancy_id, candidate_id, company_id
        )
        if not vc:
            return False
        if vc.status == "rejected":
            return True
        vc.previous_status = vc.status
        vc.status = "rejected"
        _note = f"[elegibilidade] reprovado em pergunta eliminatoria ({reason})"
        vc.notes = f"{vc.notes}\n{_note}".strip() if vc.notes else _note
        await self.update(vc)
        return True

    async def list_awaiting_screening_for_vacancy(
        self,
        vacancy_id: str | UUID,
        limit: int = 1,
        company_id: str | None = None,
    ) -> list[VacancyCandidate]:
        """Return queued candidates ordered by lia_score DESC, created_at ASC.

        Used by automation_handlers.process_screening_queue (slot promotion).

        Multi-tenancy defense-in-depth via company_id filter (REGRA ZERO + B.1).
        """
        from sqlalchemy import and_

        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = (
            select(VacancyCandidate)
            .where(
                and_(
                    VacancyCandidate.vacancy_id == vacancy_id,
                    VacancyCandidate.status == "awaiting_screening",
                )
            )
            .order_by(
                VacancyCandidate.lia_score.desc().nullslast(),
                VacancyCandidate.created_at.asc(),
            )
            .limit(limit)
        )
        if company_id:
            query = query.where(VacancyCandidate.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_created_since(
        self,
        company_id: str,
        since_dt,
    ) -> int:
        """Count candidates created since ``since_dt`` for a company.

        P1-6 (Fase B 2026-05-23): canonical method consumed por
        ``/lia/suggestions`` para detectar fluxo recente de candidatos novos.
        Antes era inline ``select(func.count(...))`` no endpoint (viola ADR-001).

        Multi-tenancy: filtro mandatorio por company_id.
        """
        from sqlalchemy import and_ as _and_, func

        result = await self.db.execute(
            select(func.count(VacancyCandidate.candidate_id)).where(
                _and_(
                    VacancyCandidate.company_id == company_id,
                    VacancyCandidate.created_at >= since_dt,
                )
            )
        )
        return result.scalar() or 0


    async def list_stale_for_company(
        self,
        company_id: str,
        days_threshold: int = 7,
        statuses: list[str] | None = None,
    ) -> list[VacancyCandidate]:
        """WT-2022 ProactiveDetector: candidates sem feedback X dias.

        Multi-tenancy: filter mandatorio por company_id (NUNCA trust payload).
        Status default canonical: pos-triagem (interview/screening/final_evaluation).
        Util consumer: app/shared/services/proactive_detector_service.py.
        """
        from datetime import datetime, timedelta

        if statuses is None:
            statuses = ["interview", "screening", "final_evaluation"]
        cutoff = datetime.utcnow() - timedelta(days=days_threshold)

        result = await self.db.execute(
            select(VacancyCandidate)
            .where(
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.updated_at < cutoff,
                VacancyCandidate.status.in_(statuses),
            )
            .order_by(VacancyCandidate.updated_at.asc())
        )
        return list(result.scalars().all())

    # ── ADR-001 W1-004-B: methods migrated from talent_tool_registry ──────────

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        """Fail-closed multi-tenancy gate. Raises if company_id is empty/None."""
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy invariant fail-closed)"
            )
        return company_id

    async def list_candidate_ids_for_vacancy(
        self, vacancy_id: str, company_id: str
    ) -> list[str]:
        """P0-1: candidate_ids vinculados a uma vaga (company-scoped, fail-closed).

        Usado para escopar list_candidates por vaga (board do Kanban) reusando o
        path `ids=` existente — board e candidates_count passam a ler a MESMA
        fonte canônica (vacancy_candidates). Vaga sem links → lista vazia.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            sa_text(
                """
                SELECT vc.candidate_id
                FROM vacancy_candidates vc
                WHERE vc.vacancy_id::text = :vid AND vc.company_id = :cid
                ORDER BY vc.lia_score DESC NULLS LAST, vc.created_at DESC
                """
            ),
            {"vid": vacancy_id, "cid": cid},
        )
        return [str(r[0]) for r in rows.fetchall()]

    async def list_for_talent_funnel(
        self,
        company_id: str,
        status: str = "all",
        vacancy_id: str = "",
        limit: int = 20,
    ) -> dict:
        """List candidates in the funnel with status and vacancy filters.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        rows = await self.db.execute(
            sa_text("""
                SELECT vc.id AS vc_id, vc.vacancy_id, vc.candidate_id,
                       vc.status, vc.stage, vc.lia_score, vc.match_percentage,
                       vc.created_at,
                       c.name, c.current_title, c.location_city, c.technical_skills
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE (:status = 'all' OR vc.status = :status)
                  AND (:vid = '' OR vc.vacancy_id::text = :vid)
                  AND vc.company_id = :cid
                ORDER BY vc.lia_score DESC NULLS LAST, vc.created_at DESC
                LIMIT :lim
            """),
            {"status": status, "vid": vacancy_id, "cid": cid, "lim": limit},
        )
        candidates = []
        for row in rows.mappings():
            candidates.append({
                "id": str(row["candidate_id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "location": row["location_city"],
                "skills": row["technical_skills"] or [],
                "status": row["status"],
                "stage": row["stage"],
                "lia_score": row["lia_score"],
                "match_percentage": row["match_percentage"],
                "applied_at": str(row["created_at"]) if row["created_at"] else None,
            })

        count_row = await self.db.execute(
            sa_text("""
                SELECT COUNT(*) AS total FROM vacancy_candidates vc
                WHERE (:status = 'all' OR vc.status = :status)
                  AND (:vid = '' OR vc.vacancy_id::text = :vid)
                  AND vc.company_id = :cid
            """),
            {"status": status, "vid": vacancy_id, "cid": cid},
        )
        total = int((count_row.mappings().first() or {}).get("total", len(candidates)))
        return {"candidates": candidates, "total": total}

    async def rank_for_job(
        self,
        vacancy_id: str,
        company_id: str,
        criteria: str = "fit_score",
        limit: int = 50,
    ) -> list[dict]:
        """Rank non-rejected candidates for a vacancy by score or match.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        order_by = "match" if criteria == "skills" else "score"
        rows = await self.db.execute(
            sa_text("""
                SELECT vc.candidate_id, vc.status, vc.stage,
                       vc.lia_score, vc.match_percentage,
                       c.name, c.current_title, c.technical_skills
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.vacancy_id::text = :vid
                  AND vc.company_id = :cid
                  AND vc.status != 'rejected'
                ORDER BY
                  CASE
                    WHEN :order_by = 'match' THEN vc.match_percentage
                    WHEN :order_by = 'score' THEN vc.lia_score
                    ELSE vc.lia_score
                  END DESC NULLS LAST
                LIMIT :lim
            """),
            {"vid": vacancy_id, "cid": cid, "order_by": order_by, "lim": limit},
        )
        ranking = []
        for position, row in enumerate(rows.mappings(), start=1):
            ranking.append({
                "position": position,
                "candidate_id": str(row["candidate_id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "skills": row["technical_skills"] or [],
                "lia_score": row["lia_score"],
                "match_percentage": row["match_percentage"],
                "status": row["status"],
                "stage": row["stage"],
            })
        return ranking

    async def update_match_percentage(
        self,
        candidate_id: str,
        vacancy_id: str,
        match_percentage: float,
    ) -> None:
        """Persist match_percentage on vacancy_candidate record.

        No company_id required here — caller must gate on company_id before calling.
        Composite (candidate_id, vacancy_id) uniquely identifies the record.
        """
        from sqlalchemy import text as sa_text
        await self.db.execute(
            sa_text("""
                UPDATE vacancy_candidates
                SET match_percentage = :mp
                WHERE candidate_id = :cid AND vacancy_id::text = :vid
            """),
            {"mp": match_percentage, "cid": candidate_id, "vid": vacancy_id},
        )
        await self.db.commit()

    async def get_pool_benchmarks(
        self,
        company_id: str,
        vacancy_id: str = "",
    ) -> dict:
        """Get pool size, avg score, and stage distribution for benchmarks.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            sa_text("""
                SELECT
                    COUNT(*) AS total,
                    AVG(CASE WHEN score IS NOT NULL THEN score ELSE 0 END) AS avg_score
                FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
            """),
            {"vid": vacancy_id, "cid": cid},
        )
        row = result.mappings().first()
        pool_size = int(row["total"] or 0) if row else 0
        avg_score = round(float(row["avg_score"] or 0), 1) if row else 0.0

        stage_result = await self.db.execute(
            sa_text("""
                SELECT stage, COUNT(*) AS cnt
                FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
                GROUP BY stage
                ORDER BY cnt DESC
            """),
            {"vid": vacancy_id, "cid": cid},
        )
        stage_distribution = {}
        for srow in stage_result.mappings():
            stage_distribution[str(srow["stage"])] = int(srow["cnt"])

        return {"pool_size": pool_size, "avg_score": avg_score, "stage_distribution": stage_distribution}

    async def get_pool_health(
        self,
        company_id: str,
        vacancy_id: str = "",
    ) -> dict:
        """Get pool health metrics: size, avg score, stagnant count.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as sa_text
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            sa_text("""
                SELECT
                    COUNT(*) AS total,
                    AVG(CASE WHEN score IS NOT NULL THEN score ELSE 0 END) AS avg_score,
                    COUNT(*) FILTER (
                        WHERE updated_at < NOW() - INTERVAL '14 days'
                    ) AS stagnant
                FROM vacancy_candidates
                WHERE (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
            """),
            {"vid": vacancy_id, "cid": cid},
        )
        row = result.mappings().first()
        if row:
            return {
                "pool_size": int(row["total"] or 0),
                "avg_score": round(float(row["avg_score"] or 0), 1),
                "stagnant_count": int(row["stagnant"] or 0),
            }
        return {"pool_size": 0, "avg_score": 0.0, "stagnant_count": 0}

    # ── ADR-001 W1-004-C: new methods migrated from services ──────────────────

    async def get_lia_score(self, candidate_id: str, vacancy_id: str, company_id: str) -> float:
        """Score LIA para um candidato numa vaga específica.

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as _text
        self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
            SELECT COALESCE(lia_score, match_percentage, 0.5)
            FROM vacancy_candidates
            WHERE candidate_id::text = :cid
              AND vacancy_id::text = :vid
              AND company_id = :company_id
            LIMIT 1
            """),
            {"cid": candidate_id, "vid": vacancy_id, "company_id": company_id}
        )
        row = result.fetchone()
        return float(row[0]) if row else 0.5

    async def get_latest_lia_score(self, candidate_id: str, company_id: str) -> float:
        """Score LIA mais recente para um candidato (qualquer vaga).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        """
        from sqlalchemy import text as _text
        self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
            SELECT COALESCE(lia_score, match_percentage, 0.5)
            FROM vacancy_candidates
            WHERE candidate_id::text = :cid
              AND company_id = :company_id
            ORDER BY created_at DESC LIMIT 1
            """),
            {"cid": candidate_id, "company_id": company_id}
        )
        row = result.fetchone()
        return float(row[0]) if row else 0.5

    async def append_note(self, candidate_id: str, company_id: str, note: str) -> bool:
        """Adiciona nota a um vacancy_candidate (COALESCE append).

        Multi-tenancy: company_id validated via _require_company_id fail-closed.
        Returns True if at least one row was updated.
        """
        from sqlalchemy import text as _text
        self._require_company_id(company_id)
        result = await self.db.execute(
            _text("""
            UPDATE vacancy_candidates
            SET notes = COALESCE(notes, '') || :separator || :note,
                updated_at = NOW()
            WHERE candidate_id::text = :cid AND company_id = :company_id
            """),
            {"cid": candidate_id, "company_id": company_id, "note": note, "separator": "\n---\n"}
        )
        await self.db.commit()
        return result.rowcount > 0

    async def count_status_for_candidates(
        self,
        company_id: str,
        candidate_ids: list[str],
    ) -> dict[str, int]:
        """Conta status canonical (approved/rejected/pending) para um conjunto
        de candidate_ids, escolhendo o status MAIS DECISIVO por candidato.

        Onda C4.1 (2026-05-29): consumido por
        GET /custom-agents/{id}/kpis para popular candidates_approved/
        rejected/pending (antes hardcoded 0 — quebrava perguntas 1+2 do Paulo).

        Um mesmo candidato pode estar em N vagas com status distintos. Regra de
        precedencia por candidato (decisao terminal > em fluxo):
          approved  > rejected > pending
        Logo um candidato aprovado em qualquer vaga conta como approved; se nao
        aprovado mas rejeitado em alguma, conta rejected; senao pending.

        Mapeamento canonical (VacancyCandidate.VALID_STATUSES):
          approved = approved, hired, shortlisted, offer
          rejected = rejected, not_selected, cancelled
          pending  = sourced, pending, on_hold, screening, interview (resto)

        Multi-tenancy: company_id validado fail-closed (candidatos de outro
        tenant NUNCA contam). Retorna {"approved":N,"rejected":N,"pending":N}.
        """
        from sqlalchemy import and_ as _and_

        cid = self._require_company_id(company_id)
        empty = {"approved": 0, "rejected": 0, "pending": 0}
        if not candidate_ids:
            return dict(empty)

        # normaliza para str (candidate_id em vacancy_candidates e UUID; o set
        # do endpoint vem como str — comparamos via cast textual fail-safe)
        wanted = {str(c) for c in candidate_ids if c}
        if not wanted:
            return dict(empty)

        approved_statuses = {"approved", "hired", "shortlisted", "offer"}
        rejected_statuses = {"rejected", "not_selected", "cancelled"}

        # candidate_id em vacancy_candidates e UUID — descartamos ids legacy/
        # bigint que nunca casariam (fail-safe, evita query com IN vazio).
        wanted_uuids = [UUID(c) for c in wanted if _is_uuid(c)]
        if not wanted_uuids:
            return dict(empty)

        result = await self.db.execute(
            select(
                VacancyCandidate.candidate_id,
                VacancyCandidate.status,
            ).where(
                _and_(
                    VacancyCandidate.company_id == cid,
                    VacancyCandidate.candidate_id.in_(wanted_uuids),
                )
            )
        )

        # precedencia por candidato: 2=approved, 1=rejected, 0=pending
        best_rank: dict[str, int] = {}
        for row_cid, status in result.all():
            key = str(row_cid)
            if status in approved_statuses:
                rank = 2
            elif status in rejected_statuses:
                rank = 1
            else:
                rank = 0
            if rank > best_rank.get(key, -1):
                best_rank[key] = rank

        counts = dict(empty)
        for rank in best_rank.values():
            if rank == 2:
                counts["approved"] += 1
            elif rank == 1:
                counts["rejected"] += 1
            else:
                counts["pending"] += 1
        return counts


def _is_uuid(value: str) -> bool:
    """True se value e um UUID valido (fail-safe para candidate_ids
    legacy/bigint que nao batem com vacancy_candidates.candidate_id UUID)."""
    try:
        UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False
