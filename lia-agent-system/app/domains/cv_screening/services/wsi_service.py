"""
WSI (WeDoTalent Skill Index) Service - Metodologia Científica de Avaliação.

Aplica 4 frameworks científicos:
1. CBI (Competency-Based Interviewing) - McClelland, 1973
2. Bloom's Taxonomy (Revisada) - Anderson et al., 2001
3. Dreyfus Model - Dreyfus & Dreyfus, 1980
4. Big Five (OCEAN) - Goldberg, 1992
"""
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import json
import uuid
import logging

from app.services.llm import llm_service
from app.services.wsi_deterministic_scorer import (
    calculate_wsi_deterministic,
    calculate_final_wsi_score,
    DeterministicWSIResult
)

logger = logging.getLogger(__name__)


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
    scoring_criteria: Dict[str, str]


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
    
    classification: Literal["excelente", "alto", "medio", "regular", "baixo"]
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
        mode: Literal["compact", "compact_plus"] = "compact"
    ) -> List[WSIQuestion]:
        """
        ETAPA 2: Gera perguntas científicas baseadas em competências.
        
        Aplica frameworks:
        - CBI para perguntas contextuais
        - Dreyfus para autodeclaração
        - Bloom para microcases
        - Big Five para fit comportamental
        
        Args:
            competencies: Lista de competências a avaliar
            mode: "compact" (6-8 perguntas) ou "compact_plus" (8-10)
            
        Returns:
            Lista de perguntas WSI estruturadas
        """
        return await self.question_generator.generate_all(competencies, mode)
    
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
    
    async def generate_all(
        self,
        competencies: List[Competency],
        mode: Literal["compact", "compact_plus"] = "compact"
    ) -> List[WSIQuestion]:
        """
        Gera todas as perguntas para as competências selecionadas.

        Estratégia:
        - compact:      6 perguntas (5-7 min WhatsApp)
        - compact_plus: 10 perguntas (8-12 min WhatsApp)

        Ambos os modos extraem 5 técnicas + 5 comportamentais do JD.
        A metodologia seleciona as mais relevantes por peso e is_critical.

        Distribuição compact (6 perguntas):
        - CBI técnico:        2 perguntas  (top 2 técnicas por is_critical + peso)
        - CBI comportamental: 1 pergunta   (top 1 comportamental por peso)
        - Dreyfus:            1 pergunta   (3ª técnica — autodeclaração)
        - Bloom:              1 pergunta   (4ª técnica — microcase)
        - Big Five:           1 pergunta   (2ª comportamental — fit cultural/situacional)

        Distribuição compact_plus (10 perguntas):
        - CBI técnico:        3 perguntas  (top 3 técnicas por is_critical + peso)
        - CBI comportamental: 3 perguntas  (top 3 comportamentais por peso)
        - Dreyfus:            2 perguntas  (4ª e 5ª técnicas — autodeclaração)
        - Bloom:              1 pergunta   (microcase — técnica com maior bloom_level)
        - Big Five:           1 pergunta   (4ª comportamental — fit cultural/situacional)
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

        questions = []

        if mode == "compact":
            # --- CBI técnico: top 2 técnicas ---
            for comp in technical[:2]:
                questions.append(await self._generate_cbi_question(comp))

            # --- CBI comportamental: top 1 comportamental ---
            if behavioral:
                questions.append(await self._generate_cbi_question(behavioral[0]))

            # --- Dreyfus: 3ª técnica (autodeclaração de proficiência) ---
            if len(technical) > 2:
                questions.append(await self._generate_dreyfus_question(technical[2]))

            # --- Bloom: 4ª técnica (microcase situacional) ---
            if len(technical) > 3:
                questions.append(await self._generate_bloom_question(technical[3]))

            # --- Big Five: 2ª comportamental (fit cultural / situacional OCEAN) ---
            bigfive_comp = behavioral[1] if len(behavioral) > 1 else (behavioral[0] if behavioral else technical[0])
            questions.append(await self._generate_bigfive_question(bigfive_comp))

        else:  # compact_plus — 10 perguntas
            # --- CBI técnico: top 3 técnicas ---
            for comp in technical[:3]:
                questions.append(await self._generate_cbi_question(comp))

            # --- CBI comportamental: top 3 comportamentais ---
            for comp in behavioral[:3]:
                questions.append(await self._generate_cbi_question(comp))

            # --- Dreyfus: 4ª e 5ª técnicas (autodeclaração) ---
            for comp in technical[3:5]:
                questions.append(await self._generate_dreyfus_question(comp))

            # --- Bloom: microcase — técnica não coberta ainda ---
            bloom_idx = min(5, len(technical) - 1)
            if bloom_idx >= 0 and len(technical) > 5:
                questions.append(await self._generate_bloom_question(technical[5]))
            elif len(technical) > 0:
                # fallback: usa a técnica mais pesada com bloom se não chegamos em 5
                questions.append(await self._generate_bloom_question(technical[0]))

            # --- Big Five: 4ª comportamental (fit cultural / situacional) ---
            bigfive_comp = behavioral[3] if len(behavioral) > 3 else (behavioral[-1] if behavioral else technical[0])
            questions.append(await self._generate_bigfive_question(bigfive_comp))

        target_count = 6 if mode == "compact" else 10

        if len(questions) < target_count:
            logger.warning(f"Generated only {len(questions)}/{target_count} questions due to limited competencies")

        return questions[:target_count]
    
    async def _generate_cbi_question(self, competency: Competency) -> WSIQuestion:
        """Gera pergunta CBI (contextual) para competência."""
        
        prompt = f"""Gere UMA pergunta CBI (Competency-Based Interviewing) para avaliar: **{competency.name}**

Nível da vaga: {competency.seniority_level}
Tipo: {competency.type}

Princípio CBI: "Comportamentos passados são os melhores preditores de performance futura."

Estrutura: "Conte sobre uma situação em que [contexto específico]. O que você fez e qual foi o resultado?"

Exemplos de referência do RAG:
{self.question_templates[:2000]}

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
            response = await self.llm.claude.ainvoke(prompt)
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
            scoring_criteria=data.get("scoring_criteria", {})
        )
    
    async def _generate_dreyfus_question(self, competency: Competency) -> WSIQuestion:
        """Gera pergunta Dreyfus (autodeclaração) para competência."""
        
        prompt = f"""Gere UMA pergunta Dreyfus (autodeclaração) para avaliar: **{competency.name}**

Estrutura: "De 1 a 5, quanto você domina [tecnologia]? Pode citar um projeto recente onde aplicou?"

Combina:
- Autodeclaração (score 1-5)
- Validação contextual (projeto real)

Responda APENAS em JSON com mesma estrutura anterior."""

        try:
            response = await self.llm.claude.ainvoke(prompt)
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
    
    async def _generate_bloom_question(self, competency: Competency) -> WSIQuestion:
        """Gera microcase Bloom para competência."""
        
        seniority_level_map = {
            "junior": 3,
            "pleno": 4,
            "senior": 4,
            "lead": 5,
            "executive": 5
        }
        bloom_level = seniority_level_map.get(competency.seniority_level, 3)
        
        prompt = f"""Gere UMA pergunta tipo microcase (Bloom Level {bloom_level}) para: **{competency.name}**

Nível cognitivo esperado: {"APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"}

Exemplos:
- Level 3 (Aplicar): "Como você implementaria [solução]?"
- Level 4 (Analisar): "Como diagnosticaria [problema]?"
- Level 5 (Criar): "Projete [arquitetura/solução]"

Responda APENAS em JSON."""

        cognitive_level = "APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"
        
        try:
            response = await self.llm.claude.ainvoke(prompt)
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
    
    async def _generate_bigfive_question(self, competency: Competency) -> WSIQuestion:
        """Gera pergunta Big Five (situacional) para competência."""
        
        prompt = f"""Gere UMA pergunta Big Five (situacional) para avaliar: **{competency.name}**

Tipo: Comportamental/Cultural

Estrutura: "Como você reage quando...", "Descreva uma situação em que..."

Foco em traços OCEAN:
- Openness: Inovação, aprendizado
- Conscientiousness: Organização, entrega
- Extraversion: Comunicação, liderança
- Agreeableness: Colaboração
- Emotional Stability: Pressão

Responda APENAS em JSON."""

        try:
            response = await self.llm.claude.ainvoke(prompt)
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
        
        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="BigFive",
            question_type="situational",
            question_text=data["question_text"],
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Situação", "Comportamento", "Resultado"]),
            scoring_criteria=data.get("scoring_criteria", {})
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

CRITÉRIOS OBJETIVOS PARA DECISÃO (OBRIGATÓRIO seguir):
- WSI Geral >= 4.0 → decisao = "APROVADO"
- WSI Geral >= 3.0 e < 4.0 → decisao = "AGUARDANDO" (requer avaliação adicional)
- WSI Geral < 3.0 → decisao = "NÃO APROVADO"
- EXCEÇÃO: Se WSI Geral >= 3.5 E todos os scores técnicos >= 3.0 → pode ser "APROVADO"
- EXCEÇÃO: Se WSI Geral >= 4.0 MAS há red_flags graves → rebaixa para "AGUARDANDO"

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
