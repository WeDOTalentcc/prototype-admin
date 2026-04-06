"""
LIA Talent Assistant Service - AI-powered analysis for talent funnel.
Uses Replit AI Integrations for Anthropic access.
"""
import json
import logging
import os
import re
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import (
    TalentCommandType,
    build_talent_prompt,
    detect_talent_command_type,
    get_talent_system_prompt,
)

logger = logging.getLogger(__name__)

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")


class TalentAssistantService:
    """Service for AI-powered talent funnel analysis using Claude."""

    def __init__(self):
        self._client: Anthropic | None = None

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            if not AI_INTEGRATIONS_ANTHROPIC_API_KEY or not AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
                raise ValueError(
                    "AI_INTEGRATIONS_ANTHROPIC_API_KEY or AI_INTEGRATIONS_ANTHROPIC_BASE_URL not configured"
                )
            self._client = Anthropic(
                api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def process_command(
        self,
        command: str,
        command_type: str | None,
        candidates: list[dict[str, Any]],
        selected_candidate_ids: list[str] | None = None,
        search_context: dict[str, Any] | None = None,
        target_job: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        detected_type, confidence = detect_talent_command_type(command)
        final_type = (
            command_type
            if command_type and command_type in [e.value for e in TalentCommandType]
            else detected_type
        )

        logger.info(f"Processing Talent command - Type: {final_type} (confidence: {confidence:.2f})")

        full_prompt = build_talent_prompt(
            command_type=final_type,
            user_query=command,
            candidates=candidates,
            selected_ids=selected_candidate_ids,
            search_context=search_context,
            target_job=target_job,
        )

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2048,
                system=get_talent_system_prompt(),
                messages=[{"role": "user", "content": full_prompt}],
            )

            response_text = message.content[0].text
            structured_data = self._parse_json_response(response_text)
            content = self._extract_content(response_text, structured_data)
            suggestions = self._extract_suggestions(structured_data, final_type)

            return {
                "content": content,
                "command_type": final_type,
                "confidence": confidence,
                "structured_data": structured_data,
                "suggested_prompts": suggestions,
            }

        except Exception as e:
            logger.error(f"Talent Assistant LLM error: {e}")
            return self._build_fallback(command, final_type, candidates, confidence)

    def _parse_json_response(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'(\{[\s\S]*\})',
        ]
        for pattern in json_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        return None

    def _extract_content(self, raw_text: str, structured: dict | None) -> str:
        if structured and structured.get("resposta"):
            return structured["resposta"]
        cleaned = raw_text
        cleaned = re.sub(r'```json\s*[\s\S]*?\s*```', '', cleaned)
        cleaned = re.sub(r'```\s*[\s\S]*?\s*```', '', cleaned)
        cleaned = cleaned.strip()
        return cleaned if cleaned else raw_text

    def _extract_suggestions(self, structured: dict | None, cmd_type: str) -> list[str]:
        if structured and structured.get("sugestoes"):
            return structured["sugestoes"][:6]

        defaults = {
            "rankear_candidatos": [
                "Compare os top 3 em detalhes",
                "Analise as skills do ranking",
                "Qual tem melhor fit para a vaga?",
            ],
            "comparar_candidatos": [
                "Quem é o melhor e por quê?",
                "Analise as skills de cada um",
                "Busque perfis similares",
            ],
            "analisar_perfil": [
                "Compare com outros candidatos",
                "Busque perfis similares",
                "Qual o match com a vaga?",
            ],
            "top_candidatos": [
                "Compare os top candidatos",
                "Analisar skills do top 3",
                "Estratégia de sourcing",
            ],
        }
        return defaults.get(cmd_type, [
            "Quem são os top candidatos?",
            "Analise as skills do pool",
            "Compare os selecionados",
        ])

    def _build_fallback(
        self, command: str, cmd_type: str, candidates: list[dict], confidence: float
    ) -> dict[str, Any]:
        total = len(candidates)
        content = (
            f"## 🔍 Análise do Pool\n\n"
            f"Você tem **{total} candidatos** em visualização. "
            f"Estou processando sua solicitação sobre *\"{command}\"*.\n\n"
            f"Posso ajudar com ranking, comparação, análise de perfil e muito mais. "
            f"Tente ser mais específico ou selecione candidatos para uma análise focada."
        )
        return {
            "content": content,
            "command_type": cmd_type,
            "confidence": confidence,
            "structured_data": None,
            "suggested_prompts": [
                "Quem são os top 5?",
                "Compare os selecionados",
                "Analise as skills",
            ],
        }


talent_assistant = TalentAssistantService()
