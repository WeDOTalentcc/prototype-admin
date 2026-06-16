/**
 * Smoke test — ComplianceOverviewPanel (P2-4 audit 2026-05-26).
 */
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ComplianceOverviewPanel } from "@/components/settings/ComplianceOverviewPanel"

describe("ComplianceOverviewPanel — P2-4 dashboard agregador", () => {
  it("renderiza container canonical com testid", () => {
    render(<ComplianceOverviewPanel />)
    expect(screen.getByTestId("compliance-overview-panel")).toBeInTheDocument()
  })

  it("renderiza os 5 cards de métrica canonical", () => {
    render(<ComplianceOverviewPanel />)
    expect(screen.getByTestId("compliance-card-consent")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-dsr")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-audit")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-fairness")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-cross-tenant")).toBeInTheDocument()
  })

  it("mostra titulo visivel da visao geral", () => {
    render(<ComplianceOverviewPanel />)
    expect(screen.getByText(/Visão geral de Compliance/)).toBeInTheDocument()
  })

  it("mostra disclaimer sobre wire-up futuro de API real", () => {
    render(<ComplianceOverviewPanel />)
    expect(screen.getByText(/serão wired no follow-up/)).toBeInTheDocument()
  })

  it("links sao renderizados quando handler passado", () => {
    const noop = () => {}
    render(<ComplianceOverviewPanel onNavigateToSubsection={noop} />)
    expect(screen.getByTestId("compliance-card-link-consent")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-link-dsr")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-link-audit")).toBeInTheDocument()
    expect(screen.getByTestId("compliance-card-link-fairness")).toBeInTheDocument()
  })

  it("cross-tenant card NAO tem link (no subsection target)", () => {
    const noop = () => {}
    render(<ComplianceOverviewPanel onNavigateToSubsection={noop} />)
    expect(screen.queryByTestId("compliance-card-link-cross-tenant")).not.toBeInTheDocument()
  })
})
