"""
MultiStrategySearchService — runs 4 search strategies in parallel with deduplication.

Implements the hireEZ EZ Agent pattern: multiple strategies, dedup, weighted ranking.

Strategies:
  A. direct       — exact criteria from job/archetype
  B. adjacent     — LLM-generated similar titles + related skills
  C. silver       — candidates who were finalists in similar jobs
  D. reengagement — inactive candidates (180+ days) matching skills

Apply to: lia-agent-system/app/services/multi_strategy_search.py
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    strategy_id: str
    strategy_name: str
    candidates: list[dict]
    count: int
    elapsed_ms: float
    error: Optional[str] = None


@dataclass
class MultiStrategyResult:
    total_unique: int
    candidates_ranked: list[dict]  # deduplicated + ranked by weighted score
    strategy_results: list[StrategyResult]
    elapsed_ms: float


class MultiStrategySearchService:

    async def search(
        self,
        job_title: str,
        required_skills: list[str],
        location: str,
        company_id: str,
        job_id: Optional[str] = None,
        seniority: Optional[str] = None,
        exclusions: Optional[list[str]] = None,
        strategies: Optional[list[str]] = None,
        weights: Optional[dict[str, float]] = None,
        limit: int = 50,
    ) -> MultiStrategyResult:
        """
        Execute multiple search strategies in parallel and return deduplicated ranked results.
        """
        start = time.time()

        enabled = strategies or ["direct", "adjacent", "silver", "reengagement"]
        w = weights or {"direct": 0.30, "adjacent": 0.25, "silver": 0.25, "reengagement": 0.20}

        # Build tasks for parallel execution
        tasks: dict[str, asyncio.Task] = {}
        if "direct" in enabled:
            tasks["direct"] = asyncio.create_task(
                self._strategy_direct(job_title, required_skills, location, seniority, exclusions, limit)
            )
        if "adjacent" in enabled:
            tasks["adjacent"] = asyncio.create_task(
                self._strategy_adjacent(job_title, required_skills, location, limit, company_id=company_id)
            )
        if "silver" in enabled and job_id:
            tasks["silver"] = asyncio.create_task(
                self._strategy_silver_medalists(job_id, required_skills, company_id, limit)
            )
        if "reengagement" in enabled:
            tasks["reengagement"] = asyncio.create_task(
                self._strategy_reengagement(company_id, required_skills, limit)
            )

        # Await all in parallel
        results_raw = await asyncio.gather(*tasks.values(), return_exceptions=True)

        strategy_results: list[StrategyResult] = []
        for (sid, _task), result in zip(tasks.items(), results_raw):
            if isinstance(result, Exception):
                logger.warning("[MultiStrategy] %s failed: %s", sid, result)
                strategy_results.append(StrategyResult(
                    strategy_id=sid, strategy_name=self._strategy_name(sid),
                    candidates=[], count=0, elapsed_ms=0, error=str(result)
                ))
            else:
                strategy_results.append(result)

        # Deduplicate by email or linkedin_url or id
        all_candidates: list[dict] = []
        seen: set[str] = set()
        for sr in strategy_results:
            for c in sr.candidates:
                uid = c.get("email") or c.get("linkedin_url") or c.get("id") or ""
                if uid and uid in seen:
                    # Candidate already exists — merge strategy info
                    existing = next((x for x in all_candidates if self._uid(x) == uid), None)
                    if existing:
                        existing.setdefault("found_via_strategies", []).append(sr.strategy_id)
                    continue
                if uid:
                    seen.add(uid)
                c["found_via"] = sr.strategy_id
                c["found_via_strategies"] = [sr.strategy_id]
                all_candidates.append(c)

        # Weighted scoring
        for c in all_candidates:
            base_score = c.get("lia_score") or c.get("fit_score") or c.get("score") or 50
            strategy_bonus = sum(
                w.get(s, 0.1) for s in c.get("found_via_strategies", [])
            )
            c["multi_strategy_score"] = round(float(base_score) * (1 + strategy_bonus * 0.2), 1)

        # Rank by multi_strategy_score descending
        ranked = sorted(all_candidates, key=lambda x: x.get("multi_strategy_score", 0), reverse=True)[:limit]

        elapsed = (time.time() - start) * 1000
        return MultiStrategyResult(
            total_unique=len(ranked),
            candidates_ranked=ranked,
            strategy_results=strategy_results,
            elapsed_ms=round(elapsed, 1),
        )

    # ---------- Strategies ----------

    async def _strategy_direct(
        self, title: str, skills: list[str], location: str,
        seniority: Optional[str], exclusions: Optional[list[str]], limit: int,
    ) -> StrategyResult:
        """Strategy A: exact criteria search."""
        t = time.time()
        query = f"Buscar {title} com {', '.join(skills)} em {location}"
        if seniority:
            query += f" nível {seniority}"
        if exclusions:
            query += f". Excluir: {', '.join(exclusions)}"

        candidates = await self._execute_search(query, limit)
        return StrategyResult(
            strategy_id="direct", strategy_name="Busca Direta",
            candidates=candidates, count=len(candidates),
            elapsed_ms=round((time.time() - t) * 1000, 1),
        )

    async def _strategy_adjacent(
        self, title: str, skills: list[str], location: str, limit: int,
        company_id: str | None = None,
    ) -> StrategyResult:
        """Strategy B: similar titles + related skills via LLM."""
        t = time.time()
        try:
            # Canonical LLM factory (multi-tenant aware). Replaces broken
            # get_llm import — feature was 100% in fallback (single title,
            # no adjacent expansion) until 2026-05-27.
            from app.shared.providers.llm_factory import create_tracked_llm
            llm = create_tracked_llm(
                temperature=0.3,
                service_name="MultiStrategySearch",
                operation="adjacent_titles",
                max_output_tokens=256,
                tenant_id=company_id,
            )
            resp = await llm.ainvoke(
                f"Liste 3 títulos de cargo similares a '{title}' no mercado brasileiro. "
                f"Liste também 3 skills relacionadas a {', '.join(skills[:3])}. "
                f'Responda APENAS com JSON: {{"titles": [...], "related_skills": [...]}}'
            )
            data = json.loads(resp.content)
            adj_titles = data.get("titles", [title])
            related_skills = data.get("related_skills", skills)
        except Exception:
            adj_titles = [title]
            related_skills = skills

        query = f"Buscar {' ou '.join(adj_titles)} com {', '.join(related_skills)} em {location}"
        candidates = await self._execute_search(query, limit)

        return StrategyResult(
            strategy_id="adjacent", strategy_name="Títulos Adjacentes",
            candidates=candidates, count=len(candidates),
            elapsed_ms=round((time.time() - t) * 1000, 1),
        )

    async def _strategy_silver_medalists(
        self, job_id: str, skills: list[str], company_id: str, limit: int,
    ) -> StrategyResult:
        """Strategy C: candidates who were finalists in similar jobs but not hired."""
        t = time.time()
        candidates = []
        try:
            # Search for candidates in advanced stages of similar jobs
            query = f"Candidatos que chegaram à etapa de entrevista em vagas similares, skills: {', '.join(skills)}"
            candidates = await self._execute_search(query, limit)

            # Mark as silver medalists
            for c in candidates:
                c["silver_medalist"] = True
        except Exception as e:
            logger.warning("[MultiStrategy] silver_medalists failed: %s", e)

        return StrategyResult(
            strategy_id="silver", strategy_name="Silver Medalists",
            candidates=candidates, count=len(candidates),
            elapsed_ms=round((time.time() - t) * 1000, 1),
        )

    async def _strategy_reengagement(
        self, company_id: str, skills: list[str], limit: int,
    ) -> StrategyResult:
        """Strategy D: inactive candidates (180+ days) in internal database."""
        t = time.time()
        candidates = []
        try:
            query = (
                f"Candidatos inativos há mais de 6 meses no banco interno "
                f"com skills: {', '.join(skills)}. Priorizar quem demonstrou interesse anteriormente."
            )
            candidates = await self._execute_search(query, limit)

            for c in candidates:
                c["reengagement"] = True
        except Exception as e:
            logger.warning("[MultiStrategy] reengagement failed: %s", e)

        return StrategyResult(
            strategy_id="reengagement", strategy_name="Reengajamento",
            candidates=candidates, count=len(candidates),
            elapsed_ms=round((time.time() - t) * 1000, 1),
        )

    # ---------- Helpers ----------

    async def _execute_search(self, query: str, limit: int) -> list[dict]:
        """Execute search using existing SourcingSearchAgent."""
        try:
            from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
            from lia_agents_core.agent_interface import AgentInput

            agent = SourcingSearchAgent()
            output = await agent.process(AgentInput(
                message=query,
                context={"limit": limit},
            ))
            return output.data.get("candidates", [])[:limit]
        except Exception as e:
            logger.warning("[MultiStrategy] Search execution failed: %s", e)
            return []

    @staticmethod
    def _uid(candidate: dict) -> str:
        return candidate.get("email") or candidate.get("linkedin_url") or candidate.get("id") or ""

    @staticmethod
    def _strategy_name(sid: str) -> str:
        return {
            "direct": "Busca Direta",
            "adjacent": "Títulos Adjacentes",
            "silver": "Silver Medalists",
            "reengagement": "Reengajamento",
        }.get(sid, sid)


multi_strategy_search = MultiStrategySearchService()
