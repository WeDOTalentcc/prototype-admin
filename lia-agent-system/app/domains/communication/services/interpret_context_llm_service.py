"""
InterpretContextLLMService - AI-powered interpretation of recruiter mini-prompts.
Layer 2: Uses Claude to understand natural language instructions during candidate transitions.
Falls back to rule-based logic on failure.
"""
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.shared.providers.llm_client import is_llm_available, llm_complete

logger = logging.getLogger(__name__)

INTERPRET_SYSTEM_PROMPT = """Assistente de recrutamento inteligente da WeDoTalent.
Sua tarefa é interpretar o mini-prompt do recrutador durante a movimentação de candidatos no pipeline.

Você deve extrair informações estruturadas do texto livre do recrutador e retornar um JSON.
Sua resposta (lia_message) deve ser ACIONÁVEL — confirme exatamente o que será feito, incluindo data, hora, formato e quaisquer detalhes mencionados."""

def _build_interpret_prompt(
    prompt: str,
    candidate_name: str | None,
    job_title: str | None,
    from_stage: str,
    to_stage: str,
    action_behavior: str,
) -> str:
    return f"""Analise o mini-prompt do recrutador abaixo e extraia informações estruturadas.

CONTEXTO DA TRANSIÇÃO:
- Candidato: {candidate_name or 'Não informado'}
- Vaga: {job_title or 'Não informada'}
- Etapa origem: {from_stage}
- Etapa destino: {to_stage}
- Tipo de ação: {action_behavior}

MINI-PROMPT DO RECRUTADOR:
"{prompt}"

Retorne um JSON com os seguintes campos:
{{
  "extracted_preferences": {{
    "date": "data mencionada ou null",
    "time": "horário mencionado ou null",
    "interviewer": "nome do entrevistador mencionado ou null",
    "location": "local mencionado ou null",
    "format": "formato mencionado (presencial/remoto/híbrido) ou null",
    "duration": "duração mencionada ou null",
    "notes": "observações extras relevantes ou null"
  }},
  "suggested_sub_status": "sub-status mais adequado baseado no contexto (ou null se não tiver certeza)",
  "suggested_action": "lia_auto ou manual ou just_move",
  "urgency": "high ou normal ou low",
  "lia_message": "mensagem curta e natural da LIA respondendo ao recrutador (máx 2 frases)",
  "confidence": 0.0 a 1.0,
  "reasoning": "breve explicação da interpretação"
}}

REGRAS:
- Se o recrutador pedir algo manual ou dizer "eu mesmo faço", suggested_action = "manual"
- Se mencionar urgência, prioridade ou "agora", urgency = "high"
- Se for etapa passiva (intake/passive) sem instruções, suggested_action = "just_move"
- A lia_message deve ser natural, em português, como se a LIA estivesse respondendo ao recrutador
- A lia_message DEVE ser acionável e confirmar exatamente o que será executado
- Para agendamentos: confirme data, hora, formato e local na lia_message. Ex: "Entendido! Vou enviar o convite de entrevista para dia 25/02 às 18h por videoconferência. Ao confirmar, o candidato receberá o convite por e-mail."
- Para triagens: confirme o tipo de avaliação. Ex: "Vou iniciar a triagem WSI com o candidato. Ele receberá as perguntas por e-mail."
- Para testes: confirme o tipo de teste. Ex: "Vou enviar o teste técnico para o candidato."
- Extraia TODAS as preferências que encontrar no texto
- Responda APENAS com o JSON, sem texto adicional"""


async def interpret_with_llm(
    prompt: str,
    candidate_name: str | None = None,
    job_title: str | None = None,
    from_stage: str = "",
    to_stage: str = "",
    action_behavior: str = "",
) -> dict[str, Any] | None:
    """
    Interpret recruiter mini-prompt using Claude LLM.
    Returns structured interpretation or None on failure.
    """
    if not settings.ENABLE_LLM_INTERPRET_CONTEXT:
        logger.info("[INTERPRET-LLM] Feature flag disabled")
        return None

    if not is_llm_available():
        logger.warning("[INTERPRET-LLM] LLM not available")
        return None

    if not prompt or not prompt.strip():
        return None

    try:
        full_prompt = _build_interpret_prompt(
            prompt=prompt,
            candidate_name=candidate_name,
            job_title=job_title,
            from_stage=from_stage,
            to_stage=to_stage,
            action_behavior=action_behavior,
        )

        response_text = await llm_complete(
            prompt=full_prompt,
            system=INTERPRET_SYSTEM_PROMPT,
            max_tokens=800,
            temperature=0.2,
        )

        if not response_text:
            logger.warning("[INTERPRET-LLM] Empty response from LLM")
            return None

        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            logger.warning(f"[INTERPRET-LLM] No JSON found in response: {response_text[:200]}")
            return None

        result = json.loads(json_match.group())

        prefs = result.get("extracted_preferences", {})
        clean_prefs = {k: v for k, v in prefs.items() if v is not None and v != "null" and v != ""}
        result["extracted_preferences"] = clean_prefs if clean_prefs else None

        if result.get("suggested_sub_status") in (None, "null", ""):
            result["suggested_sub_status"] = None

        result["method"] = "llm"

        logger.info(
            f"[INTERPRET-LLM] Successfully interpreted prompt. "
            f"Confidence: {result.get('confidence', 'N/A')}, "
            f"Action: {result.get('suggested_action', 'N/A')}"
        )

        return result

    except json.JSONDecodeError as e:
        logger.error(f"[INTERPRET-LLM] JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"[INTERPRET-LLM] Error: {e}", exc_info=True)
        return None
