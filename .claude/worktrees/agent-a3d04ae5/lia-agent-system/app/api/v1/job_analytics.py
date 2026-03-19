"""
Job Analytics API - Connects LIA prompt frontend to JobAnalyticsPromptService.

Provides endpoints for job analysis, metrics, comparisons, and AI-powered insights.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.job_analytics_prompt_service import job_analytics_prompt_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-analytics", tags=["job-analytics"])


class CommandInfo(BaseModel):
    id: str
    name: str
    description: str
    required_context: List[str]
    agent: Optional[str] = None


class CommandsResponse(BaseModel):
    commands: List[CommandInfo]


class ExecuteCommandContext(BaseModel):
    job_id: Optional[str] = None
    job_ids: Optional[List[str]] = None


class ExecuteCommandRequest(BaseModel):
    command_id: str = Field(..., description="ID of the command template to execute")
    context: ExecuteCommandContext = Field(default_factory=ExecuteCommandContext)


class NaturalQueryContext(BaseModel):
    job_id: Optional[str] = None
    job_ids: Optional[List[str]] = None
    page: Optional[str] = None


class NaturalQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query about jobs")
    context: NaturalQueryContext = Field(default_factory=NaturalQueryContext)


class ChartData(BaseModel):
    type: str
    title: str
    data: Any


class AnalyticsResultResponse(BaseModel):
    success: bool
    command: str
    agent_used: str
    response: str
    data: Dict[str, Any] = Field(default_factory=dict)
    charts: List[ChartData] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class FunnelMetrics(BaseModel):
    total_candidates: int
    candidates_by_stage: Dict[str, int]
    conversion_rate: Optional[float] = None


class TimeMetrics(BaseModel):
    days_open: int
    new_this_week: int


class QuickInsightsResponse(BaseModel):
    job_id: str
    job_title: str
    status: str
    funnel: FunnelMetrics
    time_in_pipeline: TimeMetrics
    priority: str
    charts: List[ChartData] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CompareJobsRequest(BaseModel):
    job_ids: List[str] = Field(..., min_length=2, description="List of job IDs to compare")


class SuggestionItem(BaseModel):
    action: str
    reason: str
    priority: str
    agent: Optional[str] = None
    command: Optional[str] = None


class SuggestionsResponse(BaseModel):
    job_id: str
    job_title: Optional[str] = None
    suggestions: List[SuggestionItem]
    additional_suggestions: List[str] = Field(default_factory=list)


class BatchAnalyzeRequest(BaseModel):
    job_ids: List[str] = Field(..., min_length=1, description="List of job IDs to analyze")
    analysis_types: List[str] = Field(..., min_length=1, description="Types of analysis to run")


class BatchAnalysisResult(BaseModel):
    job_id: str
    analysis_type: str
    success: bool
    response: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BatchAnalyzeResponse(BaseModel):
    total_jobs: int
    total_analyses: int
    successful: int
    failed: int
    results: List[BatchAnalysisResult]


@router.get("/commands", response_model=CommandsResponse)
async def get_available_commands():
    """
    Returns available analysis commands and templates.
    
    These are predefined analysis types that can be executed via the /execute endpoint.
    """
    try:
        commands = job_analytics_prompt_service.get_available_commands()
        return CommandsResponse(
            commands=[CommandInfo(**cmd) for cmd in commands]
        )
    except Exception as e:
        logger.error(f"Error getting available commands: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=AnalyticsResultResponse)
async def execute_command(
    request: ExecuteCommandRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a predefined command template.
    
    Pass the command_id and required context (job_id or job_ids based on the command).
    """
    try:
        context = request.context.model_dump(exclude_none=True)
        
        result = await job_analytics_prompt_service.execute_command(
            command_id=request.command_id,
            context=context,
            db=db
        )
        
        return AnalyticsResultResponse(
            success=result.success,
            command=result.command,
            agent_used=result.agent_used,
            response=result.response,
            data=result.data,
            charts=[ChartData(**c) for c in result.charts] if result.charts else [],
            suggestions=result.suggestions,
            metadata=result.metadata,
            error=result.error
        )
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/natural-query", response_model=AnalyticsResultResponse)
async def natural_query(
    request: NaturalQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles natural language queries about jobs.
    
    Routes the query to the appropriate specialized agent based on intent detection.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        context = request.context.model_dump(exclude_none=True)
        
        result = await job_analytics_prompt_service.analyze_natural_query(
            query=request.query,
            context=context,
            db=db
        )
        
        return AnalyticsResultResponse(
            success=result.success,
            command=result.command,
            agent_used=result.agent_used,
            response=result.response,
            data=result.data,
            charts=[ChartData(**c) for c in result.charts] if result.charts else [],
            suggestions=result.suggestions,
            metadata=result.metadata,
            error=result.error
        )
    except Exception as e:
        logger.error(f"Error processing natural query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-insights/{job_id}", response_model=QuickInsightsResponse)
async def get_quick_insights(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns quick metrics card data for a job.
    
    Provides funnel data, time in pipeline, quality indicators, and suggestions.
    """
    try:
        result = await job_analytics_prompt_service.get_job_quick_insights(
            job_id=job_id,
            db=db
        )
        
        if not result.success:
            raise HTTPException(status_code=404, detail=result.error or "Job not found")
        
        data = result.data
        
        return QuickInsightsResponse(
            job_id=data.get("job_id", job_id),
            job_title=data.get("job_title", ""),
            status=data.get("status", "unknown"),
            funnel=FunnelMetrics(
                total_candidates=data.get("total_candidates", 0),
                candidates_by_stage=data.get("candidates_by_stage", {}),
                conversion_rate=data.get("overall_conversion_rate")
            ),
            time_in_pipeline=TimeMetrics(
                days_open=data.get("days_open", 0),
                new_this_week=data.get("new_candidates_this_week", 0)
            ),
            priority=data.get("priority", "normal"),
            charts=[ChartData(**c) for c in result.charts] if result.charts else [],
            suggestions=result.suggestions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quick insights for job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=AnalyticsResultResponse)
async def compare_jobs(
    request: CompareJobsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compares multiple jobs.
    
    Returns comparison table data with metrics for each job.
    """
    try:
        result = await job_analytics_prompt_service.get_multi_job_comparison(
            job_ids=request.job_ids,
            db=db
        )
        
        return AnalyticsResultResponse(
            success=result.success,
            command=result.command,
            agent_used=result.agent_used,
            response=result.response,
            data=result.data,
            charts=[ChartData(**c) for c in result.charts] if result.charts else [],
            suggestions=result.suggestions,
            metadata=result.metadata,
            error=result.error
        )
    except Exception as e:
        logger.error(f"Error comparing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{job_id}", response_model=SuggestionsResponse)
async def get_suggestions(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns AI-suggested next actions for the job.
    
    Analyzes job state and provides prioritized recommendations.
    """
    try:
        result = await job_analytics_prompt_service.suggest_next_actions(
            job_id=job_id,
            db=db
        )
        
        if not result.success:
            raise HTTPException(status_code=404, detail=result.error or "Job not found")
        
        data = result.data
        priority_actions = data.get("priority_actions", [])
        
        suggestions = [
            SuggestionItem(
                action=action.get("action", ""),
                reason=action.get("description", ""),
                priority=action.get("priority", "medium"),
                agent=None,
                command=action.get("command")
            )
            for action in priority_actions
        ]
        
        return SuggestionsResponse(
            job_id=data.get("job_id", job_id),
            job_title=data.get("job_title"),
            suggestions=suggestions,
            additional_suggestions=data.get("additional_suggestions", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions for job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze(
    request: BatchAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Runs multiple analyses on multiple jobs.
    
    For bulk operations - executes specified analysis types for each job.
    """
    available_commands = job_analytics_prompt_service.get_available_commands()
    valid_commands = {cmd["id"] for cmd in available_commands}
    
    invalid_types = [t for t in request.analysis_types if t not in valid_commands]
    if invalid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis types: {invalid_types}. Valid types: {list(valid_commands)}"
        )
    
    results: List[BatchAnalysisResult] = []
    successful = 0
    failed = 0
    
    async def analyze_job(job_id: str, analysis_type: str) -> BatchAnalysisResult:
        try:
            result = await job_analytics_prompt_service.execute_command(
                command_id=analysis_type,
                context={"job_id": job_id},
                db=db
            )
            
            return BatchAnalysisResult(
                job_id=job_id,
                analysis_type=analysis_type,
                success=result.success,
                response=result.response,
                data=result.data,
                error=result.error
            )
        except Exception as e:
            logger.error(f"Error in batch analyze for job {job_id}, type {analysis_type}: {e}")
            return BatchAnalysisResult(
                job_id=job_id,
                analysis_type=analysis_type,
                success=False,
                response=f"Error: {str(e)}",
                data={},
                error=str(e)
            )
    
    tasks = []
    for job_id in request.job_ids:
        for analysis_type in request.analysis_types:
            tasks.append(analyze_job(job_id, analysis_type))
    
    results = await asyncio.gather(*tasks)
    
    for result in results:
        if result.success:
            successful += 1
        else:
            failed += 1
    
    return BatchAnalyzeResponse(
        total_jobs=len(request.job_ids),
        total_analyses=len(results),
        successful=successful,
        failed=failed,
        results=list(results)
    )
