"""
One-shot LLM question about a specific candidate — used by the hover popover.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from app.domains.candidates.dependencies import get_candidate_repo
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.schemas.envelope import ok_envelope
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class CandidateQuickAskRequest(WeDoBaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    job_id: Optional[str] = None


@router.post("/{candidate_id}/quick-ask")
async def quick_ask_about_candidate(
    candidate_id: str,
    payload: CandidateQuickAskRequest,
    company_id: str = Depends(require_company_id),
    repo: CandidateRepository = Depends(get_candidate_repo),
):
    """One-shot LLM question about a candidate — drives the hover mini-chat popover.

    Multi-tenancy: company_id from JWT (require_company_id). Never from payload.
    No persistent state — each call is independent.
    """
    profile = await repo.get_full_profile(candidate_id, company_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")

    name = profile.get("name", "Candidato")

    context_lines = [
        f"Nome: {name}",
        f"Cargo atual: {profile.get('current_title') or 'não informado'}",
        f"Empresa atual: {profile.get('current_company') or 'não informada'}",
        f"Senioridade: {profile.get('seniority_level') or 'não informado'}",
        f"Experiência: {profile.get('years_of_experience') or '?'} anos",
    ]

    if profile.get("lia_score"):
        context_lines.append(f"Score LIA: {profile['lia_score']}%")

    if profile.get("technical_skills"):
        skills = profile["technical_skills"]
        if isinstance(skills, list) and skills:
            context_lines.append(f"Skills: {', '.join(str(s) for s in skills[:8])}")

    if profile.get("location_city"):
        loc = profile["location_city"]
        if profile.get("location_state"):
            loc += f", {profile['location_state']}"
        context_lines.append(f"Localização: {loc}")

    if profile.get("self_introduction"):
        intro = str(profile["self_introduction"])[:300]
        context_lines.append(f"Apresentação: {intro}")

    candidate_context = "\n".join(context_lines)

    system_prompt = (
        "Você é a LIA, assistente de recrutamento da WeDOTalent.\n"
        "O recrutador fez uma pergunta rápida sobre o candidato abaixo.\n"
        "Responda de forma direta e objetiva, em no máximo 3 frases curtas.\n"
        "Use apenas os dados fornecidos. Se não souber, diga claramente.\n"
        "Não invente informações.\n\n"
        f"DADOS DO CANDIDATO:\n{candidate_context}"
    )

    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant

        provider = get_provider_for_tenant()
        answer = await provider.generate_with_fallback(
            prompt=payload.question,
            system=system_prompt,
            domain="quick_ask",
            operation="candidate_hover_popover",
            company_id=company_id,
        )
    except Exception as exc:
        logger.error("quick_ask LLM call failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="LIA indisponível no momento. Tente no chat completo.")

    return ok_envelope({"answer": answer, "candidate_name": name})
