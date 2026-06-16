"""
Glossary lookup endpoints — surface canonical term definitions in the chat UI.

Powers the `/definir <termo>` chat slash command and any tooltip that needs the
official meaning of WSI, BARS, Bloom, etc. Reads from
`docs/GLOSSARY.md` via `glossary_loader.get_term`, so the API never drifts from
the documentation source of truth.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.shared.prompts.glossary_loader import (
    CANONICAL_PROMPT_TERMS,
    GlossaryEntry,
    get_glossary,
    get_term,
)
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

router = APIRouter()


def _serialize(entry: GlossaryEntry) -> dict:
    return {
        "name": entry.name,
        "sigla": entry.sigla,
        "definition": entry.definition,
        "category": entry.category,
    }


@router.get(
    "/terms",
    summary="List canonical glossary terms",
    tags=["glossary"],
)
async def list_terms(company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Return the canonical prompt terms that have a definition available."""
    glossary = get_glossary()
    available: list[dict] = []
    for key in CANONICAL_PROMPT_TERMS:
        entry = get_term(key)
        if entry is not None:
            available.append(_serialize(entry))
    return {
        "success": True,
        "data": {
            "terms": available,
            "total_loaded": len(glossary),
        },
    }


@router.get(
    "/terms/{term}",
    summary="Lookup a glossary entry by name",
    tags=["glossary"],
)
async def get_term_definition(term: str, company_id: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Return the canonical definition for ``term`` (tolerant to case/accent)."""
    cleaned = term.strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="term must not be empty")
    entry = get_term(cleaned)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Termo '{cleaned}' não encontrado no glossário canônico.",
        )
    return {"success": True, "data": _serialize(entry)}
