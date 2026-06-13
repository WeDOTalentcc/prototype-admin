"""CandidateEmbedding Repository — upsert + similarity search."""
import logging
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CandidateEmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")
        return str(company_id)

    async def upsert_embedding(
        self,
        candidate_id: str,
        company_id: str,
        embedding: list[float],
        embedding_text: str,
        name: str | None = None,
        skills: list[str] | None = None,
        summary: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> int:
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            sa_text("""
                INSERT INTO candidate_embeddings
                    (id, company_id, candidate_id, name, summary, skills,
                     embedding, embedding_text, embedding_provider, embedding_model,
                     is_active, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :company_id, :candidate_id::uuid, :name, :summary, :skills,
                     :embedding::vector, :embedding_text, :provider, :model,
                     true, NOW(), NOW())
                ON CONFLICT (company_id, candidate_id)
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    embedding_text = EXCLUDED.embedding_text,
                    name = COALESCE(EXCLUDED.name, candidate_embeddings.name),
                    summary = COALESCE(EXCLUDED.summary, candidate_embeddings.summary),
                    skills = COALESCE(EXCLUDED.skills, candidate_embeddings.skills),
                    embedding_provider = EXCLUDED.embedding_provider,
                    embedding_model = EXCLUDED.embedding_model,
                    updated_at = NOW()
            """),
            {
                "company_id": cid,
                "candidate_id": str(candidate_id),
                "name": name,
                "summary": summary,
                "skills": skills or [],
                "embedding": str(embedding),
                "embedding_text": embedding_text[:4000] if embedding_text else "",
                "provider": provider,
                "model": model,
            },
        )
        return result.rowcount

    async def search_similar(
        self,
        embedding: list[float],
        company_id: str,
        limit: int = 20,
        exclude_candidate_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        cid = self._require_company_id(company_id)
        exclude = exclude_candidate_ids or []
        exclude_clause = ""
        params: dict[str, Any] = {
            "company_id": cid,
            "embedding": str(embedding),
            "limit": limit,
        }
        if exclude:
            exclude_clause = "AND candidate_id::text != ALL(:excludes)"
            params["excludes"] = exclude

        result = await self.db.execute(
            sa_text(f"""
                SELECT candidate_id, name, skills,
                       1 - (embedding <=> :embedding::vector) AS similarity
                FROM candidate_embeddings
                WHERE company_id = :company_id
                  AND is_active = true
                  AND embedding IS NOT NULL
                  {exclude_clause}
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """),
            params,
        )
        rows = result.fetchall()
        return [
            {
                "candidate_id": str(r[0]),
                "name": r[1],
                "skills": r[2],
                "similarity": float(r[3]),
            }
            for r in rows
        ]
