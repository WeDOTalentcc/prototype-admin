"""
LIA Jobs Management Assistant Service - AI-powered analysis for job portfolio management.
Uses LLMProviderFactory for all LLM calls (Task #93 migration).
"""
import json
import logging
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.domains.recruiter_assistant.prompts.jobs_management_prompts import (
    JobsManagementCommandType,
    build_jobs_management_prompt,
    detect_jobs_command_type,
    get_jobs_management_system_prompt,
    resolve_jobs_ui_action,
)
from app.shared.providers.llm_factory import get_provider_for_tenant

logger = logging.getLogger(__name__)


class JobsManagementAssistantService:
    """Service for AI-powered job portfolio analysis via LLMProviderFactory."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def process_command(
        self,
        command: str,
        command_type: str | None,
        jobs_context: dict[str, Any],
        selected_jobs: list[dict[str, Any]] | None = None,
        top_jobs: list[dict[str, Any]] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        detected_type, confidence = detect_jobs_command_type(command)
        final_type = (
            command_type
            if command_type and command_type in [e.value for e in JobsManagementCommandType]
            else detected_type
        )

        logger.info(f"Processing Jobs Management command - Type: {final_type} (confidence: {confidence:.2f})")

        full_prompt = build_jobs_management_prompt(
            command_type=final_type,
            user_query=command,
            jobs_context=jobs_context,
            selected_jobs=selected_jobs,
            top_jobs=top_jobs,
        )

        messages = []
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": full_prompt})

        try:
            container = get_provider_for_tenant()
            user_content = messages[-1]["content"] if messages else full_prompt
            system_prompt = get_jobs_management_system_prompt()
            if len(messages) > 1:
                history_text = "\n".join(
                    f"{m['role'].upper()}: {m['content']}" for m in messages[:-1]
                )
                user_content = history_text + "\n\nUSER: " + user_content
            response_text = await container.generate_with_fallback(
                user_content, system=system_prompt,
                agent_type="RecruiterAssistantAgent",
            )
            structured_data = self._parse_json_response(response_text)
            content = self._extract_content(response_text, structured_data)
            suggestions = self._extract_suggestions(structured_data, final_type)
            ui_action = resolve_jobs_ui_action(final_type)

            return {
                "content": content,
                "command_type": final_type,
                "confidence": confidence,
                "structured_data": structured_data,
                "suggested_prompts": suggestions,
                "ui_action": ui_action,
                "ui_action_params": None,
            }

        except Exception as e:
            logger.error(f"Jobs Management LLM error: {e}")
            return self._build_fallback(command, final_type, jobs_context, confidence)

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
        if structured:
            for field in ("resposta", "response", "content", "message", "texto", "answer"):
                value = structured.get(field)
                if value and isinstance(value, str) and value.strip():
                    return value.strip()
            return "Analisei os dados disponíveis. Como posso ajudar com mais detalhes?"

        cleaned = raw_text
        cleaned = re.sub(r'```json\s*[\s\S]*?\s*```', '', cleaned)
        cleaned = re.sub(r'```\s*[\s\S]*?\s*```', '', cleaned)
        cleaned = cleaned.strip()

        if not cleaned:
            return "Analisei os dados disponíveis. Como posso ajudar com mais detalhes?"

        return cleaned

    def _extract_suggestions(self, structured: dict | None, cmd_type: str) -> list[str]:
        if structured and structured.get("sugestoes"):
            return structured["sugestoes"][:6]

        defaults = {
            "visao_geral": [
                "Quais vagas precisam de atenção urgente?",
                "Compare a performance por departamento",
                "Qual o tempo médio de contratação?",
            ],
            "vagas_urgentes": [
                "Como está o SLA dessas vagas?",
                "Quais ações tomar primeiro?",
                "Mostrar vagas sem candidatos",
            ],
            "comparar_vagas": [
                "Qual vaga tem melhor pipeline?",
                "Visão geral de todas as vagas",
                "Gargalos entre essas vagas",
            ],
        }
        return defaults.get(cmd_type, [
            "Como estão as vagas?",
            "Quais vagas precisam de atenção?",
            "Qual a taxa de preenchimento?",
        ])

    def _build_fallback(
        self, command: str, cmd_type: str, jobs_context: dict, confidence: float
    ) -> dict[str, Any]:
        total = jobs_context.get("total", 0)
        active = jobs_context.get("active", 0)
        urgent = jobs_context.get("urgent", 0)

        content = (
            f"## 📊 Resumo Rápido das Vagas\n\n"
            f"Você tem **{total} vagas** no sistema, sendo **{active} ativas**"
        )
        if urgent > 0:
            content += f" e **{urgent} urgentes**"
        content += (
            f".\n\nEstou processando sua solicitação sobre *\"{command}\"*. "
            f"Posso ajudar com análises detalhadas — tente ser mais específico ou "
            f"pergunte sobre vagas urgentes, SLA ou performance por departamento."
        )

        return {
            "content": content,
            "command_type": cmd_type,
            "confidence": confidence,
            "structured_data": None,
            "suggested_prompts": [
                "Como estão as vagas?",
                "Quais vagas precisam de atenção?",
                "Tempo médio de contratação",
            ],
            "ui_action": None,
            "ui_action_params": None,
        }


jobs_management_assistant = JobsManagementAssistantService()
