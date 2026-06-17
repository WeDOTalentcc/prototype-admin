/**
 * Fase 3 Sprint 5 (2026-05-30) — sensor do mapeamento categoria => acento.
 *
 * Garante que:
 *  - TODA AgentCategory canonical tem entrada em CATEGORY_ACCENT_TOKEN (build
 *    quebra se alguém adicionar categoria sem acento).
 *  - O acento é CONTIDO (bg /12 + text no token) e CYAN-EXCLUÍDO.
 *  - `general` é deliberadamente neutro (sem acento de categoria).
 *  - Nenhum token de acento contém "cyan" (white-label: cyan reservado à
 *    assistente da plataforma).
 */
import { describe, it, expect } from "vitest"
import {
  CATEGORY_ACCENT_TOKEN,
  categoryAvatarClasses,
} from "../category-accent"
import { CATEGORY_KEYS, type AgentCategory } from "@/components/pages-agent-studio/custom-agents/types"

const CANONICAL: AgentCategory[] = [
  "screening",
  "sourcing",
  "communication",
  "analytics",
  "job_management",
  "automation",
  "general",
]

describe("category-accent — mapeamento canonical", () => {
  it("cobre TODA AgentCategory canonical (sync com CATEGORY_KEYS)", () => {
    expect(Object.keys(CATEGORY_ACCENT_TOKEN).sort()).toEqual([...CANONICAL].sort())
    // Sincronia com a fonte de verdade de categorias.
    expect(Object.keys(CATEGORY_ACCENT_TOKEN).sort()).toEqual(
      Object.keys(CATEGORY_KEYS).sort(),
    )
  })

  it("general é neutro (sem acento de categoria)", () => {
    expect(CATEGORY_ACCENT_TOKEN.general).toBeNull()
    const cls = categoryAvatarClasses("general")
    expect(cls.bg).toContain("bg-powder")
    expect(cls.text).toContain("text-graphite")
    expect(cls.bg).not.toContain("agent-cat-")
  })

  it("categorias com acento usam token agent-cat-* + bg tonal /12 (contido)", () => {
    for (const cat of CANONICAL) {
      if (cat === "general") continue
      const token = CATEGORY_ACCENT_TOKEN[cat]
      expect(token, `categoria ${cat} sem token`).toBeTruthy()
      expect(token).toMatch(/^agent-cat-/)
      const cls = categoryAvatarClasses(cat)
      // Fundo tonal sutil (12%) — contido, não card inteiro saturado.
      expect(cls.bg).toBe(`bg-${token}/12`)
      expect(cls.text).toBe(`text-${token}`)
    }
  })

  it("NENHUM acento usa cyan (white-label: cyan exclusivo da assistente)", () => {
    for (const cat of CANONICAL) {
      const token = CATEGORY_ACCENT_TOKEN[cat]
      if (!token) continue
      expect(token.toLowerCase()).not.toContain("cyan")
      const cls = categoryAvatarClasses(cat)
      expect(cls.bg.toLowerCase()).not.toContain("cyan")
      expect(cls.text.toLowerCase()).not.toContain("cyan")
    }
  })

  it("NENHUM acento usa cores primárias 500 cruas do Tailwind", () => {
    // O acento deve ser sempre um token canonical agent-cat-*, nunca
    // amber-500/rose-500/violet-500 (o multicolor saturado removido na Sprint 1).
    for (const cat of CANONICAL) {
      const cls = categoryAvatarClasses(cat)
      expect(cls.bg).not.toMatch(/-(amber|rose|violet|emerald|sky|blue|red|green|purple)-\d{3}/)
      expect(cls.text).not.toMatch(/-(amber|rose|violet|emerald|sky|blue|red|green|purple)-\d{3}/)
    }
  })
})
