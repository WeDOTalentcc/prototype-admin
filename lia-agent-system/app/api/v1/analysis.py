"""
LIA Analysis API endpoints.
Provides AI-powered candidate analysis using Claude.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.shared.services.analysis_service import analysis_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analysis/candidates", response_model=AnalysisResponse)
async def analyze_candidates(request: AnalysisRequest, company_id: str = Depends(require_company_id)) -> AnalysisResponse:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analyze candidates using AI-powered LIA methodology.
    
    - **contextual**: Compares candidates against a specific job vacancy
    - **general**: Generates profile, archetype, and potential roles
    
    Returns detailed analysis including:
    - lia_score: Overall compatibility score (0-100)
    - fit_score: Personality fit score (0-100)
    - archetype: Big Five archetype classification
    - strengths: Top 3 identified strengths
    - gaps: Areas for development
    - recommendation: Hiring recommendation
    - explanation: Detailed reasoning
    """
    if not request.candidates:
        raise HTTPException(status_code=400, detail="No candidates provided for analysis")
    
    if len(request.candidates) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 candidates per batch analysis")
    
    try:
        logger.info(f"Starting analysis for {len(request.candidates)} candidates (type: {request.analysis_type})")
        
        response = await analysis_service.analyze_candidates(request)
        
        logger.info(f"Analysis complete. Average score: {response.average_score}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=503, detail="Serviço de análise indisponível — verifique a configuração")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/analysis/archetypes", response_model=None)
async def get_archetypes(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get available Big Five archetypes.
    """
    return {
        "archetypes": [
            {
                "name": "Catalisador Visionário",
                "profile": "Alto O/E, Baixo N",
                "characteristics": "Inovador, inspirador, busca mudanças",
                "ideal_roles": ["Fundador", "Product Manager", "Diretor de Inovação"]
            },
            {
                "name": "Executor Confiável",
                "profile": "Alto C/A, Baixo N",
                "characteristics": "Metódico, colaborativo, entrega consistente",
                "ideal_roles": ["Gerente de Projetos", "Analista Sênior", "Ops Manager"]
            },
            {
                "name": "Guardião de Clientes",
                "profile": "Alto A/E, Médio O",
                "characteristics": "Empático, comunicativo, orientado ao cliente",
                "ideal_roles": ["Customer Success", "Account Manager", "Suporte Sênior"]
            },
            {
                "name": "Estrategista Analítico",
                "profile": "Alto O/C, Baixo E",
                "characteristics": "Pensador profundo, orientado a dados",
                "ideal_roles": ["Data Scientist", "Arquiteto", "Pesquisador"]
            },
            {
                "name": "Mediador Adaptável",
                "profile": "Alto A/O, Médio C",
                "characteristics": "Flexível, harmonizador, diplomático",
                "ideal_roles": ["HRBP", "Scrum Master", "Consultor"]
            },
            {
                "name": "Rainmaker Audacioso",
                "profile": "Alto E/O, Baixo A",
                "characteristics": "Persuasivo, ambicioso, orientado a resultados",
                "ideal_roles": ["Vendedor", "BD", "Founder"]
            },
            {
                "name": "Operador Resiliente",
                "profile": "Alto C, N controlado",
                "characteristics": "Estável sob pressão, focado, persistente",
                "ideal_roles": ["SRE", "Suporte Crítico", "Operações 24/7"]
            },
            {
                "name": "Arquiteto Metódico",
                "profile": "Alto C/O, Baixo E",
                "characteristics": "Detalhista, sistemático, qualidade",
                "ideal_roles": ["Engenheiro Sênior", "QA Lead", "Arquiteto de Software"]
            }
        ]
    }


@router.get("/analysis/scoring-methodology", response_model=None)
async def get_scoring_methodology(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the LIA scoring methodology.
    """
    return {
        "components": [
            {
                "name": "Match Técnico",
                "weight": 35,
                "description": "Alinhamento de habilidades técnicas com requisitos"
            },
            {
                "name": "Fit de Personalidade",
                "weight": 25,
                "description": "Compatibilidade Big Five com arquétipo ideal da vaga"
            },
            {
                "name": "Relevância de Experiência",
                "weight": 20,
                "description": "Experiências prévias similares ao contexto da vaga"
            },
            {
                "name": "Alinhamento Cultural",
                "weight": 20,
                "description": "Valores e comportamentos compatíveis com a empresa"
            }
        ],
        "recommendation_levels": [
            {"level": "highly_recommended", "score_range": "85-100%", "action": "Priorizar para entrevista"},
            {"level": "recommended", "score_range": "70-84%", "action": "Considerar para processo"},
            {"level": "potential", "score_range": "55-69%", "action": "Avaliar gaps específicos"},
            {"level": "low_match", "score_range": "40-54%", "action": "Arquivar para futuras vagas"},
            {"level": "not_recommended", "score_range": "0-39%", "action": "Não prosseguir"}
        ]
    }
