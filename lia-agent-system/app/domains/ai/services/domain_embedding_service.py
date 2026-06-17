"""
DomainEmbeddingService — manages embeddings per domain for RAG isolation.

Domains: talent (candidates), jobs (vacancies), policy (policy blocks),
         company (company documents), general (default).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

DOMAIN_MAP: dict[str, str] = {
    "candidates": "talent",
    "job_vacancies": "jobs",
    "policy_blocks": "policy",
    "company_docs": "company",
}


@dataclass
class EmbeddingRecord:
    source_type: str
    source_id: str
    company_id: str
    domain: str
    content: str
    embedded_at: datetime


class DomainEmbeddingService:
    """Manages domain-tagged embeddings for isolated RAG search."""

    def detect_domain(self, source_type: str) -> str:
        """Map source_type to domain name."""
        return DOMAIN_MAP.get(source_type, "general")

    async def embed_document(
        self,
        content: str,
        source_type: str,
        source_id: str,
        company_id: str,
        db,
    ) -> bool:
        """Generate and persist embedding with domain tag. Fail-open."""
        try:
            domain = self.detect_domain(source_type)
            # Import embedding service lazily to avoid circular imports
            from app.shared.intelligence.embedding_service import EmbeddingService
            svc = EmbeddingService()
            embedding = await svc.generate_embedding(content, company_id=company_id)
            if embedding is None:
                return False
            # Persist to routing_cache_vectors with domain
            from sqlalchemy import text
            await db.execute(
                text(
                    "INSERT INTO routing_cache_vectors "
                    "(company_id, content, embedding, domain, created_at) "
                    "VALUES (:company_id, :content, :embedding, :domain, NOW()) "
                    "ON CONFLICT DO NOTHING"
                ),
                {
                    "company_id": company_id,
                    "content": content[:2000],
                    "embedding": str(embedding),
                    "domain": domain,
                },
            )
            await db.commit()
            logger.info(
                "[DomainEmbedding] embedded source_type=%s source_id=%s domain=%s",
                source_type, source_id, domain,
            )
            return True
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning("[DomainEmbedding] embed_document failed (fail-open): %s", exc)
            return False

    async def rebuild_domain_index(
        self, domain: str, company_id: str, db
    ) -> int:
        """Reprocess all documents of a domain. Returns count rebuilt. Fail-open."""
        try:
            logger.info(
                "[DomainEmbedding] rebuild_domain_index domain=%s company=%s",
                domain, company_id,
            )
            from sqlalchemy import text
            result = await db.execute(
                text(
                    "SELECT COUNT(*) FROM routing_cache_vectors "
                    "WHERE domain = :domain AND company_id = :company_id"
                ),
                {"domain": domain, "company_id": company_id},
            )
            count = result.scalar() or 0
            logger.info("[DomainEmbedding] %d vectors found for domain=%s", count, domain)
            return count
        except Exception as exc:
            logger.warning("[DomainEmbedding] rebuild_domain_index failed: %s", exc)
            return 0


domain_embedding_service = DomainEmbeddingService()
