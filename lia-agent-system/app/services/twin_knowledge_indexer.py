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
        db=None,
    ) -> int:
        """
        Index past hiring decisions from the ATS into the twin's corpus.

        Searches for candidates with reviewer_notes/feedback in the ATS,
        maps their status to approved/rejected, and generates embeddings.

        Returns number of decisions indexed.
        """
        # ADR-001-EXEMPT: cross-domain Rails-owned tables (applies, candidates,
        # jobs) — schema not modeled in lia_models; canonical CandidateRepository
        # does not cover this analytics-style join. Sprint backlog: lift to
        # ATSAnalyticsRepository when the cross-domain repo lands.
        query = sql_text("""
            SELECT
                a.candidate_id,
                a.status,
                a.reviewer_notes,
                c.name,
                c.role_name,
                c.technical_skills,
                c.years_of_experience,
                j.title as job_title
            FROM applies a
            JOIN candidates c ON c.id = a.candidate_id
            JOIN jobs j ON j.id = a.job_id
            WHERE a.company_id = :company_id
              AND a.reviewer_notes IS NOT NULL
              AND a.reviewer_notes != ''
              AND a.created_at >= NOW() - make_interval(months => :months)
            LIMIT 2000
        """)

        try:
            result = await db.execute(query, {
                "company_id": company_id,
                "months": months_back,
            })
            rows = result.fetchall()
        except Exception as e:
            logger.warning("[TwinIndexer] ATS query failed, trying simplified: %s", e)
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

            # P0-4(b) audit 2026-05-21: LGPD Art. 7/11 — sem PII direta no embed.
            # 'name' removido do candidate_snapshot. candidate_id mantido para JIT lookup
            # (que respeitará erasure via cascade na Wave 2). reviewer_notes embedado mas
            # idealmente passaria por PII strip server-side antes (Wave 2).
            candidate_snapshot = {
                "candidate_id": str(row.candidate_id),  # ref, não PII
                "role_name": row.role_name,
                "technical_skills": row.technical_skills or [],
                "years_of_experience": row.years_of_experience,
            }

            text_for_embedding = (
                f"Decisão: {decision}\n"
                f"Cargo: {row.job_title}\n"
                f"Perfil: {json.dumps(candidate_snapshot, ensure_ascii=False)}\n"
                f"Raciocínio: {row.reviewer_notes}"
            )
            embedding = await self._embed(text_for_embedding)

            td = TwinDecision(
                id=uuid.uuid4(),
                twin_id=twin_id,
                decision=decision,
                reasoning=row.reviewer_notes or "",
                candidate_snapshot=candidate_snapshot,
                job_snapshot={"title": row.job_title},
                embedding=embedding,
                source="ats_history",
            )
            await repo.add_decision(decision=td, company_id=company_id)
            indexed += 1

        if indexed > 0:
            await db.commit()
            await repo.update_decision_count(
                twin_id=twin_id, company_id=company_id
            )
            await db.commit()

        logger.info("[TwinIndexer] twin=%s indexed %d decisions from ATS", twin_id, indexed)
        return indexed

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
        decisions = await self._extract_decisions_from_transcript(transcription)

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

    async def _extract_decisions_from_transcript(self, transcript: str) -> list[dict]:
        """Extract individual decisions from a transcript via LLM."""
        try:
            from app.shared.providers.llm_factory import get_llm
            llm = get_llm(tier="fast")
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
        APPROVED = {"hired", "offer_accepted", "passed_interview", "shortlisted", "approved"}
        REJECTED = {"rejected", "disqualified", "failed_screening", "declined"}
        if status in APPROVED:
            return "approved"
        if status in REJECTED:
            return "rejected"
        return None


twin_knowledge_indexer = TwinKnowledgeIndexer()
