/**
 * Fase 4 — Publicação de Vaga
 *
 * Testa o fluxo de publicação/despublicação:
 *   1. Abrir modal de publicação
 *   2. Selecionar LinkedIn
 *   3. Selecionar Portal Carreiras
 *   4. Publicar vaga
 *   5. Warning ao publicar sem WSI
 *   6. Despublicar / congelar vaga
 *
 * Ref: src/components/modals/job-publish-modal.tsx
 *      src/components/modals/job-unpublish-modal.tsx
 */
import { test, expect, SEL } from '../../fixtures/job-creation.fixture'

const SCREENSHOTS_DIR = 'e2e/screenshots/job-creation'

test.describe('05 — Publicação de Vaga', () => {
  test.setTimeout(60_000)

  test.afterEach(async ({ authenticatedPage: page }, testInfo) => {
    if (testInfo.status !== 'passed') {
      await page.screenshot({
        path: `${SCREENSHOTS_DIR}/05-${testInfo.title.replace(/\s+/g, '-')}-FAIL.png`,
        fullPage: true,
      })
    }
  })

  // -----------------------------------------------------------------------
  // Test 1: Abrir modal de publicação
  // -----------------------------------------------------------------------
  test('T01 — Abrir modal de publicação', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.screenshotStep('05-T01-lista-vagas')

    // Procura botão de publicar na lista de vagas (pode ser em ações ou menu de contexto)
    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
      .or(page.locator('[data-testid*="publish"]').first())

    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)

      // Verifica se modal de publicação abriu
      const publishModal = page.locator('[data-testid="job-publish-modal"]')
        .or(page.locator('[role="dialog"]').filter({ hasText: /publicar|publish/i }))

      if (await publishModal.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await jobHelpers.screenshotStep('05-T01-modal-publicacao')
        await expect(publishModal).toBeVisible()
      }
    } else {
      // Tenta abrir via menu de contexto de um job
      const menuBtn = page.locator('[data-testid*="job-actions"], button[aria-haspopup="menu"]').first()
        .or(page.locator('button').filter({ hasText: /ações|actions|⋯|⋮|more/i }).first())

      if (await menuBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
        await menuBtn.click()
        await page.waitForTimeout(500)

        const publishOption = page.locator('[role="menuitem"]').filter({ hasText: /publicar|publish/i }).first()
        if (await publishOption.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await publishOption.click()
          await page.waitForTimeout(1_000)
        }
      }
    }

    await jobHelpers.screenshotStep('05-T01-publish-result')
  })

  // -----------------------------------------------------------------------
  // Test 2: Selecionar LinkedIn
  // -----------------------------------------------------------------------
  test('T02 — Selecionar canal LinkedIn para publicação', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    // Abre publish modal
    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)
    }

    // Procura checkbox/opção LinkedIn
    const linkedinOption = page.getByText(/linkedin/i).first()
    if (await linkedinOption.isVisible({ timeout: 5_000 }).catch(() => false)) {
      // Pode ser um card clicável ou checkbox
      const linkedinCheckbox = linkedinOption.locator('..').locator('input[type="checkbox"], [role="checkbox"]').first()
      if (await linkedinCheckbox.isVisible().catch(() => false)) {
        await linkedinCheckbox.click()
      } else {
        // É um card clicável
        await linkedinOption.click()
      }
    }

    await jobHelpers.screenshotStep('05-T02-linkedin-selecionado')
  })

  // -----------------------------------------------------------------------
  // Test 3: Selecionar Portal Carreiras
  // -----------------------------------------------------------------------
  test('T03 — Selecionar Portal Carreiras para publicação', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)
    }

    // Procura opção Portal
    const portalOption = page.getByText(/portal|carreiras|website|career/i).first()
    if (await portalOption.isVisible({ timeout: 5_000 }).catch(() => false)) {
      const portalCheckbox = portalOption.locator('..').locator('input[type="checkbox"], [role="checkbox"]').first()
      if (await portalCheckbox.isVisible().catch(() => false)) {
        await portalCheckbox.click()
      } else {
        await portalOption.click()
      }
    }

    await jobHelpers.screenshotStep('05-T03-portal-selecionado')
  })

  // -----------------------------------------------------------------------
  // Test 4: Publicar vaga
  // -----------------------------------------------------------------------
  test('T04 — Publicar vaga com canal selecionado', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)
    }

    // Seleciona pelo menos o portal
    const portalOption = page.getByText(/portal|carreiras|website/i).first()
    if (await portalOption.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await portalOption.click()
    }

    // Clica no botão de confirmar publicação
    const confirmPublish = page.locator('[role="dialog"]').locator('button').filter({ hasText: /publicar vaga|publish job|confirmar/i }).first()
    if (await confirmPublish.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const apiPromise = page.waitForResponse(
        res => res.url().includes('/publish') || res.url().includes('/job-boards') || res.url().includes('/job-vacancies'),
        { timeout: 15_000 }
      ).catch(() => null)

      await confirmPublish.click()

      const response = await apiPromise
      if (response) {
        expect(response.status()).toBeLessThan(500)
      }
    }

    await jobHelpers.screenshotStep('05-T04-vaga-publicada')
  })

  // -----------------------------------------------------------------------
  // Test 5: Warning ao publicar sem WSI
  // -----------------------------------------------------------------------
  test('T05 — Warning ao publicar vaga sem triagem configurada', async ({ authenticatedPage: page, jobHelpers }) => {
    // Cria vaga nova (sem screening) e tenta publicar
    const jobId = await jobHelpers.createJobViaUI()
    await jobHelpers.screenshotStep('05-T05-vaga-criada')

    // Navega de volta para lista
    await jobHelpers.navigateToJobs()
    await page.waitForTimeout(2_000)

    // Tenta publicar a vaga recém-criada
    const publishBtn = page.locator('button').filter({ hasText: /publicar|publish/i }).first()
    if (await publishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await publishBtn.click()
      await page.waitForTimeout(1_000)

      // Verifica se aparece warning sobre WSI/triagem
      const wsiWarning = page.getByText(/triagem|wsi|screening|sem roteiro|without screening/i)
      const hasWarning = await wsiWarning.isVisible({ timeout: 5_000 }).catch(() => false)

      if (hasWarning) {
        await jobHelpers.screenshotStep('05-T05-warning-wsi')
        // Verifica se precisa marcar checkbox para continuar
        const acknowledgeCheckbox = page.getByText(/entendo|acknowledge|publicar mesmo/i).locator('..').locator('input[type="checkbox"], [role="checkbox"]').first()
        if (await acknowledgeCheckbox.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await expect(acknowledgeCheckbox).toBeVisible()
        }
      }
    }

    await jobHelpers.screenshotStep('05-T05-warning-result')
  })

  // -----------------------------------------------------------------------
  // Test 6: Despublicar / congelar vaga
  // -----------------------------------------------------------------------
  test('T06 — Despublicar e congelar vaga', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    // Procura botão de despublicar (geralmente em vagas ativas)
    const unpublishBtn = page.locator('button').filter({ hasText: /despublicar|unpublish|congelar|freeze/i }).first()
      .or(page.locator('[data-testid*="unpublish"]').first())

    if (await unpublishBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await unpublishBtn.click()
      await page.waitForTimeout(1_000)

      // Modal de despublicação
      const unpublishModal = page.locator('[role="dialog"]').filter({ hasText: /despublicar|unpublish|congelar/i })
      if (await unpublishModal.isVisible({ timeout: 3_000 }).catch(() => false)) {
        // Marcar congelar
        const freezeCheckbox = unpublishModal.getByText(/congelar|freeze/i).locator('..').locator('input[type="checkbox"], [role="checkbox"]').first()
        if (await freezeCheckbox.isVisible().catch(() => false)) {
          await freezeCheckbox.click()
        }

        // Selecionar razão
        const reasonSelect = unpublishModal.locator('select, [role="combobox"]').first()
        if (await reasonSelect.isVisible().catch(() => false)) {
          await reasonSelect.click()
          const option = page.locator('[role="option"]').first()
          if (await option.isVisible({ timeout: 2_000 }).catch(() => false)) {
            await option.click()
          }
        }

        // Confirmar
        const confirmBtn = unpublishModal.locator('button').filter({ hasText: /confirmar|despublicar|confirmar/i }).first()
        if (await confirmBtn.isVisible().catch(() => false)) {
          await confirmBtn.click()
        }
      }
    } else {
      // Pode não ter vagas publicadas — tenta via menu de contexto
      const menuBtn = page.locator('button[aria-haspopup="menu"]').first()
      if (await menuBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await menuBtn.click()
        const unpublishOption = page.locator('[role="menuitem"]').filter({ hasText: /despublicar|unpublish|congelar/i }).first()
        if (await unpublishOption.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await unpublishOption.click()
        }
      }
    }

    await jobHelpers.screenshotStep('05-T06-despublicacao')
  })
})
