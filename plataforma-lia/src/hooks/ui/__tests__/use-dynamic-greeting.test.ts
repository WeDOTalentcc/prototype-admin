/**
 * use-dynamic-greeting.test.ts — renderização contextual do hook (Task #1319).
 *
 * `selectGreeting` (lógica pura) já tem cobertura em
 * `src/lib/dynamic-greeting.test.ts`. Aqui blindamos a OUTRA metade: a
 * renderização real através do hook — interpolação das contagens do briefing
 * diário e do nome nos templates ICU de `next-intl`. Uma quebra de chave i18n
 * ou de placeholder (`{interviews}`, `{count}`, `{jobs}`…) passaria despercebida
 * pelo teste puro, mas falha aqui.
 *
 * Estratégia: mock de `useJWTAuth` + `useDailyBriefing` (estado mutável por
 * teste), `NextIntlClientProvider` com os templates REAIS de pt-BR, e assert no
 * texto final renderizado contendo as contagens corretas.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import * as React from "react"

type MockUser = { name: string } | null
type MockBriefing = {
  pipeline_summary: {
    active_jobs: number
    candidates_to_contact: number
    awaiting_feedback: number
    offers_pending: number
  }
  metrics: { interviews_today: number }
} | null

let mockUser: MockUser = null
let mockBriefing: MockBriefing = null

vi.mock("@/contexts/auth-context", () => ({
  useJWTAuth: () => ({ user: mockUser }),
}))
vi.mock("@/hooks/ai/use-daily-briefing", () => ({
  useDailyBriefing: () => ({ briefing: mockBriefing }),
}))

import { useDynamicGreeting } from "../use-dynamic-greeting"
import type { GreetingSurface } from "@/lib/dynamic-greeting"

// Templates REAIS de pt-BR (messages/pt-BR.json → dynamicGreetings).
const messages = {
  dynamicGreetings: {
    timeOfDay: { morning: "Bom dia", afternoon: "Boa tarde", evening: "Boa noite" },
    chat: {
      curated: ["Como posso ajudar hoje?"],
      curatedNamed: ["Por onde começamos?"],
      context: {
        interviewsAndFeedback:
          "{greeting}, {name}. Você tem {interviews, plural, one {# entrevista} other {# entrevistas}} hoje e {feedback, plural, one {# candidato aguardando} other {# candidatos aguardando}} retorno.",
        interviewsToday:
          "{greeting}, {name}. Você tem {count, plural, one {# entrevista} other {# entrevistas}} hoje.",
        candidatesToContact:
          "{greeting}, {name}. {count, plural, one {# candidato precisa} other {# candidatos precisam}} de contato hoje.",
        offersPending:
          "{greeting}, {name}. {count, plural, one {# proposta aguarda} other {# propostas aguardam}} sua decisão.",
        allClear: "{greeting}, {name}. Tudo em dia. Vamos adiantar algo?",
      },
    },
    funnel: {
      curated: ["Quem você procura hoje?"],
      context: {
        openJobsAndContacts:
          "Você tem {jobs, plural, one {# vaga aberta} other {# vagas abertas}} e {contacts, plural, one {# candidato a contatar} other {# candidatos a contatar}}. Por onde começamos?",
        openJobs:
          "Você tem {count, plural, one {# vaga aberta} other {# vagas abertas}}. Quer que eu encontre candidatos?",
        candidatesToContact:
          "{count, plural, one {# candidato aguarda} other {# candidatos aguardam}} contato. Ou busque um novo perfil.",
      },
    },
  },
}

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(
    NextIntlClientProvider,
    { locale: "pt-BR", messages, onError: () => {}, getMessageFallback: ({ key }) => key },
    children,
  )
}

function renderGreeting(surface: GreetingSurface, fallback: string): string {
  const { result } = renderHook(() => useDynamicGreeting(surface, fallback), { wrapper })
  return result.current
}

function emptyBriefing(): MockBriefing {
  return {
    pipeline_summary: {
      active_jobs: 0,
      candidates_to_contact: 0,
      awaiting_feedback: 0,
      offers_pending: 0,
    },
    metrics: { interviews_today: 0 },
  }
}

beforeEach(() => {
  mockUser = null
  mockBriefing = null
})
afterEach(() => {
  vi.clearAllMocks()
})

describe("useDynamicGreeting — chat contextual interpolado", () => {
  it("entrevistas + feedback: interpola ambas as contagens e o nome", () => {
    mockUser = { name: "Ana" }
    mockBriefing = emptyBriefing()
    mockBriefing!.metrics.interviews_today = 3
    mockBriefing!.pipeline_summary.awaiting_feedback = 2

    const phrase = renderGreeting("chat", "fallback")
    expect(phrase).toContain("Ana")
    expect(phrase).toContain("3 entrevistas hoje")
    expect(phrase).toContain("2 candidatos aguardando")
  })

  it("só entrevistas: interpola a contagem de entrevistas", () => {
    mockUser = { name: "Ana" }
    mockBriefing = emptyBriefing()
    mockBriefing!.metrics.interviews_today = 3

    const phrase = renderGreeting("chat", "fallback")
    expect(phrase).toContain("3 entrevistas hoje")
    expect(phrase).not.toContain("aguardando")
  })

  it("só candidatos a contatar: interpola a contagem de candidatos", () => {
    mockUser = { name: "Ana" }
    mockBriefing = emptyBriefing()
    mockBriefing!.pipeline_summary.candidates_to_contact = 4

    const phrase = renderGreeting("chat", "fallback")
    expect(phrase).toContain("4 candidatos precisam de contato hoje")
  })

  it("all-clear: briefing zerado com nome rende a frase de tudo em dia", () => {
    mockUser = { name: "Ana" }
    mockBriefing = emptyBriefing()

    const phrase = renderGreeting("chat", "fallback")
    expect(phrase).toContain("Ana")
    expect(phrase).toContain("Tudo em dia")
    expect(phrase).not.toBe("fallback")
  })

  it("plural=one: 1 entrevista usa a forma singular do template", () => {
    mockUser = { name: "Ana" }
    mockBriefing = emptyBriefing()
    mockBriefing!.metrics.interviews_today = 1

    const phrase = renderGreeting("chat", "fallback")
    expect(phrase).toContain("1 entrevista hoje")
    expect(phrase).not.toContain("entrevistas")
  })
})

describe("useDynamicGreeting — funnel contextual interpolado", () => {
  it("vagas abertas + candidatos a contatar: interpola ambas as contagens", () => {
    mockBriefing = emptyBriefing()
    mockBriefing!.pipeline_summary.active_jobs = 2
    mockBriefing!.pipeline_summary.candidates_to_contact = 5

    const phrase = renderGreeting("funnel", "fallback")
    expect(phrase).toContain("2 vagas abertas")
    expect(phrase).toContain("5 candidatos a contatar")
  })

  it("só vagas abertas: interpola a contagem de vagas", () => {
    mockBriefing = emptyBriefing()
    mockBriefing!.pipeline_summary.active_jobs = 1

    const phrase = renderGreeting("funnel", "fallback")
    expect(phrase).toContain("1 vaga aberta")
  })
})
