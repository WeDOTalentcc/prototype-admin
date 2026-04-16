/**
 * Fixture de suporte para testes E2E de criação de vaga.
 * Extende auth.fixture.ts com helpers específicos para o fluxo de job creation.
 */
import { test as authTest, expect } from './auth.fixture'
import type { Page } from '@playwright/test'

// ---------------------------------------------------------------------------
// Test Data
// ---------------------------------------------------------------------------

export function uniqueJobTitle(prefix = 'E2E Vaga') {
  return `${prefix} ${Date.now()}`
}

export const TEST_JOB_MINIMAL = {
  title: 'E2E Vaga Minima',
  manager: 'Paulo Test',
  managerEmail: 'paulo.test@wedotalent.com',
}

export const TEST_JOB_FULL = {
  title: 'E2E Vaga Completa',
  department: 'Tecnologia',
  workModel: 'remoto',
  employmentType: 'CLT',
  manager: 'Paulo Test',
  managerEmail: 'paulo.test@wedotalent.com',
}

// ---------------------------------------------------------------------------
// Selectors (extraídos do código-fonte)
// ---------------------------------------------------------------------------

export const SEL = {
  // Jobs page — selectors resilientes (Replit pode usar layout diferente do local)
  jobsHeader: '[data-testid="jobs-header"]',
  newJobBtn: '[data-testid="jobs-header"] button:last-of-type',

  // Create modal
  modal: '[role="dialog"][aria-modal="true"]',
  modalTitle: '#create-job-modal-title',
  btnManual: 'button:has-text("Criar manualmente")',
  btnWizard: 'button:has-text("Criar com a LIA")',
  btnSubmit: 'button:has-text("Criar e Configurar")',
  btnBack: 'button:has-text("Voltar")',
  btnClose: 'button[aria-label="Fechar"]',

  // Form fields
  fieldTitle: '#job-title',
  fieldDepartment: '#job-department',
  fieldWorkModel: '#job-work-model',
  fieldEmploymentType: '#job-employment-type',
  fieldManager: '#job-manager',
  fieldManagerEmail: '#job-manager-email',

  // Validation
  errorMsg: 'p:has(svg.w-3)',

  // Toast
  toast: '[data-sonner-toast]',

  // Edit modal
  editModal: '[data-testid="edit-job-modal"]',
}

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------

export interface JobCreationFixture {
  authenticatedPage: Page
  jobHelpers: {
    navigateToJobs: () => Promise<void>
    openCreateModal: () => Promise<void>
    selectManualMode: () => Promise<void>
    fillMinimalForm: (overrides?: Partial<typeof TEST_JOB_MINIMAL>) => Promise<void>
    fillFullForm: (overrides?: Partial<typeof TEST_JOB_FULL>) => Promise<void>
    submitCreateForm: () => Promise<void>
    createJobViaUI: (data?: Partial<typeof TEST_JOB_FULL>) => Promise<string>
    openJobDetail: (jobTitle?: string) => Promise<void>
    openJobSettings: () => Promise<void>
    screenshotStep: (name: string) => Promise<void>
  }
}

export const test = authTest.extend<JobCreationFixture>({
  jobHelpers: async ({ authenticatedPage: page }, use) => {
    const screenshotsDir = 'e2e/screenshots/job-creation'

    const helpers = {
      navigateToJobs: async () => {
        await page.goto('/pt/jobs', { waitUntil: 'domcontentloaded' })
        await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {})
        // Espera algum indicador da página de vagas (Replit pode ter layout diferente)
        await page.getByRole('heading', { name: /vagas|gestão de vagas|jobs/i }).first()
          .or(page.locator(SEL.jobsHeader))
          .waitFor({ state: 'visible', timeout: 15_000 }).catch(() => {})
      },

      openCreateModal: async () => {
        // Estratégia resiliente: busca por role button com texto "Nova Vaga"
        const newJobButton = page.getByRole('button', { name: /nova vaga/i }).first()
        await newJobButton.waitFor({ state: 'visible', timeout: 10_000 })
        await newJobButton.click()
        // Espera modal abrir — usa getByRole dialog que é o mais semântico
        await page.getByRole('dialog').first().waitFor({ state: 'visible', timeout: 10_000 })
      },

      selectManualMode: async () => {
        await page.locator(SEL.btnManual).click()
        // Espera o título mudar para "Criar Vaga Manualmente"
        await page.locator(SEL.modalTitle).filter({ hasText: 'Criar Vaga Manualmente' }).waitFor({ timeout: 3_000 }).catch(() => {})
      },

      fillMinimalForm: async (overrides: Partial<typeof TEST_JOB_MINIMAL> = {}) => {
        const data = { ...TEST_JOB_MINIMAL, title: uniqueJobTitle(), ...overrides }
        await page.locator(SEL.fieldTitle).fill(data.title)
        await page.locator(SEL.fieldManager).fill(data.manager)
        await page.locator(SEL.fieldManagerEmail).fill(data.managerEmail)
      },

      fillFullForm: async (overrides: Partial<typeof TEST_JOB_FULL> = {}) => {
        const data = { ...TEST_JOB_FULL, title: uniqueJobTitle('E2E Full'), ...overrides }
        await page.locator(SEL.fieldTitle).fill(data.title)
        if (data.department) {
          await page.locator(SEL.fieldDepartment).selectOption(data.department)
        }
        if (data.workModel) {
          await page.locator(SEL.fieldWorkModel).selectOption(data.workModel)
        }
        if (data.employmentType) {
          await page.locator(SEL.fieldEmploymentType).selectOption(data.employmentType)
        }
        await page.locator(SEL.fieldManager).fill(data.manager)
        await page.locator(SEL.fieldManagerEmail).fill(data.managerEmail)
      },

      submitCreateForm: async () => {
        await page.locator(SEL.btnSubmit).click()
        // Espera toast de sucesso ou erro
        await page.locator(SEL.toast).first().waitFor({ state: 'visible', timeout: 15_000 }).catch(() => {})
      },

      createJobViaUI: async (overrides: Partial<typeof TEST_JOB_FULL> = {}) => {
        await helpers.navigateToJobs()
        await helpers.openCreateModal()
        await helpers.selectManualMode()
        await helpers.fillFullForm(overrides)

        // Intercepta a response para pegar o jobId
        const responsePromise = page.waitForResponse(
          res => res.url().includes('/job-vacancies') && res.request().method() === 'POST',
          { timeout: 15_000 }
        ).catch(() => null)

        await helpers.submitCreateForm()

        const response = await responsePromise
        let jobId = ''
        if (response) {
          try {
            const body = await response.json()
            jobId = body.id || body.job_id || ''
          } catch { /* ignore parse errors */ }
        }

        return jobId
      },

      /**
       * Abre o detalhe de uma vaga clicando na row da tabela.
       * No Replit, isso ativa o JobKanbanPage (showKanban=true), não navega para URL.
       * Ref: useJobsPageCore.ts → handleJobClick → setSelectedJobAndOpenKanban
       */
      openJobDetail: async (jobTitle?: string) => {
        if (jobTitle) {
          // Clica no botão do título da vaga na tabela
          const titleBtn = page.getByRole('button', { name: jobTitle }).first()
          if (await titleBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
            await titleBtn.click()
          } else {
            const row = page.getByRole('row').filter({ hasText: jobTitle }).first()
            await row.click()
          }
        } else {
          // Clica no título da primeira vaga na tabela (coluna "Vaga" contém um button)
          const firstJobTitle = page.locator('tbody button').first()
          if (await firstJobTitle.isVisible({ timeout: 5_000 }).catch(() => false)) {
            await firstJobTitle.click()
          } else {
            // Fallback: clica na primeira row do tbody
            const firstRow = page.getByRole('row').nth(1) // nth(0) é o header
            await firstRow.click()
          }
        }
        // Espera o Kanban/detalhe carregar
        await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {})
        await page.waitForTimeout(2_000)
      },

      /**
       * Dentro do detalhe da vaga (Kanban), abre a aba Settings/Edição.
       * Ref: KanbanJobHeader.tsx → setActiveTab('edit') → JobEditTab
       */
      openJobSettings: async () => {
        // Procura o botão Settings (ícone engrenagem) no header do Kanban
        const settingsBtn = page.getByRole('button', { name: /settings|configurações|editar/i }).first()
          .or(page.locator('button').filter({ hasText: /settings|configurações/i }).first())
        if (await settingsBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
          await settingsBtn.click()
          await page.waitForTimeout(1_000)
        } else {
          // Fallback: procura tab/botão com ícone Settings
          const settingsTab = page.locator('button:has(svg)').filter({ hasText: /config|settings|editar/i }).first()
          if (await settingsTab.isVisible({ timeout: 3_000 }).catch(() => false)) {
            await settingsTab.click()
            await page.waitForTimeout(1_000)
          }
        }
      },

      screenshotStep: async (name: string) => {
        await page.screenshot({
          path: `${screenshotsDir}/${name}.png`,
          fullPage: true,
        })
      },
    }

    await use(helpers)
  },
})

export { expect }
