import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, delete, select, update
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import AsyncSessionLocal, Base

logger = logging.getLogger(__name__)

VALID_MEMORY_TYPES = {"pattern", "preference", "learning", "outcome"}


class AgentLongTermMemory(Base):
    __tablename__ = "agent_long_term_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    domain = Column(String(100), nullable=False)
    memory_type = Column(String(50), nullable=False)
    memory_key = Column(String(255), nullable=False)
    memory_value = Column(JSON, default=dict)
    context_tags = Column(JSON, default=list)
    usage_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=1.0)
    source_session_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
    expires_at = Column(DateTime, nullable=True)


class LongTermMemoryService:

    async def store(
        self,
        company_id: str,
        domain: str,
        memory_type: str,
        key: str,
        value: Any,
        tags: List[str],
        session_id: str,
    ) -> AgentLongTermMemory:
        if memory_type not in VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type '{memory_type}'. Must be one of: {VALID_MEMORY_TYPES}"
            )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentLongTermMemory).where(
                    AgentLongTermMemory.company_id == company_id,  # type: ignore
                    AgentLongTermMemory.domain == domain,  # type: ignore
                    AgentLongTermMemory.memory_key == key,  # type: ignore
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.memory_value = value  # type: ignore
                existing.context_tags = tags  # type: ignore
                existing.memory_type = memory_type  # type: ignore
                existing.source_session_id = session_id  # type: ignore
                existing.updated_at = datetime.utcnow()  # type: ignore
                existing.relevance_score = min(existing.relevance_score + 0.1, 1.0)  # type: ignore
                await session.commit()
                await session.refresh(existing)
                logger.info(
                    f"Updated long-term memory key='{key}' for company={company_id} domain={domain}"
                )
                return existing

            memory = AgentLongTermMemory(
                company_id=company_id,
                domain=domain,
                memory_type=memory_type,
                memory_key=key,
                memory_value=value,
                context_tags=tags,
                usage_count=0,
                relevance_score=1.0,
                source_session_id=session_id,
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            logger.info(
                f"Stored new long-term memory key='{key}' for company={company_id} domain={domain}"
            )
            return memory

    async def recall(
        self,
        company_id: str,
        domain: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[AgentLongTermMemory]:
        async with AsyncSessionLocal() as session:
            query = select(AgentLongTermMemory).where(
                AgentLongTermMemory.company_id == company_id,  # type: ignore
            )

            if domain:
                query = query.where(AgentLongTermMemory.domain == domain)  # type: ignore

            if memory_type:
                query = query.where(AgentLongTermMemory.memory_type == memory_type)  # type: ignore

            now = datetime.utcnow()
            query = query.where(
                (AgentLongTermMemory.expires_at.is_(None))
                | (AgentLongTermMemory.expires_at > now)
            )

            query = query.order_by(
                (AgentLongTermMemory.relevance_score * (AgentLongTermMemory.usage_count + 1)).desc()
            ).limit(limit)

            result = await session.execute(query)
            memories = list(result.scalars().all())

            if tags and memories:
                tag_set = set(tags)
                scored = []
                for mem in memories:
                    mem_tags = set(mem.context_tags or [])  # type: ignore
                    overlap = len(tag_set & mem_tags)
                    scored.append((overlap, mem))
                scored.sort(key=lambda x: x[0], reverse=True)
                memories = [m for _, m in scored if _ > 0] or memories

            for mem in memories:
                mem.usage_count = (mem.usage_count or 0) + 1  # type: ignore
                mem.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()

            logger.debug(
                f"Recalled {len(memories)} long-term memories for company={company_id} "
                f"domain={domain} type={memory_type}"
            )
            return memories

    async def recall_for_context(
        self,
        company_id: str,
        domain: str,
        context_text: str,
        limit: int = 3,
    ) -> List[AgentLongTermMemory]:
        context_words = set(context_text.lower().split())

        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            query = (
                select(AgentLongTermMemory)
                .where(
                    AgentLongTermMemory.company_id == company_id,  # type: ignore
                    AgentLongTermMemory.domain == domain,  # type: ignore
                    (AgentLongTermMemory.expires_at.is_(None))
                    | (AgentLongTermMemory.expires_at > now),
                )
                .order_by(
                    (AgentLongTermMemory.relevance_score * (AgentLongTermMemory.usage_count + 1)).desc()
                )
                .limit(50)
            )

            result = await session.execute(query)
            candidates = list(result.scalars().all())

            scored: List[tuple] = []
            for mem in candidates:
                mem_tags = set(t.lower() for t in (mem.context_tags or []))  # type: ignore
                mem_key_words = set(mem.memory_key.lower().replace("_", " ").split())  # type: ignore
                all_mem_words = mem_tags | mem_key_words
                overlap = len(context_words & all_mem_words)
                if overlap > 0:
                    score = overlap * mem.relevance_score * (mem.usage_count + 1)  # type: ignore
                    scored.append((score, mem))

            scored.sort(key=lambda x: x[0], reverse=True)
            matched = [m for _, m in scored[:limit]]

            for mem in matched:
                mem.usage_count = (mem.usage_count or 0) + 1  # type: ignore
                mem.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()

            logger.debug(
                f"Recalled {len(matched)} context-matched memories for company={company_id} domain={domain}"
            )
            return matched

    async def update_relevance(
        self,
        memory_id: str,
        boost: float = 0.1,
    ) -> None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentLongTermMemory).where(
                    AgentLongTermMemory.id == memory_id,  # type: ignore
                )
            )
            memory = result.scalar_one_or_none()

            if memory is None:
                logger.warning(f"Cannot update relevance: memory {memory_id} not found")
                return

            memory.relevance_score = min((memory.relevance_score or 0) + boost, 1.0)  # type: ignore
            memory.updated_at = datetime.utcnow()  # type: ignore
            await session.commit()
            logger.debug(
                f"Boosted relevance for memory {memory_id} to {memory.relevance_score:.2f}"
            )

    async def decay_relevance(
        self,
        company_id: str,
        decay_factor: float = 0.95,
    ) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AgentLongTermMemory)
                .where(AgentLongTermMemory.company_id == company_id)  # type: ignore
                .values(
                    relevance_score=AgentLongTermMemory.relevance_score * decay_factor,
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()
            logger.info(
                f"Applied relevance decay (factor={decay_factor}) for company={company_id}"
            )

    async def get_company_learnings(
        self,
        company_id: str,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            query = select(AgentLongTermMemory).where(
                AgentLongTermMemory.company_id == company_id,  # type: ignore
                AgentLongTermMemory.memory_type == "learning",  # type: ignore
            )

            if domain:
                query = query.where(AgentLongTermMemory.domain == domain)  # type: ignore

            query = query.order_by(AgentLongTermMemory.updated_at.desc())

            result = await session.execute(query)
            memories = result.scalars().all()

            return [
                {
                    "id": str(mem.id),
                    "domain": mem.domain,
                    "key": mem.memory_key,
                    "value": mem.memory_value,
                    "tags": mem.context_tags or [],  # type: ignore
                    "usage_count": mem.usage_count,
                    "relevance_score": mem.relevance_score,
                    "created_at": mem.created_at.isoformat() if mem.created_at else None,  # type: ignore
                    "updated_at": mem.updated_at.isoformat() if mem.updated_at else None,  # type: ignore
                }
                for mem in memories
            ]

    async def compress_old_episodes(
        self,
        company_id: str,
        domain: str,
        age_days: int = 30,
    ) -> int:
        """
        Z4-02: Comprime episódios LTM mais antigos que age_days.

        Busca episódios antigos, gera resumo LLM, armazena como novo episódio
        comprimido e marca os antigos com expires_at=now para purge posterior.

        Returns:
            Número de episódios marcados para expiração.
        """
        cutoff = datetime.utcnow() - timedelta(days=age_days)
        compressed_count = 0

        try:
            async with AsyncSessionLocal() as session:
                query = (
                    select(AgentLongTermMemory)
                    .where(
                        AgentLongTermMemory.company_id == company_id,
                        AgentLongTermMemory.domain == domain,
                        AgentLongTermMemory.created_at < cutoff,
                        AgentLongTermMemory.expires_at.is_(None),
                    )
                    .order_by(AgentLongTermMemory.created_at.asc())
                    .limit(50)
                )
                result = await session.execute(query)
                old_episodes = list(result.scalars().all())

                if not old_episodes:
                    return 0

                # Gera resumo LLM (fail-safe: usa concatenação simples se LLM indisponível)
                summary_text = ""
                try:
                    from anthropic import Anthropic
                    import os

                    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                    if api_key:
                        client = Anthropic(api_key=api_key)
                        episodes_text = "\n".join(
                            f"- {ep.memory_key}: {ep.memory_value}"
                            for ep in old_episodes[:20]
                        )
                        response = client.messages.create(
                            model="claude-haiku-20240307",
                            max_tokens=512,
                            messages=[
                                {
                                    "role": "user",
                                    "content": (
                                        f"Resuma em 3-5 bullet points os seguintes episódios "
                                        f"de memória de agente IA (domínio: {domain}):\n\n"
                                        f"{episodes_text}"
                                    ),
                                }
                            ],
                        )
                        summary_text = response.content[0].text
                except Exception as llm_exc:
                    logger.debug(
                        "[LTM.compress] LLM summary falhou (fallback concat): %s", llm_exc
                    )
                    summary_text = "; ".join(
                        f"{ep.memory_key}={ep.memory_value}"
                        for ep in old_episodes[:10]
                    )

                # Armazena episódio comprimido
                compressed_key = (
                    f"compressed_{domain}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )
                compressed_memory = AgentLongTermMemory(
                    company_id=company_id,
                    domain=domain,
                    memory_type="learning",
                    memory_key=compressed_key,
                    memory_value={
                        "summary": summary_text,
                        "source_count": len(old_episodes),
                        "oldest_episode": (
                            old_episodes[0].created_at.isoformat()
                            if old_episodes[0].created_at
                            else None
                        ),
                        "compressed_at": datetime.utcnow().isoformat(),
                    },
                    context_tags=["compressed", domain],
                    usage_count=0,
                    relevance_score=0.8,
                    source_session_id="compression_job",
                )
                session.add(compressed_memory)

                # Marca episódios antigos para expiração
                now = datetime.utcnow()
                for ep in old_episodes:
                    ep.expires_at = now  # type: ignore
                    compressed_count += 1

                await session.commit()
                logger.info(
                    "[LTM.compress] company=%s domain=%s: %d episódios comprimidos",
                    company_id,
                    domain,
                    compressed_count,
                )
        except Exception as exc:
            logger.warning("[LTM.compress] falhou company=%s domain=%s: %s", company_id, domain, exc)

        return compressed_count

    async def purge_expired(self, company_id: str) -> int:
        """
        Z4-02: Remove registros com expires_at <= now (usado pelo Celery).

        Returns:
            Número de registros deletados.
        """
        deleted_count = 0
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                result = await session.execute(
                    delete(AgentLongTermMemory).where(
                        AgentLongTermMemory.company_id == company_id,
                        AgentLongTermMemory.expires_at.isnot(None),
                        AgentLongTermMemory.expires_at <= now,
                    )
                )
                deleted_count = result.rowcount or 0
                await session.commit()
                logger.info(
                    "[LTM.purge] company=%s: %d registros expirados removidos",
                    company_id,
                    deleted_count,
                )
        except Exception as exc:
            logger.warning("[LTM.purge] falhou company=%s: %s", company_id, exc)

        return deleted_count

    async def record_outcome(
        self,
        company_id: str,
        domain: str,
        session_id: str,
        outcome_type: str,
        outcome_data: Dict[str, Any],
        tags: List[str],
    ) -> AgentLongTermMemory:
        key = f"{outcome_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        value = {
            "outcome_type": outcome_type,
            "data": outcome_data,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        return await self.store(
            company_id=company_id,
            domain=domain,
            memory_type="outcome",
            key=key,
            value=value,
            tags=tags,
            session_id=session_id,
        )
