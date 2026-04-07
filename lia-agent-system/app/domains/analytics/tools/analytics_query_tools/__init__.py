"""
Analytics query tools package.

Provides function calling capabilities for:
- Pipeline statistics and vacancy funnel analysis
- Candidate comparison and activity summaries
- Pending actions and recruiter performance metrics
- Velocity, efficiency, and comparative metrics
- Workload distribution and bottleneck analysis
- Stakeholder metrics and hiring quality
- Prediction metrics, cost analysis, and trends
- ML predictions, conversion patterns, and smart alerts

All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
from .activity_metrics import get_activity_summary, get_pending_actions
from .financial_trends import get_cost_metrics, get_trends
from .intelligence import get_conversion_patterns, get_ml_predictions, get_smart_alerts
from .pipeline_analytics import compare_candidates, get_pipeline_stats, get_vacancy_funnel
from .quality_metrics import get_hiring_quality, get_prediction_metrics, get_stakeholder_metrics
from .recruiter_performance import (
    get_comparative_metrics,
    get_efficiency_metrics,
    get_recruiter_metrics,
    get_velocity_metrics,
)
from .registry import register_analytics_query_tools
from .workload_analysis import get_bottleneck_analysis, get_workload_distribution

__all__ = [
    "get_pipeline_stats",
    "get_vacancy_funnel",
    "compare_candidates",
    "get_activity_summary",
    "get_pending_actions",
    "get_recruiter_metrics",
    "get_velocity_metrics",
    "get_efficiency_metrics",
    "get_comparative_metrics",
    "get_workload_distribution",
    "get_bottleneck_analysis",
    "get_stakeholder_metrics",
    "get_hiring_quality",
    "get_prediction_metrics",
    "get_cost_metrics",
    "get_trends",
    "get_ml_predictions",
    "get_conversion_patterns",
    "get_smart_alerts",
    "register_analytics_query_tools",
]
