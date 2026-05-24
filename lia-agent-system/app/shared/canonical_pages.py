"""Canonical page vocabulary — single source of truth for chat page context.

G1 canonical fix (2026-05-24). Before this, the page vocabulary was
fragmented across:
- context_adapter.py:PAGE_TO_CONTEXT_TYPE (5-key dict)
- system_prompt_builder.py:page_descriptions (9-key dict, partial overlap)
- frontend useChatMessages.ts (PT-BR routes missing, EN-only matcher)
- frontend LiaChatMessageList.tsx:pageToUrl (5-key reverse map, PT-BR)

Result: pages like /configuracoes, /funil-de-talentos, /agent-studio,
/recrutar fell back to "general" → LLM had no idea where the user was.

This module is the canonical source. The TypeScript equivalent lives in
plataforma-lia/src/lib/canonical-pages.ts (mirror — sync changes here).
"""
from __future__ import annotations

from enum import StrEnum


class CanonicalPage(StrEnum):
    """All pages a user can be on when chatting with LIA.

    Add a new page here ONLY if it has a meaningful conversation context.
    Login, password reset, etc. are not chat surfaces — they do not need
    a value here.
    """

    HOME = "home"
    VAGAS = "vagas"                          # job list
    VAGA_DETALHE = "vaga_detalhe"            # single job detail
    RECRUTAR = "recrutar"                    # wizard / criação de vaga
    FUNIL_TALENTOS = "funil_talentos"        # funil de talentos main
    CANDIDATO_DETALHE = "candidato_detalhe"  # single candidate detail
    PIPELINE_KANBAN = "pipeline_kanban"      # kanban view of pipeline
    DASHBOARD = "dashboard"                  # dashboard / indicadores
    CONFIGURACOES = "configuracoes"          # company settings (any subpath)
    AGENT_STUDIO = "agent_studio"            # agent studio
    AJUDA = "ajuda"                          # help / docs
    BANCOS_TALENTOS = "bancos_talentos"      # talent pools
    BIBLIOTECA = "biblioteca"                # LIA library
    CENTRAL_COMUNICACAO = "central_comunicacao"  # communication center
    TASKS = "tasks"                          # task center
    CHAT = "chat"                            # dedicated chat page
    TRUST = "trust"                          # trust / compliance hub
    GENERAL = "general"                      # fallback only


# Page descriptions used by SystemPromptBuilder to inject the "Localização"
# section into the LLM's system prompt. Each description is a complete
# sentence in PT-BR. The LLM uses these as grounding for context-aware
# responses ("você está na página X — pode sugerir Y").
#
# Invariant: every CanonicalPage value (except GENERAL) MUST have a
# description. The canonical contract test enforces this.
PAGE_DESCRIPTIONS_PT_BR: dict[CanonicalPage, str] = {
    CanonicalPage.HOME: (
        "O usuário está na página inicial / dashboard principal da plataforma."
    ),
    CanonicalPage.VAGAS: (
        "O usuário está na página de Vagas, visualizando a lista de vagas "
        "cadastradas da empresa."
    ),
    CanonicalPage.VAGA_DETALHE: (
        "O usuário está visualizando uma vaga específica em detalhe — "
        "ele pode estar olhando descrição, candidatos, pipeline ou métricas."
    ),
    CanonicalPage.RECRUTAR: (
        "O usuário está no fluxo de recrutamento — criando ou editando "
        "uma vaga via wizard."
    ),
    CanonicalPage.FUNIL_TALENTOS: (
        "O usuário está no Funil de Talentos, visualizando candidatos em "
        "todas as etapas do pipeline."
    ),
    CanonicalPage.CANDIDATO_DETALHE: (
        "O usuário está visualizando um candidato específico em detalhe — "
        "perfil, CV, histórico, score ou comunicações."
    ),
    CanonicalPage.PIPELINE_KANBAN: (
        "O usuário está no Kanban do pipeline, visualizando candidatos "
        "agrupados por etapa do processo de seleção."
    ),
    CanonicalPage.DASHBOARD: (
        "O usuário está no dashboard de indicadores — métricas de "
        "recrutamento, conversão, qualidade, eficiência."
    ),
    CanonicalPage.CONFIGURACOES: (
        "O usuário está em Configurações — perfil da empresa, benefícios, "
        "políticas de recrutamento, cultura, integrações."
    ),
    CanonicalPage.AGENT_STUDIO: (
        "O usuário está no Agent Studio — onde configura, treina e gerencia "
        "agentes IA customizados (incluindo a LIA)."
    ),
    CanonicalPage.AJUDA: (
        "O usuário está na página de ajuda / documentação da plataforma."
    ),
    CanonicalPage.BANCOS_TALENTOS: (
        "O usuário está em Bancos de Talentos — listas e segmentações "
        "de candidatos para reativação ou matching futuro."
    ),
    CanonicalPage.BIBLIOTECA: (
        "O usuário está na Biblioteca LIA — templates, prompts, e "
        "artefatos reutilizáveis."
    ),
    CanonicalPage.CENTRAL_COMUNICACAO: (
        "O usuário está na Central de Comunicação — emails, WhatsApp, "
        "templates e histórico de mensagens."
    ),
    CanonicalPage.TASKS: (
        "O usuário está no Centro de Tarefas — pendências, aprovações, "
        "ações que precisam de decisão humana (HITL)."
    ),
    CanonicalPage.CHAT: (
        "O usuário está na página dedicada de chat com a LIA."
    ),
    CanonicalPage.TRUST: (
        "O usuário está no Trust Center — compliance, LGPD, auditoria, "
        "transparência e governança."
    ),
    CanonicalPage.GENERAL: (
        "O usuário não está em uma página específica identificada — "
        "responda de forma genérica e ofereça ajuda navegação."
    ),
}


# Legacy aliases — incoming page_type strings from older frontend code
# or third-party callers. Maps to canonical enum. Add new aliases here
# only when migrating a producer; do NOT introduce NEW vocabularies.
#
# Eventually frontend will only send canonical values and this dict
# becomes a no-op pass-through.
LEGACY_PAGE_ALIASES: dict[str, CanonicalPage] = {
    # Pre-G1 vocabulary from useChatMessages.ts
    "kanban": CanonicalPage.PIPELINE_KANBAN,
    "candidates": CanonicalPage.CANDIDATO_DETALHE,
    "settings_config": CanonicalPage.CONFIGURACOES,
    "job_detail": CanonicalPage.VAGA_DETALHE,
    # Pre-G1 vocabulary from context_adapter.py:PAGE_TO_CONTEXT_TYPE keys
    "sourcing": CanonicalPage.FUNIL_TALENTOS,
    "talent": CanonicalPage.FUNIL_TALENTOS,
    "pipeline": CanonicalPage.PIPELINE_KANBAN,
    "job": CanonicalPage.VAGAS,
    "jobs": CanonicalPage.VAGAS,
    "vacancies": CanonicalPage.VAGAS,
    "wizard": CanonicalPage.RECRUTAR,
    "analytics": CanonicalPage.DASHBOARD,
    "global": CanonicalPage.GENERAL,
}


def normalize_page(raw: str | None) -> CanonicalPage:
    """Map any incoming page string to a CanonicalPage.

    Accepts:
        - Direct canonical values ("vagas", "funil_talentos", ...).
        - Legacy aliases ("kanban", "candidates", "settings_config", ...).
        - None / empty / unknown → CanonicalPage.GENERAL.

    Always returns a valid CanonicalPage — never raises.
    """
    if not raw:
        return CanonicalPage.GENERAL
    raw_norm = raw.strip().lower()
    # Direct canonical value?
    try:
        return CanonicalPage(raw_norm)
    except ValueError:
        pass
    # Legacy alias?
    if raw_norm in LEGACY_PAGE_ALIASES:
        return LEGACY_PAGE_ALIASES[raw_norm]
    return CanonicalPage.GENERAL


def describe_page(page: CanonicalPage | str | None) -> str | None:
    """Return the PT-BR description for a page, or None if GENERAL/unknown.

    The None return signals to the system_prompt_builder that no
    "Localização" section should be added (avoid telling the LLM
    "user is in the general page" which is useless noise).
    """
    canonical = (
        page if isinstance(page, CanonicalPage)
        else normalize_page(page)
    )
    if canonical == CanonicalPage.GENERAL:
        return None
    return PAGE_DESCRIPTIONS_PT_BR.get(canonical)
