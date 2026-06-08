import { readFileSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

import { describe, it, expect } from "vitest"

import {
  selectGreeting,
  type GreetingBriefingInput,
  type GreetingSurface,
} from "./dynamic-greeting"

/**
 * Paridade i18n das saudações dinâmicas (Task #1316).
 *
 * As frases de abertura leem chaves do namespace `dynamicGreetings.*`. Se alguém
 * adicionar um ramo novo em `selectGreeting` e esquecer uma tradução, o usuário
 * cai silenciosamente no `fallback` (sem erro em dev até virar produção).
 *
 * Estes testes garantem que:
 *  1. O conjunto de chaves `dynamicGreetings.*` é IDÊNTICO em pt-BR e en.
 *  2. TODA chave que `selectGreeting` consegue emitir (chat + funnel, contextual
 *     e curada, com/sem nome, todas as faixas horárias) existe em AMBOS os JSONs.
 */

const dirname = path.dirname(fileURLToPath(import.meta.url))
const messagesDir = path.resolve(dirname, "../../messages")

function loadGreetings(locale: string): Record<string, unknown> {
  const raw = readFileSync(path.join(messagesDir, `${locale}.json`), "utf-8")
  const parsed = JSON.parse(raw) as { dynamicGreetings?: Record<string, unknown> }
  expect(parsed.dynamicGreetings, `${locale}.json deve ter o namespace dynamicGreetings`).toBeTruthy()
  return parsed.dynamicGreetings as Record<string, unknown>
}

/** Achata um objeto em chaves "a.b.c". Arrays viram uma folha (não recursam). */
function flattenKeys(obj: unknown, prefix = ""): Set<string> {
  const keys = new Set<string>()
  if (obj === null || typeof obj !== "object" || Array.isArray(obj)) {
    if (prefix) keys.add(prefix)
    return keys
  }
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const next = prefix ? `${prefix}.${k}` : k
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      for (const nested of flattenKeys(v, next)) keys.add(nested)
    } else {
      keys.add(next)
    }
  }
  return keys
}

/** Resolve uma chave "a.b.c" dentro do objeto; retorna undefined se faltar. */
function resolveKey(obj: Record<string, unknown>, dotted: string): unknown {
  return dotted.split(".").reduce<unknown>((acc, part) => {
    if (acc !== null && typeof acc === "object" && !Array.isArray(acc)) {
      return (acc as Record<string, unknown>)[part]
    }
    return undefined
  }, obj)
}

/**
 * Deriva TODAS as chaves i18n que o builder pode referenciar exercitando
 * `selectGreeting` por toda a matriz de entradas relevantes.
 */
function collectReferencedKeys(): Set<string> {
  const keys = new Set<string>()
  // timeOfDay é sempre referenciado (greeting de qualquer plano).
  keys.add("timeOfDay.morning")
  keys.add("timeOfDay.afternoon")
  keys.add("timeOfDay.evening")

  const surfaces: GreetingSurface[] = ["chat", "funnel"]
  const flags = [0, 1]
  const names: (string | null)[] = [null, "Ana"]
  const hours = [9, 14, 20] // morning / afternoon / evening

  for (const surface of surfaces) {
    for (const name of names) {
      for (const hour of hours) {
        for (const aj of flags)
          for (const ctc of flags)
            for (const af of flags)
              for (const op of flags)
                for (const it of flags) {
                  const briefing: GreetingBriefingInput = {
                    activeJobs: aj,
                    candidatesToContact: ctc,
                    awaitingFeedback: af,
                    offersPending: op,
                    interviewsToday: it,
                  }
                  for (const input of [null, briefing] as (GreetingBriefingInput | null)[]) {
                    const plan = selectGreeting({
                      surface,
                      now: new Date(2026, 5, 5, hour, 0, 0),
                      briefing: input,
                      name,
                      seed: 1,
                    })
                    if (plan.kind === "context") {
                      keys.add(`${surface}.context.${plan.key}`)
                    } else {
                      keys.add(plan.named ? `${surface}.curatedNamed` : `${surface}.curated`)
                    }
                  }
                }
      }
    }
  }

  return keys
}

describe("dynamicGreetings — paridade i18n pt-BR ↔ en", () => {
  const pt = loadGreetings("pt-BR")
  const en = loadGreetings("en")

  it("o conjunto de chaves é idêntico nos dois idiomas", () => {
    const ptKeys = [...flattenKeys(pt)].sort()
    const enKeys = [...flattenKeys(en)].sort()

    const missingInEn = ptKeys.filter((k) => !enKeys.includes(k))
    const missingInPt = enKeys.filter((k) => !ptKeys.includes(k))

    expect(missingInEn, `chaves presentes em pt-BR mas ausentes em en: ${missingInEn.join(", ")}`).toEqual([])
    expect(missingInPt, `chaves presentes em en mas ausentes em pt-BR: ${missingInPt.join(", ")}`).toEqual([])
  })
})

describe("dynamicGreetings — toda chave usada por selectGreeting existe", () => {
  const pt = loadGreetings("pt-BR")
  const en = loadGreetings("en")
  const referenced = [...collectReferencedKeys()].sort()

  it("sanidade: a matriz cobre os ramos contextuais e curados conhecidos", () => {
    // Garante que o coletor realmente exercita os ramos esperados — se o builder
    // mudar e parar de emitir algum destes, este teste sinaliza antes da paridade.
    for (const expected of [
      "chat.context.interviewsAndFeedback",
      "chat.context.interviewsAndFeedbackAnon",
      "chat.context.interviewsToday",
      "chat.context.interviewsTodayAnon",
      "chat.context.candidatesToContact",
      "chat.context.candidatesToContactAnon",
      "chat.context.offersPending",
      "chat.context.offersPendingAnon",
      "chat.context.allClear",
      "chat.context.allClearAnon",
      "chat.curated",
      "chat.curatedNamed",
      "funnel.context.openJobsAndContacts",
      "funnel.context.openJobs",
      "funnel.context.candidatesToContact",
      "funnel.curated",
    ]) {
      expect(referenced, `coletor deveria incluir ${expected}`).toContain(expected)
    }
  })

  it.each(["pt-BR", "en"] as const)("%s define todas as chaves referenciadas", (locale) => {
    const dict = locale === "pt-BR" ? pt : en
    for (const key of referenced) {
      const value = resolveKey(dict, key)
      expect(value, `${locale}.json: dynamicGreetings.${key} ausente ou vazio`).toBeTruthy()
      if (key.endsWith(".curated") || key.endsWith(".curatedNamed")) {
        expect(Array.isArray(value), `${locale}.json: dynamicGreetings.${key} deve ser array`).toBe(true)
        expect((value as unknown[]).length, `${locale}.json: dynamicGreetings.${key} não pode ser vazio`).toBeGreaterThan(0)
      } else {
        expect(typeof value, `${locale}.json: dynamicGreetings.${key} deve ser string`).toBe("string")
      }
    }
  })
})
