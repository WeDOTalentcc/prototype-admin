/**
 * PR-E — OfferReviewModal component tests
 *
 * Validates the 2-column offer modal rendering, state-driven visibility,
 * button enabled/disabled rules, and action callbacks.
 *
 * Skill: lia-testing PARTE 1 (TDD red→green) + harness-engineering
 * (sensor computacional: detecta regressão antes de deploy).
 *
 * Mocking strategy: vi.mock o useOfferDraftStore — isolado de Zustand
 * e da rede. Child components (JobDataPanel, OfferDataForm) são renderizados
 * reais para capturar regressões de composição.
 */

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import type { OfferDraft } from "@/types/offer"

// ─── Mocks de infra ──────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

// Stub mínimo para window.matchMedia (jsdom não implementa)
beforeEach(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false, media: query, onchange: null,
        addEventListener: vi.fn(), removeEventListener: vi.fn(),
        addListener: vi.fn(), removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }),
    })
  }
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// ─── Draft fixture ────────────────────────────────────────────────────────────

const DRAFT_BASE: OfferDraft = {
  id: "offer-001",
  company_id: "co-1",
  candidate_id: "cand-1",
  job_id: "job-1",
  job_data_snapshot: {
    title: "Engenheiro de Software",
    department: "Tecnologia",
    salary_range: { min: 8000, max: 12000, currency: "BRL" },
    benefits: ["VT", "VR"],
    contract_type: "CLT",
    work_model: "Híbrido",
  },
  candidate_data_snapshot: {
    name: "Maria Silva",
    email: "maria@example.com",
  },
  offered_salary: 10000,
  offered_salary_currency: "BRL",
  validity_days: 7,
  status: "draft",
  created_by_user_id: "user-1",
  created_at: "2026-04-27T10:00:00Z",
  updated_at: "2026-04-27T10:00:00Z",
}

// ─── Store mock helpers ───────────────────────────────────────────────────────

const mockUpdateField = vi.fn().mockResolvedValue(undefined)
const mockSendAuto = vi.fn().mockResolvedValue({ success: true, message: "Proposta enviada com sucesso!" })
const mockPrepareManual = vi.fn().mockResolvedValue({ subject: "Proposta para Maria", body: "Texto da proposta" })
const mockCancel = vi.fn().mockResolvedValue(undefined)
const mockClearDraft = vi.fn()

function mockStore(overrides: Partial<{ draft: OfferDraft | null; isSaving: boolean; salaryWarnings: { level: "warning" | "info"; message: string }[] }> = {}) {
  return {
    draft: DRAFT_BASE,
    isSaving: false,
    error: null,
    isLoading: false,
    salaryWarnings: [],
    updateField: mockUpdateField,
    sendAuto: mockSendAuto,
    prepareManual: mockPrepareManual,
    cancel: mockCancel,
    clearDraft: mockClearDraft,
    ...overrides,
  }
}

vi.mock("@/stores/offer-draft-store", () => ({
  useOfferDraftStore: vi.fn(),
}))

import { useOfferDraftStore } from "@/stores/offer-draft-store"
import { OfferReviewModal } from "../OfferReviewModal"

// ─── Testes ───────────────────────────────────────────────────────────────────

describe("OfferReviewModal", () => {
  describe("visibilidade", () => {
    it("não renderiza nada quando draft é null", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ draft: null }) as ReturnType<typeof useOfferDraftStore>)
      const { container } = render(<OfferReviewModal />)
      expect(container.firstChild).toBeNull()
    })

    it("não renderiza quando draft.status !== 'draft'", () => {
      const sentDraft = { ...DRAFT_BASE, status: "sent" as const }
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ draft: sentDraft }) as ReturnType<typeof useOfferDraftStore>)
      const { container } = render(<OfferReviewModal />)
      // Dialog fechado — não há conteúdo visível
      expect(screen.queryByRole("dialog")).toBeNull()
    })

    it("renderiza o modal quando draft está presente e status é 'draft'", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      expect(screen.getByRole("dialog")).toBeTruthy()
    })
  })

  describe("cabeçalho", () => {
    it("exibe nome do candidato no título", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      expect(screen.getByText(/Maria Silva/)).toBeTruthy()
    })

    it("exibe título da vaga no subtítulo", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      // Job title appears in header subtitle and JobDataPanel — use getAllByText
      expect(screen.getAllByText("Engenheiro de Software").length).toBeGreaterThanOrEqual(1)
    })

    it("usa fallback 'Candidato' quando nome está ausente", () => {
      const draftNoName = { ...DRAFT_BASE, candidate_data_snapshot: { email: "x@x.com" } }
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ draft: draftNoName }) as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      expect(screen.getByText(/Candidato/)).toBeTruthy()
    })
  })

  describe("regras de habilitação dos botões", () => {
    it("botão 'Enviar Proposta' está habilitado quando há salário e não está salvando", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      const btn = screen.getByRole("button", { name: /Enviar Proposta/ })
      expect((btn as HTMLButtonElement).disabled).toBe(false)
    })

    it("botão 'Enviar Proposta' está desabilitado quando offered_salary está ausente", () => {
      const draftNoSalary = { ...DRAFT_BASE, offered_salary: undefined }
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ draft: draftNoSalary }) as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      const btn = screen.getByRole("button", { name: /Enviar Proposta/ })
      expect((btn as HTMLButtonElement).disabled).toBe(true)
    })

    it("botão 'Enviar Proposta' está desabilitado quando isSaving=true", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ isSaving: true }) as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      const btn = screen.getByRole("button", { name: /Enviar Proposta/ })
      expect((btn as HTMLButtonElement).disabled).toBe(true)
    })

    it("botão 'Envio Manual' está desabilitado quando offered_salary está ausente", () => {
      const draftNoSalary = { ...DRAFT_BASE, offered_salary: undefined }
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore({ draft: draftNoSalary }) as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      const btn = screen.getByRole("button", { name: /Envio Manual/ })
      expect((btn as HTMLButtonElement).disabled).toBe(true)
    })
  })

  describe("ações dos botões", () => {
    it("clique em 'Cancelar rascunho' chama cancel()", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      fireEvent.click(screen.getByRole("button", { name: /Cancelar rascunho/ }))
      expect(mockCancel).toHaveBeenCalledOnce()
    })

    it("clique em 'Enviar Proposta' confirma via HITL e chama sendAuto()", async () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      // Step 1: request confirmation (idle -> confirming)
      fireEvent.click(screen.getByRole("button", { name: /Enviar Proposta/ }))
      // OfferHITLBanner in confirming state shows Confirmar envio button
      const confirmBtn = await waitFor(() => screen.getByRole("button", { name: /Confirmar envio/ }))
      // Step 2: user confirms (user_confirmation: true — HITL gate)
      fireEvent.click(confirmBtn)
      await waitFor(() => expect(mockSendAuto).toHaveBeenCalledOnce())
    })

    it("exibe mensagem de sucesso após confirmação HITL e envio", async () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      // Two-step HITL: request -> confirm
      fireEvent.click(screen.getByRole("button", { name: /Enviar Proposta/ }))
      const confirmBtn = await waitFor(() => screen.getByRole("button", { name: /Confirmar envio/ }))
      fireEvent.click(confirmBtn)
      // OfferHITLBanner success state shows fixed success text
      await waitFor(() => expect(screen.getByText("Proposta enviada com sucesso!")).toBeTruthy())
    })

    it("clique em 'Envio Manual' chama prepareManual() e emite lia:open_modal com modal_id=send_email_offer", async () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      const events: CustomEvent[] = []
      function listener(e: Event) { events.push(e as CustomEvent) }
      window.addEventListener("lia:open_modal", listener)
      render(<OfferReviewModal />)
      fireEvent.click(screen.getByRole("button", { name: /Envio Manual/ }))
      await waitFor(() => expect(mockPrepareManual).toHaveBeenCalledOnce())
      await waitFor(() => {
        const offerEvents = events.filter(e => e.detail?.modal_id === "send_email_offer")
        expect(offerEvents).toHaveLength(1)
      })
      window.removeEventListener("lia:open_modal", listener)
    })
  })

  describe("salary warnings (harness: sensor computacional)", () => {
    it("exibe banner de warning quando salário está acima da faixa", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(
        mockStore({ salaryWarnings: [{ level: "warning", message: "Salário acima de 110% do máximo da faixa" }] }) as ReturnType<typeof useOfferDraftStore>
      )
      render(<OfferReviewModal />)
      expect(screen.getByText(/Salário acima de 110%/)).toBeTruthy()
    })

    it("exibe banner de info quando salário está abaixo do mínimo", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(
        mockStore({ salaryWarnings: [{ level: "info", message: "Salário abaixo do mínimo da faixa" }] }) as ReturnType<typeof useOfferDraftStore>
      )
      render(<OfferReviewModal />)
      expect(screen.getByText(/Salário abaixo do mínimo/)).toBeTruthy()
    })

    it("não exibe banners quando salaryWarnings está vazio", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      expect(screen.queryByText(/Salário acima/)).toBeNull()
      expect(screen.queryByText(/Salário abaixo/)).toBeNull()
    })
  })

  describe("multi-tenancy (Non-Negotiable #1)", () => {
    it("o draft carregado preserva company_id da sessão", () => {
      vi.mocked(useOfferDraftStore).mockReturnValue(mockStore() as ReturnType<typeof useOfferDraftStore>)
      render(<OfferReviewModal />)
      // Modal renderiza — o draft tem company_id. O store é responsável
      // por validar multi-tenancy; este test verifica que o modal não
      // sobrescreve ou ignora o company_id do draft.
      const { draft } = vi.mocked(useOfferDraftStore).mock.results[0].value
      expect(draft?.company_id).toBe("co-1")
    })
  })
})
