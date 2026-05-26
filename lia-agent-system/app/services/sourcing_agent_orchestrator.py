"""
SourcingAgentOrchestrator — manages persistent multi-agent sourcing per job/pool.

Each sourcing agent is an isolated instance with:
  - Persistent search_strategy that evolves via recruiter feedback
  - Calibration via Big Card modal (min 3 approvals)
  - Recalibration on every approve/reject signal

Integrates with:
  - SourcingSearchAgent (existing LIA) for actual candidate search
  - AgentTemplate (Stage 8) for prompt configuration
  - TalentPool (Phase 6.1) as candidate destination

Apply to: lia-agent-system/app/services/sourcing_agent_orchestrator.py
"""

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

# SourcingAgentSignal canonical-only fail-closed (Part 1.5 + Part 2 layers 1+2):
# writes/reads usam custom_agent_id; agent_id legacy é nullable (migration 209).
from lia_models.sourcing_agent import SourcingAgentSignal  # noqa: E402 imported at module level for consolidation

logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    calibration_version: int
    total_signals: int
    approved_count: int
    rejected_count: int
    strategy_updated: bool
    new_exclusions: list[str]
    new_positive_signals: list[str]


class SourcingAgentOrchestrator:

    async def create_agent(
        self,
        company_id: str,
        agent_name: str,
        job_id: Optional[str] = None,
        talent_pool_id: Optional[str] = None,
        agent_template_id: Optional[str] = None,
        search_strategy: Optional[dict] = None,
        preferences: Optional[dict] = None,
        db=None,
    ) -> dict:
        """
        Cria CustomAgent canonical (category='sourcing') preservando dict return shape.

        Sprint 7B-3b Part 1: refactor interno. Caller legacy /sourcing-agents POST
        continua funcionando — return shape backward compat {agent_id, status, strategy}.

        Auto-extract de search_strategy via LLM quando job_id provided (preservado).
        agent_template_id → copia system_prompt do template (canonical AgentTemplate).
        talent_pool_id → cria PoolAgentAssignment (canonical Pool→Agent canonical).
        """
        from lia_models.custom_agent import CustomAgent, CustomAgentStatus
        from lia_models.pool_agent_assignment import PoolAgentAssignment

        # Extract strategy from JD if not provided (PRESERVADO)
        if not search_strategy and job_id:
            search_strategy = await self._extract_strategy_from_job(job_id, db)
        elif not search_strategy:
            search_strategy = {"required_skills": [], "exclusions": [], "positive_signals": []}

        # Resolve system_prompt do template (quando provided)
        system_prompt = ""
        if agent_template_id:
            try:
                from lia_models.agent_template import AgentTemplate
                from sqlalchemy import select

                tpl_result = await db.execute(
                    select(AgentTemplate).where(AgentTemplate.id == agent_template_id)
                )
                template = tpl_result.scalar_one_or_none()
                if template and getattr(template, "system_prompt", None):
                    system_prompt = template.system_prompt
            except Exception as exc:
                logger.error(
                    "[SourcingAgent] template lookup failed for template_id=%s: %s",
                    agent_template_id, exc, exc_info=True,
                )

        if not system_prompt:
            system_prompt = (
                f"Você é um agente de sourcing autônomo chamado {agent_name}. "
                f"Busque candidatos seguindo a search_strategy canonical e calibre "
                f"via feedback do recrutador."
            )

        # Cria CustomAgent canonical (category='sourcing')
        agent_id = uuid.uuid4()
        agent = CustomAgent(
            id=agent_id,
            company_id=company_id,
            created_by=company_id,  # actor canonical when no user context (admin/system)
            name=agent_name,
            role="sourcing-agent",
            description=f"Sourcing agent for job={job_id or 'none'} pool={talent_pool_id or 'none'}",
            system_prompt=system_prompt,
            allowed_tools=[],
            domain="general",
            status=CustomAgentStatus.ACTIVE.value,
            category="sourcing",
            search_strategy=search_strategy,
            runtime_metrics={},
            config={
                "job_id": job_id,
                "talent_pool_id": talent_pool_id,
                "agent_template_id": agent_template_id,
                "preferences": preferences or self._default_preferences(),
            },
        )

        db.add(agent)
        await db.flush()

        # PoolAgentAssignment quando talent_pool provided
        if talent_pool_id:
            assignment = PoolAgentAssignment(
                id=uuid.uuid4(),
                company_id=company_id,
                talent_pool_id=talent_pool_id,
                custom_agent_id=agent_id,
                status="active",
                created_by=company_id,
            )
            db.add(assignment)
            await db.flush()

        await db.commit()

        # Audit dim 5 — canonical log_decision (non-blocking)
        try:
            from app.shared.compliance.audit_service import AuditService

            audit_service = AuditService()
            await audit_service.log_decision(
                company_id=company_id,
                agent_name=agent_name,
                decision_type="creation",
                action="custom_agent_created",
                decision="created",
                reasoning=[
                    f"category=sourcing template={agent_template_id or 'none'} "
                    f"job={job_id or 'none'} pool={talent_pool_id or 'none'}"
                ],
                criteria_used=[],
            )
        except Exception as exc:
            logger.error(
                "[SourcingAgent] audit log_decision failed (non-blocking): %s",
                exc, exc_info=True,
            )

        logger.info(
            "[SourcingAgent] CustomAgent created agent=%s category=sourcing job=%s pool=%s",
            agent_id, job_id, talent_pool_id,
        )

        # Backward compat: dict shape antiga
        return {
            "agent_id": str(agent_id),
            "status": "active",
            "strategy": search_strategy,
        }

    async def process_feedback(
        self,
        agent_id: str,
        candidate_id: str,
        signal_type: str,  # "positive" or "negative"
        reason: str,
        db=None,
    ) -> CalibrationResult:
        """
        Process recruiter feedback (approve/reject) and recalibrate agent strategy.

        This is the core of the Juicebox-style feedback loop:
        - Each rejection + reason → LLM extracts anti-criteria → added to exclusions
        - Each approval → LLM extracts positive criteria → reinforces positive_signals
        """
        from lia_models.custom_agent import CustomAgent
        from sqlalchemy import select

        # Load agent canonical (CustomAgent + category='sourcing').
        # Sprint 7B-3b Part 3a: OR shim removed — frontend Part 2 v2 swap completou.
        result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.id == agent_id,
                CustomAgent.category == "sourcing",
            )
        )
        agent = result.scalar_one()

        # Extract criteria from reason via LLM
        criteria = await self._extract_criteria(reason, signal_type)

        # Persist signal (Layer 2 canonical: custom_agent_id direto)
        signal = SourcingAgentSignal(
            id=str(uuid.uuid4()),
            custom_agent_id=agent.id,
            signal_type=signal_type,
            candidate_id=candidate_id,
            reason=reason,
            criteria_extracted=criteria,
        )
        db.add(signal)

        # Recalibrate strategy
        strategy = dict(agent.search_strategy or {})
        new_exclusions = []
        new_positives = []

        if signal_type == "negative":
            strategy.setdefault("exclusions", [])
            new_exclusions = [c for c in criteria if c not in strategy["exclusions"]]
            strategy["exclusions"] = list(set(strategy["exclusions"] + criteria))
        else:
            strategy.setdefault("positive_signals", [])
            new_positives = [c for c in criteria if c not in strategy["positive_signals"]]
            strategy["positive_signals"] = list(set(strategy.get("positive_signals", []) + criteria))

        agent.search_strategy = strategy

        # Counters canonical via runtime_metrics JSONB dict.
        metrics = dict(agent.runtime_metrics or {})
        metrics["calibration_v"] = int(metrics.get("calibration_v", 0)) + 1
        metrics["profiles_viewed"] = int(metrics.get("profiles_viewed", 0)) + 1
        if signal_type == "positive":
            metrics["profiles_approved"] = int(metrics.get("profiles_approved", 0)) + 1
        else:
            metrics["profiles_rejected"] = int(metrics.get("profiles_rejected", 0)) + 1
        agent.runtime_metrics = metrics

        await db.commit()

        # 7.6: Feed calibration signal to ML pipeline for weight adaptation
        # Canonical: app.shared.services.ml_feedback_service (Paulo locked 2026-05-26).
        # Option A silent fallback policy: logger.error(exc_info=True) — NÃO logger.debug.
        # FeedbackSignal canonical dataclass (db, signal) — signature exata
        # de app/domains/analytics/services/ml_feedback_service.py:92.
        try:
            from app.shared.services.ml_feedback_service import (
                FeedbackSignal,
                MLFeedbackService,
            )
            prefs = agent.preferences or {}
            job_id_fallback = prefs.get("job_id", "") if isinstance(prefs, dict) else ""
            ml_svc = MLFeedbackService()
            signal_payload = FeedbackSignal(
                candidate_id=candidate_id,
                job_id=job_id_fallback,
                company_id=agent.company_id,
                ai_score=0.0,
                recruiter_decision="hire" if signal_type == "positive" else "reject",
            )
            await ml_svc.record_signal(db, signal_payload)
        except Exception as ml_err:
            logger.error(
                "[SourcingAgent] MLFeedback record_signal failed (non-blocking side channel): %s",
                ml_err,
                exc_info=True,
            )

        # Audit dim 5 — log_decision canonical (action='pool_agent_dispatch').
        try:
            from app.shared.compliance.audit_service import AuditService
            audit_service = AuditService()
            await audit_service.log_decision(
                company_id=agent.company_id,
                agent_name=agent.name,
                decision_type="feedback",
                action="pool_agent_dispatch",
                decision="positive" if signal_type == "positive" else "negative",
                reasoning=[reason],
                criteria_used=criteria or [],
                candidate_id=candidate_id,
            )
        except Exception as audit_err:
            logger.error(
                "[SourcingAgent] audit log_decision failed (non-blocking): %s",
                audit_err,
                exc_info=True,
            )

        # Count total signals for calibration status (canonical: custom_agent_id)
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count()).where(SourcingAgentSignal.custom_agent_id == agent.id)
        )
        total = count_result.scalar()

        cal_v = int(metrics.get("calibration_v", 0))
        logger.info(
            "[SourcingAgent] agent=%s recalibrated to v%d | %s | criteria=%s",
            agent.id, cal_v, signal_type, criteria,
        )

        return CalibrationResult(
            calibration_version=cal_v,
            total_signals=total,
            approved_count=int(metrics.get("profiles_approved", 0)),
            rejected_count=int(metrics.get("profiles_rejected", 0)),
            strategy_updated=bool(new_exclusions or new_positives),
            new_exclusions=new_exclusions,
            new_positive_signals=new_positives,
        )

    async def get_calibration_candidates(
        self,
        agent_id: str,
        limit: int = 10,
        db=None,
        company_id: str | None = None,
    ) -> list[dict]:
        """
        Get initial candidates for the Big Card calibration modal.

        Uses the agent's search_strategy to find candidates, then generates
        match_criteria for each (Why we matched this profile).

        Multi-tenancy canonical (2026-05-22): filtra por company_id quando
        passado. Levanta LookupError quando agent inexistente ou cross-tenant
        (fail-loud REGRA 4, handler traduz pra HTTP 404).
        """
        from lia_models.custom_agent import CustomAgent
        from sqlalchemy import select

        # Sprint 7B-3b Part 3a: OR shim removed — frontend Part 2 v2 swap completou.
        stmt = select(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.category == "sourcing",
        )
        if company_id is not None:
            stmt = stmt.where(CustomAgent.company_id == company_id)
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()
        if agent is None:
            raise LookupError(
                f"CustomAgent agent_id={agent_id} company_id={company_id} not found"
            )

        query = self._strategy_to_query(agent.search_strategy or {})

        # Wave 3 sectoral wiring (audit 2026-05-21): enriquece query com prompt
        # canonical do AgentTemplate quando agent_template_id está setado em config.
        # Antes: template content era ghost. Agora: SourcingSearchAgent recebe
        # contexto sectorial (LGPD compliance, scoring_weights, screening_questions).
        prefs_for_tpl = agent.preferences or {}
        agent_template_id = prefs_for_tpl.get("agent_template_id") if isinstance(prefs_for_tpl, dict) else None
        template_context = await self._load_template_context(agent_template_id, db)
        if template_context:
            query = (
                f"[CONTEXTO SECTORAL]\n{template_context}\n\n"
                f"[BUSCA ATUAL]\n{query}"
            )

        candidates = []

        try:
            from app.domains.sourcing.agents.sourcing_search_agent import SourcingSearchAgent
            from lia_agents_core.agent_interface import AgentInput

            search_agent = SourcingSearchAgent()
            output = await search_agent.process(AgentInput(
                message=query,
                context={"company_id": agent.company_id, "limit": limit},
            ))
            candidates = output.data.get("candidates", [])[:limit]
        except Exception as e:
            logger.warning("[SourcingAgent] SourcingSearchAgent failed, trying DB fallback: %s", e)

        if not candidates:
            candidates = await self._fallback_db_candidates(agent, limit, db)

        enriched = []
        for c in candidates:
            match_criteria = await self._generate_match_criteria(c, agent.search_strategy)
            enriched.append({**c, "match_criteria": match_criteria})

        return enriched

    async def get_agent_timeline(self, agent_id: str, limit: int = 20, db=None) -> list[dict]:
        """Get activity timeline for the Agents tab.

        Sprint 7B-3b Part 3a: OR shim removed — frontend Part 2 v2 swap completou.
        Lookup canonical via CustomAgent.id; filtra signals por custom_agent_id.
        """
        from lia_models.custom_agent import CustomAgent
        from sqlalchemy import select

        agent_row = (
            await db.execute(
                select(CustomAgent.id).where(
                    CustomAgent.id == agent_id,
                    CustomAgent.category == "sourcing",
                )
            )
        ).scalar_one_or_none()
        if agent_row is None:
            return []

        result = await db.execute(
            select(SourcingAgentSignal)
            .where(SourcingAgentSignal.custom_agent_id == agent_row)
            .order_by(SourcingAgentSignal.created_at.desc())
            .limit(limit)
        )
        signals = result.scalars().all()

        timeline = []
        for s in signals:
            icon = "✅" if s.signal_type == "positive" else "❌"
            timeline.append({
                "id": str(s.id),
                "icon": icon,
                "type": s.signal_type,
                "reason": s.reason,
                "criteria": s.criteria_extracted or [],
                "candidate_id": s.candidate_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
        return timeline

    async def _extract_criteria(self, reason: str, signal_type: str) -> list[str]:
        """Extract criteria from recruiter's feedback reason via LLM."""
        try:
            from app.shared.providers.llm_factory import get_llm
            llm = get_llm(tier="fast")
            action = "aprovou" if signal_type == "positive" else "rejeitou"
            prompt = (
                f"Um recrutador {action} um candidato.\n"
                f'Motivo: "{reason}"\n\n'
                f"Extraia os critérios técnicos como lista de strings curtas (máx 5 itens).\n"
                f'Responda APENAS com JSON: {{"criterios": ["critério 1", "critério 2"]}}'
            )
            resp = await llm.ainvoke(prompt)
            data = json.loads(resp.content)
            return data.get("criterios", [])[:5]
        except Exception as e:
            logger.warning("[SourcingAgent] Criteria extraction failed: %s", e)
            return [reason[:100]]  # Fallback: use reason as-is

    async def _extract_strategy_from_job(self, job_id: str, db) -> dict:
        """Extract search strategy from job description via LLM."""
        try:
            from app.shared.providers.llm_factory import get_llm
            llm = get_llm(tier="fast")
            # Load job (simplified — adapt to actual model)
            prompt = (
                f"Extraia os critérios de busca para um agente de sourcing.\n"
                f"Job ID: {job_id}\n\n"
                f"Responda com JSON:\n"
                f'{{"required_skills": [], "seniority": "", "location": "", '
                f'"min_years_exp": 0, "exclusions": [], "positive_signals": []}}'
            )
            resp = await llm.ainvoke(prompt)
            return json.loads(resp.content)
        except Exception:
            return {"required_skills": [], "exclusions": [], "positive_signals": []}

    async def _generate_match_criteria(self, candidate: dict, strategy: dict) -> list[dict]:
        """Generate 'Why we matched' criteria for calibration card."""
        try:
            from app.shared.providers.llm_factory import get_llm
            llm = get_llm(tier="fast")
            prompt = (
                f"Critérios de busca: {json.dumps(strategy, ensure_ascii=False)}\n"
                f"Candidato: {json.dumps(candidate, ensure_ascii=False)[:500]}\n\n"
                f"Para cada critério da busca, avalie se o candidato atende.\n"
                f"Responda com JSON:\n"
                f'[{{"criterion": "5+ anos Python", "match": "good"|"partial"|"no", '
                f'"explanation": "Candidato tem 7 anos de Python..."}}]'
            )
            resp = await llm.ainvoke(prompt)
            return json.loads(resp.content)
        except Exception:
            return [{"criterion": "Análise geral", "match": "partial", "explanation": "Avaliação automática indisponível"}]

    async def _fallback_db_candidates(self, agent, limit: int, db) -> list[dict]:
        """Fallback: search candidates directly from DB using agent's search_strategy."""
        try:
            from lia_models.candidate import Candidate, CandidateExperience, CandidateEducation
            from sqlalchemy import select, or_, func

            strategy = agent.search_strategy or {}
            required_skills = strategy.get("required_skills", [])
            exclusions = strategy.get("exclusions", [])

            query = select(Candidate).where(Candidate.is_active == True)

            if required_skills:
                skill_filters = []
                for skill in required_skills:
                    skill_filters.append(Candidate.technical_skills.any(skill))
                if skill_filters:
                    query = query.where(or_(*skill_filters))

            if exclusions:
                for excl in exclusions:
                    query = query.where(~Candidate.technical_skills.any(excl))

            query = query.order_by(func.random()).limit(limit)
            result = await db.execute(query)
            candidates_db = result.scalars().all()

            candidates = []
            for c in candidates_db:
                exp_result = await db.execute(
                    select(CandidateExperience)
                    .where(CandidateExperience.candidate_id == c.id)
                    .order_by(CandidateExperience.start_date.desc())
                    .limit(4)
                )
                experiences = exp_result.scalars().all()

                edu_result = await db.execute(
                    select(CandidateEducation)
                    .where(CandidateEducation.candidate_id == c.id)
                    .limit(3)
                )
                educations = edu_result.scalars().all()

                location_parts = [p for p in [c.location_city, c.location_state, c.location_country] if p]
                candidates.append({
                    "id": str(c.id),
                    "name": c.name or "Candidato",
                    "current_title": c.current_title or "",
                    "current_company": c.current_company or "",
                    "location": ", ".join(location_parts) if location_parts else "",
                    "avatar_url": c.avatar_url,
                    "total_experience_years": c.years_of_experience or 0,
                    "skills": list(c.technical_skills or [])[:10],
                    "experiences": [
                        {
                            "title": e.title or "",
                            "company": e.company_name or "",
                            "start_date": e.start_date or "",
                            "end_date": e.end_date or None,
                            "duration_years": e.duration_years or 0,
                            "description": e.description or "",
                            "is_current": e.is_current or False,
                        }
                        for e in experiences
                    ],
                    "education": [
                        {
                            "institution": ed.institution or "",
                            "degree": ed.degree or "",
                            "field": ed.field_of_study or "",
                        }
                        for ed in educations
                    ],
                })

            logger.info("[SourcingAgent] DB fallback returned %d candidates for agent=%s", len(candidates), agent.id)
            return candidates
        except Exception as e:
            logger.warning("[SourcingAgent] DB fallback also failed: %s", e)
            return []

    async def _load_template_context(self, template_id: str | None, db) -> str:
        """Wave 3 sectoral wiring (audit 2026-05-21): carregar AgentTemplate
        e extrair prompt canonical do system_prompt_yaml.

        Retorna string vazia (degraded gracefully) se template ausente,
        YAML malformado, ou erro de DB. Logger.warning em qualquer falha
        para detectar drift em monitoring.
        """
        if not template_id:
            return ""
        try:
            from lia_models.agent_template import AgentTemplate
            from sqlalchemy import select
            import yaml as _yaml

            res = await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id))
            template = res.scalar_one_or_none()
            if not template or not template.system_prompt_yaml:
                return ""

            parsed = _yaml.safe_load(template.system_prompt_yaml)
            if isinstance(parsed, dict):
                prompt_text = parsed.get("prompt", "")
                if isinstance(prompt_text, str) and prompt_text.strip():
                    return prompt_text.strip()
            return ""
        except Exception as exc:
            logger.warning(
                "[SourcingAgent] template context load failed for template_id=%s: %s",
                template_id, exc,
            )
            return ""

    @staticmethod
    def _strategy_to_query(strategy: dict) -> str:
        skills = ", ".join(strategy.get("required_skills", []))
        loc = strategy.get("location", "")
        excl = strategy.get("exclusions", [])
        excl_str = f" Excluir: {', '.join(excl)}." if excl else ""
        return f"Buscar candidatos com {skills} em {loc}.{excl_str}"

    @staticmethod
    def _default_preferences() -> dict:
        return {
            "candidates_per_day": 20,
            "channels": ["internal", "linkedin"],
            "schedule": "continuous",
            "notify_frequency": "daily",
        }


sourcing_agent_orchestrator = SourcingAgentOrchestrator()
