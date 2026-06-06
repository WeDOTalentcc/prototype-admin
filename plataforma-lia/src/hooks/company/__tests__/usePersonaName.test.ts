import { renderHook } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach } from "vitest"
import { usePersonaName } from "../usePersonaName"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

vi.mock("@/hooks/company/use-ai-persona", () => ({ useAiPersona: vi.fn() }))

const mockPersona = (v: unknown) => (useAiPersona as unknown as ReturnType<typeof vi.fn>).mockReturnValue(v)

describe("usePersonaName (white-label)", () => {
  beforeEach(() => vi.clearAllMocks())

  it("retorna o nome da persona configurada", () => {
    mockPersona({ persona: { name: "Sofia", tone: "profissional" } })
    const { result } = renderHook(() => usePersonaName())
    expect(result.current).toBe("Sofia")
  })

  it("default LIA quando sem persona", () => {
    mockPersona({ persona: null })
    const { result } = renderHook(() => usePersonaName())
    expect(result.current).toBe("LIA")
  })

  it("default LIA quando nome vazio/whitespace", () => {
    mockPersona({ persona: { name: "   " } })
    const { result } = renderHook(() => usePersonaName())
    expect(result.current).toBe("LIA")
  })
})
