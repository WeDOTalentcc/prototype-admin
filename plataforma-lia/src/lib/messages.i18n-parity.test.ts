import { readFileSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

import { describe, it, expect } from "vitest"

/**
 * Paridade i18n de TODO o app (Task #1318).
 *
 * A Task #1316 cobriu apenas o namespace `dynamicGreetings.*`. O restante das
 * strings de UI em `messages/pt-BR.json` e `messages/en.json` não tinha guarda
 * automática: se alguém adiciona um label/botão/mensagem em um idioma e esquece
 * o outro, o usuário vê silenciosamente a string no idioma errado (ou a chave
 * crua) — sem falha até produção.
 *
 * Este teste compara o conjunto COMPLETO de chaves dos dois arquivos e falha
 * listando qualquer chave presente em um e ausente no outro.
 *
 * Diferenças estruturais intencionais: NENHUMA. Os dois arquivos devem ter
 * exatamente o mesmo conjunto de chaves. Se uma divergência intencional surgir
 * no futuro, ela deve ser documentada explicitamente em `INTENTIONAL_DIFFS`
 * abaixo (e não simplesmente ignorada em silêncio).
 */

const dirname = path.dirname(fileURLToPath(import.meta.url))
const messagesDir = path.resolve(dirname, "../../messages")

/**
 * Chaves achatadas ("a.b.c") cuja ausência em um dos idiomas é intencional.
 * Mantenha vazio salvo divergência deliberada e documentada. Cada entrada deve
 * vir com um comentário explicando o porquê.
 */
const INTENTIONAL_DIFFS: ReadonlySet<string> = new Set<string>([
  // (nenhuma divergência intencional no momento)
])

function loadMessages(locale: string): Record<string, unknown> {
  const raw = readFileSync(path.join(messagesDir, `${locale}.json`), "utf-8")
  return JSON.parse(raw) as Record<string, unknown>
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

describe("messages — paridade i18n pt-BR ↔ en (app inteiro)", () => {
  const pt = loadMessages("pt-BR")
  const en = loadMessages("en")
  const ptKeys = [...flattenKeys(pt)].sort()
  const enKeys = [...flattenKeys(en)].sort()

  it("os arquivos não estão vazios (sanidade)", () => {
    expect(ptKeys.length).toBeGreaterThan(0)
    expect(enKeys.length).toBeGreaterThan(0)
  })

  it("toda chave de pt-BR existe em en", () => {
    const missingInEn = ptKeys.filter(
      (k) => !enKeys.includes(k) && !INTENTIONAL_DIFFS.has(k),
    )
    expect(
      missingInEn,
      `chaves presentes em pt-BR mas ausentes em en: ${missingInEn.join(", ")}`,
    ).toEqual([])
  })

  it("toda chave de en existe em pt-BR", () => {
    const missingInPt = enKeys.filter(
      (k) => !ptKeys.includes(k) && !INTENTIONAL_DIFFS.has(k),
    )
    expect(
      missingInPt,
      `chaves presentes em en mas ausentes em pt-BR: ${missingInPt.join(", ")}`,
    ).toEqual([])
  })

  it("o conjunto de chaves é idêntico nos dois idiomas", () => {
    const ptSet = new Set(ptKeys)
    const enSet = new Set(enKeys)
    const diff = [
      ...ptKeys.filter((k) => !enSet.has(k)),
      ...enKeys.filter((k) => !ptSet.has(k)),
    ].filter((k) => !INTENTIONAL_DIFFS.has(k))
    expect(
      diff,
      `divergência de chaves entre pt-BR e en: ${[...new Set(diff)].sort().join(", ")}`,
    ).toEqual([])
  })
})
