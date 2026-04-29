"""
PreConditionChecker — D10 Proactive Contextual Assistance.

Detects missing pre-conditions that block or degrade the recruiter's workflow
and surfaces them as ProactiveHints so the orchestrator can:
  - navigate the user to the right settings page
  - offer to auto-fix (ask permission first)
  - include a proactive suggestion in LIA's response

Checks run BEFORE the LLM is invoked. They are fail-open — a check that
crashes does not block the request.

D2 expanded (8 checks total):
  1. missing_company_id
  2. incomplete_company_profile (basic fields)
  3. vacancy_no_screening_questions
  4. company_website_missing (→ offers auto-scrape)
  5. culture_profile_missing (→ offers culture analysis)
  6. benefits_catalog_empty (→ offers import)
  7. hiring_policy_missing (→ offers suggest_recruiting_policy)
  8. candidates_missing_contact (→ offers batch enrich_candidate_linkedin)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# P3#9 — in-memory cache with 5-minute TTL to reduce DB load
# Keyed by (company_id, intent). Avoid running 7 queries per chat message.
import time as _time_mod
_CHECKER_CACHE: dict[str, tuple[list, float]] = {}
_CHECKER_TTL = 300.0  # 5 minutes


def _cache_key(ctx) -> str:
    return f"{getattr(ctx, 'company_id', '') or ''}:{(getattr(ctx, 'intent', '') or '').lower()}"


def clear_precondition_cache() -> None:
    """Manual eviction (useful for tests + admin triggers)."""
    _CHECKER_CACHE.clear()


@dataclass
class ProactiveHint:
    """A hint surfaced to the LIA orchestrator for proactive assistance."""

    type: str
    message: str
    action: str | None = None
    severity: str = "info"  # "info" | "warning" | "critical"
    metadata: dict[str, Any] = field(default_factory=dict)


class PreConditionChecker:
    """Runs pre-condition checks and returns a list of ProactiveHints."""

    async def check(self, ctx: Any) -> list[ProactiveHint]:
        """
        Run all checks against the orchestration context. Always returns a
        list; individual failures are logged and do not propagate.

        P3#9 — Results cached 5 min per (company_id, intent) to reduce DB load
        (7 queries → 1 query amortized).
        """
        _key = _cache_key(ctx)
        _now = _time_mod.monotonic()
        _cached = _CHECKER_CACHE.get(_key)
        if _cached and (_now - _cached[1]) < _CHECKER_TTL:
            return list(_cached[0])

        hints: list[ProactiveHint] = []

        # --- Check 1: company_id empty/missing ---
        try:
            company_id = getattr(ctx, "company_id", None) or ""
            if not company_id:
                hints.append(ProactiveHint(
                    type="missing_company_id",
                    message=(
                        "Notei que seu perfil de empresa ainda nao esta configurado. "
                        "Isso limita buscas de candidatos e triagens. "
                        "Quer que eu te leve ate Configuracoes agora?"
                    ),
                    action="navigate_to_settings",
                    severity="warning",
                    metadata={"target_page": "settings"},
                ))
                # If no company_id, skip DB-backed checks
                return hints
        except Exception as exc:
            logger.debug("[PreConditionChecker] company_id check failed: %s", exc)
            return hints

        company_id = ctx.company_id

        # --- Check 2: company profile incomplete (basic fields) ---
        try:
            missing_fields = await self._check_company_profile_completeness(company_id)
            if missing_fields:
                hints.append(ProactiveHint(
                    type="incomplete_company_profile",
                    message=(
                        f"Seu perfil de empresa esta incompleto (faltam: {', '.join(missing_fields)}). "
                        "Isso reduz a precisao das recomendacoes. "
                        "Posso te ajudar a completar em Configuracoes."
                    ),
                    action="navigate_to_settings",
                    severity="info",
                    metadata={"target_page": "settings", "missing_fields": missing_fields},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] profile completeness check failed: %s", exc)

        # --- Check 3: intent=screening but vacancy has no screening questions ---
        try:
            intent = (getattr(ctx, "intent", "") or "").lower()
            if intent in ("screening", "wsi", "tria", "triagem"):
                vacancy_id = getattr(ctx, "vacancy_id", None) or getattr(ctx, "job_id", None)
                if vacancy_id and await self._vacancy_has_no_questions(company_id, vacancy_id):
                    hints.append(ProactiveHint(
                        type="vacancy_no_screening_questions",
                        message=(
                            "Essa vaga nao tem perguntas de triagem cadastradas. "
                            "Posso sugerir um conjunto de perguntas baseado na descricao da vaga?"
                        ),
                        action="suggest_screening_questions",
                        severity="warning",
                        metadata={"vacancy_id": str(vacancy_id)},
                    ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] screening precondition check failed: %s", exc)

        # --- Check 4 (D2 NEW): company_website_missing — offer auto-scrape ---
        try:
            website = await self._get_company_website(company_id)
            if not website:
                hints.append(ProactiveHint(
                    type="company_website_missing",
                    message=(
                        "Nao vi o site da sua empresa cadastrado. Se voce me passar a URL, "
                        "consigo preencher automaticamente varios campos (nome, setor, cultura, beneficios) "
                        "via analyze_company_website (scraping inteligente)."
                    ),
                    action="request_website_and_scrape",
                    severity="info",
                    metadata={"next_tool": "analyze_company_website"},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] website check failed: %s", exc)

        # --- Check 5 (D2 NEW): culture_profile_missing ---
        try:
            if await self._culture_profile_missing(company_id):
                hints.append(ProactiveHint(
                    type="culture_profile_missing",
                    message=(
                        "Sua empresa ainda nao tem perfil cultural cadastrado "
                        "(missao, visao, valores, modelo de trabalho). "
                        "Isso ajuda a LIA a fazer match cultural nas triagens. "
                        "Posso te guiar por 5 perguntas rapidas ou analisar via website."
                    ),
                    action="culture_onboarding",
                    severity="info",
                    metadata={},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] culture check failed: %s", exc)

        # --- Check 6 (D2 NEW): benefits_catalog_empty ---
        try:
            if await self._benefits_catalog_empty(company_id):
                hints.append(ProactiveHint(
                    type="benefits_catalog_empty",
                    message=(
                        "Catalogo de beneficios vazio. Beneficios completos ajudam na atracao "
                        "de candidatos. Posso importar de uma lista que voce tem ou te guiar na "
                        "criacao. Categorias sugeridas: Saude, Alimentacao, Transporte, Educacao."
                    ),
                    action="navigate_to_benefits_import",
                    severity="info",
                    metadata={"next_tool": "import_benefits_from_data", "target_page": "settings", "subsection": "benefits-import"},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] benefits check failed: %s", exc)

        # --- Check 7 (D2 NEW): hiring_policy_missing ---
        try:
            if await self._hiring_policy_missing(company_id):
                hints.append(ProactiveHint(
                    type="hiring_policy_missing",
                    message=(
                        "Sua empresa nao tem politica de recrutamento formalizada. "
                        "Posso sugerir uma baseline apropriada ao seu setor e tamanho, "
                        "ja validada por fairness guard (zero discriminacao)."
                    ),
                    action="suggest_recruiting_policy",
                    severity="info",
                    metadata={"next_tool": "suggest_recruiting_policy"},
                ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] hiring policy check failed: %s", exc)

        # --- Check 8 (D2 NEW): candidates_missing_contact ---
        # Only run this check if intent suggests outreach/pipeline activity
        try:
            intent = (getattr(ctx, "intent", "") or "").lower()
            outreach_intents = ("sourcing", "outreach", "contact", "contato", "enviar", "mensagem")
            if any(kw in intent for kw in outreach_intents):
                count = await self._candidates_without_contact_count(company_id)
                if count >= 3:
                    hints.append(ProactiveHint(
                        type="candidates_missing_contact",
                        message=(
                            f"Vi que {count} candidatos no seu pipeline estao sem email/telefone. "
                            "Isso bloqueia outreach. Posso enriquecer em batch via LinkedIn "
                            "(Apify). Custo rastreado por tenant."
                        ),
                        action="batch_enrich_contacts",
                        severity="warning",
                        metadata={"count": count, "next_tool": "enrich_candidate_linkedin"},
                    ))
        except Exception as exc:
            logger.debug("[PreConditionChecker] candidates contact check failed: %s", exc)

        # P3#9 cache result
        _CHECKER_CACHE[_key] = (list(hints), _now)
        return hints

    # ═══════════════════════════════════════════════════════════════
    # DB helpers — all fail-open (return benign defaults on error)
    # ═══════════════════════════════════════════════════════════════

    async def _check_company_profile_completeness(self, company_id: str) -> list[str]:
        """Return list of missing canonical fields in the company profile. Empty if complete.

        Uses canonical `company_profiles` table (schema: CompanyProfile model).
        Matches fields with D1 `check_company_completeness` tool for consistency.

        Note: `website` is intentionally NOT part of this check. It has its own
        dedicated hint (`company_website_missing` — Check 4 below) which doubles
        as the trigger for the `analyze_company_website` offer (see contract
        `docs/governance/tenant-minimum-config.md` §5.1). Including it here
        would surface the same gap twice on every onboarding chat.
        """
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                # Match by id OR client_account_id — token semantics vary across call paths
                row = (await session.execute(
                    text(
                        "SELECT name, industry, company_size "
                        "FROM company_profiles "
                        "WHERE id::text = :cid OR client_account_id::text = :cid "
                        "LIMIT 1"
                    ),
                    {"cid": company_id},
                )).first()
                if row is None:
                    return ["nome", "setor", "tamanho"]
                missing: list[str] = []
                if not row[0]:
                    missing.append("nome")
                if not row[1]:
                    missing.append("setor")
                if not row[2]:
                    missing.append("tamanho")
                return missing
        except Exception as exc:
            logger.debug("[PreConditionChecker] profile read failed: %s", exc)
            return []

    async def _vacancy_has_no_questions(self, company_id: str, vacancy_id: str) -> bool:
        """Return True if the vacancy has zero screening questions configured."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                result = (await session.execute(
                    text(
                        "SELECT COUNT(*) FROM screening_questions "
                        "WHERE vacancy_id = :vid AND company_id = :cid"
                    ),
                    {"vid": str(vacancy_id), "cid": company_id},
                )).scalar()
                return (result or 0) == 0
        except Exception as exc:
            logger.debug("[PreConditionChecker] vacancy question check failed: %s", exc)
            return False

    async def _get_company_website(self, company_id: str) -> str | None:
        """Return the company's website URL, or None if not set.

        Uses canonical company_profiles table. Matches by id OR client_account_id
        to handle both tenant token semantics.
        """
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                row = (await session.execute(
                    text(
                        "SELECT website FROM company_profiles "
                        "WHERE id::text = :cid OR client_account_id::text = :cid "
                        "LIMIT 1"
                    ),
                    {"cid": company_id},
                )).first()
                return row[0] if row and row[0] else None
        except Exception as exc:
            logger.debug("[PreConditionChecker] website read failed: %s", exc)
            return None

    async def _culture_profile_missing(self, company_id: str) -> bool:
        """True if company_culture_profiles has no record for this tenant."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                count = (await session.execute(
                    text("SELECT COUNT(*) FROM company_culture_profiles WHERE company_id::text = :cid"),
                    {"cid": company_id},
                )).scalar()
                return (count or 0) == 0
        except Exception as exc:
            logger.debug("[PreConditionChecker] culture check failed: %s", exc)
            return False

    async def _benefits_catalog_empty(self, company_id: str) -> bool:
        """True if company_benefits has no active record for this tenant."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                count = (await session.execute(
                    text(
                        "SELECT COUNT(*) FROM company_benefits "
                        "WHERE company_id::text = :cid AND is_active = true"
                    ),
                    {"cid": company_id},
                )).scalar()
                return (count or 0) == 0
        except Exception as exc:
            logger.debug("[PreConditionChecker] benefits check failed: %s", exc)
            return False

    async def _hiring_policy_missing(self, company_id: str) -> bool:
        """True if company_hiring_policies has no record for this tenant."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                count = (await session.execute(
                    text("SELECT COUNT(*) FROM company_hiring_policies WHERE company_id::text = :cid"),
                    {"cid": company_id},
                )).scalar()
                return (count or 0) == 0
        except Exception as exc:
            logger.debug("[PreConditionChecker] hiring policy check failed: %s", exc)
            return False

    async def _candidates_without_contact_count(self, company_id: str) -> int:
        """Count candidates in active pipeline without email or phone."""
        try:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                count = (await session.execute(
                    text(
                        "SELECT COUNT(*) FROM candidates "
                        "WHERE company_id::text = :cid "
                        "  AND (email IS NULL OR email = '') "
                        "  AND (phone IS NULL OR phone = '') "
                        "  AND status NOT IN ('rejected', 'archived', 'hired')"
                    ),
                    {"cid": company_id},
                )).scalar()
                return int(count or 0)
        except Exception as exc:
            logger.debug("[PreConditionChecker] candidates contact check failed: %s", exc)
            return 0


# Module-level singleton
precondition_checker = PreConditionChecker()
