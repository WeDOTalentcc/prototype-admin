"""Fase 4 — persist Pearch profiles on search (snapshot de crédito zero).

Módulo isolado: nunca importado em hot path síncrono; chamado via
asyncio.create_task (fire-and-forget) em search.py.

LGPD Art. 7 IX — base legal: interesse legítimo recrutamento.
company_id sempre do JWT (multi-tenancy). RLS já ativo em
external_candidate_profiles (4 policies, migration 222+).
TTL 180 dias não-engajados: lgpd_cleanup_service.py.
Erasure cascade Art. 18: data_subject_repository.py.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import sqlalchemy as sa

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_SUPPRESSION_TIMEOUT_S = 2.0
_SUPPRESSION_LIMIT = 500   # max docids enviados ao Pearch por busca
_PERSIST_TIMEOUT_S = 10.0


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalize(name: str | None) -> str | None:
    """Normalização leve de nome (sem acentos, minúsculas) — evitar import circular."""
    if not name:
        return None
    import unicodedata
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()
    return n or None


def _profile_to_row(
    profile: Any,
    company_id: str,
    search_fingerprint: str,
    search_query: str,
) -> dict | None:
    """Mapeia CandidateProfile → dict de upsert para external_candidate_profiles.

    gender/estimated_age NÃO são armazenados no raw_payload exposto —
    evita vazar PII sensível inferenciais via snapshot endpoint.
    raw_payload = {} (deliberadamente vazio; campos estruturados bastam para UI).

    Retorna None se docid ausente (sem source_profile_id → upsert impossível).
    """
    docid = getattr(profile, "docid", None)
    if not docid:
        return None

    # Location: "City, State, Country" ou string livre
    loc_parts = [(getattr(profile, "location", None) or "").split(",")]
    loc_raw = getattr(profile, "location", None)
    loc_city = loc_parts[0][0].strip() if loc_parts[0] else None
    loc_state = loc_parts[0][1].strip() if len(loc_parts[0]) > 1 else None
    loc_country = loc_parts[0][2].strip() if len(loc_parts[0]) > 2 else None

    # Name normalization
    full_name = getattr(profile, "name", None) or ""
    first_name = getattr(profile, "first_name", None)
    last_name = getattr(profile, "last_name", None)
    if not first_name and full_name:
        parts = full_name.split(" ", 1)
        first_name = parts[0] if parts else None
        last_name = parts[1] if len(parts) > 1 else None

    # LinkedIn URL
    slug = getattr(profile, "linkedin_slug", None)
    linkedin_url = f"https://www.linkedin.com/in/{slug}" if slug else None

    # Contact
    emails = getattr(profile, "emails", []) or []
    phones = getattr(profile, "phone_numbers", []) or []
    email = emails[0] if emails else None
    phone = phones[0] if phones else None

    # Experiences snapshot (campos canônicos, sem company_info aninhado)
    exp_snapshot = []
    for exp in getattr(profile, "experiences", []) or []:
        exp_snapshot.append({
            "company_name": getattr(exp, "company", None),
            "title": getattr(exp, "title", None),
            "start_date": getattr(exp, "start_date", None),
            "end_date": getattr(exp, "end_date", None),
            "duration_years": getattr(exp, "duration_years", None),
            "description": getattr(exp, "description", None),
            "location": getattr(exp, "location", None),
            "industries": getattr(exp, "industries", []) or [],
            "company_size": getattr(exp, "company_size", None),
        })

    # Education snapshot
    edu_snapshot = []
    for edu in getattr(profile, "education", []) or []:
        if hasattr(edu, "model_dump"):
            edu_snapshot.append(edu.model_dump())
        elif hasattr(edu, "__dict__"):
            edu_snapshot.append({k: v for k, v in edu.__dict__.items() if not k.startswith("_")})

    # Languages
    langs_raw = getattr(profile, "languages", []) or []
    langs = {"items": [{"language": getattr(l, "language", str(l)), "proficiency": getattr(l, "proficiency", None)} for l in langs_raw]}

    skills = (getattr(profile, "skills", []) or [])[:50]
    expertise = (getattr(profile, "expertise", []) or [])[:20]
    yoe = getattr(profile, "total_experience_years", None)

    return {
        "company_id": company_id,
        "source": "pearch",
        "source_profile_id": docid,
        "linkedin_url": linkedin_url,
        "raw_payload": {},
        "name": full_name or docid,
        "normalized_name": _normalize(full_name),
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "avatar_url": getattr(profile, "picture_url", None),
        "headline": getattr(profile, "headline", None),
        "summary": getattr(profile, "summary", None),
        "current_title": getattr(profile, "current_title", None) or getattr(profile, "title", None),
        "current_company": getattr(profile, "current_company", None),
        "location_city": loc_city,
        "location_state": loc_state,
        "location_country": loc_country,
        "location_raw": loc_raw,
        "years_of_experience": int(yoe) if yoe is not None else None,
        "skills": skills,
        "expertise": expertise,
        "languages": langs,
        "experiences_snapshot": exp_snapshot,
        "education_snapshot": edu_snapshot,
        "is_open_to_work": getattr(profile, "is_opentowork", None),
        "is_decision_maker": bool(getattr(profile, "is_decision_maker", None)),
        "is_top_universities": getattr(profile, "is_top_universities", None),
        "has_email": bool(email),
        "has_phone": bool(phone),
        "contact_revealed": bool(email or phone),
        "best_personal_email": getattr(profile, "best_personal_email", None),
        "best_business_email": getattr(profile, "best_business_email", None),
        "personal_emails": list(getattr(profile, "personal_emails", []) or []),
        "business_emails": list(getattr(profile, "business_emails", []) or []),
        "status": "discovered",
        "search_query": search_query,
        "search_fingerprint": search_fingerprint,
    }


# ── Persist (fire-and-forget) ─────────────────────────────────────────────────

async def _persist_pearch_profiles_best_effort(
    profiles: list,
    company_id: str,
    search_fingerprint: str,
    search_query: str,
) -> None:
    """Upsert de perfis Pearch em external_candidate_profiles.

    Chamado via asyncio.create_task — fire-and-forget, nunca propaga exceção.
    Cria sessão própria (não usa a sessão do request já encerrada).
    RLS configurado explicitamente com company_id do parâmetro (JWT-sourced).

    LGPD Art. 7 IX: interesse legítimo recrutamento. Restrição à empresa
    recrutadora garantida por company_id + RLS. TTL 180 dias em cleanup.
    Upsert ON CONFLICT (uq_external_source_profile): idempotente.
    """
    if not profiles:
        return

    try:
        rows = []
        for p in profiles:
            row = _profile_to_row(p, company_id, search_fingerprint, search_query)
            if row:
                rows.append(row)

        if not rows:
            logger.debug("[persist_pearch] zero valid rows (all missing docid), skip")
            return

        from lia_config.database import async_session_factory
        from lia_models.candidate import ExternalCandidateProfile
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        async with async_session_factory() as db:
            try:
                # RLS setup explícito — ContextVar do request pode estar limpo
                await db.execute(sa.text("SET ROLE lia_app"))
                await db.execute(
                    sa.text("SELECT set_config('app.company_id', :cid, true)"),
                    {"cid": company_id},
                )
                stmt = pg_insert(ExternalCandidateProfile).values(rows)
                upsert = stmt.on_conflict_do_update(
                    constraint="uq_external_source_profile",
                    set_={
                        # Sempre atualiza fingerprint (pode ser de busca mais recente)
                        "search_fingerprint": stmt.excluded.search_fingerprint,
                        "updated_at": sa.func.now(),
                        # Enriquece somente se campo estava vazio (não sobrescreve import manual)
                        "headline": sa.case(
                            (ExternalCandidateProfile.headline.is_(None), stmt.excluded.headline),
                            else_=ExternalCandidateProfile.headline,
                        ),
                        "skills": sa.case(
                            (ExternalCandidateProfile.skills == sa.cast(sa.literal("{}"), sa.ARRAY(sa.String)), stmt.excluded.skills),
                            else_=ExternalCandidateProfile.skills,
                        ),
                    },
                )
                await db.execute(upsert)
                await db.commit()
                logger.info(
                    "[persist_pearch] upserted %d profiles cid=%.8s fp=%.12s",
                    len(rows), company_id, search_fingerprint,
                )
            except Exception as exc:
                await db.rollback()
                raise
    except Exception as exc:
        logger.warning("[persist_pearch] best-effort failed (non-blocking): %.200s", exc)


# ── Suppression ───────────────────────────────────────────────────────────────

async def get_suppression_docids(
    db: "AsyncSession",
    company_id: str,
) -> List[str]:
    """Docids Pearch já conhecidos pela empresa → passados ao docid_blacklist.

    Economiza crédito Pearch ao excluir perfis já armazenados em buscas anteriores.
    Best-effort: timeout 2s; retorna [] em falha (busca continua normalmente).

    RLS da sessão do request já isola por company automaticamente.
    company_id adicionado como filtro explícito para defense-in-depth.
    """
    try:
        from lia_models.candidate import ExternalCandidateProfile

        result = await asyncio.wait_for(
            db.execute(
                sa.select(ExternalCandidateProfile.source_profile_id)
                .where(
                    sa.and_(
                        ExternalCandidateProfile.source == "pearch",
                        ExternalCandidateProfile.status != "promoted",
                        ExternalCandidateProfile.company_id == company_id,
                    )
                )
                .limit(_SUPPRESSION_LIMIT)
            ),
            timeout=_SUPPRESSION_TIMEOUT_S,
        )
        docids = [row[0] for row in result.fetchall() if row[0]]
        logger.debug("[persist_pearch] suppression: %d known docids cid=%.8s", len(docids), company_id)
        return docids
    except Exception as exc:
        logger.debug("[persist_pearch] suppression query failed (fail-open): %.200s", exc)
        return []
