/**
 * Task #1165 — Roteamento e split-view coerentes.
 *
 * Garante o contrato UX:
 *
 *  (A) Quando o recrutador já está em `/chat` e digita uma intenção de
 *      criação de vaga, a LIA NÃO faz `router.push('/vagas')` cego — o
 *      hint é suprimido em `useNavigationIntent` (helper puro
 *      `resolveNavigationIntentMode`) e o fluxo segue em chat.
 *
 *  (B) Quando o recrutador está fora de `/vagas`, a LIA PERGUNTA via chat
 *      antes de empurrar a rota. A resposta livre PT-BR ("sim", "vamos",
 *      "agora não" etc.) é classificada por `classifyNavConfirmation` no
 *      `DashboardApp`. Só `yes` dispara o push; `no` apenas reconhece.
 *
 *  (C) Quando o wizard transita para uma SPLIT_STAGE (review/publish/
 *      calibration/handoff/done/scheduling), `useWizardFlow` emite o
 *      próprio `lia:navigation-hint` com `mode: "ask"` propondo a
 *      transição para o ambiente dedicado.
 *
 * Os asserts E2E focam no comportamento observável (URL e mensagens no
 * chat). A lógica fina vive nos testes unitários
 * `src/hooks/__tests__/use-navigation-intent.context.test.ts` e
 * `src/components/__tests__/classify-nav-confirmation.test.ts`, que
 * cobrem o classificador PT-BR exaustivamente (positivos / negativos /
 * ambíguos) — este spec apenas valida a integração end-to-end.
 */

import { test, expect } from "@playwright/test"
import { loginAsRecrutador } from "./01-helpers"

test.describe("Task #1165 — roteamento e split-view coerentes", () => {
  test("A) em /chat, intent de criação de vaga NÃO empurra para /vagas", async ({ page }) => {
    await loginAsRecrutador(page)
    await page.goto("/pt-BR/chat")
    await expect(page).toHaveURL(/\/chat(\/|$)/)

    const input = page.getByPlaceholder(/Pergunte algo|Conversar com a LIA/i).first()
    await input.fill("quero criar uma vaga de engenheiro backend pleno")
    await input.press("Enter")

    // Aguarda o ciclo: detect → resolveNavigationIntentMode (já em /chat
    // + Vagas) → page=null → SEM dispatch → SEM router.push.
    await page.waitForTimeout(1500)
    await expect(page).toHaveURL(/\/chat(\/|$)/)
  })

  test("B) fora de /vagas, a LIA pergunta antes de mover", async ({ page }) => {
    await loginAsRecrutador(page)
    await page.goto("/pt-BR/funil-de-talentos")

    // Simula o hint vindo do wizard (mode=ask) — não dependemos do LLM
    // classifier nesse spec, queremos validar o handler do DashboardApp.
    await page.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent("lia:navigation-hint", {
          detail: { page: "Vagas", hint: "wizard:review", mode: "ask" },
        }),
      )
    })

    await expect(page.getByText(/Posso te levar para o ambiente de vagas/i)).toBeVisible()
    await expect(page).toHaveURL(/\/funil-de-talentos/)

    // Resposta positiva livre → push.
    const input = page.getByPlaceholder(/Pergunte algo|Conversar com a LIA/i).first()
    await input.fill("pode ir")
    await input.press("Enter")
    await expect(page).toHaveURL(/\/vagas(\/|$)/, { timeout: 5000 })
  })

  test("B') resposta negativa cancela a transição", async ({ page }) => {
    await loginAsRecrutador(page)
    await page.goto("/pt-BR/funil-de-talentos")
    await page.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent("lia:navigation-hint", {
          detail: { page: "Vagas", mode: "ask" },
        }),
      )
    })
    await expect(page.getByText(/Posso te levar para o ambiente de vagas/i)).toBeVisible()

    const input = page.getByPlaceholder(/Pergunte algo|Conversar com a LIA/i).first()
    await input.fill("agora não")
    await input.press("Enter")
    await expect(page.getByText(/Combinado — seguimos por aqui/i)).toBeVisible()
    await expect(page).toHaveURL(/\/funil-de-talentos/)
  })
})
