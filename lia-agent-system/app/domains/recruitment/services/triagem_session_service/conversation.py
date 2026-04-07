"""
Conversation helpers: intent classification, off-script and contextual question generation.
"""
import logging
from typing import Any

from ._shared import (
    CONTEXTUAL_QUESTION_PROMPT,
    FORCE_RESUME_MESSAGE,
    INTENT_CLASSIFICATION_PROMPT,
    MAX_CONSECUTIVE_OFF_SCRIPT,
    OFF_SCRIPT_SYSTEM_PROMPT,
    _call_llm,
)

logger = logging.getLogger(__name__)


async def _classify_intent(message: str, block_name: str, current_question: str) -> str:
    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        message=message[:500],
        block_name=block_name,
        current_question=current_question,
    )
    result = await _call_llm(prompt)
    if result and result.upper().strip() in ("ANSWER", "QUESTION", "GREETING", "UNCLEAR"):
        return result.upper().strip()
    return "ANSWER"


async def _generate_off_script_response(
    candidate_message: str,
    original_question: str,
    block_name: str,
    company_name: str,
    job_title: str,
) -> str | None:
    prompt = OFF_SCRIPT_SYSTEM_PROMPT.format(
        company_name=company_name or "a empresa",
        job_title=job_title or "a vaga",
        original_question=original_question,
        candidate_message=candidate_message[:500],
        block_name=block_name,
    )
    return await _call_llm(prompt)


async def _generate_contextual_question(
    previous_question: str,
    candidate_response: str,
    base_question: str,
    block_name: str,
    block_type: str,
    competency: str,
    company_name: str,
    job_title: str,
) -> str | None:
    prompt = CONTEXTUAL_QUESTION_PROMPT.format(
        job_title=job_title or "a vaga",
        company_name=company_name or "a empresa",
        previous_question=previous_question[:300],
        candidate_response=candidate_response[:500],
        base_question=base_question,
        block_name=block_name,
        block_type=block_type,
        competency=competency,
    )
    return await _call_llm(prompt)
