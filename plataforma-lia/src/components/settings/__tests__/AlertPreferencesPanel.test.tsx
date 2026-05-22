/**
 * Smoke tests — AlertPreferencesPanel (ADR-WT-2025 Sprint D Commit 5/5).
 *
 * Cobre patterns canonical:
 *  1. render: monta componente, espera preferences listadas
 *  2. toggle: clique em enable toggle dispara PUT /alerts/preferences
 *  3. multi-tenancy R2: payload NUNCA inclui company_id
 *  4. error UI: falha de save exibe banner explícito (REGRA 4)
 *
 * Pattern: mock do hook canonical via vi.mock; smoke render apenas.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import { AlertPreferencesPanel } from "../AlertPreferencesPanel"
import type {
  AlertPreference,
} from "@/hooks/settings/use-alert-preferences"

const FIXTURE_PREFS: AlertPreference[] = [
  {
    id: "pref-1",
    user_id: "user-1",
    alert_type: "time_to_hire_critical",
    name: "Time to Hire Crítico",
    description: "Alerta quando time to hire ultrapassa limite",
    is_enabled: true,
    threshold: 45,
    channels: { email: true, bell: true, teams: false, whatsapp: false },
    cooldown_hours: 24,
  },
  {
    id: "pref-2",
    user_id: "user-1",
    alert_type: "nps_declining",
    name: "NPS em Declínio",
    description: "Alerta quando NPS cai abaixo do limite",
    is_enabled: false,
    threshold: 75,
    channels: { email: false, bell: true, teams: false, whatsapp: false },
    cooldown_hours: 24,
  },
]

const MESSAGES = {
  settings: {
    communication: {
      alertPreferences: {
        title: "Preferências de Alertas",
        subtitle: "Configure quais alertas receber e por onde",
        saved: "Preferência salva",
        loading: "Carregando...",
        empty: "Nenhuma preferência configurada",
        channelEmail: "Email",
        channelInApp: "App",
        channelTeams: "Teams",
        channelWhatsapp: "WhatsApp",
        toggleAria: "Ativar/desativar {type}",
        thresholdAria: "Limite para {type}",
        cooldownAria: "Cooldown em horas para {type}",
        unit: {
          count: "und",
          hours: "h",
          days: "d",
          percent: "%",
        },
      },
    },
  },
}

const updatePreferenceMock = vi.fn()

vi.mock("@/hooks/settings/use-alert-preferences", () => ({
  useAlertPreferences: () => ({
    preferences: FIXTURE_PREFS,
    isLoading: false,
    error: null,
    updatePreference: updatePreferenceMock,
    createPreference: vi.fn(),
    refetch: vi.fn(),
  }),
}))

function renderPanel() {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      <AlertPreferencesPanel />
    </NextIntlClientProvider>
  )
}

describe("AlertPreferencesPanel", () => {
  beforeEach(() => {
    updatePreferenceMock.mockReset()
    updatePreferenceMock.mockResolvedValue(undefined)
  })

  test("renders all canonical preferences with title", () => {
    renderPanel()
    expect(screen.getByText("Preferências de Alertas")).toBeTruthy()
    expect(screen.getByText("Time to Hire Crítico")).toBeTruthy()
    expect(screen.getByText("NPS em Declínio")).toBeTruthy()
  })

  test("clicking toggle calls updatePreference (PUT /alerts/preferences)", async () => {
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-time_to_hire_critical")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(updatePreferenceMock).toHaveBeenCalledTimes(1)
    })
    const [pref, updates] = updatePreferenceMock.mock.calls[0]
    expect(pref.alert_type).toBe("time_to_hire_critical")
    expect(updates).toEqual({ is_enabled: false })
  })

  test("update payload NEVER contains company_id (REGRA 2)", async () => {
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-nps_declining")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(updatePreferenceMock).toHaveBeenCalledTimes(1)
    })
    const [, updates] = updatePreferenceMock.mock.calls[0]
    // updates é AlertPreferenceUpdate — sem company_id
    expect(updates).not.toHaveProperty("company_id")
  })

  test("save failure renders explicit error banner (REGRA 4)", async () => {
    updatePreferenceMock.mockRejectedValueOnce(new Error("HTTP 500: backend down"))
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-time_to_hire_critical")
    fireEvent.click(toggle)
    await waitFor(() => {
      const banner = screen.getByTestId("alert-preferences-error")
      expect(banner).toBeTruthy()
      expect(banner.textContent).toContain("HTTP 500")
    })
  })
})
