/**
 * P2-B — Testes unitários: useCurrentScope + resolveScopeFromPathname
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. /funil → talent_funnel
 * 2. /funil-de-talentos → talent_funnel
 * 3. /funil/qualquer-sub → talent_funnel
 * 4. /jobs (exato) → job_table
 * 5. /jobs/ (trailing slash) → job_table
 * 6. /jobs/123 → in_job
 * 7. /jobs/abc-uuid/pipeline → in_job
 * 8. / (raiz) → global
 * 9. /admin/configuracoes → global
 * 10. "" (vazio) → global
 * 11. Hook retorna scopeName PT-BR correto
 * 12. Hook retorna global quando pathname é null
 */

import { resolveScopeFromPathname } from "../company/use-current-scope"

describe("resolveScopeFromPathname — mapeamento de URL para PromptScope", () => {

  describe("TALENT_FUNNEL — rotas de candidatos/funil", () => {
    it("/funil-de-talentos → talent_funnel", () => {
      expect(resolveScopeFromPathname("/funil-de-talentos")).toBe("talent_funnel")
    })

    it("/funil/candidatos → talent_funnel (sub-rota)", () => {
      expect(resolveScopeFromPathname("/funil/candidatos")).toBe("talent_funnel")
    })

    it("/funil-de-talentos/abc → talent_funnel (sub-rota)", () => {
      expect(resolveScopeFromPathname("/funil-de-talentos/abc")).toBe("talent_funnel")
    })
  })

  describe("JOB_TABLE — listagem de vagas", () => {
    it("/jobs → job_table", () => {
      expect(resolveScopeFromPathname("/jobs")).toBe("job_table")
    })

    it("/jobs/ → job_table (trailing slash)", () => {
      expect(resolveScopeFromPathname("/jobs/")).toBe("job_table")
    })
  })

  describe("IN_JOB — dentro de uma vaga específica", () => {
    it("/jobs/123 → in_job", () => {
      expect(resolveScopeFromPathname("/jobs/123")).toBe("in_job")
    })

    it("/jobs/abc-uuid/pipeline → in_job (sub-rota da vaga)", () => {
      expect(resolveScopeFromPathname("/jobs/abc-uuid/pipeline")).toBe("in_job")
    })

    it("/jobs/uuid-completo/candidatos → in_job", () => {
      expect(resolveScopeFromPathname("/jobs/a1b2c3d4/candidatos")).toBe("in_job")
    })
  })

  describe("GLOBAL — tudo o mais", () => {
    it("/ → global", () => {
      expect(resolveScopeFromPathname("/")).toBe("global")
    })

    it("/admin/configuracoes → global", () => {
      expect(resolveScopeFromPathname("/admin/configuracoes")).toBe("global")
    })

    it("/chat → global", () => {
      expect(resolveScopeFromPathname("/chat")).toBe("global")
    })

    it("string vazia → global", () => {
      expect(resolveScopeFromPathname("")).toBe("global")
    })
  })
})

// ── Testes do hook useCurrentScope via mock de usePathname ──────────────────

import { renderHook } from "@testing-library/react"
import { useCurrentScope } from "../company/use-current-scope"

// Mocka next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(),
}))

import { usePathname } from "next/navigation"
const mockUsePathname = usePathname as ReturnType<typeof vi.fn>

describe("useCurrentScope — hook com usePathname mockado", () => {
  it("retorna scope e scopeName corretos para /funil", () => {
    mockUsePathname.mockReturnValue("/funil-de-talentos")
    const { result } = renderHook(() => useCurrentScope())
    expect(result.current.scope).toBe("talent_funnel")
    expect(result.current.scopeName).toBe("Funil de Talentos")
  })

  it("retorna scope e scopeName corretos para /jobs", () => {
    mockUsePathname.mockReturnValue("/jobs")
    const { result } = renderHook(() => useCurrentScope())
    expect(result.current.scope).toBe("job_table")
    expect(result.current.scopeName).toBe("Vagas")
  })

  it("retorna scope in_job para /jobs/123", () => {
    mockUsePathname.mockReturnValue("/jobs/123")
    const { result } = renderHook(() => useCurrentScope())
    expect(result.current.scope).toBe("in_job")
    expect(result.current.scopeName).toBe("Vaga Específica")
  })

  it("retorna global quando pathname é null", () => {
    mockUsePathname.mockReturnValue(null)
    const { result } = renderHook(() => useCurrentScope())
    expect(result.current.scope).toBe("global")
    expect(result.current.scopeName).toBe("Global")
  })
})
