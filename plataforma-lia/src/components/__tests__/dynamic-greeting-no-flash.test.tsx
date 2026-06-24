/**
 * dynamic-greeting-no-flash — contrato anti-"piscar" do `useDynamicGreeting`.
 *
 * O hook usa um mount-guard (seed semeado em useEffect): na 1ª pintura
 * (SSR + 1º paint no cliente) retorna EXATAMENTE o `fallback` estático; só
 * após montar troca para a frase dinâmica. Isso evita mismatch de hidratação
 * (a saudação não pode "piscar"/trocar entre server e cliente).
 *
 * Este teste blinda esse contrato nos DOIS consumidores reais:
 *  - `UnifiedChatEmptyState` (empty state do chat)
 *  - `CandidateSearchBar` (herói do Funil de Talentos)
 *
 * Estratégia:
 *  - 1ª pintura → `renderToStaticMarkup` (SSR não roda useEffect → fallback).
 *  - Após mount → `render` do Testing Library (effects rodam → frase dinâmica).
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { renderToStaticMarkup } from "react-dom/server"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

// O hook depende do usuário autenticado e do briefing diário. Sem nome e sem
// briefing, `selectGreeting` cai no caminho "curado plain" → frase = pool[0],
// determinística independente do seed (pool de 1 elemento).
vi.mock("@/contexts/auth-context", () => ({
  useJWTAuth: () => ({ user: null }),
}))
vi.mock("@/hooks/ai/use-daily-briefing", () => ({
  useDailyBriefing: () => ({ briefing: null }),
}))

// Filhos pesados irrelevantes para a saudação — stub mínimo.
vi.mock("@/components/ui/chat-workflow-reels", () => ({
  ChatWorkflowReels: () => null,
}))
vi.mock("@/components/search/smart-search-input", () => ({
  SmartSearchInput: () => null,
}))
vi.mock("@/components/ui/search-loading-animation", () => ({
  SearchLoadingAnimation: () => null,
}))

import { UnifiedChatEmptyState } from "@/components/unified-chat/UnifiedChatEmptyState"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"

const FALLBACK_CHAT = "Olá! Como posso ajudar você hoje?"
const DYNAMIC_CHAT = "FRASE_DINAMICA_DO_CHAT"
const FALLBACK_FUNNEL = "Quem você procura hoje?"
const DYNAMIC_FUNNEL = "FRASE_DINAMICA_DO_FUNIL"

const messages = {
  chat: {
    greeting: FALLBACK_CHAT,
  },
  candidates: {
    searchBar: {
      defaultTitle: FALLBACK_FUNNEL,
      searchingTitle: "Buscando...",
      searchPlaceholder: "Busque candidatos...",
      dropCvHere: "Solte o CV aqui",
      fileFormats: "PDF, DOCX",
      analyzingCv: "Analisando CV...",
    },
    table: {
      loadingAriaLabel: "Carregando",
    },
  },
  dynamicGreetings: {
    chat: { curated: [DYNAMIC_CHAT], curatedNamed: [DYNAMIC_CHAT] },
    funnel: { curated: [DYNAMIC_FUNNEL], curatedNamed: [DYNAMIC_FUNNEL] },
    timeOfDay: { morning: "Bom dia", afternoon: "Boa tarde", evening: "Boa noite" },
  },
}

function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextIntlClientProvider
      locale="pt-BR"
      messages={messages}
      onError={() => {}}
      getMessageFallback={({ key }) => key}
    >
      {children}
    </NextIntlClientProvider>
  )
}

const searchBarProps = {
  isSearchActive: false,
  isDroppingCV: false,
  cvUploadLoading: false,
  searchTerm: "",
  isLoading: false,
  activeFiltersCount: 0,
  searchSource: "internal" as never,
  pearchSearchOptions: { requireEmails: false, requirePhoneNumbers: false },
  onSearchTermChange: vi.fn(),
  onSubmit: vi.fn(async () => {}),
  onDrop: vi.fn(),
  onDragOver: vi.fn(),
  onDragLeave: vi.fn(),
  onOpenFilters: vi.fn(),
  onGoToResults: vi.fn(),
  onSearchSourceChange: vi.fn(),
  onRequireEmailsChange: vi.fn(),
  onRequirePhoneNumbersChange: vi.fn(),
}

describe("useDynamicGreeting — sem piscar (chat empty state)", () => {
  it("1ª pintura (SSR, sem effects) usa o texto de fallback", () => {
    const html = renderToStaticMarkup(
      <Providers>
        <UnifiedChatEmptyState mode="floating" onSuggestionClick={vi.fn()} />
      </Providers>,
    )
    expect(html).toContain(FALLBACK_CHAT)
    expect(html).not.toContain(DYNAMIC_CHAT)
  })

  it("após mount (effects rodam) troca para a frase dinâmica", () => {
    render(
      <Providers>
        <UnifiedChatEmptyState mode="floating" onSuggestionClick={vi.fn()} />
      </Providers>,
    )
    expect(screen.getByText(DYNAMIC_CHAT)).toBeInTheDocument()
    expect(screen.queryByText(FALLBACK_CHAT)).not.toBeInTheDocument()
  })
})

describe("useDynamicGreeting — sem piscar (herói do Funil)", () => {
  it("1ª pintura (SSR, sem effects) usa o título de fallback", () => {
    const html = renderToStaticMarkup(
      <Providers>
        <CandidateSearchBar {...searchBarProps} />
      </Providers>,
    )
    expect(html).toContain(FALLBACK_FUNNEL)
    expect(html).not.toContain(DYNAMIC_FUNNEL)
  })

  it("após mount (effects rodam) troca para a frase dinâmica", () => {
    render(
      <Providers>
        <CandidateSearchBar {...searchBarProps} />
      </Providers>,
    )
    expect(screen.getByText(DYNAMIC_FUNNEL)).toBeInTheDocument()
    expect(screen.queryByText(FALLBACK_FUNNEL)).not.toBeInTheDocument()
  })
})
