// candidates-core.constants.ts
// Pure static data: tab definitions, search templates, LIA tips, default options.
// No React or Next.js imports — safe for Vue/server portability.

import type { PearchSearchOptions } from "./candidates-core.types"

/** Navigation tabs shown above the candidate list */
export const CANDIDATES_TABS = [
  { id: 'search', label: 'Busca' },
  { id: 'favorites', label: 'Favoritos' },
  { id: 'lists', label: 'Listas' },
  { id: 'talent-pools', label: 'Bancos de Talentos' },
  { id: 'saved-searches', label: 'Buscas Salvas' },
  { id: 'history', label: 'Histórico' },
] as const

/** Example search queries shown in the prompt area */
export const SEARCH_TEMPLATES: string[] = [
  "Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python",
  "Frontend Pleno remoto, 3+ anos em startups, React e TypeScript",
  "Product Manager Sênior em Campinas, experiência em B2B SaaS, metodologias ágeis",
  "Data Scientist Pleno híbrido, 4+ anos em e-commerce, Python e machine learning",
  "Tech Lead em São Paulo, 7+ anos em healthtech, liderança de times ágeis",
]

/** Default tips shown in the LIA assistant panel */
export const LIA_ASSISTANT_TIPS_DEFAULT: string[] = [
  "Seja específico sobre habilidades técnicas necessárias",
  "Indique a senioridade desejada (júnior, pleno, sênior)",
  "Mencione localização se for relevante para a vaga",
  "Inclua soft competências importantes para o time",
]

/** Default options for Pearch (global talent) searches */
export const DEFAULT_PEARCH_OPTIONS: PearchSearchOptions = {
  searchType: 'fast',
  limit: 10,  // 10 por pagina: busca rapida + loop de calibracao (Paulo)
  showEmails: false,
  showPhoneNumbers: false,
  highFreshness: false,
  requireEmails: true,  // email padrao: sem email nao ha disparo de triagem (decisao Paulo)
  requirePhoneNumbers: false,
}

/** Preview panel sizing constraints (px) */
export const PREVIEW_WIDTH_DEFAULT = 420
export const PREVIEW_WIDTH_MIN = 280
export const PREVIEW_WIDTH_MAX = 600

/** LIA sidebar default width (px) */
export const LIA_WIDTH_DEFAULT = 400
