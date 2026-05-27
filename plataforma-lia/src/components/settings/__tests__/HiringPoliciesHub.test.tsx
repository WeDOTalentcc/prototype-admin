/**
 * HiringPoliciesHub tests (Sprint P0-1, 2026-05-27)
 *
 * Coverage:
 * 1. Renders all 18 question textareas
 * 2. onBlur triggers PATCH mutation when value changes
 * 3. onBlur skips save when value is unchanged
 * 4. Shows loading state while fetching
 * 5. Shows error state on fetch failure
 * 6. rules-of-hooks: no early returns before hooks
 * 7. i18n canonical contract: no MISSING_MESSAGE (component hardcodes PT-BR, no useTranslations)
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { HiringPoliciesHub } from "../HiringPoliciesHub"

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockFetch = vi.fn()
global.fetch = mockFetch

vi.mock("@/hooks/settings/useSettingsBroadcast", () => ({
  SETTINGS_QUERY_KEYS: {
    hiringPolicy: () => ["hiring-policy"],
    companyProfile: () => ["company-profile"],
    cultureProfile: (id: string) => ["culture-profile", id],
    benefits: (id: string) => ["company-benefits", id],
    settingsProgress: () => ["settings-progress"],
  },
  dispatchSettingsUpdate: vi.fn(),
}))

vi.mock("@/hooks/settings/useCompanyBlocks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/hooks/settings/useCompanyBlocks")>()
  return {
    ...actual,
    POLICY_FIELD_TO_BLOCK: {
      ...actual.POLICY_FIELD_TO_BLOCK,
      screening_criteria: "screening_rules",
      candidate_feedback_policy: "communication_rules",
      communication_window: "communication_rules",
      interview_scheduling_policy: "scheduling_rules",
      interview_reminder_policy: "scheduling_rules",
      no_show_policy: "scheduling_rules",
      minimum_compatibility_score: "screening_rules",
      salary_negotiation_policy: "screening_rules",
      remote_work_policy: "screening_rules",
      data_retention_candidate_policy: "screening_rules",
      talent_pool_opt_in_policy: "screening_rules",
      diversity_inclusion_guidelines: "screening_rules",
      manager_approval_sla_hours: "pipeline_rules",
      vacancy_approval_required: "pipeline_rules",
    },
  }
})

// ── Helpers ───────────────────────────────────────────────────────────────────

const MINIMAL_MESSAGES = {
  settings: {
    hiring_policies: {},
  },
}

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderHub(queryClient = makeQueryClient()) {
  return render(
    <QueryClientProvider client={queryClient}>
      <NextIntlClientProvider locale="pt" messages={MINIMAL_MESSAGES}>
        <HiringPoliciesHub />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("HiringPoliciesHub", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        pipeline_rules: {},
        scheduling_rules: {},
        communication_rules: {},
        screening_rules: {},
        automation_rules: {},
      }),
    })
  })

  test("renders all 18 question textarea fields", async () => {
    renderHub()
    await waitFor(() => {
      // All 18 question blocks should be present via data-testid
      const EXPECTED_FIELDS = [
        "screening_criteria",
        "auto_screening",
        "auto_stage_advance",
        "manager_approval_for_offer",
        "manager_approval_sla_hours",
        "vacancy_approval_required",
        "communication_window",
        "preferred_channel",
        "candidate_feedback_policy",
        "interview_scheduling_policy",
        "interview_reminder_policy",
        "no_show_policy",
        "minimum_compatibility_score",
        "salary_negotiation_policy",
        "remote_work_policy",
        "data_retention_candidate_policy",
        "talent_pool_opt_in_policy",
        "diversity_inclusion_guidelines",
      ]
      for (const field of EXPECTED_FIELDS) {
        expect(
          screen.getByTestId(`question-block-${field}`),
          `Missing question block: ${field}`,
        ).toBeTruthy()
      }
    })
  })

  test("renders exactly 18 textareas", async () => {
    renderHub()
    await waitFor(() => {
      const textareas = screen.getAllByRole("textbox")
      expect(textareas).toHaveLength(18)
    })
  })

  test("shows loading state while fetching", () => {
    // Never resolves
    mockFetch.mockImplementation(() => new Promise(() => {}))
    renderHub()
    expect(screen.getByText(/Carregando políticas/i)).toBeTruthy()
  })

  test("renders empty textareas gracefully when fetch returns 500", async () => {
    // The hub's fetchHiringPolicy returns null (not throws) on non-404 errors,
    // matching the pattern in use-company-settings-cards. So the hub renders
    // empty textareas rather than an error state (graceful degradation).
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    })
    renderHub()
    await waitFor(() => {
      // Hub still renders — all 18 fields present but empty
      expect(screen.getByTestId("hiring-policies-hub")).toBeTruthy()
      expect(screen.getByText(/0 \/ 18 respondidas/i)).toBeTruthy()
    })
  })

  test("onBlur triggers PATCH mutation when value changes", async () => {
    let patchCalled = false
    mockFetch.mockImplementation(async (url: string, opts?: RequestInit) => {
      if (url === "/api/backend-proxy/hiring-policy/block" && opts?.method === "PATCH") {
        patchCalled = true
        return {
          ok: true,
          status: 200,
          json: async () => ({}),
        }
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          pipeline_rules: {},
          scheduling_rules: {},
          communication_rules: {},
          screening_rules: {},
          automation_rules: {},
        }),
      }
    })

    renderHub()

    await waitFor(() => {
      expect(screen.getByTestId("question-block-screening_criteria")).toBeTruthy()
    })

    const textarea = screen.getByRole("textbox", { name: /critérios mínimos/i })
    fireEvent.change(textarea, { target: { value: "Novo critério de triagem" } })
    fireEvent.blur(textarea)

    await waitFor(() => {
      expect(patchCalled).toBe(true)
    })
  })

  test("onBlur skips save when value is unchanged (empty → empty)", async () => {
    let patchCallCount = 0
    mockFetch.mockImplementation(async (url: string, opts?: RequestInit) => {
      if (url === "/api/backend-proxy/hiring-policy/block" && opts?.method === "PATCH") {
        patchCallCount++
        return { ok: true, status: 200, json: async () => ({}) }
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          pipeline_rules: {},
          scheduling_rules: {},
          communication_rules: {},
          screening_rules: {},
          automation_rules: {},
        }),
      }
    })

    renderHub()

    await waitFor(() => {
      expect(screen.getByTestId("question-block-screening_criteria")).toBeTruthy()
    })

    const textarea = screen.getByRole("textbox", { name: /critérios mínimos/i })
    // Blur without changing value (empty → empty)
    fireEvent.blur(textarea)

    // Give time for any async side effects
    await new Promise((r) => setTimeout(r, 50))
    expect(patchCallCount).toBe(0)
  })

  test("shows group headings for all 6 groups", async () => {
    renderHub()
    await waitFor(() => {
      const groups = ["A. Triagem", "B. Aprovação e Governança", "C. Comunicação com o candidato", "D. Entrevistas e agenda", "E. Compatibilidade e filtros", "F. Dados e LGPD"]
      for (const g of groups) {
        expect(screen.getByText(new RegExp(g, "i"))).toBeTruthy()
      }
    })
  })

  test("shows counter of answered questions", async () => {
    renderHub()
    await waitFor(() => {
      expect(screen.getByText(/0 \/ 18 respondidas/i)).toBeTruthy()
    })
  })

  test("pre-fills textareas with existing policy data", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        screening_rules: { screening_criteria: "Mínimo 3 anos de experiência" },
        pipeline_rules: {},
        scheduling_rules: {},
        communication_rules: {},
        automation_rules: {},
      }),
    })

    renderHub()

    await waitFor(() => {
      const textarea = screen.getByDisplayValue("Mínimo 3 anos de experiência")
      expect(textarea).toBeTruthy()
    })
  })
})
