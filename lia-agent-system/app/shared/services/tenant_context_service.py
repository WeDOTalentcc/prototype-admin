"""
TenantContextService — contexto rico por tenant para personalização da LIA.

# CROSS-CUTTING: kept in app/shared/services because it is consumed by the central
# orchestrator (main_orchestrator.py) to inject tenant context into ALL LIA responses
# regardless of domain. It depends on company + job_vacancy data and has no single
# domain owner.
Injeta nome, setor, nível de autonomia e estado atual no contexto do orquestrador.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level cache: company_id → (TenantContext, timestamp)
# TTL=60s: tenant config changes infrequently; stale-for-60s is acceptable.
# Harness: guide=computacional (deterministic, no inference). Sensor: unit tests.
# ---------------------------------------------------------------------------
_tenant_ctx_cache: dict[str, tuple[Any, float]] = {}
_TENANT_CTX_TTL = 60.0  # seconds


def invalidate_tenant_context_cache(company_id: str) -> None:
    """Remove a single tenant entry from the cache (e.g. after config change)."""
    _tenant_ctx_cache.pop(company_id, None)


@dataclass
class TenantContext:
    company_id: str
    company_name: str
    sector: str
    open_vacancies: int
    autonomy_level: str  # "high" | "medium" | "low"
    plan: str
    # Platform awareness fields (P35-044)
    active_channels: list[str] | None = None  # ["email", "whatsapp", "teams"]
    timezone: str = "America/Sao_Paulo"
    communication_templates_count: int = 0
    ml_models_active: list[str] | None = None  # ["wsi_scoring", "time_to_fill"]
    pipeline_stages: list[str] | None = None  # ["Triagem", "Entrevista RH", "Proposta"]
    custom_persona: str | None = None  # tenant-specific LIA persona override
    lia_filtered_prompt: str = ""  # rich company context filtered by lia_field_toggles (produtor único)

    def to_prompt_snippet(self) -> str:
        parts = [
            f"Você está assistindo **{self.company_name}**, empresa do setor "
            f"**{self.sector}** com **{self.open_vacancies}** vagas abertas. "
            f"Nível de autonomia configurado: **{self.autonomy_level}**. "
            f"Plano: {self.plan}.",
        ]

        # Platform awareness: active channels
        if self.active_channels:
            channels_str = ", ".join(self.active_channels)
            parts.append(
                f"Canais de comunicação ATIVOS: {channels_str}. "
                "Só ofereça envio pelos canais listados acima."
            )
        else:
            parts.append(
                "Canais de comunicação: não configurados. "
                "Informe o recrutador que precisa configurar em Configurações."
            )

        # Timezone
        if self.timezone != "America/Sao_Paulo":
            parts.append(f"Fuso horário do tenant: {self.timezone}.")

        # Communication templates
        if self.communication_templates_count > 0:
            parts.append(
                f"Templates de comunicação disponíveis: {self.communication_templates_count}."
            )

        # ML models
        if self.ml_models_active:
            models_str = ", ".join(self.ml_models_active)
            parts.append(f"Modelos ML ativos: {models_str}.")

        # Pipeline stages of current job (if available)
        if self.pipeline_stages:
            stages_str = " → ".join(self.pipeline_stages)
            parts.append(f"Pipeline desta vaga: {stages_str}.")

        # Custom persona
        if self.custom_persona:
            parts.append(f"Persona customizada do tenant: {self.custom_persona}")

        # Produtor único: rich company context filtered by lia_field_toggles
        # (mirrors AggregatedContext.lia_filtered_prompt). Separator emitted only
        # when there IS content, so we never leave a hanging section.
        if self.lia_filtered_prompt:
            parts.append("")
            parts.append("---")
            parts.append(self.lia_filtered_prompt)

        return "\n".join(parts)


class TenantContextService:
    """Busca contexto rico do tenant para personalizar respostas da LIA."""

    async def get_context(
        self,
        company_id: str,
        db: AsyncSession,
        job_id: str | None = None,
    ) -> TenantContext:
        """Retorna contexto do tenant. Fail-safe: retorna defaults se falhar.

        Cache: module-level dict with TTL=60s. Cache key is company_id only
        (job_id contexts are NOT cached because pipeline_stages vary per job).
        Cache is bypassed when job_id is provided to preserve per-job accuracy.

        Args:
            company_id: Tenant ID.
            db: AsyncSession.
            job_id: Optional — if provided, includes pipeline stages for this job.
                    Bypasses cache when set.
        """
        # Cache hit: skip all DB queries for the common case (no job_id context)
        if not job_id:
            cached = _tenant_ctx_cache.get(company_id)
            if cached is not None:
                ctx, ts = cached
                if time.time() - ts < _TENANT_CTX_TTL:
                    logger.debug(
                        "[TenantContextService] cache hit company=%s age=%.1fs",
                        company_id, time.time() - ts,
                    )
                    return ctx

        result_ctx = await self._fetch_from_db(company_id=company_id, db=db, job_id=job_id)

        # Store in cache only for non-job_id requests (stable context)
        if not job_id:
            _tenant_ctx_cache[company_id] = (result_ctx, time.time())

        return result_ctx

    async def _fetch_from_db(
        self,
        company_id: str,
        db: AsyncSession,
        job_id: str | None = None,
    ) -> TenantContext:
        """Internal: fetch TenantContext from DB. Called by get_context on cache miss."""
        try:
            from lia_models.company import Company
            from lia_models.job_vacancy import JobVacancy

            result = await db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = result.scalar_one_or_none()

            open_count_result = await db.execute(
                select(func.count()).select_from(JobVacancy).where(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status == "open",
                )
            )
            open_vacancies = open_count_result.scalar() or 0

            # Determinar nível de autonomia via PolicyEngine
            autonomy_level = "medium"
            try:
                # Canonical path (Sprint 11 T-09 B+A combo: shim app.shared.services.policy_engine_service deletado)
                from app.domains.policy.services.policy_engine_service import PolicyEngineService
                policy_svc = PolicyEngineService()
                policy = await policy_svc.get_active_policy(company_id, db)
                if policy:
                    autonomy_level = getattr(policy, "autonomy_level", "medium")
            except Exception:
                pass

            # Detect active communication channels
            active_channels = self._detect_active_channels(company)

            # Count communication templates
            templates_count = 0
            try:
                from lia_models.communication_settings import CommunicationTemplate
                tpl_result = await db.execute(
                    select(func.count()).select_from(CommunicationTemplate).where(
                        CommunicationTemplate.company_id == company_id,
                        CommunicationTemplate.is_active == True,
                    )
                )
                templates_count = tpl_result.scalar() or 0
            except Exception:
                pass  # table may not exist yet

            # Detect ML models
            ml_models = self._detect_ml_models(company)

            # Fetch pipeline stages for the current job (if job_id provided)
            pipeline_stages = None
            if job_id:
                try:
                    from lia_models.selective_process import SelectiveProcess
                    sp_result = await db.execute(
                        select(SelectiveProcess.name)
                        .where(
                            SelectiveProcess.job_id == job_id,
                            SelectiveProcess.company_id == company_id,
                        )
                        .order_by(SelectiveProcess.position)
                    )
                    stages = [row[0] for row in sp_result.all() if row[0]]
                    if stages:
                        pipeline_stages = stages
                except Exception:
                    pass  # selective_process table may not exist

            # Custom persona from company settings
            custom_persona = None
            if company:
                custom_persona = getattr(company, "lia_persona_override", None)

            if company:
                # Produtor único: bloco rico de empresa filtrado por lia_field_toggles,
                # injetado em TODO react agent + orquestrador via to_prompt_snippet().
                # Espelha AggregatedContext.lia_filtered_prompt. Helper nunca raise.
                from app.shared.services.lia_agent_context_builder import (
                    build_company_agent_context,
                )
                lia_filtered_prompt = await build_company_agent_context(
                    company_id=company_id,
                    db=db,
                    job_context=None,  # title/department indisponíveis aqui; helper tolera None
                )
                return TenantContext(
                    company_id=company_id,
                    company_name=getattr(company, "name", "sua empresa"),
                    sector=getattr(company, "sector", "geral"),
                    open_vacancies=open_vacancies,
                    autonomy_level=autonomy_level,
                    plan=getattr(company, "plan", "standard"),
                    active_channels=active_channels,
                    timezone=getattr(company, "timezone", "America/Sao_Paulo"),
                    communication_templates_count=templates_count,
                    ml_models_active=ml_models,
                    pipeline_stages=pipeline_stages,
                    custom_persona=custom_persona,
                    lia_filtered_prompt=lia_filtered_prompt,
                )
        except Exception as exc:
            logger.debug("[TenantContextService] fallback defaults: %s", exc)

        return TenantContext(
            company_id=company_id,
            company_name="sua empresa",
            sector="geral",
            open_vacancies=0,
            autonomy_level="medium",
            plan="standard",
        )

    @staticmethod
    def build_authenticated_snippet(company_id: str) -> str:
        return (
            f"O usuário já está autenticado na plataforma (company_id={company_id}). "
            "Você NÃO precisa perguntar o nome da empresa, CNPJ ou identificação — "
            "essas informações já estão disponíveis no sistema. "
            "Prossiga diretamente com o que o recrutador precisa."
        )

    @staticmethod
    def _detect_active_channels(company) -> list[str]:
        """Detect which communication channels are configured for the tenant."""
        channels = []
        # Email is always available if company exists
        channels.append("email")
        # WhatsApp: check if Twilio is configured
        import os
        if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("ENVIRONMENT") == "production":
            channels.append("whatsapp")
        # Teams: check if Microsoft Bot is configured
        if os.getenv("MICROSOFT_APP_ID") and os.getenv("MICROSOFT_APP_PASSWORD"):
            channels.append("teams")
        return channels

    @staticmethod
    def _detect_ml_models(company) -> list[str]:
        """Detect which ML models are active for the tenant."""
        models = ["wsi_scoring"]  # always available (deterministic fallback)
        try:
            from app.shared.services.ml_feedback_service import ml_feedback_service
            if ml_feedback_service and hasattr(ml_feedback_service, "is_trained"):
                models.append("time_to_fill_prediction")
        except Exception:
            pass
        return models
