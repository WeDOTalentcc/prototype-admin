"""
Task #1144 — Redis tenant-namespace migration script.

Scans the production Redis instance for legacy (non-tenant-namespaced) keys
left behind by the pre-#1144 code paths and decides their fate based on
whether the key can be **attributed to a tenant**:

  1. Try metadata-based attribution (e.g. SessionBridge stores ``company_id``
     inside the JSON payload — when readable, the key is RENAMEd to the new
     ``<prefix>:<company_id>:<suffix>`` shape instead of being purged).
  2. When attribution is impossible (opaque hash, encrypted payload, expired
     entry), fall back to a **non-destructive TTL** via ``PEXPIRE`` so the
     key ages out naturally — this preserves audit trails for SOX.
  3. Only ``--delete`` (explicit + ``--yes-i-am-sure``) issues ``DEL``.

Legacy key shapes detected:

  ``route_cache:<md5>``                                   (SemanticCache)
  ``lia:session:<session_id>``                            (SessionBridge)
  ``lia:action_history:<session_id>``                     (MemoryResolver)
  ``prompt_exp:<experiment_id>:<variant_id>:<day>``       (PromptExperiment)
  ``rl:user:<user_id>:(min|hour)``                        (RateLimiter)
  ``rl:company:<company_id>:(min|hour)``                  (RateLimiter)
  ``lia:<domain>:<param_hash>``                           (CacheStrategy)

Usage:
    # Default — report-only, no writes:
    python -m scripts.redis.migrate_tenant_namespaced_keys

    # Apply (TTL fallback for un-attributable keys, RENAME for attributable):
    python -m scripts.redis.migrate_tenant_namespaced_keys --apply --yes-i-am-sure

    # Hard-delete instead of TTL (irreversible):
    python -m scripts.redis.migrate_tenant_namespaced_keys --apply --delete \\
        --yes-i-am-sure

Safety:
* Default mode is REPORT-only (read-only ``SCAN``).
* ``--apply`` requires ``--yes-i-am-sure``.
* ``--delete`` only takes effect together with both flags above.
* Uses ``SCAN`` (non-blocking) with ``MATCH`` patterns; never ``KEYS *``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from collections import defaultdict

logger = logging.getLogger("redis_tenant_migration")

# Default TTL for legacy keys that cannot be attributed to a tenant.
# 24h is long enough for on-call to roll back the migration but short enough
# that stale cross-tenant cache entries cannot influence routing for >1 day.
# Policy (Task #1144): the 24h grace period gives on-call a full day to roll
# back the migration if a downstream consumer breaks. Operators who want
# immediate cache-miss semantics MUST pass ``--apply --delete`` (hard DEL)
# or override with ``--ttl-ms 0``. The default is grace, not zero.
DEFAULT_LEGACY_TTL_MS: int = 24 * 60 * 60 * 1000

LEGACY_PATTERNS: dict[str, str] = {
    "route_cache_legacy": "route_cache:*",
    "session_legacy": "lia:session:*",
    "action_history_legacy": "lia:action_history:*",
    "prompt_exp_legacy": "prompt_exp:*",
    "rl_user_legacy": "rl:user:*",
    "rl_company_legacy": "rl:company:*",
    # Task #1144 — CacheStrategy family. Legacy shape is
    # ``lia:<domain>:<param_hash>`` (3 segments) where the new shape is
    # ``lia:<domain>:<company_id>:<param_hash>`` (4 segments). We enumerate
    # the well-known CacheDomain values explicitly (one pattern per
    # domain) instead of scanning ``lia:*`` — that avoids touching
    # unrelated keys that happen to share the ``lia:`` prefix, which
    # could cause operational/data-loss risk under ``--apply --delete``.
}
_CACHE_STRATEGY_DOMAINS: tuple[str, ...] = (
    "candidate_search",
    "candidate_profile",
    "job_vacancy",
    "job_description",
    "wsi_score",
    "pipeline_stages",
    "company_config",
    "skill_catalog",
    "llm_response",
    "template",
    "analytics",
    "routing",
    "salary_benchmark",
    "market_data",
    "skills_suggestions",
    "jd_summary",
    "learning_patterns",
    "embeddings",
)
for _d in _CACHE_STRATEGY_DOMAINS:
    LEGACY_PATTERNS[f"cache_strategy_{_d}_legacy"] = f"lia:{_d}:*"


def _is_legacy(key: str, pattern_name: str) -> bool:
    """Return True if the SCAN-matched key is in the legacy shape."""
    parts = key.split(":")
    if pattern_name == "route_cache_legacy":
        return len(parts) == 2
    if pattern_name == "session_legacy":
        return len(parts) == 3
    if pattern_name == "action_history_legacy":
        return len(parts) == 3
    if pattern_name == "prompt_exp_legacy":
        return len(parts) == 4
    if pattern_name in ("rl_user_legacy", "rl_company_legacy"):
        return len(parts) == 4
    if pattern_name.startswith("cache_strategy_") and pattern_name.endswith("_legacy"):
        # new: lia:<domain>:<cid>:<param_hash>     → 4 segments
        # legacy: lia:<domain>:<param_hash>        → 3 segments
        # Per-domain patterns (one per CacheDomain) keep the scan tight
        # and avoid touching unrelated ``lia:``-prefixed keys.
        if len(parts) != 3:
            return False
        return parts[1] not in {"session", "action_history"}
    return False


async def _try_attribute_session(client, raw_key: str) -> str | None:
    """Best-effort tenant attribution for ``lia:session:<sid>`` legacy keys.

    SessionBridge persists JSON-serialised ``SessionContext`` which (post-1144)
    embeds ``company_id``. For plaintext entries we can decode and read it;
    encrypted entries (REDIS_ENCRYPTION_KEY) return None and fall back to
    TTL/delete.
    """
    try:
        raw = await client.get(raw_key)
        if not raw:
            return None
        payload = json.loads(raw)
        cid = payload.get("company_id")
        if isinstance(cid, str) and cid:
            return cid
    except Exception:
        return None
    return None


async def _rename_with_namespace(client, old_key: str, new_key: str) -> bool:
    """Atomic RENAMENX so we never clobber an existing tenant-namespaced key."""
    try:
        return bool(await client.renamenx(old_key, new_key))
    except Exception as exc:
        logger.warning("RENAMENX %s -> %s failed: %s", old_key, new_key, exc)
        return False


async def scan_and_act(
    redis_url: str,
    *,
    apply: bool,
    delete: bool,
    ttl_ms: int,
    batch: int = 500,
) -> dict[str, int]:
    """Scan Redis for legacy keys; attribute / expire / delete as configured."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(redis_url, decode_responses=True)
    await client.ping()

    found: dict[str, int] = defaultdict(int)
    attributed: dict[str, int] = defaultdict(int)
    expired: dict[str, int] = defaultdict(int)
    deleted: dict[str, int] = defaultdict(int)

    pending_del: list[str] = []
    pending_del_label: list[str] = []
    pending_exp: list[tuple[str, str]] = []  # (label, key)

    async def _flush_del() -> None:
        if not pending_del:
            return
        await client.delete(*pending_del)
        for lbl in pending_del_label:
            deleted[lbl] += 1
        pending_del.clear()
        pending_del_label.clear()

    async def _flush_exp() -> None:
        if not pending_exp:
            return
        pipe = client.pipeline()
        for _, k in pending_exp:
            pipe.pexpire(k, ttl_ms)
        await pipe.execute()
        for lbl, _ in pending_exp:
            expired[lbl] += 1
        pending_exp.clear()

    try:
        for label, pattern in LEGACY_PATTERNS.items():
            async for raw_key in client.scan_iter(match=pattern, count=500):
                if not _is_legacy(raw_key, label):
                    continue
                found[label] += 1
                if not apply:
                    continue

                # 1) Try metadata-based attribution (only sessions today).
                cid: str | None = None
                if label == "session_legacy":
                    cid = await _try_attribute_session(client, raw_key)
                if cid:
                    sid = raw_key.split(":", 2)[2]
                    new_key = f"lia:session:{cid}:{sid}"
                    if await _rename_with_namespace(client, raw_key, new_key):
                        attributed[label] += 1
                        continue
                    # If RENAMENX collided, fall through to TTL/delete.

                # 2) Fallback: hard delete (only when explicitly opted in)
                #    or non-destructive TTL via PEXPIRE.
                if delete:
                    pending_del.append(raw_key)
                    pending_del_label.append(label)
                    if len(pending_del) >= batch:
                        await _flush_del()
                else:
                    pending_exp.append((label, raw_key))
                    if len(pending_exp) >= batch:
                        await _flush_exp()

        await _flush_del()
        await _flush_exp()
    finally:
        await client.aclose()

    out: dict[str, int] = {}
    for label in LEGACY_PATTERNS:
        out[f"{label}_found"] = found.get(label, 0)
        out[f"{label}_attributed"] = attributed.get(label, 0)
        out[f"{label}_expired"] = expired.get(label, 0)
        out[f"{label}_deleted"] = deleted.get(label, 0)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Report-only scan (default). No writes to Redis.",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Perform writes (rename/expire/delete).",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Hard DEL un-attributable keys (default: PEXPIRE TTL fallback).",
    )
    parser.add_argument(
        "--yes-i-am-sure",
        action="store_true",
        help="Required acknowledgement for --apply.",
    )
    parser.add_argument(
        "--ttl-ms",
        type=int,
        default=DEFAULT_LEGACY_TTL_MS,
        help=f"PEXPIRE TTL for un-attributable keys (default: {DEFAULT_LEGACY_TTL_MS} ms = 24h).",
    )
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    apply = bool(args.apply)
    delete = bool(args.delete)
    if apply and not args.yes_i_am_sure:
        logger.error("--apply requires --yes-i-am-sure (writes to production Redis).")
        return 1
    if delete and not apply:
        logger.error("--delete requires --apply.")
        return 1

    mode = "REPORT-ONLY"
    if apply:
        mode = "APPLY+DELETE" if delete else f"APPLY+TTL({args.ttl_ms}ms)"
    logger.info("Mode=%s redis_url=%s", mode, args.redis_url)
    try:
        result = asyncio.run(
            scan_and_act(
                args.redis_url,
                apply=apply,
                delete=delete,
                ttl_ms=args.ttl_ms,
            )
        )
    except Exception as exc:
        logger.exception("Migration failed: %s", exc)
        return 1

    for k, v in sorted(result.items()):
        logger.info("  %s = %d", k, v)
    total_legacy = sum(v for k, v in result.items() if k.endswith("_found"))
    total_attributed = sum(v for k, v in result.items() if k.endswith("_attributed"))
    logger.info(
        "Summary: legacy=%d attributed=%d", total_legacy, total_attributed
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
