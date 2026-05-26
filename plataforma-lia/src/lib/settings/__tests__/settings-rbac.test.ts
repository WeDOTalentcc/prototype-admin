/**
 * Smoke test — settings-rbac (P2-3 audit 2026-05-26).
 * Cobre acceptance criteria:
 *  1. Cada role tem permissão definida para todos os hubs canonical
 *  2. Helpers getHubPermission, isHubVisible, canEditHub funcionam
 *  3. Fail-secure: role null → hidden
 */
import { describe, it, expect } from "vitest"
import {
  SETTINGS_HUB_PERMISSIONS,
  getHubPermission,
  isHubVisible,
  canEditHub,
} from "@/lib/settings/settings-rbac"

const ALL_HUBS = [
  "minha-empresa",
  "lia-personalizacao",
  "recrutamento-lia",
  "comunicacao-alertas",
  "usuarios-departamentos",
  "integrations",
  "ai-credits",
  "fairness-compliance",
]

const ALL_ROLES = ["admin", "manager", "recruiter", "viewer"] as const

describe("settings-rbac — P2-3 matrix completude", () => {
  it("matriz canonical define permissão pra TODOS os 8 hubs", () => {
    for (const hub of ALL_HUBS) {
      expect(SETTINGS_HUB_PERMISSIONS[hub]).toBeDefined()
    }
  })

  it("cada hub define permissão pra TODAS as 4 roles", () => {
    for (const hub of ALL_HUBS) {
      for (const role of ALL_ROLES) {
        const perm = SETTINGS_HUB_PERMISSIONS[hub]?.[role]
        expect(perm).toBeDefined()
        expect(["edit", "view", "hidden"]).toContain(perm)
      }
    }
  })

  it("admin pode editar TUDO (default canonical)", () => {
    for (const hub of ALL_HUBS) {
      expect(canEditHub(hub, "admin")).toBe(true)
    }
  })

  it("viewer só vê hubs que são view-only de natureza", () => {
    expect(isHubVisible("minha-empresa", "viewer")).toBe(true)
    expect(isHubVisible("recrutamento-lia", "viewer")).toBe(true)
    expect(isHubVisible("fairness-compliance", "viewer")).toBe(true)

    expect(isHubVisible("usuarios-departamentos", "viewer")).toBe(false)
    expect(isHubVisible("integrations", "viewer")).toBe(false)
    expect(isHubVisible("ai-credits", "viewer")).toBe(false)
  })

  it("recruiter NÃO acessa users/integrations (settings de plataforma)", () => {
    expect(isHubVisible("usuarios-departamentos", "recruiter")).toBe(false)
    expect(isHubVisible("integrations", "recruiter")).toBe(false)
  })

  it("recruiter EDITA hubs operacionais (Recrutamento, Comunicação)", () => {
    expect(canEditHub("recrutamento-lia", "recruiter")).toBe(true)
    expect(canEditHub("comunicacao-alertas", "recruiter")).toBe(true)
  })

  it("fail-secure: role null/undefined → hidden", () => {
    expect(getHubPermission("minha-empresa", null)).toBe("hidden")
    expect(getHubPermission("minha-empresa", undefined)).toBe("hidden")
    expect(isHubVisible("minha-empresa", null)).toBe(false)
  })

  it("fail-secure: role desconhecida → hidden", () => {
    expect(getHubPermission("minha-empresa", "hacker")).toBe("hidden")
  })

  it("fail-secure: hub desconhecido → hidden", () => {
    expect(getHubPermission("unknown-hub", "admin")).toBe("hidden")
  })
})
