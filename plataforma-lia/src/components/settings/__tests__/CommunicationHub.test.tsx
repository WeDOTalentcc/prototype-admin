/**
 * Smoke tests — CommunicationHub
 *
 * Verifica que o hub monta e não lança para as combinações de props
 * esperadas (sem visibleTabs, com visibleTabs de templates, com stacked).
 *
 * Todos os tabs filhos são mockados — seus testes próprios verificam
 * o conteúdo interno.
 */
import React from "react"
import { render } from "@testing-library/react"
import { describe, it, vi, beforeAll } from "vitest"

beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false, media: query, onchange: null,
        addEventListener: () => {}, removeEventListener: () => {},
        addListener: () => {}, removeListener: () => {},
        dispatchEvent: () => false,
      }),
    })
  }
})

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/components/settings/communication-hub/useCommunicationHub", () => ({
  useCommunicationHub: () => ({
    activeTab: "templates",
    setActiveTab: vi.fn(),
    loading: false,
    error: null,
    successMessage: null,
    channelFilter: "all",
    setChannelFilter: vi.fn(),
    triggerTypeFilter: "all",
    setTriggerTypeFilter: vi.fn(),
    searchQuery: "",
    setSearchQuery: vi.fn(),
    expandedGroups: {},
    setExpandedGroups: vi.fn(),
    templates: [],
    signature: null,
    schedule: null,
    preferences: [],
    abTests: [],
    setSchedule: vi.fn(),
    setPreferences: vi.fn(),
    fetchData: vi.fn(),
    saveTemplate: vi.fn(),
    saveSignature: vi.fn(),
    saveSchedule: vi.fn(),
    savePreferences: vi.fn(),
  }),
}))

vi.mock("@/components/settings/communication-hub/TemplatesTab", () => ({
  TemplatesTab: () => <div data-testid="templates-tab-stub" />,
}))
vi.mock("@/components/settings/communication-hub/SignatureTab", () => ({
  SignatureTab: () => <div data-testid="signature-tab-stub" />,
}))
vi.mock("@/components/settings/AlertPreferencesPanel", () => ({
  AlertPreferencesPanel: () => <div data-testid="alert-preferences-stub" />,
}))

import { CommunicationHub } from "@/components/settings/CommunicationHub"

describe("CommunicationHub — smoke rerender (rules-of-hooks + mount)", () => {
  it("monta sem props sem lançar (modo padrão — todas as tabs)", () => {
    const { unmount } = render(<CommunicationHub />)
    unmount()
  })

  it("monta com visibleTabs=['templates','signature'] + stacked=true sem lançar", () => {
    const { unmount } = render(
      <CommunicationHub visibleTabs={["templates", "signature"]} stacked={true} />
    )
    unmount()
  })

  it("rerenderiza entre activeSubsections sem lançar (detecta rules-of-hooks regression)", () => {
    const { rerender, unmount } = render(<CommunicationHub activeSubsection="templates" />)
    rerender(<CommunicationHub activeSubsection="signature" />)
    rerender(<CommunicationHub activeSubsection="alerts" />)
    unmount()
  })
})
