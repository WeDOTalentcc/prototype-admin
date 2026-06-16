/**
 * E2E sentinel — Task #1128 nova-conversa-reset-canonical.
 *
 * Reproduz o bug do screenshot: recrutador abre o wizard, avança até
 * uma etapa intermediária, clica em "Nova conversa" (ou digita
 * `/nova-conversa`) e — antes da correção — o próximo turno reabre o
 * wizard no estágio anterior porque o backend manteve o checkpoint
 * aberto enquanto o frontend só limpou a UI.
 *
 * Modelo canônico Task #1128:
 *   - Frontend chama DELETE /api/v1/lia/job-wizard/session/<sid>;
 *   - Backend marca current_stage="completed", conversation=[];
 *   - is_wizard_session_active → False;
 *   - Próximo turno começa fresco em `intake`.
 *
 * Estratégia: usa `page.route` para interceptar a chamada DELETE e
 * validar que o frontend (a) chamou o proxy canônico, (b) NÃO reusa a
 * conversation_id antiga, (c) re-hydrata via GET na sessão seguinte.
 * Não exigimos um backend wizard funcional aqui — a sentinela cobre o
 * contrato do client; os testes integrados de backend cobrem o efeito
 * no checkpointer.
 */
import { test, expect, type Page } from "@playwright/test"
import { authenticateAsRecruiter } from "../../fixtures/auth.fixture"

/**
 * Shared route fixture: intercept both GET and DELETE on the canonical
 * wizard-session proxy. Returns counters so each test asserts only on
 * the verbs it cares about. The GET fixture is parameterised by
 * `activeStage` so the cancel test can simulate "wizard is currently
 * mid-jd_enrichment" and verify the stepper disappears after DELETE.
 */
async function installWizardSessionRoutes(
  page: Page,
  opts: { activeStage?: string | null } = {},
) {
  const counters = { deleteHits: 0, getHits: 0, lastDeletePath: null as string | null }
  await page.route("**/api/backend-proxy/lia/job-wizard/session/**", async (route) => {
    const method = route.request().method()
    const url = new URL(route.request().url())
    const sid = decodeURIComponent(url.pathname.split("/").pop() ?? "")
    if (method === "DELETE") {
      counters.deleteHits += 1
      counters.lastDeletePath = url.pathname
      // After a successful DELETE the GET fixture must report inactive
      // so the stepper actually disappears on re-hydration.
      opts.activeStage = null
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          session_id: sid,
          thread_id: `wiz-token-${sid}`,
          was_active: true,
        }),
      })
      return
    }
    if (method === "GET") {
      counters.getHits += 1
      const stage = opts.activeStage ?? null
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session_id: sid,
          thread_id: `wiz-token-${sid}`,
          active: !!stage,
          current_stage: stage,
          completeness: stage ? 0.3 : 0,
          requires_approval: false,
          stage_data: stage
            ? { jd_enrichment_used_fallback: false, role_title: "Engenheira Backend" }
            : {},
          degraded_stages: {},
          conversation_message_count: stage ? 2 : 0,
        }),
      })
      return
    }
    await route.continue()
  })
  return counters
}

test.describe("Wizard — Nova conversa reseta o wizard via DELETE backend", () => {
  test("clicar em Nova conversa chama DELETE /job-wizard/session/<sid>", async ({ page }) => {
    test.setTimeout(120_000)
    const counters = await installWizardSessionRoutes(page)

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")

    // Aguarda a primeira hidratação GET (acontece assim que o
    // chatSessionId é resolvido pelo contexto).
    await expect.poll(() => counters.getHits, { timeout: 30_000 }).toBeGreaterThanOrEqual(1)

    const newChatButton = page
      .getByRole("button", { name: /nova conversa/i })
      .first()
    await newChatButton.click()

    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBeGreaterThanOrEqual(1)
    expect(counters.lastDeletePath).toMatch(
      /^\/api\/backend-proxy\/lia\/job-wizard\/session\/[^/]+$/,
    )

    // Purge legado: nada de `lia-wizard-state-*` deve sobreviver.
    const leftover = await page.evaluate(() => {
      const keys: string[] = []
      for (let i = 0; i < window.localStorage.length; i++) {
        const k = window.localStorage.key(i)
        if (k && k.startsWith("lia-wizard-state")) keys.push(k)
      }
      return keys
    })
    expect(leftover).toEqual([])
  })

  test("slash `/nova-conversa` dispara o MESMO handler canônico (DELETE + purge)", async ({ page }) => {
    test.setTimeout(120_000)
    const counters = await installWizardSessionRoutes(page)

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")
    await expect.poll(() => counters.getHits, { timeout: 30_000 }).toBeGreaterThanOrEqual(1)

    // Digita o slash command no input — o useSlashCommands abre o
    // popover, e ao confirmar a entrada (Enter) o onExecuteCommand é
    // disparado. Garante paridade com o botão "Nova conversa".
    const input = page
      .getByRole("textbox")
      .or(page.locator("textarea"))
      .first()
    await input.click()
    await input.fill("/nova-conversa")
    // Enter executa o item destacado no popover.
    await input.press("Enter")

    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBeGreaterThanOrEqual(1)
    expect(counters.lastDeletePath).toMatch(
      /^\/api\/backend-proxy\/lia\/job-wizard\/session\/[^/]+$/,
    )
  })

  test("Cancelar wizard mata o stepper SEM mudar conversation_id", async ({ page }) => {
    test.setTimeout(120_000)
    // Wizard começa "ativo" no mock — o GET inicial vai hidratar o
    // stepper no chat antes do recrutador clicar em cancelar.
    const counters = await installWizardSessionRoutes(page, {
      activeStage: "jd_enrichment",
    })

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")

    // Stepper deve estar visível depois da primeira hidratação.
    await expect(page.getByTestId("wizard-progress-bar")).toBeVisible({ timeout: 30_000 })
    const conversationIdBefore = await page.evaluate(
      () => new URL(window.location.href).searchParams.get("conversation_id"),
    )

    // Task #1133 — o `window.confirm` foi substituído pelo AlertDialog
    // canônico do DS LIA v4.2.2. O recrutador precisa clicar em
    // "Descartar rascunho" no modal antes do DELETE ser disparado.
    const cancelButton = page
      .getByTestId("wizard-cancel-button")
      .or(page.getByTestId("wizard-cancel-button-compact"))
      .first()
    await cancelButton.click()

    await expect(page.getByTestId("wizard-cancel-confirm-dialog")).toBeVisible({
      timeout: 5_000,
    })
    await expect(
      page.getByTestId("wizard-cancel-confirm-dialog"),
    ).toContainText(/cancelar criação da vaga\?/i)
    await page.getByTestId("wizard-cancel-confirm-discard").click()

    // DELETE foi chamado uma vez.
    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBe(1)

    // Stepper sumiu — confirma que `wizard.reset()` rodou e o estado
    // local não está mais "ativo".
    await expect(page.getByTestId("wizard-progress-bar")).toBeHidden({
      timeout: 10_000,
    })

    // conversation_id NÃO mudou — diferencia "Cancelar wizard" de
    // "Nova conversa". Esse é o invariante exigido pela Task #1128.
    const conversationIdAfter = await page.evaluate(
      () => new URL(window.location.href).searchParams.get("conversation_id"),
    )
    expect(conversationIdAfter).toBe(conversationIdBefore)
  })

  test("após Cancelar wizard + page.reload(), o stepper continua ausente (reset persiste no backend)", async ({ page }) => {
    test.setTimeout(120_000)
    // Wizard começa "ativo" — depois do DELETE o mock muda activeStage
    // para null, então a re-hidratação pós-reload devolve `active=false`.
    // Isso reproduz o invariante real: o backend é a fonte da verdade,
    // não há mais cache local que ressuscite o wizard no reload.
    const counters = await installWizardSessionRoutes(page, {
      activeStage: "jd_enrichment",
    })

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")
    await expect(page.getByTestId("wizard-progress-bar")).toBeVisible({ timeout: 30_000 })

    const cancelButton = page
      .getByTestId("wizard-cancel-button")
      .or(page.getByTestId("wizard-cancel-button-compact"))
      .first()
    await cancelButton.click()
    // Task #1133 — confirma via modal canônico antes do DELETE.
    await page.getByTestId("wizard-cancel-confirm-discard").click()
    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBe(1)
    await expect(page.getByTestId("wizard-progress-bar")).toBeHidden({ timeout: 10_000 })

    // Reload — o invariante crítico (Task #1128) é que sem cache local,
    // o frontend re-hidrata via GET e recebe `active=false`. NÃO pode
    // ressurgir stepper nem banner degradado.
    const getsBeforeReload = counters.getHits
    await page.reload()
    await page.waitForLoadState("networkidle")
    await expect.poll(() => counters.getHits, { timeout: 30_000 }).toBeGreaterThan(getsBeforeReload)

    // Stepper continua ausente.
    await expect(page.getByTestId("wizard-progress-bar")).toBeHidden({ timeout: 10_000 })
    // Banner de stage degradado (degraded_stages) também não pode
    // aparecer — o snapshot pós-reset é limpo.
    await expect(page.getByTestId("wizard-degraded-banner")).toHaveCount(0)
    // E nenhum resíduo de localStorage da era pré-Task #1128.
    const leftover = await page.evaluate(() => {
      const keys: string[] = []
      for (let i = 0; i < window.localStorage.length; i++) {
        const k = window.localStorage.key(i)
        if (k && k.startsWith("lia-wizard-state")) keys.push(k)
      }
      return keys
    })
    expect(leftover).toEqual([])
  })

  test("recusar o modal cancela a operação — nenhum DELETE é emitido (Task #1133)", async ({ page }) => {
    test.setTimeout(60_000)
    const counters = await installWizardSessionRoutes(page, {
      activeStage: "jd_enrichment",
    })

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")
    await expect(page.getByTestId("wizard-progress-bar")).toBeVisible({ timeout: 30_000 })

    const cancelButton = page
      .getByTestId("wizard-cancel-button")
      .or(page.getByTestId("wizard-cancel-button-compact"))
      .first()
    await cancelButton.click()

    // Task #1133 — modal canônico DS LIA v4.2.2 aparece; clicar em
    // "Continuar editando" fecha sem disparar o DELETE.
    await expect(page.getByTestId("wizard-cancel-confirm-dialog")).toBeVisible({
      timeout: 5_000,
    })
    await page.getByTestId("wizard-cancel-confirm-keep").click()
    await expect(
      page.getByTestId("wizard-cancel-confirm-dialog"),
    ).toBeHidden({ timeout: 5_000 })

    // Pequena janela para confirmar que nenhuma chamada extra foi feita.
    await page.waitForTimeout(500)
    expect(counters.deleteHits).toBe(0)
    await expect(page.getByTestId("wizard-progress-bar")).toBeVisible()
  })

  test("Task #1133 — Nova conversa com wizard ATIVO exige confirmação no modal canônico", async ({ page }) => {
    test.setTimeout(120_000)
    const counters = await installWizardSessionRoutes(page, {
      activeStage: "jd_enrichment",
    })

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")
    await expect(page.getByTestId("wizard-progress-bar")).toBeVisible({
      timeout: 30_000,
    })

    const newChatButton = page
      .getByRole("button", { name: /nova conversa/i })
      .first()
    await newChatButton.click()

    // Modal canônico AlertDialog aparece com copy modo "new-chat".
    await expect(page.getByTestId("wizard-cancel-confirm-dialog")).toBeVisible({
      timeout: 5_000,
    })
    await expect(
      page.getByTestId("wizard-cancel-confirm-dialog"),
    ).toContainText(/iniciar nova conversa e descartar rascunho\?/i)

    // Sem confirmar, nenhum DELETE pode ter sido emitido.
    expect(counters.deleteHits).toBe(0)

    await page.getByTestId("wizard-cancel-confirm-discard").click()
    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBe(1)
  })

  test("Task #1133 — Nova conversa com wizard INATIVO não exibe modal (UX inalterada)", async ({ page }) => {
    test.setTimeout(120_000)
    // activeStage=null garante que o GET inicial responde active=false.
    const counters = await installWizardSessionRoutes(page, {
      activeStage: null,
    })

    await authenticateAsRecruiter(page)
    await page.goto("/pt/chat")
    await page.waitForLoadState("networkidle")
    await expect
      .poll(() => counters.getHits, { timeout: 30_000 })
      .toBeGreaterThanOrEqual(1)
    // Stepper NÃO está visível porque o wizard está inativo.
    await expect(page.getByTestId("wizard-progress-bar")).toBeHidden()

    const newChatButton = page
      .getByRole("button", { name: /nova conversa/i })
      .first()
    await newChatButton.click()

    // O modal NÃO pode aparecer — não há rascunho em risco.
    await page.waitForTimeout(500)
    await expect(page.getByTestId("wizard-cancel-confirm-dialog")).toBeHidden()

    // Mas o DELETE canônico continua sendo emitido (Task #1128) — o
    // reset é idempotente mesmo sem wizard ativo, mantém o contrato.
    await expect.poll(() => counters.deleteHits, { timeout: 15_000 }).toBe(1)
  })
})
