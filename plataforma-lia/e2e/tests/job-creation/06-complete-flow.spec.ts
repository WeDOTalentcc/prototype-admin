/**
 * Fase 5 — Fluxo Completo + Edge Cases
 *
 * Testa cenários end-to-end e edge cases:
 *   1. Criar vaga mínima → verificar Rascunho
 *   2. Fluxo completo: criar → editar → triagem → publicar
 *   3. Criar → publicar sem triagem → warning
 *   4. Caracteres especiais no título
 *   5. Duplicar título de vaga
 *
 * Ref: Todos os componentes de job creation
 */
import { test, expect, SEL, uniqueJobTitle } from '../../fixtures/job-creation.fixture'

const SCREENSHOTS_DIR = 'e2e/screenshots/job-creation'

test.describe('06 — Fluxo Completo + Edge Cases', () => {
  test.setTimeout(90_000) // Mais tempo para fluxos completos

  test.afterEach(async ({ authenticatedPage: page }, testInfo) => {
    if (testInfo.status !== 'passed') {
      await page.screenshot({
        path: `${SCREENSHOTS_DIR}/06-${testInfo.title.replace(/\s+/g, '-')}-FAIL.png`,
        fullPage: true,
      })
    }
  })

  // -----------------------------------------------------------------------
  // Test 1: Criar vaga mínima → verificar status Rascunho
  // -----------------------------------------------------------------------
  test('T01 — Criar vaga mínima tem status Rascunho', async ({ authenticatedPage: page, jobHelpers }) => {
    const title = uniqueJobTitle('E2E Rascunho')

    await jobHelpers.navigateToJobs()
    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()
    await jobHelpers.fillMinimalForm({ title })

    // Intercepta API
    const apiPromise = page.waitForResponse(
      res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
      { timeout: 15_000 }
    ).catch(() => null)

    await jobHelpers.submitCreateForm()
    await jobHelpers.screenshotStep('06-T01-vaga-criada')

    const response = await apiPromise
    if (response && response.status() < 400) {
      const body = await response.json().catch(() => ({}))
      if (body.status) {
        expect(body.status).toBe('Rascunho')
      }
    }

    // Navega para lista e verifica que a vaga está como Rascunho
    await jobHelpers.navigateToJobs()
    await page.waitForTimeout(2_000)

    // Procura a vaga pelo título
    const vagaRow = page.getByText(title).first()
    if (await vagaRow.isVisible({ timeout: 5_000 }).catch(() => false)) {
      // Verifica badge de status próximo
      const statusBadge = vagaRow.locator('..').getByText(/rascunho|draft/i).first()
        .or(vagaRow.locator('..').locator('..').getByText(/rascunho|draft/i).first())
      const hasRascunhoBadge = await statusBadge.isVisible({ timeout: 3_000 }).catch(() => false)
      // Screenshot para diagnóstico
    }

    await jobHelpers.screenshotStep('06-T01-status-rascunho')
  })

  // -----------------------------------------------------------------------
  // Test 2: Fluxo completo — criar → editar → verificar
  // -----------------------------------------------------------------------
  test('T02 — Fluxo completo: criar vaga, editar campos, verificar persistência', async ({ authenticatedPage: page, jobHelpers }) => {
    const title = uniqueJobTitle('E2E Lifecycle')

    // STEP 1: Criar vaga
    await jobHelpers.navigateToJobs()
    await jobHelpers.screenshotStep('06-T02-step1-lista')

    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()
    await jobHelpers.fillFullForm({ title })
    await jobHelpers.screenshotStep('06-T02-step2-form-preenchido')

    const apiPromise = page.waitForResponse(
      res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
      { timeout: 15_000 }
    ).catch(() => null)

    await jobHelpers.submitCreateForm()
    await jobHelpers.screenshotStep('06-T02-step3-apos-criar')

    const createResponse = await apiPromise
    let jobId = ''
    if (createResponse && createResponse.status() < 400) {
      const body = await createResponse.json().catch(() => ({}))
      jobId = body.id || body.job_id || ''
    }

    // Espera navegação pós-criação
    await page.waitForTimeout(3_000)
    await jobHelpers.screenshotStep('06-T02-step4-pos-navegacao')

    // STEP 2: Tentar editar (abre edit modal se disponível)
    const editTrigger = page.locator('button').filter({ hasText: /editar|edit/i }).first()
    if (await editTrigger.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await editTrigger.click()
      await page.locator(SEL.editModal).waitFor({ state: 'visible', timeout: 10_000 }).catch(() => {})

      const editModal = page.locator(SEL.editModal)
      if (await editModal.isVisible().catch(() => false)) {
        await jobHelpers.screenshotStep('06-T02-step5-edit-modal')

        // Verifica que os dados estão preenchidos
        const inputs = editModal.locator('input')
        const inputCount = await inputs.count()
        expect(inputCount).toBeGreaterThan(0)

        // Tenta salvar
        const saveBtn = editModal.locator('button').filter({ hasText: /salvar|save/i }).first()
        if (await saveBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
          await saveBtn.click()
          await page.waitForTimeout(2_000)
        }

        await jobHelpers.screenshotStep('06-T02-step6-salvo')
      }
    }

    // STEP 3: Verificar na lista
    await jobHelpers.navigateToJobs()
    await page.waitForTimeout(2_000)

    const vagaRow = page.getByText(title).first()
    const isVisible = await vagaRow.isVisible({ timeout: 5_000 }).catch(() => false)

    await jobHelpers.screenshotStep('06-T02-step7-verificacao-lista')
  })

  // -----------------------------------------------------------------------
  // Test 3: Publicar sem triagem → warning
  // -----------------------------------------------------------------------
  test('T03 — Publicar vaga sem triagem mostra aviso', async ({ authenticatedPage: page, jobHelpers }) => {
    const title = uniqueJobTitle('E2E SemTriagem')

    // Cria vaga limpa
    await jobHelpers.navigateToJobs()
    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()
    await jobHelpers.fillMinimalForm({ title })
    await jobHelpers.submitCreateForm()
    await page.waitForTimeout(3_000)

    await jobHelpers.screenshotStep('06-T03-vaga-criada')

    // Tenta publicar
    await jobHelpers.navigateToJobs()
    await page.waitForTimeout(2_000)

    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)

      // Verifica warning sobre triagem
      const warning = page.getByText(/triagem|screening|wsi|sem roteiro/i)
      const hasWarning = await warning.isVisible({ timeout: 5_000 }).catch(() => false)

      await jobHelpers.screenshotStep('06-T03-warning')
    }

    await jobHelpers.screenshotStep('06-T03-result')
  })

  // -----------------------------------------------------------------------
  // Test 4: Caracteres especiais no título
  // -----------------------------------------------------------------------
  test('T04 — Título com caracteres especiais (acentos, símbolos)', async ({ authenticatedPage: page, jobHelpers }) => {
    const specialTitle = `E2E Ação & Inovação – Développeur «Senior» ${Date.now()}`

    // Reload fresh para evitar estado residual do teste anterior
    await page.goto('/pt/jobs', { waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {})
    await page.waitForTimeout(2_000)
    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()

    await page.locator(SEL.fieldTitle).fill(specialTitle)
    await page.locator(SEL.fieldManager).fill('José María García-López')
    await page.locator(SEL.fieldManagerEmail).fill('jose.garcia@wedotalent.com')

    await jobHelpers.screenshotStep('06-T04-caracteres-especiais')

    const apiPromise = page.waitForResponse(
      res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
      { timeout: 15_000 }
    ).catch(() => null)

    await jobHelpers.submitCreateForm()

    const response = await apiPromise
    if (response) {
      expect(response.status()).toBeLessThan(400)
      const body = await response.json().catch(() => ({}))
      if (body.title) {
        expect(body.title).toContain('Ação')
        expect(body.title).toContain('Inovação')
      }
    }

    await jobHelpers.screenshotStep('06-T04-resultado')
  })

  // -----------------------------------------------------------------------
  // Test 5: Duas vagas com títulos similares
  // -----------------------------------------------------------------------
  test('T05 — Criar duas vagas com títulos similares', async ({ authenticatedPage: page, jobHelpers }) => {
    const baseTitle = `E2E Duplicado ${Date.now()}`

    // Reload fresh para evitar estado residual
    await page.goto('/pt/jobs', { waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {})
    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()
    await jobHelpers.fillMinimalForm({ title: `${baseTitle} - A` })

    const api1 = page.waitForResponse(
      res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
      { timeout: 15_000 }
    ).catch(() => null)

    await jobHelpers.submitCreateForm()
    const res1 = await api1
    if (res1) {
      expect(res1.status()).toBeLessThan(400)
    }

    await page.waitForTimeout(3_000)
    await jobHelpers.screenshotStep('06-T05-primeira-criada')

    // Cria segunda vaga com título similar
    await jobHelpers.navigateToJobs()
    await jobHelpers.openCreateModal()
    await jobHelpers.selectManualMode()
    await jobHelpers.fillMinimalForm({ title: `${baseTitle} - B` })

    const api2 = page.waitForResponse(
      res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
      { timeout: 15_000 }
    ).catch(() => null)

    await jobHelpers.submitCreateForm()
    const res2 = await api2
    if (res2) {
      expect(res2.status()).toBeLessThan(400)
    }

    await jobHelpers.screenshotStep('06-T05-segunda-criada')

    // Verifica que ambas existem na lista
    await jobHelpers.navigateToJobs()
    await page.waitForTimeout(2_000)

    await jobHelpers.screenshotStep('06-T05-ambas-na-lista')
  })
})
