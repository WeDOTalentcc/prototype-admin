"""CandidateEmbeddingService — gera embedding text + persiste via repo."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CandidateEmbeddingService:
    def build_embedding_text(self, candidate: dict[str, Any]) -> str:
        """Monta texto canônico para embedding a partir de dados do candidato.

        Sem PII sensível (CPF/RG) — só dados profissionais.
        """
        parts: list[str] = []
        if candidate.get("summary"):
            parts.append(str(candidate["summary"]))
        if candidate.get("skills"):
            skills = candidate["skills"]
            if isinstance(skills, list):
                parts.append("Skills: " + ", ".join(str(s) for s in skills))
        if candidate.get("experience"):
            exp = candidate["experience"]
            if isinstance(exp, list):
                for e in exp[:5]:
                    if isinstance(e, dict):
                        title = e.get("title", "")
                        company = e.get("company", "")
                        if title or company:
                            parts.append(f"{title} @ {company}".strip(" @"))
        if candidate.get("education"):
            edu = candidate["education"]
            if isinstance(edu, list):
                for ed in edu[:3]:
                    if isinstance(ed, dict):
                        degree = ed.get("degree", "")
                        institution = ed.get("institution", "")
                        if degree or institution:
                            parts.append(f"{degree} - {institution}".strip(" -"))
        if candidate.get("languages"):
            langs = candidate["languages"]
            if isinstance(langs, list):
                parts.append("Languages: " + ", ".join(str(la) for la in langs))
        return "\n".join(parts) if parts else ""

    async def embed_candidate(
        self,
        candidate: dict[str, Any],
        company_id: str,
        db,
    ) -> bool:
        """Gera embedding e persiste. Fail-open."""
        try:
            text = self.build_embedding_text(candidate)
            if not text or len(text) < 10:
                logger.info("[CandidateEmbedding] texto muito curto, skip candidate=%s", candidate.get("id"))
                return False

            from app.shared.intelligence.embedding_service import EmbeddingService
            svc = EmbeddingService()
            embedding = await svc.generate_embedding(text, company_id=company_id)
            if not embedding:
                return False

            from app.domains.ai.repositories.candidate_embedding_repository import (
                CandidateEmbeddingRepository,
            )
            repo = CandidateEmbeddingRepository(db)
            await repo.upsert_embedding(
                candidate_id=str(candidate.get("id", "")),
                company_id=company_id,
                embedding=embedding,
                embedding_text=text,
                name=candidate.get("name"),
                skills=candidate.get("skills") if isinstance(candidate.get("skills"), list) else None,
                summary=candidate.get("summary"),
                provider=getattr(svc, "_last_provider", None),
            )
            return True
        except Exception as exc:
            logger.warning("[CandidateEmbedding] embed_candidate failed (fail-open): %s", exc)
            return False


    async def find_similar_candidates(
        self,
        candidate: dict,
        company_id: str,
        db,
        limit: int = 20,
    ) -> list[dict]:
        text = self.build_embedding_text(candidate)
        if not text or len(text) < 10:
            return []
        try:
            from app.shared.intelligence.embedding_service import EmbeddingService
            svc = EmbeddingService()
            embedding = await svc.generate_embedding(text, company_id=company_id)
            if not embedding:
                return []
            from app.domains.ai.repositories.candidate_embedding_repository import (
                CandidateEmbeddingRepository,
            )
            repo = CandidateEmbeddingRepository(db)
            return await repo.search_similar(
                embedding=embedding,
                company_id=company_id,
                limit=limit,
                exclude_candidate_ids=[str(candidate.get("id", ""))],
            )
        except Exception as exc:
            logger.warning("[CandidateEmbedding] find_similar failed: %s", exc)
            return []


candidate_embedding_service = CandidateEmbeddingService()
