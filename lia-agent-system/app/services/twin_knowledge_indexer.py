"""
TwinKnowledgeIndexer — builds the knowledge corpus of a Digital Twin.

Sources:
  1. ATS history: past hiring decisions with reasoning (approved/rejected + why)
  2. Audio transcription: recorded interviews with the SME explaining decisions
  3. Manual: recruiter manually enters decision + reasoning

Each decision is embedded (768d) and stored in twin_decisions for K-NN retrieval.

Apply to: lia-agent-system/app/services/twin_knowledge_indexer.py

Wave C1.1 (2026-05-27): raw `select(DigitalTwin)` for stats refresh migrated to
`DigitalTwinRepository.update_decision_count` (ADR-001 canonical). All `index_*`
methods now require `company_id` (multi-tenancy fail-closed via repo guard).
"""

import json
import logging
import uuid
from typing import Optional

# Module-level imports for canonical model + raw ATS query that operates on
# Rails-owned tables (applies/candidates/jobs) — see ADR-001-EXEMPT in
# index_from_ats_history.
from sqlalchemy import text as sql_text

from lia_models.digital_twin import TwinDecision

logger = logging.getLogger(__name__)


class TwinKnowledgeIndexer:

    async def index_from_ats_history(
        self,
        twin_id: str,
        company_id: str,
        months_back: int = 12,
        evaluator_email: Optional[str] = None,
        db=None,
    ) -> int:
        """
        Index past decisions from vacancy_candidates into the twin's corpus.

        2026-06-01 (audit): swapped from the non-existent `applies` table to the
        live `vacancy_candidates` (the table recruiters actually write to). When
        `evaluator_email` is given, scopes to that person's decisions (added_by =
        email; human_reviewer_id is 0% populated here). `notes` is empty, so the
        reasoning text is SYNTHESIZED from status + candidate profile.

        Multi-tenancy: company_id comes from the caller (JWT), never the payload.
        Returns number of decisions indexed.
        """
        sql = self._ats_decision_sql(bool(evaluator_email))
        params = {"company_id": company_id, "months": months_back, "limit": 2000}
        if evaluator_email:
            params["evaluator_email"] = evaluator_email
        # ADR-001-EXEMPT: cross-table analytics read (vacancy_candidates + candidates
        # + job_vacancies); canonical repos do not cover this twin-corpus join.
        try:
            result = await db.execute(sql_text(sql), params)
            rows = result.fetchall()
        except Exception as e:
            logger.warning("[TwinIndexer] vacancy_candidates query failed: %s", e)
            rows = []

        from app.domains.agent_studio.repositories.digital_twin_repository import (
            DigitalTwinRepository,
        )
        repo = DigitalTwinRepository(db)

        indexed = 0
        for row in rows:
            decision = self._map_status(row.status)
            if not decision:
                continue

            snapshot, reasoning = self._synthesize_decision(row, decision)
            text_for_embedding = (
                f"Decis\u00e3o: {decision}\n"
                f"Cargo: {row.job_title}\n"
                f"Perfil: {json.dumps(snapshot, ensure_ascii=False)}\n"
                f"Racioc\u00ednio: {reasoning}"
            )
            embedding = await self._embed(text_for_embedding)

            td = TwinDecision(
                id=uuid.uuid4(),
                twin_id=twin_id,
                decision=decision,
                reasoning=reasoning,
                candidate_snapshot=snapshot,
                job_snapshot={"title": row.job_title},
                embedding=embedding,
                source="ats_history",
            )
            await repo.add_decision(decision=td, company_id=company_id)
            indexed += 1

        if indexed > 0:
            await db.commit()
            await repo.update_decision_count(twin_id=twin_id, company_id=company_id)
            await db.commit()

        logger.info("[TwinIndexer] twin=%s indexed %d decisions from vacancy_candidates", twin_id, indexed)
        return indexed

    @staticmethod
    def _ats_decision_sql(filter_evaluator: bool) -> str:
        """Shared decision query over vacancy_candidates (the live ATS table).

        `notes` is empty in this DB so no rationale column is selected (reasoning is
        synthesized downstream). `added_by` holds the evaluator EMAIL.
        """
        evaluator_clause = "AND vc.added_by = :evaluator_email" if filter_evaluator else ""
        return f"""
            SELECT
                vc.candidate_id,
                vc.status,
                vc.added_by,
                vc.lia_score,
                vc.match_percentage,
                vc.created_at,
                c.current_title,
                c.technical_skills,
                c.years_of_experience,
                j.title AS job_title
            FROM vacancy_candidates vc
            JOIN candidates c ON c.id = vc.candidate_id
            LEFT JOIN job_vacancies j ON j.id = vc.vacancy_id
            WHERE vc.company_id = :company_id
              AND vc.status IN ('approved','hired','offer','rejected','not_selected')
              AND vc.created_at >= NOW() - make_interval(months => :months)
              {evaluator_clause}
            ORDER BY vc.created_at DESC
            LIMIT :limit
        """

    @staticmethod
    def _synthesize_decision(row, decision: str):
        """PII-safe candidate snapshot + synthesized reasoning (notes is empty).

        LGPD: no direct PII (no name) in the embedded corpus; candidate_id kept as a
        reference for JIT lookup (erasure-cascade safe).
        """
        skills = list(row.technical_skills or [])
        snapshot = {
            "candidate_id": str(row.candidate_id),
            "current_title": row.current_title,
            "technical_skills": skills,
            "years_of_experience": row.years_of_experience,
        }
        decision_pt = "aprovou" if decision == "approved" else "rejeitou"
        parts = [
            f"{decision_pt} para {row.job_title or 'a vaga'}",
            f"perfil: {row.current_title or 'n/d'}",
            f"{row.years_of_experience} anos" if row.years_of_experience is not None else None,
            f"skills: {', '.join(skills[:6])}" if skills else None,
            f"score IA {row.lia_score}" if row.lia_score is not None else None,
            f"match {row.match_percentage}%" if row.match_percentage is not None else None,
        ]
        reasoning = " \u2014 ".join([p for p in parts if p])
        return snapshot, reasoning

    async def scan_ats_history_preview(
        self,
        company_id: str,
        evaluator_email: Optional[str],
        months_back: int = 12,
        sample_size: int = 5,
        db=None,
    ) -> dict:
        """Read-only dry run: count + sample an evaluator's decisions WITHOUT
        embedding or persisting. Powers the create-modal preview (B2).
        """
        sql = self._ats_decision_sql(bool(evaluator_email))
        params = {"company_id": company_id, "months": months_back, "limit": 2000}
        if evaluator_email:
            params["evaluator_email"] = evaluator_email
        # ADR-001-EXEMPT: read-only analytics join (see _ats_decision_sql).
        try:
            rows = (await db.execute(sql_text(sql), params)).fetchall()
        except Exception as e:
            logger.warning("[TwinIndexer] scan-preview query failed: %s", e)
            rows = []

        approved = rejected = 0
        samples: list[dict] = []
        for row in rows:
            decision = self._map_status(row.status)
            if not decision:
                continue
            if decision == "approved":
                approved += 1
            else:
                rejected += 1
            if len(samples) < sample_size:
                _snapshot, reasoning = self._synthesize_decision(row, decision)
                samples.append({
                    "decision": decision,
                    "role": row.current_title or row.job_title,
                    "skills": list(row.technical_skills or [])[:5],
                    "summary": reasoning,
                })
        total = approved + rejected
        return {
            "decisions_found": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "sample_decisions": samples,
            "has_enough": total >= 5,
        }

    async def index_from_audio(
        self,
        twin_id: str,
        company_id: str,
        audio_bytes: bytes,
        audio_format: str = "audio/mp4",
        language: str = "pt-BR",
        db=None,
    ) -> dict:
        """
        Transcribe an interview recording with the SME and extract decisions.

        The SME explains their decision-making process about past candidates.
        LLM extracts individual decisions from the transcript.
        """
        # 1. Transcribe
        transcription = await self._transcribe(audio_bytes, audio_format, language)
        if not transcription:
            return {"status": "error", "message": "Transcrição falhou"}

        # 2. Extract decisions from transcript via LLM
        decisions = await self._extract_decisions_from_transcript(transcription, company_id=company_id)

        # 3. Index each decision via canonical repo (tenant validation)
        from app.domains.agent_studio.repositories.digital_twin_repository import (
            DigitalTwinRepository,
        )
        repo = DigitalTwinRepository(db)

        indexed = 0
        for d in decisions:
            text_for_embedding = f"Decisão: {d['decision']}\nRaciocínio: {d['reasoning']}"
            embedding = await self._embed(text_for_embedding)

            td = TwinDecision(
                id=uuid.uuid4(),
                twin_id=twin_id,
                decision=d["decision"],
                reasoning=d["reasoning"],
                candidate_snapshot=d.get("candidate_context"),
                embedding=embedding,
                source="audio",
            )
            await repo.add_decision(decision=td, company_id=company_id)
            indexed += 1

        if indexed > 0:
            await db.commit()
            await repo.update_decision_count(
                twin_id=twin_id, company_id=company_id
            )
            await db.commit()

        return {"status": "ok", "indexed": indexed, "transcript_length": len(transcription)}

    async def index_manual_decision(
        self,
        twin_id: str,
        company_id: str,
        decision: str,
        reasoning: str,
        candidate_snapshot: Optional[dict] = None,
        job_snapshot: Optional[dict] = None,
        db=None,
    ) -> dict:
        """Index a single manually entered decision."""
        from app.domains.agent_studio.repositories.digital_twin_repository import (
            DigitalTwinRepository,
        )
        repo = DigitalTwinRepository(db)

        text_for_embedding = (
            f"Decisão: {decision}\n"
            f"Perfil: {json.dumps(candidate_snapshot or {}, ensure_ascii=False)}\n"
            f"Raciocínio: {reasoning}"
        )
        embedding = await self._embed(text_for_embedding)

        td = TwinDecision(
            id=uuid.uuid4(),
            twin_id=twin_id,
            decision=decision,
            reasoning=reasoning,
            candidate_snapshot=candidate_snapshot,
            job_snapshot=job_snapshot,
            embedding=embedding,
            source="manual",
        )
        await repo.add_decision(decision=td, company_id=company_id)
        await db.commit()
        await repo.update_decision_count(twin_id=twin_id, company_id=company_id)
        await db.commit()

        return {"status": "ok", "decision_id": str(td.id)}

    # ---------- Helpers ----------

    async def _embed(self, text: str) -> Optional[list[float]]:
        """Generate 768d embedding. Reuses existing embedding infrastructure."""
        try:
            from app.domains.sourcing.services.pgv_analyzer import get_text_embedding
            return await get_text_embedding(text)
        except Exception as e:
            logger.warning("[TwinIndexer] Embedding failed: %s", e)
            return None

    async def _transcribe(self, audio_bytes: bytes, audio_format: str, language: str) -> str:
        """Transcribe audio using available STT service."""
        try:
            from app.shared.services.gemini_voice_service import GeminiVoiceService
            svc = GeminiVoiceService()
            result = await svc.transcribe_audio(audio_bytes, audio_format, language)
            return result.text
        except Exception:
            pass

        try:
            import whisper
            import tempfile
            import os
            model = whisper.load_model("base")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                f.flush()
                result = model.transcribe(f.name, language=language[:2])
                os.unlink(f.name)
                return result.get("text", "")
        except Exception:
            pass

        return ""

    async def _extract_decisions_from_transcript(
        self, transcript: str, company_id: str | None = None,
    ) -> list[dict]:
        """Extract individual decisions from a transcript via LLM."""
        try:
            # Canonical LLM factory (multi-tenant aware). Replaces broken
            # get_llm import — twin audio indexing was 100% in fallback
            # (returned []) until 2026-05-27.
            from app.shared.providers.llm_factory import create_tracked_llm
            llm = create_tracked_llm(
                temperature=0.3,
                service_name="TwinKnowledgeIndexer",
                operation="extract_decisions",
                max_output_tokens=1024,
                tenant_id=company_id,
            )
            prompt = (
                "A seguir é a transcrição de uma entrevista onde um especialista de RH "
                "explica suas decisões sobre candidatos. Extraia cada decisão como JSON:\n\n"
                f"Transcrição: {transcript[:3000]}\n\n"
                "Retorne um array JSON:\n"
                '[{"decision": "approved|rejected|maybe", '
                '"reasoning": "explicação do especialista", '
                '"candidate_context": {"name": "nome mencionado", "role": "cargo"}}]\n'
                "Responda APENAS com o JSON."
            )
            resp = await llm.ainvoke(prompt)
            return json.loads(resp.content)
        except Exception as e:
            logger.warning("[TwinIndexer] Decision extraction failed: %s", e)
            return []

    @staticmethod
    def _map_status(status: str) -> Optional[str]:
        APPROVED = {"hired", "offer_accepted", "passed_interview", "shortlisted", "approved", "offer"}
        REJECTED = {"rejected", "disqualified", "failed_screening", "declined", "not_selected"}
        if status in APPROVED:
            return "approved"
        if status in REJECTED:
            return "rejected"
        return None


twin_knowledge_indexer = TwinKnowledgeIndexer()
