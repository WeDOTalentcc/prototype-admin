"""
SystemPromptBuilder — compositor dinâmico de system prompts para a LIA.

Single entry point para compor prompts em runtime, combinando:
  (a) persona base (lia_persona.yaml — cached)
  (b) adições de domínio específico
  (c) contexto do tenant (empresa, setor, vagas)
  (d) contexto do usuário (nome, role)
  (e) resumo do histórico de conversa
  (f) contexto de scope/página
  (g) regras anti-repetição baseadas no estado da conversa
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_persona_base() -> str:
    from app.shared.prompts.loader import PromptLoader
    data = PromptLoader.load("shared/lia_persona")
    return data["prompts"]["lia_persona"]


@lru_cache(maxsize=16)
def _load_domain_additions(agent_type: str) -> str | None:
    try:
        from app.shared.prompts.loader import PromptLoader
        data = PromptLoader.load("shared/agent_prompts")
        return data["prompts"].get(agent_type)
    except Exception as exc:
        logger.warning("Failed to load domain additions for agent_type=%s: %s", agent_type, exc)
        return None


class SystemPromptBuilder:
    """Compõe system prompts dinamicamente para qualquer agente/contexto/tenant."""

    @staticmethod
    def build(
        *,
        agent_type: str = "orchestrator",
        tenant_context_snippet: str = "",
        user_name: str = "",
        user_role: str = "",
        conversation_summary: str = "",
        conversation_history: list[dict[str, Any]] | None = None,
        context_page: str = "general",
        entity_type: str | None = None,
        intent: str = "",
        entities: dict[str, Any] | None = None,
        extra_instructions: str = "",
    ) -> str:
        sections: list[str] = []

        persona = _load_persona_base()
        sections.append(persona)

        domain_additions = _load_domain_additions(agent_type)
        if domain_additions:
            sections.append(f"\n## Especialização do Agente ({agent_type})\n{domain_additions}")

        context_parts: list[str] = []

        if tenant_context_snippet:
            context_parts.append(f"### Contexto do Cliente\n{tenant_context_snippet}")

        if user_name:
            user_desc = f"Você está conversando com **{user_name}**"
            if user_role:
                user_desc += f", que atua como **{user_role}**"
            user_desc += "."
            context_parts.append(f"### Usuário\n{user_desc}")

        if context_page and context_page != "general":
            page_descriptions = {
                "sourcing": "O usuário está na página de sourcing/busca de candidatos.",
                "talent": "O usuário está visualizando o funil de talentos.",
                "pipeline": "O usuário está gerenciando o pipeline de candidatos.",
                "kanban": "O usuário está no kanban de pipeline.",
                "job": "O usuário está visualizando uma vaga específica.",
                "jobs": "O usuário está na lista de vagas.",
                "vacancies": "O usuário está na página de vagas.",
                "wizard": "O usuário está criando/editando uma vaga pelo wizard.",
                "analytics": "O usuário está na página de relatórios e analytics.",
            }
            page_desc = page_descriptions.get(context_page, f"O usuário está na página: {context_page}.")
            context_parts.append(f"### Localização\n{page_desc}")

        if conversation_summary:
            context_parts.append(f"### Resumo da Conversa Anterior\n{conversation_summary}")

        if context_parts:
            sections.append("\n## Contexto Atual\n" + "\n\n".join(context_parts))

        is_ongoing = _detect_ongoing_conversation(conversation_history)
        if is_ongoing:
            sections.append(
                "\n## Regras para esta mensagem\n"
                "- NÃO se re-apresente. A conversa já está em andamento.\n"
                "- NÃO repita informações que já foram ditas.\n"
                "- Seja direta e vá ao ponto."
            )

        if intent:
            intent_line = f"Intent detectado: {intent}"
            if entities:
                intent_line += f" | Entidades: {entities}"
            sections.append(f"\n## Roteamento\n{intent_line}")

        if extra_instructions:
            sections.append(f"\n## Instruções Adicionais\n{extra_instructions}")

        return "\n".join(sections)

    @staticmethod
    def build_error_response(
        *,
        user_name: str = "",
        partial_context: str = "",
        context_page: str = "",
        is_ongoing_conversation: bool = False,
    ) -> str:
        greeting = f"{user_name}, " if user_name else ""
        base = f"{greeting}estou com dificuldade para processar essa solicitação no momento."

        if context_page and context_page not in ("general", ""):
            page_hints = {
                "wizard": " Você pode tentar descrever a vaga novamente ou voltar à etapa anterior.",
                "sourcing": " Pode reformular a busca ou tentar com outros filtros.",
                "pipeline": " Tente novamente em alguns segundos.",
                "kanban": " Tente novamente em alguns segundos.",
                "analytics": " Tente atualizar a página ou solicitar o relatório novamente.",
            }
            hint = page_hints.get(context_page, "")
            return f"{base}{hint} Se persistir, me avise que busco outra forma de ajudar."

        return f"{base} Pode tentar novamente em alguns segundos? Se persistir, me avise que busco outra forma de ajudar."

    @staticmethod
    def build_clarification(
        message: str,
        partial_matches: list[dict[str, Any]] | None = None,
        user_name: str = "",
    ) -> tuple[str, list[str]]:
        snippet = message.strip()[:80]
        greeting = f"{user_name}, " if user_name else ""

        if partial_matches and len(partial_matches) >= 2:
            domains_desc = {
                "job_planner": "criar ou gerenciar vagas",
                "sourcing": "buscar candidatos",
                "cv_screening": "analisar currículos e compatibilidade",
                "interviewer": "conduzir entrevistas",
                "wsi_evaluator": "avaliar com metodologia WSI",
                "scheduling": "agendar entrevistas",
                "analyst_feedback": "relatórios e feedback",
                "ats_integrator": "integração com ATS",
                "recruiter_assistant": "suporte geral de recrutamento",
                "pipeline": "gerenciar pipeline",
            }
            matched_domains = [m.get("domain_id", "") for m in partial_matches[:3]]
            options = [domains_desc.get(d, d) for d in matched_domains if d in domains_desc]

            if options:
                options_text = " ou ".join(options)
                question = (
                    f"{greeting}Sua mensagem pode estar relacionada a {options_text}. "
                    "Pode me dar mais detalhes sobre o que precisa?"
                )
                suggestion_list = [domains_desc.get(d, d).capitalize() for d in matched_domains if d in domains_desc]
                return question, suggestion_list

        default_options = [
            "Criar ou gerenciar vagas",
            "Buscar candidatos",
            "Analisar currículos",
            "Agendar entrevistas",
            "Relatórios e analytics",
        ]

        if snippet:
            question = (
                f"{greeting}Não consegui entender exatamente o que você precisa a partir de \"{snippet}\". "
                "Pode reformular ou me dar mais contexto?"
            )
        else:
            question = f"{greeting}Como posso ajudar você?"

        return question, default_options


def _detect_ongoing_conversation(history: list[dict[str, Any]] | None) -> bool:
    if not history:
        return False
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]
    return len(assistant_msgs) >= 1
