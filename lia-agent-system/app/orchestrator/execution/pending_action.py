"""
PendingActionState - Multi-turn action state management for LIA.

When LIA needs to collect parameters or wait for confirmation,
this module stores the pending action state keyed by conversation_id.

Uses PostgreSQL for persistent storage with in-memory cache as L1.
Falls back to memory-only if DB is unavailable.
"""
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PendingActionState:
    pending_id: str
    intent: str
    action_id: str
    domain_id: str
    collected_params: dict[str, Any]
    missing_params: list[str]
    conversation_id: str
    company_id: str | None = None
    awaiting_confirmation: bool = False
    confirmation_summary: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))

    @property
    def is_complete(self) -> bool:
        return len(self.missing_params) == 0

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def add_param(self, param_name: str, value: Any) -> None:
        self.collected_params[param_name] = value
        if param_name in self.missing_params:
            self.missing_params.remove(param_name)

    def next_missing_param(self) -> str | None:
        return self.missing_params[0] if self.missing_params else None


class PendingActionStore:

    def __init__(self):
        self._memory_store: dict[str, PendingActionState] = {}
        self._lock = threading.Lock()
        self._pool = None
        self._init_db_pool()

    def _init_db_pool(self):
        try:
            from psycopg2.pool import SimpleConnectionPool
            db_url = os.environ.get("DATABASE_URL", "")
            if db_url:
                self._pool = SimpleConnectionPool(1, 5, dsn=db_url)
                logger.info("PendingActionStore: PostgreSQL persistence enabled")
            else:
                logger.warning("PendingActionStore: No DATABASE_URL, using memory-only")
        except Exception as e:
            logger.warning(f"PendingActionStore: DB pool init failed, using memory-only: {e}")
            self._pool = None

    def _get_conn(self):
        if self._pool:
            try:
                return self._pool.getconn()
            except Exception as e:
                logger.warning(f"PendingActionStore: Failed to get connection: {e}")
        return None

    def _put_conn(self, conn):
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception:
                # T-04 Tipo C: returning connection to pool is best-effort;
                # pool may be closed or connection invalidated.
                logger.debug(
                    "[PendingActionStore] putconn failed (best-effort)",
                    exc_info=True,
                )

    def get(self, conversation_id: str) -> PendingActionState | None:
        with self._lock:
            state = self._memory_store.get(conversation_id)
            if state:
                if state.is_expired:
                    del self._memory_store[conversation_id]
                    self._db_remove(conversation_id)
                    logger.info(f"Pending action expired for conversation {conversation_id}")
                    return None
                return state

            state = self._db_get(conversation_id)
            if state:
                if state.is_expired:
                    self._db_remove(conversation_id)
                    logger.info(f"Pending action expired for conversation {conversation_id}")
                    return None
                self._memory_store[conversation_id] = state
            return state

    def save(self, conversation_id: str, state: PendingActionState) -> None:
        with self._lock:
            self._memory_store[conversation_id] = state
            self._db_save(conversation_id, state)
            logger.info(f"Saved pending action for conversation {conversation_id}: {state.action_id}")

    def remove(self, conversation_id: str) -> None:
        with self._lock:
            self._memory_store.pop(conversation_id, None)
            self._db_remove(conversation_id)
            logger.info(f"Removed pending action for conversation {conversation_id}")

    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = [k for k, v in self._memory_store.items() if v.is_expired]
            for k in expired_keys:
                del self._memory_store[k]

            db_cleaned = self._db_cleanup_expired()
            return max(len(expired_keys), db_cleaned)

    def _db_get(self, conversation_id: str) -> PendingActionState | None:
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pending_id, intent, action_id, domain_id, collected_params, "
                    "missing_params, awaiting_confirmation, confirmation_summary, created_at, expires_at, company_id "
                    "FROM pending_actions WHERE conversation_id = %s",
                    (conversation_id,)
                )
                row = cur.fetchone()
                if row:
                    return PendingActionState(
                        pending_id=row[0],
                        intent=row[1],
                        action_id=row[2],
                        domain_id=row[3],
                        collected_params=row[4] or {},
                        missing_params=row[5] or [],
                        conversation_id=conversation_id,
                        awaiting_confirmation=row[6],
                        confirmation_summary=row[7],
                        created_at=row[8],
                        expires_at=row[9],
                        company_id=row[10],
                    )
            return None
        except Exception as e:
            logger.warning(f"PendingActionStore DB get failed: {e}")
            return None
        finally:
            self._put_conn(conn)

    def _db_save(self, conversation_id: str, state: PendingActionState):
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO pending_actions
                    (conversation_id, pending_id, company_id, intent, action_id, domain_id,
                     collected_params, missing_params, awaiting_confirmation,
                     confirmation_summary, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conversation_id)
                    DO UPDATE SET pending_id=%s, company_id=%s, intent=%s, action_id=%s, domain_id=%s,
                     collected_params=%s, missing_params=%s, awaiting_confirmation=%s,
                     confirmation_summary=%s, created_at=%s, expires_at=%s""",
                    (
                        conversation_id, state.pending_id, state.company_id,
                        state.intent, state.action_id, state.domain_id,
                        json.dumps(state.collected_params), json.dumps(state.missing_params),
                        state.awaiting_confirmation,
                        json.dumps(state.confirmation_summary) if state.confirmation_summary else None,
                        state.created_at, state.expires_at,
                        state.pending_id, state.company_id,
                        state.intent, state.action_id, state.domain_id,
                        json.dumps(state.collected_params), json.dumps(state.missing_params),
                        state.awaiting_confirmation,
                        json.dumps(state.confirmation_summary) if state.confirmation_summary else None,
                        state.created_at, state.expires_at,
                    )
                )
            conn.commit()
        except Exception as e:
            logger.warning(f"PendingActionStore DB save failed: {e}")
            try:
                conn.rollback()
            except Exception:
                # T-04 Tipo C: rollback is best-effort after save failed;
                # connection may already be in invalid state.
                logger.debug(
                    "[PendingActionStore] save rollback failed (best-effort)",
                    exc_info=True,
                )
        finally:
            self._put_conn(conn)

    def _db_remove(self, conversation_id: str):
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pending_actions WHERE conversation_id = %s", (conversation_id,))
            conn.commit()
        except Exception as e:
            logger.warning(f"PendingActionStore DB remove failed: {e}")
            try:
                conn.rollback()
            except Exception:
                # T-04 Tipo C: rollback is best-effort after remove failed;
                # connection may already be in invalid state.
                logger.debug(
                    "[PendingActionStore] remove rollback failed (best-effort)",
                    exc_info=True,
                )
        finally:
            self._put_conn(conn)

    def _db_cleanup_expired(self) -> int:
        conn = self._get_conn()
        if not conn:
            return 0
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pending_actions WHERE expires_at < NOW()")
                count = cur.rowcount
            conn.commit()
            return count
        except Exception as e:
            logger.warning(f"PendingActionStore DB cleanup failed: {e}")
            try:
                conn.rollback()
            except Exception:
                # T-04 Tipo C: rollback is best-effort after cleanup failed;
                # connection may already be in invalid state.
                logger.debug(
                    "[PendingActionStore] cleanup rollback failed (best-effort)",
                    exc_info=True,
                )
            return 0
        finally:
            self._put_conn(conn)


pending_action_store = PendingActionStore()
