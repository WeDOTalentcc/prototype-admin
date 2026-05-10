"""
Culture Analyzer Service.
Uses LLM to analyze company content and extract culture profile with Big Five mapping.
Enhanced with multi-source extraction (Website + LinkedIn).
"""
import json
import logging
import re
from datetime import timedelta
from typing import Any

from app.domains.ai.services.llm import LLMProvider, llm_service
from app.shared.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)

def _get_culture_prompt() -> str:
    """Lazy-load culture analysis prompt from YAML."""
    return PromptLoader.get_domain_prompt("culture_analysis")


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
        linkedin_data: dict | None = None,
        provider: LLMProvider = "claude"
    ) -> dict[str, Any]:
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
            
            prompt = _get_culture_prompt().format(
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Error analyzing culture: {type(e).__name__}: {e}")
            return self._get_default_result(str(e))
    
    def _merge_linkedin_data(self, analysis: dict, linkedin_data: dict) -> dict:
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
    
    def _parse_llm_response(self, response: str) -> dict[str, Any]:
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
    
    def _validate_and_normalize(self, data: dict) -> dict[str, Any]:
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
    
    def _get_default_result(self, error: str) -> dict[str, Any]:
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
        company_profile: dict[str, int], 
        candidate_profile: dict[str, int]
    ) -> dict[str, Any]:
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
