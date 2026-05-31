"""
WSI Service - Main orchestrator combining all WSI components.
"""
import json
import logging
from typing import Any, Literal

from .models import (
    CandidateFeedback,
    Competency,
    CompetencySuggestion,
    ResponseAnalysis,
    StructuredReport,
    WSIQuestion,
    WSIResult,
    normalize_weights,
)
from .question_generator import WSIQuestionGenerator
from .response_analyzer import WSIResponseAnalyzer
from .score_calculator import WSIScoreCalculator
from .report_generator import WSIReportGenerator

from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)

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
        company_culture: dict | None = None,
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

        content_str = await self.llm.safe_invoke(prompt, provider="claude")
        # Robustez canonica (2026-05-31): o LLM pode devolver JSON cercado por
        # markdown; json.loads cru falha com "char 0". Strip defensivo beneficia
        # toda a plataforma (Settings + automacao + wizard conversacional).
        _cs = (content_str or "").strip()
        if _cs.startswith('```'):
            _parts = _cs.split('```')
            _cs = _parts[1] if len(_parts) > 1 else ""
            if _cs.lstrip().lower().startswith("json"):
                _cs = _cs.lstrip()[4:]
            _cs = _cs.strip()
        data = json.loads(_cs)
        
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
        competencies: list[Competency],
        mode: Literal["compact", "full"] = "compact",
        job_description: str | None = None,
        seniority: str | None = None,
        enriched_jd: dict | None = None,
    ) -> list[WSIQuestion]:
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
        skills: list[str],
        behavioral: list[str] | None = None,
        seniority: str = "pleno",
        job_description: str | None = None,
        mode: Literal["compact", "full"] = "compact",
        max_questions: int | None = None,
    ) -> list[WSIQuestion]:
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

        competencies: list[Competency] = []

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

        questions = await self.generate_screening_questions(
            competencies=competencies,
            mode=mode,
            job_description=job_description,
            seniority=_seniority_level if _seniority_level in ("junior", "pleno", "senior", "lead", "executive") else "pleno",
        )
        if max_questions is not None and len(questions) > max_questions:
            questions = questions[:max_questions]
        return questions

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
        original: list["Competency"],
        enriched: list["Competency"],
    ) -> list["Competency"]:
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
        responses: list[ResponseAnalysis],
        weights: dict[str, float]
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
        responses: list[ResponseAnalysis]
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
        responses: list[ResponseAnalysis],
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



wsi_service = WSIService()


async def generate_wsi_questions_tool(job_id: str, count: int = 5, **kwargs) -> list[dict[str, Any]]:
    result = await wsi_service.generate_from_simple_inputs(
        skills=kwargs.get("technical_skills", []),
        behavioral=kwargs.get("behavioral_competencies"),
        seniority=kwargs.get("seniority", "pleno"),
        job_description=kwargs.get("job_description"),
        max_questions=count,
    )
    return [q.dict() if hasattr(q, "dict") else q for q in result]


def get_wsi_service() -> "WSIService":
    """Return the module-level WSIService singleton. No db needed — pure LLM service."""
    return wsi_service

