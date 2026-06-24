"""
Shared constants, helpers, and prompts for triagem_session_service sub-modules.
"""
import base64
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level cache for event dispatcher (lazy init to avoid circular imports)
# ---------------------------------------------------------------------------
_event_dispatcher_cache = None


def _get_event_dispatcher():
    global _event_dispatcher_cache
    if _event_dispatcher_cache is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher_cache = event_dispatcher
    return _event_dispatcher_cache


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WELCOME_MESSAGE = (
    "Vou conduzir sua triagem para a vaga de {job_title} na {company_name}. "
    "A conversa tem {total_blocks} etapas e dura aproximadamente 15-20 minutos. "
    "Você pode responder por texto ou gravar áudio. Vamos começar?"
)

COMPLETION_MESSAGE = (
    "**Triagem concluída com sucesso.**\n\n"
    "Obrigada, {candidate_name}. Suas respostas foram registradas.\n\n"
    "**Próximos passos:**\n"
    "- Você receberá um e-mail de confirmação em instantes\n"
    "- A equipe da {company_name} avaliará seu perfil nos próximos dias\n"
    "- Fique atento ao seu e-mail para atualizações\n\n"
    "Agradecemos sua participação e desejamos sucesso."
)

COMPLETION_NEXT_STEPS = [
    "Você receberá um e-mail de confirmação em instantes",
    "A equipe da {company_name} avaliará seu perfil nos próximos dias",
    "Fique atento ao seu e-mail para atualizações",
]

BLOCK_TRANSITION_MESSAGES = [
    "Certo. Vamos para a próxima etapa: **{block_name}**.",
    "Entendido. Agora vamos falar sobre **{block_name}**.",
    "Obrigada. Seguindo para **{block_name}**.",
    "Anotado. Próxima etapa: **{block_name}**.",
]

PRE_COMPLETION_MESSAGE = (
    "Chegamos ao final da triagem.\n\n"
    "Foram **{total_questions} perguntas** respondidas em **{duration_minutes} minutos**.\n\n"
    "Deseja revisar alguma resposta antes de finalizar?"
)

MAX_CONSECUTIVE_OFF_SCRIPT = 3

OFF_SCRIPT_SYSTEM_PROMPT = """Assistente de recrutamento da empresa {company_name}.
Está conduzindo uma triagem para a vaga de {job_title}.

O candidato fez uma pergunta fora do roteiro em vez de responder à pergunta da triagem.
Responda a pergunta do candidato de forma breve e profissional, usando o contexto da vaga e empresa.
Depois, retome o roteiro naturalmente, reapresentando a pergunta original.

Pergunta original da triagem: {original_question}
Pergunta/comentário do candidato: {candidate_message}
Bloco atual: {block_name}

Responda em português brasileiro. Seja acolhedora e profissional.
Limite sua resposta a 3-4 frases, incluindo a retomada da pergunta original."""

FORCE_RESUME_MESSAGE = (
    "Entendo sua curiosidade. Essas informações adicionais podem ser discutidas com o recrutador "
    "nas próximas etapas do processo. Vamos prosseguir com a triagem para avaliar melhor o seu perfil."
    "\n\n{original_question}"
)

CONTEXTUAL_QUESTION_PROMPT = """Assistente de recrutamento.
Está conduzindo uma triagem para a vaga de {job_title} na {company_name}.

O candidato acabou de responder à seguinte pergunta:
Pergunta: {previous_question}
Resposta do candidato: {candidate_response}

Agora você precisa fazer a próxima pergunta do bloco **{block_name}** ({block_type}).
A pergunta base é: {base_question}

Adapte a pergunta de forma natural considerando o que o candidato já compartilhou.
Faça uma transição suave entre a resposta anterior e a nova pergunta.
Mantenha o foco na competência sendo avaliada: {competency}.

Responda APENAS com a pergunta adaptada (sem explicações extras).
Limite: 2-3 frases no máximo. Português brasileiro."""

INTENT_CLASSIFICATION_PROMPT = """Classifique a intenção da seguinte mensagem de um candidato em uma triagem de emprego.

Mensagem: "{message}"

Contexto: O candidato deveria estar respondendo a uma pergunta de triagem no bloco "{block_name}".
Pergunta feita: "{current_question}"

Responda APENAS com uma das seguintes classificações:
- ANSWER: O candidato está respondendo à pergunta (mesmo que parcialmente)
- QUESTION: O candidato está fazendo uma pergunta sobre a vaga, empresa ou processo
- GREETING: O candidato está cumprimentando ou fazendo small talk
- UNCLEAR: A mensagem é confusa ou muito curta para classificar

Responda com apenas uma palavra: ANSWER, QUESTION, GREETING ou UNCLEAR"""

WSI_BLOCKS_FALLBACK = [
    {"index": 0, "name": "Abordagem Inicial", "block_type": "technical", "competency": "technical_skills", "questions": [
        "Para começar, gostaria de confirmar algumas informações. Você tem disponibilidade para início imediato ou em qual prazo?",
        "Qual sua pretensão salarial para esta posição?",
    ], "question_frameworks": ["CBI", "CBI"]},
    {"index": 1, "name": "Apresentação da Oportunidade", "block_type": "behavioral", "competency": "motivation", "questions": [
        "O que te motivou a se candidatar para esta vaga?",
        "O que você sabe sobre a nossa empresa?",
    ], "question_frameworks": ["CBI", "CBI"]},
    {"index": 2, "name": "Perguntas Padrão da Empresa", "block_type": "behavioral", "competency": "cultural_fit", "questions": [
        "Descreva seu estilo de trabalho em equipe.",
    ], "question_frameworks": ["CBI"]},
    {"index": 3, "name": "Competências Técnicas", "block_type": "technical", "competency": "technical_skills", "questions": [
        "Conte-me sobre sua experiência mais relevante para esta vaga. Quais tecnologias ou ferramentas você domina?",
        "Descreva um projeto técnico desafiador que você liderou ou participou. Qual foi seu papel e o resultado?",
    ], "question_frameworks": ["CBI", "CBI"]},
    {"index": 4, "name": "Competências Comportamentais e Fit", "block_type": "behavioral", "competency": "interpersonal_skills", "questions": [
        "Me conte sobre uma situação em que você precisou lidar com um conflito no ambiente de trabalho. Como você agiu?",
        "Descreva um momento em que você recebeu um feedback difícil. Como reagiu e o que mudou?",
        "Imagine que você recebe uma demanda urgente de dois gestores diferentes ao mesmo tempo. Como você priorizaria?",
    ], "question_frameworks": ["CBI", "CBI", "CBI"]},
    {"index": 5, "name": "Resultado e Encerramento", "block_type": "behavioral", "competency": "self_assessment", "questions": [
        "Onde você se vê profissionalmente nos próximos 2-3 anos?",
        "Há algo mais que você gostaria de compartilhar sobre seu perfil ou experiência?",
    ], "question_frameworks": ["CBI", "CBI"]},
]

WSI_BLOCKS = WSI_BLOCKS_FALLBACK
TOTAL_QUESTIONS = sum(len(b["questions"]) for b in WSI_BLOCKS)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_progress(
    current_block: int,
    questions_answered: int,
    blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    active_blocks = blocks if blocks is not None else WSI_BLOCKS
    total_questions = sum(len(b["questions"]) for b in active_blocks)
    block_name = "Concluído"
    if current_block < len(active_blocks):
        block_name = active_blocks[current_block]["name"]
    remaining = max(0, total_questions - questions_answered)
    estimated_minutes = int(remaining * 1.5) if remaining > 0 else 0
    return {
        "current_block": current_block,
        "total_blocks": len(active_blocks),
        "block_name": block_name,
        "questions_answered": questions_answered,
        "total_questions": total_questions,
        "estimated_minutes_remaining": estimated_minutes,
    }


def _get_session_blocks(session: Any) -> list[dict[str, Any]]:
    """Retrieve the WSI blocks for a session from its metadata_json cache."""
    meta = session.metadata_json or {}
    cached_blocks = meta.get("wsi_blocks_cache")
    if cached_blocks and isinstance(cached_blocks, list) and len(cached_blocks) > 0:
        return cached_blocks
    return WSI_BLOCKS_FALLBACK


def _get_screening_config(session: Any) -> dict[str, Any]:
    """Get the screening_config stored in session metadata, or empty dict."""
    meta = session.metadata_json or {}
    return meta.get("screening_config", {}) or {}


async def _call_llm(prompt: str) -> str | None:
    try:
        from app.domains.ai.services.llm import llm_service
        result = await llm_service.generate(prompt, provider="gemini")
        return result.strip() if result else None
    except Exception as exc:
        logger.warning(f"[Triagem] LLM call failed: {exc}")
        return None
