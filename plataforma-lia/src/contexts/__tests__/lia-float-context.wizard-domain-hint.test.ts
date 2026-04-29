/**
 * Sensor: LiaFloatContext.sendChatMessage enriches metadata with Rail A hint
 * when a dynamic panel is active.
 *
 * Audit context (2026-04-29 wizard-domain-hint-leak):
 *   While the job_creation wizard panel is active, mid-wizard messages were
 *   leaking into the `job_management` domain via the vector cache (Tier 3,
 *   cosine ≥0.85). The fix injects `metadata.{source: "rail_a", domain_hint}`
 *   in `sendChatMessage` so backend Tier -1 (`rail_a_hint_override`) routes
 *   deterministically with confidence=0.99, bypassing the vector cache.
 *
 * Guards (structural — read source file, regex over expected patterns):
 *   1. PANEL_TYPE_TO_DOMAIN_HINT map exists and contains job_creation: "wizard".
 *   2. sendChatMessage reads state.dynamicPanel?.panelType.
 *   3. enrichedMetadata sets source: "rail_a" and uses the mapped domain_hint.
 *   4. useCallback dependency array includes state.dynamicPanel.
 *   5. Caller-provided metadata.domain_hint takes precedence (no override).
 *
 * Fix se falhar:
 *   Verificar `src/contexts/lia-float-context.tsx` — sendChatMessage deve
 *   consultar PANEL_TYPE_TO_DOMAIN_HINT[state.dynamicPanel?.panelType] e,
 *   quando match, injetar source/card_id/domain_hint em metadata antes de
 *   passar para connection.sendMessage. Mapping panel→domain_hint deve
 *   estar exportado/visível no topo do arquivo.
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

describe("PR-A FE — wizard domain_hint injection", () => {
  test("Guard 1: PANEL_TYPE_TO_DOMAIN_HINT map declared with job_creation → wizard", () => {
    expect(SRC).toMatch(/PANEL_TYPE_TO_DOMAIN_HINT[^=]*=/)
    // Loose match on the wizard mapping (allow whitespace / quotes variation).
    expect(SRC).toMatch(/job_creation\s*:\s*["']wizard["']/)
  })

  test("Guard 2: sendChatMessage reads state.dynamicPanel?.panelType", () => {
    // We expect a read of dynamicPanel.panelType inside (or around) sendChatMessage.
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toBeDefined()
    expect(sendBlock).toMatch(/dynamicPanel\?\.panelType/)
  })

  test("Guard 3: enriched metadata sets source 'rail_a' and uses mapped domain_hint", () => {
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toMatch(/source\s*:\s*[^,]*["']rail_a["']/)
    expect(sendBlock).toMatch(/domain_hint\s*:\s*hintDomain/)
  })

  test("Guard 4: useCallback deps include state.dynamicPanel", () => {
    // After the closure body, the deps array must include state.dynamicPanel.
    const sendBlock = SRC.split("const sendChatMessage")[1]
    // Find the deps array — first ']' followed by ')' after the closure.
    expect(sendBlock).toMatch(/\[[^\]]*state\.dynamicPanel[^\]]*\]/)
  })

  test("Guard 5: caller-provided metadata.domain_hint not overridden", () => {
    // The conditional must check `!metadata?.domain_hint` so explicit
    // caller hints win (e.g., Rail A card click setting its own hint).
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toMatch(/!metadata\?\.domain_hint/)
  })
})
