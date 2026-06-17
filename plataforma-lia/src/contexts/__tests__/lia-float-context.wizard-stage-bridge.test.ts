/**
 * Sensor: LiaFloatContext bridges `lia:wizard-stage-payload` window event to
 * `openDynamicPanel`, garantindo que o painel direito do wizard abre quando
 * o backend emite `wizard_stage` via WebSocket.
 *
 * Audit context (2026-05-27 WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P0-NOVO-#2):
 *   O backend canonical (`agent_chat_ws.py:1146-1163`) emite APENAS `wizard_stage`
 *   ao avançar de etapa — nunca `panel_update`. O `useChatSocket.ts` dispatcha
 *   o window event `lia:wizard-stage-payload`, mas NÃO chama `openDynamicPanel`.
 *   Resultado: `state.dynamicPanel` permanece `null` durante todo o wizard.
 *   O gate `hasDynamicPanel = !!dynamicPanel && SPLIT_STAGES.includes(stage)`
 *   nunca dispara → painel HITL nunca renderiza → recrutador fica preso no
 *   chat sem ver botões de aprovação.
 *
 *   Fix #1 do commit f8043593d (adicionar jd_enrichment ao SPLIT_STAGES) foi
 *   condição necessária mas COMPLETAMENTE ineficaz isoladamente — faltava a
 *   bridge que este sensor protege.
 *
 * Guards (estruturais — regex sobre source file):
 *   1. useEffect registra listener para `lia:wizard-stage-payload`.
 *   2. Handler chama `openDynamicPanel` com payload do CustomEvent.detail.
 *   3. Payload mapeia `panelType: "job_creation"` (canonical wizard hint).
 *   4. Payload extrai `stage`, `data` e `requires_approval` do event.detail.
 *   5. useEffect retorna cleanup com `removeEventListener` (zero memory leak).
 *
 * Fix se falhar:
 *   Em `src/contexts/lia-float-context.tsx`, após a declaração de
 *   `openDynamicPanel`, adicionar useEffect:
 *
 *     useEffect(() => {
 *       if (typeof window === "undefined") return
 *       const handler = (e: Event) => {
 *         const detail = (e as CustomEvent).detail ?? {}
 *         openDynamicPanel({
 *           panelType: "job_creation",
 *           data: detail.data ?? {},
 *           stage: detail.stage,
 *           requires_approval: !!detail.requires_approval,
 *         })
 *       }
 *       window.addEventListener("lia:wizard-stage-payload", handler)
 *       return () => window.removeEventListener("lia:wizard-stage-payload", handler)
 *     }, [openDynamicPanel])
 *
 * Skill canônica: harness-engineering [sensor computacional].
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SRC = readFileSync(
  join(__dirname, "..", "lia-float-context.tsx"),
  "utf8",
)

describe("Fix B — wizard_stage → openDynamicPanel bridge", () => {
  test("Guard 1: useEffect listens for lia:wizard-stage-payload window event", () => {
    expect(SRC).toMatch(/addEventListener\(\s*["']lia:wizard-stage-payload["']/)
  })

  test("Guard 2: bridge handler calls openDynamicPanel", () => {
    // Find the section between addEventListener and removeEventListener of our event
    const bridgeRegion = SRC.split("lia:wizard-stage-payload")
    expect(bridgeRegion.length).toBeGreaterThanOrEqual(2)
    // Inspect the region around the handler — openDynamicPanel must be called
    // in the vicinity (within ~1500 chars of the listener registration).
    const aroundListener = SRC.substring(
      Math.max(0, SRC.indexOf('lia:wizard-stage-payload') - 1500),
      Math.min(SRC.length, SRC.indexOf('lia:wizard-stage-payload') + 1500),
    )
    expect(aroundListener).toMatch(/openDynamicPanel\(/)
  })

  test("Guard 3: bridge sets panelType = 'job_creation' (canonical wizard hint)", () => {
    const aroundListener = SRC.substring(
      Math.max(0, SRC.indexOf('lia:wizard-stage-payload') - 1500),
      Math.min(SRC.length, SRC.indexOf('lia:wizard-stage-payload') + 1500),
    )
    expect(aroundListener).toMatch(/panelType\s*:\s*["']job_creation["']/)
  })

  test("Guard 4: bridge extracts stage/data/requires_approval from event.detail", () => {
    const aroundListener = SRC.substring(
      Math.max(0, SRC.indexOf('lia:wizard-stage-payload') - 1500),
      Math.min(SRC.length, SRC.indexOf('lia:wizard-stage-payload') + 1500),
    )
    // Read at least these 3 fields from detail (or via destructuring)
    expect(aroundListener).toMatch(/(detail\.stage|stage\s*[,}])/)
    expect(aroundListener).toMatch(/(detail\.data|data\s*[,}])/)
    expect(aroundListener).toMatch(/(detail\.requires_approval|requires_approval)/)
  })

  test("Guard 5: useEffect cleanup removes the event listener (no memory leak)", () => {
    expect(SRC).toMatch(/removeEventListener\(\s*["']lia:wizard-stage-payload["']/)
  })
})
