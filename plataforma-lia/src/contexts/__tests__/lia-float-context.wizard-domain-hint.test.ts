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
 *   2. sendChatMessage reads the active panel via dynamicPanelRef (Bug 2).
 *   3. enrichedMetadata sets source: "rail_a" and uses the mapped domain_hint.
 *   4. (Bug 2) sendChatMessage é ESTÁVEL — não depende de state.dynamicPanel
 *      (lê via ref sincronizado), evitando churn dos listeners WSI.
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

  test("Guard 2: sendChatMessage lê o panelType do painel ativo via ref", () => {
    // Bug 2: lê via dynamicPanelRef.current (ref sincronizado todo render),
    // não via state.dynamicPanel direto — mantém o callback estável.
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toBeDefined()
    expect(sendBlock).toMatch(/dynamicPanelRef\.current\?\.panelType/)
  })

  test("Guard 3: enriched metadata sets source 'rail_a' and uses mapped domain_hint", () => {
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toMatch(/source\s*:\s*[^,]*["']rail_a["']/)
    expect(sendBlock).toMatch(/domain_hint\s*:\s*hintDomain/)
  })

  test("Guard 4 (Bug 2): sendChatMessage estável — NÃO depende de state.dynamicPanel", () => {
    // Bug 2: state.dynamicPanel no dep array recriava sendChatMessage a cada
    // wizard_stage -> churn dos listeners de edit/regenerate WSI -> loop.
    // Agora o painel ativo é lido via dynamicPanelRef (sincronizado todo
    // render), então o callback não precisa de state.dynamicPanel nas deps.
    const sendBlock = SRC.split("const sendChatMessage")[1].split(
      "const sendOrchestratedMessage",
    )[0]
    expect(sendBlock).not.toMatch(/state\.dynamicPanel/)
    // O ref deve ser sincronizado no corpo do provider.
    expect(SRC).toMatch(/dynamicPanelRef\.current\s*=\s*state\.dynamicPanel/)
  })

  test("Guard 5: caller-provided metadata.domain_hint not overridden", () => {
    // The conditional must check `!metadata?.domain_hint` so explicit
    // caller hints win (e.g., Rail A card click setting its own hint).
    const sendBlock = SRC.split("const sendChatMessage")[1]
    expect(sendBlock).toMatch(/!metadata\?\.domain_hint/)
  })
})
