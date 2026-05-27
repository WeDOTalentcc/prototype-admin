/**
 * Sensor: SPLIT_STAGES cobre todos os stages que renderizam painel HITL no
 * split-view do wizard. Cruzamento estrutural entre 3 fontes canonical:
 *   - WizardStage Literal (wizard-types.ts) -- universo de stages.
 *   - renderPanel switch cases (DynamicContextPanel.tsx) -- stages com painel.
 *   - SPLIT_STAGES array (DynamicContextPanel.tsx) -- stages que abrem o
 *     split-view direito.
 *
 * Audit context (2026-05-27 WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P1-NOVO-#2):
 *   Fix #1 do commit f8043593d adicionou apenas `jd_enrichment` ao SPLIT_STAGES.
 *   Mas o renderPanel switch tem case para 13 stages (intake, bigfive, salary,
 *   competency, wsi_questions, eligibility, review, publish, calibration,
 *   handoff, done, scheduling). Painel desaparece silenciosamente quando
 *   wizard transita pra bigfive/competency/wsi_questions -- recrutador vê
 *   chat continuar mas perde a UI estruturada.
 *
 * Excluido intencionalmente do SPLIT_STAGES:
 *   - `pipeline_template`: renderizado FORA do gate hasDynamicPanel, inline
 *     em UnifiedChat.tsx via WizardPipelineTemplateStagePanel
 *     (gate proprio `wizard.currentStage === "pipeline_template"`).
 *
 * Guards (estruturais -- regex sobre source file):
 *   1. SPLIT_STAGES inclui todos os 7 stages HITL canonical (intake,
 *      jd_enrichment, bigfive, salary, competency, wsi_questions, eligibility).
 *   2. SPLIT_STAGES inclui todos os 6 stages post-publish canonical
 *      (review, publish, calibration, handoff, done, scheduling).
 *   3. Todo stage em SPLIT_STAGES tem case no renderPanel switch.
 *   4. WizardStage Literal cobre todos os stages do SPLIT_STAGES.
 *   5. `pipeline_template` deliberadamente NAO esta em SPLIT_STAGES (tem
 *      caminho de renderizacao proprio em UnifiedChat.tsx).
 *
 * Fix se falhar:
 *   Em `src/components/unified-chat/wizard/DynamicContextPanel.tsx`,
 *   expandir `SPLIT_STAGES` para incluir o(s) stage(s) ausente(s) E
 *   confirmar que renderPanel switch tem case correspondente.
 *
 * Skill canonica: harness-engineering [sensor computacional].
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SRC = readFileSync(
  join(__dirname, "..", "DynamicContextPanel.tsx"),
  "utf8",
)

const TYPES = readFileSync(
  join(__dirname, "..", "wizard-types.ts"),
  "utf8",
)

function extractSplitStages(src: string): string[] {
  const match = src.match(/SPLIT_STAGES\s*:\s*WizardStage\[\]\s*=\s*\[([\s\S]*?)\]/)
  if (!match) return []
  return Array.from(match[1].matchAll(/"([a-z_]+)"/g)).map((m) => m[1])
}

function extractSwitchCases(src: string): string[] {
  return Array.from(src.matchAll(/case\s+"([a-z_]+)":/g)).map((m) => m[1])
}

function extractLiteralStages(src: string): string[] {
  // type WizardStage = | "x" | "y" | ...
  const match = src.match(/type\s+WizardStage\s*=\s*([\s\S]*?)(?:\n\nexport\s+type|\n\nexport\s+const|\nexport\s+const)/)
  if (!match) return []
  return Array.from(match[1].matchAll(/"([a-z_]+)"/g)).map((m) => m[1])
}

const SPLIT_STAGES = extractSplitStages(SRC)
const SWITCH_CASES = extractSwitchCases(SRC)
const LITERAL_STAGES = extractLiteralStages(TYPES)

const HITL_STAGES_CANONICAL = [
  "intake",
  "jd_enrichment",
  "bigfive",
  "salary",
  "competency",
  "wsi_questions",
  "eligibility",
]

const POST_PUBLISH_STAGES_CANONICAL = [
  "review",
  "publish",
  "calibration",
  "handoff",
  "done",
  "scheduling",
]

describe("Fix C+I -- SPLIT_STAGES cross-TS/Python canonical sensor", () => {
  test("Guard 1: SPLIT_STAGES inclui todos os 7 stages HITL canonical", () => {
    for (const stage of HITL_STAGES_CANONICAL) {
      expect(SPLIT_STAGES).toContain(stage)
    }
  })

  test("Guard 2: SPLIT_STAGES inclui todos os 6 stages post-publish canonical", () => {
    for (const stage of POST_PUBLISH_STAGES_CANONICAL) {
      expect(SPLIT_STAGES).toContain(stage)
    }
  })

  test("Guard 3: todo stage em SPLIT_STAGES tem case no renderPanel switch", () => {
    for (const stage of SPLIT_STAGES) {
      expect(SWITCH_CASES).toContain(stage)
    }
  })

  test("Guard 4: WizardStage Literal cobre todos os stages em SPLIT_STAGES", () => {
    for (const stage of SPLIT_STAGES) {
      expect(LITERAL_STAGES).toContain(stage)
    }
  })

  test("Guard 5: pipeline_template NAO esta em SPLIT_STAGES (rendering proprio em UnifiedChat)", () => {
    expect(SPLIT_STAGES).not.toContain("pipeline_template")
    expect(LITERAL_STAGES).toContain("pipeline_template")
  })
})
