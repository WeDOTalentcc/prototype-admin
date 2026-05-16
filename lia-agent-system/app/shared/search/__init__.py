"""Tenant-aware search utilities (Task #1147).

Canonical wrappers + interceptors that guarantee every Elasticsearch query
emitted by the backend carries a ``company_id`` term filter. See
``tenant_aware_es_query`` for the public API.
"""
from __future__ import annotations

from app.shared.search.tenant_aware_es_query import (
    ConflictingTenantFilterError,
    MissingTenantFilterError,
    TenantAwareElasticsearchClient,
    get_es_tenant_filter_metrics,
    query_has_tenant_filter,
    with_tenant_filter,
)

__all__ = [
    "ConflictingTenantFilterError",
    "MissingTenantFilterError",
    "TenantAwareElasticsearchClient",
    "get_es_tenant_filter_metrics",
    "query_has_tenant_filter",
    "with_tenant_filter",
]
