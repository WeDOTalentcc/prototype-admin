"""WSI (WeDoTalent Skill Index) Repository — DB access layer for WSI sessions.

Extracted from app/api/wsi_endpoints.py as part of Phase 2 refactor.
All 25 direct DB calls in wsi_endpoints.py are represented here as named methods.

Tables covered:
  - wsi_sessions
  - wsi_questions
  - wsi_response_analyses
  - wsi_results
  - wsi_reports
  - wsi_feedbacks
"""
import json
import hashlib
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.voice.schemas.wsi_types import (
    WsiCandidateRankRow,
    WsiFeedbackRow,
    WsiJobVacancyContextRow,
    WsiQuestionTextRow,
    WsiReportRow,
    WsiResultRow,
    WsiSessionRow,
    WsiVacancyAveragesRow,
)


class WsiRepository:
    """Repository for WSI screening workflow data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # wsi_sessions
    # ------------------------------------------------------------------

    async def upsert_session(
        self,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        screening_type: str,
        mode: str,
        status: str,
        question_set_version: Any = None,
        question_set_id: Any = None,
    ) -> None:
        """Insert a new WSI session; silently skip if session_id already exists."""
        # RLS-EXEMPT: wsi_sessions — transitive isolation via job_vacancy_id join (migration 118 design decision)
        await self.db.execute(text("""
            INSERT INTO wsi_sessions (
                id, candidate_id, job_vacancy_id, screening_type, mode, status,
                question_set_version, question_set_id
            )
            VALUES (
                :session_id, :candidate_id, :job_vacancy_id, :screening_type, :mode, :status,
                :question_set_version, :question_set_id
            )
            ON CONFLICT (id) DO NOTHING
        """), {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "screening_type": screening_type,
            "mode": mode,
            "status": status,
            "question_set_version": question_set_version,
            "question_set_id": question_set_id,
        })

    async def complete_session(self, session_id: str) -> None:
        """Mark a session as completed and set completed_at timestamp."""
        await self.db.execute(text("""
            UPDATE wsi_sessions
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = :session_id
        """), {"session_id": session_id})

    async def get_session(self, session_id: str) -> WsiSessionRow | None:
        """Fetch core session row by ID. Returns a Row or None."""
        result = await self.db.execute(text("""
            SELECT id, candidate_id, job_vacancy_id, screening_type, mode,
                   status, started_at, completed_at
            FROM wsi_sessions
            WHERE id = :session_id
        """), {"session_id": session_id})
        return result.fetchone()

    # ------------------------------------------------------------------
    # wsi_questions
    # ------------------------------------------------------------------

    async def insert_question(
        self,
        question_id: str,
        session_id: str,
        competency: str,
        framework: str,
        question_type: str,
        question_text: str,
        weight: float,
        expected_signals: list,
        scoring_criteria: dict,
        sequence_order: int,
        is_critical: bool = False,
    ) -> None:
        """Persist a single WSI question for a session."""
        # RLS-EXEMPT: wsi_questions — transitive via wsi_sessions.job_vacancy_id
        await self.db.execute(text("""
            INSERT INTO wsi_questions (
                id, session_id, competency, framework, question_type,
                question_text, weight, expected_signals, scoring_criteria, sequence_order
            )
            VALUES (
                :id, :session_id, :competency, :framework, :question_type,
                :question_text, :weight, :expected_signals::jsonb, :scoring_criteria::jsonb, :sequence_order
            )
        """), {
            "id": question_id,
            "session_id": session_id,
            "competency": competency,
            "framework": framework,
            "question_type": question_type,
            "question_text": question_text,
            "weight": weight,
            "expected_signals": json.dumps(expected_signals),
            "scoring_criteria": json.dumps({**scoring_criteria, "is_critical": is_critical}),
            "sequence_order": sequence_order,
        })

    async def get_questions_for_session(self, session_id: str) -> list:
        """Return ordered questions for a session."""
        result = await self.db.execute(text("""
            SELECT id, competency, framework, question_type, question_text, weight, sequence_order
            FROM wsi_questions
            WHERE session_id = :session_id
            ORDER BY sequence_order
        """), {"session_id": session_id})
        return result.fetchall()

    # ------------------------------------------------------------------
    # wsi_response_analyses
    # ------------------------------------------------------------------

    async def insert_response_analysis(
        self,
        analysis_id: str,
        session_id: str,
        question_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        competency: str,
        response_text: str,
        response_audio_url: str | None,
        autodeclaration_score: float | None,
        context_score: float | None,
        bloom_level: int | None,
        dreyfus_level: int | None,
        evidences: list,
        red_flags: list,
        consistency_penalty: float | None,
        final_score: float,
        justification: str,
    ) -> None:
        """Persist a response analysis record."""
        # RLS-EXEMPT: wsi_response_analyses — transitive via session
        await self.db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, response_audio_url,
                autodeclaration_score, context_score, bloom_level, dreyfus_level,
                evidences, red_flags, consistency_penalty, final_score, justification
            )
            VALUES (
                :id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                :competency, :response_text, :response_audio_url,
                :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level,
                :evidences::jsonb, :red_flags::jsonb, :consistency_penalty, :final_score, :justification
            )
        """), {
            "id": analysis_id,
            "session_id": session_id,
            "question_id": question_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "competency": competency,
            "response_text": response_text,
            "response_audio_url": response_audio_url,
            "autodeclaration_score": autodeclaration_score,
            "context_score": context_score,
            "bloom_level": bloom_level,
            "dreyfus_level": dreyfus_level,
            "evidences": json.dumps(evidences),
            "red_flags": json.dumps(red_flags),
            "consistency_penalty": consistency_penalty,
            "final_score": final_score,
            "justification": justification,
        })

    async def get_response_scores_for_session(self, session_id: str) -> list:
        """Return (competency, final_score) pairs for a session — used in WSI calculation."""
        result = await self.db.execute(text("""
            SELECT competency, final_score FROM wsi_response_analyses
            WHERE session_id = :session_id
        """), {"session_id": session_id})
        return result.fetchall()

    async def get_responses_for_session(self, session_id: str) -> list:
        """Return full response-analysis rows joined with question details."""
        result = await self.db.execute(text("""
            SELECT ra.competency, ra.response_text, ra.autodeclaration_score, ra.context_score,
                   ra.bloom_level, ra.dreyfus_level, ra.evidences, ra.red_flags,
                   ra.consistency_penalty, ra.final_score, ra.justification, ra.created_at,
                   q.question_text, q.framework, q.question_type, q.weight, q.expected_signals,
                   q.sequence_order
            FROM wsi_response_analyses ra
            JOIN wsi_questions q ON ra.question_id = q.id
            WHERE ra.session_id = :session_id
            ORDER BY q.sequence_order
        """), {"session_id": session_id})
        return result.fetchall()

    async def get_responses_for_session_summary(self, session_id: str) -> list:
        """Return lightweight (question_id, competency, final_score, justification) rows."""
        result = await self.db.execute(text("""
            SELECT question_id, competency, final_score, justification
            FROM wsi_response_analyses
            WHERE session_id = :session_id
        """), {"session_id": session_id})
        return result.fetchall()

    # ------------------------------------------------------------------
    # wsi_results
    # ------------------------------------------------------------------

    async def insert_result(
        self,
        result_id: str,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        technical_wsi: float,
        behavioral_wsi: float,
        overall_wsi: float,
        classification: str,
        percentile: int | None,
    ) -> None:
        """Persist final WSI scores."""
        # RLS-EXEMPT: wsi_results — transitive via session
        await self.db.execute(text("""
            INSERT INTO wsi_results (
                id, session_id, candidate_id, job_vacancy_id,
                technical_wsi, behavioral_wsi, overall_wsi, classification, percentile
            )
            VALUES (
                :id, :session_id, :candidate_id, :job_vacancy_id,
                :technical_wsi, :behavioral_wsi, :overall_wsi, :classification, :percentile
            )
        """), {
            "id": result_id,
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "technical_wsi": technical_wsi,
            "behavioral_wsi": behavioral_wsi,
            "overall_wsi": overall_wsi,
            "classification": classification,
            "percentile": percentile,
        })

    async def get_result_with_session(self, result_id: str) -> WsiResultRow | None:
        """Fetch result row joined with session for full detail view."""
        result = await self.db.execute(text("""
            SELECT r.id, r.session_id, r.candidate_id, r.job_vacancy_id,
                   r.technical_wsi, r.behavioral_wsi, r.overall_wsi,
                   r.classification, r.percentile, r.created_at,
                   s.screening_type, s.mode, s.started_at, s.completed_at
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            WHERE r.id = :result_id
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_results_for_candidate(self, candidate_id: str, limit: int = 10) -> list:
        """Return recent WSI results for a candidate (ordered by date desc)."""
        result = await self.db.execute(text("""
            SELECT r.id, r.job_vacancy_id, r.overall_wsi, r.technical_wsi, r.behavioral_wsi,
                   r.classification, r.percentile, r.created_at, s.screening_type
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            WHERE r.candidate_id = :candidate_id
            ORDER BY r.created_at DESC
            LIMIT :limit
        """), {"candidate_id": candidate_id, "limit": limit})
        return result.fetchall()

    async def get_vacancy_ranking(self, job_vacancy_id: str) -> list:
        """Return ranked candidates for a job vacancy."""
        result = await self.db.execute(text("""
            SELECT r.id as result_id, r.candidate_id, r.overall_wsi, r.technical_wsi, r.behavioral_wsi,
                   r.classification, r.percentile, r.created_at, s.screening_type,
                   c.name as candidate_name, c.current_title,
                   RANK() OVER (ORDER BY r.overall_wsi DESC) as rank_position,
                   COUNT(*) OVER () as total_candidates
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            JOIN candidates c ON r.candidate_id = c.id
            WHERE r.job_vacancy_id = :job_vacancy_id
              AND s.status = 'completed'
            ORDER BY r.overall_wsi DESC
        """), {"job_vacancy_id": job_vacancy_id})
        return result.fetchall()

    async def get_vacancy_averages(self, job_vacancy_id: str) -> WsiVacancyAveragesRow | None:
        """Return average WSI scores across all completed sessions for a vacancy."""
        result = await self.db.execute(text("""
            SELECT ROUND(AVG(r.overall_wsi)::numeric, 2),
                   ROUND(AVG(r.technical_wsi)::numeric, 2),
                   ROUND(AVG(r.behavioral_wsi)::numeric, 2)
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            WHERE r.job_vacancy_id = :job_vacancy_id AND s.status = 'completed'
        """), {"job_vacancy_id": job_vacancy_id})
        return result.fetchone()

    async def get_candidate_rank_in_vacancy(self, candidate_id: str, job_vacancy_id: str) -> WsiCandidateRankRow | None:
        """Return a single candidate's rank position within a vacancy."""
        result = await self.db.execute(text("""
            WITH ranked AS (
                SELECT r.candidate_id,
                       r.overall_wsi,
                       RANK() OVER (ORDER BY r.overall_wsi DESC) as rank_position,
                       COUNT(*) OVER () as total_candidates
                FROM wsi_results r
                JOIN wsi_sessions s ON r.session_id = s.id
                WHERE r.job_vacancy_id = :job_vacancy_id AND s.status = 'completed'
            )
            SELECT rank_position, total_candidates, overall_wsi
            FROM ranked WHERE candidate_id = :candidate_id
        """), {"candidate_id": candidate_id, "job_vacancy_id": job_vacancy_id})
        return result.fetchone()

    # ------------------------------------------------------------------
    # wsi_reports
    # ------------------------------------------------------------------

    async def get_report_for_result(self, result_id: str) -> WsiReportRow | None:
        """Fetch the structured report row for a WSI result."""
        result = await self.db.execute(text("""
            SELECT executive_summary, technical_analysis, behavioral_analysis,
                   cultural_fit, recommendation
            FROM wsi_reports WHERE wsi_result_id = :result_id
        """), {"result_id": result_id})
        return result.fetchone()

    # ------------------------------------------------------------------
    # wsi_feedbacks
    # ------------------------------------------------------------------

    async def get_feedback_for_result(self, result_id: str) -> WsiFeedbackRow | None:
        """Fetch the candidate feedback row for a WSI result."""
        result = await self.db.execute(text("""
            SELECT decision, main_message, technical_strengths, development_opportunities,
                   behavioral_strengths, next_steps, personalized_tip
            FROM wsi_feedbacks WHERE wsi_result_id = :result_id
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_result_summary(self, result_id: str):
        """Fetch (candidate_id, job_vacancy_id, overall_wsi, classification) for a result."""
        result = await self.db.execute(text("""
            SELECT candidate_id, job_vacancy_id, overall_wsi, classification
            FROM wsi_results
            WHERE id = :result_id
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_result_candidate_vacancy(self, result_id: str):
        """Fetch minimal (candidate_id, job_vacancy_id) for a result."""
        result = await self.db.execute(text("""
            SELECT candidate_id, job_vacancy_id FROM wsi_results WHERE id = :result_id
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_report_content(self, result_id: str):
        """Fetch report content (JSON) for development areas extraction."""
        result = await self.db.execute(text("""
            SELECT content FROM wsi_reports WHERE wsi_result_id = :result_id LIMIT 1
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_candidate_contact(self, candidate_id: str):
        """Fetch (name, email, phone) for a candidate."""
        result = await self.db.execute(text("""
            SELECT name, email, phone FROM candidates WHERE id = :candidate_id LIMIT 1
        """), {"candidate_id": candidate_id})
        return result.fetchone()

    async def get_vacancy_title(self, job_vacancy_id: str):
        """Fetch (title, company_name) for a vacancy."""
        result = await self.db.execute(text("""
            SELECT title, company_name FROM job_vacancies WHERE id = :job_vacancy_id LIMIT 1
        """), {"job_vacancy_id": job_vacancy_id})
        return result.fetchone()

    async def get_wsi_feedback_detail(self, result_id: str):
        """Fetch detailed feedback row for a result (for feedback-status endpoint)."""
        result = await self.db.execute(text("""
            SELECT id, decision, main_message, technical_strengths, development_opportunities,
                   behavioral_strengths, next_steps, personalized_tip
            FROM wsi_feedbacks WHERE wsi_result_id = :result_id LIMIT 1
        """), {"result_id": result_id})
        return result.fetchone()

    async def get_latest_scores_per_candidate(self, job_vacancy_id: str) -> list:
        """Return one result per candidate (latest) for a vacancy with WSI scores."""
        result = await self.db.execute(text("""
            SELECT DISTINCT ON (candidate_id)
                candidate_id, overall_wsi, technical_wsi, behavioral_wsi,
                classification, percentile
            FROM wsi_results
            WHERE job_vacancy_id = :job_vacancy_id
            ORDER BY candidate_id, created_at DESC
        """), {"job_vacancy_id": job_vacancy_id})
        return result.fetchall()


    # ------------------------------------------------------------------
    # Phase-2 additions
    # ------------------------------------------------------------------

    async def get_question_text_and_competency(self, question_id: str) -> WsiQuestionTextRow | None:
        """Fetch (question_text, competency) for a question — used in analyze-response."""
        result = await self.db.execute(text("""
            SELECT question_text, competency FROM wsi_questions WHERE id = :question_id
        """), {"question_id": question_id})
        return result.fetchone()

    async def insert_response_analysis_simple(
        self,
        analysis_id: str,
        session_id: str,
        question_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        competency: str,
        response_text: str,
        bloom_level: int,
        dreyfus_level: int,
        evidences: list,
        red_flags: list,
        final_score: float,
        justification: str,
    ) -> None:
        """Persist a simplified response-analysis record (ON CONFLICT DO NOTHING)."""
        # RLS-EXEMPT: wsi_response_analyses — transitive via session
        await self.db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, bloom_level, dreyfus_level,
                evidences, red_flags, final_score, justification
            )
            VALUES (:id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                    :competency, :response_text, :bloom_level, :dreyfus_level,
                    :evidences::jsonb, :red_flags::jsonb, :final_score, :justification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": analysis_id,
            "session_id": session_id,
            "question_id": question_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "competency": competency,
            "response_text": response_text,
            "bloom_level": bloom_level,
            "dreyfus_level": dreyfus_level,
            "evidences": json.dumps(evidences),
            "red_flags": json.dumps(red_flags),
            "final_score": final_score,
            "justification": justification,
        })

    async def upsert_result(
        self,
        result_id: str,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        technical_wsi: float,
        behavioral_wsi: float,
        overall_wsi: float,
        classification: str,
    ) -> None:
        """Insert WSI result, silently skip if id already exists (ON CONFLICT DO NOTHING)."""
        # RLS-EXEMPT: wsi_results — transitive via session
        await self.db.execute(text("""
            INSERT INTO wsi_results (
                id, session_id, candidate_id, job_vacancy_id,
                technical_wsi, behavioral_wsi, overall_wsi, classification
            )
            VALUES (:id, :session_id, :candidate_id, :job_vacancy_id,
                    :technical_wsi, :behavioral_wsi, :overall_wsi, :classification)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": result_id,
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "technical_wsi": technical_wsi,
            "behavioral_wsi": behavioral_wsi,
            "overall_wsi": overall_wsi,
            "classification": classification,
        })

    async def upsert_question(
        self,
        question_id: str,
        session_id: str,
        competency: str,
        framework: str,
        question_type: str,
        question_text: str,
        weight: float,
        expected_signals: list,
        scoring_criteria: dict,
        sequence_order: int,
    ) -> None:
        """Insert or ignore a WSI question record (ON CONFLICT DO NOTHING)."""
        # RLS-EXEMPT: wsi_questions — transitive via wsi_sessions.job_vacancy_id
        await self.db.execute(text("""
            INSERT INTO wsi_questions (
                id, session_id, competency, framework, question_type,
                question_text, weight, expected_signals, scoring_criteria, sequence_order
            )
            VALUES (:id, :session_id, :competency, :framework, :question_type,
                    :question_text, :weight, :expected_signals::jsonb, :scoring_criteria::jsonb, :sequence_order)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": question_id,
            "session_id": session_id,
            "competency": competency,
            "framework": framework,
            "question_type": question_type,
            "question_text": question_text,
            "weight": weight,
            "expected_signals": json.dumps(expected_signals),
            "scoring_criteria": json.dumps(scoring_criteria),
            "sequence_order": sequence_order,
        })

    async def get_job_vacancy_context(self, job_id: str, company_id: str) -> WsiJobVacancyContextRow | None:
        """Fetch (title, description, seniority_level) for a job vacancy."""
        result = await self.db.execute(text("""
            SELECT title, description, seniority_level
            FROM job_vacancies WHERE id = :job_id AND company_id = :company_id
            LIMIT 1
        """), {"job_id": job_id, "company_id": company_id})
        return result.fetchone()

    async def upsert_job_screening_question(
        self,
        question_id: str,
        job_id: str,
        question_text: str,
        category: str,
        question_type: str,
        weight: float,
        skill_targeted: str,
        block_id,
        source: str,
    ) -> None:
        """Insert or update a job_screening_questions record."""
        # RLS-EXEMPT: job_screening_questions — transitive via job_vacancies
        await self.db.execute(text("""
            INSERT INTO job_screening_questions (
                id, job_vacancy_id, question_text, category, question_type,
                weight, skill_targeted, block_id, source, is_active
            )
            VALUES (:id, :job_id, :text, :category, :type, :weight, :skill_targeted, :block_id, :source, true)
            ON CONFLICT (id) DO UPDATE SET
                question_text = EXCLUDED.question_text,
                category = EXCLUDED.category,
                question_type = EXCLUDED.question_type,
                weight = EXCLUDED.weight,
                skill_targeted = EXCLUDED.skill_targeted,
                block_id = EXCLUDED.block_id,
                updated_at = NOW()
        """), {
            "id": question_id,
            "job_id": job_id,
            "text": question_text,
            "category": category,
            "type": question_type,
            "weight": weight,
            "skill_targeted": skill_targeted,
            "block_id": block_id,
            "source": source,
        })

    # ------------------------------------------------------------------
    # Voice call — session/call_id binding (twilio_voice.py Phase 2)
    # ------------------------------------------------------------------

    async def get_session_id_by_call_sid(self, call_sid: str) -> str | None:
        """Look up a wsi_session id by its associated Twilio call_id. Returns None if not found."""
        result = await self.db.execute(
            text("SELECT id FROM wsi_sessions WHERE call_id = :call_sid LIMIT 1"),
            {"call_sid": call_sid},
        )
        row = result.fetchone()
        return row[0] if row else None

    async def bind_call_sid_to_session(self, session_id: str, call_sid: str) -> None:
        """Update wsi_session.call_id to bind a Twilio call SID to a screening session."""
        await self.db.execute(
            text(
                "UPDATE wsi_sessions SET call_id = :call_id, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = :session_id"
            ),
            {"call_id": call_sid, "session_id": session_id},
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # Cross-domain helpers (added Sprint Q2 ADR-001 cleanup)
    # ------------------------------------------------------------------

    async def get_latest_completed_session_version(
        self, candidate_id: str, job_vacancy_id: str,
    ) -> int | None:
        """Latest completed `question_set_version` for (candidate, job).

        Used by candidates/services/candidate_comparison_service.py to
        normalize scores across question-set versions when comparing
        candidates for the same job. Returns None if no completed session.
        """
        result = await self.db.execute(
            text(
                "SELECT question_set_version FROM wsi_sessions "
                "WHERE job_vacancy_id = :job_id "
                "  AND candidate_id = :candidate_id "
                "  AND status = 'completed' "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"job_id": job_vacancy_id, "candidate_id": candidate_id},
        )
        row = result.fetchone()
        return row[0] if row and row[0] is not None else None

    # ------------------------------------------------------------------
    # Cross-version analytics (Sprint 6 ADR-001 — used by
    # cv_screening/services/screening_question_set_service.py and
    # cv_screening/services/score_normalization_service.py)
    # ------------------------------------------------------------------

    async def count_completed_sessions(self, job_vacancy_id: str) -> int:
        """Total completed wsi_sessions for a job."""
        result = await self.db.execute(
            text(
                "SELECT COUNT(*) FROM wsi_sessions "
                "WHERE job_vacancy_id = :job_vacancy_id AND status = 'completed'"
            ),
            {"job_vacancy_id": job_vacancy_id},
        )
        row = result.fetchone()
        return int(row[0]) if row else 0

    async def count_completed_sessions_at_version(
        self, job_vacancy_id: str, version: int,
    ) -> int:
        """Completed sessions for a job at a specific question_set_version."""
        result = await self.db.execute(
            text(
                "SELECT COUNT(*) FROM wsi_sessions "
                "WHERE job_vacancy_id = :job_vacancy_id "
                "  AND status = 'completed' "
                "  AND question_set_version = :version"
            ),
            {"job_vacancy_id": job_vacancy_id, "version": version},
        )
        row = result.fetchone()
        return int(row[0]) if row else 0

    async def get_older_versions_session_counts(
        self, job_vacancy_id: str, current_version: int,
    ) -> list[tuple[int, int]]:
        """List of (version, count) for completed sessions on versions < current."""
        result = await self.db.execute(
            text(
                "SELECT question_set_version, COUNT(*) "
                "FROM wsi_sessions "
                "WHERE job_vacancy_id = :job_vacancy_id "
                "  AND status = 'completed' "
                "  AND question_set_version IS NOT NULL "
                "  AND question_set_version < :current_version "
                "GROUP BY question_set_version "
                "ORDER BY question_set_version DESC"
            ),
            {"job_vacancy_id": job_vacancy_id, "current_version": current_version},
        )
        return [(int(row[0]), int(row[1])) for row in result.fetchall()]

    async def get_completed_sessions_count_by_version(
        self, job_vacancy_id: str,
    ) -> dict[int | None, int]:
        """{version → count} of completed sessions for a job (all versions)."""
        result = await self.db.execute(
            text(
                "SELECT question_set_version, COUNT(*) "
                "FROM wsi_sessions "
                "WHERE job_vacancy_id = :job_vacancy_id AND status = 'completed' "
                "GROUP BY question_set_version"
            ),
            {"job_vacancy_id": job_vacancy_id},
        )
        return {row[0]: int(row[1]) for row in result.fetchall()}

    # ------------------------------------------------------------------
    # Triagem completion persistence (Sprint 6 ADR-001 — used by
    # recruitment/services/triagem_session_service/completion.py)
    # ------------------------------------------------------------------

    async def insert_session_with_completed_at(
        self,
        *,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        screening_type: str,
        mode: str,
        status: str,
        question_set_version: int | None,
        question_set_id: str | None,
        completed_at,
    ) -> None:
        """Insert wsi_sessions row including `completed_at` (triagem chat path).

        Distinct from `upsert_session` because this caller already has a
        `completed_at` timestamp and inserts a session in a single shot
        (not the multi-step lifecycle from voice/twilio).
        """
        await self.db.execute(
            # RLS-EXEMPT: wsi_sessions — transitive isolation via job_vacancy_id join (migration 118 design decision)
            text(
                "INSERT INTO wsi_sessions "
                "    (id, candidate_id, job_vacancy_id, screening_type, mode, status, "
                "     question_set_version, question_set_id, completed_at) "
                "VALUES "
                "    (:id, :candidate_id, :job_vacancy_id, :screening_type, :mode, :status, "
                "     :question_set_version, :question_set_id, :completed_at)"
            ),
            {
                "id": session_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "screening_type": screening_type,
                "mode": mode,
                "status": status,
                "question_set_version": question_set_version,
                "question_set_id": question_set_id,
                "completed_at": completed_at,
            },
        )

    async def insert_question_full(
        self,
        *,
        question_id: str,
        session_id: str,
        competency: str,
        framework: str,
        question_type: str,
        question_text: str,
        weight: float,
        sequence_order: int,
    ) -> None:
        """Insert wsi_questions row (triagem chat path — `weight` + `sequence_order`)."""
        await self.db.execute(
            # RLS-EXEMPT: wsi_questions — transitive via wsi_sessions.job_vacancy_id
            text(
                "INSERT INTO wsi_questions "
                "    (id, session_id, competency, framework, question_type, question_text, "
                "     weight, sequence_order) "
                "VALUES "
                "    (:id, :session_id, :competency, :framework, :question_type, :question_text, "
                "     :weight, :sequence_order)"
            ),
            {
                "id": question_id,
                "session_id": session_id,
                "competency": competency,
                "framework": framework,
                "question_type": question_type,
                "question_text": question_text,
                "weight": weight,
                "sequence_order": sequence_order,
            },
        )

    async def insert_response_analysis_full(
        self,
        *,
        analysis_id: str,
        session_id: str,
        question_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        competency: str,
        response_text: str,
        autodeclaration_score: float,
        context_score: float,
        bloom_level: int,
        dreyfus_level: int,
        evidences_json: str,
        red_flags_json: str,
        consistency_penalty: float,
        final_score: float,
        justification: str,
        response_hash: str | None = None,
    ) -> None:
        """Insert wsi_response_analyses row with full analysis fields.

        candidate_id, job_vacancy_id e response_hash sao NOT NULL no schema.
        Antes eram OMITIDOS -> o insert falhava silenciosamente em producao
        (candidato real ficava sem respostas por-competencia no modal de
        triagem). response_hash e derivado de response_text (md5) quando nao
        informado. Casts jsonb usam CAST(...) (evita o bug :param::cast).
        """
        if not response_hash:
            response_hash = hashlib.md5(
                (response_text or "").encode("utf-8")
            ).hexdigest()
        await self.db.execute(
            # RLS-EXEMPT: wsi_response_analyses — transitive via session
            text(
                "INSERT INTO wsi_response_analyses "
                "    (id, session_id, question_id, candidate_id, job_vacancy_id, "
                "     competency, response_text, "
                "     autodeclaration_score, context_score, bloom_level, dreyfus_level, "
                "     evidences, red_flags, consistency_penalty, final_score, "
                "     justification, response_hash) "
                "VALUES "
                "    (:id, :session_id, :question_id, :candidate_id, :job_vacancy_id, "
                "     :competency, :response_text, "
                "     :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level, "
                "     CAST(:evidences AS jsonb), CAST(:red_flags AS jsonb), "
                "     :consistency_penalty, :final_score, :justification, :response_hash)"
            ),
            {
                "id": analysis_id,
                "session_id": session_id,
                "question_id": question_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "competency": competency,
                "response_text": response_text,
                "autodeclaration_score": autodeclaration_score,
                "context_score": context_score,
                "bloom_level": bloom_level,
                "dreyfus_level": dreyfus_level,
                "evidences": evidences_json,
                "red_flags": red_flags_json,
                "consistency_penalty": consistency_penalty,
                "final_score": final_score,
                "justification": justification,
                "response_hash": response_hash,
            },
        )

    async def insert_result_full(
        self,
        *,
        result_id: str,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        technical_wsi: float,
        behavioral_wsi: float,
        overall_wsi: float,
        classification: str,
        percentile: float | None,
    ) -> None:
        """Insert wsi_results row with all 5 score dimensions."""
        await self.db.execute(
            # RLS-EXEMPT: wsi_results — transitive via session
            text(
                "INSERT INTO wsi_results "
                "    (id, session_id, candidate_id, job_vacancy_id, "
                "     technical_wsi, behavioral_wsi, overall_wsi, classification, percentile) "
                "VALUES "
                "    (:id, :session_id, :candidate_id, :job_vacancy_id, "
                "     :technical_wsi, :behavioral_wsi, :overall_wsi, :classification, :percentile)"
            ),
            {
                "id": result_id,
                "session_id": session_id,
                "candidate_id": candidate_id,
                "job_vacancy_id": job_vacancy_id,
                "technical_wsi": technical_wsi,
                "behavioral_wsi": behavioral_wsi,
                "overall_wsi": overall_wsi,
                "classification": classification,
                "percentile": percentile,
            },
        )

    # ------------------------------------------------------------------
    # Voice screening canonical (F-13 ADR-001, audit 2026-05-22)
    # Replaces inline SQL in voice_screening_orchestrator.py
    # ------------------------------------------------------------------

    async def update_voice_session_state(
        self,
        session_id: str,
        state_json: str,
    ) -> None:
        """F-13: Persist voice session state on wsi_sessions row.

        Caller manages transaction (commit/rollback). The orchestrator
        runs this inside a per-call best-effort try/except.
        """
        await self.db.execute(text("""
            UPDATE wsi_sessions
            SET voice_session_state = CAST(:state AS jsonb),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :session_id
        """), {"state": state_json, "session_id": session_id})

    async def get_voice_session_state(self, session_id: str):
        """F-13: Read voice_session_state column for a session.

        Returns the raw JSONB value (dict when SQLAlchemy decodes) or
        None when no row / column is null.
        """
        result = await self.db.execute(text("""
            SELECT voice_session_state
            FROM wsi_sessions
            WHERE id = :session_id
              AND voice_session_state IS NOT NULL
        """), {"session_id": session_id})
        row = result.fetchone()
        if not row:
            return None
        return row[0]

    async def list_question_texts_for_session(self, session_id: str) -> list[str]:
        """F-13: Return only question_text strings ordered by sequence_order.

        Lighter than get_questions_for_session (which returns 7 cols);
        voice orchestrator only needs the texts to feed the LLM.
        """
        result = await self.db.execute(text("""
            SELECT question_text
            FROM wsi_questions
            WHERE session_id = :session_id
            ORDER BY sequence_order
        """), {"session_id": session_id})
        return [row[0] for row in result.fetchall() if row[0]]

    async def upsert_voice_session(
        self,
        *,
        session_id: str,
        candidate_id: str,
        job_vacancy_id: str,
        mode: str,
        call_id: str | None,
        status: str,
    ) -> None:
        """F-13: Compact insert/update of wsi_sessions row used by voice path.

        Distinct from upsert_session (no question_set_*, no screening_type)
        because voice flow registers a row with minimal fields; the call_id
        + status are mutable.
        """
        # RLS-EXEMPT: wsi_sessions — transitive isolation via job_vacancy_id join (migration 118 design decision)
        await self.db.execute(text("""
            INSERT INTO wsi_sessions (
                id, candidate_id, job_vacancy_id, mode, call_id, status,
                created_at, updated_at
            )
            VALUES (
                :id, :candidate_id, :job_vacancy_id, :mode, :call_id, :status,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (id) DO UPDATE
                SET call_id = :call_id,
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
        """), {
            "id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "mode": mode,
            "call_id": call_id,
            "status": status,
        })

    async def insert_voice_question(
        self,
        *,
        question_id: str,
        session_id: str,
        competency: str,
        framework: str,
        question_type: str,
        question_text: str,
        weight: float,
        sequence_order: int,
    ) -> None:
        """F-13: Insert a single voice-generated WSI question.

        Distinct from insert_question (no expected_signals/scoring_criteria)
        because voice path stores plain question texts without analytic
        metadata at insert time — analytics are appended later by
        wsi_orchestrator hooks.
        """
        # RLS-EXEMPT: wsi_questions — transitive via wsi_sessions.job_vacancy_id
        await self.db.execute(text("""
            INSERT INTO wsi_questions (
                id, session_id, competency, framework, question_type,
                question_text, weight, sequence_order
            )
            VALUES (
                :id, :session_id, :competency, :framework, :question_type,
                :question_text, :weight, :sequence_order
            )
            ON CONFLICT DO NOTHING
        """), {
            "id": question_id,
            "session_id": session_id,
            "competency": competency,
            "framework": framework,
            "question_type": question_type,
            "question_text": question_text,
            "weight": weight,
            "sequence_order": sequence_order,
        })

