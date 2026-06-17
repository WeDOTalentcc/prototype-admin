/**
 * Sensor (audit P1-2 2026-06-05): proveniência do score do JD.
 *
 * O score exibido em JDEvaluationHeader (`{evaluation.score}/100`) mede os campos
 * ESTRUTURADOS/canônicos (responsabilidades, competências, critérios D1–D9), NÃO o
 * texto livre mostrado em "DESCRIÇÃO ENRIQUECIDA (LIA)". Sem microcopy, o recrutador
 * pode achar que o número avalia a prosa gerada pela LIA. Este sentinel garante que a
 * clarificação não regrida (source-level, sem render — espelha o padrão .sentinel).
 */
import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const __dir = dirname(fileURLToPath(import.meta.url))
const SRC = readFileSync(join(__dir, "..", "JDEvaluationHeader.tsx"), "utf-8")

describe("JDEvaluationHeader — proveniência do score (audit P1-2)", () => {
  it("microcopy esclarece que o score mede campos estruturados", () => {
    expect(SRC).toMatch(/campos estruturados/i)
  })

  it("microcopy deixa claro que NÃO é o texto livre da descrição enriquecida", () => {
    expect(SRC).toMatch(/n[aã]o\s+o\s+texto\s+livre/i)
  })
})
