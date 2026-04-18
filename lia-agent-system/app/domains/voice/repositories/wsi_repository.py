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
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.security.wsi_hashing import hash_response


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

    async def get_session(self, session_id: str) -> Any:
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
        response_hash: str | None = None,
    ) -> None:
        """Persist a response analysis record.

        Task #511 round 3: `response_hash` é obrigatório (NOT NULL na coluna
        após migration 091). Se o caller não fornecer, calculamos aqui via
        `hash_response` para garantir consistência — a coluna nunca pode
        receber NULL após a migration.
        """
        if not response_hash:
            response_hash = hash_response(response_text, session_id, question_id)
        # Audit trail paralelo (wsi_responses) — mesmo hash, FAIL-FAST.
        await self.db.execute(text("""
            INSERT INTO wsi_responses (
                session_id, question_id, raw_text, response_hash,
                candidate_id
            )
            VALUES (:session_id, :question_id, :raw_text, :response_hash,
                    :candidate_id)
        """), {
            "session_id": session_id,
            "question_id": question_id,
            "raw_text": response_text or "",
            "response_hash": response_hash,
            "candidate_id": candidate_id,
        })
        await self.db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, response_audio_url,
                autodeclaration_score, context_score, bloom_level, dreyfus_level,
                evidences, red_flags, consistency_penalty, final_score, justification,
                response_hash
            )
            VALUES (
                :id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                :competency, :response_text, :response_audio_url,
                :autodeclaration_score, :context_score, :bloom_level, :dreyfus_level,
                :evidences::jsonb, :red_flags::jsonb, :consistency_penalty, :final_score, :justification,
                :response_hash
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
            "response_hash": response_hash,
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

    async def get_result_with_session(self, result_id: str) -> Any:
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

    async def get_vacancy_averages(self, job_vacancy_id: str) -> Any:
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

    async def get_candidate_rank_in_vacancy(self, candidate_id: str, job_vacancy_id: str) -> Any:
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

    async def get_report_for_result(self, result_id: str) -> Any:
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

    async def get_feedback_for_result(self, result_id: str) -> Any:
        """Fetch the candidate feedback row for a WSI result."""
        result = await self.db.execute(text("""
            SELECT decision, main_message, technical_strengths, development_opportunities,
                   behavioral_strengths, next_steps, personalized_tip, development_plan,
                   recommended_resources
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

    async def get_question_text_and_competency(self, question_id: str) -> Any:
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
        response_hash: str | None = None,
    ) -> None:
        """Persist a simplified response-analysis record (ON CONFLICT DO NOTHING).

        Task #511 round 3: `response_hash` obrigatório na coluna após
        migration 091. Calculado se não fornecido para garantir
        compatibilidade com callers legados (eval pipeline).
        """
        if not response_hash:
            response_hash = hash_response(response_text, session_id, question_id)
        await self.db.execute(text("""
            INSERT INTO wsi_response_analyses (
                id, session_id, question_id, candidate_id, job_vacancy_id,
                competency, response_text, bloom_level, dreyfus_level,
                evidences, red_flags, final_score, justification,
                response_hash
            )
            VALUES (:id, :session_id, :question_id, :candidate_id, :job_vacancy_id,
                    :competency, :response_text, :bloom_level, :dreyfus_level,
                    :evidences::jsonb, :red_flags::jsonb, :final_score, :justification,
                    :response_hash)
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
            "response_hash": response_hash,
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

    async def get_job_vacancy_context(self, job_id: str, company_id: str) -> Any:
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

    async def get_job_screening_questions(self, job_id: str) -> list[dict]:
        """Return active job_screening_questions rows for *job_id*, ordered by id.

        Used as a fallback read path when no active screening_question_sets record
        exists for the job.
        """
        result = await self.db.execute(text("""
            SELECT id, question_text, category, question_type, weight, skill_targeted, block_id
            FROM job_screening_questions
            WHERE job_vacancy_id = :job_id
              AND is_active = TRUE
            ORDER BY id
        """), {"job_id": job_id})
        rows = result.fetchall()
        return [
            {
                "id": r[0],
                "text": r[1],
                "category": r[2],
                "type": r[3],
                "weight": r[4],
                "skill_targeted": r[5],
                "block_id": r[6],
            }
            for r in rows
        ]

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
