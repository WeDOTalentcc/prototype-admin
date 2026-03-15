"""
Culture Analyzer Service.
Uses LLM to analyze company content and extract culture profile with Big Five mapping.
Enhanced with multi-source extraction (Website + LinkedIn).
"""
import json
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.llm import llm_service, LLMProvider

logger = logging.getLogger(__name__)

CULTURE_ANALYSIS_PROMPT_TEMPLATE = """<role>
Você é um Especialista Sênior em Estratégia de RH e Cultura Organizacional com mais de 20 anos de experiência em:
- Employer Branding e Employee Value Proposition (EVP)
- Análise e desenvolvimento de cultura organizacional
- Pesquisa e extração de dados de empresas
- Mapeamento de competências e perfis comportamentais (Big Five)
- Consultoria para empresas Fortune 500 e startups de alto crescimento
</role>

<task>
Analise cuidadosamente o conteúdo do website da empresa e os dados estruturados do LinkedIn (se disponíveis) para extrair um perfil cultural completo e estruturado. Sua análise deve ser precisa, baseada em evidências encontradas no conteúdo, e você deve inferir informações apenas quando houver indícios claros.
</task>

<thinking_instructions>
Antes de gerar o JSON final, raciocine internamente sobre:

1. **Setor e Indústria**: Qual é o setor principal? Há subsetores específicos?
2. **Tamanho e Maturidade**: É uma startup, PME ou enterprise? Qual o estágio de crescimento?
3. **Cultura Organizacional**: É mais tradicional ou inovadora? Hierárquica ou horizontal?
4. **EVP (Employee Value Proposition)**: O que a empresa oferece aos funcionários? Quais benefícios destacam?
5. **Modelo de Trabalho**: Há indicações de trabalho remoto, híbrido ou presencial?
6. **Valores e Competências**: Quais comportamentos e competências são valorizados?
7. **Responsabilidade Social**: Há iniciativas de DEI, sustentabilidade ou impacto social?
8. **Tech Stack** (se aplicável): Quais tecnologias são mencionadas?
9. **Big Five Organizacional**: Com base em todos os indícios, qual perfil comportamental da organização?

Não inclua a tag <thinking> na resposta final - apenas o JSON.
</thinking_instructions>

<examples>
<example_1>
INPUT (resumo): Site de startup de tecnologia com foco em IA, menciona trabalho remoto, cultura de experimentação, times pequenos, muita autonomia.
OUTPUT:
{{
  "mission": "Democratizar o acesso à inteligência artificial para pequenas empresas",
  "vision": "Ser a principal plataforma de IA para PMEs na América Latina",
  "values": ["Inovação", "Autonomia", "Transparência", "Foco no Cliente", "Experimentação"],
  "evp_bullets": ["Trabalho 100% remoto", "Equity para todos os funcionários", "Budget de aprendizado", "Férias ilimitadas"],
  "core_competencies": ["Pensamento analítico", "Adaptabilidade", "Autonomia", "Comunicação", "Resolução de problemas"],
  "culture_description": "Cultura de startup com alta autonomia, experimentação constante e foco em resultados. Ambiente informal com comunicação aberta e hierarquia horizontal.",
  "industry": "Tecnologia - Inteligência Artificial",
  "employee_count": 45,
  "company_size": "Startup",
  "headquarters": "São Paulo, SP",
  "locations": ["São Paulo", "Remoto Global"],
  "founded_year": 2021,
  "work_model": "Remoto",
  "growth_opportunities": "Plano de carreira estruturado com trilhas técnicas e de gestão. Promoções baseadas em impacto.",
  "team_dynamics": "Times pequenos e multidisciplinares com alta autonomia. Squads de 4-6 pessoas.",
  "leadership_style": "Liderança servidora com foco em capacitação e remoção de obstáculos.",
  "dei_initiatives": "Programa de diversidade com metas de contratação inclusiva",
  "sustainability": null,
  "social_impact": "Programa de mentoria para jovens de periferias",
  "tech_stack": ["Python", "React", "AWS", "PostgreSQL", "LangChain"],
  "engineering_culture": "Cultura de engenharia focada em qualidade, code review rigoroso e experimentação controlada.",
  "big_five": {{
    "openness": 85,
    "conscientiousness": 60,
    "extraversion": 70,
    "agreeableness": 75,
    "stability": 55
  }},
  "confidence": 0.85
}}
</example_1>

<example_2>
INPUT (resumo): Site de banco tradicional, ênfase em segurança e compliance, escritórios físicos, dress code formal, hierarquia clara.
OUTPUT:
{{
  "mission": "Oferecer soluções financeiras seguras e confiáveis para nossos clientes",
  "vision": "Ser o banco mais seguro e respeitado do Brasil",
  "values": ["Segurança", "Integridade", "Excelência", "Tradição", "Responsabilidade"],
  "evp_bullets": ["Estabilidade de carreira", "Plano de saúde completo", "Previdência privada", "PLR competitivo"],
  "core_competencies": ["Atenção a detalhes", "Ética", "Organização", "Trabalho em equipe", "Foco em qualidade"],
  "culture_description": "Cultura corporativa tradicional com foco em processos, compliance e segurança. Hierarquia definida com progressão de carreira estruturada.",
  "industry": "Serviços Financeiros - Banco",
  "employee_count": 12000,
  "company_size": "Enterprise",
  "headquarters": "São Paulo, SP",
  "locations": ["São Paulo", "Rio de Janeiro", "Brasília", "Belo Horizonte"],
  "founded_year": 1952,
  "work_model": "Presencial",
  "growth_opportunities": "Carreira estruturada com níveis claros. Programas de trainee e desenvolvimento de líderes.",
  "team_dynamics": "Áreas funcionais bem definidas com processos estruturados de colaboração.",
  "leadership_style": "Liderança diretiva com foco em resultados e compliance.",
  "dei_initiatives": "Comitê de diversidade com programas de inclusão e equidade salarial",
  "sustainability": "Compromisso com finanças sustentáveis e carbono neutro até 2030",
  "social_impact": "Fundação social com foco em educação financeira",
  "tech_stack": [],
  "engineering_culture": null,
  "big_five": {{
    "openness": 35,
    "conscientiousness": 90,
    "extraversion": 50,
    "agreeableness": 60,
    "stability": 85
  }},
  "confidence": 0.90
}}
</example_2>
</examples>

<data_sources>
<website_content>
{website_content}
</website_content>

<linkedin_data>
{linkedin_data}
</linkedin_data>
</data_sources>

<output_instructions>
IMPORTANTE: Retorne APENAS um JSON válido, sem texto adicional antes ou depois. Não inclua markdown, comentários ou explicações.

O JSON deve seguir EXATAMENTE este schema:
</output_instructions>

<output_schema>
{{
  "mission": "Missão da empresa em 1-2 frases. Null se não encontrado explicitamente.",
  "vision": "Visão da empresa em 1-2 frases. Null se não encontrado explicitamente.",
  "values": ["Lista de 3-7 valores da empresa. Array vazio se não encontrado."],
  "evp_bullets": ["3-5 pontos principais sobre benefícios/EVP de trabalhar na empresa"],
  "core_competencies": ["3-7 competências comportamentais valorizadas pela empresa"],
  "culture_description": "Descrição da cultura organizacional em 1 parágrafo (máximo 200 palavras). Baseie-se em evidências do conteúdo.",
  
  "industry": "Setor/indústria principal da empresa. Ex: Tecnologia - SaaS, Varejo, Serviços Financeiros",
  "employee_count": "Número estimado de funcionários (integer ou null)",
  "company_size": "Classificação: Startup (1-50), PME (51-500), Média-Grande (501-5000), Enterprise (5000+)",
  "headquarters": "Cidade/País da sede principal",
  "locations": ["Lista de cidades/escritórios"],
  "founded_year": "Ano de fundação (integer ou null)",
  
  "work_model": "Modelo de trabalho: Remoto, Híbrido, Presencial, ou Flexível",
  "growth_opportunities": "Descrição de oportunidades de carreira e crescimento",
  "team_dynamics": "Descrição da dinâmica de equipes e colaboração",
  "leadership_style": "Estilo de liderança predominante na organização",
  
  "dei_initiatives": "Iniciativas de Diversidade, Equidade e Inclusão. Null se não mencionado.",
  "sustainability": "Iniciativas de sustentabilidade ambiental. Null se não mencionado.",
  "social_impact": "Programas de impacto social. Null se não mencionado.",
  
  "tech_stack": ["Tecnologias mencionadas, principalmente para empresas de tech"],
  "engineering_culture": "Descrição da cultura de engenharia/desenvolvimento. Null se não aplicável.",
  
  "big_five": {{
    "openness": "0-100 (Inovação, criatividade, abertura a mudanças)",
    "conscientiousness": "0-100 (Processos, organização, qualidade, compliance)",
    "extraversion": "0-100 (Colaboração, comunicação, trabalho em equipe)",
    "agreeableness": "0-100 (Foco em pessoas, empatia, bem-estar)",
    "stability": "0-100 (Ambiente calmo, previsibilidade, baixo estresse)"
  }},
  "confidence": "0.0-1.0 (Confiança na análise baseada na qualidade/quantidade de dados)"
}}
</output_schema>

<scoring_guide>
GUIA PARA SCORES BIG FIVE ORGANIZACIONAL (0-100):

1. OPENNESS (Abertura a Experiências):
   - Alto (70-100): Startups, inovação constante, experimentação, criatividade valorizada
   - Médio (40-70): Equilíbrio entre inovação e estabilidade
   - Baixo (0-40): Empresas tradicionais, processos estabelecidos, aversão a riscos

2. CONSCIENTIOUSNESS (Conscienciosidade):
   - Alto (70-100): Foco em processos, qualidade, compliance, organização rigorosa, regulamentado
   - Médio (40-70): Processos estruturados com flexibilidade
   - Baixo (0-40): Ambiente informal, menos processos formais, agilidade sobre processos

3. EXTRAVERSION (Extroversão):
   - Alto (70-100): Cultura colaborativa intensa, muita comunicação, eventos, trabalho em equipe
   - Médio (40-70): Equilíbrio entre colaboração e trabalho individual
   - Baixo (0-40): Foco em trabalho individual, introspecção, deep work

4. AGREEABLENESS (Amabilidade):
   - Alto (70-100): Foco em pessoas, empatia, DEI forte, bem-estar, cultura de cuidado
   - Médio (40-70): Equilíbrio entre resultados e cuidado com pessoas
   - Baixo (0-40): Cultura competitiva, foco em resultados, meritocracia agressiva

5. STABILITY (Estabilidade - inverso de Neuroticism):
   - Alto (70-100): Ambiente calmo, estável, previsível, baixo estresse, work-life balance
   - Médio (40-70): Alguns desafios mas ambiente geralmente estável
   - Baixo (0-40): Ambiente dinâmico, alta pressão, startup chaos, mudanças frequentes
</scoring_guide>

Analise com cuidado os dados fornecidos e retorne APENAS o JSON válido."""


class CultureAnalyzerService:
    """
    Service for analyzing company culture using LLM.
    Enhanced with multi-source analysis (Website + LinkedIn).
    """
    
    def __init__(self):
        self.cache_duration = timedelta(days=30)
    
    async def analyze_culture(
        self, 
        content: str, 
        linkedin_data: Optional[Dict] = None,
        provider: LLMProvider = "claude"
    ) -> Dict[str, Any]:
        """
        Analyze company culture from scraped content and LinkedIn data.
        
        Args:
            content: Scraped website content
            linkedin_data: Optional structured data from LinkedIn
            provider: LLM provider to use (claude, openai, gemini)
            
        Returns:
            Dict with culture analysis results including new fields
        """
        logger.info(f"Analyzing culture content ({len(content)} chars) with {provider}")
        
        try:
            linkedin_str = "Dados do LinkedIn não disponíveis."
            if linkedin_data:
                linkedin_str = json.dumps(linkedin_data, ensure_ascii=False, indent=2)
            
            prompt = CULTURE_ANALYSIS_PROMPT_TEMPLATE.format(
                website_content=content[:40000],
                linkedin_data=linkedin_str[:5000]
            )
            
            logger.info(f"Calling LLM service with provider: {provider}")
            response = await llm_service.generate(prompt, provider=provider)
            logger.info(f"LLM response received, length: {len(response) if response else 0}")
            logger.debug(f"LLM response preview: {response[:500] if response else 'None'}")
            
            result = self._parse_llm_response(response)
            
            if linkedin_data and result.get("success"):
                result = self._merge_linkedin_data(result, linkedin_data)
            
            result["raw_response"] = response
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing culture: {type(e).__name__}: {e}")
            return self._get_default_result(str(e))
    
    def _merge_linkedin_data(self, analysis: Dict, linkedin_data: Dict) -> Dict:
        """
        Merge LinkedIn structured data with LLM analysis.
        LinkedIn data takes precedence for factual fields.
        """
        if linkedin_data.get("industry") and not analysis.get("industry"):
            analysis["industry"] = linkedin_data["industry"]
        
        if linkedin_data.get("employee_count"):
            analysis["employee_count"] = str(linkedin_data["employee_count"])
        
        if linkedin_data.get("company_size"):
            analysis["company_size"] = linkedin_data["company_size"]
        
        if linkedin_data.get("headquarters") and not analysis.get("headquarters"):
            analysis["headquarters"] = linkedin_data["headquarters"]
        
        if linkedin_data.get("locations"):
            existing = set(analysis.get("locations", []))
            for loc in linkedin_data["locations"]:
                existing.add(loc)
            analysis["locations"] = list(existing)
        
        if linkedin_data.get("founded_year"):
            analysis["founded_year"] = linkedin_data["founded_year"]
        
        return analysis
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON data."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                return self._validate_and_normalize(data)
            else:
                logger.error("No JSON found in LLM response")
                return self._get_default_result("No JSON found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._get_default_result(f"JSON parse error: {e}")
    
    def _validate_and_normalize(self, data: Dict) -> Dict[str, Any]:
        """Validate and normalize the parsed data including new fields."""
        result = {
            "success": True,
            "error": None,
            
            "mission": data.get("mission"),
            "vision": data.get("vision"),
            "values": data.get("values", []),
            "evp_bullets": data.get("evp_bullets", []),
            "core_competencies": data.get("core_competencies", []),
            "culture_description": data.get("culture_description"),
            
            "industry": data.get("industry"),
            "employee_count": None,
            "company_size": data.get("company_size"),
            "headquarters": data.get("headquarters"),
            "locations": data.get("locations", []),
            "founded_year": None,
            
            "work_model": data.get("work_model"),
            "growth_opportunities": data.get("growth_opportunities"),
            "team_dynamics": data.get("team_dynamics"),
            "leadership_style": data.get("leadership_style"),
            
            "dei_initiatives": data.get("dei_initiatives"),
            "sustainability": data.get("sustainability"),
            "social_impact": data.get("social_impact"),
            
            "tech_stack": data.get("tech_stack", []),
            "engineering_culture": data.get("engineering_culture"),
            
            "big_five": {},
            "confidence": float(data.get("confidence", 0.7)),
        }
        
        for field in ["values", "evp_bullets", "core_competencies", "locations", "tech_stack"]:
            if not isinstance(result[field], list):
                result[field] = []
        
        if data.get("employee_count"):
            try:
                result["employee_count"] = str(data["employee_count"])
            except (ValueError, TypeError):
                pass
        
        if data.get("founded_year"):
            try:
                result["founded_year"] = int(data["founded_year"])
            except (ValueError, TypeError):
                pass
        
        big_five = data.get("big_five", {})
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]:
            score = big_five.get(trait, 50)
            try:
                score = int(score)
                score = max(0, min(100, score))
            except (ValueError, TypeError):
                score = 50
            result["big_five"][trait] = score
        
        return result
    
    def _get_default_result(self, error: str) -> Dict[str, Any]:
        """Return default result structure on error."""
        return {
            "success": False,
            "error": error,
            
            "mission": None,
            "vision": None,
            "values": [],
            "evp_bullets": [],
            "core_competencies": [],
            "culture_description": None,
            
            "industry": None,
            "employee_count": None,
            "company_size": None,
            "headquarters": None,
            "locations": [],
            "founded_year": None,
            
            "work_model": None,
            "growth_opportunities": None,
            "team_dynamics": None,
            "leadership_style": None,
            
            "dei_initiatives": None,
            "sustainability": None,
            "social_impact": None,
            
            "tech_stack": [],
            "engineering_culture": None,
            
            "big_five": {
                "openness": 50,
                "conscientiousness": 50,
                "extraversion": 50,
                "agreeableness": 50,
                "stability": 50
            },
            "confidence": 0.0
        }
    
    def calculate_culture_match(
        self, 
        company_profile: Dict[str, int], 
        candidate_profile: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Calculate culture fit match between company and candidate Big Five profiles.
        
        Args:
            company_profile: Company's Big Five scores (0-100)
            candidate_profile: Candidate's Big Five scores (0-100)
            
        Returns:
            Dict with overall match score and per-trait analysis
        """
        traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]
        
        trait_weights = {
            "openness": 1.0,
            "conscientiousness": 1.2,
            "extraversion": 0.9,
            "agreeableness": 1.1,
            "stability": 1.0
        }
        
        trait_matches = {}
        weighted_sum = 0
        weight_total = 0
        
        for trait in traits:
            company_score = company_profile.get(trait, 50)
            candidate_score = candidate_profile.get(trait, 50)
            
            difference = abs(company_score - candidate_score)
            match_score = max(0, 100 - difference)
            
            trait_matches[trait] = {
                "company_score": company_score,
                "candidate_score": candidate_score,
                "difference": difference,
                "match_score": match_score
            }
            
            weight = trait_weights[trait]
            weighted_sum += match_score * weight
            weight_total += weight
        
        overall_match = weighted_sum / weight_total if weight_total > 0 else 0
        
        return {
            "overall_match": round(overall_match, 1),
            "trait_analysis": trait_matches,
            "recommendation": self._get_match_recommendation(overall_match)
        }
    
    def _get_match_recommendation(self, match_score: float) -> str:
        """Get recommendation text based on match score."""
        if match_score >= 85:
            return "Excelente fit cultural. Candidato altamente compatível com a cultura da empresa."
        elif match_score >= 70:
            return "Bom fit cultural. Candidato compatível com a maioria dos traços culturais."
        elif match_score >= 55:
            return "Fit cultural moderado. Algumas diferenças que podem requerer adaptação."
        else:
            return "Fit cultural baixo. Diferenças significativas nos perfis podem gerar desafios."


culture_analyzer_service = CultureAnalyzerService()
