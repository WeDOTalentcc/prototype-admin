"""BigFiveDepartmentService - Sprint B Phase 2.

Hybrid Big Five blend formula em 4 camadas:

    Layer 1 (LLM):           0.40 - sempre presente (vem do rank_traits caller)
    Layer 2 (O*NET prior):   0.20 - sempre presente
    Layer 3 (CompanyCulture): 0.15 - se CompanyCultureProfile + toggle ON
    Layer 4 (DeptHistory):   0.25 - se BigFiveDeptProfile >= 10 samples + toggle ON

Stability semantics: alto = bom (alinhado com CompanyCultureProfile.stability_score).
Multi-tenancy: company_id sempre via parametros explicitos (do JWT ao caller).
LGPD: record_hire valida whitelist OCEAN, sem PII em logs.

Fairness gate: NAO bloqueia neste estagio (P0.4 fix). adverse_impact_score real
exigiria comparacao com grupos protegidos (genero/raca/idade) que nao temos
no candidate_traits_snapshot. Strategy: emitir WARNING estruturado com TODO
explicito + bloquear apenas via fairness_audit_log batch (proxima fase).

EU AI Act Art. 13 — Transparency Disclosure (Sprint B P1 — 2026-05-10):
  The BigFive department history learning loop constitutes an automated
  decision-support system under EU AI Act Art. 6(2) (recruitment AI). The
  following transparency obligations apply:

  1. Candidates assessed must be informed that AI personality analysis
     (OCEAN traits) from their screening contributes to hiring-outcome
     learning for the company's department profile.
     Disclosure surface: candidate consent modal (LGPD Art. 20 + EU AI Act
     Art. 13(1)(f)) — managed by CandidateConsentService.

  2. Recruiters must see a notice when BigFive department history is active
     (toggle learning_loops.bigfive_department_history = true). The notice
     must include: "This recommendation is partially influenced by hiring
     patterns from previous candidates in this department."
     Disclosure surface: feature-flag toggle disclosure modal (lia_assistant_flags.py
     + frontend Configurações > Políticas de Recrutamento > Loops de Aprendizado).

  3. Right to explanation: any candidate can request via LGPD erasure endpoint
     (/api/v1/lgpd/candidate-erasure) to have their trait contribution removed.
     Current implementation: cascade FK deletion removes lia_opinions row;
     bigfive_department_profiles aggregate is marked stale for recompute
     (see lgpd_cleanup_service.run_cleanup docstring for the known gap and
     migration path).

  Implementation status: items 1+2 documented here, item 3 partially covered
  (FK cascade confirmed, aggregate recompute = Sprint B+ backlog).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.hiring_policy.repositories.hiring_policy_repository import (
    HiringPolicyRepository,
)
from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
    ALLOWED_TRAITS,
    BigFiveDepartmentProfileRepository,
)

logger = logging.getLogger(__name__)


# Thresholds
MIN_DEPT_SAMPLES = 10
TEMPORAL_DECAY_LAMBDA = 0.05
DECAY_THRESHOLD_DAYS = 548  # ~18 months

# Fairness gate threshold (informacional ate Phase 2.5; ver TODO abaixo)
FAIRNESS_THRESHOLD = 0.10


# Pesos por nivel de blend (caller deve consumir como prior weights)
WEIGHTS_4L = {"llm": 0.40, "onet": 0.20, "culture": 0.15, "dept": 0.25}
WEIGHTS_3L = {"llm": 0.40, "onet": 0.35, "culture": 0.25}


@dataclass
class BigFiveBlend:
    """Resultado de get_blend_weights.

    method: "llm_only" | "company_culture" | "dept_blend"

    Quando method=llm_only, scores ficam None (caller usa LLM raw).
    Stability semantics: 0.0-1.0, alto = estavel/bom.

    adverse_impact_score: NAO bloqueante neste estagio (Phase 2.5 follow-up).
    """
    method: str
    openness_score: float | None = None
    conscientiousness_score: float | None = None
    extraversion_score: float | None = None
    agreeableness_score: float | None = None
    stability_score: float | None = None
    adverse_impact_score: float = 0.0


class BigFiveDepartmentService:
    """Servico de blend hibrido para WSI rank_traits.

    Multi-tenancy: company_id sempre por argumento explicito.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BigFiveDepartmentProfileRepository(db)

    # -- Internal helpers (patchaveis em testes) --------------------------

    async def _get_dept_profile(
        self, company_id: str, department: str, seniority_level: str,
    ):
        try:
            return await self.repo.get_or_none(company_id, department, seniority_level)
        except SQLAlchemyError as exc:
            logger.warning(
                "[BigFiveSvc] dept profile DB error company_hash=%s: %s",
                hash(company_id) % 100000, str(exc)[:100],
            )
            return None

    async def _get_culture_profile(self, company_id: str):
        """Carrega CompanyCultureProfile da empresa, ou None."""
        try:
            from app.domains.company.repositories.culture_profile_repository import (
                CultureProfileRepository,
            )
        except ImportError:
            logger.error("[BigFiveSvc] CultureProfileRepository unavailable")
            return None

        import uuid as _uuid
        try:
            _company_uuid = (
                company_id
                if isinstance(company_id, _uuid.UUID)
                else _uuid.UUID(str(company_id))
            )
        except (ValueError, AttributeError):
            return None

        try:
            repo = CultureProfileRepository(self.db)
            # Fase 5.1 gate: only approved/human-authored culture feeds the blend.
            return await repo.get_for_agent_context(_company_uuid)
        except SQLAlchemyError as exc:
            logger.warning(
                "[BigFiveSvc] culture profile DB error: %s", str(exc)[:100],
            )
            return None

    async def _get_toggles(self, company_id: str) -> dict:
        """Carrega learning_loops toggles de CompanyHiringPolicy ou defaults.

        Delega ao helper canonical em
        ``app.shared.services.learning_loops_toggles`` (single source of
        truth desde 2026-05-21). Wrapper mantido por compat com chamadas
        ``self._get_toggles(...)`` existentes; novo código DEVE chamar
        ``load_learning_loops_toggles(...)`` direto.
        """
        from app.shared.services.learning_loops_toggles import (
            load_learning_loops_toggles,
        )
        return await load_learning_loops_toggles(company_id, self.db)

    # -- Helpers stability normalizacao ------------------------------------

    @staticmethod
    def _culture_to_unit(score: int | float | None) -> float:
        """CompanyCultureProfile usa 0-100 (Integer). Normaliza pra 0-1.

        None => 0.5 (neutro).
        """
        if score is None:
            return 0.5
        if score > 1:
            return round(min(score / 100.0, 1.0), 4)
        return float(score)

    # -- Public API --------------------------------------------------------

    async def get_blend_weights(
        self,
        company_id: str,
        department: str,
        seniority_level: str,
    ) -> BigFiveBlend:
        """Calcula blend para rank_traits().

        Returns BigFiveBlend com method indicando quais layers ativaram.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        toggles = await self._get_toggles(company_id)
        master_on = toggles.get("enabled")

        culture = None
        dept = None

        if master_on and toggles.get("bigfive_company_culture"):
            culture = await self._get_culture_profile(company_id)

        if master_on and toggles.get("bigfive_department_history"):
            dept = await self._get_dept_profile(company_id, department, seniority_level)
            if dept is not None and (dept.sample_count or 0) < MIN_DEPT_SAMPLES:
                logger.debug(
                    "[BigFiveSvc] dept profile below min_samples=%d (n=%d) - skip Layer 4",
                    MIN_DEPT_SAMPLES, dept.sample_count,
                )
                dept = None

        if dept is not None and culture is not None:
            return self._blend_4layer(culture, dept)
        if dept is not None:
            return self._blend_dept_only(dept)
        if culture is not None:
            return self._blend_culture_only(culture)
        return BigFiveBlend(method="llm_only")

    # -- Blends (stability semantics, alto=bom em ambas tabelas) ----------

    def _blend_4layer(self, culture, dept) -> BigFiveBlend:
        """Combina culture (15%) + dept (25%) como prior unico (40% peso prior).

        Caller (rank_traits) aplica os pesos LLM (40%) + O*NET (20%) por cima.
        Stability NORMALIZADA: alto = bom em ambas fontes.
        """
        scores: dict[str, float] = {}
        culture_w = WEIGHTS_4L["culture"]
        dept_w = WEIGHTS_4L["dept"]
        prior_total = culture_w + dept_w  # 0.40

        for trait in ALLOWED_TRAITS:
            c_raw = getattr(culture, f"{trait}_score", None)
            c_val = self._culture_to_unit(c_raw)
            d_val = getattr(dept, f"{trait}_score", None)
            if d_val is None:
                d_val = 0.5
            combined = (culture_w * c_val + dept_w * d_val) / prior_total
            scores[trait] = round(combined, 4)

        blend = BigFiveBlend(
            method="dept_blend",
            openness_score=scores["openness"],
            conscientiousness_score=scores["conscientiousness"],
            extraversion_score=scores["extraversion"],
            agreeableness_score=scores["agreeableness"],
            stability_score=scores["stability"],
        )
        self._fairness_warning(blend)
        return blend

    def _blend_dept_only(self, dept) -> BigFiveBlend:
        """Sem culture: dept e o unico prior (peso 25% no formula final)."""
        blend = BigFiveBlend(
            method="dept_blend",
            openness_score=getattr(dept, "openness_score", None),
            conscientiousness_score=getattr(dept, "conscientiousness_score", None),
            extraversion_score=getattr(dept, "extraversion_score", None),
            agreeableness_score=getattr(dept, "agreeableness_score", None),
            stability_score=getattr(dept, "stability_score", None),
        )
        self._fairness_warning(blend)
        return blend

    def _blend_culture_only(self, culture) -> BigFiveBlend:
        """Sem dept: culture e o unico prior (peso 25% no formula final)."""
        return BigFiveBlend(
            method="company_culture",
            openness_score=self._culture_to_unit(getattr(culture, "openness_score", None)),
            conscientiousness_score=self._culture_to_unit(getattr(culture, "conscientiousness_score", None)),
            extraversion_score=self._culture_to_unit(getattr(culture, "extraversion_score", None)),
            agreeableness_score=self._culture_to_unit(getattr(culture, "agreeableness_score", None)),
            stability_score=self._culture_to_unit(getattr(culture, "stability_score", None)),
        )

    # -- Fairness (P0.4 fix: warning honesto, sem teatro) -----------------

    def _fairness_warning(self, blend: BigFiveBlend) -> None:
        """Phase 2 fairness gate: WARNING estruturado, NAO bloqueia ainda.

        TODO Phase 2.5: implementar adverse_impact real comparando hire/reject
        distribution por grupo protegido (genero/raca/idade) usando
        fairness_audit_log (migration 015). Ate la, log apenas.

        Nao usamos blend.adverse_impact_score como gate ate ser populado por
        pipeline real - caso contrario seria security theater.
        """
        # Placeholder structured signal pra Prometheus/observability
        logger.info(
            "[BigFiveSvc:Fairness] blend produced method=%s "
            "(adverse_impact NOT YET CALCULATED - Phase 2.5 follow-up)",
            blend.method,
        )

    # -- Record hire (running average + temporal decay) -------------------

    async def record_hire(
        self,
        company_id: str,
        department: str,
        seniority_level: str,
        candidate_traits_snapshot: dict[str, Any],
    ) -> None:
        """Atualiza profile do dept apos hire confirmado.

        LGPD: snapshot deve conter APENAS keys OCEAN whitelist.
        Multi-tenancy: company_id obrigatorio.
        Temporal decay: profiles > 18m com peso reduzido (lambda 0.05).
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        # PII guard: rejeita keys que nao sejam OCEAN traits
        invalid_keys = set(candidate_traits_snapshot.keys()) - ALLOWED_TRAITS
        if invalid_keys:
            raise ValueError(
                f"candidate_traits_snapshot has invalid keys {sorted(invalid_keys)} - "
                f"only OCEAN traits allowed: {sorted(ALLOWED_TRAITS)}",
            )

        profile = await self._get_dept_profile(company_id, department, seniority_level)

        sample_weight = 1.0
        if profile is not None and profile.last_updated_at is not None:
            age_days = (datetime.utcnow() - profile.last_updated_at).days
            if age_days > DECAY_THRESHOLD_DAYS:
                months_over = (age_days - DECAY_THRESHOLD_DAYS) / 30.0
                sample_weight = math.exp(-TEMPORAL_DECAY_LAMBDA * months_over)
                logger.info(
                    "[BigFiveSvc] temporal decay age=%dd weight=%.4f",
                    age_days, sample_weight,
                )

        # Constroi trait_delta apenas com keys validas (defesa em profundidade)
        trait_delta = {
            t: float(candidate_traits_snapshot.get(t, 0.5))
            for t in ALLOWED_TRAITS
            if t in candidate_traits_snapshot
        }

        await self.repo.upsert(
            company_id=company_id,
            department=department,
            seniority_level=seniority_level,
            trait_delta=trait_delta,
            sample_weight=sample_weight,
            existing_profile=profile,  # Evita double lookup (P1.5 fix)
        )
