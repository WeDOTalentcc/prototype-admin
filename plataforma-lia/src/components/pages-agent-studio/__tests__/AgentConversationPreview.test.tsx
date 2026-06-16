/**
 * Fase 3 Sprint 2 — AgentConversationPreview canonical tests.
 *
 * Cobre: renderiza turnos, distingue candidate/agent, compact vs full,
 * lookup por slug + fallback por categoria, white-label (sem cyan no DOM/class),
 * a11y (role=list + aria-label).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, within } from "@testing-library/react"

import { AgentConversationPreview } from "../AgentConversationPreview"
import {
  getSampleConversation,
  CURATED_CONVERSATION_SLUGS,
} from "@/lib/agents/sample-conversations"

// next-intl: t() ecoa a key; useLocale fixa "pt".
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => {
    const map: Record<string, string> = {
      agentRole: "Agente",
      candidateRole: "Candidato",
      ariaLabel: "Exemplo de conversa",
      turnFrom: "Mensagem de",
    }
    return map[key] ?? key
  },
  useLocale: () => "pt",
}))

describe("AgentConversationPreview", () => {
  it("renderiza turnos explícitos em ordem", () => {
    render(
      <AgentConversationPreview
        turns={[
          { role: "candidate", text: "Tenho 5 anos com Python." },
          { role: "agent", text: "Perfil forte. Recomendo avançar." },
        ]}
      />,
    )
    expect(screen.getByText("Tenho 5 anos com Python.")).toBeInTheDocument()
    expect(
      screen.getByText("Perfil forte. Recomendo avançar."),
    ).toBeInTheDocument()
  })

  it("distingue balão de candidato e de agente via data-testid", () => {
    render(
      <AgentConversationPreview
        turns={[
          { role: "candidate", text: "Olá" },
          { role: "agent", text: "Analisei seu perfil" },
        ]}
      />,
    )
    expect(
      screen.getByTestId("conversation-turn-candidate"),
    ).toBeInTheDocument()
    expect(screen.getByTestId("conversation-turn-agent")).toBeInTheDocument()
  })

  it("mostra rótulos traduzidos Candidato/Agente", () => {
    render(
      <AgentConversationPreview
        turns={[
          { role: "candidate", text: "Olá" },
          { role: "agent", text: "Oi" },
        ]}
      />,
    )
    const candidate = screen.getByTestId("conversation-turn-candidate")
    const agent = screen.getByTestId("conversation-turn-agent")
    expect(within(candidate).getByText("Candidato")).toBeInTheDocument()
    expect(within(agent).getByText("Agente")).toBeInTheDocument()
  })

  it("usa agentName white-label quando fornecido", () => {
    render(
      <AgentConversationPreview
        agentName="Nina"
        turns={[{ role: "agent", text: "Oi" }]}
      />,
    )
    const agent = screen.getByTestId("conversation-turn-agent")
    expect(within(agent).getByText("Nina")).toBeInTheDocument()
  })

  it("compact limita a 2 turnos e marca data-compact", () => {
    render(<AgentConversationPreview slug="tpl-triagem-tech" compact />)
    const root = screen.getByTestId("agent-conversation-preview")
    expect(root.getAttribute("data-compact")).toBe("true")
    const turns = within(root).getAllByRole("listitem")
    expect(turns.length).toBe(2)
  })

  it("full renderiza 3+ turnos do diálogo curado", () => {
    render(<AgentConversationPreview slug="tpl-triagem-tech" />)
    const root = screen.getByTestId("agent-conversation-preview")
    const turns = within(root).getAllByRole("listitem")
    expect(turns.length).toBeGreaterThanOrEqual(3)
  })

  it("faz fallback por categoria quando slug não tem diálogo curado", () => {
    render(
      <AgentConversationPreview slug="tpl-inexistente" category="sourcing" />,
    )
    const root = screen.getByTestId("agent-conversation-preview")
    expect(within(root).getAllByRole("listitem").length).toBeGreaterThan(0)
  })

  it("a11y: lista semântica com aria-label", () => {
    render(
      <AgentConversationPreview turns={[{ role: "agent", text: "Oi" }]} />,
    )
    const list = screen.getByRole("list", { name: "Exemplo de conversa" })
    expect(list).toBeInTheDocument()
  })

  it("white-label: nenhuma classe wedo-cyan no DOM (cyan reservado à assistente)", () => {
    const { container } = render(
      <AgentConversationPreview slug="tpl-triagem-tech" />,
    )
    expect(container.innerHTML).not.toMatch(/wedo-cyan/)
  })

  it("não renderiza nada quando não há turnos", () => {
    render(<AgentConversationPreview turns={[]} />)
    expect(
      screen.queryByTestId("agent-conversation-preview"),
    ).not.toBeInTheDocument()
  })
})

describe("getSampleConversation (data)", () => {
  it("retorna diálogo curado por slug", () => {
    const turns = getSampleConversation({ slug: "tpl-triagem-tech", locale: "pt" })
    expect(turns.length).toBeGreaterThanOrEqual(3)
    expect(turns[0].role).toBe("candidate")
  })

  it("retorna versão en quando locale=en", () => {
    const turns = getSampleConversation({ slug: "tpl-triagem-tech", locale: "en" })
    expect(turns[0].text).toMatch(/Python/)
  })

  it("compact trunca a 2 turnos", () => {
    const turns = getSampleConversation({
      slug: "tpl-triagem-tech",
      locale: "pt",
      compact: true,
    })
    expect(turns.length).toBe(2)
  })

  it("fallback general nunca retorna vazio", () => {
    const turns = getSampleConversation({ slug: null, category: null, locale: "pt" })
    expect(turns.length).toBeGreaterThan(0)
  })

  it("todos os slugs curados têm pt e en não-vazios", () => {
    for (const slug of CURATED_CONVERSATION_SLUGS) {
      const pt = getSampleConversation({ slug, locale: "pt" })
      const en = getSampleConversation({ slug, locale: "en" })
      expect(pt.length).toBeGreaterThanOrEqual(2)
      expect(en.length).toBeGreaterThanOrEqual(2)
    }
  })
})
