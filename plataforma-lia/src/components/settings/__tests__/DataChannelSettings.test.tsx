/**
 * DataChannelSettings — smoke tests.
 *
 * Covers:
 *  1. Renders title and all 4 channel options
 *  2. Current channel has aria-checked=true
 *  3. Clicking a different channel triggers mutation
 *  4. Error state renders alert
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

// -- Mocks -------------------------------------------------------------------

const mockMutate = vi.fn()
const mockInvalidateQueries = vi.fn()

let mockQueryData: Record<string, unknown> | undefined = {
  communication_rules: { preferred_data_channel: "email" },
}
let mockMutationState = { isPending: false, isError: false, isSuccess: false }

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: mockQueryData,
    isLoading: false,
  })),
  useMutation: vi.fn(({ mutationFn, onSuccess }: { mutationFn: (c: string) => Promise<unknown>; onSuccess?: () => void }) => ({
    mutate: (channel: string) => {
      mockMutate(channel)
      if (onSuccess) onSuccess()
    },
    ...mockMutationState,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: mockInvalidateQueries,
  })),
}))

vi.mock("@/hooks/settings/useSettingsBroadcast", () => ({
  SETTINGS_QUERY_KEYS: {
    hiringPolicy: () => ["hiring-policy"],
    companyProfile: () => ["company-profile"],
  },
  dispatchSettingsUpdate: vi.fn(),
}))

// Mock HubHeader as a simple div so the test doesn't need the full _shared
vi.mock("@/components/settings/_shared", () => ({
  HubHeader: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="hub-header">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  ),
}))

const MESSAGES = {
  settings: {
    communication: {
      dataChannel: {
        title: "Canal de Coleta de Dados",
        description: "Canal padrão para solicitar dados ao candidato. Pode ser sobrescrito por vaga.",
        channelEmail: "E-mail",
        channelEmailDesc: "Envia link do portal de dados por e-mail",
        channelWeb: "Portal Web",
        channelWebDesc: "Candidato acessa o portal de dados pelo link direto",
        channelWhatsapp: "WhatsApp",
        channelWhatsappDesc: "Coleta via mensagem interativa no WhatsApp",
        channelVoice: "Ligação por Voz",
        channelVoiceDesc: "Coleta via ligação telefônica com IA",
        saveSuccess: "Canal de coleta atualizado com sucesso",
        saveError: "Erro ao atualizar canal de coleta",
      },
    },
  },
}

import { DataChannelSettings } from "../DataChannelSettings"

function renderComponent() {
  return render(
    <NextIntlClientProvider locale="pt" messages={MESSAGES}>
      <DataChannelSettings />
    </NextIntlClientProvider>
  )
}

describe("DataChannelSettings", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockQueryData = { communication_rules: { preferred_data_channel: "email" } }
    mockMutationState = { isPending: false, isError: false, isSuccess: false }
  })

  test("renders title via HubHeader", () => {
    renderComponent()
    expect(screen.getByTestId("hub-header")).toBeDefined()
    expect(screen.getByText("Canal de Coleta de Dados")).toBeDefined()
  })

  test("renders all 4 channel options", () => {
    renderComponent()
    expect(screen.getByTestId("data-channel-email")).toBeDefined()
    expect(screen.getByTestId("data-channel-web")).toBeDefined()
    expect(screen.getByTestId("data-channel-whatsapp")).toBeDefined()
    expect(screen.getByTestId("data-channel-voice")).toBeDefined()
  })

  test("renders channel labels", () => {
    renderComponent()
    expect(screen.getByText("E-mail")).toBeDefined()
    expect(screen.getByText("Portal Web")).toBeDefined()
    expect(screen.getByText("WhatsApp")).toBeDefined()
    expect(screen.getByText("Ligação por Voz")).toBeDefined()
  })

  test("current channel has aria-checked=true", () => {
    renderComponent()
    const emailBtn = screen.getByTestId("data-channel-email")
    const webBtn = screen.getByTestId("data-channel-web")
    expect(emailBtn.getAttribute("aria-checked")).toBe("true")
    expect(webBtn.getAttribute("aria-checked")).toBe("false")
  })

  test("clicking a different channel triggers mutate", () => {
    renderComponent()
    fireEvent.click(screen.getByTestId("data-channel-voice"))
    expect(mockMutate).toHaveBeenCalledWith("voice")
  })

  test("clicking the current channel does NOT trigger mutate", () => {
    renderComponent()
    fireEvent.click(screen.getByTestId("data-channel-email"))
    expect(mockMutate).not.toHaveBeenCalled()
  })

  test("error state renders alert", () => {
    mockMutationState = { isPending: false, isError: true, isSuccess: false }
    renderComponent()
    expect(screen.getByRole("alert")).toBeDefined()
    expect(screen.getByText("Erro ao atualizar canal de coleta")).toBeDefined()
  })

  test("success state renders status message", () => {
    mockMutationState = { isPending: false, isError: false, isSuccess: true }
    renderComponent()
    expect(screen.getByRole("status")).toBeDefined()
    expect(screen.getByText("Canal de coleta atualizado com sucesso")).toBeDefined()
  })

  test("defaults to email when no preferred_data_channel set", () => {
    mockQueryData = { communication_rules: {} }
    renderComponent()
    expect(screen.getByTestId("data-channel-email").getAttribute("aria-checked")).toBe("true")
  })
})
