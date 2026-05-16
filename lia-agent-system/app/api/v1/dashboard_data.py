
"""
Dashboard Data API endpoints with fictitious data for visualization.
"""
from datetime import datetime
from enum import Enum, StrEnum

from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class TrendDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class StrategicIndicator(BaseModel):
    id: str
    name: str
    value: float
    unit: str
    target: float | None = None
    previous_value: float | None = None
    trend: TrendDirection
    trend_percentage: float
    category: str
    description: str | None = None


class StrategicIndicatorsResponse(BaseModel):
    indicators: list[StrategicIndicator]
    period: str
    generated_at: datetime


class FunnelStage(BaseModel):
    stage_name: str
    stage_order: int
    count: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_in_stage_days: float


class FunnelPerformanceResponse(BaseModel):
    stages: list[FunnelStage]
    total_candidates: int
    overall_conversion_rate: float
    period: str
    generated_at: datetime


class ChannelPerformance(BaseModel):
    channel_name: str
    candidates_count: int
    percentage: float
    quality_score: float
    conversion_rate: float
    cost_per_hire: float
    avg_time_to_hire_days: int


class ChannelPerformanceResponse(BaseModel):
    channels: list[ChannelPerformance]
    total_candidates: int
    period: str
    generated_at: datetime


class RecruiterPerformance(BaseModel):
    recruiter_id: str
    recruiter_name: str
    avatar_url: str | None = None
    positions_filled: int
    positions_target: int
    candidates_screened: int
    interviews_conducted: int
    conversion_rate: float
    avg_time_to_fill_days: float
    quality_score: float
    rank: int


class RecruiterRankingResponse(BaseModel):
    recruiters: list[RecruiterPerformance]
    period: str
    generated_at: datetime


class Prediction(BaseModel):
    prediction_id: str
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    timeframe: str
    trend: TrendDirection
    factors: list[str]
    recommendation: str | None = None


class PredictionsResponse(BaseModel):
    predictions: list[Prediction]
    model_version: str
    generated_at: datetime


@router.get("/strategic-indicators", response_model=StrategicIndicatorsResponse)
async def get_strategic_indicators(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get strategic KPI indicators for the business dashboard."""
    indicators = [
        StrategicIndicator(
            id="open_positions",
            name="Vagas Abertas",
            value=45,
            unit="vagas",
            target=50,
            previous_value=42,
            trend=TrendDirection.UP,
            trend_percentage=7.1,
            category="recruitment",
            description="Total de vagas atualmente em aberto"
        ),
        StrategicIndicator(
            id="active_candidates",
            name="Candidatos Ativos",
            value=1247,
            unit="candidatos",
            target=1500,
            previous_value=1180,
            trend=TrendDirection.UP,
            trend_percentage=5.7,
            category="pipeline",
            description="Candidatos em processo ativo"
        ),
        StrategicIndicator(
            id="monthly_hires",
            name="Contratações no Mês",
            value=12,
            unit="contratações",
            target=15,
            previous_value=10,
            trend=TrendDirection.UP,
            trend_percentage=20.0,
            category="recruitment",
            description="Número de contratações realizadas no mês"
        ),
        StrategicIndicator(
            id="avg_time_to_hire",
            name="Tempo Médio de Contratação",
            value=28,
            unit="dias",
            target=25,
            previous_value=32,
            trend=TrendDirection.DOWN,
            trend_percentage=-12.5,
            category="efficiency",
            description="Tempo médio desde abertura até contratação"
        ),
        StrategicIndicator(
            id="cost_per_hire",
            name="Custo por Contratação",
            value=4500,
            unit="R$",
            target=4000,
            previous_value=4800,
            trend=TrendDirection.DOWN,
            trend_percentage=-6.25,
            category="financial",
            description="Custo médio por contratação realizada"
        ),
        StrategicIndicator(
            id="conversion_rate",
            name="Taxa de Conversão",
            value=2.1,
            unit="%",
            target=3.0,
            previous_value=1.8,
            trend=TrendDirection.UP,
            trend_percentage=16.7,
            category="efficiency",
            description="Taxa de conversão de candidatos para contratados"
        ),
        StrategicIndicator(
            id="candidate_nps",
            name="NPS Candidatos",
            value=87,
            unit="pontos",
            target=85,
            previous_value=82,
            trend=TrendDirection.UP,
            trend_percentage=6.1,
            category="satisfaction",
            description="Net Promoter Score dos candidatos"
        ),
        StrategicIndicator(
            id="manager_satisfaction",
            name="Satisfação do Gestor",
            value=4.6,
            unit="/5",
            target=4.5,
            previous_value=4.4,
            trend=TrendDirection.UP,
            trend_percentage=4.5,
            category="satisfaction",
            description="Nota média de satisfação dos gestores"
        ),
        StrategicIndicator(
            id="offer_acceptance_rate",
            name="Taxa de Aceite de Ofertas",
            value=89.5,
            unit="%",
            target=90,
            previous_value=85.2,
            trend=TrendDirection.UP,
            trend_percentage=5.0,
            category="recruitment",
            description="Percentual de ofertas aceitas"
        ),
        StrategicIndicator(
            id="source_quality",
            name="Qualidade de Sourcing",
            value=78,
            unit="%",
            target=80,
            previous_value=72,
            trend=TrendDirection.UP,
            trend_percentage=8.3,
            category="pipeline",
            description="Percentual de candidatos qualificados no sourcing"
        ),
        StrategicIndicator(
            id="interview_to_offer_ratio",
            name="Ratio Entrevista/Oferta",
            value=3.2,
            unit=":1",
            target=3.0,
            previous_value=3.8,
            trend=TrendDirection.DOWN,
            trend_percentage=-15.8,
            category="efficiency",
            description="Número de entrevistas por oferta realizada"
        ),
        StrategicIndicator(
            id="diversity_index",
            name="Índice de Diversidade",
            value=72,
            unit="%",
            target=75,
            previous_value=68,
            trend=TrendDirection.UP,
            trend_percentage=5.9,
            category="dei",
            description="Índice de diversidade nas contratações"
        ),
    ]
    
    return StrategicIndicatorsResponse(
        indicators=indicators,
        period="2024-12",
        generated_at=datetime.now()
    )


@router.get("/funnel-performance", response_model=FunnelPerformanceResponse)
async def get_funnel_performance(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get recruitment funnel performance data."""
    stages = [
        FunnelStage(
            stage_name="Applied",
            stage_order=1,
            count=1247,
            conversion_rate=100.0,
            drop_off_rate=0.0,
            avg_time_in_stage_days=2.5
        ),
        FunnelStage(
            stage_name="Triagem",
            stage_order=2,
            count=678,
            conversion_rate=54.4,
            drop_off_rate=45.6,
            avg_time_in_stage_days=3.2
        ),
        FunnelStage(
            stage_name="Entrevista",
            stage_order=3,
            count=234,
            conversion_rate=34.5,
            drop_off_rate=65.5,
            avg_time_in_stage_days=5.8
        ),
        FunnelStage(
            stage_name="Etapa Final",
            stage_order=4,
            count=89,
            conversion_rate=38.0,
            drop_off_rate=62.0,
            avg_time_in_stage_days=4.3
        ),
        FunnelStage(
            stage_name="Contratado",
            stage_order=5,
            count=12,
            conversion_rate=13.5,
            drop_off_rate=86.5,
            avg_time_in_stage_days=0
        ),
    ]
    
    return FunnelPerformanceResponse(
        stages=stages,
        total_candidates=1247,
        overall_conversion_rate=0.96,
        period="2024-12",
        generated_at=datetime.now()
    )


@router.get("/channel-performance", response_model=ChannelPerformanceResponse)
async def get_channel_performance(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get sourcing channel performance data."""
    total = 1247
    channels = [
        ChannelPerformance(
            channel_name="LinkedIn",
            candidates_count=524,
            percentage=42.0,
            quality_score=85.0,
            conversion_rate=2.5,
            cost_per_hire=3800,
            avg_time_to_hire_days=25
        ),
        ChannelPerformance(
            channel_name="Website Carreiras",
            candidates_count=349,
            percentage=28.0,
            quality_score=72.0,
            conversion_rate=1.8,
            cost_per_hire=2500,
            avg_time_to_hire_days=30
        ),
        ChannelPerformance(
            channel_name="Referral",
            candidates_count=187,
            percentage=15.0,
            quality_score=92.0,
            conversion_rate=4.2,
            cost_per_hire=1500,
            avg_time_to_hire_days=18
        ),
        ChannelPerformance(
            channel_name="LIA Database",
            candidates_count=125,
            percentage=10.0,
            quality_score=88.0,
            conversion_rate=3.8,
            cost_per_hire=800,
            avg_time_to_hire_days=15
        ),
        ChannelPerformance(
            channel_name="Outros",
            candidates_count=62,
            percentage=5.0,
            quality_score=65.0,
            conversion_rate=1.2,
            cost_per_hire=5200,
            avg_time_to_hire_days=35
        ),
    ]
    
    return ChannelPerformanceResponse(
        channels=channels,
        total_candidates=total,
        period="2024-12",
        generated_at=datetime.now()
    )


@router.get("/recruiter-ranking", response_model=RecruiterRankingResponse)
async def get_recruiter_ranking(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get recruiter performance ranking."""
    recruiters = [
        RecruiterPerformance(
            recruiter_id="rec-001",
            recruiter_name="Ana Silva",
            avatar_url="/images/candidates/ana_silva.jpg",
            positions_filled=5,
            positions_target=4,
            candidates_screened=156,
            interviews_conducted=42,
            conversion_rate=3.2,
            avg_time_to_fill_days=22,
            quality_score=94.5,
            rank=1
        ),
        RecruiterPerformance(
            recruiter_id="rec-002",
            recruiter_name="Carlos Mendes",
            avatar_url="/images/candidates/carlos_mendes.jpg",
            positions_filled=4,
            positions_target=4,
            candidates_screened=128,
            interviews_conducted=35,
            conversion_rate=3.1,
            avg_time_to_fill_days=26,
            quality_score=91.2,
            rank=2
        ),
        RecruiterPerformance(
            recruiter_id="rec-003",
            recruiter_name="Juliana Martins",
            avatar_url="/images/candidates/juliana_martins.jpg",
            positions_filled=3,
            positions_target=3,
            candidates_screened=98,
            interviews_conducted=28,
            conversion_rate=3.1,
            avg_time_to_fill_days=28,
            quality_score=89.8,
            rank=3
        ),
        RecruiterPerformance(
            recruiter_id="rec-004",
            recruiter_name="Ricardo Souza",
            avatar_url="/images/candidates/ricardo_souza.jpg",
            positions_filled=2,
            positions_target=3,
            candidates_screened=85,
            interviews_conducted=24,
            conversion_rate=2.4,
            avg_time_to_fill_days=32,
            quality_score=85.4,
            rank=4
        ),
        RecruiterPerformance(
            recruiter_id="rec-005",
            recruiter_name="Fernanda Costa",
            avatar_url="/images/candidates/fernanda_costa.jpg",
            positions_filled=1,
            positions_target=2,
            candidates_screened=67,
            interviews_conducted=18,
            conversion_rate=1.5,
            avg_time_to_fill_days=38,
            quality_score=82.1,
            rank=5
        ),
    ]
    
    return RecruiterRankingResponse(
        recruiters=recruiters,
        period="2024-12",
        generated_at=datetime.now()
    )


@router.get("/predictions", response_model=PredictionsResponse)
async def get_predictions(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get AI-powered predictions for recruitment metrics."""
    predictions = [
        Prediction(
            prediction_id="pred-001",
            metric_name="Contratações Próximo Mês",
            current_value=12,
            predicted_value=15,
            confidence=0.85,
            timeframe="próximo mês",
            trend=TrendDirection.UP,
            factors=[
                "Aumento de 23% nas candidaturas",
                "3 novas vagas urgentes abertas",
                "Melhora na taxa de conversão"
            ],
            recommendation="Considere aumentar capacidade de entrevistas em 20%"
        ),
        Prediction(
            prediction_id="pred-002",
            metric_name="Tempo Médio de Contratação",
            current_value=28,
            predicted_value=24,
            confidence=0.78,
            timeframe="próximo trimestre",
            trend=TrendDirection.DOWN,
            factors=[
                "Implementação de triagem automatizada",
                "Redução de etapas redundantes",
                "Maior alinhamento com gestores"
            ],
            recommendation="Mantenha otimizações no processo de triagem"
        ),
        Prediction(
            prediction_id="pred-003",
            metric_name="Taxa de Turnover",
            current_value=8.5,
            predicted_value=7.2,
            confidence=0.72,
            timeframe="próximos 6 meses",
            trend=TrendDirection.DOWN,
            factors=[
                "Melhoria no fit cultural das contratações",
                "Programa de onboarding otimizado",
                "Maior satisfação dos candidatos"
            ],
            recommendation="Continue investindo em avaliação de fit cultural"
        ),
        Prediction(
            prediction_id="pred-004",
            metric_name="Custo por Contratação",
            current_value=4500,
            predicted_value=4100,
            confidence=0.81,
            timeframe="próximo trimestre",
            trend=TrendDirection.DOWN,
            factors=[
                "Aumento de indicações internas",
                "Melhor uso do banco de talentos LIA",
                "Otimização de campanhas de sourcing"
            ],
            recommendation="Fortaleça programa de referral para reduzir custos"
        ),
        Prediction(
            prediction_id="pred-005",
            metric_name="Candidatos no Pipeline",
            current_value=1247,
            predicted_value=1450,
            confidence=0.88,
            timeframe="próximo mês",
            trend=TrendDirection.UP,
            factors=[
                "Campanhas de employer branding ativas",
                "Novas vagas publicadas",
                "Sazonalidade favorável"
            ],
            recommendation="Prepare equipe para maior volume de triagem"
        ),
    ]
    
    return PredictionsResponse(
        predictions=predictions,
        model_version="LIA-Predict-v2.1",
        generated_at=datetime.now()
    )
