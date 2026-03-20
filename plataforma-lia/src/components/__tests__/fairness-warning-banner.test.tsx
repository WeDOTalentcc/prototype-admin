/**
 * Tests — FairnessWarningBanner (FAR-2/C)
 *
 * Testa a lógica do componente sem dependência de @testing-library/dom
 * (pré-requisito ausente no ambiente de CI).
 */
import { describe, it, expect, vi } from "vitest"
import { FairnessWarningBanner } from "../fairness-warning-banner"

describe("FairnessWarningBanner — estrutura e exports", () => {
  it("componente é exportado como função", () => {
    expect(typeof FairnessWarningBanner).toBe("function")
  })

  it("componente aceita props warnings e onDismiss", () => {
    // Verificar que o componente pode ser chamado com os props corretos
    // (sem renderização DOM — ambiente sem @testing-library/dom)
    const props = { warnings: ["Aviso de viés"], onDismiss: vi.fn() }
    expect(() => FairnessWarningBanner(props)).not.toThrow()
  })

  it("retorna null para warnings vazio", () => {
    const result = FairnessWarningBanner({ warnings: [], onDismiss: vi.fn() })
    expect(result).toBeNull()
  })

  it("retorna elemento React para warnings não-vazio", () => {
    const result = FairnessWarningBanner({
      warnings: ["Viés socioeconômico detectado"],
      onDismiss: vi.fn(),
    })
    expect(result).not.toBeNull()
  })

  it("não chama onDismiss na renderização inicial", () => {
    const onDismiss = vi.fn()
    FairnessWarningBanner({ warnings: ["Aviso"], onDismiss })
    expect(onDismiss).not.toHaveBeenCalled()
  })
})
