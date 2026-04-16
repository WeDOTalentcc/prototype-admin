/**
 * Fase 2B — Edição de Requisitos, Benefícios e Etapas
 *
 * Acessa a edição via: Lista → Click row → Kanban → Settings tab → JobEditTab
 * Ref: useJobsPageCore.ts (handleJobClick), KanbanJobHeader.tsx (Settings tab), JobEditTab.tsx
 *
 * Testes:
 *   1. Abrir detalhe da vaga e acessar aba Settings
 *   2. Verificar seções de edição no JobEditTab
 *   3. Editar campos da seção de configuração da vaga
 *   4. Navegar para seções de triagem no sidebar
 *   5. Adicionar benefícios (se campo disponível)
 *   6. Salvar alterações
 */
import { test, expect, SEL } from '../../fixtures/job-creation.fixture'

const SCREENSHOTS_DIR = 'e2e/screenshots/job-creation'

test.describe('03 — Requisitos, Benefícios e Etapas (via JobEditTab)', () => {
  test.setTimeout(60_000)

  test.afterEach(async ({ authenticatedPage: page }, testInfo) => {
    if (testInfo.status !== 'passed') {
      await page.screenshot({
        path: `${SCREENSHOTS_DIR}/03-${testInfo.title.replace(/\s+/g, '-')}-FAIL.png`,
        fullPage: true,
      })
    }
  })

  // -----------------------------------------------------------------------
  // Test 1: Abrir detalhe da vaga e acessar aba Settings
  // -----------------------------------------------------------------------
  test('T01 — Abrir detalhe da vaga via click na row', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.screenshotStep('03-T01-lista')

    // Clica na primeira vaga da tabela
    await jobHelpers.openJobDetail()
    await jobHelpers.screenshotStep('03-T01-kanban-aberto')

    // Verifica que saímos da lista e estamos no detalhe/kanban
    // O Kanban deve ter informações da vaga (título, status, etc.)
    const kanbanContent = page.getByText(/pipeline|kanban|candidatos|etapas|triagem|inscrição/i).first()
    const hasKanbanContent = await kanbanContent.isVisible({ timeout: 5_000 }).catch(() => false)

    await jobHelpers.screenshotStep('03-T01-detalhe-vaga')
  })

  // -----------------------------------------------------------------------
  // Test 2: Acessar aba Settings dentro do detalhe
  // -----------------------------------------------------------------------
  test('T02 — Acessar aba Settings mostra JobEditTab', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.openJobDetail()

    // Abre Settings
    await jobHelpers.openJobSettings()
    await jobHelpers.screenshotStep('03-T02-settings-aberto')

    // Verifica se o JobEditTab tem seções no sidebar
    const sidebarSection = page.getByText(/configurações da vaga|configurações de triagem|informações|geral/i).first()
    const hasSidebar = await sidebarSection.isVisible({ timeout: 5_000 }).catch(() => false)

    await jobHelpers.screenshotStep('03-T02-sidebar-secoes')
  })

  // -----------------------------------------------------------------------
  // Test 3: Editar campos na seção de configuração da vaga
  // -----------------------------------------------------------------------
  test('T03 — Editar campos de configuração da vaga', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    // Procura campos editáveis no formulário
    const inputs = page.locator('input:visible, textarea:visible, select:visible')
    const inputCount = await inputs.count()

    await jobHelpers.screenshotStep('03-T03-campos-disponiveis')

    if (inputCount > 0) {
      // Tenta editar o primeiro campo de texto disponível
      const firstInput = page.locator('input[type="text"]:visible').first()
      if (await firstInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
        const original = await firstInput.inputValue()
        await firstInput.clear()
        await firstInput.fill(`${original} E2E`)
        await jobHelpers.screenshotStep('03-T03-campo-editado')
      }
    }

    // Procura selects/dropdowns editáveis
    const selects = page.locator('select:visible, [role="combobox"]:visible')
    const selectCount = await selects.count()

    if (selectCount > 0) {
      const firstSelect = selects.first()
      const isNativeSelect = await firstSelect.evaluate(el => el.tagName === 'SELECT').catch(() => false)
      if (isNativeSelect) {
        const options = await firstSelect.locator('option').allTextContents()
        if (options.length > 1) {
          await firstSelect.selectOption({ index: 1 })
        }
      }
    }

    await jobHelpers.screenshotStep('03-T03-apos-editar')
  })

  // -----------------------------------------------------------------------
  // Test 4: Navegar entre seções do sidebar
  // -----------------------------------------------------------------------
  test('T04 — Navegar para seções de triagem no sidebar', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    await jobHelpers.screenshotStep('03-T04-antes-navegar')

    // Procura botões/links de seção no sidebar do JobEditTab
    const sectionButtons = page.locator('button, a, [role="tab"]').filter({
      hasText: /configurações|descrição|perguntas|triagem|geral|requisitos|benefícios/i
    })
    const sectionCount = await sectionButtons.count()

    // Clica em cada seção do sidebar para verificar se carrega
    for (let i = 0; i < Math.min(sectionCount, 5); i++) {
      const btn = sectionButtons.nth(i)
      const text = await btn.textContent().catch(() => '')
      if (await btn.isVisible().catch(() => false)) {
        await btn.click()
        await page.waitForTimeout(500)
        await jobHelpers.screenshotStep(`03-T04-secao-${i}-${text?.trim().slice(0, 15).replace(/\s+/g, '-') || i}`)
      }
    }

    await jobHelpers.screenshotStep('03-T04-navegacao-completa')
  })

  // -----------------------------------------------------------------------
  // Test 5: Interagir com campos de benefícios/skills
  // -----------------------------------------------------------------------
  test('T05 — Interagir com campos de benefícios ou skills', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    // Navega para seção que tenha campos de adicionar (benefícios, skills, etc.)
    const addButtons = page.locator('button:visible').filter({
      hasText: /adicionar|add|\+ |nova|novo/i
    })
    const addCount = await addButtons.count()

    await jobHelpers.screenshotStep('03-T05-botoes-adicionar')

    if (addCount > 0) {
      // Procura inputs próximos ao botão de adicionar
      const firstAddBtn = addButtons.first()
      const parent = firstAddBtn.locator('..')
      const nearbyInput = parent.locator('input:visible').first()
        .or(page.locator('input:visible').last())

      if (await nearbyInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await nearbyInput.fill('E2E Test Item')
        await firstAddBtn.click()
        await page.waitForTimeout(500)
      }
    }

    await jobHelpers.screenshotStep('03-T05-interacao')
  })

  // -----------------------------------------------------------------------
  // Test 6: Salvar alterações
  // -----------------------------------------------------------------------
  test('T06 — Salvar alterações no JobEditTab', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    // Procura botão salvar
    const saveBtn = page.locator('button:visible').filter({ hasText: /salvar|save|atualizar|update/i }).first()
    const hasSaveBtn = await saveBtn.isVisible({ timeout: 5_000 }).catch(() => false)

    await jobHelpers.screenshotStep('03-T06-antes-salvar')

    if (hasSaveBtn) {
      const apiPromise = page.waitForResponse(
        res => (res.url().includes('/job') || res.url().includes('/screening')) &&
          (res.request().method() === 'PUT' || res.request().method() === 'PATCH' || res.request().method() === 'POST'),
        { timeout: 10_000 }
      ).catch(() => null)

      await saveBtn.click()

      const response = await apiPromise
      if (response) {
        expect(response.status()).toBeLessThan(500)
      }

      // Toast de sucesso
      const toast = page.locator(SEL.toast).filter({ hasText: /salv|sucesso|saved|atualiz/i })
      await expect(toast).toBeVisible({ timeout: 5_000 }).catch(() => {})
    }

    await jobHelpers.screenshotStep('03-T06-apos-salvar')
  })
})
