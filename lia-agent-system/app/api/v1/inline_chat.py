"""
Generic one-shot inline chat endpoint — serves text-selection, hover, and BTW queries.
"""
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from app.domains.candidates.dependencies import get_candidate_repo
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.schemas.envelope import ok_envelope
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(tags=["inline-chat"])
logger = logging.getLogger(__name__)

ContextType = Literal["text_selection", "candidate", "job", "page"]
Intent = Literal["answer", "suggest_rewrite", "defer"]


class InlineChatContextData(WeDoBaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    selected_text: Optional[str] = Field(None, max_length=2000)
    page_url: Optional[str] = Field(None, max_length=500)
    page_title: Optional[str] = Field(None, max_length=200)


class InlineChatRequest(WeDoBaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    context_type: ContextType = "page"
    context_data: InlineChatContextData = Field(default_factory=InlineChatContextData)
    intent: Intent = "answer"


@router.post("/ask")
async def inline_chat_ask(
    payload: InlineChatRequest,
    company_id: str = Depends(require_company_id),
    repo: CandidateRepository = Depends(get_candidate_repo),
):
    """Generic one-shot LLM query for the inline chat popover.

    Handles 3 surfaces: text-selection (anywhere in the platform),
    hover-on-entity (candidate/job), BTW page query.

    Multi-tenancy: company_id from JWT via require_company_id. Never from payload.
    No persistent state — each call is independent.
    """
    context_lines: list[str] = []

    if payload.context_type == "text_selection" and payload.context_data.selected_text:
        selected = payload.context_data.selected_text.strip()[:1500]
        context_lines.append(f"TRECHO SELECIONADO PELO RECRUTADOR:\n{selected}")

    elif payload.context_type == "candidate" and payload.context_data.candidate_id:
        profile = await repo.get_full_profile(payload.context_data.candidate_id, company_id)
        if profile:
            context_lines += [
                f"Nome: {profile.get('name', 'Candidato')}",
                f"Cargo: {profile.get('current_title') or 'não informado'}",
                f"Empresa: {profile.get('current_company') or 'não informada'}",
                f"Senioridade: {profile.get('seniority_level') or 'não informado'}",
                f"Experiência: {profile.get('years_of_experience', '?')} anos",
            ]
            if profile.get("lia_score"):
                context_lines.append(f"Score LIA: {profile['lia_score']}%")
            skills = profile.get("technical_skills")
            if isinstance(skills, list) and skills:
                context_lines.append(f"Skills: {', '.join(str(s) for s in skills[:8])}")

    elif payload.context_type == "job" and payload.context_data.job_id:
        context_lines.append(f"Vaga ID: {payload.context_data.job_id}")

    if payload.context_data.page_title:
        context_lines.append(f"Seção: {payload.context_data.page_title}")

    context_block = "\n".join(context_lines) if context_lines else "Nenhum contexto específico."

    if payload.intent == "suggest_rewrite" and payload.context_type == "text_selection":
        system_prompt = (
            "Você é a LIA, assistente de recrutamento da WeDOTalent.\n"
            "O recrutador selecionou um trecho e pediu uma sugestão de melhoria.\n"
            "Retorne APENAS o trecho reescrito — sem explicações, sem prefácio, sem aspas.\n"
            "Mantenha o estilo e tom do original. Aplique fairness: linguagem neutra de gênero, "
            "foco em competências, não em características pessoais.\n\n"
            f"CONTEXTO:\n{context_block}"
        )
    elif payload.intent == "defer":
        system_prompt = (
            "Você é a LIA, assistente de recrutamento da WeDOTalent.\n"
            "O recrutador fez uma solicitação de lembrete ou ação futura.\n"
            "Confirme em 1 frase curta iniciando com 'Anotado:' o que foi registrado.\n\n"
            f"CONTEXTO:\n{context_block}"
        )
    else:
        system_prompt = (
            "Você é a LIA, assistente de recrutamento da WeDOTalent.\n"
            "O recrutador fez uma pergunta rápida enquanto trabalha na plataforma.\n"
            "Responda de forma direta e objetiva, em no máximo 3 frases curtas.\n"
            "Use apenas os dados fornecidos. Se não souber, diga claramente. Não invente.\n\n"
            f"CONTEXTO:\n{context_block}"
        )

    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant
        provider = get_provider_for_tenant()
        answer = await provider.generate_with_fallback(
            prompt=payload.question,
            system=system_prompt,
            domain="inline_chat",
            operation=f"{payload.context_type}_{payload.intent}",
            company_id=company_id,
        )
    except Exception as exc:
        logger.error("inline_chat LLM call failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="LIA indisponível no momento. Tente no chat completo.",
        )

    return ok_envelope({
        "answer": answer,
        "intent": payload.intent,
        "context_type": payload.context_type,
    })
