"""
Conversational AI, job-draft management, and context-suggestions routes:
  POST /lia/conversational
  GET  /lia/job-draft/{conversation_id}
  DELETE /lia/job-draft/{conversation_id}
  GET  /lia/context-suggestions
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.dependencies.token_budget import require_token_budget
from app.services.llm import LLMService

from ._shared import (
    # data tables
    _CONTEXT_SUGGESTIONS,
    _PAGE_BADGES,
    ContextBadge,
    ContextSuggestion,
    ContextSuggestionsResponse,
    # models
    ConversationalRequest,
    ConversationalResponse,
    _job_drafts,
    logger,
)

router = APIRouter()

LIA_CAPABILITIES_PROMPT = """Você é a LIA, assistente inteligente de recrutamento da plataforma WeDoTalent.

SUAS CAPACIDADES NESTE CHAT:
1. **Criar vagas de emprego** - Guio você pelo processo completo de criação de vagas com análise inteligente
2. **Reutilizar vagas anteriores** (Fast Track) - Encontro vagas passadas similares para republicar rapidamente
3. **Analisar remuneração** - Forneço benchmarks de mercado e recomendações salariais
4. **Sugerir competências** - Recomendo skills técnicas e comportamentais baseadas no cargo
5. **Gerar descrições de vaga** - Crio JDs profissionais otimizadas

CAPACIDADES DISPONÍVEIS EM OUTROS MÓDULOS DA LIA:
- **Pipeline e Status** - Mover candidatos entre etapas, aprovar, reprovar, avançar no pipeline
- **Candidatos** - Buscar, analisar currículos, calcular score WSI, comparar candidatos
- **Entrevistas** - Agendar, reagendar, cancelar entrevistas
- **Comunicação** - Enviar e-mails, feedback, WhatsApp para candidatos
- **Relatórios** - KPIs, funil de conversão, gargalos, previsões

IMPORTANTE:
- Este chat é otimizado para criação e gestão de vagas
- Se o usuário pedir algo de outro módulo (como mover candidato, alterar status, agendar entrevista), informe que a funcionalidade existe na plataforma e oriente a usar o chat principal da LIA para essas ações
- Nunca diga que a LIA "não possui" ou "não tem" funcionalidades de pipeline, status ou gestão de candidatos — essas capacidades existem em outros módulos

INSTRUÇÕES:
- Responda sempre em português brasileiro
- Seja natural e conversacional, não robótica
- Se o usuário perguntar algo fora do escopo deste chat, explique que a funcionalidade existe e oriente sobre como acessá-la
- Se for uma saudação ou conversa casual, responda de forma amigável e redirecione para ajudar com vagas
- Mantenha respostas concisas mas úteis

Mensagem do usuário: {message}

Responda de forma natural e útil:"""


@router.post("/conversational", response_model=ConversationalResponse)
async def handle_conversational_message(
    request: ConversationalRequest,
    _budget: None = Depends(require_token_budget),
):
    """
    Handle general conversational messages using LLM for natural responses.

    This endpoint enables LIA to have real conversations, understanding
    questions about capabilities and responding intelligently.
    """
    try:
        # Mode: salary_benchmark — use structured salary analysis (fix C-06)
        if request.mode == "salary_benchmark":
            salary_prompt = f"""Você é especialista em remuneração do mercado brasileiro de tecnologia.
Forneça uma análise completa de faixa salarial para a seguinte solicitação.

REGRAS OBRIGATÓRIAS:
1. Sempre inclua valores em Reais no formato R$ XX.XXX (ponto como separador de milhar)
2. Estruture a resposta com:
   - Faixa mínima: R$ X.XXX
   - Mediana: R$ X.XXX
   - Faixa máxima: R$ X.XXX
   - Recomendação: R$ X.XXX - R$ X.XXX mensais (CLT)
3. Considere senioridade, localização e mercado brasileiro 2025
4. Responda em Português do Brasil

Solicitação: {request.message}"""

            llm_svc = LLMService()
            response_text = await llm_svc.generate(salary_prompt, provider="gemini")
            return ConversationalResponse(
                response=response_text,
                understood_intent="salary_benchmark",
                suggested_action=None,
                can_help=True
            )

        llm_svc = LLMService()
        prompt = LIA_CAPABILITIES_PROMPT.format(message=request.message)
        response_text = await llm_svc.generate(prompt, provider="gemini")

        lower_msg = request.message.lower()

        if any(word in lower_msg for word in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hello']):
            intent = "greeting"
        elif '?' in request.message or any(word in lower_msg for word in ['como', 'o que', 'pode', 'consegue', 'faz', 'ajuda']):
            intent = "question"
        elif any(word in lower_msg for word in ['criar', 'nova vaga', 'do zero', 'começar']):
            intent = "create_job"
        elif any(word in lower_msg for word in ['reutilizar', 'anterior', 'fast track', 'aproveitar']):
            intent = "fast_track"
        else:
            intent = "other"

        suggested_action = None
        if intent == "create_job":
            suggested_action = "from_scratch"
        elif intent == "fast_track":
            suggested_action = "fast_track"

        return ConversationalResponse(
            response=response_text,
            understood_intent=intent,
            suggested_action=suggested_action,
            can_help=True
        )

    except Exception as e:
        logger.error(f"Error in conversational response: {e}")
        return ConversationalResponse(
            response="Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
            understood_intent="fallback",
            can_help=True
        )


@router.get("/job-draft/{conversation_id}", response_model=None)
async def get_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo)
) -> dict[str, Any]:
    """Get the current job draft for a conversation."""
    if conversation_id in _job_drafts:
        return {
            "success": True,
            "job_draft": _job_drafts[conversation_id]
        }
    return {
        "success": False,
        "message": "Job draft not found",
        "job_draft": None
    }


@router.delete("/job-draft/{conversation_id}", response_model=None)
async def clear_job_draft(
    conversation_id: str,
    current_user: User = Depends(get_current_user_or_demo)
) -> dict[str, Any]:
    """Clear a job draft from memory."""
    if conversation_id in _job_drafts:
        del _job_drafts[conversation_id]
        return {"success": True, "message": "Job draft cleared"}
    return {"success": False, "message": "Job draft not found"}


@router.get("/context-suggestions", response_model=ContextSuggestionsResponse)
async def get_context_suggestions(
    page: str = Query(..., description="Page context: home|vaga|candidato|pipeline|triagem|relatorios|configuracoes"),
    entity_id: str | None = Query(None, description="ID of the current entity (job or candidate)"),
    entity_name: str | None = Query(None, description="Display name of the current entity"),
    limit: int = Query(default=5, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Returns a context badge + proactive suggestion chips for the current page.
    Mirrors the Notion AI pattern: badge shows where you are, chips offer smart actions.
    """
    page_key = page.lower().strip()

    badge_config = _PAGE_BADGES.get(page_key, _PAGE_BADGES["home"])
    badge_label = badge_config["label"]
    if entity_name:
        badge_label = f"{badge_config['label']}: {entity_name}"

    context_badge = ContextBadge(
        label=badge_label,
        icon=badge_config["icon"],
        color=badge_config["color"],
        description=f"Contexto: {badge_config['label'].lower()}",
    )

    raw_suggestions = _CONTEXT_SUGGESTIONS.get(page_key, _CONTEXT_SUGGESTIONS["home"])

    personalized: list[ContextSuggestion] = []
    for s in raw_suggestions[:limit]:
        prompt = s["prompt"]
        if entity_name and page_key in ("vaga", "candidato"):
            prompt = f"{prompt} (referindo-se a: {entity_name}" + (f", ID: {entity_id}" if entity_id else "") + ")"
        personalized.append(ContextSuggestion(
            id=s["id"],
            label=s["label"],
            prompt=prompt,
            icon=s.get("icon"),
            category=s.get("category", "action"),
        ))

    return ContextSuggestionsResponse(
        context_badge=context_badge,
        suggestions=personalized,
        page=page_key,
        entity_id=entity_id,
        generated_at=datetime.utcnow().isoformat(),
    )
