/**
 * use-integrations-data.test.ts
 *
 * Covers the critical property: Teams card status is ALWAYS derived from the
 * per-tenant `/integrations/teams/status` endpoint — never from the catalog's
 * own status field.
 *
 * Regression scenario: catalog returns Teams with status "connected" (e.g. from
 * a stale snapshot), but the per-tenant endpoint returns { configured: false }.
 * The hook must honour the tenant endpoint and surface "not_configured".
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: vi.fn(),
}))

vi.mock("@/hooks/integrations/use-integration-catalog", () => ({
  useIntegrationCatalog: () => ({ entries: [], isLoading: false }),
  flattenEntries: () => [],
}))

vi.mock("@/components/settings/integrations/integration-data", () => ({
  integrations: [
    {
      id: "teams",
      name: "Microsoft Teams",
      category: "communication",
      status: "connected",
      shortDescription: "Teams",
      fullDescription: "Teams full",
      iconBg: "",
      iconColor: "",
      iconLetter: "T",
      capabilities: [],
      configFields: [],
    },
    {
      id: "google-calendar",
      name: "Google Calendar",
      category: "calendar",
      status: "not_configured",
      shortDescription: "Cal",
      fullDescription: "Cal full",
      iconBg: "",
      iconColor: "",
      iconLetter: "G",
      capabilities: [],
      configFields: [],
    },
  ],
  categories: [],
}))

import { useIntegrationsData } from "../use-integrations-data"
import { apiFetch } from "@/lib/api/api-fetch"

const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client }, children)
}

beforeEach(() => {
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue({ ok: false, json: async () => ({}) })
})

describe("useIntegrationsData — Teams status derivation", () => {
  it("returns teamsStatus=not_configured when tenant endpoint returns configured:false even if catalog has connected", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/integrations/teams/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ configured: false, source: "none" }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    const { result } = renderHook(() => useIntegrationsData(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.teamsStatus).toBe("not_configured"))
  })

  it("enrichedIntegrations marks Teams as not_configured when tenant endpoint returns configured:false", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/integrations/teams/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ configured: false, source: "none" }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    const { result } = renderHook(() => useIntegrationsData(), { wrapper: makeWrapper() })
    await waitFor(() => {
      const teams = result.current.enrichedIntegrations.find((i) => i.id === "teams")
      expect(teams?.status).toBe("not_configured")
    })
  })

  it("returns teamsStatus=configured when tenant endpoint returns configured:true", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/integrations/teams/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ configured: true, source: "db" }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    const { result } = renderHook(() => useIntegrationsData(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.teamsStatus).toBe("configured"))
  })

  it("enrichedIntegrations marks Teams as connected when tenant endpoint returns configured:true", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/integrations/teams/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ configured: true, source: "db" }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    const { result } = renderHook(() => useIntegrationsData(), { wrapper: makeWrapper() })
    await waitFor(() => {
      const teams = result.current.enrichedIntegrations.find((i) => i.id === "teams")
      expect(teams?.status).toBe("connected")
    })
  })

  it("exposes refetchTeamsStatus as a function", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url.includes("/integrations/teams/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ configured: false }) })
      }
      return Promise.resolve({ ok: true, json: async () => ({}) })
    })

    const { result } = renderHook(() => useIntegrationsData(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.teamsStatus).toBe("not_configured"))
    expect(typeof result.current.refetchTeamsStatus).toBe("function")
  })
})
