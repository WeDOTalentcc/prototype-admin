"""
WSI (WeDoTalent Skill Index) Service - Metodologia Científica de Avaliação.

Aplica 4 frameworks científicos:
1. CBI (Competency-Based Interviewing) - McClelland, 1973
2. Bloom's Taxonomy (Revisada) - Anderson et al., 2001
3. Dreyfus Model - Dreyfus & Dreyfus, 1980
4. Big Five (OCEAN) - Goldberg, 1992
"""
from typing import List, Dict, Optional, Literal, Any, Callable
from pydantic import BaseModel, Field, ValidationError
from dataclasses import dataclass, field as dc_field
from datetime import datetime
import json
import uuid
import logging
import re

from app.services.llm import llm_service
from app.services.wsi_deterministic_scorer import (
    calculate_wsi_deterministic,
    calculate_final_wsi_score,
    DeterministicWSIResult
)
from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# F2 Big Five Pipeline — modelos e constantes (spec WSI F2.5/F3/F5)
# ---------------------------------------------------------------------------

@dataclass
class OceanTraitScore:
    """Score de relevância 0-100 de um trait OCEAN para a vaga (F2.5 NEO-PI-R rubric)."""
    trait: str              # openness | conscientiousness | extraversion | agreeableness | stability
    score: int              # 0-100: intensidade com que a vaga exige o trait
    confidence: str = "medium"                          # high | medium | low
    evidence: List[str] = dc_field(default_factory=list)  # citações literais do JD


# Número de traits OCEAN selecionados por nível de senioridade (F5)
SENIORITY_BIGFIVE_TOP_N: Dict[str, int] = {
    "estagiario": 2,
    "junior":     2,
    "pleno":      3,
    "senior":     3,
    "lead":       4,
    "principal":  4,
    "diretor":    5,
    "vp_clevel":  5,
}


# ============================================================================
# HELPER FUNCTIONS - Error Handling & Robustness
# ============================================================================

def safe_json_parse(content: Any, fallback: Optional[Dict] = None) -> Dict:
    """
    Safely parse JSON content from LLM response with robust error handling.
    
    Args:
        content: LLM response content (str, dict, or AIMessage)
        fallback: Optional fallback dict if parsing fails
        
    Returns:
        Parsed dict or fallback
        
    Raises:
        ValueError: If parsing fails and no fallback provided
    """
    try:
        # Handle different content types
        if isinstance(content, dict):
            return content
        
        content_str = content if isinstance(content, str) else str(content)
        
        # Try to extract JSON from markdown code blocks
        if "```json" in content_str:
            start = content_str.find("```json") + 7
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        elif "```" in content_str:
            start = content_str.find("```") + 3
            end = content_str.find("```", start)
            content_str = content_str[start:end].strip()
        
        # Parse JSON
        parsed = json.loads(content_str)
        return parsed
        
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"Content was: {content}")
        
        if fallback is not None:
            logger.warning(f"Using fallback: {fallback}")
            return fallback
        
        raise ValueError(f"Failed to parse JSON and no fallback provided: {e}")


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize weights to sum to 1.0.
    
    Args:
        weights: Dict of competency -> weight
        
    Returns:
        Normalized weights dict
        
    Raises:
        ValueError: If total weight is 0
    """
    total = sum(weights.values())
    
    if total == 0:
        raise ValueError("Total weights cannot be zero")
    
    if abs(total - 1.0) < 0.01:  # Already normalized
        return weights
    
    normalized = {k: v / total for k, v in weights.items()}
    logger.info(f"Normalized weights from sum={total:.2f} to sum=1.0")
    
    return normalized


class Competency(BaseModel):
    """Competência a ser avaliada."""
    name: str
    type: Literal["technical", "behavioral", "cultural"]
    weight: float = Field(ge=0, le=1)
    seniority_level: Literal["junior", "pleno", "senior", "lead", "executive"]
    is_critical: bool = False
    big_five_mapping: Optional[str] = None  # F6.6: trait OCEAN pré-mapeado (openness|conscientiousness|extraversion|agreeableness|stability)


class CompetencySuggestion(BaseModel):
    """Sugestão automática de competências baseada em JD."""
    technical_competencies: List[Competency]
    behavioral_competencies: List[Competency]
    cultural_competencies: List[Competency]
    suggested_weights: Dict[str, float]
    confidence_score: float


class WSIQuestion(BaseModel):
    """Pergunta WSI estruturada."""
    id: str
    competency: str
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"]
    question_type: Literal["autodeclaration", "contextual", "microcase", "situational"]
    question_text: str
    weight: float
    expected_signals: List[str]
    scoring_criteria: Dict[str, Any]
    is_critical: bool = False
    # F6.8 — validação pós-geração
    needs_manual_review: bool = False
    validation_flags: Dict[str, Any] = Field(default_factory=dict)


class ResponseAnalysis(BaseModel):
    """Análise de resposta do candidato."""
    question_id: str
    competency: str
    response_text: str
    
    autodeclaration_score: Optional[float] = Field(None, ge=1, le=5)
    context_score: Optional[float] = Field(None, ge=1, le=5)
    bloom_level: Optional[int] = Field(None, ge=1, le=6)
    dreyfus_level: Optional[int] = Field(None, ge=1, le=5)
    
    evidences: List[str]
    red_flags: List[str]
    consistency_penalty: float = 0.0
    
    final_score: float = Field(ge=1, le=5)
    justification: str


class WSIResult(BaseModel):
    """Resultado final da avaliação WSI."""
    candidate_id: str
    job_vacancy_id: str
    
    technical_wsi: float = Field(ge=0, le=5)
    behavioral_wsi: float = Field(ge=0, le=5)
    overall_wsi: float = Field(ge=0, le=5)
    
    classification: Literal["excepcional", "excelente", "alto", "medio", "regular", "baixo"]
    percentile: Optional[int] = None
    
    response_analyses: List[ResponseAnalysis]
    created_at: datetime = Field(default_factory=datetime.now)


class StructuredReport(BaseModel):
    """Parecer estruturado do candidato."""
    candidate_id: str
    wsi_result: WSIResult
    
    executive_summary: str
    
    technical_analysis: Dict[str, Any]
    behavioral_analysis: Dict[str, Any]
    cultural_fit: Dict[str, Any]
    
    recommendation: Dict[str, Any]


class CandidateFeedback(BaseModel):
    """Feedback estruturado para o candidato."""
    candidate_id: str
    decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    
    main_message: str
    technical_strengths: List[str]
    development_opportunities: List[str]
    behavioral_strengths: List[str]
    
    next_steps: str
    personalized_tip: Optional[str] = None
    development_plan: Optional[Dict[str, List[str]]] = None
    recommended_resources: Optional[List[str]] = None


class WSIService:
    """
    Serviço completo de aplicação da metodologia WSI.
    
    Responsabilidades:
    1. Analisar JD e sugerir competências
    2. Gerar perguntas científicas baseadas em frameworks
    3. Analisar respostas semanticamente (scoring 1-5)
    4. Calcular WSI (média ponderada)
    5. Gerar pareceres estruturados
    6. Gerar feedbacks construtivos para candidatos
    """
    
    def __init__(self):
        self.llm = llm_service
        self.question_generator = WSIQuestionGenerator(self.llm)
        self.response_analyzer = WSIResponseAnalyzer(self.llm)
        self.score_calculator = WSIScoreCalculator()
        self.report_generator = WSIReportGenerator(self.llm)
    
    async def analyze_jd_and_suggest_competencies(
        self,
        job_description: str,
        company_culture: Optional[Dict] = None,
        seniority: Literal["junior", "pleno", "senior", "lead", "executive"] = "pleno"
    ) -> CompetencySuggestion:
        """
        ETAPA 1: Analisa JD e sugere competências automaticamente.
        
        Usa NLP para extrair:
        - Hard skills (Python, React, AWS, etc.)
        - Soft skills (liderança, comunicação, etc.)
        - Nível de senioridade
        - Fit cultural esperado
        
        Args:
            job_description: Texto completo do JD
            company_culture: Valores e cultura da empresa
            seniority: Nível da vaga
            
        Returns:
            CompetencySuggestion com 5-7 competências sugeridas
        """
        prompt = f"""Analise este Job Description e sugira as competências mais importantes para avaliação em triagem.

JD:
{job_description}

Cultura da empresa:
{company_culture or "Não fornecida"}

Nível da vaga: {seniority}

Sua tarefa:
1. Extraia as 5 competências TÉCNICAS mais críticas para a vaga (hard skills)
2. Extraia as 5 competências COMPORTAMENTAIS mais relevantes para a vaga
   - Pode classificar cada uma como "behavioral" (soft skill interpessoal) ou "cultural" (fit com valores/cultura)
   - Ordene da mais crítica para a menos crítica conforme o perfil da vaga
3. Sugira pesos (total = 1.0):
   - 60% para técnicas (distribuir entre as 5, ex: 0.18, 0.15, 0.12, 0.10, 0.05)
   - 40% para comportamentais/culturais (distribuir entre as 5, ex: 0.12, 0.10, 0.08, 0.06, 0.04)

As 5 comportamentais garantem que tanto no modo compacto (6 perguntas) quanto no modo completo (10 perguntas)
a metodologia possa selecionar as mais relevantes conforme o perfil específico da vaga.

Responda em JSON:
{{
  "technical_competencies": [
    {{"name": "Python", "weight": 0.20, "is_critical": true}},
    {{"name": "Django/FastAPI", "weight": 0.15, "is_critical": true}},
    {{"name": "PostgreSQL", "weight": 0.10, "is_critical": false}},
    {{"name": "AWS", "weight": 0.10, "is_critical": false}},
    {{"name": "Docker", "weight": 0.05, "is_critical": false}}
  ],
  "behavioral_competencies": [
    {{"name": "Comunicação Assertiva", "weight": 0.10}},
    {{"name": "Colaboração em Equipe", "weight": 0.08}},
    {{"name": "Gestão de Conflito", "weight": 0.08}},
    {{"name": "Adaptabilidade", "weight": 0.07}},
    {{"name": "Orientação a Resultados", "weight": 0.07}}
  ],
  "cultural_competencies": [],
  "confidence_score": 0.95
}}"""

        response = await self.llm.claude.ainvoke(prompt)
        
        # Parse JSON response
        content_str = response.content if isinstance(response.content, str) else str(response.content)
        data = json.loads(content_str)
        
        # Converter para Competency objects
        technical = [
            Competency(
                name=comp["name"],
                type="technical",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=comp.get("is_critical", False)
            )
            for comp in data["technical_competencies"]
        ]
        
        behavioral = [
            Competency(
                name=comp["name"],
                type="behavioral",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=False
            )
            for comp in data.get("behavioral_competencies", [])
        ]
        
        cultural = [
            Competency(
                name=comp["name"],
                type="cultural",
                weight=comp["weight"],
                seniority_level=seniority,
                is_critical=False
            )
            for comp in data.get("cultural_competencies", [])
        ]
        
        return CompetencySuggestion(
            technical_competencies=technical,
            behavioral_competencies=behavioral,
            cultural_competencies=cultural,
            suggested_weights={comp.name: comp.weight for comp in technical + behavioral + cultural},
            confidence_score=data.get("confidence_score", 0.9)
        )
    
    async def generate_screening_questions(
        self,
        competencies: List[Competency],
        mode: Literal["compact", "full"] = "compact",
        job_description: Optional[str] = None,
        seniority: Optional[str] = None,
        enriched_jd: Optional[Dict] = None,
    ) -> List[WSIQuestion]:
        """
        ETAPA 2: Gera perguntas científicas baseadas em competências.

        Aplica frameworks:
        - CBI para perguntas contextuais (técnico E comportamental)
        - Dreyfus para autodeclaração de proficiência técnica
        - Bloom para microcases situacionais
        - Big Five para fit comportamental/cultural (F6.6 via pipeline F2.5→F3→F5)

        Args:
            competencies: Lista de competências a avaliar
            mode: "compact" (7 perguntas) ou "full" (12 perguntas)
            job_description: Descrição da vaga para pipeline F2.5 OCEAN scoring (opcional)
            seniority: Nível de senioridade para seleção F5 top-N traits (opcional)
            enriched_jd: Output serializado de JdEnrichmentService (opcional).
                         Quando fornecido: preenche big_five_mapping das competências
                         comportamentais e usa about_role+responsabilidades como
                         contexto F2.5 se job_description não fornecido.

        Returns:
            Lista de perguntas WSI estruturadas
        """
        # F1.C → WSI bridge: enriquecer competências com big_five_mapping do enriched_jd
        if enriched_jd:
            enriched_comps, jd_context = self._build_competencies_from_enriched_jd(
                enriched_jd, seniority or "pleno"
            )
            competencies = self._merge_with_enriched(competencies, enriched_comps)
            if not job_description and jd_context:
                job_description = jd_context
                logger.info("WSI F1.C bridge: usando jd_context do enriched_jd para F2.5")

        return await self.question_generator.generate_all(
            competencies,
            mode,
            job_description=job_description,
            seniority=seniority,
        )

    async def generate_from_simple_inputs(
        self,
        skills: List[str],
        behavioral: Optional[List[str]] = None,
        seniority: str = "pleno",
        job_description: Optional[str] = None,
        mode: Literal["compact", "full"] = "compact",
        max_questions: Optional[int] = None,
    ) -> List[WSIQuestion]:
        """Convenience wrapper: converts string skill/behavioral lists into Competency
        objects and delegates to ``generate_screening_questions()``.

        This allows callers that only have simple string lists (e.g. API
        endpoints, wizard) to use the canonical F6 pipeline without manually
        building ``Competency`` objects.
        """
        _seniority = (seniority or "pleno").lower().strip()
        _seniority_level = _seniority.replace(" ", "_").replace("-", "_")
        _valid_levels = ("junior", "pleno", "senior", "lead", "executive", "estagiario", "principal", "diretor", "vp_clevel")
        if _seniority_level not in _valid_levels:
            _seniority_level = "pleno"

        competencies: List[Competency] = []

        for idx, skill in enumerate(skills or []):
            if not skill or not skill.strip():
                continue
            competencies.append(Competency(
                name=skill.strip(),
                type="technical",
                weight=round(max(0.1, 1.0 - idx * 0.05), 2),
                seniority_level=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
                is_critical=idx < 3,
            ))

        for idx, comp in enumerate(behavioral or []):
            if not comp or not comp.strip():
                continue
            competencies.append(Competency(
                name=comp.strip(),
                type="behavioral",
                weight=round(max(0.1, 0.9 - idx * 0.05), 2),
                seniority_level=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
                is_critical=False,
            ))

        if not competencies:
            competencies.append(Competency(
                name="General",
                type="technical",
                weight=1.0,
                seniority_level="pleno",
                is_critical=False,
            ))

        return await self.generate_screening_questions(
            competencies=competencies,
            mode=mode,
            job_description=job_description,
            seniority=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
        )

    @staticmethod
    def _build_competencies_from_enriched_jd(
        enriched_jd: dict,
        seniority: str = "pleno",
    ) -> tuple:
        """F1.C → WSI bridge: converte EnrichedJobDescription em competências WSI.

        Extrai de enriched_jd:
        - skills_obrigatorias → Competency(type="technical") com is_critical nos top 3
        - competencias_comportamentais → Competency(type="behavioral") com big_five_mapping preenchido
        - about_role + responsabilidades → texto de contexto para F2.5

        Args:
            enriched_jd: dict output de JdEnrichmentService (EnrichedJobDescription serializado)
            seniority: nível para seniority_level das competências geradas

        Returns:
            Tuple[List[Competency], str] — (competências com big_five_mapping, jd_context para F2.5)
        """
        _SENIORITY_MAP = {
            "estagiario": "junior", "estagiário": "junior",
            "junior": "junior", "júnior": "junior",
            "pleno": "pleno",
            "senior": "senior", "sênior": "senior",
            "lead": "lead", "principal": "lead",
            "diretor": "executive", "vp": "executive", "clevel": "executive", "c-level": "executive",
        }
        seniority_level = _SENIORITY_MAP.get(seniority.lower().strip(), "pleno")
        competencies: list = []

        # --- Técnicas: de skills_obrigatorias ---
        skills_raw = enriched_jd.get("skills_obrigatorias", [])
        n_skills = max(len(skills_raw), 1)
        for i, skill_entry in enumerate(skills_raw):
            if isinstance(skill_entry, str):
                skill_name = skill_entry
            elif isinstance(skill_entry, dict):
                skill_name = skill_entry.get("skill") or skill_entry.get("value") or str(skill_entry)
            else:
                continue
            competencies.append(Competency(
                name=skill_name,
                type="technical",
                weight=round(0.6 / n_skills, 4),
                seniority_level=seniority_level,
                is_critical=(i < 2),  # F6-5: máximo 2 skills críticas por triagem (spec §6.5)
            ))

        # --- Comportamentais: de competencias_comportamentais com trait pré-mapeado ---
        behavioral_raw = enriched_jd.get("competencias_comportamentais", [])
        n_behavioral = max(len(behavioral_raw), 1)
        for comp_entry in behavioral_raw:
            if isinstance(comp_entry, str):
                comp_name, trait = comp_entry, None
            elif isinstance(comp_entry, dict):
                comp_name = (
                    comp_entry.get("competencia")
                    or comp_entry.get("value")
                    or comp_entry.get("name")
                    or str(comp_entry)
                )
                # trait_big_five ou big_five_mapping — aceitar ambos
                trait = comp_entry.get("trait_big_five") or comp_entry.get("big_five_mapping")
            else:
                continue
            competencies.append(Competency(
                name=comp_name,
                type="behavioral",
                weight=round(0.4 / n_behavioral, 4),
                seniority_level=seniority_level,
                big_five_mapping=trait,
            ))

        # --- Texto de contexto para F2.5 ---
        about = enriched_jd.get("about_role", "")
        resps = enriched_jd.get("responsabilidades", [])
        if isinstance(resps, list):
            resps_text = " ".join(resps)
        else:
            resps_text = str(resps)
        jd_context = f"{about}\n\n{resps_text}".strip()

        return competencies, jd_context

    @staticmethod
    def _merge_with_enriched(
        original: List["Competency"],
        enriched: List["Competency"],
    ) -> List["Competency"]:
        """Mescla lista original de competências com versão enriquecida.

        Para cada competência original sem big_five_mapping, tenta encontrar
        correspondência por nome (case-insensitive) na lista enriquecida e
        copia o big_five_mapping. Mantém todas as competências originais.
        """
        enriched_by_name = {c.name.lower().strip(): c for c in enriched}
        merged = []
        for comp in original:
            if comp.big_five_mapping is None and comp.type in ("behavioral", "cultural"):
                match = enriched_by_name.get(comp.name.lower().strip())
                if match and match.big_five_mapping:
                    comp = comp.model_copy(update={"big_five_mapping": match.big_five_mapping})
            merged.append(comp)
        # Adicionar comportamentais enriquecidas sem equivalente original
        original_names = {c.name.lower().strip() for c in original}
        for comp in enriched:
            if comp.name.lower().strip() not in original_names:
                merged.append(comp)
        return merged

    async def analyze_response(
        self,
        question: WSIQuestion,
        response: str
    ) -> ResponseAnalysis:
        """
        ETAPA 3: Analisa resposta e atribui score 1-5.
        
        Aplica:
        - Extração de autodeclaração (se houver)
        - Análise de contexto (Bloom + Dreyfus)
        - Detecção de evidências concretas
        - Detecção de red flags
        - Cálculo de score ponderado
        
        Args:
            question: Pergunta WSI
            response: Resposta do candidato (texto ou transcrição)
            
        Returns:
            ResponseAnalysis com scores e justificativas
        """
        return await self.response_analyzer.analyze(question, response)
    
    def calculate_wsi(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        responses: List[ResponseAnalysis],
        weights: Dict[str, float]
    ) -> WSIResult:
        """
        ETAPA 4: Calcula WSI final.
        
        Fórmula: WSI = Σ(peso_i × score_i) / 100
        
        Classificação:
        - 4.5-5.0: Excelente
        - 4.0-4.4: Alto
        - 3.0-3.9: Médio
        - 2.0-2.9: Regular
        - < 2.0: Baixo
        
        Args:
            candidate_id: ID do candidato
            job_vacancy_id: ID da vaga
            responses: Lista de análises de respostas
            weights: Pesos por competência
            
        Returns:
            WSIResult com score final e classificação
        """
        # Normalize weights before calculation
        normalized_weights = normalize_weights(weights)
        
        return self.score_calculator.calculate(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            responses=responses,
            weights=normalized_weights
        )
    
    async def generate_structured_report(
        self,
        candidate_id: str,
        wsi_result: WSIResult,
        responses: List[ResponseAnalysis]
    ) -> StructuredReport:
        """
        ETAPA 5: Gera parecer estruturado.
        
        Inclui:
        - Sumário executivo
        - Análise técnica (pontos fortes, gaps)
        - Análise comportamental
        - Fit cultural
        - Recomendação fundamentada (APROVADO/AGUARDANDO/NÃO APROVADO)
        
        Args:
            candidate_id: ID do candidato
            wsi_result: Resultado WSI calculado
            responses: Análises detalhadas
            
        Returns:
            StructuredReport com parecer completo
        """
        return await self.report_generator.generate_report(
            candidate_id, wsi_result, responses
        )
    
    async def generate_candidate_feedback(
        self,
        wsi_result: WSIResult,
        responses: List[ResponseAnalysis],
        decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    ) -> CandidateFeedback:
        """
        ETAPA 6: Gera feedback estruturado para candidato.
        
        Inclui:
        - Mensagem principal
        - Pontos fortes técnicos
        - Oportunidades de desenvolvimento
        - Próximos passos ou plano de desenvolvimento
        - Recursos recomendados (se não aprovado)
        
        Args:
            wsi_result: Resultado WSI
            responses: Análises detalhadas
            decision: Decisão final
            
        Returns:
            CandidateFeedback estruturado e construtivo
        """
        return await self.report_generator.generate_feedback(
            wsi_result, responses, decision
        )


class WSIQuestionGenerator:
    """Gerador de perguntas científicas baseado em frameworks e RAG."""
    
    def __init__(self, llm):
        self.llm = llm
        self._load_rag_templates()
    
    def _load_rag_templates(self):
        """Carrega templates de perguntas do RAG knowledge base com fallbacks."""
        from pathlib import Path
        
        rag_dir = Path("lia-agent-system/training/rag_knowledge/wsi_methodology")
        
        # Load frameworks overview with fallback
        frameworks_file = rag_dir / "frameworks_overview.md"
        if frameworks_file.exists():
            self.frameworks_doc = frameworks_file.read_text(encoding="utf-8")
        else:
            logger.warning("RAG frameworks_overview.md not found. Using hardcoded fallback.")
            self.frameworks_doc = """
# WSI Frameworks Overview (Fallback)

## 1. CBI (Competency-Based Interviewing)
Princípio: Comportamentos passados são os melhores preditores de performance futura.
Estrutura: "Conte sobre uma situação..." (STAR: Situation, Task, Action, Result)

## 2. Dreyfus Model
Levels: 1-Novice, 2-Advanced Beginner, 3-Competent, 4-Proficient, 5-Expert

## 3. Bloom's Taxonomy
Levels: 1-Lembrar, 2-Compreender, 3-Aplicar, 4-Analisar, 5-Avaliar, 6-Criar

## 4. Big Five (OCEAN)
Traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
"""
        
        # Load question templates with fallback
        templates_file = rag_dir / "question_generation_templates.md"
        if templates_file.exists():
            self.question_templates = templates_file.read_text(encoding="utf-8")
        else:
            logger.warning("RAG question_generation_templates.md not found. Using hardcoded fallback.")
            self.question_templates = """
# Question Templates (Fallback)

## CBI Questions
- "Conte sobre um projeto onde você usou {skill}. Qual foi o contexto, sua ação e o resultado?"
- "Descreva uma situação desafiadora envolvendo {skill}. Como você resolveu?"

## Dreyfus Questions
- "De 1 a 5, quanto você domina {skill}? Cite um projeto recente onde aplicou."

## Bloom Questions  
- Level 3-4: "Como você implementaria/diagnosticaria {scenario}?"
- Level 5: "Projete uma solução para {complex_problem}"

## Big Five Questions
- "Como você reage quando {stressful_situation}?"
- "Descreva como você trabalha em equipe..."
"""
    
    async def _extract_ocean_scores(
        self,
        job_description: str,
        behavioral_competencies: Optional[List[str]] = None,
    ) -> List[OceanTraitScore]:
        """F2.5 — Extrai perfil Big Five do JD com rubric NEO-PI-R (Abordagem C).

        Temperatura 0.1: extração estruturada baseada em evidências — não criação.
        Retorna lista ordenada por score decrescente (F3 — ranking).
        """
        _FIVE_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]
        _FALLBACK = {t: {"score": 60, "evidence": [], "confidence": "low"} for t in _FIVE_TRAITS}

        behav_context = (
            f"Competências comportamentais declaradas: {', '.join(behavioral_competencies)}"
            if behavioral_competencies else ""
        )

        prompt = f"""Você é um psicólogo organizacional especialista em avaliação de competências e modelo Big Five (NEO-PI-R).
Analise o Job Description fornecido e extraia o perfil de personalidade requerido pela vaga.
Para cada um dos 5 traits do Big Five, avalie a INTENSIDADE com que o JD REQUER aquele trait.
Baseie-se EXCLUSIVAMENTE no texto do JD — não em suposições sobre o tipo de cargo.

RUBRIC DE AVALIAÇÃO:
- 0–30: O trait não é mencionado ou relevante para este papel
- 31–50: O trait aparece implicitamente; é útil mas não diferenciador
- 51–70: O trait é claramente necessário; mencionado em responsabilidades ou requisitos
- 71–85: O trait é central para o papel; mencionado múltiplas vezes com evidências fortes
- 86–100: O trait é absolutamente crítico; a vaga seria inviável sem ele

REGRAS DE EVIDÊNCIA (OBRIGATÓRIAS):
- O campo "evidence" deve conter CITAÇÕES LITERAIS do JD — trechos exatos entre aspas duplas
  Correto:   "evidence": ["\"lidera equipes multidisciplinares em contextos de alta ambiguidade\""]
  PROIBIDO:  "evidence": ["menciona liderança de equipes"] — paráfrase NÃO é evidência
- Se um trait não tem nenhum trecho literal que o suporte, "evidence" deve ser [] e
  "confidence" deve ser "low" com score ≤ 30
- NUNCA infira traits a partir do nome da empresa, setor, tecnologias usadas ou cargo —
  somente do texto explícito de responsabilidades, requisitos e contexto do JD

REGRAS PARA JD INSUFICIENTE:
- Se o JD tiver menos de 50 palavras úteis disponíveis para análise:
  definir "confidence": "low" para TODOS os traits, independentemente dos scores
  adicionar nota em todos os "evidence": ["[JD insuficiente — análise com baixa confiança]"]

REGRAS PARA SINAIS CONTRADITÓRIOS:
- Quando o JD apresentar sinais que se contradizem para o mesmo trait,
  registrar em "evidence" com prefixo "[SINAL CONTRADITÓRIO]" e reduzir score para 40–55,
  definir "confidence": "medium"

JD enriquecido:
---
{job_description[:2000]}
---
{behav_context}

Retorne APENAS JSON válido (sem texto fora do JSON):
{{
  "big_five_jd": {{
    "openness":          {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "conscientiousness": {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "extraversion":      {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "agreeableness":     {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "stability":         {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }}
  }}
}}"""
        try:
            response = await self.llm.claude.bind(temperature=0.1, max_tokens=800).ainvoke(prompt)
            parsed = safe_json_parse(response.content, fallback={"big_five_jd": _FALLBACK})
            data = parsed.get("big_five_jd") or _FALLBACK
            if not isinstance(data, dict) or not any(t in data for t in _FIVE_TRAITS):
                data = _FALLBACK
        except Exception as e:
            logger.error(f"F2.5 OCEAN extraction failed: {e} — using fallback")
            data = _FALLBACK

        result = []
        for t in _FIVE_TRAITS:
            if t not in data:
                continue
            entry = data[t]
            result.append(OceanTraitScore(
                trait=t,
                score=max(0, min(100, int(entry.get("score", 60)))),
                confidence=entry.get("confidence", "medium"),
                evidence=entry.get("evidence", []),
            ))
        return sorted(result, key=lambda x: x.score, reverse=True)

    def _select_traits_by_seniority(
        self,
        ranked_traits: List[OceanTraitScore],
        seniority: str,
    ) -> List[OceanTraitScore]:
        """F5 — Seleciona top-N traits conforme senioridade da vaga."""
        key = seniority.lower().strip().replace(" ", "_").replace("-", "_")
        n = SENIORITY_BIGFIVE_TOP_N.get(key, 3)
        return ranked_traits[:n]

    async def generate_all(
        self,
        competencies: List[Competency],
        mode: Literal["compact", "full"] = "compact",
        job_description: Optional[str] = None,
        seniority: Optional[str] = None,
    ) -> List[WSIQuestion]:
        """
        Gera todas as perguntas para as competências selecionadas.

        Estratégia:
        - compact: 7 perguntas  (~14 min WhatsApp)
        - full:    12 perguntas (~25 min WhatsApp)

        Ambos os modos extraem 5 técnicas + 5 comportamentais do JD.
        A metodologia seleciona as mais relevantes por peso e is_critical.
        CBI cobre técnico E comportamental em ambos os modos.

        Distribuição compact (7 perguntas):
        - CBI técnico:        2 perguntas  (top 2 técnicas por is_critical + peso)
        - CBI comportamental: 1 pergunta   (top 1 comportamental por peso)
        - Dreyfus:            1 pergunta   (3ª técnica — autodeclaração)
        - Bloom:              1 pergunta   (4ª técnica — microcase)
        - Big Five:           2 perguntas  (2ª e 3ª comportamentais — fit cultural/situacional OCEAN)

        Distribuição full (12 perguntas):
        - CBI técnico:        3 perguntas  (top 3 técnicas por is_critical + peso)
        - CBI comportamental: 3 perguntas  (top 3 comportamentais por peso)
        - Dreyfus:            2 perguntas  (4ª e 5ª técnicas — autodeclaração)
        - Bloom:              2 perguntas  (microcase — técnica de maior bloom_level + outra técnica crítica)
        - Big Five:           2 perguntas  (4ª e 5ª comportamentais — fit cultural/situacional)
        """
        if not competencies:
            raise ValueError("At least 1 competency is required to generate questions")

        if len(competencies) < 2:
            logger.warning(f"Only {len(competencies)} competencies provided. Minimum 2 recommended for WSI screening.")

        # Separar e ordenar por relevância: is_critical primeiro, depois peso decrescente
        technical = sorted(
            [c for c in competencies if c.type == "technical"],
            key=lambda c: (c.is_critical, c.weight),
            reverse=True
        )
        behavioral = sorted(
            [c for c in competencies if c.type in ("behavioral", "cultural")],
            key=lambda c: c.weight,
            reverse=True
        )

        if not technical:
            logger.warning("No technical competencies provided. Using behavioral for all questions.")
            technical = behavioral

        # D3/D4 quality warnings: alertar quando abaixo dos mínimos ideais da spec WSI F8
        if len(technical) < 9:
            logger.warning(
                f"WSI question generation: only {len(technical)} technical competencies provided "
                f"(spec minimum: 9). Question quality may be reduced for {'compact' if mode == 'compact' else 'full'} mode."
            )
        if len(behavioral) < 5:
            logger.warning(
                f"WSI question generation: only {len(behavioral)} behavioral competencies provided "
                f"(spec minimum: 5). Big Five questions may repeat competencies."
            )

        # F2.5 / F3 / F5 pipeline — quando job_description disponível
        selected_traits: List[OceanTraitScore] = []
        if job_description:
            behav_names = [c.name for c in behavioral]
            ranked = await self._extract_ocean_scores(job_description, behav_names)
            selected_traits = self._select_traits_by_seniority(ranked, seniority or "pleno")
            logger.info(f"WSI F2.5 OCEAN ranked: {[(t.trait, t.score) for t in ranked]}")
            logger.info(f"WSI F5 selected ({len(selected_traits)} for '{seniority}'): {[t.trait for t in selected_traits]}")

        # F5 — distribuição adaptativa por senioridade (WSI-8)
        _norm_sen = (seniority or "pleno").lower().strip().replace(" ", "_").replace("-", "_")
        _mode_dists = SENIORITY_DISTRIBUTIONS.get(mode, SENIORITY_DISTRIBUTIONS["full"])
        _dist = _mode_dists.get(_norm_sen, _mode_dists.get("senior", list(_mode_dists.values())[0]))
        _tech_target = _dist["technical"]
        _behav_target = _dist["behavioral"]

        if mode == "compact":
            _has_dreyfus = _tech_target >= 2
            _has_bloom = _tech_target >= 3
            _cbi_tech_n = max(1, _tech_target - int(_has_dreyfus) - int(_has_bloom))
            _dreyfus_n = int(_has_dreyfus)
            _bloom_n = int(_has_bloom)
            _cbi_behav_n = 1
            _bigfive_n = _behav_target - 1
        else:  # full
            _dreyfus_n = min(2, max(0, _tech_target - 3))
            _bloom_n = min(2, max(0, _tech_target - 1 - _dreyfus_n))
            _cbi_tech_n = max(1, _tech_target - _dreyfus_n - _bloom_n)
            _cbi_behav_n = max(1, _behav_target - 2)
            _bigfive_n = _behav_target - _cbi_behav_n

        logger.info(
            f"WSI F5 generate_all distribution ({_norm_sen}/{mode}): "
            f"cbi_tech={_cbi_tech_n}, dreyfus={_dreyfus_n}, bloom={_bloom_n}, "
            f"cbi_behav={_cbi_behav_n}, bigfive={_bigfive_n}"
        )

        questions = []
        jd = job_description  # alias curto para legibilidade

        # --- CBI técnico ---
        for comp in technical[:_cbi_tech_n]:
            questions.append(await self._generate_with_validation(
                self._generate_cbi_question, comp,
                jd_text=jd, skill_or_trait=comp.name, question_category="technical",
            ))

        # --- CBI comportamental ---
        for comp in behavioral[:_cbi_behav_n]:
            questions.append(await self._generate_with_validation(
                self._generate_cbi_question, comp,
                jd_text=jd, skill_or_trait=comp.name, question_category="behavioral",
            ))

        # --- Dreyfus (autodeclaração de proficiência) ---
        dreyfus_offset = _cbi_tech_n
        for i in range(_dreyfus_n):
            comp = technical[dreyfus_offset + i] if len(technical) > dreyfus_offset + i else technical[-1]
            questions.append(await self._generate_with_validation(
                self._generate_dreyfus_question, comp,
                jd_text=jd, skill_or_trait=comp.name, question_category="technical",
            ))

        # --- Bloom (microcase situacional) ---
        bloom_offset = dreyfus_offset + _dreyfus_n
        for i in range(_bloom_n):
            comp = technical[bloom_offset + i] if len(technical) > bloom_offset + i else technical[0]
            questions.append(await self._generate_with_validation(
                self._generate_bloom_question, comp,
                jd_text=jd, skill_or_trait=comp.name, question_category="technical",
            ))

        # --- Big Five: F6.6 — seleção por afinidade de trait (fallback: posicional) ---
        used_bf: set = set()
        for i in range(_bigfive_n):
            trait = selected_traits[i].trait if i < len(selected_traits) else None
            if trait and behavioral:
                bf_comp, idx = self._select_comp_by_trait(trait, behavioral, used_bf)
                used_bf.add(idx)
            else:
                available = [j for j in range(len(behavioral)) if j not in used_bf]
                idx = available[0] if available else 0
                bf_comp = behavioral[idx] if behavioral else technical[0]
                used_bf.add(idx)
            questions.append(await self._generate_with_validation(
                self._generate_bigfive_question, bf_comp,
                jd_text=jd, skill_or_trait=trait or bf_comp.name, question_category="behavioral",
                ocean_trait=trait,
            ))

        target_count = _dist["total"]

        if len(questions) < target_count:
            logger.warning(f"Generated only {len(questions)}/{target_count} questions due to limited competencies")

        return questions[:target_count]

    # -----------------------------------------------------------------------
    # F6.8 — Validação automática pós-geração (determinística + LLM anchoring)
    # -----------------------------------------------------------------------

    _BIAS_MARKERS_RE = re.compile(
        r"\b(homem|mulher|masculino|feminino|gênero|raça|etnia|origem|religião|"
        r"casad[oa]|filh[oa]s?|grávid[ao]|deficiência)\b",
        re.IGNORECASE,
    )
    _HYPOTHETICAL_RE = re.compile(
        r"\b(como você faria se|imagine que|suponha que|se você fosse|"
        r"o que você faria se|e se você)\b",
        re.IGNORECASE,
    )
    _PAST_VERB_RE = re.compile(
        r"\b(conte|descreva|fale|dê um exemplo|me diga|relat[ea]|compartilhe)\b",
        re.IGNORECASE,
    )

    def _validate_deterministic(self, text: str) -> list[str]:
        """F6.8 Estágio 1 — verificações determinísticas (regex, ~0 ms).

        Returns:
            Lista de flags de falha (vazia = aprovado).
        """
        flags: list[str] = []
        word_count = len(text.split())
        if word_count < 15 or word_count > 80:
            flags.append(f"length_out_of_range:{word_count}_words")
        if self._HYPOTHETICAL_RE.search(text):
            flags.append("hypothetical_phrasing")
        if self._BIAS_MARKERS_RE.search(text):
            flags.append("bias_marker_detected")
        if not self._PAST_VERB_RE.search(text):
            flags.append("missing_situational_verb")
        return flags

    async def _validate_jd_anchor(
        self,
        question_text: str,
        jd_text: str,
        skill_or_trait: str,
        question_category: str = "technical",
    ) -> dict:
        """F6.8.1 — Validação de ancoragem no JD via LLM (temperature=0.0).

        Returns dict com campos: is_anchored, evidence_in_jd, anchor_type,
        confidence, anchor_explanation, suggestion.
        """
        system_prompt = (
            "Você é um auditor de qualidade de perguntas de triagem.\n"
            "Sua única tarefa é verificar se a pergunta gerada é ANCORADA no Job Description fornecido.\n\n"
            "Uma pergunta é ANCORADA quando:\n"
            "- Refere-se a uma responsabilidade, skill, contexto ou desafio EXPLICITAMENTE mencionado no JD\n"
            "- Não poderia ser feita com a mesma especificidade para qualquer outra vaga\n\n"
            "Uma pergunta NÃO é ancorada quando:\n"
            '- Poderia ser feita para qualquer cargo do mesmo nível ("Descreva um projeto desafiador...")\n'
            "- Refere-se a skills ou contextos ausentes do JD\n"
            "- É genérica o suficiente para ser reutilizada em vagas completamente diferentes\n\n"
            "REGRAS:\n"
            "- Retorne APENAS o JSON. Sem texto fora do JSON.\n"
            '- "evidence_in_jd" deve ser uma citação LITERAL do JD entre aspas — nunca paráfrase\n'
            '- Se a pergunta não for ancorada, "evidence_in_jd" deve ser "" (string vazia)\n'
            '- "anchor_type" classifica o tipo de ancoragem encontrada'
        )
        user_prompt = (
            f"Job Description da vaga (texto completo ou trecho relevante):\n"
            f"---\n{jd_text[:3000]}\n---\n\n"
            f"Skill ou trait que a pergunta avalia: {skill_or_trait}\n"
            f"Tipo de pergunta: {question_category} (technical | behavioral)\n\n"
            f'Pergunta gerada para validar:\n"{question_text}"\n\n'
            "Retorne o seguinte JSON (sem texto fora do JSON):\n"
            "{\n"
            '  "is_anchored": true|false,\n'
            '  "evidence_in_jd": "trecho literal exato do JD (vazio se não ancorada)",\n'
            '  "anchor_type": "responsibility | skill | context | challenge | none",\n'
            '  "confidence": "high | medium | low",\n'
            '  "anchor_explanation": "em 1 frase: por que esta pergunta é ou não é específica para este JD",\n'
            '  "suggestion": "reformulação sugerida apenas se is_anchored = false, senão string vazia"\n'
            "}"
        )
        full_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
        try:
            response = await self.llm.claude.bind(temperature=0.0, max_tokens=300).ainvoke(full_prompt)
            result = safe_json_parse(response.content, fallback=None)
            if result and isinstance(result, dict) and "is_anchored" in result:
                return result
        except Exception as e:
            logger.warning(f"WSI F6.8.1 anchor validation failed: {e}")
        # Fallback: assume ancorada para não bloquear indefinidamente
        return {
            "is_anchored": True,
            "evidence_in_jd": "",
            "anchor_type": "none",
            "confidence": "low",
            "anchor_explanation": "Validação de ancoragem indisponível — aprovado automaticamente.",
            "suggestion": "",
        }

    async def _generate_with_validation(
        self,
        gen_fn: Callable,
        competency: "Competency",
        jd_text: Optional[str] = None,
        skill_or_trait: Optional[str] = None,
        question_category: str = "technical",
        **gen_kwargs,
    ) -> "WSIQuestion":
        """F6.8 wrapper — gera pergunta com até 3 tentativas de validação.

        Fluxo:
        1. Gera pergunta via gen_fn(competency, **gen_kwargs)
        2. Estágio 1: _validate_deterministic → se falhar, regenera com hint
        3. Estágio 2: _validate_jd_anchor (se jd_text fornecido) → se falhar, regenera com suggestion
        4. Após 3 falhas em qualquer estágio, marca needs_manual_review=True e retorna
        """
        MAX_RETRIES = 3
        last_question: Optional["WSIQuestion"] = None
        improvement_hint: Optional[str] = None

        for attempt in range(1, MAX_RETRIES + 1):
            if improvement_hint:
                gen_kwargs["improvement_hint"] = improvement_hint

            question = await gen_fn(competency, **gen_kwargs)
            last_question = question

            # Estágio 1 — determinístico
            det_flags = self._validate_deterministic(question.question_text)
            if det_flags:
                logger.warning(
                    f"WSI F6.8 det. flags (attempt {attempt}/{MAX_RETRIES}) "
                    f"for '{competency.name}': {det_flags}"
                )
                improvement_hint = (
                    f"A pergunta anterior falhou nas seguintes verificações automáticas: {det_flags}. "
                    "Corrija: use verbo situacional no imperativo (Conte/Descreva), "
                    "mantenha entre 15 e 80 palavras, evite linguagem hipotética e marcadores de viés."
                )
                if attempt == MAX_RETRIES:
                    question.needs_manual_review = True
                    question.validation_flags = {"deterministic": det_flags}
                    logger.error(
                        f"WSI F6.8 max retries reached for '{competency.name}'. "
                        "Marking needs_manual_review=True."
                    )
                    return question
                continue

            # Estágio 2 — ancoragem no JD (somente se jd_text disponível)
            if jd_text and skill_or_trait:
                anchor = await self._validate_jd_anchor(
                    question_text=question.question_text,
                    jd_text=jd_text,
                    skill_or_trait=skill_or_trait,
                    question_category=question_category,
                )
                if not anchor.get("is_anchored", True):
                    logger.warning(
                        f"WSI F6.8.1 not anchored (attempt {attempt}/{MAX_RETRIES}) "
                        f"for '{competency.name}': {anchor.get('anchor_explanation')}"
                    )
                    suggestion = anchor.get("suggestion", "")
                    improvement_hint = (
                        f"A pergunta anterior não está ancorada no Job Description. "
                        f"Sugestão de reformulação: {suggestion}"
                        if suggestion else
                        "A pergunta anterior é genérica demais. Referencie explicitamente "
                        "uma responsabilidade ou skill mencionada no JD."
                    )
                    if attempt == MAX_RETRIES:
                        question.needs_manual_review = True
                        question.validation_flags = {
                            "anchor": anchor,
                            "attempts": MAX_RETRIES,
                        }
                        logger.error(
                            f"WSI F6.8.1 max retries reached for '{competency.name}'. "
                            "Marking needs_manual_review=True."
                        )
                        return question
                    continue
                # Persiste metadados de ancoragem nos flags (auditável)
                question.validation_flags = {
                    "anchor_type": anchor.get("anchor_type"),
                    "confidence": anchor.get("confidence"),
                    "evidence_in_jd": anchor.get("evidence_in_jd", ""),
                }

            return question

        # Nunca deveria chegar aqui, mas retorna last_question por segurança
        if last_question:
            last_question.needs_manual_review = True
        return last_question  # type: ignore[return-value]

    async def _generate_cbi_question(
        self, competency: Competency, improvement_hint: Optional[str] = None
    ) -> WSIQuestion:
        """Gera pergunta CBI (contextual) para competência."""
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA (baseada em validação anterior):\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta CBI (Competency-Based Interviewing) para avaliar: **{competency.name}**

Nível da vaga: {competency.seniority_level}
Tipo: {competency.type}

Princípio CBI: "Comportamentos passados são os melhores preditores de performance futura."

Estrutura: "Conte sobre uma situação em que [contexto específico]. O que você fez e qual foi o resultado?"

Exemplos de referência do RAG:
{self.question_templates[:2000]}
{hint_block}
Responda APENAS em JSON:
{{
  "framework": "CBI",
  "question_type": "contextual",
  "question_text": "[Pergunta aqui]",
  "expected_signals": ["Contexto claro", "Ação técnica", "Resultado mensurável"],
  "scoring_criteria": {{
    "score_5": "Contexto complexo + decisões avançadas + impacto quantificado",
    "score_3": "Contexto claro + ação técnica + resultado visível",
    "score_1": "Contexto vago + ação genérica + sem resultado"
  }}
}}"""

        try:
            response = await self.llm.claude.bind(temperature=0.7).ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "framework": "CBI",
                "question_type": "contextual",
                "question_text": f"Conte sobre uma experiência onde você aplicou {competency.name} em um projeto real. Qual foi o contexto, sua ação e o resultado?",
                "expected_signals": ["Contexto claro", "Ação específica", "Resultado mensurável"],
                "scoring_criteria": {
                    "score_5": "Projeto complexo + decisões avançadas + impacto quantificado",
                    "score_3": "Projeto real + ação técnica + resultado visível",
                    "score_1": "Projeto vago + ação genérica"
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate CBI question for {competency.name}: {e}")
            # Use fallback
            data = {
                "framework": "CBI",
                "question_type": "contextual",
                "question_text": f"Conte sobre uma experiência onde você aplicou {competency.name} em um projeto real. Qual foi o contexto, sua ação e o resultado?",
                "expected_signals": ["Contexto claro", "Ação específica", "Resultado mensurável"],
                "scoring_criteria": {
                    "score_5": "Projeto complexo + decisões avançadas + impacto quantificado",
                    "score_3": "Projeto real + ação técnica + resultado visível",
                    "score_1": "Projeto vago + ação genérica"
                }
            }
        
        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="CBI",
            question_type="contextual",
            question_text=data["question_text"],
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Contexto", "Ação", "Resultado"]),
            scoring_criteria=data.get("scoring_criteria", {}),
            is_critical=competency.is_critical,
        )
    
    async def _generate_dreyfus_question(
        self, competency: Competency, improvement_hint: Optional[str] = None
    ) -> WSIQuestion:
        """Gera pergunta Dreyfus (autodeclaração) para competência."""
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta Dreyfus (autodeclaração) para avaliar: **{competency.name}**

Estrutura: "De 1 a 5, quanto você domina [tecnologia]? Pode citar um projeto recente onde aplicou?"

Combina:
- Autodeclaração (score 1-5)
- Validação contextual (projeto real)
{hint_block}
Responda APENAS em JSON com mesma estrutura anterior."""

        try:
            response = await self.llm.claude.bind(temperature=0.75).ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "framework": "Dreyfus",
                "question_type": "autodeclaration",
                "question_text": f"De 1 a 5, quanto você se considera proficiente em {competency.name}? Pode citar um projeto recente onde aplicou essa competência?",
                "expected_signals": ["Autodeclaração honesta", "Projeto real mencionado", "Contexto de aplicação"],
                "scoring_criteria": {
                    "score_5": "Expert com projeto complexo e impacto mensurável",
                    "score_3": "Competente com projeto real e aplicação prática",
                    "score_1": "Iniciante sem experiência prática"
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate Dreyfus question for {competency.name}: {e}")
            # Use fallback
            data = {
                "framework": "Dreyfus",
                "question_type": "autodeclaration",
                "question_text": f"De 1 a 5, quanto você se considera proficiente em {competency.name}? Pode citar um projeto recente onde aplicou essa competência?",
                "expected_signals": ["Autodeclaração honesta", "Projeto real mencionado", "Contexto de aplicação"],
                "scoring_criteria": {
                    "score_5": "Expert com projeto complexo e impacto mensurável",
                    "score_3": "Competente com projeto real e aplicação prática",
                    "score_1": "Iniciante sem experiência prática"
                }
            }
        
        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="Dreyfus",
            question_type="autodeclaration",
            question_text=data["question_text"],
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Autodeclaração", "Projeto", "Contexto"]),
            scoring_criteria=data.get("scoring_criteria", {})
        )
    
    async def _generate_bloom_question(
        self, competency: Competency, improvement_hint: Optional[str] = None
    ) -> WSIQuestion:
        """Gera microcase Bloom para competência."""
        seniority_level_map = {
            "junior": 3,
            "pleno": 4,
            "senior": 4,
            "lead": 5,
            "executive": 5
        }
        bloom_level = seniority_level_map.get(competency.seniority_level, 3)
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta tipo microcase (Bloom Level {bloom_level}) para: **{competency.name}**

Nível cognitivo esperado: {"APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"}

Exemplos:
- Level 3 (Aplicar): "Como você implementaria [solução]?"
- Level 4 (Analisar): "Como diagnosticaria [problema]?"
- Level 5 (Criar): "Projete [arquitetura/solução]"
{hint_block}
Responda APENAS em JSON."""

        cognitive_level = "APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"
        
        try:
            response = await self.llm.claude.bind(temperature=0.75).ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "framework": "Bloom",
                "question_type": "microcase",
                "question_text": f"Como você abordaria um desafio técnico envolvendo {competency.name}? Descreva sua estratégia de solução.",
                "expected_signals": ["Raciocínio técnico", "Abordagem estruturada", "Conhecimento aplicado"],
                "scoring_criteria": {
                    "score_5": f"Nível {cognitive_level}: Solução completa, trade-offs considerados, best practices",
                    "score_3": f"Nível {cognitive_level}: Solução funcional com conceitos corretos",
                    "score_1": "Conhecimento teórico sem aplicação prática"
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate Bloom question for {competency.name}: {e}")
            # Use fallback
            data = {
                "framework": "Bloom",
                "question_type": "microcase",
                "question_text": f"Como você abordaria um desafio técnico envolvendo {competency.name}? Descreva sua estratégia de solução.",
                "expected_signals": ["Raciocínio técnico", "Abordagem estruturada", "Conhecimento aplicado"],
                "scoring_criteria": {
                    "score_5": f"Nível {cognitive_level}: Solução completa, trade-offs considerados, best practices",
                    "score_3": f"Nível {cognitive_level}: Solução funcional com conceitos corretos",
                    "score_1": "Conhecimento teórico sem aplicação prática"
                }
            }
        
        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="Bloom",
            question_type="microcase",
            question_text=data["question_text"],
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Raciocínio", "Abordagem", "Conhecimento"]),
            scoring_criteria=data.get("scoring_criteria", {})
        )
    
    def _select_comp_by_trait(
        self,
        trait: str,
        behavioral: List["Competency"],
        used_indices: set,
    ) -> tuple:
        """F6.6 — Seleciona competência comportamental por afinidade de trait OCEAN.

        Estratégia:
        1. Match exato: busca competência com big_five_mapping == trait
        2. Fallback posicional: próxima disponível não usada
        3. Último recurso: primeira da lista

        Args:
            trait: trait OCEAN alvo (openness|conscientiousness|extraversion|agreeableness|stability)
            behavioral: lista ordenada de competências comportamentais
            used_indices: índices já utilizados (evita repetição)

        Returns:
            Tuple[Competency, int] — competência selecionada e seu índice
        """
        # 1. Match exato por big_five_mapping
        for i, comp in enumerate(behavioral):
            if i not in used_indices and comp.big_five_mapping == trait:
                logger.info(f"WSI F6.6 trait-match (exact): {trait} → {comp.name} (idx={i})")
                return comp, i
        # 2. Fallback posicional — próxima disponível
        for i, comp in enumerate(behavioral):
            if i not in used_indices:
                logger.info(f"WSI F6.6 trait-match (fallback positional): {trait} → {comp.name} (idx={i})")
                return comp, i
        # 3. Último recurso — reusar primeira
        logger.warning(f"WSI F6.6 trait-match: no available competency for {trait}, reusing behavioral[0]")
        return behavioral[0], 0

    async def _generate_bigfive_question(
        self,
        competency: Competency,
        ocean_trait: Optional[str] = None,
        improvement_hint: Optional[str] = None,
    ) -> WSIQuestion:
        """Gera pergunta Big Five (situacional) para competência.

        Args:
            competency: Competência a avaliar
            ocean_trait: Trait OCEAN alvo (F6.6). Quando fornecido, calibra a pergunta
                         para revelar especificamente esse trait.
            improvement_hint: Sugestão de melhoria da validação F6.8.1 (ancoragem no JD).
        """
        _TRAIT_LABELS = {
            "openness":          "Abertura a mudanças — inovação, curiosidade, aprendizado",
            "conscientiousness": "Organização e disciplina — entregas, rigor, método",
            "extraversion":      "Sociabilidade — comunicação, assertividade, energia",
            "agreeableness":     "Cooperação — empatia, colaboração, gestão de stakeholders",
            "stability":         "Estabilidade emocional — resiliência sob pressão",
        }
        trait_context = (
            f"\nTrait OCEAN alvo: {ocean_trait} ({_TRAIT_LABELS.get(ocean_trait, '')})\n"
            "A pergunta deve revelar especificamente este trait."
            if ocean_trait else ""
        )
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )

        prompt = f"""Gere UMA pergunta Big Five (situacional) para avaliar: **{competency.name}**

Tipo: Comportamental/Cultural

Estrutura: "Como você reage quando...", "Descreva uma situação em que..."

Foco em traços OCEAN:
- Openness: Inovação, aprendizado
- Conscientiousness: Organização, entrega
- Extraversion: Comunicação, liderança
- Agreeableness: Colaboração
- Emotional Stability: Pressão
{trait_context}{hint_block}
Responda APENAS em JSON."""

        try:
            response = await self.llm.claude.bind(temperature=0.8).ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "framework": "BigFive",
                "question_type": "situational",
                "question_text": f"Descreva uma situação recente onde você demonstrou {competency.name}. Como você lidou com o desafio e qual foi o resultado?",
                "expected_signals": ["Situação real", "Comportamento específico", "Resultado alcançado"],
                "scoring_criteria": {
                    "score_5": "Situação complexa + comportamento exemplar + impacto positivo mensurável",
                    "score_3": "Situação clara + comportamento adequado + resultado satisfatório",
                    "score_1": "Situação vaga + comportamento genérico + sem resultado claro"
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate BigFive question for {competency.name}: {e}")
            # Use fallback
            data = {
                "framework": "BigFive",
                "question_type": "situational",
                "question_text": f"Descreva uma situação recente onde você demonstrou {competency.name}. Como você lidou com o desafio e qual foi o resultado?",
                "expected_signals": ["Situação real", "Comportamento específico", "Resultado alcançado"],
                "scoring_criteria": {
                    "score_5": "Situação complexa + comportamento exemplar + impacto positivo mensurável",
                    "score_3": "Situação clara + comportamento adequado + resultado satisfatório",
                    "score_1": "Situação vaga + comportamento genérico + sem resultado claro"
                }
            }
        
        scoring_criteria = data.get("scoring_criteria", {})
        if ocean_trait:
            scoring_criteria["ocean_trait"] = ocean_trait

        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="BigFive",
            question_type="situational",
            question_text=data["question_text"],
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Situação", "Comportamento", "Resultado"]),
            scoring_criteria=scoring_criteria,
        )


class WSIResponseAnalyzer:
    """
    Analisador de respostas com scoring DETERMINÍSTICO baseado em Dreyfus + Bloom.
    
    IMPORTANTE: Os scores são calculados de forma 100% determinística.
    O LLM NÃO participa do cálculo de scores - apenas da extração de informações.
    """
    
    def __init__(self, llm):
        self.llm = llm
    
    async def analyze(
        self,
        question: WSIQuestion,
        response: str
    ) -> ResponseAnalysis:
        """
        Analisa resposta usando cálculos 100% DETERMINÍSTICOS.
        
        Metodologia WSI (scoring determinístico):
        1. Extrai autodeclaração via regex
        2. Calcula contexto via indicadores
        3. Classifica Bloom via keywords
        4. Classifica Dreyfus via anos + contexto
        5. Detecta red flags via regras fixas
        6. Aplica fórmula fixa: Score = (0.6 × Autodec) + (0.4 × Contexto) - Penalty + Bonus
        
        NENHUM LLM é usado para calcular scores.
        """
        try:
            result: DeterministicWSIResult = calculate_wsi_deterministic(
                response_text=response,
                competency_name=question.competency,
                question_framework=question.framework
            )
            
            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=result.autodeclaracao_score,
                context_score=result.context_score,
                bloom_level=result.bloom_level,
                dreyfus_level=result.dreyfus_level,
                evidences=result.evidences,
                red_flags=result.red_flags,
                consistency_penalty=result.penalty,
                final_score=result.final_score,
                justification=f"{result.justification} | Fórmula: {result.formula_applied}"
            )
        except Exception as e:
            logger.error(f"Deterministic analysis failed for {question.competency}: {e}")
            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=3.0,
                context_score=3.0,
                bloom_level=3,
                dreyfus_level=3,
                evidences=[],
                red_flags=["Erro no processamento determinístico"],
                consistency_penalty=0.0,
                final_score=3.0,
                justification=f"Fallback aplicado devido a erro: {str(e)}"
            )


class WSIScoreCalculator:
    """Calculadora de WSI (média ponderada) e ranking."""
    
    def calculate(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        responses: List[ResponseAnalysis],
        weights: Dict[str, float]
    ) -> WSIResult:
        """
        Calcula WSI final usando média ponderada.
        
        Fórmula: WSI = Σ(peso_i × score_i) / Σ(pesos)
        
        Classificação WSI:
        - 4.5-5.0: Excelente
        - 4.0-4.4: Alto
        - 3.0-3.9: Médio
        - 2.0-2.9: Regular
        - < 2.0: Baixo
        """
        
        # Separar respostas por tipo de competência
        technical_responses = [r for r in responses if r.competency in weights and "python" in r.competency.lower() or "javascript" in r.competency.lower() or "sql" in r.competency.lower() or "docker" in r.competency.lower() or "aws" in r.competency.lower()]
        
        # Se não conseguiu detectar técnicas por nome, assume primeiras 70%
        if not technical_responses:
            technical_count = int(len(responses) * 0.7)
            technical_responses = responses[:technical_count]
        
        behavioral_responses = [r for r in responses if r not in technical_responses]
        
        # Calcular WSI Técnico
        technical_wsi = 0.0
        technical_weight_sum = 0.0
        
        for response in technical_responses:
            weight = weights.get(response.competency, 0.15)  # Default 15%
            technical_wsi += response.final_score * weight
            technical_weight_sum += weight
        
        if technical_weight_sum > 0:
            technical_wsi = technical_wsi / technical_weight_sum
        else:
            technical_wsi = 0.0
        
        # Calcular WSI Comportamental
        behavioral_wsi = 0.0
        behavioral_weight_sum = 0.0
        
        for response in behavioral_responses:
            weight = weights.get(response.competency, 0.10)  # Default 10%
            behavioral_wsi += response.final_score * weight
            behavioral_weight_sum += weight
        
        if behavioral_weight_sum > 0:
            behavioral_wsi = behavioral_wsi / behavioral_weight_sum
        elif len(behavioral_responses) > 0:
            # Se não tem weights, usa média simples
            behavioral_wsi = sum(r.final_score for r in behavioral_responses) / len(behavioral_responses)
        else:
            # Se não tem respostas comportamentais, usa 70% do técnico
            behavioral_wsi = technical_wsi * 0.7
        
        # Calcular WSI Geral (70% técnico + 30% comportamental)
        overall_wsi = (technical_wsi * 0.7) + (behavioral_wsi * 0.3)
        
        # Classificação
        if overall_wsi >= 4.5:
            classification = "excelente"
        elif overall_wsi >= 4.0:
            classification = "alto"
        elif overall_wsi >= 3.0:
            classification = "medio"
        elif overall_wsi >= 2.0:
            classification = "regular"
        else:
            classification = "baixo"
        
        return WSIResult(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            technical_wsi=round(technical_wsi, 2),
            behavioral_wsi=round(behavioral_wsi, 2),
            overall_wsi=round(overall_wsi, 2),
            classification=classification,
            percentile=None,  # Será calculado depois comparando com outros candidatos
            response_analyses=responses
        )
    
    def calculate_percentiles(
        self,
        results: List[WSIResult]
    ) -> List[WSIResult]:
        """
        Calcula percentis para um grupo de candidatos.
        
        Exemplo: Candidato com WSI 4.2 que está no top 10%
        terá percentile = 90.
        """
        if not results:
            return results
        
        # Ordenar por overall_wsi descendente
        sorted_results = sorted(results, key=lambda r: r.overall_wsi, reverse=True)
        total = len(sorted_results)
        
        # Atribuir percentis e ranking
        for idx, result in enumerate(sorted_results):
            result.percentile = int(((total - idx) / total) * 100)
            # Note: percentile seria melhor salvar no banco, não mutar aqui
            # Mas para simplificar o exemplo, estamos mutando
        
        return sorted_results


class WSIReportGenerator:
    """Gerador de pareceres estruturados e feedbacks com RAG."""
    
    def __init__(self, llm):
        self.llm = llm
        self._load_rag_templates()
    
    def _load_rag_templates(self):
        """Carrega templates do RAG."""
        from pathlib import Path
        
        rag_dir = Path("lia-agent-system/training/rag_knowledge/wsi_methodology")
        self.report_templates = (rag_dir / "report_templates.md").read_text(encoding="utf-8") if (rag_dir / "report_templates.md").exists() else ""
    
    async def generate_report(
        self,
        candidate_id: str,
        wsi_result: WSIResult,
        responses: List[ResponseAnalysis]
    ) -> StructuredReport:
        """Gera parecer estruturado para recrutadores."""
        
        # Preparar contexto das respostas
        responses_summary = "\n".join([
            f"- {r.competency} (Score: {r.final_score}/5): {r.justification}"
            for r in responses
        ])
        
        tech_responses = [r for r in responses if r.competency and any(
            kw in r.competency.lower() for kw in ["python", "react", "java", "sql", "aws", "node", "go", "rust", "docker", "kubernetes", "api", "backend", "frontend", "devops", "data", "machine", "deep", "cloud"]
        )]
        behav_responses = [r for r in responses if r not in tech_responses]
        
        tech_strong = [f"{r.competency} ({r.final_score}/5)" for r in tech_responses if r.final_score >= 4.0]
        tech_gaps = [f"{r.competency} ({r.final_score}/5)" for r in tech_responses if r.final_score < 3.0]
        behav_strong = [f"{r.competency} ({r.final_score}/5)" for r in behav_responses if r.final_score >= 4.0]
        
        prompt = f"""Gere um parecer estruturado completo para recrutadores usando a metodologia WSI.

CANDIDATO ID: {candidate_id}

WSI RESULTADOS:
- WSI Técnico: {wsi_result.technical_wsi}/5.0
- WSI Comportamental: {wsi_result.behavioral_wsi}/5.0
- WSI Geral: {wsi_result.overall_wsi}/5.0
- Classificação: {wsi_result.classification.upper()}

ANÁLISES DAS RESPOSTAS:
{responses_summary}

PONTOS FORTES TÉCNICOS: {tech_strong or "Nenhum score >= 4.0"}
GAPS TÉCNICOS: {tech_gaps or "Nenhum score < 3.0"}
PONTOS FORTES COMPORTAMENTAIS: {behav_strong or "Nenhum score >= 4.0"}

TEMPLATES DE REFERÊNCIA (exemplos do RAG):
{self.report_templates[:3000]}

---

CRITÉRIOS OBJETIVOS PARA DECISÃO (OBRIGATÓRIO seguir — WSI_CUTOFFS canônicos):
- WSI Geral >= 3.75 → decisao = "APROVADO" (= 7.5/10)
- WSI Geral >= 3.0 e < 3.75 → decisao = "AGUARDANDO" / "EM_AVALIACAO" (= 6.0–7.4/10)
- WSI Geral < 3.0 → decisao = "NÃO APROVADO" (= < 6.0/10)
- EXCEÇÃO: Se WSI Geral >= 3.75 MAS há red_flags graves → rebaixa para "AGUARDANDO"

REGRAS DE QUALIDADE DO PARECER:
1. **Sumário Executivo** DEVE ter 2-3 frases completas (mínimo 100 caracteres), incluindo: perfil resumido, principal ponto forte e recomendação clara
2. **Análise Técnica**: Citar ao menos 2 evidências concretas extraídas das respostas (projetos, métricas, tecnologias mencionadas)
3. **Análise Comportamental**: Scores de 1.0 a 5.0 para cada dimensão, baseados nas respostas observadas
4. **Fit Cultural**: Identificar ao menos 1 valor alinhado e 1 ponto de atenção quando WSI < 4.0
5. **Recomendação**: Justificativa DEVE referenciar dados do WSI (scores, classificação). Próximos passos DEVEM ser acionáveis

Gere parecer estruturado incluindo:
1. **Sumário Executivo** (2-3 frases): Resumo do perfil, pontos fortes, recomendação
2. **Análise Técnica**: Pontos fortes (top 3), gaps (se houver), evidências concretas das respostas
3. **Análise Comportamental**: Colaboração, inovação, organização, resiliência (scores 1.0-5.0)
4. **Fit Cultural**: Score geral, valores alinhados, pontos de atenção
5. **Recomendação**: Decisão (seguir critérios acima), justificativa com dados, próximos passos acionáveis

RETORNE APENAS JSON:
{{
  "executive_summary": "...",
  "technical_analysis": {{
    "pontos_fortes": ["...", "...", "..."],
    "gaps": ["..."],
    "evidencias": ["Projeto X", "Métrica Y"]
  }},
  "behavioral_analysis": {{
    "colaboracao": 4.0,
    "inovacao": 4.5,
    "organizacao": 4.0,
    "resiliencia": 3.5
  }},
  "cultural_fit": {{
    "score": 4.0,
    "valores_alinhados": ["Excelência técnica", "..."],
    "atencoes": ["..."]
  }},
  "recommendation": {{
    "decisao": "APROVADO",
    "justificativa": "...",
    "proximos_passos": ["Agendar técnica", "..."]
  }}
}}"""

        try:
            response = await self.llm.claude.ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "executive_summary": f"Candidato com WSI {wsi_result.classification} ({wsi_result.overall_wsi}/5.0). Análise detalhada não disponível.",
                "technical_analysis": {
                    "pontos_fortes": ["Análise em processamento"],
                    "gaps": [],
                    "evidencias": []
                },
                "behavioral_analysis": {
                    "colaboracao": 3.0,
                    "inovacao": 3.0,
                    "organizacao": 3.0,
                    "resiliencia": 3.0
                },
                "cultural_fit": {
                    "score": 3.0,
                    "valores_alinhados": ["Em avaliação"],
                    "atencoes": []
                },
                "recommendation": {
                    "decisao": "AGUARDANDO",
                    "justificativa": "Análise em processamento - revisar manualmente",
                    "proximos_passos": ["Revisar análise manualmente"]
                }
            })
        except Exception as e:
            logger.error(f"Failed to generate report for candidate {candidate_id}: {e}")
            # Use fallback
            data = {
                "executive_summary": f"Candidato com WSI {wsi_result.classification} ({wsi_result.overall_wsi}/5.0). Análise detalhada não disponível.",
                "technical_analysis": {
                    "pontos_fortes": ["Análise em processamento"],
                    "gaps": [],
                    "evidencias": []
                },
                "behavioral_analysis": {
                    "colaboracao": 3.0,
                    "inovacao": 3.0,
                    "organizacao": 3.0,
                    "resiliencia": 3.0
                },
                "cultural_fit": {
                    "score": 3.0,
                    "valores_alinhados": ["Em avaliação"],
                    "atencoes": []
                },
                "recommendation": {
                    "decisao": "AGUARDANDO",
                    "justificativa": "Análise em processamento - revisar manualmente",
                    "proximos_passos": ["Revisar análise manualmente"]
                }
            }
        
        return StructuredReport(
            candidate_id=candidate_id,
            wsi_result=wsi_result,
            executive_summary=data.get("executive_summary", "Análise não disponível"),
            technical_analysis=data.get("technical_analysis", {}),
            behavioral_analysis=data.get("behavioral_analysis", {}),
            cultural_fit=data.get("cultural_fit", {}),
            recommendation=data.get("recommendation", {})
        )
    
    async def generate_feedback(
        self,
        wsi_result: WSIResult,
        responses: List[ResponseAnalysis],
        decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    ) -> CandidateFeedback:
        """Gera feedback construtivo para candidato."""
        
        # Identificar pontos fortes
        strong_responses = [r for r in responses if r.final_score >= 4.0]
        development_responses = [r for r in responses if r.final_score < 3.5]
        
        strong_competencies = [f"{r.competency} ({r.final_score}/5)" for r in strong_responses]
        development_competencies = [f"{r.competency} ({r.final_score}/5)" for r in development_responses]
        
        tech_strong = [r for r in responses if r.final_score >= 4.0 and r not in development_responses]
        behav_strong_list = [r.competency for r in tech_strong if r.competency and not any(
            kw in r.competency.lower() for kw in ["python", "react", "java", "sql", "aws", "node", "go", "rust", "docker", "kubernetes", "api", "backend", "frontend", "devops", "data", "machine", "deep", "cloud"]
        )]
        
        tone_map = {
            "aprovado": "Empolgado e encorajador. Celebre as conquistas, demonstre entusiasmo genuíno pela performance.",
            "aguardando": "Construtivo e empático. Reconheça pontos fortes, posicione gaps como oportunidades de crescimento.",
            "nao_aprovado": "Respeitoso e construtivo. Agradeça sinceramente, destaque pontos positivos antes dos gaps, ofereça orientação de desenvolvimento."
        }
        
        prompt = f"""Gere um feedback estruturado e construtivo para o candidato.

DECISÃO: {decision.upper()}
WSI GERAL: {wsi_result.overall_wsi}/5.0 ({wsi_result.classification})

PONTOS FORTES TÉCNICOS: {strong_competencies}
PONTOS FORTES COMPORTAMENTAIS: {behav_strong_list or "Nenhum identificado com score >= 4.0"}
OPORTUNIDADES DE DESENVOLVIMENTO: {development_competencies}

TEMPLATES DE REFERÊNCIA (exemplos do RAG):
{self.report_templates[10000:13000]}

---

TOM OBRIGATÓRIO: {tone_map.get(decision, "Construtivo e empático")}

REGRAS DE QUALIDADE DO FEEDBACK:
1. **main_message**: Mínimo 150 caracteres. NUNCA começar com "Infelizmente". Começar agradecendo a participação.
2. **technical_strengths**: Citar ao menos 2 competências específicas mencionadas nas respostas. Não usar genéricos como "Participação no processo".
3. **development_opportunities**: Ser específico sobre o que melhorar (ex: "Aprofundar conhecimento em design patterns" vs "Estudar mais").
4. **behavioral_strengths**: Citar comportamentos observados nas respostas (ex: "Demonstrou capacidade analítica ao descrever o diagnóstico do problema").
5. **next_steps**: Ser claro e acionável. Para APROVADO: próxima etapa do processo. Para AGUARDANDO: o que será avaliado. Para NÃO APROVADO: encorajar nova candidatura futura.
6. **personalized_tip**: Uma dica prática e específica baseada nos gaps identificados.
7. **development_plan**: Curto prazo (1-3 meses) e médio prazo (3-6 meses) com ações concretas.
8. **recommended_resources**: Ao menos 2 recursos reais (cursos, livros, certificações, plataformas) relevantes para os gaps.

NUNCA revelar scores numéricos ao candidato. Usar termos qualitativos ("excelente domínio", "bom conhecimento", "oportunidade de aprofundamento").

RETORNE APENAS JSON:
{{
  "main_message": "...",
  "technical_strengths": ["...", "..."],
  "development_opportunities": ["...", "..."],
  "behavioral_strengths": ["...", "..."],
  "next_steps": "...",
  "personalized_tip": "...",
  "development_plan": {{"curto_prazo": ["..."], "medio_prazo": ["..."]}},
  "recommended_resources": ["Curso X", "Projeto Y"]
}}"""

        try:
            response = await self.llm.claude.ainvoke(prompt)
            data = safe_json_parse(response.content, fallback={
                "main_message": f"Obrigado por participar do processo seletivo. Seu desempenho foi {wsi_result.classification}.",
                "technical_strengths": ["Participação no processo"],
                "development_opportunities": ["Continue desenvolvendo suas habilidades"],
                "behavioral_strengths": ["Engajamento"],
                "next_steps": "Aguarde retorno da equipe de recrutamento.",
                "personalized_tip": "Continue aprimorando suas competências técnicas e comportamentais.",
                "development_plan": {"curto_prazo": ["Revisar conceitos fundamentais"], "medio_prazo": ["Desenvolver projetos práticos"]},
                "recommended_resources": []
            })
        except Exception as e:
            logger.error(f"Failed to generate feedback for candidate {wsi_result.candidate_id}: {e}")
            # Use fallback
            data = {
                "main_message": f"Obrigado por participar do processo seletivo. Seu desempenho foi {wsi_result.classification}.",
                "technical_strengths": ["Participação no processo"],
                "development_opportunities": ["Continue desenvolvendo suas habilidades"],
                "behavioral_strengths": ["Engajamento"],
                "next_steps": "Aguarde retorno da equipe de recrutamento.",
                "personalized_tip": "Continue aprimorando suas competências técnicas e comportamentais.",
                "development_plan": {"curto_prazo": ["Revisar conceitos fundamentais"], "medio_prazo": ["Desenvolver projetos práticos"]},
                "recommended_resources": []
            }
        
        return CandidateFeedback(
            candidate_id=wsi_result.candidate_id,
            decision=decision,
            main_message=data.get("main_message", "Obrigado por participar"),
            technical_strengths=data.get("technical_strengths", []),
            development_opportunities=data.get("development_opportunities", []),
            behavioral_strengths=data.get("behavioral_strengths", []),
            next_steps=data.get("next_steps", "Aguarde retorno"),
            personalized_tip=data.get("personalized_tip"),
            development_plan=data.get("development_plan"),
            recommended_resources=data.get("recommended_resources")
        )


# Global WSI service instance
wsi_service = WSIService()


async def generate_wsi_questions_tool(job_id: str, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
    result = await wsi_service.generate_from_simple_inputs(
        job_title=kwargs.get("job_title", ""),
        technical_skills=kwargs.get("technical_skills", []),
        behavioral_competencies=kwargs.get("behavioral_competencies", []),
        seniority=kwargs.get("seniority"),
        max_questions=count,
    )
    return [q.dict() if hasattr(q, "dict") else q for q in result]
