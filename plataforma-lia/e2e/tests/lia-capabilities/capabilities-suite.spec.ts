/**
 * LIA Capabilities Suite — Camada 1 (Functional)
 *
 * Executa 1 teste por capability mapeada em catalog.ts. Cada teste:
 *   1. (opcional) navega para a página de contexto
 *   2. envia o prompt via chat
 *   3. valida HTTP 200, content não-vazio, menções esperadas/proibidas
 *
 * Rodar (contra Replit via proxy local na porta 3333):
 *   PLAYWRIGHT_BASE_URL=http://localhost:3333 \
 *     npx playwright test lia-capabilities/capabilities-suite
 *
 * Filtrar por severidade:
 *   npx playwright test lia-capabilities/capabilities-suite -g "@critical"
 *
 * Filtrar por domínio:
 *   npx playwright test lia-capabilities/capabilities-suite -g "@domain:jobs-mgmt"
 */
import { test } from "@playwright/test"
import {
  sendPromptAndCapture,
  expectCapabilitySuccess,
  navigateToPage,
  recordResult,
} from "./helpers"
import { CAPABILITIES } from "./catalog"

const LOCALE_HOME = "/pt"

test.describe("LIA Capabilities", () => {
  for (const cap of CAPABILITIES) {
    const tags = [`@${cap.severity}`, `@domain:${cap.domain}`]
    if (cap.relatedBug) tags.push(`@${cap.relatedBug}`)

    test(
      `${cap.id} — ${cap.prompt.slice(0, 60)} ${tags.join(" ")}`,
      async ({ page }) => {
        await page.goto(LOCALE_HOME, { waitUntil: "domcontentloaded" })
        await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {})

        if (cap.pageContext) {
          await navigateToPage(page, cap.pageContext)
        }

        try {
          const result = await sendPromptAndCapture(page, cap.prompt, 25000)

          expectCapabilitySuccess(result, {
            shouldMention: cap.shouldMention,
            shouldNotMention: cap.shouldNotMention,
            minContentLength: 5,
            allowLenientFail: cap.allowLenientFail,
          })

          recordResult({
            id: cap.id,
            prompt: cap.prompt,
            domain: cap.domain,
            status: "PASS",
            durationMs: result.durationMs,
          })
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err)
          recordResult({
            id: cap.id,
            prompt: cap.prompt,
            domain: cap.domain,
            status: "FAIL",
            durationMs: 0,
            errorMessage: msg.slice(0, 500),
          })
          throw err
        }
      },
    )
  }
})
