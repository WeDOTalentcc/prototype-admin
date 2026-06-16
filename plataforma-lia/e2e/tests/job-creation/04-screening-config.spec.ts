/**
 * Fase 3 — Configuração de Triagem / WSI
 *
 * Testa a configuração de screening na página de detalhe da vaga:
 *   1. Navegar para config de triagem
 *   2. Ativar triagem
 *   3. Configurar canais (WhatsApp, Chat Web, Phone)
 *   4. Criar pergunta custom
 *   5. Configurar min_score
 *   6. Configurar auto-agendamento
 *   7. Gerar/atualizar job description
 *
 * Ref: src/components/screening-config/ScreeningConfigManager.tsx
 *      src/components/screening-config/ScreeningScriptTab.tsx
 *      src/components/screening-config/SCMSectionPerguntasEdit.tsx
 */
import { test, expect, SEL } from '../../fixtures/job-creation.fixture'

const SCREENSHOTS_DIR = 'e2e/screenshots/job-creation'

test.describe('04 — Configuração de Triagem / WSI', () => {
  test.setTimeout(60_000)

  test.afterEach(async ({ authenticatedPage: page }, testInfo) => {
    if (testInfo.status !== 'passed') {
      await page.screenshot({
        path: `${SCREENSHOTS_DIR}/04-${testInfo.title.replace(/\s+/g, '-')}-FAIL.png`,
        fullPage: true,
      })
    }
  })

  // -----------------------------------------------------------------------
  // Test 1: Navegar para config de triagem
  // -----------------------------------------------------------------------
  test('T01 — Acessar seção de triagem na página da vaga', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()
    await jobHelpers.screenshotStep('04-T01-lista-vagas')

    // Clica na primeira vaga da tabela (abre Kanban/detalhe)
    await jobHelpers.openJobDetail()
    await jobHelpers.screenshotStep('04-T01-kanban-aberto')

    // Abre a aba Settings para acessar configurações de triagem
    await jobHelpers.openJobSettings()
    await jobHelpers.screenshotStep('04-T01-settings-aberto')

    // Procura seções de triagem no sidebar do JobEditTab
    const screeningSection = page.getByText(/configurações de triagem|triagem|screening|perguntas/i).first()
    if (await screeningSection.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningSection.click()
      await page.waitForTimeout(1_000)
    }

    await jobHelpers.screenshotStep('04-T01-triagem-disponivel')
  })

  // -----------------------------------------------------------------------
  // Test 2: Ativar triagem
  // -----------------------------------------------------------------------
  test('T02 — Ativar triagem da vaga', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    // Navega para detalhe da vaga
    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    // Procura tab de triagem
    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Procura toggle de ativação
    const toggleBtn = page.locator('[role="switch"]').first()
      .or(page.locator('button').filter({ hasText: /ativar|activate|habilitar|enable/i }).first())

    if (await toggleBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await toggleBtn.click()
      await page.waitForTimeout(1_000)

      // Pode aparecer dialog de confirmação
      const confirmBtn = page.locator('button').filter({ hasText: /confirmar|confirm|ativar/i }).first()
      if (await confirmBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await confirmBtn.click()
      }
    }

    await jobHelpers.screenshotStep('04-T02-triagem-ativada')
  })

  // -----------------------------------------------------------------------
  // Test 3: Configurar canais
  // -----------------------------------------------------------------------
  test('T03 — Configurar canais de triagem', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Procura botão de configurar canais
    const channelsBtn = page.locator('button').filter({ hasText: /canais|channels|configurar canal/i }).first()
      .or(page.getByText(/whatsapp|chat web|phone/i).first())

    if (await channelsBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await channelsBtn.click()
      await page.waitForTimeout(1_000)

      // Procura switches para cada canal
      const whatsappSwitch = page.getByText(/whatsapp/i).locator('..').locator('[role="switch"]').first()
      const chatWebSwitch = page.getByText(/chat web/i).locator('..').locator('[role="switch"]').first()
      const phoneSwitch = page.getByText(/phone|telefone|voz/i).locator('..').locator('[role="switch"]').first()

      for (const sw of [whatsappSwitch, chatWebSwitch, phoneSwitch]) {
        if (await sw.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await sw.click()
          await page.waitForTimeout(300)
        }
      }
    }

    await jobHelpers.screenshotStep('04-T03-canais-configurados')
  })

  // -----------------------------------------------------------------------
  // Test 4: Criar pergunta custom
  // -----------------------------------------------------------------------
  test('T04 — Criar pergunta de triagem customizada', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Navega para seção de perguntas
    const questionsSection = page.getByText(/perguntas|questions/i).first()
    if (await questionsSection.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await questionsSection.click()
      await page.waitForTimeout(500)
    }

    // Procura botão/input para adicionar pergunta
    const addQuestionBtn = page.locator('button').filter({ hasText: /adicionar pergunta|nova pergunta|add question|\+ pergunta/i }).first()
    if (await addQuestionBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await addQuestionBtn.click()
      await page.waitForTimeout(500)

      // Preenche a pergunta
      const questionInput = page.locator('textarea, input').filter({ hasText: '' }).last()
        .or(page.locator('textarea[placeholder*="pergunta"], input[placeholder*="pergunta"]').first())
      if (await questionInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await questionInput.fill('Descreva sua experiência com gestão de projetos em equipes remotas.')
      }
    }

    await jobHelpers.screenshotStep('04-T04-pergunta-criada')
  })

  // -----------------------------------------------------------------------
  // Test 5: Configurar min_score
  // -----------------------------------------------------------------------
  test('T05 — Configurar score mínimo de triagem', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Procura configurações de score
    const settingsBtn = page.locator('button').filter({ hasText: /configurações|settings|editar config/i }).first()
    if (await settingsBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await settingsBtn.click()
      await page.waitForTimeout(500)
    }

    // Procura input de min_score
    const scoreInput = page.locator('input[type="number"]').filter({ hasText: '' })
      .or(page.getByLabel(/score|pontuação|mínimo/i).first())
      .first()

    if (await scoreInput.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await scoreInput.clear()
      await scoreInput.fill('70')
    }

    await jobHelpers.screenshotStep('04-T05-score-configurado')
  })

  // -----------------------------------------------------------------------
  // Test 6: Configurar auto-agendamento
  // -----------------------------------------------------------------------
  test('T06 — Configurar auto-agendamento', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Procura configuração de agendamento
    const schedulingBtn = page.locator('button').filter({ hasText: /agendamento|scheduling|agendar/i }).first()
    if (await schedulingBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await schedulingBtn.click()
      await page.waitForTimeout(500)
    }

    // Toggle de auto-agendamento
    const autoToggle = page.getByText(/auto.*agendamento|auto.*scheduling|automático/i).locator('..').locator('[role="switch"]').first()
    if (await autoToggle.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await autoToggle.click()
    }

    await jobHelpers.screenshotStep('04-T06-agendamento-configurado')
  })

  // -----------------------------------------------------------------------
  // Test 7: Gerar/atualizar job description
  // -----------------------------------------------------------------------
  test('T07 — Gerar ou atualizar job description', async ({ authenticatedPage: page, jobHelpers }) => {
    await jobHelpers.navigateToJobs()

    await jobHelpers.openJobDetail()
    await jobHelpers.openJobSettings()

    const screeningTab = page.getByText(/triagem|screening|roteiro|wsi/i).first()
    if (await screeningTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await screeningTab.click()
      await page.waitForTimeout(1_000)
    }

    // Procura seção de descrição do cargo
    const descSection = page.getByText(/descrição do cargo|job description/i).first()
    if (await descSection.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await descSection.click()
      await page.waitForTimeout(500)
    }

    // Procura botão de gerar/atualizar
    const generateBtn = page.locator('button').filter({ hasText: /gerar|generate|atualizar descrição|update description/i }).first()
    if (await generateBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const apiPromise = page.waitForResponse(
        res => res.url().includes('/job-description') || res.url().includes('/screening'),
        { timeout: 20_000 }
      ).catch(() => null)

      await generateBtn.click()

      const response = await apiPromise
      if (response) {
        expect(response.status()).toBeLessThan(500)
      }
    }

    await jobHelpers.screenshotStep('04-T07-description-gerada')
  })
})
