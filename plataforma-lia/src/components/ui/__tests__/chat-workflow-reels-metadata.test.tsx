/**
 * PR-A — Rail A metadata routing
 *
 * Cobre o fix de FE-H03 (audit enterprise 2026-04-26): ao clicar num card do
 * Rail A, o `onSelect` deve receber `(command, metadata)` onde `metadata`
 * carrega `source: "rail_a"`, `card_id`, `stage`, `domain_hint` e `intent_hint`.
 *
 * Esses hints são consumidos pelo orchestrator (`main_orchestrator.py`)
 * como **guide computacional** (per harness-engineering): rota determinística
 * para o domínio/action correto antes do fallback keyword-based.
 *
 * Skill: lia-testing PARTE 1 (TDD red→green) + harness-engineering (guide).
 */

import { describe, it, expect, vi, beforeAll } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

// jsdom não implementa matchMedia — mock global p/ useDockMagnifier (prefers-reduced-motion).
beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }),
    })
  }
  // ResizeObserver tampouco existe — stub mínimo.
  if (typeof window !== "undefined" && !(window as unknown as { ResizeObserver?: unknown }).ResizeObserver) {
    ;(window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
})
import {
  ChatWorkflowReels,
  buildSuggestionMetadata,
  SUGGESTION_HINTS,
  type ChatSuggestionMetadata,
} from "../chat-workflow-reels"

// ─── Messages mínimos para next-intl ─────────────────────────────────────
const messages = {
  chat: {
    workflowReels: {
      scrollLeft: "Rolar para esquerda",
      scrollRight: "Rolar para direita",
      stages: {
        "definir-vaga": { label: "Definir Vaga", shortLabel: "Vaga" },
        "sourcing": { label: "Captação", shortLabel: "Captação" },
        "triagem": { label: "Triagem", shortLabel: "Triagem" },
        "entrevista": { label: "Entrevista", shortLabel: "Entrevista" },
        "oferta": { label: "Oferta", shortLabel: "Oferta" },
        "contratacao": { label: "Contratação", shortLabel: "Contratação" },
        "analytics": { label: "Análises", shortLabel: "Análises" },
        "ia-automacoes": { label: "IA & Automações", shortLabel: "IA" },
        "configuracoes": { label: "Configurações", shortLabel: "Config" },
      },
      suggestions: {
        "create-job": { title: "Criar nova vaga", description: "...", command: "Criar uma nova vaga" },
        "job-template": { title: "Usar modelo", description: "...", command: "Criar vaga a partir de template" },
        "search-candidates": { title: "Buscar", description: "...", command: "Buscar candidatos" },
        "add-candidate": { title: "Adicionar", description: "...", command: "Adicione novo candidato" },
        "talent-pool": { title: "Banco", description: "...", command: "Mostrar meus bancos de talentos" },
        "candidate-info": { title: "Consultar", description: "...", command: "Consulte informações sobre candidato" },
        "update-status": { title: "Status", description: "...", command: "Atualize status do candidato" },
        "schedule-interview": { title: "Agendar", description: "...", command: "Agendar uma entrevista" },
        "reschedule-interview": { title: "Reagendar", description: "...", command: "Reagende uma entrevista" },
        "send-offer": { title: "Proposta", description: "...", command: "Enviar proposta para candidato" },
        "compare-candidates": { title: "Comparar", description: "...", command: "Comparar candidatos finalistas" },
        "register-hire": { title: "Registrar", description: "...", command: "Registrar contratação de candidato" },
        "close-vacancy": { title: "Encerrar", description: "...", command: "Encerrar vaga" },
        "job-report": { title: "Relatório", description: "...", command: "Gerar relatório da vaga" },
        "daily-briefing": { title: "Briefing", description: "...", command: "Me dê o briefing de hoje" },
        "hiring-predictions": { title: "Previsões", description: "...", command: "Mostrar previsões de contratação" },
        "configure-automations": { title: "Automações", description: "...", command: "Configurar automações de recrutamento" },
        "wsi-screening": { title: "WSI", description: "...", command: "Iniciar triagem WSI para candidatos" },
        "ai-suggestions": { title: "Sugestões", description: "...", command: "O que você sugere para minhas vagas?" },
        "ai-credits": { title: "Créditos", description: "...", command: "Verificar meus créditos de IA" },
        "hiring-policy": { title: "Política", description: "...", command: "Configurar política de contratação" },
        "email-templates": { title: "Templates", description: "...", command: "Gerenciar templates de email" },
      },
    },
    greeting: "Como posso ajudar hoje?",
    suggestionCount: "{label} — {count} sugestões",
    pulseBadge: "{count} candidatos",
  },
}

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  )
}

// ─── Pure function: buildSuggestionMetadata ──────────────────────────────

describe("buildSuggestionMetadata — pure metadata constructor", () => {
  it("monta metadata completa para card 1.1 (create-job)", () => {
    expect(buildSuggestionMetadata("create-job", "definir-vaga")).toEqual({
      source: "rail_a",
      card_id: "create-job",
      stage: "definir-vaga",
      domain_hint: "job_management",
      intent_hint: "create_job",
    } satisfies ChatSuggestionMetadata)
  })

  it("monta metadata para card 6.2 (close-vacancy)", () => {
    expect(buildSuggestionMetadata("close-vacancy", "contratacao")).toEqual({
      source: "rail_a",
      card_id: "close-vacancy",
      stage: "contratacao",
      domain_hint: "job_management",
      intent_hint: "close_job",
    })
  })

  it("monta metadata para card utilitário 9.2 (hiring-policy)", () => {
    expect(buildSuggestionMetadata("hiring-policy", "configuracoes")).toEqual({
      source: "rail_a",
      card_id: "hiring-policy",
      stage: "configuracoes",
      domain_hint: "hiring_policy",
      intent_hint: "configure_policy",
    })
  })

  it("retorna metadata sem hints quando card não tem mapeamento (defensivo)", () => {
    const m = buildSuggestionMetadata("unknown-card", "definir-vaga")
    expect(m.source).toBe("rail_a")
    expect(m.card_id).toBe("unknown-card")
    expect(m.stage).toBe("definir-vaga")
    expect(m.domain_hint).toBeUndefined()
    expect(m.intent_hint).toBeUndefined()
  })
})

// ─── Cobertura completa: 22 cards × hints válidos ────────────────────────

describe("SUGGESTION_HINTS — completude do mapa de 22 cards", () => {
  const expectedCards = [
    // Funil (13)
    { id: "create-job",           domain: "job_management",      intent: "create_job" },
    { id: "job-template",         domain: "job_management",      intent: "create_from_template" },
    { id: "search-candidates",    domain: "sourcing",            intent: "search_candidates" },
    { id: "add-candidate",        domain: "sourcing",            intent: "add_candidate" },
    { id: "talent-pool",          domain: "talent_pool",         intent: "list_talent_pools" },
    { id: "candidate-info",       domain: "recruiter_assistant", intent: "quick_question" },
    { id: "update-status",        domain: "pipeline",            intent: "move_candidate" },
    { id: "schedule-interview",   domain: "interview_scheduling", intent: "schedule_interview" },
    { id: "reschedule-interview", domain: "interview_scheduling", intent: "reschedule_interview" },
    { id: "send-offer",           domain: "communication",       intent: undefined }, // P0: action a criar em PR-B
    { id: "compare-candidates",   domain: "sourcing",            intent: "compare_candidates" },
    { id: "register-hire",        domain: "pipeline",            intent: "move_candidate" }, // PR-C dará ação dedicada
    { id: "close-vacancy",        domain: "job_management",      intent: "close_job" },
    // Utilitárias (9)
    { id: "job-report",           domain: "analytics",           intent: "generate_job_report" },
    { id: "daily-briefing",       domain: "recruiter_assistant", intent: "daily_briefing" },
    { id: "hiring-predictions",   domain: "analytics",           intent: "forecast" },
    { id: "configure-automations", domain: "automation",         intent: "create_automation" },
    { id: "wsi-screening",        domain: "interview_scheduling", intent: "start_wsi_interview" },
    { id: "ai-suggestions",       domain: "recruiter_assistant", intent: "suggest_action" },
    { id: "ai-credits",           domain: "agent_studio",        intent: "get_studio_consumption" },
    { id: "hiring-policy",        domain: "hiring_policy",       intent: "configure_policy" },
    { id: "email-templates",      domain: "communication",       intent: "create_template" },
  ]

  it("tem entrada para os 22 cards do Rail A", () => {
    expect(Object.keys(SUGGESTION_HINTS)).toHaveLength(22)
  })

  it.each(expectedCards)(
    "card $id roteia para domain=$domain intent=$intent",
    ({ id, domain, intent }) => {
      const hint = SUGGESTION_HINTS[id]
      expect(hint).toBeDefined()
      expect(hint.domain_hint).toBe(domain)
      expect(hint.intent_hint).toBe(intent)
    },
  )
})

// ─── Integração: click envia metadata via onSelect ───────────────────────

describe("ChatWorkflowReels — onSelect recebe (command, metadata)", () => {
  it("clique no card 'Criar nova vaga' chama onSelect com metadata correta", () => {
    const onSelect = vi.fn()
    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />)

    // Stage "Vaga" é o primeiro com sugestões → ativo por default.
    // Card "Criar nova vaga" aparece no painel inferior.
    const card = screen.getByRole("button", { name: /Criar nova vaga/i })
    fireEvent.click(card)

    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(
      "Criar uma nova vaga",
      expect.objectContaining({
        source: "rail_a",
        card_id: "create-job",
        stage: "definir-vaga",
        domain_hint: "job_management",
        intent_hint: "create_job",
      }),
    )
  })

  it("modo compact também envia metadata", () => {
    const onSelect = vi.fn()
    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} compact />)

    const card = screen.getByRole("button", { name: /Criar nova vaga/i })
    fireEvent.click(card)

    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(
      "Criar uma nova vaga",
      expect.objectContaining({
        source: "rail_a",
        card_id: "create-job",
        stage: "definir-vaga",
      }),
    )
  })
})
