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



@lru_cache(maxsize=1)
def _get_canonical_glossary_block() -> str:
    """Load canonical term definitions from docs/GLOSSARY.md at startup.

    Returns a markdown block listing key WSI/methodology terms with their
    live definitions, so agents stay in sync with the glossary without a
    code deploy. Returns "" if the glossary file is unavailable.

    Drift between the prompt's expected terms and the glossary is logged
    as a WARNING so it can be detected via log monitoring.
    """
    try:
        from app.shared.prompts.glossary_loader import (
            CANONICAL_PROMPT_TERMS,
            detect_drift,
            render_canonical_terms_section,
        )
        block = render_canonical_terms_section(CANONICAL_PROMPT_TERMS)
        missing = detect_drift(CANONICAL_PROMPT_TERMS)
        if missing:
            logger.warning(
                "[SystemPromptBuilder] Glossary drift -- terms missing from "
                "docs/GLOSSARY.md: %s",
                ", ".join(missing),
            )
        return block
    except Exception as exc:
        logger.debug("[SystemPromptBuilder] Glossary load failed: %s", exc)
        return ""


_CANONICAL_GLOSSARY_BLOCK = _get_canonical_glossary_block()


def _append_ai_persona_override(
    sections: list[str], ai_persona: dict[str, str],
) -> None:
    """Append per-tenant persona override sections to ``sections``.

    Append-only — NEVER mutates the canonical persona base. Two possible
    sections (each conditional on the field being different from canonical
    default):

    - **Override de Persona**: instructs the LLM to use the tenant-chosen
      name when introducing itself, overriding the base which references
      "LIA". The base remains visible for context but the override takes
      precedence (LLM instruction prompt priority).
    - **Tom de Voz Customizado**: appends the textual tone instruction
      mapped from :data:`TONE_INSTRUCTIONS`.

    Fail-safe on garbage input:
    - Invalid tone (not in canonical enum) → skip silently (log debug),
      better LLM with no custom tone than crash.
    - Missing dict field → fall back to canonical default for that field.
    - ``ai_persona=None`` / empty dict → caller should not have called us;
      no-op.
    """
    if not ai_persona:
        return
    # Local import keeps this builder usable even if persona service has
    # transient issues (rare circular-import scenarios with shared services).
    try:
        from app.domains.persona.services.ai_persona_validator import (
            DEFAULT_AI_NAME,
            DEFAULT_AI_TONE,
            TONE_INSTRUCTIONS,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "[SystemPromptBuilder] ai_persona_validator unavailable; "
            "skipping persona override. Reason: %s", exc,
        )
        return

    name = (ai_persona.get("name") or DEFAULT_AI_NAME).strip()
    tone = ai_persona.get("tone") or DEFAULT_AI_TONE

    # Name override (only when truly custom)
    if name and name != DEFAULT_AI_NAME:
        sections.append(
            "\n## Override de Persona (per-tenant)\n\n"
            f"Você é **{name}**, não LIA.\n\n"
            f"O nome \"LIA\" mencionado no persona base acima é o nome "
            f"técnico do sistema. Sua identidade pública para este cliente "
            f"é **{name}**. Quando se apresentar ou se referir a si mesma, "
            f"use **{name}** — exceto se o usuário perguntar explicitamente "
            f"sobre o sistema técnico por trás (aí pode mencionar que roda "
            f"sobre a plataforma WeDOTalent).\n"
        )

    # Tone instruction (only when canonical AND non-default)
    if tone != DEFAULT_AI_TONE:
        instruction = TONE_INSTRUCTIONS.get(tone)
        if instruction:
            sections.append(
                "\n## Tom de Voz Customizado\n\n"
                f"{instruction}\n\n"
                "Esta configuração de tom **sobrepõe** o tom padrão descrito "
                "no persona base. Mantenha as regras de ética e compliance "
                "inalteradas — apenas o ESTILO de comunicação muda."
            )
        else:
            logger.debug(
                "[SystemPromptBuilder] ai_persona.tone='%s' não mapeia para "
                "TONE_INSTRUCTIONS; ignorando.",
                tone,
            )

REACT_INSTRUCTIONS = (
    "\n## Protocolo de Raciocinio (ReAct)\n\n"
    "Voce opera em um ciclo de Raciocinio-Acao-Observacao:\n\n"
    "1. RACIOCINE sobre a situacao atual:\n"
    "   - O que o recrutador realmente precisa?\n"
    "   - Preciso buscar dados ou posso responder diretamente?\n"
    "   - Ha algum risco de compliance, fairness ou LGPD?\n\n"
    "2. AJA de uma das formas:\n"
    '   - action="call_tool": Chamar uma ferramenta para consultar/executar\n'
    '   - action="respond": Responder ao recrutador com insights\n'
    '   - action="ask_clarification": Pedir esclarecimento quando ambiguo\n\n'
    "3. OBSERVE o resultado e decida se precisa agir novamente ou responder.\n\n"
    'Entenda confirmacoes: "sim", "pode", "confirmo", "ok", "beleza", "bora"\n'
    'Entenda negacoes: "nao", "espera", "cancela", "volta", "quero mudar"\n'
)

class SystemPromptBuilder:
    """Compõe system prompts dinamicamente para qualquer agente/contexto/tenant."""

    @staticmethod
    def build(
        *,
        agent_type: str = "orchestrator",
        tenant_context_snippet: str = "",
        user_name: str = "",
        user_role: str = "",
        recruiter_context: str = "",
        conversation_summary: str = "",
        conversation_history: list[dict[str, Any]] | None = None,
        context_page: str = "general",
        entity_type: str | None = None,
        intent: str = "",
        entities: dict[str, Any] | None = None,
        extra_instructions: str = "",
        ai_persona: dict[str, str] | None = None,
    ) -> str:
        """Build the full system prompt.

        ``ai_persona`` (audit 2026-05-21 E2.3): per-tenant override of name
        + tone. Shape: ``{"name": str, "tone": str}``. When passed:

        - Custom name (not the canonical default ``"LIA"``) → emits a
          "Override de Persona" section that tells the LLM to use the
          tenant-chosen name when introducing itself.
        - Custom tone (not the canonical default ``"profissional"``) →
          emits a "Tom de Voz Customizado" section with the textual
          instruction mapped from ``TONE_INSTRUCTIONS``.
        - Defaults or absence → no new sections; legacy callers unaffected.

        Invariant preserved: the persona base YAML is NEVER mutated. We
        only APPEND sections. Ethics blocks (LGPD / fairness / EU AI Act)
        live in the base and remain untouchable.
        """
        sections: list[str] = []

        persona = _load_persona_base()
        sections.append(persona)

        # Canonical glossary (live from docs/GLOSSARY.md). Empty when
        # the file is unavailable -- callers fall back to static prose.
        if _CANONICAL_GLOSSARY_BLOCK:
            sections.append(_CANONICAL_GLOSSARY_BLOCK)

        domain_additions = _load_domain_additions(agent_type)
        if domain_additions:
            sections.append(f"\n## Especialização do Agente ({agent_type})\n{domain_additions}")

        # E2.3 ai_persona override (append-only, never mutates the YAML base)
        if ai_persona:
            _append_ai_persona_override(sections, ai_persona)

        context_parts: list[str] = []

        if tenant_context_snippet:
            context_parts.append(f"### Contexto do Cliente\n{tenant_context_snippet}")

        if recruiter_context:
            context_parts.append(f"### Preferências do Recrutador\n{recruiter_context}")

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

        # Inject ReAct protocol for agent contexts
        if agent_type and agent_type != "orchestrator":
            sections.append(REACT_INSTRUCTIONS)

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
