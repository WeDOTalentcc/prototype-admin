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

        # G1 canonical fix (2026-05-24): use canonical_pages.describe_page
        # instead of hardcoded dict. Single source of truth, full coverage
        # of PT-BR routes (configuracoes, funil_talentos, recrutar,
        # agent_studio, ajuda, ...). Legacy aliases (sourcing, kanban,
        # vacancies, ...) still normalize correctly via LEGACY_PAGE_ALIASES.
        from app.shared.canonical_pages import describe_page
        if context_page:
            page_desc = describe_page(context_page)
            if page_desc:
                context_parts.append(f"### Localização\n{page_desc}")

        # G3 canonical fix (2026-05-24): grant LLM raw path the same
        # navigation capability that ACTIONABLE_INTENTS / Rail A paths
        # already have. Without this, the LLM persona base prompt makes
        # it refuse ("não consigo navegar") when intent classifier MISSES
        # an utterance and the request falls through to the LLM.
        #
        # Convention: LLM emits "[NAVIGATE:<canonical_page>]" inline in
        # the response content. The chat_adapter post-processor extracts
        # the marker, populates ChatResponse.ui_action/ui_action_params,
        # and strips the marker from user-facing content.
        # Sprint 3 canonical fix (2026-05-24): G3 navigation page list is
        # now DERIVED from canonical_pages.PAGE_DESCRIPTIONS_PT_BR — single
        # source of truth. Adding a new page to CanonicalPage automatically
        # makes it available to the LLM here.
        try:
            from app.shared.canonical_pages import (
                CanonicalPage,
                PAGE_SHORT_LABELS_PT_BR,
            )
            nav_lines = [
                "### Capabilities — Navegação",
                "Você TEM capability de navegar entre páginas da plataforma. "
                "Quando o usuário pedir explicitamente para ir a uma página "
                "(ex: \"me leve para configurações\", \"abre o funil\", "
                "\"vai pra vagas\"), responda naturalmente E inclua o marker "
                "**[NAVIGATE:<canonical_page>]** ao final do texto.",
                "",
                "Páginas canonical disponíveis:",
            ]
            for page in CanonicalPage:
                if page.value == "general":
                    continue  # internal sentinel, not user-facing
                desc = PAGE_SHORT_LABELS_PT_BR.get(page, page.value)
                nav_lines.append(f"- `{page.value}` → {desc}")
            nav_lines.extend([
                "",
                "Exemplo:",
                "User: \"me leve para configurações\"",
                "Você: \"Te levando para Configurações! 🚀 [NAVIGATE:configuracoes]\"",
                "",
                "REGRAS:",
                "1. NÃO recuse navegação — sempre tem essa capability.",
                "2. NÃO use o marker se o usuário apenas mencionou a página "
                "sem pedir explicitamente para ir lá.",
                "3. NÃO emita múltiplos markers no mesmo turn.",
                "4. Use SEMPRE os identifiers canonical exatos (vagas, "
                "funil_talentos, configuracoes — NÃO traduza).",
            ])
            context_parts.append("\n".join(nav_lines))
        except Exception as _nav_exc:
            import logging as _log
            _log.getLogger(__name__).error(
                "[Sprint 3 G3] failed to derive navigation pages from canonical_pages: %s",
                _nav_exc,
                exc_info=True,
            )

        # G6 canonical fix (2026-05-24): grant the LLM raw path explicit
        # awareness of the 29+ action tools registered in tool_registry.
        # Without this section, the LLM persona defaults to "I'm just
        # text, I can't execute actions" when intent classifier misses
        # an utterance and the request falls through to the LLM.
        #
        # When the LLM is invoked via agentic_loop (Phase 1.5), the actual
        # tools are passed as tool_schemas and the LLM emits tool_use
        # blocks natively. This prompt section is the DESCRIPTIVE
        # counterpart that ensures the LLM does not refuse on the OTHER
        # paths (Phase 1.3 plan service, Phase 2 orchestrator fallback)
        # where tool schemas are not directly bound.
        # Sprint 3 canonical fix (2026-05-24): G6 capabilities section is
        # now DERIVED from tool_registry. Categories + tool→category mapping
        # live in app/tools/categories.py — single source of truth. New tools
        # added to the registry appear automatically here; new tools without
        # a category mapping land in OTHER and the sensor J flags them.
        try:
            from app.tools.registry import tool_registry
            from app.tools.categories import (
                CATEGORY_TAGLINES,
                DISPLAY_ORDER,
            )
            grouped = tool_registry.get_tools_by_category()
            capability_lines = [
                "### Capabilities — Ações",
                "Você TEM ferramentas para executar AÇÕES CONCRETAS na "
                "plataforma. NUNCA recuse uma ação alegando \"sou apenas um "
                "assistente de texto\" sem verificar primeiro a lista abaixo.",
                "",
            ]
            for cat_name in DISPLAY_ORDER:
                tools = grouped.get(cat_name, [])
                if not tools:
                    continue
                tagline = CATEGORY_TAGLINES.get(cat_name, "")
                tool_names = ", ".join(t.name for t in tools)
                if tagline:
                    capability_lines.append(
                        f"**{cat_name}**: {tagline} ({tool_names})."
                    )
                else:
                    capability_lines.append(f"**{cat_name}**: {tool_names}.")
                capability_lines.append("")
            # OTHER bucket: any unmapped tool. Surfaced so the LLM at least
            # knows the name exists; sensor J flags the mapping gap.
            other_tools = grouped.get("OTHER", [])
            if other_tools:
                tool_names = ", ".join(t.name for t in other_tools)
                capability_lines.append(
                    f"**OUTROS** (sem categoria canonical, ver app/tools/categories.py): "
                    f"{tool_names}."
                )
                capability_lines.append("")
            capability_lines.extend([
                "EXEMPLO de mapeamento NL → ação:",
                "- \"rejeite o candidato João\" → reject_candidate",
                "- \"mova maria pra próxima etapa\" → update_candidate_stage",
                "- \"mande um email pro candidato X\" → send_email",
                "- \"fecha a vaga de Dev Backend\" → close_job",
                "- \"agenda entrevista com fulano amanhã 14h\" → schedule_interview",
                "- \"como está o funil dessa vaga?\" → get_vacancy_funnel",
                "",
                "REGRAS:",
                "1. Quando o usuário pedir uma ação que mapeia para a lista "
                "acima, EXECUTE (não responda apenas com texto descritivo).",
                "2. Se a ação exigir parâmetros (qual candidato, qual etapa, "
                "qual vaga), pergunte naturalmente em PT-BR coloquial.",
                "3. Se a ação não estiver na lista, seja transparente: "
                "\"essa ação específica eu ainda não consigo executar, mas "
                "posso te ajudar com X, Y, Z\".",
                "4. SEMPRE confirme antes de ações destrutivas "
                "(close_job, reject_candidate, bulk operations).",
            ])
            context_parts.append("\n".join(capability_lines))
        except Exception as _cap_exc:
            # Fail-open: if registry unavailable for any reason, the LLM
            # still gets the persona base prompt. Log loud for ops.
            import logging as _log
            _log.getLogger(__name__).error(
                "[Sprint 3 G6] failed to derive capabilities from registry: %s",
                _cap_exc,
                exc_info=True,
            )

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

        # Wave D1.2 (2026-05-27): canonical compliance_block injection.
        # PromptComposer.compliance_blocks_for() é single source of truth
        # — LGPD + fairness + bias + audit + guardrails universais. Garante
        # que TODO system prompt construído via SystemPromptBuilder (Studio
        # custom agents, recruiter_assistant, autonomous, orchestrator, etc.)
        # leva os 14 protected attributes + EU AI Act + universal guardrails.
        # Variant é selecionada automaticamente por agent_type via
        # _classify_agent_variant (decision / communication / operational).
        # Fail-open: se YAML load falhar, retorna string vazia (graceful).
        try:
            from app.shared.prompts.prompt_composer import PromptComposer
            compliance_block = PromptComposer.compliance_blocks_for(agent_type)
            if compliance_block and compliance_block.strip():
                sections.append(f"\n## Compliance e Guardrails\n{compliance_block}")
        except Exception as _comp_exc:
            import logging as _log
            _log.getLogger(__name__).error(
                "[Wave D1.2] compliance_block injection failed: %s",
                _comp_exc,
                exc_info=True,
            )

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
