"""
Query Tools - Backward-compatible shim module.

This module was decomposed into domain-specific files:
- app/domains/sourcing/tools/query_tools.py (sourcing domain)
- app/domains/job_management/tools/query_tools.py (job management domain)
- app/domains/analytics/tools/analytics_query_tools.py (analytics domain)

All functions are re-exported here for backward compatibility.
"""
import logging

from app.domains.sourcing.tools.query_tools import (  # noqa: F401
    search_candidates,
    get_candidate_details,
    get_candidate_stats,
    get_candidate_history,
    get_talent_quality,
    get_talent_engagement,
    get_talent_availability,
    get_diversity_metrics,
    get_market_benchmarks,
    register_sourcing_query_tools,
)

from app.domains.job_management.tools.query_tools import (  # noqa: F401
    search_jobs,
    get_job_details,
    get_job_velocity,
    get_job_quality_metrics,
    get_job_benchmark,
    register_job_management_query_tools,
)

from app.domains.analytics.tools.analytics_query_tools import (  # noqa: F401
    get_pipeline_stats,
    get_vacancy_funnel,
    compare_candidates,
    get_activity_summary,
    get_pending_actions,
    get_recruiter_metrics,
    get_velocity_metrics,
    get_efficiency_metrics,
    get_comparative_metrics,
    get_workload_distribution,
    get_bottleneck_analysis,
    get_stakeholder_metrics,
    get_hiring_quality,
    get_prediction_metrics,
    get_cost_metrics,
    get_trends,
    get_ml_predictions,
    get_conversion_patterns,
    get_smart_alerts,
    register_analytics_query_tools,
)

logger = logging.getLogger(__name__)


def register_query_tools() -> None:
    """Register all query tools from all domains."""
    register_sourcing_query_tools()
    register_job_management_query_tools()
    register_analytics_query_tools()
    logger.info("✅ Registered all 33 query tools (sourcing: 9, job_management: 5, analytics: 19)")
