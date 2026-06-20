"""
Pearch AI integration service for candidate search (API v2).
Based on https://apidocs.pearch.ai/reference/post_v2-search
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.constants.industries import expand_industries_for_search
from lia_models.candidate import Candidate
from lia_models.pearch import (
    CandidateEducation,
    CandidateExperience,
    CandidateInsights,
    CandidateProfile,
    CompanyInfo,
    CompanyRole,
    CreditEstimate,
    HybridSearchRequest,
    HybridSearchResponse,
    Language,
    PearchSearchRequest,
    PearchSearchResponse,
    PearchSearchResult,
    QueryInsight,
    SearchConfirmation,
    SearchType,
)
from app.core.config import settings
from app.shared.resilience.circuit_breaker import circuit_breaker
from app.shared.resilience.cache_manager_service import RedisCache

logger = logging.getLogger(__name__)

# G-12: TTL do cache de busca Pearch (sem PII de contato). Default 15min.
SEARCH_CACHE_TTL = int(os.environ.get("PEARCH_SEARCH_CACHE_TTL", "900"))


# P1-11: deadline interno da chamada Pearch (caminho non-email). Menor que o
# deadline da rota (SEARCH_CANDIDATES_DEADLINE_SECONDS) para que um Pearch lento
# vire um TimeoutError CAPTURADO aqui (preservando os candidatos LOCAIS ja
# encontrados) em vez de estourar o deadline da rota e cancelar a coroutine
# inteira (que zerava ate os locais).
# BUG-PEARCH-TIMEOUT (2026-06-09): API Pearch v2 /v2/search leva ~26s em prod
# (retrieval 14s + scoring 5s + insights 4s). Deadline anterior (12s) cancelava
# TODAS as buscas globais silenciosamente. Elevado para 35s.
_PEARCH_CALL_DEADLINE_SECONDS = float(os.getenv("PEARCH_CALL_DEADLINE_SECONDS", "35.0"))


def _profile_has_email(profile: Any) -> bool:
    """Task #1219 — True se o perfil TEM email (modo require_emails).

    Cobre os dois modos do Pearch: com ``show_emails=False`` ele não retorna a
    string do email mas sinaliza ``has_emails=True``; com reveal ligado os
    campos ``emails``/``best_*_email`` vêm preenchidos. Candidatos locais setam
    ``has_emails`` a partir de ``Candidate.email is not None``. Usado como rede
    de segurança para garantir "só candidatos com email" no resultado final.
    """
    return bool(
        getattr(profile, "has_emails", None)
        or getattr(profile, "emails", None)
        or getattr(profile, "best_personal_email", None)
        or getattr(profile, "best_business_email", None)
    )


async def _pearch_search_fallback(self, request, timeout=None):
    """Fallback quando circuit breaker do Pearch está aberto.

    D10: Em vez de retornar vazio, tenta busca interna via RAG Híbrido
    (Sprint G6 — BM25 + pgvector). Loga [PEARCH-FALLBACK] com contagem de
    resultados internos. Fail-safe: se o RAG também falhar, retorna vazio.
    """
    query = request.query if request else ""
    company_id = getattr(request, "company_id", "") or ""

    logger.warning(
        "[PEARCH-FALLBACK] Circuit aberto — tentando busca interna RAG para query='%s' company_id='%s'",
        query, company_id,
    )

    if query and company_id:
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

            rag_svc = RAGPipelineService()
            async with AsyncSessionLocal() as db:
                rag_result = await rag_svc.search(
                    query=query,
                    company_id=company_id,
                    db=db,
                    limit=getattr(request, "limit", 20) or 20,
                    alpha=0.5,
                    job_title=getattr(request, "job_title", ""),
                    job_area=getattr(request, "job_area", ""),
                    job_requirements=getattr(request, "job_requirements", query),
                    sector=getattr(request, "sector", ""),
                )

            count = rag_result.total if rag_result else 0
            logger.info(
                "[PEARCH-FALLBACK] Busca interna retornou %d candidato(s) para query='%s'",
                count, query,
            )

            # Converter RAGSearchResult → PearchSearchResponse
            rag_search_results: list = []
            for item in (rag_result.results if rag_result else []):
                profile = CandidateProfile(
                    docid=str(item.get("id", "")),
                    name=item.get("name", ""),
                    current_title=item.get("current_role", ""),
                    location=item.get("location", ""),
                    summary=item.get("summary", ""),
                )
                rag_search_results.append(
                    PearchSearchResult(
                        docid=str(item.get("id", "")),
                        score=int(item.get("score", 0) * 100),
                        profile=profile,
                    )
                )

            return PearchSearchResponse(
                uuid="internal-fallback",
                thread_id="",
                query=query,
                status="internal_fallback",
                total_estimate=count,
                search_results=rag_search_results,
            )

        except Exception as _rag_exc:
            logger.warning(
                "[PEARCH-FALLBACK] Busca interna RAG também falhou: %s — retornando vazio", _rag_exc
            )

    return PearchSearchResponse(
        uuid="circuit-breaker-fallback",
        thread_id="",
        query=query,
        status="unavailable",
        total_estimate=0,
    )


class PearchService:
    """Service for interacting with Pearch AI API v2."""
    
    BASE_URL = "https://api.pearch.ai/v2"
    
    def __init__(self, timeout: float | None = None):
        """
        Args:
            timeout: HTTP timeout in seconds. Defaults to settings.HTTP_TIMEOUT_PEARCH_SECONDS.
        """
        self.api_key = os.getenv("PEARCH_API_KEY")
        # UC-P2-12 fix: resolve None to settings default + store as instance attr
        if timeout is None:
            from app.core.config import settings as _s
            timeout = _s.HTTP_TIMEOUT_PEARCH_SECONDS
        self.timeout = timeout
        self._search_cache = RedisCache()

        if not self.api_key:
            logger.warning("PEARCH_API_KEY not set - external candidate search will not work")

    @property
    def is_configured(self) -> bool:
        """Check if Pearch API key is configured."""
        return bool(self.api_key)

    async def health_check(self) -> dict[str, Any]:
        """
        Return structured health status for the Pearch integration.

        Returns:
            dict with status (connected | not_configured | error) and details.
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "PEARCH_API_KEY not set — external candidate search unavailable. "
                           "Fallback to local RAG search is active.",
                "configured": False,
            }
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_PEARCH_HEALTH_SECONDS) as client:  # UC-P2-12
                response = await client.get(
                    f"{self.BASE_URL}/health",
                    headers=self._get_headers(),
                )
                if response.status_code < 400:
                    return {"status": "connected", "configured": True, "http_status": response.status_code}
                return {
                    "status": "disconnected",
                    "configured": True,
                    "http_status": response.status_code,
                    "message": f"Pearch API returned HTTP {response.status_code}",
                }
        except Exception as exc:
            logger.warning("Pearch health check failed: %s", exc)
            return {"status": "disconnected", "configured": True, "message": str(exc)[:200]}

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def estimate_credits(self, request: PearchSearchRequest) -> CreditEstimate:
        """
        Estima o custo em créditos para uma busca (modo Fast apenas).
        
        Custos por candidato:
        - fast: 1 crédito base
        - insights: +1 crédito
        - profile_scoring: +1 crédito
        - high_freshness: +2 créditos
        
        Contatos são enriquecidos via Apify ($0.01/candidato), não via Pearch.
        """
        base = 1
        insights = 1 if request.insights else 0
        scoring = 1 if request.profile_scoring else 0
        freshness = 2 if request.high_freshness else 0
        
        per_candidate = base + insights + scoring + freshness
        
        return CreditEstimate(
            base_cost=base,
            insights_cost=insights + scoring,
            email_cost=0,
            phone_cost=0,
            freshness_cost=freshness,
            total_per_candidate=per_candidate,
            estimated_candidates=request.limit,
            total_estimated=per_candidate * request.limit
        )
    
    def create_confirmation_message(self, request: PearchSearchRequest) -> SearchConfirmation:
        """Cria mensagem de confirmação antes de executar busca."""
        estimate = self.estimate_credits(request)
        
        message_parts = [
            f"Busca: \"{request.query}\"",
            f"Tipo: {request.type.value.upper()} ({estimate.base_cost} créditos/candidato base)",
            f"Limite: até {request.limit} candidatos",
            "",
            "Custo estimado por candidato:"
        ]
        
        cost_details = [f"  - Base: {estimate.base_cost} créditos"]
        if estimate.insights_cost:
            cost_details.append(f"  - Insights/Scoring: +{estimate.insights_cost} créditos")
        if estimate.email_cost:
            cost_details.append(f"  - Emails: +{estimate.email_cost} créditos")
        if estimate.phone_cost:
            cost_details.append(f"  - Telefones: +{estimate.phone_cost} créditos")
        if estimate.freshness_cost:
            cost_details.append(f"  - Dados frescos: +{estimate.freshness_cost} créditos")
        
        message_parts.extend(cost_details)
        message_parts.append("")
        message_parts.append(f"TOTAL ESTIMADO: {estimate.total_estimated} créditos (máximo)")
        
        return SearchConfirmation(
            query=request.query,
            estimated_results=request.limit,
            credit_estimate=estimate,
            requires_confirmation=True,
            confirmation_message="\n".join(message_parts),
            search_request=request
        )
    
    def _search_cache_key(self, request, company_id) -> str:
        import hashlib
        import json as _json
        material = _json.dumps(
            {
                "c": str(company_id),
                "q": request.query,
                "t": request.type.value,
                "ins": request.insights,
                "fresh": request.high_freshness,
                "score": request.profile_scoring,
                "strict": request.strict_filters,
                "req_em": request.require_emails,
                "req_ph": request.require_phone_numbers,
                "req_eo": request.require_phones_or_emails,
                "filters": request.custom_filters or {},
                "limit": request.limit,
                "blacklist": sorted(request.docid_blacklist or []),
            },
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(material.encode()).hexdigest()[:32]
        return f"pearch_search:{company_id}:{digest}"

    def _strip_contact_pii(self, response):
        # Defesa em profundidade: zero email/telefone no cache, mesmo que o
        # Pearch retorne algum contato em modo sem-reveal.
        _CONTACT_FIELDS = (
            "email", "emails", "phone", "phones", "personal_emails",
            "business_emails", "phone_numbers", "mobile_phone", "secondary_email",
        )
        safe = response.model_copy(deep=True)
        _profiles = list(safe.candidates)
        _profiles.extend(r.profile for r in safe.search_results)
        for prof in _profiles:
            for f in _CONTACT_FIELDS:
                if hasattr(prof, f):
                    try:
                        setattr(prof, f, None)
                    except Exception:
                        pass
        return safe

    @circuit_breaker("pearch", failure_threshold=3, recovery_timeout=15.0, fallback=_pearch_search_fallback)
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
    async def search_candidates(
        self,
        request: PearchSearchRequest,
        timeout: float | None = None,  # UC-P2-12: defaults to HTTP_TIMEOUT_PEARCH_SECONDS
        company_id: str | None = None,
    ) -> PearchSearchResponse:
        """
        Busca candidatos usando a API v2 da Pearch.
        
        Args:
            request: Configurações da busca
            timeout: Timeout em segundos
        
        Returns:
            PearchSearchResponse com resultados
        """
        if not self.api_key:
            logger.warning(
                "[PearchService] PEARCH_API_KEY not set — routing to local RAG fallback for query='%s'",
                request.query if request else "",
            )
            return await _pearch_search_fallback(self, request, timeout)

        # FAR-2: FairnessGuard — bloquear queries discriminatórias antes de enviar ao Pearch
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(request.query)
            if _fg_result.is_blocked:
                logger.warning(
                    "[PearchService][FAR-2] FairnessGuard bloqueou query pearch: "
                    "category=%s terms=%s",
                    _fg_result.category, _fg_result.blocked_terms,
                )
                _blocked = PearchSearchResponse(
                    uuid="fairness-blocked",
                    thread_id="",
                    query=request.query,
                    status="fairness_blocked",
                    total_estimate=0,
                    search_results=[],
                )
                try:
                    await _fg.log_check(
                        result=_fg_result,
                        context="pearch_search",
                        company_id=getattr(request, "company_id", None),
                    )
                except Exception:
                    pass
                return _blocked
        except Exception as _fg_exc:
            logger.error(
                "[PearchService] FairnessGuard check FAILED (pearch query proceeding without fairness verification): %s",
                _fg_exc, exc_info=True,
            )

        company_id = company_id or getattr(request, "company_id", None)

        # G-12: cache de busca sem PII de contato. Ativo so em modo sem-reveal
        # (show_emails/show_phone_numbers=False) — nesse modo o Pearch nao
        # retorna emails/telefones. Hit = 0 creditos. Chave inclui company_id
        # (isolamento multi-tenant) + parametros que determinam o resultado.
        _cacheable = bool(company_id) and not request.show_emails and not request.show_phone_numbers
        _cache_key = self._search_cache_key(request, company_id) if _cacheable else None
        if _cache_key:
            try:
                _cached = await self._search_cache.get(_cache_key)
                if _cached.hit and _cached.value:
                    logger.info("[PearchService][cache] HIT — 0 creditos (key=...%s)", _cache_key[-12:])
                    return PearchSearchResponse.model_validate(_cached.value)
            except Exception as _ce:
                logger.debug("[PearchService][cache] get falhou: %s", _ce)

        logger.info(f"Searching Pearch AI v2: '{request.query}' (limit={request.limit}, type={request.type})")
        
        start_time = datetime.now()
        
        payload = {
            "query": request.query,
            "type": request.type.value,
            "insights": request.insights,
            "high_freshness": request.high_freshness,
            "profile_scoring": request.profile_scoring,
            "strict_filters": request.strict_filters,
            "require_emails": request.require_emails,
            "show_emails": request.show_emails,
            "require_phone_numbers": request.require_phone_numbers,
            "require_phones_or_emails": request.require_phones_or_emails,
            "show_phone_numbers": request.show_phone_numbers,
            "limit": request.limit
        }
        
        if request.thread_id:
            payload["thread_id"] = request.thread_id
        
        if request.custom_filters:
            payload["custom_filters"] = request.custom_filters
        
        if request.docid_blacklist:
            payload["docid_blacklist"] = request.docid_blacklist
        
        # UC-P2-12 fix: hybrid_search chama search_candidates SEM timeout (default None),
        # e None + 10 quebrava com TypeError -> RetryError -> busca global vazia.
        # Resolve None para o default ja calculado no __init__ (self.timeout).
        _timeout = timeout if timeout is not None else self.timeout
        try:
            async with httpx.AsyncClient(timeout=_timeout + 10) as client:
                response = await client.post(
                    f"{self.BASE_URL}/search",
                    json=payload,
                    headers=self._get_headers()
                )
                
                response.raise_for_status()
                data = response.json()
                
                search_time = (datetime.now() - start_time).total_seconds()
                
                parsed_response = self._parse_response(data, search_time)
                
                logger.info(
                    f"Found {len(parsed_response.search_results)} candidates in {search_time:.2f}s "
                    f"(credits remaining: {parsed_response.credits_remaining})"
                )
                
                credit_estimate = self.estimate_credits(request)
                estimated_credits = min(
                    credit_estimate.total_estimated,
                    credit_estimate.total_per_candidate * len(parsed_response.search_results),
                )

                await self._track_pearch_consumption(
                    company_id=company_id,
                    operation="search",
                    credits_consumed=estimated_credits,
                    success=True,
                    result_status="success",
                    response_time_ms=int(search_time * 1000),
                )

                if _cache_key:
                    try:
                        _safe = self._strip_contact_pii(parsed_response)
                        await self._search_cache.set(
                            _cache_key,
                            _safe.model_dump(mode="json"),
                            ttl_seconds=SEARCH_CACHE_TTL,
                            source="pearch_search",
                        )
                    except Exception as _ce:
                        logger.debug("[PearchService][cache] set falhou: %s", _ce)

                return parsed_response
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After", "unknown")
                logger.warning(
                    "[PearchService] Rate limited (429) — Retry-After: %s. "
                    "Routing to local RAG fallback for query='%s'.",
                    retry_after, request.query,
                )
                await self._track_pearch_consumption(
                    company_id=company_id,
                    operation="search",
                    credits_consumed=0,
                    success=False,
                    result_status="rate_limited",
                    error_message=f"HTTP 429 rate limited",
                )
                return await _pearch_search_fallback(self, request, timeout)
            logger.error(f"Pearch API error: {e.response.status_code} - {e.response.text}")
            await self._track_pearch_consumption(
                company_id=company_id,
                operation="search",
                credits_consumed=0,
                success=False,
                result_status="fail",
                error_message=f"HTTP {e.response.status_code}",
            )
            raise
        except httpx.TimeoutException:
            logger.error(f"Pearch API timeout after {timeout}s")
            await self._track_pearch_consumption(
                company_id=company_id,
                operation="search",
                credits_consumed=0,
                success=False,
                result_status="timeout",
                error_message=f"Timeout after {timeout}s",
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Pearch API: {e}")
            await self._track_pearch_consumption(
                company_id=company_id,
                operation="search",
                credits_consumed=0,
                success=False,
                result_status="fail",
                error_message=str(e)[:500],
            )
            raise

    async def search_by_job_description(
        self,
        job_description: str,
        location: str | None = None,
        limit: int = 20,
        company_id: str | None = None,
    ) -> "PearchSearchResponse":
        """F8.B1 fix (2026-05-20): wrapper canonical para busca por JD.

        Constrói PearchSearchRequest usando o JD como query natural-language e
        delega para ``search_candidates``. Permite que clientes (frontend, agentes)
        usem o JD completo como query sem precisar montar request manualmente.

        Args:
            job_description: Texto do JD (truncado em 2000 chars para evitar overflow).
            location: Localização para filtrar (e.g. "São Paulo").
            limit: Número máximo de resultados (default 20).
            company_id: Tenant context (auditoria + multi-tenancy).

        Returns:
            PearchSearchResponse com candidatos encontrados.
        """
        from lia_models.pearch import PearchSearchRequest, SearchType

        request = PearchSearchRequest(
            query=(job_description or "")[:2000],
            type=SearchType.FAST,
            insights=True,
            profile_scoring=True,
            custom_filters={"location": location} if location else None,
            limit=max(1, min(int(limit or 20), 100)),
        )
        # Pass explicit timeout — search_candidates does timeout+10 internally
        return await self.search_candidates(request, timeout=30.0, company_id=company_id)

    @staticmethod
    async def _track_pearch_consumption(
        company_id: str | None,
        operation: str,
        credits_consumed: int,
        success: bool,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
    ) -> None:
        resolved_company_id = company_id or "unattributed"
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
            async with AsyncSessionLocal() as db:
                await ConsumptionTrackingService.record_pearch_call(
                    db=db,
                    company_id=resolved_company_id,
                    user_id=None,
                    operation=operation,
                    credits_consumed=credits_consumed,
                    success=success,
                    result_status=result_status,
                    response_time_ms=response_time_ms,
                    error_message=error_message,
                )
                await db.commit()
        except Exception as e:
            logger.error("[PearchService] Failed to track consumption: %s", e)

    def _parse_response(self, data: dict[str, Any], search_time: float) -> PearchSearchResponse:
        """Parse raw API response into structured models."""
        search_results = []
        
        for raw_result in data.get("search_results", []):
            profile_data = raw_result.get("profile", {})
            insights_data = raw_result.get("insights")
            
            # Parse profile
            profile = self._parse_profile(profile_data)
            profile.score = raw_result.get("score")
            profile.outreach_message = raw_result.get("outreach_message")
            
            # Parse insights
            insights = None
            if insights_data:
                query_insights = []
                for qi in insights_data.get("query_insights", []):
                    query_insights.append(QueryInsight(
                        subquery=qi.get("subquery"),
                        match_level=qi.get("match_level"),
                        priority=qi.get("priority"),
                        short_rationale=qi.get("short_rationale"),
                        short_quotes=qi.get("short_quotes", [])
                    ))
                
                insights = CandidateInsights(
                    overall_summary=insights_data.get("overall_summary"),
                    query_insights=query_insights
                )
                profile.insights = insights
            
            search_results.append(PearchSearchResult(
                docid=raw_result.get("docid", profile_data.get("docid", "")),
                score=raw_result.get("score"),
                insights=insights,
                profile=profile,
                outreach_message=raw_result.get("outreach_message")
            ))
        
        return PearchSearchResponse(
            uuid=data.get("uuid", ""),
            thread_id=data.get("thread_id", ""),
            query=data.get("query", ""),
            user=None,  # F8.O2 LGPD: mascarado — não vaza email admin Pearch WeDOTalent pro cliente (audit 2026-05-20)
            created_at=data.get("created_at"),
            duration=data.get("duration"),
            status=data.get("status", "completed"),
            total_estimate=data.get("total_estimate", len(search_results)),
            total_estimate_is_lower_bound=data.get("total_estimate_is_lower_bound", False),
            credits_remaining=data.get("credits_remaining"),
            search_results=search_results,
            total_results=len(search_results),
            candidates=[r.profile for r in search_results],
            search_time_seconds=search_time
        )
    
    def _parse_company_location(self, company_info: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
        """
        Parse company HQ location from company_info.
        
        Returns:
            Tuple of (city, state, country)
        """
        city = company_info.get("hq_city")
        state = company_info.get("hq_state")
        country = company_info.get("hq_country")
        
        if not city and not state and not country:
            short_address = company_info.get("short_address", "")
            if short_address:
                parts = [p.strip() for p in short_address.split(",")]
                if len(parts) >= 3:
                    city = parts[0]
                    state = parts[1]
                    country = parts[-1]
                elif len(parts) == 2:
                    city = parts[0]
                    country = parts[-1]
                elif len(parts) == 1:
                    country = parts[0]
            
            if not country and company_info.get("locations"):
                first_loc = company_info["locations"][0] if company_info["locations"] else ""
                if first_loc:
                    loc_parts = [p.strip() for p in first_loc.split(",")]
                    if loc_parts:
                        country = loc_parts[-1]
                        if len(loc_parts) >= 2:
                            city = loc_parts[0]
        
        return city, state, country
    
    def _parse_institution_location(self, education_data: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
        """
        Parse institution location from education data.
        
        Returns:
            Tuple of (city, state, country)
        """
        city = education_data.get("institution_city") or education_data.get("city")
        state = education_data.get("institution_state") or education_data.get("state")
        country = education_data.get("institution_country") or education_data.get("country")
        
        if not city and not state and not country:
            location = education_data.get("location", "")
            if location:
                parts = [p.strip() for p in location.split(",")]
                if len(parts) >= 3:
                    city = parts[0]
                    state = parts[1]
                    country = parts[-1]
                elif len(parts) == 2:
                    city = parts[0]
                    country = parts[-1]
                elif len(parts) == 1:
                    country = parts[0]
        
        return city, state, country
    
    def _parse_profile(self, data: dict[str, Any]) -> CandidateProfile:
        """Parse profile data into CandidateProfile model."""
        # Parse languages
        languages = []
        for lang in data.get("languages", []):
            if isinstance(lang, dict):
                languages.append(Language(
                    language=lang.get("language"),
                    proficiency=lang.get("proficiency")
                ))
        
        inferred_languages = []
        for lang in data.get("inferred_languages", []):
            if isinstance(lang, dict):
                inferred_languages.append(Language(
                    language=lang.get("language"),
                    proficiency=lang.get("proficiency")
                ))
        
        # Parse experiences
        experiences = []
        for exp in data.get("experiences", []):
            company_info = None
            funding_stage = None
            company_tags = []
            company_hq_city = None
            company_hq_state = None
            company_hq_country = None
            company_size = None
            industries = []
            
            if "company_info" in exp and exp["company_info"]:
                ci = exp["company_info"]
                
                hq_city, hq_state, hq_country = self._parse_company_location(ci)
                
                company_info = CompanyInfo(
                    name=ci.get("name"),
                    domain=ci.get("domain"),
                    website=ci.get("website"),
                    linkedin_url=ci.get("linkedin_url"),
                    linkedin_slug=ci.get("linkedin_slug"),
                    short_address=ci.get("short_address"),
                    locations=ci.get("locations", []),
                    type=ci.get("type"),
                    description=ci.get("description"),
                    industries=ci.get("industries", []),
                    specialties=ci.get("specialties", []),
                    keywords=ci.get("keywords", []),
                    technologies=ci.get("technologies", []),
                    founded_in=ci.get("founded_in"),
                    num_employees=ci.get("num_employees"),
                    num_employees_range=ci.get("num_employees_range"),
                    annual_revenue=ci.get("annual_revenue"),
                    followers_count=ci.get("followers_count"),
                    is_startup=ci.get("is_startup"),
                    is_hiring=ci.get("is_hiring"),
                    icon=ci.get("icon"),
                    funding_stage=ci.get("funding_stage"),
                    hq_city=hq_city,
                    hq_state=hq_state,
                    hq_country=hq_country
                )
                
                funding_stage = ci.get("funding_stage")
                company_tags = ci.get("keywords", []) + ci.get("specialties", [])
                company_hq_city = hq_city
                company_hq_state = hq_state
                company_hq_country = hq_country
                company_size = ci.get("num_employees_range") or (str(ci.get("num_employees")) if ci.get("num_employees") else None)
                industries = ci.get("industries", [])
            
            company_roles = []
            for role in exp.get("company_roles", []):
                company_roles.append(CompanyRole(
                    sequenceNo=role.get("sequenceNo"),
                    company=role.get("company"),
                    company_domain=role.get("company_domain"),
                    title=role.get("title"),
                    start_date=role.get("start_date"),
                    end_date=role.get("end_date"),
                    duration_years=role.get("duration_years"),
                    age_years=role.get("age_years"),
                    description=role.get("description"),
                    location=role.get("location")
                ))
            
            experiences.append(CandidateExperience(
                company_info=company_info,
                company_roles=company_roles,
                company=exp.get("company") or (company_info.name if company_info else None),
                title=exp.get("title"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                duration=exp.get("duration"),
                duration_years=exp.get("duration_years"),
                description=exp.get("description"),
                location=exp.get("location"),
                funding_stage=funding_stage,
                company_tags=company_tags,
                company_hq_city=company_hq_city,
                company_hq_state=company_hq_state,
                company_hq_country=company_hq_country,
                company_size=company_size,
                industries=industries
            ))
        
        # Parse education
        education = []
        for edu in data.get("education", []):
            inst_city, inst_state, inst_country = self._parse_institution_location(edu)
            education.append(CandidateEducation(
                school=edu.get("school"),
                degree=edu.get("degree"),
                field_of_study=edu.get("field_of_study") or edu.get("field"),
                start_date=edu.get("start_date"),
                end_date=edu.get("end_date"),
                institution_city=inst_city,
                institution_state=inst_state,
                institution_country=inst_country,
                institution_ranking=edu.get("institution_ranking") or edu.get("ranking"),
                institution_tier=edu.get("institution_tier") or edu.get("tier")
            ))
        
        # Build full name
        first_name = data.get("first_name", "")
        middle_name = data.get("middle_name", "")
        last_name = data.get("last_name", "")
        full_name = " ".join(p for p in [first_name, middle_name, last_name] if p)
        
        return CandidateProfile(
            docid=data.get("docid"),
            linkedin_slug=data.get("linkedin_slug"),
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            name=full_name or data.get("name"),
            picture_url=data.get("picture_url"),
            title=data.get("title"),
            headline=data.get("headline") or data.get("title"),
            current_title=data.get("current_title") or data.get("title"),
            current_company=data.get("current_company"),
            summary=data.get("summary"),
            location=data.get("location"),
            gender=data.get("gender"),
            estimated_age=data.get("estimated_age"),
            is_decision_maker=data.get("is_decision_maker"),
            is_opentowork=data.get("is_opentowork"),
            is_hiring=data.get("is_hiring"),
            is_top_universities=data.get("is_top_universities"),
            total_experience_years=data.get("total_experience_years"),
            experiences=experiences,
            education=education,
            skills=data.get("skills", []),
            expertise=data.get("expertise", []),
            languages=languages,
            inferred_languages=inferred_languages,
            has_emails=data.get("has_emails"),
            emails=data.get("emails", []),
            best_personal_email=data.get("best_personal_email"),
            best_business_email=data.get("best_business_email"),
            personal_emails=data.get("personal_emails", []),
            business_emails=data.get("business_emails", []),
            has_phone_numbers=data.get("has_phone_numbers"),
            phone_numbers=data.get("phone_numbers", []),
            phone_types=data.get("phone_types", []),
            followers_count=data.get("followers_count"),
            connections_count=data.get("connections_count")
        )
    
    async def search_local_candidates(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20,
        exclude_ids: list[int] | None = None,
        industries: list[str] | None = None,
        require_email: bool = False,
        require_phone: bool = False,
        include_discovered: bool = True,
        funding_stages: list[str] | None = None,
        company_hq_countries: list[str] | None = None,
        company_tags: list[str] | None = None,
        institution_tiers: list[str] | None = None,
        institution_countries: list[str] | None = None,
        institution_ranking_max: int | None = None,
        timezones: list[str] | None = None,
        timezone_pattern: str | None = None
    ) -> tuple[list[CandidateProfile], int]:
        """
        Busca candidatos no banco de dados local e na tabela de staging (discovered).
        
        Args:
            db: Sessão do banco
            query: Query de busca
            limit: Limite de resultados
            exclude_ids: IDs a excluir
            industries: Filtrar por setores/indústrias das experiências
            require_email: Apenas candidatos com email
            require_phone: Apenas candidatos com telefone
            include_discovered: Incluir candidatos descobertos da tabela de staging
            funding_stages: Filter by funding stages (experience table)
            company_hq_countries: Filter by company HQ countries (experience table)
            company_tags: Filter by company tags/keywords (experience table)
            institution_tiers: Filter by institution tiers (education table)
            institution_countries: Filter by institution countries (education table)
            institution_ranking_max: Filter by max institution ranking (education table)
            timezones: Filter by exact timezone matches (candidates table)
            timezone_pattern: Filter by timezone pattern with ILIKE (candidates table)
        
        Returns:
            Tuple de (lista de perfis, total encontrado)
        """
        from lia_models.candidate import CandidateEducation as CandidateEducationDB
        from lia_models.candidate import CandidateExperience, ExternalCandidateProfile
        
        logger.info(f"Searching local database: '{query}' (limit={limit}, industries={industries}, include_discovered={include_discovered})")
        
        # Parse query para extrair termos de busca
        search_terms = query.lower().split()
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            term_pattern = f"%{term}%"
            conditions.append(
                or_(
                    func.lower(Candidate.name).ilike(term_pattern),
                    func.lower(Candidate.current_title).ilike(term_pattern),
                    func.lower(Candidate.current_company).ilike(term_pattern),
                    func.lower(Candidate.location_city).ilike(term_pattern),
                    func.lower(Candidate.location_state).ilike(term_pattern),
                )
            )
        
        # Query base
        # ADR-001-EXEMPT: dynamic query builder with 13 optional filter kwargs
        # (industries, funding_stages, company_hq_countries, company_tags,
        # institution_tiers, institution_countries, institution_ranking_max,
        # timezones, timezone_pattern, require_email, require_phone, exclude_ids,
        # search_terms) and 6 EXISTS subqueries on CandidateExperience/Education.
        # Encapsulating in a repo method would either require passing 13 kwargs
        # downstream or duplicating the builder skeleton — net loss of clarity.
        stmt = select(Candidate).where(
            Candidate.is_active
        )
        
        if conditions:
            stmt = stmt.where(or_(*conditions))
        
        if exclude_ids:
            stmt = stmt.where(~Candidate.id.in_(exclude_ids))
        
        # Filtro por email/telefone
        if require_email:
            stmt = stmt.where(Candidate.email.isnot(None))
        if require_phone:
            stmt = stmt.where(Candidate.phone.isnot(None))

        # P0-1: filtros estruturados derivados do LLM (industries, funding,
        # countries, tags, tiers, timezones) sao SOFT (drop-if-zero), NAO gate
        # eliminatorio. Coletados aqui e aplicados no bloco de execucao; se
        # zerarem o conjunto, sao descartados (degradacao graciosa).
        _structured_conditions = []
        
        # Filtro por industries (via experiências) - case-insensitive overlap with synonym expansion
        if industries and len(industries) > 0:
            # Expand industries to include all synonyms (PT/EN bidirectional)
            # e.g., "Banking" also matches "Banco Digital", "Banco", etc.
            expanded_industries = expand_industries_for_search(industries)
            
            # Subquery para encontrar candidate_ids com experiências em qualquer das industries
            # Usa overlap (&&) para verificar se há intersecção entre os arrays
            
            logger.debug(f"Industry filter: original={industries}, expanded={expanded_industries[:10]}...")
            
            industry_subq = (
                select(CandidateExperience.candidate_id)
                .where(
                    CandidateExperience.industries.overlap(expanded_industries)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(industry_subq))
        
        # Filter by funding stages (via experiences table)
        if funding_stages and len(funding_stages) > 0:
            funding_stages_lower = [fs.lower() for fs in funding_stages]
            funding_subq = (
                select(CandidateExperience.candidate_id)
                .where(
                    func.lower(CandidateExperience.funding_stage).in_(funding_stages_lower)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(funding_subq))
        
        # Filter by company HQ countries (via experiences table)
        if company_hq_countries and len(company_hq_countries) > 0:
            countries_lower = [c.lower() for c in company_hq_countries]
            hq_country_subq = (
                select(CandidateExperience.candidate_id)
                .where(
                    func.lower(CandidateExperience.company_hq_country).in_(countries_lower)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(hq_country_subq))
        
        # Filter by company tags (via experiences table) - overlap with array
        if company_tags and len(company_tags) > 0:
            tags_lower = [t.lower() for t in company_tags]
            tags_subq = (
                select(CandidateExperience.candidate_id)
                .where(
                    CandidateExperience.company_tags.overlap(tags_lower)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(tags_subq))
        
        # Filter by institution tiers (via education table)
        if institution_tiers and len(institution_tiers) > 0:
            tiers_lower = [t.lower() for t in institution_tiers]
            tier_subq = (
                select(CandidateEducationDB.candidate_id)
                .where(
                    func.lower(CandidateEducationDB.institution_tier).in_(tiers_lower)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(tier_subq))
        
        # Filter by institution countries (via education table)
        if institution_countries and len(institution_countries) > 0:
            inst_countries_lower = [c.lower() for c in institution_countries]
            inst_country_subq = (
                select(CandidateEducationDB.candidate_id)
                .where(
                    func.lower(CandidateEducationDB.institution_country).in_(inst_countries_lower)
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(inst_country_subq))
        
        # Filter by institution ranking (max threshold - lower is better)
        if institution_ranking_max is not None:
            ranking_subq = (
                select(CandidateEducationDB.candidate_id)
                .where(
                    CandidateEducationDB.institution_ranking.isnot(None),
                    CandidateEducationDB.institution_ranking <= institution_ranking_max
                )
                .distinct()
            )
            _structured_conditions.append(Candidate.id.in_(ranking_subq))
        
        # Filter by timezones (exact match or IN list on candidates table)
        if timezones and len(timezones) > 0:
            timezones_lower = [tz.lower() for tz in timezones]
            _structured_conditions.append(func.lower(Candidate.timezone).in_(timezones_lower))
        
        # Filter by timezone pattern (ILIKE match on candidates table)
        if timezone_pattern:
            _structured_conditions.append(Candidate.timezone.ilike(f"%{timezone_pattern}%"))
        
        stmt = stmt.order_by(
            Candidate.lia_score.desc().nullsfirst(),
            Candidate.created_at.desc()
        ).limit(limit)
        
        if _structured_conditions:
            strict_stmt = stmt.where(and_(*_structured_conditions))
            result = await db.execute(strict_stmt)
            candidates = result.scalars().all()
            if not candidates:
                logger.warning(
                    "[search_local] filtros estruturados (%d) zeraram a busca '%s' "
                    "— degradando para text-only (filtros tratados como soft, P0-1)",
                    len(_structured_conditions), query,
                )
                result = await db.execute(stmt)
                candidates = result.scalars().all()
        else:
            result = await db.execute(stmt)
            candidates = result.scalars().all()
        
        # Convert to CandidateProfile
        profiles = []
        for c in candidates:
            # Extract values safely
            name_str = str(c.name) if c.name else ""
            name_parts = name_str.split() if name_str else []
            first_name = name_parts[0] if name_parts else None
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
            
            location_parts = []
            if c.location_city:
                location_parts.append(str(c.location_city))
            if c.location_state:
                location_parts.append(str(c.location_state))
            if c.location_country:
                location_parts.append(str(c.location_country))
            location_str = ", ".join(location_parts) if location_parts else None
            
            profile = CandidateProfile(
                docid=str(c.id),
                name=name_str or None,
                first_name=first_name,
                last_name=last_name,
                headline=str(c.current_title) if c.current_title else None,
                current_title=str(c.current_title) if c.current_title else None,
                current_company=str(c.current_company) if c.current_company else None,
                location=location_str,
                total_experience_years=float(c.years_of_experience) if c.years_of_experience else None,
                skills=list(c.technical_skills) if c.technical_skills else [],
                emails=[str(c.email)] if c.email else [],
                has_emails=c.email is not None,
                phone_numbers=[str(c.phone)] if c.phone else [],
                has_phone_numbers=c.phone is not None,
                linkedin_url=str(c.linkedin_url) if c.linkedin_url else None,
                match_score=float(c.lia_score) if c.lia_score else None,
                summary=str(c.resume_text)[:500] if c.resume_text else None,
                is_discovered=False  # Main candidates table
            )
            profiles.append(profile)
        
        # Track linkedin URLs for deduplication
        seen_linkedin_urls = set()
        for p in profiles:
            if p.linkedin_url:
                seen_linkedin_urls.add(p.linkedin_url.lower().rstrip('/'))
        
        # 2. Search staging table (ExternalCandidateProfile) if include_discovered=True
        if include_discovered:
            # Build search conditions for staging table
            staging_conditions = []
            for term in search_terms:
                term_pattern = f"%{term}%"
                staging_conditions.append(
                    or_(
                        func.lower(ExternalCandidateProfile.name).ilike(term_pattern),
                        func.lower(ExternalCandidateProfile.current_title).ilike(term_pattern),
                        func.lower(ExternalCandidateProfile.current_company).ilike(term_pattern),
                        func.lower(ExternalCandidateProfile.location_city).ilike(term_pattern),
                        func.lower(ExternalCandidateProfile.location_state).ilike(term_pattern),
                        func.lower(ExternalCandidateProfile.location_raw).ilike(term_pattern),
                    )
                )
            
            # Query staging table - exclude already promoted profiles
            # ADR-001-EXEMPT: same dynamic builder pattern as line 811 (Candidate
            # branch above) — this is the parallel staging-table branch sharing
            # search_terms/require_email/require_phone with conditional WHERE
            # accumulation. Splitting into a repo while keeping symmetry with
            # line 811 would duplicate the optional-filter wiring.
            staging_stmt = select(ExternalCandidateProfile).where(
                ExternalCandidateProfile.status != 'promoted',
                ExternalCandidateProfile.promoted_to_candidate_id.is_(None)
            )
            
            if staging_conditions:
                staging_stmt = staging_stmt.where(or_(*staging_conditions))
            
            # Filtro por email/telefone for staging
            if require_email:
                staging_stmt = staging_stmt.where(ExternalCandidateProfile.has_email)
            if require_phone:
                staging_stmt = staging_stmt.where(ExternalCandidateProfile.has_phone)
            
            # Calculate remaining limit
            remaining_limit = max(0, limit - len(profiles))
            if remaining_limit > 0:
                staging_stmt = staging_stmt.order_by(
                    ExternalCandidateProfile.similarity_score.desc().nullsfirst(),
                    ExternalCandidateProfile.created_at.desc()
                ).limit(remaining_limit)
                
                staging_result = await db.execute(staging_stmt)
                staging_candidates = staging_result.scalars().all()
                
                for sc in staging_candidates:
                    # Deduplicate by linkedin_url
                    if sc.linkedin_url:
                        normalized_url = sc.linkedin_url.lower().rstrip('/')
                        if normalized_url in seen_linkedin_urls:
                            continue
                        seen_linkedin_urls.add(normalized_url)
                    
                    # Build location string
                    staging_location_parts = []
                    if sc.location_city:
                        staging_location_parts.append(str(sc.location_city))
                    if sc.location_state:
                        staging_location_parts.append(str(sc.location_state))
                    if sc.location_country:
                        staging_location_parts.append(str(sc.location_country))
                    staging_location_str = ", ".join(staging_location_parts) if staging_location_parts else sc.location_raw
                    
                    staging_profile = CandidateProfile(
                        docid=str(sc.id),
                        name=str(sc.name) if sc.name else None,
                        first_name=str(sc.first_name) if sc.first_name else None,
                        last_name=str(sc.last_name) if sc.last_name else None,
                        headline=str(sc.headline) if sc.headline else None,
                        current_title=str(sc.current_title) if sc.current_title else None,
                        current_company=str(sc.current_company) if sc.current_company else None,
                        location=staging_location_str,
                        total_experience_years=float(sc.years_of_experience) if sc.years_of_experience else None,
                        skills=list(sc.skills) if sc.skills else [],
                        expertise=list(sc.expertise) if sc.expertise else [],
                        emails=[str(sc.email)] if sc.email else [],
                        has_emails=sc.has_email or False,
                        phone_numbers=[str(sc.phone)] if sc.phone else [],
                        has_phone_numbers=sc.has_phone or False,
                        linkedin_url=str(sc.linkedin_url) if sc.linkedin_url else None,
                        picture_url=str(sc.avatar_url) if sc.avatar_url else None,
                        match_score=float(sc.similarity_score) if sc.similarity_score else None,
                        summary=str(sc.summary)[:500] if sc.summary else None,
                        is_opentowork=sc.is_open_to_work,
                        is_discovered=True  # Mark as discovered (from staging table)
                    )
                    profiles.append(staging_profile)
                
                logger.info(f"Found {len(staging_candidates)} candidates in staging table")
        
        logger.info(f"Found {len(profiles)} total candidates (local + discovered)")
        return profiles, len(profiles)
    
    @staticmethod
    def _dedup_pearch_against_local(local_candidates, pearch_candidates):
        """G-14: remove candidatos Pearch que ja vieram no resultado local, por
        IDENTIDADE (linkedin_url normalizado). O docid_blacklist nao cobre isso:
        docid local = PK do banco, docid Pearch = id do Pearch (namespaces distintos),
        entao o mesmo humano persistido de uma busca anterior reaparecia duplicado.
        """
        def _url(c):
            try:
                u = c.get_linkedin_url()
            except Exception:
                u = getattr(c, "linkedin_url", None)
            if not u:
                return None
            u = u.strip().lower().rstrip("/")
            for pfx in ("https://", "http://", "www."):
                if u.startswith(pfx):
                    u = u[len(pfx):]
            u = u.split("?")[0].rstrip("/")
            return u or None

        local_urls = {x for x in (_url(c) for c in local_candidates) if x}
        if not local_urls:
            return pearch_candidates

        deduped = []
        removed = 0
        for c in pearch_candidates:
            n = _url(c)
            if n and n in local_urls:
                removed += 1
                continue
            deduped.append(c)
        if removed:
            logger.info(
                "[HybridSearch] dedup: %d candidato(s) Pearch removido(s) (ja no resultado local)",
                removed,
            )
        return deduped

    async def hybrid_search(
        self,
        db: AsyncSession,
        request: HybridSearchRequest
    ) -> HybridSearchResponse:
        """
        Executa busca híbrida: primeiro no banco local, depois na Pearch.
        
        Args:
            db: Sessão do banco
            request: Configurações de busca híbrida
        
        Returns:
            HybridSearchResponse com resultados combinados
        """
        logger.info(f"Starting hybrid search: '{request.query}'")
        
        import time as _time
        start_time = datetime.now()
        _loop_start_monotonic = _time.monotonic()
        local_candidates = []
        pearch_candidates = []
        pearch_credits_used = None
        pearch_credits_remaining = None
        warning_message = None
        # Task #1219 — diagnósticos do loop de completude (modo require_emails)
        _filtered_no_contact = 0
        _sources_exhausted = False
        
        # 1. Busca local
        if request.search_local_first:
            local_start = datetime.now()
            
            # Extract filters from SearchSpec if provided
            search_spec = request.get_search_spec()
            funding_stages = None
            company_hq_countries = None
            company_tags = None
            institution_tiers = None
            institution_countries = None
            institution_ranking_max = None
            timezones = None
            timezone_pattern = None
            industries = None
            
            if search_spec:
                # Funding stage filters
                if search_spec.funding_stages:
                    funding_stages = search_spec.funding_stages
                elif search_spec.funding_stage:
                    funding_stages = [search_spec.funding_stage]
                
                # Company HQ country filters
                if search_spec.company_hq_countries:
                    company_hq_countries = search_spec.company_hq_countries
                elif search_spec.company_hq_country:
                    company_hq_countries = [search_spec.company_hq_country]
                
                # Company tags filter
                if search_spec.company_tags:
                    company_tags = search_spec.company_tags
                
                # Institution tier filters
                if search_spec.institution_tiers:
                    institution_tiers = search_spec.institution_tiers
                elif search_spec.institution_tier:
                    institution_tiers = [search_spec.institution_tier]
                
                # Institution country filters
                if search_spec.institution_countries:
                    institution_countries = search_spec.institution_countries
                elif search_spec.institution_country:
                    institution_countries = [search_spec.institution_country]
                
                # Institution ranking filter
                if search_spec.institution_ranking_max is not None:
                    institution_ranking_max = search_spec.institution_ranking_max
                
                # Timezone filters
                if search_spec.timezones:
                    timezones = search_spec.timezones
                elif search_spec.timezone:
                    # Check if timezone contains wildcard pattern
                    if '%' in search_spec.timezone or '*' in search_spec.timezone:
                        timezone_pattern = search_spec.timezone.replace('*', '')
                    else:
                        timezones = [search_spec.timezone]
                
                # Industries filter from search_spec
                if search_spec.industries:
                    industries = search_spec.industries
                elif search_spec.industry:
                    industries = [search_spec.industry]
                
                logger.info(f"Local search filters from SearchSpec - funding_stages: {funding_stages}, "
                           f"company_hq_countries: {company_hq_countries}, institution_tiers: {institution_tiers}, "
                           f"timezones: {timezones}, industries: {industries}")
            
            local_candidates, _ = await self.search_local_candidates(
                db=db,
                query=request.query,
                limit=request.local_limit,
                exclude_ids=[int(id) for id in request.exclude_candidate_ids if id.isdigit()],
                include_discovered=request.include_discovered,
                # Task #1219 — no modo "Híbrida com email" o pool local também é
                # pré-filtrado a quem TEM email (DB-level). Cobre a tabela
                # Candidate; o pós-filtro abaixo cobre staging/discovered.
                require_email=request.require_emails,
                industries=industries,
                funding_stages=funding_stages,
                company_hq_countries=company_hq_countries,
                company_tags=company_tags,
                institution_tiers=institution_tiers,
                institution_countries=institution_countries,
                institution_ranking_max=institution_ranking_max,
                timezones=timezones,
                timezone_pattern=timezone_pattern
            )
            if request.require_emails:
                _before = len(local_candidates)
                local_candidates = [c for c in local_candidates if _profile_has_email(c)]
                _filtered_no_contact += _before - len(local_candidates)
            local_time = (datetime.now() - local_start).total_seconds()
        else:
            local_time = 0
        
        # 2. Busca Pearch (se necessário e permitido)
        pearch_time = 0
        if request.include_pearch and self.api_key:
            # Calcula IDs a excluir (locais + já excluídos)
            exclude_docids = list(request.exclude_candidate_ids)
            for lc in local_candidates:
                if lc.docid:
                    exclude_docids.append(lc.docid)
            
            # Extrai SearchSpec se fornecido para filtros avançados
            search_spec = request.get_search_spec()
            custom_filters = None
            use_strict_filters = False
            
            if search_spec:
                custom_filters = search_spec.to_pearch_custom_filters()
                use_strict_filters = search_spec.should_use_strict_filters()
                logger.info(f"SearchSpec applied - custom_filters: {custom_filters}, strict: {use_strict_filters}")
            
            pearch_request = PearchSearchRequest(
                query=request.query,
                thread_id=request.thread_id,
                type=request.pearch_type,
                insights=False,  # insights IA por candidato custa ~10s -> busca estourava deadline. On-demand ao abrir candidato.
                profile_scoring=True,
                strict_filters=use_strict_filters,
                custom_filters=custom_filters if custom_filters else None,
                require_emails=request.require_emails,
                require_phone_numbers=request.require_phone_numbers,
                show_emails=request.show_emails,
                show_phone_numbers=request.show_phone_numbers,
                limit=request.pearch_limit,
                docid_blacklist=exclude_docids
            )
            
            # Estima custos
            estimate = self.estimate_credits(pearch_request)
            warning_message = f"Busca Pearch pode consumir até {estimate.total_estimated} créditos"
            
            pearch_start = datetime.now()
            try:
                if request.require_emails:
                    # Task #1219 — modo "Híbrida com email": loop de completude.
                    # BUG-PEARCH-TARGET (2026-06-09): _target subtraía os candidatos
                    # locais do limite Pearch. Em buscas híbridas onde local já retorna
                    # >= pearch_limit candidatos com email, _target ficava 0 → Pearch
                    # nunca era chamado → zero candidatos globais. Correto: Pearch busca
                    # sua própria cota (additive, não cota combinada). O dedup trata
                    # sobreposições. Mantemos pearch_limit como teto do loop de email.
                    _target = request.pearch_limit
                    pearch_candidates, _loop_diag = await self._accumulate_pearch_with_emails(
                        base_request=pearch_request,
                        target=_target,
                        loop_start_monotonic=_loop_start_monotonic,
                    )
                    pearch_candidates = self._dedup_pearch_against_local(local_candidates, pearch_candidates)
                    pearch_credits_remaining = _loop_diag.get("credits_remaining")
                    _filtered_no_contact += _loop_diag.get("filtered_no_email", 0)
                    _sources_exhausted = _loop_diag.get("sources_exhausted", False)
                    if _loop_diag.get("error_message"):
                        warning_message = _loop_diag["error_message"]
                else:
                    pearch_response = await asyncio.wait_for(
                        self.search_candidates(pearch_request),
                        timeout=_PEARCH_CALL_DEADLINE_SECONDS,
                    )
                    pearch_candidates = pearch_response.get_candidates()
                    pearch_candidates = self._dedup_pearch_against_local(local_candidates, pearch_candidates)
                    pearch_credits_remaining = pearch_response.credits_remaining
                pearch_time = (datetime.now() - pearch_start).total_seconds()
            except Exception as e:
                logger.error(f"Pearch search failed: {e}")
                warning_message = f"Busca externa falhou: {str(e)}"
        
        (datetime.now() - start_time).total_seconds()
        
        return HybridSearchResponse(
            query=request.query,
            thread_id=request.thread_id,
            local_candidates=local_candidates,
            pearch_candidates=pearch_candidates,
            local_count=len(local_candidates),
            pearch_count=len(pearch_candidates),
            total_count=len(local_candidates) + len(pearch_candidates),
            pearch_credits_used=pearch_credits_used,
            pearch_credits_remaining=pearch_credits_remaining,
            local_search_time=local_time,
            pearch_search_time=pearch_time,
            status="completed",
            warning_message=warning_message,
            filtered_no_contact=_filtered_no_contact,
            sources_exhausted=_sources_exhausted,
        )

    async def _accumulate_pearch_with_emails(
        self,
        base_request: PearchSearchRequest,
        target: int,
        loop_start_monotonic: float,
    ) -> tuple[list, dict]:
        """Task #1219 — loop de completude: acumula candidatos Pearch COM email.

        Percorre páginas da Pearch (mesmo ``thread_id`` + ``docid_blacklist``
        crescente) até acumular ``target`` candidatos com email ou esgotar as
        fontes. Filtra cada página a quem TEM email (``_profile_has_email``).

        Guardrails (sem loop infinito, sem fake success):
          - deadline interno (``SEARCH_HYBRID_EMAIL_LOOP_DEADLINE_SECONDS``),
            menor que o deadline da rota — para honrar resultado parcial;
          - teto de páginas (``SEARCH_HYBRID_EMAIL_MAX_PAGES``);
          - parada em erro/429 (search_candidates já roteia 429 p/ fallback);
          - parada quando uma página não traz NENHUM docid novo (esgotamento).

        Retorna ``(candidatos[:target], diagnostics)``. ``diagnostics`` inclui
        ``filtered_no_email``, ``sources_exhausted``, ``credits_remaining``,
        ``pages`` e ``stop_reason``.
        """
        import time as _time

        accumulated: list = []
        seen_docids: set[str] = set(base_request.docid_blacklist or [])
        diagnostics: dict = {
            "pages": 0,
            "filtered_no_email": 0,
            "sources_exhausted": False,
            "credits_remaining": None,
            "stop_reason": None,
            "error_message": None,
        }

        if target <= 0:
            diagnostics["stop_reason"] = "target_reached"
            return accumulated, diagnostics

        max_pages = max(1, int(settings.SEARCH_HYBRID_EMAIL_MAX_PAGES))
        deadline = loop_start_monotonic + float(
            settings.SEARCH_HYBRID_EMAIL_LOOP_DEADLINE_SECONDS
        )
        thread_id = base_request.thread_id

        while len(accumulated) < target:
            if diagnostics["pages"] >= max_pages:
                diagnostics["stop_reason"] = "max_pages"
                break
            now = _time.monotonic()
            if now >= deadline:
                diagnostics["stop_reason"] = "deadline"
                break

            # Pede um pouco mais que o restante para compensar a atrição do
            # filtro de email server-side; cada chamada respeita o orçamento
            # de tempo restante do loop (per-page timeout).
            remaining = target - len(accumulated)
            page_limit = min(max(remaining * 2, 5), 50)
            per_page_timeout = max(1.0, deadline - now)

            page_request = base_request.model_copy(update={
                "thread_id": thread_id,
                "limit": page_limit,
                "docid_blacklist": list(seen_docids),
            })

            try:
                resp = await self.search_candidates(
                    page_request, timeout=per_page_timeout
                )
            except Exception as e:  # noqa: BLE001 — parada graciosa, parcial honesto
                logger.warning(
                    "[HybridEmailLoop] página %d falhou (%s) — devolvendo parcial",
                    diagnostics["pages"], e,
                )
                diagnostics["stop_reason"] = "error"
                diagnostics["error_message"] = f"Busca externa interrompida: {e}"
                break

            diagnostics["pages"] += 1
            if resp.credits_remaining is not None:
                diagnostics["credits_remaining"] = resp.credits_remaining
            thread_id = resp.thread_id or thread_id
            diagnostics["thread_id"] = thread_id

            page_candidates = resp.get_candidates()
            new_this_page = 0
            for c in page_candidates:
                docid = getattr(c, "docid", None)
                if docid and docid in seen_docids:
                    continue
                if docid:
                    seen_docids.add(docid)
                new_this_page += 1
                if _profile_has_email(c):
                    accumulated.append(c)
                else:
                    diagnostics["filtered_no_email"] += 1

            # Esgotamento: página não trouxe nenhum docid novo.
            if new_this_page == 0:
                diagnostics["sources_exhausted"] = True
                diagnostics["stop_reason"] = diagnostics["stop_reason"] or "exhausted"
                break

        if len(accumulated) >= target and not diagnostics["stop_reason"]:
            diagnostics["stop_reason"] = "target_reached"

        logger.info(
            "[HybridEmailLoop] alvo=%d obtidos=%d páginas=%d filtrados_sem_email=%d "
            "esgotado=%s motivo=%s",
            target, len(accumulated), diagnostics["pages"],
            diagnostics["filtered_no_email"], diagnostics["sources_exhausted"],
            diagnostics["stop_reason"],
        )
        return accumulated[:target], diagnostics

    async def refine_search(
        self,
        thread_id: str,
        additional_query: str,
        limit: int | None = None,
        require_emails: bool = False,
        require_phone_numbers: bool = False,
        docid_blacklist: list[str] | None = None,
    ) -> PearchSearchResponse:
        """
        Refina uma busca existente usando o thread_id.
        
        Args:
            thread_id: ID do thread da busca anterior
            additional_query: Critérios adicionais ou alterações
            limit: Novo limite (opcional, para pedir mais resultados)
            require_emails: Task #1219 — quando True, completa o incremento
                percorrendo páginas até atingir ``limit`` candidatos COM email
                (load-more do modo "Híbrida com email").
            require_phone_numbers: encaminhado ao Pearch.
            docid_blacklist: docids já exibidos (não repetir no incremento).
        
        Returns:
            PearchSearchResponse com resultados refinados
        """
        import time as _time

        request = PearchSearchRequest(
            query=additional_query,
            thread_id=thread_id,
            type=SearchType.FAST,
            insights=True,
            profile_scoring=True,
            limit=limit or 10,
            require_emails=require_emails,
            require_phone_numbers=require_phone_numbers,
            docid_blacklist=docid_blacklist or [],
        )

        # Task #1219 — load-more em modo email: completa o incremento usando o
        # mesmo loop de completude da busca híbrida (mantém a garantia de "só
        # com email" + guardrails). Reaproveita a forma da resposta Pearch.
        if require_emails:
            target = limit or 10
            accumulated, diag = await self._accumulate_pearch_with_emails(
                base_request=request,
                target=target,
                loop_start_monotonic=_time.monotonic(),
            )
            return PearchSearchResponse(
                uuid="refine-email-loop",
                thread_id=diag.get("thread_id") or thread_id,
                query=additional_query,
                status="completed",
                total_estimate=len(accumulated),
                credits_remaining=diag.get("credits_remaining"),
                search_results=[],
                candidates=accumulated,
            )
        
        return await self.search_candidates(request)


# Singleton instance
pearch_service = PearchService()

# FastAPI dependency injection factory
def get_pearch_service() -> "PearchService":
    return pearch_service

