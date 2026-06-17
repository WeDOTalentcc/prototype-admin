/**
 * Sensor: useWizardIntegration escuta `lia:wizard-stage-payload` window event e
 * dispara handleWizardStepResponse + atualiza missingFields/activePanelType.
 *
 * Audit context (2026-05-27 WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P1-NOVO-#4):
 *   `handleWizardStepResponse` (useWizardIntegration.ts:79) processava
 *   wizard_step_response em message.metadata, mas NENHUM caller invocava o
 *   handler -- ele estava órfão desde a Onda 33. `missingFields` sempre vazio,
 *   banner "Campos obrigatórios em aberto" em UnifiedChat.tsx:948 nunca aparecia.
 *
 * Fix G: wire o handler via useEffect que escuta `lia:wizard-stage-payload`
 * (mesmo event canonical do Fix B). Extrai missing_fields do payload + chama
 * handler com adaptador para o shape original.
 *
 * Guards estruturais (regex sobre source file):
 *   1. useEffect registra listener para `lia:wizard-stage-payload`.
 *   2. Handler chama setMissingFields ou handleWizardStepResponse.
 *   3. Handler extrai missing_fields do detail.data.
 *   4. useEffect retorna cleanup com removeEventListener.
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SRC = readFileSync(
  join(__dirname, "..", "useWizardIntegration.ts"),
  "utf8",
)

describe("Fix G — wizard_stage_payload → handleWizardStepResponse bridge", () => {
  test("Guard 1: useEffect listens for lia:wizard-stage-payload", () => {
    expect(SRC).toMatch(/addEventListener\(\s*["']lia:wizard-stage-payload["']/)
  })

  test("Guard 2: bridge invokes setMissingFields ou handleWizardStepResponse", () => {
    const idx = SRC.indexOf("lia:wizard-stage-payload")
    expect(idx).toBeGreaterThan(-1)
    const window = SRC.substring(Math.max(0, idx - 1500), idx + 1500)
    const hasSetter = /setMissingFields\(|handleWizardStepResponse\(/.test(window)
    expect(hasSetter).toBe(true)
  })

  test("Guard 3: bridge extracts missing_fields do CustomEvent.detail", () => {
    const idx = SRC.indexOf("lia:wizard-stage-payload")
    const window = SRC.substring(Math.max(0, idx - 1500), idx + 1500)
    expect(window).toMatch(/missing_fields/)
  })

  test("Guard 4: useEffect cleanup remove listener (no memory leak)", () => {
    expect(SRC).toMatch(/removeEventListener\(\s*["']lia:wizard-stage-payload["']/)
  })
})
