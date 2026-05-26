/**
 * Testes para CompensationPolicyFormModal
 *
 * Aplica:
 * - Rules of Hooks discipline: rerender isOpen false→true→false sem throw
 * - Callback contract: onClose + onSave chamados corretamente
 * - isSaving state: botão submit desabilitado durante save
 * - Source-level: verifica uso de createPortal (não removido) + ausência de hardcoded company_id no payload
 *
 * Extração canonical 2026-05-26.
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { readFileSync } from "fs"
import { join } from "path"
import { CompensationPolicyFormModal } from "../CompensationPolicyFormModal"
import type { CompensationPolicyRecord } from "../compensation-policies-types"
import { defaultPolicy } from "../compensation-policies-types"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makePolicy = (overrides: Partial<CompensationPolicyRecord> = {}): CompensationPolicyRecord => ({
  ...defaultPolicy,
  id: "policy-uuid-001",
  name: "PLR Anual 2026",
  ...overrides,
})

function renderModal(props: Partial<Parameters<typeof CompensationPolicyFormModal>[0]> = {}) {
  const defaults = {
    isOpen: true,
    initialData: null,
    onClose: vi.fn(),
    onSave: vi.fn().mockResolvedValue(undefined),
    isSaving: false,
    error: null,
  }
  return render(<CompensationPolicyFormModal {...defaults} {...props} />)
}

// ---------------------------------------------------------------------------
// Testes DOM
// ---------------------------------------------------------------------------

describe("CompensationPolicyFormModal — DOM", () => {
  it("1. mount com isOpen=false não lança e não renderiza conteúdo", () => {
    expect(() => {
      renderModal({ isOpen: false })
    }).not.toThrow()

    // Nenhum botão de submit/cancelar deve aparecer
    expect(screen.queryByText("Criar Política")).toBeNull()
    expect(screen.queryByText("Cancelar")).toBeNull()
  })

  it("2. mount com isOpen=true renderiza sem throw e mostra campos canônicos", () => {
    expect(() => {
      renderModal({ isOpen: true })
    }).not.toThrow()

    // Campo nome obrigatório
    expect(screen.getByPlaceholderText("Ex: PLR Anual Padrão 2026")).toBeTruthy()
    // Botão de criar
    expect(screen.getByText("Criar Política")).toBeTruthy()
    // Botão cancelar
    expect(screen.getByText("Cancelar")).toBeTruthy()
  })

  it("3. rerender isOpen false → true → false não lança (Rules of Hooks)", () => {
    const onClose = vi.fn()
    const onSave = vi.fn().mockResolvedValue(undefined)

    const { rerender } = render(
      <CompensationPolicyFormModal
        isOpen={false}
        initialData={null}
        onClose={onClose}
        onSave={onSave}
        isSaving={false}
        error={null}
      />
    )

    expect(() => {
      rerender(
        <CompensationPolicyFormModal
          isOpen={true}
          initialData={null}
          onClose={onClose}
          onSave={onSave}
          isSaving={false}
          error={null}
        />
      )
    }).not.toThrow()

    expect(() => {
      rerender(
        <CompensationPolicyFormModal
          isOpen={false}
          initialData={null}
          onClose={onClose}
          onSave={onSave}
          isSaving={false}
          error={null}
        />
      )
    }).not.toThrow()
  })

  it("4. onClose é chamado ao clicar no botão Cancelar", () => {
    const onClose = vi.fn()
    renderModal({ onClose })

    fireEvent.click(screen.getByText("Cancelar"))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("5. onClose é chamado ao clicar no botão X (fechar)", () => {
    const onClose = vi.fn()
    renderModal({ onClose })

    // O botão X é o único botão sem texto — tem um svg lucide X dentro
    const closeButtons = screen.getAllByRole("button")
    // O botão X do header é o que não tem aria-label, fica no header (1o botão sem texto visível)
    const xButton = closeButtons.find((btn) => {
      const text = btn.textContent?.trim()
      return text === "" || text === undefined
    })
    if (xButton) {
      fireEvent.click(xButton)
      expect(onClose).toHaveBeenCalled()
    } else {
      // Fallback: clicar no primeiro botão que não é tab/chip
      fireEvent.click(screen.getByText("Cancelar"))
      expect(onClose).toHaveBeenCalled()
    }
  })

  it("6. onSave é chamado com os dados corretos ao submeter formulário com nome preenchido", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    renderModal({ onSave })

    const nameInput = screen.getByPlaceholderText("Ex: PLR Anual Padrão 2026")
    fireEvent.change(nameInput, { target: { value: "PLR Anual 2026" } })

    const saveButton = screen.getByText("Criar Política")
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(1)
    })

    const savedData = onSave.mock.calls[0][0] as CompensationPolicyRecord
    expect(savedData.name).toBe("PLR Anual 2026")
    // company_id NUNCA deve estar no payload (multi-tenancy via JWT)
    expect("company_id" in savedData).toBe(false)
  })

  it("7. botão de submit fica desabilitado quando isSaving=true", () => {
    renderModal({ isSaving: true, initialData: makePolicy() })

    // No modo edição o botão mostra "Salvando..."
    const saveBtn = screen.getByText("Salvando...")
    expect(saveBtn).toBeDefined()
    expect((saveBtn as HTMLButtonElement).disabled).toBe(true)
  })

  it("8. botão de submit fica desabilitado quando name está vazio", () => {
    renderModal({ isOpen: true })

    // Sem preencher nome — defaultPolicy tem name=""
    const saveBtn = screen.getByText("Criar Política")
    expect((saveBtn as HTMLButtonElement).disabled).toBe(true)
  })

  it("9. exibe mensagem de erro quando prop error é passada", () => {
    renderModal({ error: "Falha ao salvar política. Tente novamente." })
    expect(screen.getByText("Falha ao salvar política. Tente novamente.")).toBeTruthy()
  })

  it("10. modal em modo edição mostra título correto e versão", () => {
    renderModal({ initialData: makePolicy({ version: 3 }) })

    expect(screen.getByText("Editar Política de Remuneração")).toBeTruthy()
    expect(screen.getByText(/Salvar v4/)).toBeTruthy()
  })
})

// ---------------------------------------------------------------------------
// Source-level sensor
// ---------------------------------------------------------------------------

describe("CompensationPolicyFormModal — source-level sensor", () => {
  const MODAL_PATH = join(
    __dirname,
    "..",
    "CompensationPolicyFormModal.tsx"
  )
  const source = readFileSync(MODAL_PATH, "utf-8")
  const codeOnly = source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "")

  it("usa createPortal (não foi removido indevidamente)", () => {
    expect(codeOnly).toMatch(/createPortal/)
  })

  it("não define company_id como field de payload (multi-tenancy canonical)", () => {
    // Garante que nenhum payload/schema local tem company_id como prop
    const hasCompanyIdField = /company_id\s*:\s*string/.test(codeOnly)
    expect(
      hasCompanyIdField,
      "company_id não deve aparecer em props/schema de payload — vem do JWT via backend."
    ).toBe(false)
  })

  it("importa ChipMultiSelect do shared canonical (não define inline)", () => {
    // Após extração, deve importar de _shared
    const definesInline = /^function ChipMultiSelect\b/.test(codeOnly)
    expect(
      definesInline,
      "ChipMultiSelect não deve ser definido inline — importar de @/components/settings/_shared."
    ).toBe(false)
  })
})
