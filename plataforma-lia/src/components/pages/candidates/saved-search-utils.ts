import type { SearchMode, SearchSource } from "@/stores/talent-funnel-store"

export interface SavedSearchInput {
  name: string
  query: string
  mode: SearchMode
  source: SearchSource
  filters?: Record<string, unknown>
}

// P1-7: produtor canonico do payload de Busca Salva. saveCurrentSearch chamava
// sessionStorage("current-search-data") (ninguem lia); agora monta este payload
// e chama talentFunnel.addSavedSearch (que a aba Buscas Salvas consome).
export function buildSavedSearchPayload(args: {
  searchTerm: string
  quickFilters?: string[]
  mode?: SearchMode
  source?: SearchSource
  dateLabel: string
  namePrefix: string
}): SavedSearchInput {
  const { searchTerm, quickFilters = [], mode = "natural", source = "local", dateLabel, namePrefix } = args
  return {
    name: namePrefix + " " + dateLabel,
    query: searchTerm,
    mode,
    source,
    filters: quickFilters.length ? { quickFilters } : undefined,
  }
}
