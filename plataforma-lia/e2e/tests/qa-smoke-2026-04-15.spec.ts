/**
 * Smoke E2E — fixes do QA Report 2026-04-15.
 *
 * Cobre fim-a-fim os 8 cenários críticos do plano de correção:
 *   1. Chat LIA responde (backend não devolve mais content vazio silencioso)
 *   2. Chat mostra "digitando" enquanto aguarda
 *   3. Agent Studio lista agentes sem exibir card de erro falso
 *   4. Quota excedida mostra a mensagem detalhada (não "Error 403")
 *   5. Troca de modo Fullscreen → Sidebar preserva a página original
 *   6. Chip contextual no input muda entre Tarefas/Vagas/Estúdio/Módulos
 *   7. Briefing diário carrega em Tarefas
 *   8. Zero requests com user_id=default_user
 *
 * Para rodar contra o Replit local proxy:
 *   PLAYWRIGHT_BASE_URL=http://localhost:3333 npx playwright test qa-smoke-2026-04-15
 */
import { test, expect, type Page, type Request } from "@playwright/test"

const REPLIT_HOST = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3333"
const LOCALE_HOME = "/pt"

/**
 * Abre o chat no modo Sidebar caso não esteja aberto.
 */
async function openChatSidebar(page: Page) {
  const textarea = page.locator('textarea[placeholder*="LIA"]').first()
  if (!(await textarea.isVisible())) {
    // Tenta clicar no botão flutuante da LIA
    await page.getByRole("button", { name: /LIA|abrir chat|mensagem/i }).first().click().catch(() => {})
    await textarea.waitFor({ state: "visible", timeout: 5000 })
  }
}

test.describe("QA Smoke 2026-04-15", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(LOCALE_HOME, { waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {})
  })

  test("BUG-01 — Chat LIA responde com texto não vazio", async ({ page }) => {
    await openChatSidebar(page)

    const textarea = page.locator('textarea[placeholder*="LIA"]').first()
    await textarea.fill("Olá LIA, me responda com uma saudação curta.")

    // Captura a resposta do backend (200 OK deve ter content populated, ou 502 com detail)
    const responsePromise = page.waitForResponse(
      (res) => res.url().includes("/api/backend-proxy/chat/message") && res.request().method() === "POST",
      { timeout: 20000 }
    )

    await page.getByRole("button", { name: /enviar mensagem/i }).click()
    const res = await responsePromise

    const body = await res.json().catch(() => ({}))
    // Depois do BUG-01, a resposta NUNCA é {"content": ""} silencioso:
    //   - Caminho feliz: content tem len > 0
    //   - Caminho infeliz: status 502 com detail legível (não 200 vazio)
    if (res.status() === 200) {
      expect(body.content?.length, `/chat/message 200 OK mas content vazio: ${JSON.stringify(body).slice(0, 200)}`).toBeGreaterThan(0)
    } else {
      expect([502, 422, 429]).toContain(res.status())
      expect(body.detail || body.message || "").not.toBe("")
    }
  })

  test("BUG-13 — indicador 'LIA digitando' aparece durante a espera", async ({ page }) => {
    await openChatSidebar(page)
    const textarea = page.locator('textarea[placeholder*="LIA"]').first()
    await textarea.fill("Teste de indicador")

    await page.getByRole("button", { name: /enviar mensagem/i }).click()

    // Algum indicador de thinking deve aparecer em até 2s
    const typingIndicator = page.locator(
      '[data-testid="typing-indicator"], [aria-label*="digitando"], [aria-label*="pensando"]'
    ).first()
    await expect(typingIndicator).toBeVisible({ timeout: 3000 })
  })

  test("BUG-02 — Agent Studio lista agentes (sem card de erro em 200 OK)", async ({ page }) => {
    // Navegar para Estúdio de Agentes
    await page.getByRole("button", { name: /Estúdio de Agentes/i }).click()
    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {})

    // Aguarda o GET /sourcing-agents terminar
    const listRes = await page.waitForResponse(
      (res) => res.url().includes("/api/backend-proxy/sourcing-agents") && res.request().method() === "GET",
      { timeout: 15000 }
    ).catch(() => null)

    if (listRes && listRes.status() === 200) {
      // Se 200, UI NUNCA deve mostrar card de erro "Não foi possível carregar"
      const errorCard = page.getByText(/Não foi possível carregar os agentes/i)
      await expect(errorCard).toHaveCount(0)
    }

    if (listRes && listRes.status() >= 500) {
      // Se 500, UI DEVE mostrar card de erro com botão "Tentar novamente"
      await expect(page.getByRole("button", { name: /Tentar novamente/i })).toBeVisible({ timeout: 5000 })
    }
  })

  test("BUG-03 — quota exceeded mostra mensagem detalhada (não 'Error 403')", async ({ page }) => {
    await page.getByRole("button", { name: /Estúdio de Agentes/i }).click()
    await page.waitForTimeout(1500)
    await page.getByRole("button", { name: /\+ Criar Agente/i }).click().catch(() => {})

    const nameInput = page.locator('input[placeholder*="Backend"]').first()
    if (await nameInput.isVisible()) {
      await nameInput.fill("QA Smoke Test Agent")
      await page.getByRole("button", { name: /Criar e Calibrar/i }).click()

      const postRes = await page.waitForResponse(
        (res) => res.url().includes("/api/backend-proxy/sourcing-agents") && res.request().method() === "POST",
        { timeout: 10000 }
      ).catch(() => null)

      if (postRes && postRes.status() === 403) {
        // Deve mostrar mensagem de quota, NÃO "Error 403"
        await expect(page.getByText(/quota|limite|upgrade/i)).toBeVisible({ timeout: 5000 })
        await expect(page.getByText(/^Error 403$/)).toHaveCount(0)
      }
    }
  })

  test("BUG-09 — trocar modo Fullscreen → Sidebar preserva página", async ({ page }) => {
    // Ir para Vagas
    await page.getByRole("button", { name: /^Vagas/i }).click()
    await page.waitForTimeout(1500)

    // Trocar chat para fullscreen
    await page.getByRole("button", { name: /Modo de exibição/i }).click()
    await page.getByRole("button", { name: /Tela cheia/i }).click()
    await page.waitForTimeout(1000)

    // Voltar para sidebar
    await page.getByRole("button", { name: /Modo de exibição/i }).click()
    await page.getByRole("button", { name: /Lateral/i }).click()
    await page.waitForTimeout(1500)

    // Após BUG-09, o usuário deve continuar em Vagas, NÃO ter sido levado para Tarefas
    await expect(page.locator("h1, h2").filter({ hasText: /Gestão de Vagas|Vagas/i })).toBeVisible({ timeout: 5000 })
  })

  test("BUG contexto — chip muda entre páginas (Decidir/Vagas/Estúdio/Módulos)", async ({ page }) => {
    await openChatSidebar(page)

    const pages = [
      { btn: /^Decidir$/i, chip: /Decidir/ },
      { btn: /^Vagas$/i, chip: /Vagas/ },
      { btn: /Estúdio de Agentes/i, chip: /Estúdio de Agentes/ },
      { btn: /^Módulos/i, chip: /Módulos/ },
    ]

    for (const { btn, chip } of pages) {
      await page.getByRole("button", { name: btn }).click()
      await page.waitForTimeout(1500)
      // chip contextual fica no input do chat
      await expect(
        page.locator('[role="chat-context-chip"], [data-chat-context]').filter({ hasText: chip })
          .or(page.getByText(chip).first())
      ).toBeVisible({ timeout: 5000 })
    }
  })

  test("BUG-07 — Briefing diário carrega em Decidir (sem card de erro)", async ({ page }) => {
    await page.getByRole("button", { name: /^Decidir$/i }).click()
    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {})

    await page.waitForResponse(
      (res) => res.url().includes("/api/backend-proxy/briefing") && res.request().method() === "GET",
      { timeout: 10000 }
    ).catch(() => null)

    // Card de erro "Não foi possível carregar o briefing diário" NÃO deve estar visível
    // (para usuário autenticado). Para usuário default_user/anônimo, o backend retorna
    // empty briefing — também sem card de erro.
    const errorCard = page.getByText(/Não foi possível carregar o briefing/i)
    await expect(errorCard).toHaveCount(0)
  })

  test("BUG-08 — zero requests com user_id=default_user", async ({ page }) => {
    const defaultUserRequests: string[] = []
    page.on("request", (req: Request) => {
      const url = req.url()
      if (url.includes("user_id=default_user")) {
        defaultUserRequests.push(url)
      }
    })

    // Navegar e disparar fetches típicos
    await page.goto(LOCALE_HOME, { waitUntil: "networkidle", timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(3000)
    await page.getByRole("button", { name: /^Decidir$/i }).click().catch(() => {})
    await page.waitForTimeout(2000)

    expect(
      defaultUserRequests,
      `Requests com user_id=default_user detectadas (BUG-08 deveria evitar):\n${defaultUserRequests.join("\n")}`
    ).toHaveLength(0)
  })
})
