import logging
from typing import Any, Dict, List, Optional

from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.long_term_memory import LongTermMemoryService

logger = logging.getLogger(__name__)


class MemoryIntegration:

    def __init__(
        self,
        working_memory: WorkingMemoryService,
        long_term_memory: LongTermMemoryService,
    ):
        self.working_memory = working_memory
        self.long_term_memory = long_term_memory

    async def get_enriched_context(
        self,
        session_id: str,
        domain: str,
        company_id: str,
    ) -> str:
        parts: List[str] = []

        try:
            wm_summary = await self.working_memory.get_context_summary(
                session_id=session_id,
                domain=domain,
            )
            if wm_summary and wm_summary != "No working memory found for this session.":
                parts.append("=== Session Memory ===")
                parts.append(wm_summary)
        except Exception as exc:
            logger.warning(f"Failed to retrieve working memory context: {exc}")

        try:
            lt_memories = await self.long_term_memory.recall(
                company_id=company_id,
                domain=domain,
                limit=5,
            )
            if lt_memories:
                parts.append("")
                parts.append("=== Cross-Session Learnings ===")
                for mem in lt_memories:
                    tags_str = ", ".join(mem.context_tags or [])  # type: ignore
                    parts.append(
                        f"- [{mem.memory_type}] {mem.memory_key}: "
                        f"{_summarize_value(mem.memory_value)} "
                        f"(tags: {tags_str}, used {mem.usage_count}x)"
                    )
        except Exception as exc:
            logger.warning(f"Failed to retrieve long-term memories: {exc}")

        return "\n".join(parts) if parts else ""

    async def save_session_learnings(
        self,
        session_id: str,
        domain: str,
        company_id: str,
        learnings: List[Dict[str, Any]],
    ) -> None:
        saved_count = 0
        for learning in learnings:
            try:
                memory_type = learning.get("type", "learning")
                key = learning.get("key", "")
                value = learning.get("value", {})
                tags = learning.get("tags", [])

                if not key:
                    logger.warning(f"Skipping learning with empty key: {learning}")
                    continue

                await self.long_term_memory.store(
                    company_id=company_id,
                    domain=domain,
                    memory_type=memory_type,
                    key=key,
                    value=value,
                    tags=tags,
                    session_id=session_id,
                )
                saved_count += 1
            except Exception as exc:
                logger.warning(
                    f"Failed to save learning '{learning.get('key', '?')}': {exc}"
                )

        logger.info(
            f"Saved {saved_count}/{len(learnings)} session learnings for "
            f"company={company_id} domain={domain} session={session_id}"
        )

    async def get_memory_summary_for_prompt(
        self,
        company_id: str,
        domain: str,
        context_tags: Optional[List[str]] = None,
    ) -> str:
        parts: List[str] = []

        try:
            if context_tags:
                memories = await self.long_term_memory.recall(
                    company_id=company_id,
                    domain=domain,
                    tags=context_tags,
                    limit=5,
                )
            else:
                memories = await self.long_term_memory.recall(
                    company_id=company_id,
                    domain=domain,
                    limit=5,
                )

            if not memories:
                return ""

            patterns = [m for m in memories if m.memory_type == "pattern"]  # type: ignore
            preferences = [m for m in memories if m.memory_type == "preference"]  # type: ignore
            learnings = [m for m in memories if m.memory_type == "learning"]  # type: ignore
            outcomes = [m for m in memories if m.memory_type == "outcome"]  # type: ignore

            if patterns:
                parts.append("Known Patterns:")
                for m in patterns:
                    parts.append(f"  - {m.memory_key}: {_summarize_value(m.memory_value)}")

            if preferences:
                parts.append("Company Preferences:")
                for m in preferences:
                    parts.append(f"  - {m.memory_key}: {_summarize_value(m.memory_value)}")

            if learnings:
                parts.append("Previous Learnings:")
                for m in learnings:
                    parts.append(f"  - {m.memory_key}: {_summarize_value(m.memory_value)}")

            if outcomes:
                parts.append("Recent Outcomes:")
                for m in outcomes[:3]:
                    parts.append(f"  - {m.memory_key}: {_summarize_value(m.memory_value)}")

        except Exception as exc:
            logger.warning(f"Failed to generate memory summary for prompt: {exc}")

        return "\n".join(parts) if parts else ""


def _summarize_value(value: Any, max_length: int = 200) -> str:
    if isinstance(value, dict):
        summary = ", ".join(f"{k}: {v}" for k, v in list(value.items())[:5])
    elif isinstance(value, list):
        summary = ", ".join(str(v) for v in value[:5])
    else:
        summary = str(value)

    if len(summary) > max_length:
        summary = summary[:max_length] + "..."

    return summary
