"""
LIA Analysis Service - AI-powered candidate analysis using Claude.
Uses Replit AI Integrations for Anthropic access.
"""
import os
import json
import logging
from typing import List, Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.schemas.analysis import (
    CandidateInput, CandidateAnalysisResult, AnalysisRequest, 
    AnalysisResponse, AnalysisType, ScoreBreakdown
)

logger = logging.getLogger(__name__)

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

ARCHETYPES = [
    "Catalisador Visionário",
    "Executor Confiável",
    "Guardião de Clientes",
    "Estrategista Analítico",
    "Mediador Adaptável",
    "Rainmaker Audacioso",
    "Operador Resiliente",
    "Arquiteto Metódico"
]

LIA_ANALYSIS_PROMPT = """Você é a LIA, uma assistente de IA especializada em análise de candidatos para recrutamento.

## METODOLOGIA DE SCORING (baseada no Framework LIA)

### Componentes do Score (Total = 100%):
1. **Match Técnico (35%)**: Alinhamento de habilidades técnicas com requisitos
2. **Fit de Personalidade (25%)**: Compatibilidade Big Five com arquétipo ideal
3. **Relevância de Experiência (20%)**: Experiências prévias similares ao contexto
4. **Alinhamento Cultural (20%)**: Valores e comportamentos compatíveis

### Arquétipos Big Five:
- **Catalisador Visionário**: Inovador, inspirador, busca mudanças (Alto O/E)
- **Executor Confiável**: Metódico, colaborativo, entrega consistente (Alto C/A)
- **Guardião de Clientes**: Empático, comunicativo, orientado ao cliente (Alto A/E)
- **Estrategista Analítico**: Pensador profundo, orientado a dados (Alto O/C)
- **Mediador Adaptável**: Flexível, harmonizador, diplomático (Alto A/O)
- **Rainmaker Audacioso**: Persuasivo, ambicioso, orientado a resultados (Alto E/O)
- **Operador Resiliente**: Estável sob pressão, focado, persistente (Alto C)
- **Arquiteto Metódico**: Detalhista, sistemático, qualidade (Alto C/O)

### Níveis de Recomendação:
- **highly_recommended** (85-100%): Priorizar para entrevista
- **recommended** (70-84%): Considerar para processo
- **potential** (55-69%): Avaliar gaps específicos
- **low_match** (40-54%): Arquivar para futuras vagas
- **not_recommended** (0-39%): Não prosseguir

{context}

## CANDIDATO A ANALISAR:
Nome: {candidate_name}
Cargo Atual: {candidate_position}
Localização: {candidate_location}
Empresa: {candidate_company}
Habilidades: {candidate_skills}
Anos de Experiência: {experience_years}
Nível de Senioridade: {seniority_level}
CV/Texto: {cv_text}

## INSTRUÇÃO:
Analise este candidato e retorne SOMENTE um JSON válido com a seguinte estrutura:
{{
    "lia_score": <número 0-100>,
    "fit_score": <número 0-100>,
    "archetype": "<um dos 8 arquétipos>",
    "strengths": ["força 1", "força 2", "força 3"],
    "gaps": ["gap 1", "gap 2"],
    "recommendation": "<recomendação de contratação em português>",
    "recommendation_level": "<highly_recommended|recommended|potential|low_match|not_recommended>",
    "explanation": "<explicação detalhada do score em português>",
    "score_breakdown": {{
        "match_tecnico": <número 0-100>,
        "fit_personalidade": <número 0-100>,
        "relevancia_experiencia": <número 0-100>,
        "alinhamento_cultural": <número 0-100>
    }},
    "potential_roles": ["role 1", "role 2", "role 3"]
}}

Retorne APENAS o JSON, sem texto adicional."""


class AnalysisService:
    """Service for AI-powered candidate analysis using Claude via Replit AI Integrations."""
    
    def __init__(self):
        self._client: Optional[Anthropic] = None
    
    @property
    def client(self) -> Anthropic:
        """Get Anthropic client with retry capability."""
        if self._client is None:
            if not AI_INTEGRATIONS_ANTHROPIC_API_KEY or not AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
                raise ValueError("AI_INTEGRATIONS_ANTHROPIC_API_KEY or AI_INTEGRATIONS_ANTHROPIC_BASE_URL not configured")
            
            self._client = Anthropic(
                api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
            )
        return self._client
    
    def _is_rate_limit_error(self, exception: BaseException) -> bool:
        """Check if the exception is a rate limit error."""
        error_msg = str(exception)
        return (
            "429" in error_msg
            or "RATELIMIT_EXCEEDED" in error_msg
            or "quota" in error_msg.lower()
            or "rate limit" in error_msg.lower()
            or (hasattr(exception, "status_code") and exception.status_code == 429)
        )
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    async def _analyze_single_candidate(
        self,
        candidate: CandidateInput,
        context: str = ""
    ) -> CandidateAnalysisResult:
        """Analyze a single candidate using Claude AI."""
        
        # SEG-3B: data minimization — remover PII do CV antes de enviar ao LLM (LGPD Art. 12)
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        _cv_text_raw = candidate.cv_text[:3000] if candidate.cv_text else "Não disponível"
        _cv_text_clean = strip_pii_for_llm_prompt(_cv_text_raw)

        prompt = LIA_ANALYSIS_PROMPT.format(
            context=context,
            candidate_name=candidate.name or "Não informado",
            candidate_position=candidate.position or "Não informado",
            candidate_location=candidate.location or "Não informado",
            candidate_company=candidate.company or "Não informado",
            candidate_skills=", ".join(candidate.skills) if candidate.skills else "Não informado",
            experience_years=candidate.experience_years or "Não informado",
            seniority_level=candidate.seniority_level or "Não informado",
            cv_text=_cv_text_clean,
        )
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            result_data = json.loads(response_text)
            
            score_breakdown = None
            if "score_breakdown" in result_data:
                score_breakdown = ScoreBreakdown(**result_data["score_breakdown"])
            
            return CandidateAnalysisResult(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                lia_score=result_data.get("lia_score", 50),
                fit_score=result_data.get("fit_score", 50),
                archetype=result_data.get("archetype", "Executor Confiável"),
                strengths=result_data.get("strengths", []),
                gaps=result_data.get("gaps", []),
                recommendation=result_data.get("recommendation", "Análise pendente"),
                recommendation_level=result_data.get("recommendation_level", "potential"),
                explanation=result_data.get("explanation", ""),
                score_breakdown=score_breakdown,
                potential_roles=result_data.get("potential_roles", [])
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return self._create_fallback_result(candidate)
        except Exception as e:
            logger.error(f"Error analyzing candidate {candidate.name}: {e}")
            raise
    
    def _create_fallback_result(self, candidate: CandidateInput) -> CandidateAnalysisResult:
        """Create a fallback result when AI analysis fails."""
        return CandidateAnalysisResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            lia_score=50,
            fit_score=50,
            archetype="Executor Confiável",
            strengths=["Perfil em análise"],
            gaps=["Informações insuficientes"],
            recommendation="Requer análise manual devido a erro na análise automática",
            recommendation_level="potential",
            explanation="A análise automática não pôde ser completada. Recomendamos revisão manual.",
            score_breakdown=ScoreBreakdown(
                match_tecnico=50,
                fit_personalidade=50,
                relevancia_experiencia=50,
                alinhamento_cultural=50
            ),
            potential_roles=[]
        )
    
    async def analyze_candidates(
        self,
        request: AnalysisRequest
    ) -> AnalysisResponse:
        """Analyze multiple candidates."""
        
        context = ""
        if request.analysis_type == AnalysisType.CONTEXTUAL and request.job_title:
            context = f"""## CONTEXTO DA VAGA:
Título: {request.job_title}
Requisitos: {', '.join(request.job_requirements) if request.job_requirements else 'Não especificado'}
Descrição: {request.job_description[:1500] if request.job_description else 'Não especificado'}

Para esta análise CONTEXTUAL, avalie o candidato em relação a esta vaga específica."""
        else:
            context = """## ANÁLISE GERAL (sem vaga específica):
Avalie o potencial geral do candidato, identificando seu arquétipo, pontos fortes e roles mais adequados."""
        
        results: List[CandidateAnalysisResult] = []
        
        for candidate in request.candidates:
            try:
                result = await self._analyze_single_candidate(candidate, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze candidate {candidate.id}: {e}")
                results.append(self._create_fallback_result(candidate))
        
        total_score = sum(r.lia_score for r in results)
        average_score = total_score / len(results) if results else 0
        
        position_counts: dict = {}
        location_counts: dict = {}
        skill_counts: dict = {}
        
        for i, candidate in enumerate(request.candidates):
            if candidate.position:
                pos = candidate.position
                if pos not in position_counts:
                    position_counts[pos] = {"count": 0, "total_score": 0}
                position_counts[pos]["count"] += 1
                position_counts[pos]["total_score"] += results[i].lia_score
            
            if candidate.location:
                loc = candidate.location
                if loc not in location_counts:
                    location_counts[loc] = {"count": 0, "total_score": 0}
                location_counts[loc]["count"] += 1
                location_counts[loc]["total_score"] += results[i].lia_score
            
            for skill in (candidate.skills or []):
                if skill not in skill_counts:
                    skill_counts[skill] = 0
                skill_counts[skill] += 1
        
        by_position = {
            pos: {"count": data["count"], "avgScore": round(data["total_score"] / data["count"], 1)}
            for pos, data in position_counts.items()
        }
        by_location = {
            loc: {"count": data["count"], "avgScore": round(data["total_score"] / data["count"], 1)}
            for loc, data in location_counts.items()
        }
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        skills_percentage = {skill: round((count / len(request.candidates)) * 100) for skill, count in top_skills}
        
        highly_recommended = sum(1 for r in results if r.recommendation_level == "highly_recommended")
        recommended = sum(1 for r in results if r.recommendation_level == "recommended")
        potential = sum(1 for r in results if r.recommendation_level == "potential")
        
        recommendations = []
        alerts = []
        
        if highly_recommended > 0:
            recommendations.append(f"{highly_recommended} candidatos com score acima de 85% - recomendo contato imediato")
            alerts.append({"type": "success", "message": f"{highly_recommended} candidatos com match perfeito identificados"})
        
        if recommended > 0:
            recommendations.append(f"{recommended} candidatos com potencial alto - considerar para processo seletivo")
        
        if potential > 0:
            recommendations.append(f"{potential} candidatos com potencial - avaliar gaps específicos")
            alerts.append({"type": "info", "message": f"{potential} candidatos com potencial para desenvolvimento"})
        
        alerts.append({"type": "info", "message": f"{len(results)} candidatos analisados com sucesso"})
        
        return AnalysisResponse(
            success=True,
            total_analyzed=len(results),
            average_score=round(average_score, 1),
            results=results,
            insights={
                "byPosition": by_position,
                "byLocation": by_location,
                "skills": skills_percentage
            },
            recommendations=recommendations,
            alerts=alerts
        )


analysis_service = AnalysisService()
