"""
Market Benchmark Service - Fetches public salary data via web search.

Uses web search to query salary data from public sources when internal data is insufficient.
Parses results using LLM to extract salary ranges and includes source attribution.
"""
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)

SERP_API_KEY = os.getenv("SERP_API_KEY", "")
SERP_API_URL = "https://serpapi.com/search"


@dataclass
class CacheEntry:
    data: dict[str, Any]
    created_at: datetime
    ttl_seconds: int = 86400
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


class TTLCache:
    def __init__(self, default_ttl: int = 86400):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._cache[key]
            return None
        return entry.data
    
    def set(self, key: str, data: dict[str, Any], ttl: int | None = None) -> None:
        self._cache[key] = CacheEntry(
            data=data,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl or self.default_ttl
        )
    
    def clear(self) -> None:
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


class MarketBenchmarkService:
    """
    Service for fetching salary benchmarks and market trends from public sources.
    
    Uses web search APIs to query salary data from sites like Glassdoor, LinkedIn,
    and other job market sources. Results are parsed using LLM to extract
    structured salary information.
    
    Features:
    - In-memory caching with TTL to avoid repeated searches
    - LLM-based parsing of search results
    - Support for Portuguese and English results
    - Graceful fallback when search fails
    - Source attribution for transparency
    """
    
    DISCLAIMER = "Estimativa baseada em dados públicos. Valores podem variar."
    CACHE_TTL_HOURS = 24
    
    SALARY_SOURCES = [
        "glassdoor.com.br",
        "linkedin.com",
        "indeed.com.br",
        "catho.com.br",
        "vagas.com.br",
        "salario.com.br",
        "lovemondays.com.br",
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = TTLCache(default_ttl=self.CACHE_TTL_HOURS * 3600)
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._serp_api_key = SERP_API_KEY
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{str(v).lower()}")
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _do_web_search(self, query: str) -> dict[str, Any]:
        """
        Execute web search using available search API.
        
        Supports SerpAPI for production use. Falls back to LLM estimation
        when no API key is configured.
        """
        if self._serp_api_key:
            return await self._search_with_serp_api(query)
        
        self.logger.info("No search API configured, using LLM estimation")
        return await self._estimate_with_llm(query)
    
    async def _search_with_serp_api(self, query: str) -> dict[str, Any]:
        """Execute search using SerpAPI."""
        try:
            params = {
                "q": query,
                "api_key": self._serp_api_key,
                "hl": "pt-br",
                "gl": "br",
                "num": 10,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(SERP_API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                organic_results = data.get("organic_results", [])
                for result in organic_results:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "link": result.get("link", ""),
                        "source": self._extract_source_domain(result.get("link", ""))
                    })
                
                return {
                    "success": True,
                    "results": results,
                    "query": query
                }
                
        except httpx.HTTPStatusError as e:
            self.logger.error(f"SerpAPI HTTP error: {e}")
            return {"success": False, "error": str(e), "results": []}
        except Exception as e:
            self.logger.error(f"SerpAPI error: {e}")
            return {"success": False, "error": str(e), "results": []}
    
    async def _estimate_with_llm(self, query: str) -> dict[str, Any]:
        """
        Use LLM to estimate salary data when no search API is available.
        This is a fallback that uses the LLM's knowledge.
        """
        return {
            "success": True,
            "results": [],
            "query": query,
            "llm_fallback": True
        }
    
    def _extract_source_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    async def _parse_salary_from_results(
        self,
        search_results: dict[str, Any],
        role: str,
        seniority: str | None = None,
        location: str | None = None
    ) -> dict[str, Any]:
        """
        Use LLM to parse search results and extract salary information.
        """
        search_results.get("query", "")
        results = search_results.get("results", [])
        is_llm_fallback = search_results.get("llm_fallback", False)
        
        context_parts = []
        if results:
            for r in results[:5]:
                context_parts.append(f"- {r.get('title', '')}: {r.get('snippet', '')}")
            context = "\n".join(context_parts)
        else:
            context = "Nenhum resultado de busca disponível."
        
        seniority_text = f" nível {seniority}" if seniority else ""
        location_text = f" em {location}" if location else " no Brasil"
        
        prompt = f"""Analise os seguintes dados e extraia informações de salário para o cargo de {role}{seniority_text}{location_text}.

Contexto da busca:
{context}

Baseado nos dados disponíveis e seu conhecimento sobre o mercado brasileiro, forneça uma estimativa salarial.

Responda APENAS com um JSON válido no seguinte formato (sem markdown, sem explicações):
{{
    "min": 8000,
    "max": 15000,
    "median": 11500,
    "sources_found": ["glassdoor.com.br", "linkedin.com"],
    "confidence": "medium",
    "trend": "estável",
    "notes": "Breve nota sobre a estimativa"
}}

Regras:
- min, max, median devem ser números inteiros em BRL (salário mensal)
- confidence: "high" (dados concretos), "medium" (estimativa razoável), "low" (pouca informação)
- trend: "alta demanda", "estável", "em declínio"
- Se não houver dados suficientes, faça uma estimativa razoável baseada no mercado brasileiro
- Considere o custo de vida da região se location foi especificado"""

        try:
            response = await llm_service.generate(prompt, provider="gemini")
            
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "success": True,
                    "data": parsed,
                    "llm_fallback": is_llm_fallback
                }
            
            self.logger.warning(f"Could not parse LLM response: {response[:200]}")
            return self._get_default_salary_estimate(role, seniority)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {e}")
            return self._get_default_salary_estimate(role, seniority)
        except Exception as e:
            self.logger.error(f"LLM parsing error: {e}")
            return self._get_default_salary_estimate(role, seniority)
    
    def _get_default_salary_estimate(
        self,
        role: str,
        seniority: str | None = None
    ) -> dict[str, Any]:
        """Return default salary estimate when parsing fails."""
        # Audit 2026-06-03 (P0): faixa default por senioridade com matching por
        # alias (PT/EN/acentos). Antes, "Diretoria" nao casava com a chave
        # "diretor" e caia no fallback de analista (6000, 12000) -- R$6-12k para
        # uma Diretoria. Agora alias resolve diretoria/c-level/etc; senioridade
        # desconhecida vira confidence="none" (consumidor pede input, nao ancora).
        base_salaries = {
            "junior": (4000, 7000),
            "pleno": (7000, 12000),
            "senior": (12000, 20000),
            "staff": (18000, 30000),
            "principal": (20000, 35000),
            "coordinator": (10000, 18000),
            "manager": (15000, 30000),
            "director": (25000, 50000),
            "c-level": (35000, 80000),
        }
        # Ordem: do mais senior pro mais junior, para "diretoria" casar com
        # director antes de um match parcial mais fraco.
        seniority_aliases = {
            "c-level": ["c-level", "clevel", "cto", "ceo", "cfo", "coo", "cmo",
                        "vp", "vice-presid", "presidente", "chief"],
            "director": ["diretor", "diretoria", "director", "head"],
            "manager": ["gerente", "manager", "gestor"],
            "coordinator": ["coorden", "coordinator"],
            "principal": ["principal", "especialista", "specialist"],
            "staff": ["staff"],
            "senior": ["senior", "sênior", "sr."],
            "pleno": ["pleno", "mid-level", "mid level"],
            "junior": ["junior", "júnior", "jr", "trainee", "estagi"],
        }
        raw_seniority = (seniority or "").lower()
        matched_key = None
        for canonical_key, aliases in seniority_aliases.items():
            if any(alias in raw_seniority for alias in aliases):
                matched_key = canonical_key
                break

        if matched_key:
            min_sal, max_sal = base_salaries[matched_key]
            default_confidence = "low"
        else:
            # Senioridade desconhecida: NAO ancora faixa de analista como fato.
            min_sal, max_sal = base_salaries["pleno"]
            default_confidence = "none"
        
        tech_keywords = ["desenvolvedor", "developer", "engenheiro", "engineer", 
                        "data", "machine learning", "devops", "cloud", "arquiteto"]
        if any(kw in role.lower() for kw in tech_keywords):
            min_sal = int(min_sal * 1.2)
            max_sal = int(max_sal * 1.3)
        
        return {
            "success": True,
            "data": {
                "min": min_sal,
                "max": max_sal,
                "median": (min_sal + max_sal) // 2,
                "sources_found": [],
                "confidence": default_confidence,
                "trend": "estável",
                "notes": "Estimativa padrão baseada em médias do mercado"
            },
            "llm_fallback": True
        }
    
    async def search_salary_benchmark(
        self,
        role: str,
        seniority: str | None = None,
        location: str | None = None
    ) -> dict[str, Any]:
        """
        Search for salary benchmark data from public sources.
        
        Args:
            role: Job role/title (e.g., "Desenvolvedor Python", "Product Manager")
            seniority: Seniority level (e.g., "Júnior", "Pleno", "Sênior")
            location: Location for regional adjustment (e.g., "São Paulo", "Remote")
        
        Returns:
            Dictionary with salary range, sources, and metadata:
            {
                "min": 12000,
                "max": 20000,
                "median": 16000,
                "sources": ["glassdoor.com.br", "linkedin.com"],
                "search_date": "2026-01-21",
                "disclaimer": "Estimativa baseada em dados públicos. Valores podem variar.",
                "confidence": "medium",
                "trend": "alta demanda"
            }
        """
        cache_key = self._generate_cache_key(
            "salary_benchmark",
            role=role,
            seniority=seniority,
            location=location
        )
        
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Cache hit for salary benchmark: {role}")
            return cached
        
        try:
            seniority_text = f" {seniority}" if seniority else ""
            location_text = f" {location}" if location else " Brasil"
            
            query = f"salário {role}{seniority_text}{location_text} 2025 2026"
            
            self.logger.info(f"Searching salary benchmark for: {query}")
            
            search_results = await self._do_web_search(query)
            
            parsed = await self._parse_salary_from_results(
                search_results,
                role=role,
                seniority=seniority,
                location=location
            )
            
            if not parsed.get("success"):
                return self._create_error_response(role, seniority, location)
            
            data = parsed.get("data", {})
            
            # Audit 2026-06-03 (P0): proveniencia honesta, fail-loud. Sem busca
            # web real (is_estimate=True ou zero resultados), o numero veio do
            # conhecimento parametrico do LLM -- NUNCA atribuir a Glassdoor/
            # LinkedIn/etc. A LIA deve declarar "estimativa nao-verificada".
            is_estimate = bool(parsed.get("llm_fallback", False))
            real_results = search_results.get("results") or []
            if is_estimate or not real_results:
                sources = ["estimativa_llm_sem_busca"]
                confidence = "low"
                is_estimate = True
            else:
                sources = data.get("sources_found", []) or list(set(
                    r.get("source") for r in real_results[:3] if r.get("source")
                ))
                sources = sources or ["estimativa_llm_sem_busca"]
                confidence = data.get("confidence", "low")

            result = {
                "min": data.get("min"),
                "max": data.get("max"),
                "median": data.get("median"),
                "sources": sources,
                "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "disclaimer": self.DISCLAIMER,
                "confidence": confidence,
                "trend": data.get("trend", "estável"),
                "currency": "BRL",
                "notes": data.get("notes"),
                "is_estimate": is_estimate,
                "unverified": is_estimate,
            }
            
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching salary benchmark: {e}")
            return self._create_error_response(role, seniority, location, error=str(e))
    
    def _create_error_response(
        self,
        role: str,
        seniority: str | None = None,
        location: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Create error response with graceful fallback."""
        default = self._get_default_salary_estimate(role, seniority)
        data = default.get("data", {})
        
        return {
            "min": data.get("min"),
            "max": data.get("max"),
            "median": data.get("median"),
            "sources": ["estimativa padrão"],
            "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "disclaimer": self.DISCLAIMER,
            "confidence": "low",
            "trend": "estável",
            "currency": "BRL",
            "is_estimate": True,
            "error": error
        }
    
    async def search_market_trends(
        self,
        role: str,
        industry: str | None = None
    ) -> dict[str, Any]:
        """
        Search for market trends and demand for a role.
        
        Args:
            role: Job role/title
            industry: Industry sector (e.g., "Tecnologia", "Financeiro")
        
        Returns:
            Dictionary with market trends:
            {
                "demand": "alta",
                "trend": "crescente",
                "skills_in_demand": ["Python", "AWS", "Docker"],
                "salary_trend": "increasing",
                "market_outlook": "positivo",
                "sources": ["linkedin.com", "glassdoor.com.br"],
                "search_date": "2026-01-21",
                "disclaimer": "..."
            }
        """
        cache_key = self._generate_cache_key(
            "market_trends",
            role=role,
            industry=industry
        )
        
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Cache hit for market trends: {role}")
            return cached
        
        try:
            industry_text = f" setor {industry}" if industry else ""
            query = f"tendências mercado trabalho {role}{industry_text} Brasil 2025 2026"
            
            self.logger.info(f"Searching market trends for: {query}")
            
            search_results = await self._do_web_search(query)
            
            parsed = await self._parse_trends_from_results(
                search_results,
                role=role,
                industry=industry
            )
            
            sources = []
            if search_results.get("results"):
                sources = list(set(
                    r.get("source")
                    for r in search_results.get("results", [])[:3]
                    if r.get("source")
                ))
            
            result = {
                "demand": parsed.get("demand", "média"),
                "trend": parsed.get("trend", "estável"),
                "skills_in_demand": parsed.get("skills_in_demand", []),
                "salary_trend": parsed.get("salary_trend", "stable"),
                "market_outlook": parsed.get("market_outlook", "neutro"),
                "hiring_volume": parsed.get("hiring_volume", "moderado"),
                "competition": parsed.get("competition", "média"),
                "sources": sources or ["estimativa interna"],
                "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "disclaimer": self.DISCLAIMER,
                "confidence": parsed.get("confidence", "medium"),
                "is_estimate": search_results.get("llm_fallback", False)
            }
            
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching market trends: {e}")
            return self._create_default_trends_response(role, industry, error=str(e))
    
    async def _parse_trends_from_results(
        self,
        search_results: dict[str, Any],
        role: str,
        industry: str | None = None
    ) -> dict[str, Any]:
        """Use LLM to parse market trends from search results."""
        results = search_results.get("results", [])
        
        context_parts = []
        if results:
            for r in results[:5]:
                context_parts.append(f"- {r.get('title', '')}: {r.get('snippet', '')}")
            context = "\n".join(context_parts)
        else:
            context = "Nenhum resultado de busca disponível."
        
        industry_text = f" no setor de {industry}" if industry else ""
        
        prompt = f"""Analise os seguintes dados e extraia tendências de mercado para o cargo de {role}{industry_text} no Brasil.

Contexto da busca:
{context}

Baseado nos dados disponíveis e seu conhecimento sobre o mercado brasileiro, forneça uma análise de tendências.

Responda APENAS com um JSON válido no seguinte formato (sem markdown, sem explicações):
{{
    "demand": "alta",
    "trend": "crescente",
    "skills_in_demand": ["Python", "AWS", "Docker"],
    "salary_trend": "increasing",
    "market_outlook": "positivo",
    "hiring_volume": "alto",
    "competition": "alta",
    "confidence": "medium"
}}

Regras:
- demand: "alta", "média", "baixa"
- trend: "crescente", "estável", "em declínio"
- salary_trend: "increasing", "stable", "decreasing"
- market_outlook: "positivo", "neutro", "negativo"
- hiring_volume: "alto", "moderado", "baixo"
- competition: "alta", "média", "baixa"
- confidence: "high", "medium", "low"
- skills_in_demand: lista de 3-5 habilidades mais procuradas"""

        try:
            response = await llm_service.generate(prompt, provider="gemini")
            
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            
            self.logger.warning(f"Could not parse trends response: {response[:200]}")
            return self._get_default_trends(role)
            
        except Exception as e:
            self.logger.error(f"LLM trends parsing error: {e}")
            return self._get_default_trends(role)
    
    def _get_default_trends(self, role: str) -> dict[str, Any]:
        """Return default trends when parsing fails."""
        tech_roles = ["desenvolvedor", "developer", "engenheiro", "engineer",
                     "data", "devops", "cloud", "arquiteto", "product"]
        
        is_tech = any(kw in role.lower() for kw in tech_roles)
        
        return {
            "demand": "alta" if is_tech else "média",
            "trend": "crescente" if is_tech else "estável",
            "skills_in_demand": [],
            "salary_trend": "increasing" if is_tech else "stable",
            "market_outlook": "positivo" if is_tech else "neutro",
            "hiring_volume": "alto" if is_tech else "moderado",
            "competition": "alta" if is_tech else "média",
            "confidence": "low"
        }
    
    def _create_default_trends_response(
        self,
        role: str,
        industry: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Create default trends response."""
        defaults = self._get_default_trends(role)
        
        return {
            **defaults,
            "sources": ["estimativa padrão"],
            "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "disclaimer": self.DISCLAIMER,
            "is_estimate": True,
            "error": error
        }
    
    def combine_with_internal(
        self,
        internal_data: dict[str, Any] | None,
        market_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Combine internal salary data with market data.
        
        Gives preference to internal data when available, but supplements
        with market data for confidence and trend information.
        
        Args:
            internal_data: Internal salary benchmark (from JobInsightsService)
            market_data: Market salary benchmark (from this service)
        
        Returns:
            Combined salary data with both sources
        """
        if not internal_data or internal_data.get("sample_size", 0) == 0:
            return {
                **market_data,
                "data_source": "market",
                "combined": False
            }
        
        if not market_data or market_data.get("confidence") == "none":
            return {
                **internal_data,
                "disclaimer": self.DISCLAIMER,
                "data_source": "internal",
                "combined": False
            }
        
        internal_confidence = internal_data.get("confidence", "none")
        market_confidence = market_data.get("confidence", "none")
        
        confidence_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
        
        internal_weight = 0.7 if confidence_order.get(internal_confidence, 0) >= 2 else 0.5
        market_weight = 1 - internal_weight
        
        internal_min = internal_data.get("min") or 0
        internal_max = internal_data.get("max") or 0
        internal_median = internal_data.get("median") or 0
        
        market_min = market_data.get("min") or 0
        market_max = market_data.get("max") or 0
        market_median = market_data.get("median") or 0
        
        combined_min = int(internal_min * internal_weight + market_min * market_weight) if internal_min and market_min else internal_min or market_min
        combined_max = int(internal_max * internal_weight + market_max * market_weight) if internal_max and market_max else internal_max or market_max
        combined_median = int(internal_median * internal_weight + market_median * market_weight) if internal_median and market_median else internal_median or market_median
        
        internal_sources = []
        if internal_data.get("based_on"):
            internal_sources = [f"interno: {internal_data.get('based_on')}"]
        
        market_sources = market_data.get("sources", [])
        
        combined_confidence = "high" if internal_confidence == "high" or market_confidence == "high" else "medium"
        
        return {
            "min": combined_min,
            "max": combined_max,
            "median": combined_median,
            "sources": internal_sources + market_sources,
            "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "disclaimer": self.DISCLAIMER,
            "confidence": combined_confidence,
            "trend": market_data.get("trend", internal_data.get("trend", "estável")),
            "currency": "BRL",
            "data_source": "combined",
            "combined": True,
            "internal_data": {
                "min": internal_min,
                "max": internal_max,
                "median": internal_median,
                "sample_size": internal_data.get("sample_size", 0),
                "confidence": internal_confidence
            },
            "market_data": {
                "min": market_min,
                "max": market_max,
                "median": market_median,
                "confidence": market_confidence
            },
            "weights": {
                "internal": internal_weight,
                "market": market_weight
            }
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Market benchmark cache cleared")
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count of removed entries."""
        removed = self.cache.cleanup_expired()
        self.logger.info(f"Removed {removed} expired cache entries")
        return removed


market_benchmark_service = MarketBenchmarkService()


def get_market_benchmark_service() -> "MarketBenchmarkService":
    return market_benchmark_service
