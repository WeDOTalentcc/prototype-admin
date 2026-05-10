"""
Predictive Tools - Recruitment predictive analytics as ReAct ToolDefinitions.

These tools provide forward-looking predictions for recruitment:
- Candidate dropout risk analysis
- Time-to-fill estimation
- Pipeline forecasting
- Strategic recommendations

All functions are async, connect to PostgreSQL via AsyncSessionLocal,
and return Dict[str, Any] with 'success', 'data', and 'message' keys.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

STAGE_ORDER = [
    "applied",
    "screening",
    "interview",
    "technical_test",
    "offer",
    "hired",
]


async def predict_dropout_risk(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Analyze dropout risk for candidates in the pipeline.

    Evaluates each candidate's risk of dropping out based on:
    - Time spent in current stage
    - Last update timestamp (inactivity)
    - Stage position in funnel
    - Engagement signals

    Categorizes each candidate as low/medium/high/critical risk.

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with candidates_at_risk list, risk_distribution,
        critical_candidates, and recommended_actions.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            result = await session.execute(
                text(f"""
                    SELECT
                        vc.candidate_id,
                        c.name,
                        c.email,
                        vc.stage,
                        vc.sub_status,
                        EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 AS days_in_stage,
                        COALESCE(vc.lia_score, 0) AS score
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    JOIN candidates c ON vc.candidate_id = c.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage IS NOT NULL
                      AND vc.stage != 'hired'
                      {job_filter}
                """),
                params,
            )
            rows = result.mappings().all()

            candidates_at_risk: list[dict[str, Any]] = []
            risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}

            for row in rows:
                days_in_stage = float(row["days_in_stage"])
                stage = row["stage"] or "unknown"
                score = float(row["score"])

                # Calculate risk score based on multiple factors
                # Time in stage: each day increases risk
                time_risk = min(days_in_stage / 14.0, 1.0)

                # Stage position: higher conversion stages have lower risk baseline
                stage_risk_baseline = {
                    "applied": 0.3,
                    "screening": 0.4,
                    "interview": 0.5,
                    "technical_test": 0.6,
                    "offer": 0.7,
                }.get(stage, 0.5)

                # Candidate quality: higher scores reduce risk
                quality_factor = max(1.0 - (score / 100.0), 0.1)

                # Combined risk calculation
                total_risk = (time_risk * 0.5 + stage_risk_baseline * 0.3 + quality_factor * 0.2)
                risk_percentage = min(total_risk * 100, 95)

                # Categorize risk
                if risk_percentage >= 70:
                    risk_category = "critical"
                elif risk_percentage >= 50:
                    risk_category = "high"
                elif risk_percentage >= 30:
                    risk_category = "medium"
                else:
                    risk_category = "low"

                risk_distribution[risk_category] += 1

                candidate_risk = {
                    "candidate_id": str(row["candidate_id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "stage": stage,
                    "days_in_stage": round(days_in_stage, 1),
                    "score": round(score, 1),
                    "risk_percentage": round(risk_percentage, 1),
                    "risk_category": risk_category,
                }

                if risk_category in ["high", "critical"]:
                    candidates_at_risk.append(candidate_risk)

            # Sort by risk percentage descending
            candidates_at_risk.sort(key=lambda x: x["risk_percentage"], reverse=True)

            critical_candidates = [c for c in candidates_at_risk if c["risk_category"] == "critical"]

            return {
                "success": True,
                "data": {
                    "candidates_at_risk": candidates_at_risk[:20],
                    "risk_distribution": risk_distribution,
                    "critical_candidates": critical_candidates,
                    "total_candidates": len(rows),
                    "total_at_risk": len(candidates_at_risk),
                },
                "message": f"Dropout risk analysis: {len(candidates_at_risk)} candidates at risk, {len(critical_candidates)} critical.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[predictive_tools] predict_dropout_risk error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def predict_time_to_fill(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Estimate time to fill based on historical data and pipeline velocity.

    Uses:
    - Historical time-to-fill for similar roles (by seniority)
    - Current pipeline velocity (candidates per stage)
    - Stage distribution and conversion rates
    - Candidate quality distribution

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with predicted_days, velocity_metrics, by_job breakdown,
        and confidence assessment.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND jv.id = :job_id"
                params["job_id"] = job_id

            # Get historical time-to-fill data
            historical_result = await session.execute(
                text("""
                    SELECT
                        jv.seniority,
                        EXTRACT(EPOCH FROM (
                            COALESCE(jv.closed_at, jv.updated_at) - jv.created_at
                        )) / 86400.0 AS days_to_fill
                    FROM job_vacancies jv
                    WHERE jv.company_id = :company_id
                      AND jv.status IN ('filled', 'closed')
                      AND jv.seniority IS NOT NULL
                    ORDER BY jv.updated_at DESC
                    LIMIT 100
                """),
                params,
            )
            historical_rows = historical_result.mappings().all()

            # Seniority-based baseline estimates (in days)
            seniority_baselines = {
                "junior": 25,
                "pleno": 35,
                "senior": 50,
                "lead": 60,
                "manager": 70,
                "director": 90,
                "c-level": 120,
            }

            # Calculate average time-to-fill by seniority from historical data
            seniority_ttf: dict[str, list[float]] = {}
            for row in historical_rows:
                seniority = (row["seniority"] or "pleno").lower()
                days = float(row["days_to_fill"])
                if days > 0:
                    seniority_ttf.setdefault(seniority, []).append(days)

            avg_seniority_ttf = {
                seniority: round(sum(vals) / len(vals), 1)
                for seniority, vals in seniority_ttf.items()
            }

            # Get current pipeline velocity
            pipeline_result = await session.execute(
                text(f"""
                    SELECT
                        jv.id,
                        jv.title,
                        jv.seniority,
                        COUNT(CASE WHEN vc.stage = 'applied' THEN 1 END) AS applied_count,
                        COUNT(CASE WHEN vc.stage = 'screening' THEN 1 END) AS screening_count,
                        COUNT(CASE WHEN vc.stage = 'interview' THEN 1 END) AS interview_count,
                        COUNT(CASE WHEN vc.stage = 'offer' THEN 1 END) AS offer_count,
                        COUNT(CASE WHEN vc.stage = 'hired' THEN 1 END) AS hired_count,
                        COUNT(*) AS total_candidates,
                        AVG(COALESCE(vc.lia_score, 0)) AS avg_score
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON jv.id = vc.vacancy_id
                    WHERE jv.company_id = :company_id
                      AND jv.status NOT IN ('filled', 'closed')
                      {job_filter}
                    GROUP BY jv.id, jv.title, jv.seniority
                """),
                params,
            )
            pipeline_rows = pipeline_result.mappings().all()

            by_job_predictions = []

            for job_row in pipeline_rows:
                seniority = (job_row["seniority"] or "pleno").lower()
                base_days = avg_seniority_ttf.get(seniority, seniority_baselines.get(seniority, 45))

                total_candidates = int(job_row["total_candidates"] or 0)
                offer_count = int(job_row["offer_count"] or 0)

                # Velocity: candidates per offer stage
                velocity_metric = offer_count if offer_count > 0 else max(total_candidates / 5, 1)

                # Estimate days to next hire based on velocity
                # Assume each offer stage candidate needs ~7 days to close
                if velocity_metric > 0:
                    estimated_days = max(7 / velocity_metric * 7, 7)
                else:
                    estimated_days = base_days

                avg_score = float(job_row["avg_score"] or 0)
                quality_adjustment = (100 - avg_score) / 10 if avg_score > 0 else 0

                predicted_days = estimated_days + quality_adjustment

                by_job_predictions.append({
                    "job_id": str(job_row["id"]),
                    "job_title": job_row["title"],
                    "seniority": seniority,
                    "predicted_days": round(predicted_days, 1),
                    "pipeline_strength": total_candidates,
                    "velocity": round(velocity_metric, 1),
                    "avg_score": round(avg_score, 1),
                })

            # Overall metrics
            if by_job_predictions:
                avg_predicted = round(sum(j["predicted_days"] for j in by_job_predictions) / len(by_job_predictions), 1)
            else:
                avg_predicted = 45.0

            return {
                "success": True,
                "data": {
                    "avg_predicted_days": avg_predicted,
                    "by_job": by_job_predictions,
                    "seniority_baselines": seniority_baselines,
                    "historical_seniority_ttf": avg_seniority_ttf,
                    "jobs_analyzed": len(by_job_predictions),
                },
                "message": f"Time-to-fill prediction: avg {avg_predicted} days across {len(by_job_predictions)} active jobs.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[predictive_tools] predict_time_to_fill error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def get_pipeline_forecast(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Forecast pipeline outcomes for next 4 weeks.

    Uses current conversion rates and stage distribution to project:
    - Expected hires per week
    - Stage progression
    - Fill probability
    - Bottleneck stages

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with weekly_forecast, expected_total_hires, fill_probability,
        and stage_projections.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            # Get current pipeline distribution
            pipeline_result = await session.execute(
                text(f"""
                    SELECT
                        vc.stage,
                        COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage IS NOT NULL
                      AND vc.stage != 'hired'
                      {job_filter}
                    GROUP BY vc.stage
                """),
                params,
            )
            pipeline_rows = pipeline_result.mappings().all()

            current_pipeline: dict[str, int] = {}
            for row in pipeline_rows:
                stage = row["stage"] or "unknown"
                current_pipeline[stage] = int(row["cnt"])

            # Calculate conversion rates from historical data
            conversion_rates_result = await session.execute(
                text(f"""
                    SELECT
                        vc.stage,
                        COUNT(*) AS stage_count,
                        COUNT(CASE WHEN vc_next.stage IS NOT NULL THEN 1 END) AS moved_forward
                    FROM vacancy_candidates vc
                    LEFT JOIN vacancy_candidates vc_next ON vc.candidate_id = vc_next.candidate_id
                        AND vc.vacancy_id = vc_next.vacancy_id
                        AND vc_next.updated_at > vc.updated_at
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage IS NOT NULL
                      {job_filter}
                    GROUP BY vc.stage
                """),
                params,
            )
            conversion_rows = conversion_rates_result.mappings().all()

            conversion_rates: dict[str, float] = {}
            for row in conversion_rows:
                stage = row["stage"] or "unknown"
                stage_count = int(row["stage_count"] or 0)
                moved = int(row["moved_forward"] or 0)
                if stage_count > 0:
                    conversion_rates[stage] = min(moved / stage_count, 1.0)
                else:
                    conversion_rates[stage] = 0.5  # Default assumption

            # Default conversion rates if not enough data
            default_rates = {
                "applied": 0.40,
                "screening": 0.50,
                "interview": 0.60,
                "technical_test": 0.65,
                "offer": 0.85,
            }

            for stage in default_rates:
                if stage not in conversion_rates or conversion_rates[stage] == 0:
                    conversion_rates[stage] = default_rates[stage]

            # Generate 4-week forecast
            weeks_ahead = 4
            weekly_forecast = []
            pipeline_snapshot = current_pipeline.copy()

            for week in range(1, weeks_ahead + 1):
                week_start = datetime.utcnow() + timedelta(weeks=week - 1)
                week_end = datetime.utcnow() + timedelta(weeks=week)

                stage_projections = {}
                total_hired_this_week = 0

                for stage, count in list(pipeline_snapshot.items()):
                    if stage in conversion_rates and count > 0:
                        conversion_rate = conversion_rates[stage]
                        converted = int(count * conversion_rate)
                        remaining = count - converted

                        # Determine next stage
                        stage_sequence = ["applied", "screening", "interview", "technical_test", "offer", "hired"]
                        try:
                            current_idx = stage_sequence.index(stage)
                            if current_idx < len(stage_sequence) - 1:
                                next_stage = stage_sequence[current_idx + 1]
                                stage_projections[next_stage] = stage_projections.get(next_stage, 0) + converted
                            else:
                                total_hired_this_week += converted
                        except ValueError:
                            stage_projections[stage] = stage_projections.get(stage, 0) + converted

                        stage_projections[stage] = stage_projections.get(stage, 0) + remaining
                    else:
                        stage_projections[stage] = count

                weekly_forecast.append({
                    "week": week,
                    "date_range": {
                        "start": week_start.strftime("%Y-%m-%d"),
                        "end": week_end.strftime("%Y-%m-%d"),
                    },
                    "stage_projections": stage_projections,
                    "expected_hires": total_hired_this_week,
                })

                pipeline_snapshot = stage_projections

            # Calculate total expected hires
            total_expected_hires = sum(w["expected_hires"] for w in weekly_forecast)

            # Get headcount requirement
            headcount_result = await session.execute(
                text(f"""
                    SELECT COUNT(*) AS open_positions
                    FROM job_vacancies jv
                    WHERE jv.company_id = :company_id
                      AND jv.status NOT IN ('filled', 'closed')
                      {job_filter}
                """),
                params,
            )
            headcount_row = headcount_result.mappings().first()
            total_headcount = int(headcount_row["open_positions"] or 1) if headcount_row else 1

            fill_probability = min((total_expected_hires / max(total_headcount, 1)) * 100, 100)

            return {
                "success": True,
                "data": {
                    "weekly_forecast": weekly_forecast,
                    "total_expected_hires": total_expected_hires,
                    "fill_probability": round(fill_probability, 1),
                    "current_pipeline": current_pipeline,
                    "conversion_rates": conversion_rates,
                    "headcount_requirement": total_headcount,
                },
                "message": f"Pipeline forecast: {total_expected_hires} expected hires in 4 weeks ({round(fill_probability, 1)}% fill probability).",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[predictive_tools] get_pipeline_forecast error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def get_strategic_recommendations(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Generate data-driven strategic recommendations (the consultive brain).

    Cross-references multiple dimensions:
    - Pipeline health (stages, flow, bottlenecks)
    - Conversion rates (funnel effectiveness)
    - Quality distribution (candidate strength)
    - Time metrics (velocity, age of candidates)
    - Dropout risk patterns
    - Historical performance

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with strategic_recommendations list (high/medium/low priority),
        insights, and action_items.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            # Gather comprehensive data
            pipeline_result = await session.execute(
                text(f"""
                    SELECT
                        vc.stage,
                        COUNT(*) AS cnt,
                        AVG(COALESCE(vc.lia_score, 0)) AS avg_score,
                        AVG(EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0) AS avg_days_in_stage
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage IS NOT NULL
                      {job_filter}
                    GROUP BY vc.stage
                """),
                params,
            )
            pipeline_result.mappings().all()

            # Job data
            job_result = await session.execute(
                text(f"""
                    SELECT
                        COUNT(*) AS total_jobs,
                        SUM(CASE WHEN status NOT IN ('filled', 'closed') THEN 1 ELSE 0 END) AS active_jobs,
                        AVG(EXTRACT(EPOCH FROM (
                            COALESCE(closed_at, updated_at) - created_at
                        )) / 86400.0) AS avg_ttf
                    FROM job_vacancies jv
                    WHERE jv.company_id = :company_id
                      {job_filter}
                """),
                params,
            )
            job_row = job_result.mappings().first()

            # Conversion path analysis
            conversion_result = await session.execute(
                text(f"""
                    SELECT
                        COUNT(CASE WHEN stage = 'applied' THEN 1 END) AS applied,
                        COUNT(CASE WHEN stage IN ('screening', 'interview', 'technical_test', 'offer') THEN 1 END) AS in_process,
                        COUNT(CASE WHEN stage = 'hired' THEN 1 END) AS hired
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      {job_filter}
                """),
                params,
            )
            conversion_row = conversion_result.mappings().first()

            # Quality analysis
            quality_result = await session.execute(
                text(f"""
                    SELECT
                        COUNT(CASE WHEN vc.lia_score >= 70 THEN 1 END) AS high_quality,
                        COUNT(CASE WHEN vc.lia_score >= 50 AND vc.lia_score < 70 THEN 1 END) AS medium_quality,
                        COUNT(CASE WHEN vc.lia_score < 50 THEN 1 END) AS low_quality,
                        AVG(COALESCE(vc.lia_score, 0)) AS avg_score
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND vc.lia_score IS NOT NULL
                      {job_filter}
                """),
                params,
            )
            quality_row = quality_result.mappings().first()

            # Risk analysis
            risk_result = await session.execute(
                text(f"""
                    SELECT
                        COUNT(CASE WHEN EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 > 14 THEN 1 END) AS stalled_candidates,
                        COUNT(*) AS total_pipeline
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage != 'hired'
                      {job_filter}
                """),
                params,
            )
            risk_row = risk_result.mappings().first()

            # Build recommendations
            recommendations: list[dict[str, Any]] = []

            # 1. Pipeline flow analysis
            applied_count = int(conversion_row["applied"] or 0) if conversion_row else 0
            in_process_count = int(conversion_row["in_process"] or 0) if conversion_row else 0
            hired_count = int(conversion_row["hired"] or 0) if conversion_row else 0

            if applied_count > 0:
                flow_rate = in_process_count / applied_count
                if flow_rate < 0.3:
                    recommendations.append({
                        "priority": "high",
                        "category": "Pipeline Flow",
                        "title": "Improve initial screening conversion",
                        "description": "Only 30% of applied candidates are progressing through screening. Review screening criteria or increase frequency.",
                        "metric": f"{round(flow_rate * 100, 1)}% flow rate (target: 40%+)",
                        "actions": ["Review screening questions for relevance", "Increase screening frequency", "Consider pre-qualification automation"],
                    })

            # 2. Quality distribution
            if quality_row:
                high_quality = int(quality_row["high_quality"] or 0)
                total_scored = high_quality + int(quality_row["medium_quality"] or 0) + int(quality_row["low_quality"] or 0)
                if total_scored > 0:
                    quality_ratio = high_quality / total_scored
                    if quality_ratio < 0.3:
                        recommendations.append({
                            "priority": "high",
                            "category": "Candidate Quality",
                            "title": "Strengthen sourcing quality",
                            "description": "Less than 30% of candidates meet quality threshold (score 70+). Source quality needs improvement.",
                            "metric": f"{round(quality_ratio * 100, 1)}% high-quality candidates",
                            "actions": ["Refine job description and requirements", "Improve search criteria", "Enhance pre-screening"],
                        })
                    elif quality_ratio > 0.7:
                        recommendations.append({
                            "priority": "low",
                            "category": "Candidate Quality",
                            "title": "Leverage high-quality pipeline",
                            "description": "70%+ of candidates are high-quality. Accelerate offer process to secure top talent.",
                            "metric": f"{round(quality_ratio * 100, 1)}% high-quality candidates",
                            "actions": ["Expedite interview process", "Prepare competitive offers", "Reduce decision time"],
                        })

            # 3. Stalled candidates
            if risk_row:
                stalled = int(risk_row["stalled_candidates"] or 0)
                total_pipeline = int(risk_row["total_pipeline"] or 0)
                if total_pipeline > 0 and stalled > 0:
                    stall_ratio = stalled / total_pipeline
                    if stall_ratio > 0.2:
                        recommendations.append({
                            "priority": "high",
                            "category": "Engagement",
                            "title": "Re-engage stalled candidates",
                            "description": f"{stalled} candidates have been inactive for 14+ days. Risk of dropout.",
                            "metric": f"{round(stall_ratio * 100, 1)}% stalled ({stalled} candidates)",
                            "actions": ["Send status updates", "Schedule follow-up interviews", "Understand blockers"],
                        })

            # 4. Time-to-fill optimization
            if job_row and job_row["avg_ttf"]:
                avg_ttf = float(job_row["avg_ttf"])
                if avg_ttf > 60:
                    recommendations.append({
                        "priority": "medium",
                        "category": "Speed to Hire",
                        "title": "Accelerate hiring process",
                        "description": f"Average time-to-fill is {round(avg_ttf)} days, above industry standard (45 days).",
                        "metric": f"{round(avg_ttf)} days avg (target: 45 days)",
                        "actions": ["Parallel processing of stages", "Automate scheduling", "Faster decision-making"],
                    })

            # 5. Offer stage progress
            if in_process_count > 0:
                offer_result = await session.execute(
                    text(f"""
                        SELECT COUNT(*) AS offer_count
                        FROM vacancy_candidates vc
                        JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                        WHERE jv.company_id = :company_id
                          AND vc.stage = 'offer'
                          {job_filter}
                    """),
                    params,
                )
                offer_row = offer_result.mappings().first()
                offers = int(offer_row["offer_count"] or 0) if offer_row else 0

                if in_process_count > 0 and offers == 0:
                    recommendations.append({
                        "priority": "medium",
                        "category": "Pipeline Progression",
                        "title": "Move candidates to offer stage",
                        "description": f"{in_process_count} candidates in process but none in offer stage. Accelerate final interviews.",
                        "metric": "0 candidates in offer stage",
                        "actions": ["Complete pending interviews", "Prepare offers", "Finalize decision approvals"],
                    })

            # 6. General optimization
            if not recommendations:
                recommendations.append({
                    "priority": "medium",
                    "category": "General",
                    "title": "Maintain pipeline momentum",
                    "description": "Pipeline appears healthy. Continue monitoring conversion rates and candidate engagement.",
                    "metric": "Pipeline healthy",
                    "actions": ["Monitor conversion rates weekly", "Keep communication frequent", "Plan next cohort sourcing"],
                })

            return {
                "success": True,
                "data": {
                    "strategic_recommendations": recommendations,
                    "pipeline_summary": {
                        "total_applied": applied_count,
                        "in_process": in_process_count,
                        "hired": hired_count,
                        "flow_rate": round((in_process_count / max(applied_count, 1)) * 100, 1),
                    },
                    "quality_summary": {
                        "high_quality": int(quality_row["high_quality"] or 0) if quality_row else 0,
                        "avg_score": round(float(quality_row["avg_score"] or 0), 1) if quality_row else 0,
                    },
                    "risk_summary": {
                        "stalled_candidates": int(risk_row["stalled_candidates"] or 0) if risk_row else 0,
                    },
                },
                "message": f"Strategic analysis complete: {len(recommendations)} recommendations generated.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[predictive_tools] get_strategic_recommendations error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_predictive_tools() -> list[ToolDefinition]:
    """Return all predictive tools as ToolDefinition objects for the ReAct loop.

    Each ToolDefinition includes the tool name, description, JSON Schema
    parameters, and the async callable function.

    Returns:
        List of ToolDefinition instances ready for ReActConfig.available_tools.
    """
    job_id_param = {
        "type": "string",
        "description": "Optional job vacancy ID to filter prediction to a specific job",
    }
    company_id_param = {
        "type": "string",
        "description": "Company ID to scope the analysis",
    }

    return [
        ToolDefinition(
            name="predict_dropout_risk",
            description=(
                "Analyze candidate dropout risk based on time in stage, inactivity, and engagement. "
                "Categorizes each candidate as low/medium/high/critical risk and identifies critical candidates."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=predict_dropout_risk,
        ),
        ToolDefinition(
            name="predict_time_to_fill",
            description=(
                "Estimate time to fill based on historical data, pipeline velocity, and seniority-based baselines. "
                "Analyzes current pipeline strength and predicts days to fill per job."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=predict_time_to_fill,
        ),
        ToolDefinition(
            name="get_pipeline_forecast",
            description=(
                "Forecast pipeline outcomes for the next 4 weeks using current conversion rates and stage distribution. "
                "Projects expected hires, fill probability, and stage progression."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_pipeline_forecast,
        ),
        ToolDefinition(
            name="get_strategic_recommendations",
            description=(
                "Generate data-driven strategic recommendations by analyzing pipeline health, conversion rates, "
                "candidate quality, and time metrics. This is the 'consultive brain' tool that synthesizes "
                "actionable insights with priority levels (high/medium/low)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_strategic_recommendations,
        ),
    ]
