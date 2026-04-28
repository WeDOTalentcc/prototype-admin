/**
 * Task #904 — smoke test for the Governança tab in Configurações.
 *
 * The hub itself is the thin parent that renders 6 sub-panels (Audit Logs,
 * Bias Audit, Automation Rules, Policy Engine, DSR/LGPD, Consent). Each
 * sub-panel is mocked here so the assertion is focused on the navigation
 * surface — the tabs themselves and the switching behavior — without
 * pulling in 6 fetch-heavy children.
 *
 * Strategy mirrors `WebhooksManager.test.tsx` (Task #895): render the hub
 * directly instead of going through SettingsPageEnhanced, since the page
 * already lazy-loads 9 dynamic chunks.
 */
import React from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { vi, describe, it, expect } from "vitest"

vi.mock("next-intl", () => ({
  useTranslations: (ns?: string) => (key: string) => `${ns ?? ""}.${key}`,
}))

vi.mock("@/components/settings/governance/AuditLogsPanel", () => ({
  AuditLogsPanel: () => <div data-testid="panel-audit-logs" />,
}))
vi.mock("@/components/settings/governance/BiasAuditPanel", () => ({
  BiasAuditPanel: () => <div data-testid="panel-bias-audit" />,
}))
vi.mock("@/components/settings/governance/AutomationRulesPanel", () => ({
  AutomationRulesPanel: () => <div data-testid="panel-automation-rules" />,
}))
vi.mock("@/components/settings/governance/PolicyEnginePanel", () => ({
  PolicyEnginePanel: () => <div data-testid="panel-policy-engine" />,
}))
vi.mock("@/components/settings/governance/DSRInboxPanel", () => ({
  DSRInboxPanel: () => <div data-testid="panel-dsr" />,
}))
vi.mock("@/components/settings/governance/ConsentPanel", () => ({
  ConsentPanel: () => <div data-testid="panel-consent" />,
}))

import { GovernancaHub } from "@/components/settings/governance/GovernancaHub"

describe("GovernancaHub — Task #904", () => {
  it("renders all 6 governance sub-tabs", () => {
    render(<GovernancaHub />)

    const expected = [
      "audit-logs",
      "bias-audit",
      "automation-rules",
      "policy-engine",
      "dsr",
      "consent",
    ]
    for (const id of expected) {
      expect(screen.getByTestId(`governanca-tab-${id}`)).toBeInTheDocument()
    }
    // Default sub-tab is "audit-logs"
    expect(screen.getByTestId("panel-audit-logs")).toBeInTheDocument()
    expect(screen.getByTestId("governanca-tab-audit-logs").getAttribute("aria-selected")).toBe("true")
  })

  it("opens directly on the activeSubsection prop when provided", () => {
    render(<GovernancaHub activeSubsection="dsr" />)
    expect(screen.getByTestId("panel-dsr")).toBeInTheDocument()
    expect(screen.getByTestId("governanca-tab-dsr").getAttribute("aria-selected")).toBe("true")
    expect(screen.queryByTestId("panel-audit-logs")).not.toBeInTheDocument()
  })

  it("switches to the bias audit panel when its tab is clicked", async () => {
    const user = userEvent.setup()
    render(<GovernancaHub />)

    await user.click(screen.getByTestId("governanca-tab-bias-audit"))

    expect(screen.getByTestId("panel-bias-audit")).toBeInTheDocument()
    expect(screen.queryByTestId("panel-audit-logs")).not.toBeInTheDocument()
    expect(screen.getByTestId("governanca-tab-bias-audit").getAttribute("aria-selected")).toBe("true")
  })

  it("switches to the consent panel when its tab is clicked", async () => {
    const user = userEvent.setup()
    render(<GovernancaHub />)

    await user.click(screen.getByTestId("governanca-tab-consent"))

    expect(screen.getByTestId("panel-consent")).toBeInTheDocument()
    expect(screen.getByTestId("governanca-tab-consent").getAttribute("aria-selected")).toBe("true")
  })
})
