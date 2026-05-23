"""
cache_cleanup.py — one-time cleanup of poisoned routing cache entries.

Removes routing_cache_vectors rows where domain_id='job_management'
AND message matches known wizard creation patterns.
Also flushes ALL Redis route_cache entries (they re-populate correctly
after the domain validator guards are in place).

Run from project root:
  cd /home/runner/workspace/lia-agent-system
  python3 cache_cleanup.py --dry-run   # preview
  python3 cache_cleanup.py             # execute
"""
import asyncio
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cache_cleanup")

# Wizard creation patterns (mirrors FastRouter patterns for wizard domain)
WIZARD_PATTERNS_SQL = r"""(
    criar?\s+(uma?\s+)?(nova\s+)?vaga
    | nova\s+vaga
    | abrir\s+(uma?\s+)?(nova\s+)?(posição|vaga)
    | preciso\s+(de\s+)?(um[a]?\s+)?(recrut|contrat|selecion)
    | iniciar\s+(o\s+)?(wizard|processo|cadastro|criação)
    | job\s+(description|posting|openings?)
    | (contratar|contratação)\s+
    | processo\s+seletivo
    | descrição\s+da\s+vaga
    | jd\s+(da?\s+)?vaga
)"""


async def clean_vector_cache(dry_run: bool = True) -> int:
    """Delete poisoned job_management entries matching wizard patterns."""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text as sa_text

        check_sql = """
            SELECT COUNT(*) FROM routing_cache_vectors
            WHERE domain_id = 'job_management'
        """
        wizard_sql = f"""
            SELECT COUNT(*) FROM routing_cache_vectors
            WHERE domain_id = 'job_management'
            AND message_text ~* '{WIZARD_PATTERNS_SQL}'
        """
        delete_sql = f"""
            DELETE FROM routing_cache_vectors
            WHERE domain_id = 'job_management'
            AND message_text ~* '{WIZARD_PATTERNS_SQL}'
        """

        async with AsyncSessionLocal() as db:
            # Count total job_management entries
            total = (await db.execute(sa_text(check_sql))).scalar()
            logger.info("routing_cache_vectors: %d total job_management entries", total)

            # Count wizard-patterned ones
            wizard_count = (await db.execute(sa_text(wizard_sql))).scalar()
            logger.info("  → %d match wizard patterns (to be deleted)", wizard_count)

            if wizard_count == 0:
                logger.info("Nothing to clean.")
                return 0

            if dry_run:
                logger.info("[DRY RUN] Would delete %d rows. Run without --dry-run to execute.", wizard_count)
                return wizard_count

            result = await db.execute(sa_text(delete_sql))
            await db.commit()
            deleted = result.rowcount
            logger.info("[DONE] Deleted %d poisoned routing_cache_vectors rows", deleted)
            return deleted

    except Exception as exc:
        logger.error("Vector cache cleanup failed: %s", exc)
        return -1


async def flush_redis_routing_cache() -> int:
    """Flush all route_cache:* keys from Redis."""
    try:
        from app.orchestrator.memory.semantic_cache import SemanticCache
        cache = SemanticCache()
        # Task #1144: flush_all() now requires an explicit scope (tenant or
        # pattern) to prevent accidental cross-tenant wipes. This script is
        # the documented operational override that intentionally targets
        # every tenant's routing cache — pass the broad pattern explicitly.
        count = await cache.flush_all(pattern="route_cache:*")
        logger.info("[DONE] Flushed %d Redis route_cache entries", count)
        return count
    except Exception as exc:
        logger.error("Redis flush failed: %s", exc)
        return -1


async def main(dry_run: bool = True):
    logger.info("=== Cache Cleanup — %s ===", "DRY RUN" if dry_run else "EXECUTE")

    # 1. Clean vector table
    deleted = await clean_vector_cache(dry_run=dry_run)
    logger.info("Vector cache: %d rows %s", deleted, "would be deleted" if dry_run else "deleted")

    # 2. Flush Redis (only in execute mode)
    if not dry_run:
        flushed = await flush_redis_routing_cache()
        logger.info("Redis cache: %d keys flushed", flushed)
    else:
        logger.info("[DRY RUN] Redis flush skipped (would flush all route_cache:* keys)")

    logger.info("=== Done ===")


if __name__ == "__main__":
    sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    if not dry_run and len(sys.argv) < 2:
        # Default to dry-run for safety
        dry_run = True
        logger.info("No --execute flag; defaulting to --dry-run. Pass --execute to run.")
    if '--execute' in sys.argv:
        dry_run = False
    asyncio.run(main(dry_run=dry_run))
