/**
 * Sentinel test (Task #1198) — guarantee category i18n keys never break the
 * Estúdio de Agentes again.
 *
 * Bug history: MISSING_MESSAGE errors blew up the Agent Studio because category
 * keys were missing from the translation files. There was no automated check, so
 * adding a brand-new AgentCategory (or accidentally removing a key) could silently
 * reintroduce the crash in production.
 *
 * This test asserts that EVERY canonical AgentCategory (via CATEGORY_KEYS) has a
 * matching translation in both `agents.customAgents.categories` and
 * `agents.customAgents.templateCategories`, in BOTH locales (pt-BR + en).
 * Adding a new category to the type without its translation fails the build.
 */
import { describe, it, expect } from "vitest"

import { CATEGORY_KEYS, type AgentCategory } from "../types"

import ptBR from "../../../../../messages/pt-BR.json"
import en from "../../../../../messages/en.json"

const LOCALES = {
  "pt-BR": ptBR as Record<string, any>,
  en: en as Record<string, any>,
}

const I18N_KEYS = Object.values(CATEGORY_KEYS)

describe("Agent Studio — category i18n coverage (Task #1198)", () => {
  it("CATEGORY_KEYS covers every canonical AgentCategory", () => {
    const canonical: AgentCategory[] = [
      "screening",
      "sourcing",
      "communication",
      "analytics",
      "job_management",
      "automation",
      "general",
    ]
    expect(Object.keys(CATEGORY_KEYS).sort()).toEqual([...canonical].sort())
  })

  for (const [locale, messages] of Object.entries(LOCALES)) {
    const customAgents = messages?.agents?.customAgents

    it(`[${locale}] has agents.customAgents.categories + templateCategories blocks`, () => {
      expect(customAgents).toBeTruthy()
      expect(customAgents.categories).toBeTruthy()
      expect(customAgents.templateCategories).toBeTruthy()
    })

    for (const key of I18N_KEYS) {
      it(`[${locale}] categories.${key} is translated`, () => {
        const value = customAgents?.categories?.[key]
        expect(value, `Missing agents.customAgents.categories.${key} in ${locale}`).toBeTruthy()
        expect(typeof value).toBe("string")
      })

      it(`[${locale}] templateCategories.${key} is translated`, () => {
        const value = customAgents?.templateCategories?.[key]
        expect(
          value,
          `Missing agents.customAgents.templateCategories.${key} in ${locale}`,
        ).toBeTruthy()
        expect(typeof value).toBe("string")
      })
    }
  }
})
