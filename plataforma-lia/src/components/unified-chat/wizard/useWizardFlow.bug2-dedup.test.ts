/**
 * Sensor (Bug 2 — 2026-05-29): o reducer STAGE_UPDATE faz dedup estrutural.
 *
 * Quando o backend re-emite o MESMO wizard_stage (ex: wsi_questions com
 * requires_approval após um edit/regenerate), sem dedup o reducer criava um
 * novo objeto `stageData` a cada dispatch, realimentando useWizardChatCards +
 * o bridge do provider -> re-render contínuo (loop). O dedup retorna o MESMO
 * objeto `state` quando stage/completeness/requires_approval/stageData são
 * estruturalmente iguais, quebrando o ciclo.
 *
 * Sensor estrutural (harness-engineering [computacional]) — o reducer não é
 * exportado, então validamos o invariante por leitura do source.
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SRC = readFileSync(join(__dirname, "useWizardFlow.ts"), "utf8")

describe("Bug 2 — STAGE_UPDATE dedup estrutural", () => {
  test("o case STAGE_UPDATE curto-circuita payload idêntico retornando o mesmo state", () => {
    const block = SRC.split('case "STAGE_UPDATE"')[1]?.split("case ")[0]
    expect(block).toBeDefined()
    // Compara stageData estruturalmente (JSON.stringify) com o atual.
    expect(block).toMatch(
      /JSON\.stringify\(state\.stageData\)\s*===\s*JSON\.stringify\(safeData\)/,
    )
    // E retorna o MESMO objeto state (sem criar novo) quando tudo bate.
    expect(block).toMatch(/return state\b/)
    // O guard cobre os 4 campos canônicos do payload.
    expect(block).toMatch(/state\.currentStage\s*===\s*stage/)
    expect(block).toMatch(/state\.completeness\s*===\s*completeness/)
    expect(block).toMatch(/state\.requiresApproval\s*===\s*\(requires_approval/)
  })
})
