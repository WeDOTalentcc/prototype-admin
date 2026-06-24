/**
 * Canonical page vocabulary — single source of truth for chat page context.
 *
 * G1 canonical fix (2026-05-24). Mirror of the Python backend module
 * lia-agent-system/app/shared/canonical_pages.py. Sync changes between
 * both files.
 *
 * Before this, getPageContext() in useChatMessages.ts matched only EN
 * routes (/kanban, /candidat, /dashboard, /agent-studio) and a couple
 * of PT-BR ones (/minha-empresa). Routes like /configuracoes,
 * /funil-de-talentos, /vagas, /recrutar all fell through to undefined
 * page_type → backend treated as "general" → LLM had no page awareness.
 */

/** Canonical page identifiers — must match Python CanonicalPage enum. */
export const CANONICAL_PAGES = {
  HOME: "home",
  VAGAS: "vagas",
  VAGA_DETALHE: "vaga_detalhe",
  RECRUTAR: "recrutar",
  FUNIL_TALENTOS: "funil_talentos",
  CANDIDATO_DETALHE: "candidato_detalhe",
  PIPELINE_KANBAN: "pipeline_kanban",
  DASHBOARD: "dashboard",
  CONFIGURACOES: "configuracoes",
  AGENT_STUDIO: "agent_studio",
  AJUDA: "ajuda",
  BANCOS_TALENTOS: "bancos_talentos",
  BIBLIOTECA: "biblioteca",
  CENTRAL_COMUNICACAO: "central_comunicacao",
  TASKS: "tasks",
  CHAT: "chat",
  TRUST: "trust",
  AGENTS_MARKETPLACE: "agents_marketplace",
  AI_CREDITS: "ai_credits",
  INTEGRACOES_ATS: "integracoes_ats",
  TEMPLATES: "templates",
  MODULOS: "modulos",
  PROJETOS: "projetos",
  GENERAL: "general",
} as const

export type CanonicalPageValue = typeof CANONICAL_PAGES[keyof typeof CANONICAL_PAGES]

/**
 * Map a Next.js pathname to a canonical page identifier.
 *
 * Order matters — more specific patterns first. UUID detail routes
 * (e.g. /jobs/<uuid>) must be matched before list routes (/jobs).
 *
 * Returns CANONICAL_PAGES.GENERAL when no pattern matches. Callers
 * should treat GENERAL as "no useful page context" — the backend
 * skips the Localização section in the system prompt for this value.
 */
export function routeToCanonicalPage(pathname: string): CanonicalPageValue {
  // Strip [locale] prefix (/en/, /pt/, /pt-BR/) so matching works on
  // the meaningful suffix only. Locales are 2-5 chars typically.
  const path = pathname.replace(/^\/[a-z]{2}(-[A-Z]{2})?(\/|$)/, "/")

  // Detail routes (UUID or slug) MUST come before list routes.
  if (/\/jobs\/[a-f0-9-]{8,}/i.test(path)) return CANONICAL_PAGES.VAGA_DETALHE
  if (/\/vagas\/[^/]+/i.test(path)) return CANONICAL_PAGES.VAGA_DETALHE
  if (/\/funil-de-talentos\/candidato\/[^/]+/i.test(path)) return CANONICAL_PAGES.CANDIDATO_DETALHE

  // List / index routes.
  if (path.includes("/jobs") || path.includes("/teams-tab/vagas")) {
    return CANONICAL_PAGES.VAGAS
  }
  if (path.includes("/funil-de-talentos")) return CANONICAL_PAGES.FUNIL_TALENTOS
  if (path.includes("/teams-tab/pipeline") || path.includes("/kanban") || path.includes("/pipeline")) {
    return CANONICAL_PAGES.PIPELINE_KANBAN
  }
  if (path.includes("/teams-tab/candidatos") || path.includes("/candidat")) {
    return CANONICAL_PAGES.CANDIDATO_DETALHE
  }
  if (path.includes("/teams-tab/dashboard") || path.includes("/dashboard") || path.includes("/indicadores")) {
    return CANONICAL_PAGES.DASHBOARD
  }
  if (path.includes("/recrutar")) return CANONICAL_PAGES.RECRUTAR
  // Fase A: ai-credits ANTES de configuracoes (a sub-rota contem o prefixo).
  if (path.includes("/ai-credits")) return CANONICAL_PAGES.AI_CREDITS
  if (path.includes("/integracoes-ats")) return CANONICAL_PAGES.INTEGRACOES_ATS
  if (path.includes("/agents/marketplace") || path.includes("/marketplace")) {
    return CANONICAL_PAGES.AGENTS_MARKETPLACE
  }
  if (path.includes("/configuracoes") || path.includes("/minha-empresa") || path.includes("/company-settings") || path.includes("/settings")) {
    return CANONICAL_PAGES.CONFIGURACOES
  }
  if (path.includes("/agent-studio")) return CANONICAL_PAGES.AGENT_STUDIO
  if (path.includes("/ajuda")) return CANONICAL_PAGES.AJUDA
  if (path.includes("/bancos-de-talentos")) return CANONICAL_PAGES.BANCOS_TALENTOS
  if (path.includes("/biblioteca-lia") || path.includes("/biblioteca")) {
    return CANONICAL_PAGES.BIBLIOTECA
  }
  if (path.includes("/central-comunicacao")) return CANONICAL_PAGES.CENTRAL_COMUNICACAO
  if (path.includes("/tasks") || path.includes("/decidir")) return CANONICAL_PAGES.TASKS
  if (path.includes("/chat")) return CANONICAL_PAGES.CHAT
  if (path.includes("/trust")) return CANONICAL_PAGES.TRUST
  if (path.includes("/projetos")) return CANONICAL_PAGES.PROJETOS

  // Root path of locale (e.g. /pt/) → home dashboard.
  if (path === "/" || path === "") return CANONICAL_PAGES.HOME

  return CANONICAL_PAGES.GENERAL
}

/**
 * Reverse map: canonical page → friendly URL slug (PT-BR routes preferred).
 * Used by chat suggestions ("Ir para Configurações" → navigate to
 * /[locale]/configuracoes).
 *
 * Returns null when the canonical page has no canonical URL (e.g. HOME
 * which is locale-root, or detail pages which require an id).
 */
export function canonicalPageToUrl(page: CanonicalPageValue, locale: string = "pt", id?: string): string | null {
  const base = `/${locale}`
  switch (page) {
    case CANONICAL_PAGES.HOME:                return `${base}/`
    case CANONICAL_PAGES.VAGAS:               return `${base}/jobs`
    case CANONICAL_PAGES.RECRUTAR:            return `${base}/recrutar`
    case CANONICAL_PAGES.FUNIL_TALENTOS:      return `${base}/funil-de-talentos`
    case CANONICAL_PAGES.CONFIGURACOES:       return `${base}/configuracoes`
    case CANONICAL_PAGES.AGENT_STUDIO:        return `${base}/agent-studio`
    case CANONICAL_PAGES.AJUDA:               return `${base}/ajuda`
    case CANONICAL_PAGES.BANCOS_TALENTOS:     return `${base}/bancos-de-talentos`
    case CANONICAL_PAGES.BIBLIOTECA:          return `${base}/biblioteca-lia`
    case CANONICAL_PAGES.CENTRAL_COMUNICACAO: return `${base}/central-comunicacao`
    case CANONICAL_PAGES.TASKS:               return `${base}/tasks`
    case CANONICAL_PAGES.CHAT:                return `${base}/chat`
    case CANONICAL_PAGES.TRUST:               return `${base}/trust`
    case CANONICAL_PAGES.PROJETOS:            return `${base}/projetos`
    // Fase A (2026-06-06): dashboard É a home (DashboardApp); pipeline_kanban
    // → visão global do pipeline (/recrutar = PipelineOverviewPage).
    // Fase A.2: abas SEM rota (in-shell) → deep-link ?view=<label> que o
    // DashboardApp lê e converte em setCurrentPage. dashboard = métricas
    // (aba Indicadores), NÃO a home (que abre em Decidir).
    case CANONICAL_PAGES.DASHBOARD:           return `${base}/?view=Indicadores`
    case CANONICAL_PAGES.TEMPLATES:           return `${base}/?view=Templates`
    case CANONICAL_PAGES.MODULOS:             return `${base}/?view=${encodeURIComponent("Módulos")}`
    case CANONICAL_PAGES.PIPELINE_KANBAN:     return `${base}/recrutar`
    case CANONICAL_PAGES.AGENTS_MARKETPLACE:  return `${base}/agents/marketplace`
    case CANONICAL_PAGES.AI_CREDITS:          return `${base}/configuracoes/ai-credits`
    case CANONICAL_PAGES.INTEGRACOES_ATS:     return `${base}/integracoes-ats`
    // Detail pages: navegáveis SE houver id (mirror do backend
    // [NAVIGATE:page:id]). Sem id não há URL canônica de "land here".
    case CANONICAL_PAGES.VAGA_DETALHE:
      return id ? `${base}/jobs/${id}` : null
    case CANONICAL_PAGES.CANDIDATO_DETALHE:
      return id ? `${base}/funil-de-talentos/candidato/${id}` : null
    // general: sentinel sem URL canônica de navegação direta.
    case CANONICAL_PAGES.GENERAL:
    default:
      return null
  }
}

/**
 * Human-readable PT-BR label for a canonical page. Used in chat UI
 * surfaces ("Você está em: Configurações", page suggestion chips).
 */
export function canonicalPageLabel(page: CanonicalPageValue): string {
  switch (page) {
    case CANONICAL_PAGES.HOME:                return "Início"
    case CANONICAL_PAGES.VAGAS:               return "Vagas"
    case CANONICAL_PAGES.VAGA_DETALHE:        return "Detalhe da Vaga"
    case CANONICAL_PAGES.RECRUTAR:            return "Recrutar"
    case CANONICAL_PAGES.FUNIL_TALENTOS:      return "Funil de Talentos"
    case CANONICAL_PAGES.CANDIDATO_DETALHE:   return "Detalhe do Candidato"
    case CANONICAL_PAGES.PIPELINE_KANBAN:     return "Pipeline Kanban"
    case CANONICAL_PAGES.DASHBOARD:           return "Dashboard"
    case CANONICAL_PAGES.CONFIGURACOES:       return "Configurações"
    case CANONICAL_PAGES.AGENT_STUDIO:        return "Agent Studio"
    case CANONICAL_PAGES.AJUDA:               return "Ajuda"
    case CANONICAL_PAGES.BANCOS_TALENTOS:     return "Bancos de Talentos"
    case CANONICAL_PAGES.BIBLIOTECA:          return "Biblioteca"
    case CANONICAL_PAGES.CENTRAL_COMUNICACAO: return "Central de Comunicação"
    case CANONICAL_PAGES.TASKS:               return "Tarefas"
    case CANONICAL_PAGES.CHAT:                return "Chat"
    case CANONICAL_PAGES.TRUST:               return "Trust Center"
    case CANONICAL_PAGES.PROJETOS:            return "Projetos"
    case CANONICAL_PAGES.AGENTS_MARKETPLACE:  return "Marketplace de Agentes"
    case CANONICAL_PAGES.AI_CREDITS:          return "Créditos de IA"
    case CANONICAL_PAGES.INTEGRACOES_ATS:     return "Integrações ATS"
    case CANONICAL_PAGES.TEMPLATES:           return "Templates"
    case CANONICAL_PAGES.MODULOS:             return "Módulos"
    case CANONICAL_PAGES.GENERAL:             return "Geral"
    default:                                  return "Geral"
  }
}

/**
 * Resultado de navegação com indicador de fallback.
 *
 * `isFallback=true` quando a page era um detalhe sem id e foi feito
 * graceful degradation para a lista pai (VAGAS ou FUNIL_TALENTOS).
 */
export interface CanonicalPageNavResult {
  url: string
  isFallback: boolean
}

/**
 * Como `canonicalPageToUrl`, mas com graceful degradation para páginas de
 * detalhe sem id. Em vez de retornar null, navega para a lista pai:
 *   - vaga_detalhe sem id       -> VAGAS  (/jobs)
 *   - candidato_detalhe sem id  -> FUNIL_TALENTOS (/funil-de-talentos)
 *
 * Retorna `{ url, isFallback }` para que o caller possa sinalizar o
 * usuário quando a navegação não foi exatamente a pedida.
 *
 * Callers que precisam do comportamento ORIGINAL (null para detalhe sem id)
 * devem continuar usando `canonicalPageToUrl`.
 */
export function canonicalPageToUrlWithFallback(
  page: CanonicalPageValue,
  locale: string = "pt",
  id?: string,
): CanonicalPageNavResult | null {
  // Caso normal: id fornecido ou page nao e detalhe — delega ao canonico.
  if (page !== CANONICAL_PAGES.VAGA_DETALHE && page !== CANONICAL_PAGES.CANDIDATO_DETALHE) {
    const url = canonicalPageToUrl(page, locale, id)
    if (!url) return null
    return { url, isFallback: false }
  }

  // Pagina de detalhe com id — resolve normalmente.
  if (id) {
    const url = canonicalPageToUrl(page, locale, id)
    if (!url) return null
    return { url, isFallback: false }
  }

  // Detalhe sem id — graceful degradation para a lista pai.
  if (page === CANONICAL_PAGES.VAGA_DETALHE) {
    const fallbackUrl = canonicalPageToUrl(CANONICAL_PAGES.VAGAS, locale)
    if (!fallbackUrl) return null
    return { url: fallbackUrl, isFallback: true }
  }

  // CANDIDATO_DETALHE sem id -> funil de talentos
  const fallbackUrl = canonicalPageToUrl(CANONICAL_PAGES.FUNIL_TALENTOS, locale)
  if (!fallbackUrl) return null
  return { url: fallbackUrl, isFallback: true }
}
