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
    alert_type: "candidate_no_interaction",
    name: "Candidato Sem Interação",
    description: "Alerta para candidatos sem contato há mais de 5 dias",
    is_enabled: true,
    threshold: 5,
    channels: { email: true, bell: true, teams: false, whatsapp: false },
    cooldown_hours: 24,
  },
  {
    id: "pref-2",
    user_id: "user-1",
    alert_type: "candidates_stagnant",
    name: "Candidatos Estagnados",
    description: "Candidatos parados na mesma etapa por muito tempo",
    is_enabled: false,
    threshold: 10,
    channels: { email: false, bell: true, teams: false, whatsapp: false },
    cooldown_hours: 24,
  },
  {
    id: "pref-3",
    user_id: "user-1",
    alert_type: "interview_not_confirmed",
    name: "Entrevista Não Confirmada",
    description: "Lembrete antes de entrevistas sem confirmação",
    is_enabled: true,
    threshold: 24,
    channels: { email: true, bell: true, teams: true, whatsapp: true },
    cooldown_hours: 12,
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
        groupRecruiter: "Alertas para o recrutador",
        groupRecruiterHint: "Notificações internas",
        groupCandidate: "Alertas para o candidato",
        groupCandidateHint: "Mensagens ao candidato",
        channelsLabel: "Enviar por",
        cooldownLabel: "Repetir no máximo a cada",
        cooldownUnit: "h",
        disabledHint: "Ative para configurar",
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
    expect(screen.getByText("Candidato Sem Interação")).toBeTruthy()
    expect(screen.getByText("Candidatos Estagnados")).toBeTruthy()
  })

  test("clicking toggle calls updatePreference (PUT /alerts/preferences)", async () => {
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-candidate_no_interaction")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(updatePreferenceMock).toHaveBeenCalledTimes(1)
    })
    const [pref, updates] = updatePreferenceMock.mock.calls[0]
    expect(pref.alert_type).toBe("candidate_no_interaction")
    expect(updates).toEqual({ is_enabled: false })
  })

  test("update payload NEVER contains company_id (REGRA 2)", async () => {
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-candidates_stagnant")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(updatePreferenceMock).toHaveBeenCalledTimes(1)
    })
    const [, updates] = updatePreferenceMock.mock.calls[0]
    // updates é AlertPreferenceUpdate — sem company_id
    expect(updates).not.toHaveProperty("company_id")
  })

  test("WhatsApp channel only applies to candidate-facing alerts", () => {
    renderPanel()
    // Recrutador (candidate_no_interaction): sem WhatsApp; tem e-mail/app/teams.
    expect(
      screen.queryByTestId("alert-pref-channel-candidate_no_interaction-whatsapp")
    ).toBeNull()
    expect(
      screen.getByTestId("alert-pref-channel-candidate_no_interaction-bell")
    ).toBeTruthy()
    // Candidato (interview_not_confirmed): tem WhatsApp e e-mail; sem canais internos.
    expect(
      screen.getByTestId("alert-pref-channel-interview_not_confirmed-whatsapp")
    ).toBeTruthy()
    expect(
      screen.queryByTestId("alert-pref-channel-interview_not_confirmed-teams")
    ).toBeNull()
    expect(
      screen.queryByTestId("alert-pref-channel-interview_not_confirmed-bell")
    ).toBeNull()
  })

  test("save failure renders explicit error banner (REGRA 4)", async () => {
    updatePreferenceMock.mockRejectedValueOnce(new Error("HTTP 500: backend down"))
    renderPanel()
    const toggle = screen.getByTestId("alert-pref-toggle-candidate_no_interaction")
    fireEvent.click(toggle)
    await waitFor(() => {
      const banner = screen.getByTestId("alert-preferences-error")
      expect(banner).toBeTruthy()
      expect(banner.textContent).toContain("HTTP 500")
    })
  })
})
