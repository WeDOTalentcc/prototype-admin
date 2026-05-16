"""Canonical tenant-filter wrapper for Elasticsearch queries (Task #1147).

Every ``es.search(...)`` / ``es.count(...)`` call in the backend MUST pass
through :func:`with_tenant_filter` so that the resulting payload carries a
``bool.filter[{"term": {"company_id": "<cid>"}}]`` clause. Elasticsearch has
no row-level-security equivalent: a missing filter == cross-tenant leak.

Three layers of defense:

1. **Build-time AST sensor** — ``scripts/check_es_search_has_tenant_filter.py``
   fails CI if a new callsite uses ``es.search(body=...)`` without first
   wrapping the body with :func:`with_tenant_filter` (allowlist for
   health/admin in ``scripts/.es_search_allowlist.txt``).
2. **Runtime interceptor** — :class:`TenantAwareElasticsearchClient` proxies
   ``search`` / ``count`` calls and asserts the payload contains a
   ``company_id`` term filter. In dev/test the assertion raises
   :class:`MissingTenantFilterError` with the originating stack; in
   production the same assertion raises ``RuntimeError`` (fail-loud).
3. **Sentinel suite** — ``tests/integration/search/test_es_tenant_filter.py``
   covers each ES callsite end-to-end with a mock ES client.

Metric:
    ``lia_es_search_tenant_filter_outcome_total{service,outcome}`` where
    ``outcome ∈ {"ok", "injected", "missing"}``.
"""
from __future__ import annotations

import copy
import logging
import os
from typing import Any

from app.shared.errors import LIATenantError
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

__all__ = [
    "ConflictingTenantFilterError",
    "MissingTenantFilterError",
    "TenantAwareElasticsearchClient",
    "get_es_tenant_filter_metrics",
    "query_has_tenant_filter",
    "with_tenant_filter",
]

_COMPANY_ID_FIELD = "company_id"


# --- exceptions -----------------------------------------------------------


class MissingTenantFilterError(LIATenantError):
    """Raised when an ES query is dispatched without a ``company_id`` term filter.

    "Missing" specifically means: the payload does not contain a
    ``{"term": {"company_id": "<cid>"}}`` clause inside ``query.bool.filter``
    (filter context — non-scoring, deterministic). A clause in ``must``,
    ``must_not``, or ``should`` does NOT satisfy the contract: ``must_not``
    would *exclude* the tenant entirely (worst-case leak), ``should`` is OR
    semantics (still matches other tenants), and ``must`` is scoring
    context that some query rewrites can drop.

    Carries the offending payload (truncated) and the calling service name
    in ``details`` so on-call can pinpoint the regression. ``error_code``
    is ``MISSING_TENANT_FILTER`` for Sentry fingerprinting alongside
    ``MISSING_TENANT_CONTEXT`` (T-A canonical).
    """

    def __init__(
        self,
        message: str = "Elasticsearch query missing company_id term filter",
        code: str = "MISSING_TENANT_FILTER",
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details or {},
            recoverable=False,
            **kwargs,
        )


class ConflictingTenantFilterError(LIATenantError):
    """Raised when ``with_tenant_filter(q, cid)`` is asked to inject a cid
    that conflicts with an existing different ``company_id`` term already
    present in ``query.bool.filter``.

    This is a hard fail-closed: the caller almost certainly has a tenant
    confusion bug (passing one tenant's authenticated cid into a query
    that was built for another tenant). Silent "last write wins" or
    "append both" would mask the bug AND in the append case the ES
    query would return zero hits (two contradictory term filters), which
    looks like a normal empty result.
    """

    def __init__(
        self,
        message: str = "Elasticsearch query already has a different company_id filter",
        code: str = "CONFLICTING_TENANT_FILTER",
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details or {},
            recoverable=False,
            **kwargs,
        )


# --- core wrapper ---------------------------------------------------------


def with_tenant_filter(query: dict[str, Any] | None, company_id: Any) -> dict[str, Any]:
    """Inject ``{"term": {"company_id": <cid>}}`` into ``query.bool.filter``.

    - Always returns a NEW dict (defensive copy of ``query``).
    - ``company_id`` is validated via :meth:`CompanyId.parse` — empty strings,
      ``"default"`` and other forbidden literals raise ``InvalidCompanyIdError``.
    - Idempotent: calling twice with the same ``company_id`` does not duplicate
      the filter clause.
    - **Conflict detection (fail-closed):** if a ``{"term": {"company_id": X}}``
      clause is already present *anywhere in the bool block*
      (``filter`` / ``must`` / ``should`` / ``must_not``) with a value
      ``X != cid``, raise :class:`ConflictingTenantFilterError`. This catches
      tenant-confusion bugs where one tenant's authenticated cid is being
      injected into a query that was pre-built for a different tenant.
    - **Stripped from non-filter context:** if the SAME ``cid`` exists in
      ``must`` / ``should`` / ``must_not``, it is removed and re-inserted in
      ``filter`` — those contexts do not provide tenant isolation
      (``must_not`` would *exclude* the tenant, ``should`` is OR, ``must``
      is scoring).

    Args:
        query: Elasticsearch query body. ``None`` is treated as ``{}``.
        company_id: tenant identifier — accepts ``str`` or ``UUID``.

    Returns:
        New query dict with ``bool.filter[{"term": {"company_id": cid}}]``
        guaranteed present and no conflicting cid elsewhere.

    Raises:
        InvalidCompanyIdError: when ``company_id`` is missing/empty/forbidden.
        ConflictingTenantFilterError: when a different cid is already present.
    """
    cid = CompanyId.parse(company_id).as_str()
    base: dict[str, Any] = copy.deepcopy(query) if query else {}

    inner = base.setdefault("query", {})
    if not isinstance(inner, dict):
        raise TypeError(
            f"query['query'] must be a dict, got {type(inner).__name__}"
        )

    bool_block = inner.setdefault("bool", {})
    if not isinstance(bool_block, dict):
        raise TypeError(
            f"query['query']['bool'] must be a dict, got {type(bool_block).__name__}"
        )

    filters = bool_block.setdefault("filter", [])
    # Accept a single-dict shortcut (`"filter": {...}`) and normalise to list.
    if isinstance(filters, dict):
        filters = [filters]
        bool_block["filter"] = filters
    if not isinstance(filters, list):
        raise TypeError(
            f"query['query']['bool']['filter'] must be list/dict, got {type(filters).__name__}"
        )

    # Scan EVERY bool sub-clause for an existing company_id term and
    # detect conflicts. We deliberately do not recurse into nested bool
    # blocks (those represent sub-queries that may legitimately scope to
    # other entities); the contract is about the top-level bool block.
    for clause_name in ("filter", "must", "should", "must_not"):
        block = bool_block.get(clause_name)
        if isinstance(block, dict):
            block = [block]
        if not isinstance(block, list):
            continue
        for clause in block:
            if not (
                isinstance(clause, dict)
                and isinstance(clause.get("term"), dict)
                and _COMPANY_ID_FIELD in clause["term"]
            ):
                continue
            existing = clause["term"][_COMPANY_ID_FIELD]
            if existing != cid:
                raise ConflictingTenantFilterError(
                    details={
                        "expected_company_id": cid,
                        "found_company_id": str(existing),
                        "clause": clause_name,
                    },
                )
            # Same cid in the wrong (non-filter) context → strip it; we'll
            # re-add canonically in `filter` below.
            if clause_name != "filter":
                block.remove(clause)

    # Idempotency check — re-injection of same cid in filter is a no-op.
    for clause in filters:
        if (
            isinstance(clause, dict)
            and isinstance(clause.get("term"), dict)
            and clause["term"].get(_COMPANY_ID_FIELD) == cid
        ):
            return base

    filters.append({"term": {_COMPANY_ID_FIELD: cid}})
    return base


def query_has_tenant_filter(query: dict[str, Any] | None) -> bool:
    """Return True iff ``query`` carries a non-empty
    ``{"term": {"company_id": <cid>}}`` clause **inside a ``bool.filter``
    block** (filter context).

    Strict semantics — clauses in ``must``, ``must_not``, ``should``, or at
    any other path in the payload do NOT count:

    - ``must_not`` would *exclude* the tenant (worst-case cross-tenant leak).
    - ``should`` is OR semantics (matches OTHER tenants too).
    - ``must`` is scoring context, can be dropped by query rewrites and is
      not the canonical isolation point.
    - Anywhere else (e.g. inside an ``aggs`` clause or a ``nested`` body) is
      not tenant scoping at all.

    Accepts both the top-level shape (``{"query": {...}}``, as sent to
    ES ``body=``) and the bare query shape (``{"bool": {...}}``, as sent
    to ES via the 8.x ``query=`` kwarg).
    """
    if not isinstance(query, dict):
        return False
    root = query.get("query") if "query" in query else query
    return _bool_filter_has_company_id(root)


def _bool_filter_has_company_id(node: Any) -> bool:
    """True iff ``node`` is a bool block (or wraps one) whose ``filter``
    list contains a ``{"term": {"company_id": <non-empty>}}`` clause —
    counting matches inside nested ``bool`` clauses that ALSO live in
    ``filter`` context (so ``bool.filter[bool.filter[...]]`` still passes).
    """
    if not isinstance(node, dict):
        return False
    bool_block = node.get("bool")
    if not isinstance(bool_block, dict):
        return False

    filters = bool_block.get("filter")
    if isinstance(filters, dict):
        filters = [filters]
    if not isinstance(filters, list):
        return False

    for clause in filters:
        if not isinstance(clause, dict):
            continue
        term = clause.get("term")
        if isinstance(term, dict) and _COMPANY_ID_FIELD in term:
            value = term[_COMPANY_ID_FIELD]
            if value not in (None, ""):
                return True
        # Recurse: nested bool whose own filter carries the tenant term
        # is still a filter-context match.
        if "bool" in clause and _bool_filter_has_company_id(clause):
            return True
    return False


# --- metrics --------------------------------------------------------------

_METRICS: dict[str, dict[str, int]] = {}
_OUTCOMES = ("ok", "injected", "missing")

try:  # pragma: no cover — exercised via integration
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import REGISTRY as _PROM_REGISTRY

    _existing = getattr(_PROM_REGISTRY, "_names_to_collectors", {}).get(
        "lia_es_search_tenant_filter_outcome_total"
    )
    if _existing is not None:
        _ES_FILTER_COUNTER = _existing
    else:
        _ES_FILTER_COUNTER = _PromCounter(
            "lia_es_search_tenant_filter_outcome_total",
            "Outcome of tenant_filter enforcement on ES search/count calls (Task #1147).",
            labelnames=("service", "outcome"),
        )
except Exception:  # pragma: no cover — defensive
    _ES_FILTER_COUNTER = None


def _record(service: str, outcome: str) -> None:
    bucket = _METRICS.setdefault(service, {k: 0 for k in _OUTCOMES})
    bucket[outcome] = bucket.get(outcome, 0) + 1
    if _ES_FILTER_COUNTER is not None:
        try:
            _ES_FILTER_COUNTER.labels(service=service, outcome=outcome).inc()
        except Exception:  # pragma: no cover — defensive
            pass


def get_es_tenant_filter_metrics() -> dict[str, dict[str, int]]:
    """Snapshot of the in-memory metric counters (for canary endpoints)."""
    return {svc: dict(buckets) for svc, buckets in _METRICS.items()}


def _reset_es_tenant_filter_metrics_for_tests() -> None:
    """Test-only reset hook."""
    _METRICS.clear()


# --- runtime interceptor --------------------------------------------------


def _is_production() -> bool:
    env = os.getenv("APP_ENV", "development").strip().lower()
    return env in {"production", "prod"}


class TenantAwareElasticsearchClient:
    """Proxy around any Elasticsearch async client that enforces tenant filter.

    Intercepts ``search`` and ``count`` calls; validates that the ``body``
    (or ``query`` kwarg) carries a ``company_id`` term filter. Behaviour on
    violation:

    - **dev / test (default):** raise :class:`MissingTenantFilterError` with
      truncated payload + service tag.
    - **production:** raise ``RuntimeError`` so the request fails loud and
      the on-call alert from sentry/sentinel triggers (S9 in T-1129 plan).

    Other methods (``index``, ``update``, ``delete``, etc.) pass through
    unchanged — those are write paths where ``company_id`` is part of the
    document itself, not the query.

    Construct with ``service`` set to a stable label (e.g.
    ``"candidates_search"``) so metrics are useful.
    """

    _INTERCEPTED = ("search", "count")

    def __init__(self, inner: Any, service: str) -> None:
        self._inner = inner
        self._service = service

    def __getattr__(self, item: str) -> Any:
        # Pass-through for everything that isn't intercepted.
        return getattr(self._inner, item)

    async def search(self, *args: Any, **kwargs: Any) -> Any:
        self._assert_tenant_filter("search", args, kwargs)
        return await self._inner.search(*args, **kwargs)

    async def count(self, *args: Any, **kwargs: Any) -> Any:
        self._assert_tenant_filter("count", args, kwargs)
        return await self._inner.count(*args, **kwargs)

    # -- helpers -----------------------------------------------------------

    def _assert_tenant_filter(
        self,
        op: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        body = kwargs.get("body")
        if body is None and "query" in kwargs:
            # elasticsearch-py 8.x accepts top-level `query=` instead of body.
            body = {"query": kwargs["query"]}
        if body is None and args:
            # Defensive: positional body (rare but supported by some clients).
            body = args[0] if isinstance(args[0], dict) else None

        if query_has_tenant_filter(body):
            _record(self._service, "ok")
            return

        _record(self._service, "missing")
        truncated = repr(body)[:512]
        msg = (
            f"ES {op} on service={self._service!r} dispatched without "
            f"company_id term filter. Wrap the query with "
            f"app.shared.search.with_tenant_filter(query, company_id)."
        )
        details = {"service": self._service, "op": op, "body": truncated}

        if _is_production():
            # Fail-loud, no MissingTenantFilterError type (kept as a
            # canonical-error so callers in dev can `except` it explicitly).
            logger.critical("[es_tenant_filter] %s | details=%s", msg, details)
            raise RuntimeError(msg)
        raise MissingTenantFilterError(msg, details=details)
