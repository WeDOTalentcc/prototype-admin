"""
TDD Red tests for P2-4: Query tools multi-tenancy — every query tool handler must be
wrapped with @tool_handler (fail-closed ContextVar enforcement).
These tests FAIL until @tool_handler is added to the listed functions.
"""
import importlib
import pytest

QUERY_TOOL_MODULES = [
    (
        "app.domains.analytics.tools.analytics_query_tools.pipeline_analytics",
        "get_pipeline_stats",
    ),
    (
        "app.domains.analytics.tools.analytics_query_tools.pipeline_analytics",
        "get_vacancy_funnel",
    ),
    (
        "app.domains.analytics.tools.analytics_query_tools.activity_metrics",
        "get_activity_summary",
    ),
    ("app.domains.sourcing.tools.query_tools", "get_candidate_details"),
    ("app.domains.sourcing.tools.query_tools", "search_candidates"),
    ("app.domains.job_management.tools.query_tools", "get_job_details"),
    ("app.domains.job_management.tools.query_tools", "search_jobs"),
]


def test_query_tools_have_tool_handler_decorator():
    """Query tool handlers must be wrapped with @tool_handler (fail-closed multi-tenancy)."""
    for module_path, fn_name in QUERY_TOOL_MODULES:
        try:
            mod = importlib.import_module(module_path)
        except ModuleNotFoundError:
            pytest.skip(f"Module {module_path} not found — skip")
        fn = getattr(mod, fn_name, None)
        if fn is None:
            pytest.skip(f"{fn_name} not found in {module_path}")
        assert hasattr(fn, "_tool_handler_wrapped") or hasattr(fn, "__tool_handler__"), (
            f"[P2-4] {module_path}.{fn_name} is missing @tool_handler decorator. "
            "Add @tool_handler('domain') before the function definition. "
            "This enforces fail-closed multi-tenancy via ContextVar."
        )
