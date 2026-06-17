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
    AGENTS_MARKETPLACE = "agents_marketplace"  # marketplace de agentes IA
    AI_CREDITS = "ai_credits"                # créditos de IA (sub de config)
    INTEGRACOES_ATS = "integracoes_ats"      # integrações com ATS externos
    TEMPLATES = "templates"                  # biblioteca de templates (in-shell)
    MODULOS = "modulos"                      # módulos / planos (in-shell)
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
    CanonicalPage.AGENTS_MARKETPLACE: (
        "O usuário está no Marketplace de Agentes — onde descobre e instala agentes IA prontos para a plataforma."
    ),
    CanonicalPage.AI_CREDITS: (
        "O usuário está em Créditos de IA (dentro de Configurações) — saldo, consumo e compra de créditos para os agentes."
    ),
    CanonicalPage.INTEGRACOES_ATS: (
        "O usuário está em Integrações ATS — conexão com sistemas de recrutamento externos (importação de vagas e candidatos)."
    ),
    CanonicalPage.TEMPLATES: (
        "O usuário está na página de Templates — modelos reutilizáveis de email, descrição de vaga e critérios de avaliação."
    ),
    CanonicalPage.MODULOS: (
        "O usuário está na página de Módulos — planos, licenças e recursos contratados da plataforma."
    ),
    CanonicalPage.GENERAL: (
        "O usuário não está em uma página específica identificada — "
        "responda de forma genérica e ofereça ajuda navegação."
    ),
}


# Short labels for compact navigation lists in chat prompts (G3).
# Distinct from PAGE_DESCRIPTIONS_PT_BR which is contextual sentence form.
# Sprint 3 (2026-05-24): canonical for SystemPromptBuilder G3 navigation list.
PAGE_SHORT_LABELS_PT_BR: dict[CanonicalPage, str] = {
    CanonicalPage.HOME: "dashboard / página inicial",
    CanonicalPage.VAGAS: "lista de vagas",
    CanonicalPage.VAGA_DETALHE: "detalhe de uma vaga (precisa do contexto da vaga)",
    CanonicalPage.RECRUTAR: "wizard de criação de vaga",
    CanonicalPage.FUNIL_TALENTOS: "funil de talentos",
    CanonicalPage.CANDIDATO_DETALHE: "detalhe de um candidato (precisa do contexto)",
    CanonicalPage.PIPELINE_KANBAN: "kanban do pipeline",
    CanonicalPage.DASHBOARD: "dashboard / indicadores",
    CanonicalPage.CONFIGURACOES: "configurações da empresa",
    CanonicalPage.AGENT_STUDIO: "Agent Studio",
    CanonicalPage.AJUDA: "ajuda / documentação",
    CanonicalPage.BANCOS_TALENTOS: "bancos de talentos",
    CanonicalPage.BIBLIOTECA: "biblioteca LIA",
    CanonicalPage.CENTRAL_COMUNICACAO: "central de comunicação",
    CanonicalPage.TASKS: "centro de tarefas",
    CanonicalPage.CHAT: "chat dedicado",
    CanonicalPage.TRUST: "trust center",
    CanonicalPage.AGENTS_MARKETPLACE: "marketplace de agentes",
    CanonicalPage.AI_CREDITS: "créditos de IA",
    CanonicalPage.INTEGRACOES_ATS: "integrações ATS",
    CanonicalPage.TEMPLATES: "templates",
    CanonicalPage.MODULOS: "módulos / planos",
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



# ---------------------------------------------------------------------------
# Sprint 14.4 (2026-05-24): page-aware dynamic suggested prompts.
# ---------------------------------------------------------------------------
# Antes: backend retornava `suggested_prompts` mas mostly hardcoded e
# repetitivo ("Como estão as vagas?" em tudo). Sprint 14.4 introduz um
# dict canonical mapeando CanonicalPage → 3-4 prompts altamente relevantes
# para aquela página.
#
# Uso: MainOrchestrator chama `suggested_prompts_for_page(context_page)`
# quando `ChatResponse.suggested_prompts` está vazio. Surfaces (chat float,
# unified-chat, kanban) já renderizam suggested_prompts como bubbles.
#
# Princípio: prompts são QUERIES que o user provavelmente faria DAQUELA
# página — não comandos genéricos. Variam por contexto.

PAGE_SUGGESTED_PROMPTS_PT_BR: dict[CanonicalPage, list[str]] = {
    CanonicalPage.HOME: [
        "O que preciso resolver hoje?",
        "Quais vagas precisam de atenção?",
        "Mostra meus indicadores principais",
    ],
    CanonicalPage.VAGAS: [
        "Quais vagas estão paradas há mais de 7 dias?",
        "Criar nova vaga",
        "Filtrar por departamento",
        "Comparar performance por vaga",
    ],
    CanonicalPage.VAGA_DETALHE: [
        "Ver pipeline desta vaga",
        "Quem são os top 3 candidatos?",
        "Status da triagem",
        "Editar requisitos",
    ],
    CanonicalPage.RECRUTAR: [
        "Continuar criação da vaga",
        "Gerar JD com IA",
        "Definir critérios de calibração",
        "Configurar triagem WSI",
    ],
    CanonicalPage.FUNIL_TALENTOS: [
        "Quais candidatos estão na etapa de entrevista?",
        "Mover candidatos por critério",
        "Buscar candidatos com perfil similar",
        "Ver gargalos do funil",
    ],
    CanonicalPage.CANDIDATO_DETALHE: [
        "Analisar match com vaga atual",
        "Resumir histórico do candidato",
        "Próxima etapa sugerida",
        "Enviar comunicação",
    ],
    CanonicalPage.PIPELINE_KANBAN: [
        "Mover candidato",
        "Quais estão prontos pra próxima etapa?",
        "Estatísticas do pipeline",
        "Filtrar por status",
    ],
    CanonicalPage.DASHBOARD: [
        "Como está o tempo médio de contratação?",
        "Comparar performance mês anterior",
        "Onde estão os gargalos?",
        "Exportar relatório",
    ],
    CanonicalPage.CONFIGURACOES: [
        "Atualizar perfil da empresa",
        "Configurar políticas de recrutamento",
        "Adicionar benefícios",
        "Conectar integração",
    ],
    CanonicalPage.AGENT_STUDIO: [
        "Criar novo agente",
        "Configurar deploy em vaga",
        "Ver agentes ativos",
        "Análise de uso",
    ],
    CanonicalPage.AJUDA: [
        "Como criar uma vaga?",
        "Como funciona a triagem WSI?",
        "Como configurar minha empresa?",
        "Contatar suporte",
    ],
    CanonicalPage.BANCOS_TALENTOS: [
        "Buscar candidatos no banco",
        "Criar novo banco de talentos",
        "Adicionar candidatos manualmente",
        "Comparar bancos por perfil",
    ],
    CanonicalPage.BIBLIOTECA: [
        "Templates de email",
        "Modelos de descrição de vaga",
        "Critérios de avaliação salvos",
        "Importar template",
    ],
    CanonicalPage.CENTRAL_COMUNICACAO: [
        "Enviar comunicação em massa",
        "Ver histórico de comunicações",
        "Templates aprovados",
        "Configurar canais ativos",
    ],
    CanonicalPage.TASKS: [
        "Quais tarefas urgentes?",
        "O que delegar hoje?",
        "Histórico de decisões",
        "Configurar lembretes",
    ],
    CanonicalPage.CHAT: [
        "Mostrar histórico desta conversa",
        "Limpar contexto",
        "Configurações da LIA",
    ],
    CanonicalPage.TRUST: [
        "Status de conformidade LGPD",
        "Auditoria recente",
        "Configurar política de retenção",
        "Solicitações pendentes",
    ],
    CanonicalPage.AGENTS_MARKETPLACE: [
        "Quais agentes posso instalar?",
        "Recomende um agente pra triagem",
        "Ver agentes mais usados",
    ],
    CanonicalPage.AI_CREDITS: [
        "Qual meu saldo de créditos?",
        "Onde estou gastando mais créditos?",
        "Comprar mais créditos",
    ],
    CanonicalPage.INTEGRACOES_ATS: [
        "Conectar um novo ATS",
        "Status das integrações ativas",
        "Importar vagas do ATS",
    ],
    CanonicalPage.TEMPLATES: [
        "Ver templates de email",
        "Criar novo template",
        "Modelos de descrição de vaga",
    ],
    CanonicalPage.MODULOS: [
        "Quais módulos tenho ativos?",
        "O que está incluído no meu plano?",
    ],
    # GENERAL intencionalmente AUSENTE — função retorna [] quando page=GENERAL
    # para evitar prompts genéricos sem contexto útil.
}


def suggested_prompts_for_page(
    page: CanonicalPage | str | None,
    limit: int = 3,
) -> list[str]:
    """Retorna prompts canonical sugeridos para uma página.

    Args:
        page: CanonicalPage enum, raw string (ex: "vagas") ou None.
        limit: máximo de prompts a retornar (default 3, máximo 4 disponíveis).

    Returns:
        Lista de prompts em PT-BR (até `limit`). Vazia quando page=GENERAL,
        unknown, ou None — sinaliza ao caller que não deve mostrar bubble
        de sugestões pra essa página.

    Uso canonical em MainOrchestrator: chamar quando ChatResponse.suggested_prompts
    está vazio e ctx.context_page é conhecido — populate dinâmicamente.
    """
    canonical = (
        page if isinstance(page, CanonicalPage)
        else normalize_page(page)
    )
    if canonical == CanonicalPage.GENERAL:
        return []
    prompts = PAGE_SUGGESTED_PROMPTS_PT_BR.get(canonical, [])
    if limit > 0:
        return prompts[:limit]
    return list(prompts)