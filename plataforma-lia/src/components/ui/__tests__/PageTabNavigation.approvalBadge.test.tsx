/**
 * Wave 0 Fix 3 (2026-05-27) — Approvals badge rendering contract.
 *
 * Pina:
 *   - count 0 → sem badge (DOM não renderiza span)
 *   - count 1..9 → renderiza count exato como string
 *   - count >= 10 → render "9+" via badgeLabel override
 *   - badgeAccent="cyan" aplica classe `bg-lia-cyan`
 *
 * Esse é o caminho canonical pro indicador de pendências de aprovação que
 * sinaliza urgência ao recrutador. Regredir aqui = recrutador perde pendências.
 */
import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"

import { PageTabNavigation } from "../page-tab-navigation"

describe("PageTabNavigation — Approvals badge contract (Wave 0 Fix 3)", () => {
  function _renderTabs(count: number) {
    const badgeLabel = count > 9 ? "9+" : undefined
    return render(
      <PageTabNavigation
        tabs={[
          { id: "my-agents", label: "Meus Agentes" },
          {
            id: "approvals",
            label: "Aprovações",
            count,
            badgeLabel,
            badgeAccent: "cyan",
          },
          { id: "twins", label: "Gêmeos" },
        ]}
        activeTab="my-agents"
        onTabChange={() => {}}
      />
    )
  }

  it("count=0: sem badge renderizado", () => {
    _renderTabs(0)
    // Tab still visible
    expect(screen.getByText("Aprovações")).toBeInTheDocument()
    // Badge value NOT in DOM
    expect(screen.queryByText("0")).not.toBeInTheDocument()
    expect(screen.queryByText("9+")).not.toBeInTheDocument()
  })

  it("count=5: badge exibe '5' exato", () => {
    _renderTabs(5)
    expect(screen.getByText("5")).toBeInTheDocument()
  })

  it("count=9: badge exibe '9' exato", () => {
    _renderTabs(9)
    expect(screen.getByText("9")).toBeInTheDocument()
    expect(screen.queryByText("9+")).not.toBeInTheDocument()
  })

  it("count=10: badge exibe '9+' (limite visual)", () => {
    _renderTabs(10)
    expect(screen.getByText("9+")).toBeInTheDocument()
    expect(screen.queryByText("10")).not.toBeInTheDocument()
  })

  it("count=99: badge exibe '9+' (anti-overflow)", () => {
    _renderTabs(99)
    expect(screen.getByText("9+")).toBeInTheDocument()
    expect(screen.queryByText("99")).not.toBeInTheDocument()
  })

  it("badgeAccent='cyan' aplica classe canonical bg-lia-cyan", () => {
    _renderTabs(3)
    const badge = screen.getByText("3")
    expect(badge.className).toMatch(/bg-lia-cyan/)
  })

  it("count<=9 renderiza o número diretamente (não usa badgeLabel)", () => {
    _renderTabs(7)
    // Confirma comportamento: badgeLabel undefined → fallback no count
    expect(screen.getByText("7")).toBeInTheDocument()
  })
})
