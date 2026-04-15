"""
Redis PII Encryption — Fernet encryption for PII values stored in Redis.

Encrypts candidate data (names, skills, scores, interview responses) before
writing to Redis. Decrypts transparently on read. Operational data (locks,
counters, routing) is NOT encrypted.

Key management:
  REDIS_ENCRYPTION_KEY env variable — URL-safe base-64 encoded Fernet key.
  Generate with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Security posture:
  FAIL-OPEN: if REDIS_ENCRYPTION_KEY is not set, data is stored in plaintext
  (same as before). This allows gradual rollout. A warning is logged once.

Item: PX08-086 — Wave 6, item 6.6
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_warned_no_key = False


class RedisCrypto:
    """Encrypt/decrypt PII values before storing in Redis.

    Usage:
        crypto = get_redis_crypto()
        encrypted = crypto.encrypt(json.dumps(candidate_data))
        redis.setex(key, ttl, encrypted)

        raw = redis.get(key)
        data = json.loads(crypto.decrypt(raw))
    """

    def __init__(self):
        key = os.environ.get("REDIS_ENCRYPTION_KEY")
        if key:
            try:
                from cryptography.fernet import Fernet
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
                logger.info("[RedisCrypto] Initialized with encryption key")
            except Exception as exc:
                logger.error("[RedisCrypto] Invalid REDIS_ENCRYPTION_KEY: %s", exc)
                self._fernet = None
        else:
            self._fernet = None
            global _warned_no_key
            if not _warned_no_key:
                logger.warning(
                    "[RedisCrypto] REDIS_ENCRYPTION_KEY not set — PII stored in plaintext"
                )
                _warned_no_key = True

    @property
    def is_enabled(self) -> bool:
        return self._fernet is not None

    def encrypt(self, value: str) -> str:
        """Encrypt a string value. Returns plaintext if no key configured."""
        if not self._fernet:
            return value
        try:
            return self._fernet.encrypt(value.encode()).decode()
        except Exception as exc:
            logger.warning("[RedisCrypto] Encrypt failed (storing plaintext): %s", exc)
            return value

    def decrypt(self, value: str) -> str:
        """Decrypt a string value. Handles plaintext gracefully (migration period)."""
        if not self._fernet:
            return value
        if not value:
            return value
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception:
            # Value is likely plaintext (pre-encryption data) — return as-is
            return value


_instance: RedisCrypto | None = None


def get_redis_crypto() -> RedisCrypto:
    """Get singleton RedisCrypto instance."""
    global _instance
    if _instance is None:
        _instance = RedisCrypto()
    return _instance
