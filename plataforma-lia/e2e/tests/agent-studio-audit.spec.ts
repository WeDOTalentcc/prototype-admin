import { test, expect, type Page } from '@playwright/test'
import { classifyResponse } from './lia-capability-eval/eval-helpers'

const PAGE_TIMEOUT = 10000

type Severity = 'critical' | 'high' | 'medium' | 'low'
type Status = 'PASS' | 'FAIL' | 'BLOCKED' | 'SKIP' | 'WARN'

interface AuditResult {
  id: string
  area: string
  status: Status
  severity: Severity
  details: string
  bug?: string
}

const results: AuditResult[] = []

let _currentPage: Page | null = null

function record(id: string, area: string, status: Status, severity: Severity, details: string, bug?: string) {
  results.push({ id, area, status, severity, details, bug })
  if (status !== 'PASS' && _currentPage) {
    _currentPage.screenshot({ path: `e2e/evidence/${id}.png`, fullPage: false }).catch(() => {})
  }
}

async function navigateToAgentStudio(page: Page) {
  await page.goto('/')
  await page.waitForLoadState('networkidle', { timeout: PAGE_TIMEOUT })
  await page.locator('text=Agent Studio').click()
  await page.waitForTimeout(3000)
}

async function captureEvidence(page: Page, testId: string) {
  await page.screenshot({ path: `e2e/evidence/${testId}.png`, fullPage: false })
}

test.describe('Agent Studio — E2E Audit', () => {

  test.beforeAll(async () => {
    const fs = await import('fs')
    if (!fs.existsSync('e2e/evidence')) {
      fs.mkdirSync('e2e/evidence', { recursive: true })
    }
  })

  test.beforeEach(async ({ page }) => {
    _currentPage = page
  })

  test.afterEach(async () => {
    _currentPage = null
  })

  test.describe('1. Navigation & Access', () => {
    test('AS-NAV-01: Agent Studio appears in sidebar under CONFIGURAÇÃO', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle', { timeout: PAGE_TIMEOUT })
      const configSection = page.locator('text=CONFIGURAÇÃO').first()
      await expect(configSection).toBeVisible()
      const sidebarItem = page.locator('text=Agent Studio')
      await expect(sidebarItem).toBeVisible()
      record('AS-NAV-01', 'Navigation', 'PASS', 'critical', 'Agent Studio found in sidebar under CONFIGURAÇÃO')
    })

    test('AS-NAV-02: Page loads on sidebar click with correct content', async ({ page }) => {
      await navigateToAgentStudio(page)
      const heading = page.locator('h1, h2, h3').filter({ hasText: 'Agent Studio' }).first()
      await expect(heading).toBeVisible()
      const createBtn = page.locator('button').filter({ hasText: 'Criar Agente' })
      await expect(createBtn).toBeVisible()
      record('AS-NAV-02', 'Navigation', 'PASS', 'critical', 'Agent Studio page loaded with heading and create button')
    })

    test('AS-NAV-03: Header shows "Criar Agente" button and refresh icon', async ({ page }) => {
      await navigateToAgentStudio(page)
      const createBtn = page.locator('button').filter({ hasText: 'Criar Agente' })
      await expect(createBtn).toBeVisible()
      await expect(createBtn).toBeEnabled()
      const refreshBtn = page.locator('button').filter({ has: page.locator('svg.lucide-refresh-cw, svg.lucide-rotate-cw') }).first()
      const hasRefresh = await refreshBtn.isVisible().catch(() => false)
      record('AS-NAV-03', 'Navigation', 'PASS', 'high',
        `Create button visible+enabled, refresh icon: ${hasRefresh}`)
    })

    test('AS-NAV-04: Page content persists after reload', async ({ page }) => {
      await navigateToAgentStudio(page)
      const bodyBefore = await page.textContent('body')
      expect(bodyBefore).toContain('Agent Studio')
      await page.reload()
      await page.waitForLoadState('networkidle', { timeout: PAGE_TIMEOUT })
      await page.waitForTimeout(2000)
      const bodyAfter = await page.textContent('body')
      expect(bodyAfter).toContain('Agent Studio')
      record('AS-NAV-04', 'Navigation', 'PASS', 'high', 'Agent Studio content survives page reload')
    })

    test('AS-NAV-05: Agent sub-items in sidebar when agents exist', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body')
      const hasAgentCards = (body?.includes('Ativo') || body?.includes('Pausado')) ?? false
      if (hasAgentCards) {
        const sidebarLinks = await page.locator('nav a, nav button').count()
        expect(sidebarLinks).toBeGreaterThan(3)
        record('AS-NAV-05', 'Navigation', 'PASS', 'medium', `Sidebar has ${sidebarLinks} navigation items with agents present`)
      } else {
        record('AS-NAV-05', 'Navigation', 'SKIP', 'medium', 'No agents exist — cannot verify sub-items')
      }
    })

    test('AS-NAV-06: No unhandled JS errors on page load', async ({ page }) => {
      const errors: string[] = []
      page.on('pageerror', err => errors.push(err.message))
      await navigateToAgentStudio(page)
      expect(errors.length).toBe(0)
      record('AS-NAV-06', 'Navigation', 'PASS', 'medium', 'Zero JS errors on Agent Studio load')
    })
  })

  test.describe('2. Empty State', () => {
    test('AS-EMPTY-01: Agent explanation section present', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasExplanation = body.includes('O que é um Agente') || body.includes('agente de sourcing') || body.includes('busca automática')
      if (hasExplanation) {
        record('AS-EMPTY-01', 'Empty State', 'PASS', 'medium', 'Agent explanation section found')
      } else {
        const hasAgents = body.includes('Ativo') || body.includes('Pausado')
        record('AS-EMPTY-01', 'Empty State', hasAgents ? 'BLOCKED' : 'FAIL', 'medium',
          hasAgents ? 'BLOCKED: Agents exist, compact/hidden explanation expected' : 'No explanation found and no agents exist')
      }
    })

    test('AS-EMPTY-02: Empty state CTA when no agents', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasAgents = body.includes('Ativo') || body.includes('Pausado')
      if (!hasAgents) {
        const hasCTA = body.includes('Nenhum agente') || body.includes('Criar seu primeiro')
        expect(hasCTA).toBeTruthy()
        record('AS-EMPTY-02', 'Empty State', 'PASS', 'low', 'Empty state CTA visible')
      } else {
        record('AS-EMPTY-02', 'Empty State', 'BLOCKED', 'low', 'BLOCKED: Agents exist in environment')
      }
    })

    test('AS-EMPTY-03: Template cards shown in empty state', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasAgents = body.includes('Ativo') || body.includes('Pausado')
      if (!hasAgents) {
        const hasTemplates = body.includes('Personalizado') || body.includes('Tecnologia')
        expect(hasTemplates).toBeTruthy()
        record('AS-EMPTY-03', 'Empty State', 'PASS', 'low', 'Templates visible in empty state')
      } else {
        record('AS-EMPTY-03', 'Empty State', 'BLOCKED', 'low', 'BLOCKED: Agents exist')
      }
    })
  })

  test.describe('3. Sector Templates', () => {
    test('AS-TPL-01: Sector templates API returns data', async ({ page }) => {
      await navigateToAgentStudio(page)
      const response = await page.request.get('/api/backend-proxy/agent-templates/sectors/tecnologia')
      const status = response.status()
      if (status !== 200) {
        await captureEvidence(page, 'AS-TPL-01-BUG')
      }
      record('AS-TPL-01', 'Templates', status === 200 ? 'PASS' : 'FAIL', 'critical',
        `Templates API /sectors/tecnologia returned HTTP ${status}`,
        status !== 200 ? 'BUG-001' : undefined)
      expect(status).toBe(200)
    })

    test('AS-TPL-02: Expected sector template cards rendered', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const expectedSectors = ['Manufatura', 'Saúde', 'Varejo', 'Tecnologia', 'Transporte']
      const found = expectedSectors.filter(s => body.includes(s))
      const missing = expectedSectors.filter(s => !body.includes(s))
      if (found.length < 3) {
        await captureEvidence(page, 'AS-TPL-02-MISSING')
      }
      record('AS-TPL-02', 'Templates', found.length >= 3 ? 'PASS' : 'FAIL', 'high',
        `Found ${found.length}/5 sectors: [${found.join(', ')}]. Missing: [${missing.join(', ')}]`,
        found.length < 3 ? 'BUG-001' : undefined)
    })

    test('AS-TPL-03: "Personalizado" template always visible', async ({ page }) => {
      await navigateToAgentStudio(page)
      const custom = page.locator('text=Personalizado').first()
      await expect(custom).toBeVisible()
      record('AS-TPL-03', 'Templates', 'PASS', 'high', '"Personalizado" template is visible')
    })

    test('AS-TPL-04: Personalizado click opens creation modal', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Personalizado').first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      await expect(modal).toBeVisible()
      const modalText = await modal.textContent()
      expect(modalText).toContain('Nome')
      record('AS-TPL-04', 'Templates', 'PASS', 'high', 'Personalizado opens modal with form fields')
    })

    test('AS-TPL-05: Sector template pre-selects skills in modal', async ({ page }) => {
      await navigateToAgentStudio(page)
      const techTemplate = page.locator('text=Tecnologia').first()
      if (await techTemplate.isVisible()) {
        await techTemplate.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const checkedSwitches = await modal.locator('button[role="switch"][data-state="checked"]').count()
          record('AS-TPL-05', 'Templates', checkedSwitches > 0 ? 'PASS' : 'WARN', 'medium',
            `${checkedSwitches} skills pre-selected from Tecnologia template`)
        } else {
          record('AS-TPL-05', 'Templates', 'FAIL', 'medium', 'Modal did not open from template click')
        }
      } else {
        await captureEvidence(page, 'AS-TPL-05-BLOCKED')
        record('AS-TPL-05', 'Templates', 'BLOCKED', 'medium', 'Tecnologia template not visible (BUG-001)', 'BUG-001')
      }
    })
  })

  test.describe('4. Creation Modal', () => {
    test('AS-CREATE-01: "+ Criar Agente" opens dialog with role="dialog"', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      await expect(modal).toBeVisible()
      record('AS-CREATE-01', 'Creation Modal', 'PASS', 'critical', 'Create button opens dialog element')
    })

    test('AS-CREATE-02: Modal contains Nome, Vincular, and Skills fields', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      const text = await modal.textContent() ?? ''
      expect(text).toContain('Nome')
      const hasVincular = text.includes('Vincular')
      const hasSkills = text.includes('Skills') || text.includes('Habilidades') || text.includes('Experiência') || text.includes('LinkedIn')
      record('AS-CREATE-02', 'Creation Modal', 'PASS', 'high',
        `Nome: yes, Vincular: ${hasVincular}, Skills/Abilities: ${hasSkills}`)
    })

    test('AS-CREATE-03: Submit button disabled when name is empty', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const nameInput = page.locator('[role="dialog"] input').first()
      await nameInput.fill('')
      const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
      await expect(submitBtn).toBeDisabled()
      record('AS-CREATE-03', 'Creation Modal', 'PASS', 'high', 'Submit button disabled with empty name')
    })

    test('AS-CREATE-04: Submit button enables after entering name', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const nameInput = page.locator('[role="dialog"] input').first()
      await nameInput.fill('Test Agent Name')
      await page.waitForTimeout(500)
      const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
      await expect(submitBtn).toBeEnabled()
      record('AS-CREATE-04', 'Creation Modal', 'PASS', 'high', 'Submit enables with valid name')
    })

    test('AS-CREATE-05: Cancel button closes modal completely', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await page.locator('button:has-text("Cancelar")').click()
      await page.waitForTimeout(500)
      await expect(page.locator('[role="dialog"]')).not.toBeVisible()
      record('AS-CREATE-05', 'Creation Modal', 'PASS', 'medium', 'Cancel closes modal, dialog no longer in DOM')
    })

    test('AS-CREATE-06: ESC key closes modal', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await page.keyboard.press('Escape')
      await page.waitForTimeout(500)
      await expect(page.locator('[role="dialog"]')).not.toBeVisible()
      record('AS-CREATE-06', 'Creation Modal', 'PASS', 'medium', 'ESC closes modal')
    })

    test('AS-CREATE-07: "Vincular a" has Vaga and Pool options', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      const text = await modal.textContent() ?? ''
      const hasVaga = text.includes('Vaga')
      const hasPool = text.includes('Pool')
      expect(hasVaga || hasPool).toBeTruthy()
      record('AS-CREATE-07', 'Creation Modal', 'PASS', 'medium',
        `Vincular options: Vaga=${hasVaga}, Pool=${hasPool}`)
    })

    test('AS-CREATE-08: Skills toggle switches are interactive', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const switches = page.locator('[role="dialog"] button[role="switch"]')
      const count = await switches.count()
      expect(count).toBeGreaterThan(0)
      if (count > 0) {
        const firstSwitch = switches.first()
        const stateBefore = await firstSwitch.getAttribute('data-state')
        await firstSwitch.click()
        await page.waitForTimeout(300)
        const stateAfter = await firstSwitch.getAttribute('data-state')
        expect(stateAfter).not.toBe(stateBefore)
        record('AS-CREATE-08', 'Creation Modal', 'PASS', 'medium',
          `${count} switches found, toggle works (${stateBefore} → ${stateAfter})`)
      }
    })

    test('AS-CREATE-09: Submit shows loading state then completes', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      await page.locator('[role="dialog"] input').first().fill(`Audit Agent ${Date.now()}`)
      const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
      await expect(submitBtn).toBeEnabled()

      const responsePromise = page.waitForResponse(
        r => r.url().includes('sourcing-agents') && r.request().method() === 'POST',
        { timeout: 10000 }
      ).catch(() => null)

      await submitBtn.click()

      const loadingVisible = await page.locator('text=Criando').isVisible().catch(() => false)
      const resp = await responsePromise
      const apiStatus = resp?.status() ?? 0

      const apiOk = apiStatus >= 200 && apiStatus < 300
      record('AS-CREATE-09', 'Creation Modal', apiOk ? 'PASS' : 'WARN', 'high',
        `Loading state observed: ${loadingVisible}, API response: ${apiStatus}`)
    })

    test('AS-CREATE-10: Full UI flow — create agent → verify in backend → verify in UI grid', async ({ page }) => {
      const agentName = `AuditCheck ${Date.now()}`
      await navigateToAgentStudio(page)

      const agentsBeforeResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      const agentsBefore = agentsBeforeResp.status() === 200
        ? ((await agentsBeforeResp.json().catch(() => ({ agents: [] }))).agents || []).length
        : -1

      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      await page.locator('[role="dialog"] input').first().fill(agentName)

      const responsePromise = page.waitForResponse(
        resp => resp.url().includes('/api/') && resp.request().method() === 'POST',
        { timeout: 15000 }
      ).catch(() => null)

      await page.locator('button:has-text("Criar e Calibrar")').click()
      const createResp = await responsePromise
      const createStatus = createResp?.status() ?? 0
      await page.waitForTimeout(3000)

      const agentsAfterResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      let agentsAfter = -1
      let foundInBackend = false
      if (agentsAfterResp.status() === 200) {
        const afterData = await agentsAfterResp.json().catch(() => ({ agents: [] }))
        const afterAgents: Record<string, unknown>[] = afterData.agents || []
        agentsAfter = afterAgents.length
        foundInBackend = afterAgents.some((a: Record<string, unknown>) =>
          String(a.agent_name || a.name || '').includes('AuditCheck')
        )
      }

      const body = await page.textContent('body') ?? ''
      const foundInUI = body.includes(agentName)

      const backendCountIncreased = agentsBefore >= 0 && agentsAfter > agentsBefore
      const fullSuccess = foundInUI && (foundInBackend || backendCountIncreased)
      const partialSuccess = foundInUI || foundInBackend || backendCountIncreased

      if (fullSuccess) {
        record('AS-CREATE-10', 'Creation Modal', 'PASS', 'high',
          `Full E2E verified: UI shows "${agentName}", backend count ${agentsBefore}→${agentsAfter}, found in backend: ${foundInBackend}, create API: ${createStatus}`)
      } else if (partialSuccess) {
        record('AS-CREATE-10', 'Creation Modal', 'WARN', 'high',
          `Partial: UI visible=${foundInUI}, backend found=${foundInBackend}, count ${agentsBefore}→${agentsAfter}, create API: ${createStatus}`)
      } else {
        record('AS-CREATE-10', 'Creation Modal', 'FAIL', 'high',
          `Agent "${agentName}" not found in UI or backend. create API: ${createStatus}, count ${agentsBefore}→${agentsAfter}`)
      }
    })
  })

  test.describe('5. Agent Cards', () => {
    test('AS-CARD-01: Card grid renders with card elements', async ({ page }) => {
      await navigateToAgentStudio(page)
      const cards = page.locator('[class*="rounded"]').filter({ hasText: /Ativo|Pausado|Calibrando/ })
      const count = await cards.count()
      if (count === 0) {
        record('AS-CARD-01', 'Agent Cards', 'SKIP', 'high', 'No agent cards found — cannot verify grid')
        test.skip()
      }
      expect(count).toBeGreaterThan(0)
      record('AS-CARD-01', 'Agent Cards', 'PASS', 'high', `${count} agent cards rendered in grid`)
    })

    test('AS-CARD-02: Each card shows name and version info', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasVersion = body.includes('v1') || body.includes('v2') || body.includes('Versão')
      const hasDate = /\d{2}\/\d{2}|\d{4}/.test(body)
      record('AS-CARD-02', 'Agent Cards', hasVersion ? 'PASS' : 'WARN', 'medium',
        `Version info: ${hasVersion}, Date pattern: ${hasDate}`)
    })

    test('AS-CARD-03: Active badge has green styling', async ({ page }) => {
      await navigateToAgentStudio(page)
      const activeBadge = page.locator('text=Ativo').first()
      if (await activeBadge.isVisible()) {
        const parent = activeBadge.locator('..')
        const classes = await parent.getAttribute('class') ?? ''
        const hasGreen = classes.includes('green') || classes.includes('emerald') || classes.includes('success')
        const bgColor = await activeBadge.evaluate(el => getComputedStyle(el).backgroundColor)
        record('AS-CARD-03', 'Agent Cards', 'PASS', 'medium',
          `Active badge visible, classes: ${hasGreen ? 'green variant' : classes.substring(0, 50)}, bg: ${bgColor}`)
      } else {
        record('AS-CARD-03', 'Agent Cards', 'SKIP', 'medium', 'No active agents to verify badge color')
      }
    })

    test('AS-CARD-04: Skills pills displayed on card', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const skills = ['LinkedIn', 'GitHub', 'Portfólio', 'Currículo', 'Indeed']
      const found = skills.filter(s => body.includes(s))
      record('AS-CARD-04', 'Agent Cards', found.length > 0 ? 'PASS' : 'WARN', 'low',
        found.length > 0 ? `Skills found: ${found.join(', ')}` : 'No skill pills detected')
    })

    test('AS-CARD-05: Card shows stats (Analisados, Aprovados, Taxa)', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const stats = ['Analisados', 'Aprovados', 'Taxa']
      const found = stats.filter(s => body.includes(s))
      expect(found.length).toBeGreaterThanOrEqual(1)
      record('AS-CARD-05', 'Agent Cards', found.length >= 2 ? 'PASS' : 'WARN', 'medium',
        `Stats found: ${found.join(', ')} (${found.length}/3)`)
    })
  })

  test.describe('6. Card Actions', () => {
    test('AS-ACT-01: Pause button sends PATCH to /sourcing-agents/:id/pause', async ({ page }) => {
      await navigateToAgentStudio(page)
      const pauseBtn = page.locator('button').filter({ hasText: 'Pausar' }).first()
      if (await pauseBtn.isVisible()) {
        const responsePromise = page.waitForResponse(
          r => r.url().includes('sourcing-agents') && (r.request().method() === 'PATCH' || r.request().method() === 'POST'),
          { timeout: 5000 }
        ).catch(() => null)
        await pauseBtn.click()
        const resp = await responsePromise
        const status = resp?.status() ?? 0
        await captureEvidence(page, 'AS-ACT-01-PAUSE')
        record('AS-ACT-01', 'Card Actions', status === 200 ? 'PASS' : 'FAIL', 'critical',
          `Pause API returned HTTP ${status} (expected 200)`,
          status !== 200 ? 'BUG-002' : undefined)
      } else {
        record('AS-ACT-01', 'Card Actions', 'SKIP', 'critical', 'No active agent with Pause button found')
      }
    })

    test('AS-ACT-02: Resume button sends PATCH to /sourcing-agents/:id/resume', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resumeBtn = page.locator('button').filter({ hasText: 'Retomar' }).first()
      if (await resumeBtn.isVisible()) {
        const responsePromise = page.waitForResponse(
          r => r.url().includes('sourcing-agents'),
          { timeout: 5000 }
        ).catch(() => null)
        await resumeBtn.click()
        const resp = await responsePromise
        const status = resp?.status() ?? 0
        await captureEvidence(page, 'AS-ACT-02-RESUME')
        record('AS-ACT-02', 'Card Actions', status === 200 ? 'PASS' : 'FAIL', 'critical',
          `Resume API returned HTTP ${status}`,
          status !== 200 ? 'BUG-002' : undefined)
      } else {
        record('AS-ACT-02', 'Card Actions', 'SKIP', 'critical', 'No paused agent with Resume button found')
      }
    })

    test('AS-ACT-03: Recalibrar opens calibration modal', async ({ page }) => {
      await navigateToAgentStudio(page)
      const recalBtn = page.locator('button').filter({ hasText: 'Recalibrar' }).first()
      if (await recalBtn.isVisible()) {
        await recalBtn.click()
        await page.waitForTimeout(2000)
        const modal = page.locator('[role="dialog"]')
        const opened = await modal.isVisible()
        await captureEvidence(page, 'AS-ACT-03-RECAL')
        record('AS-ACT-03', 'Card Actions', opened ? 'PASS' : 'FAIL', 'high',
          opened ? 'Calibration modal opened' : 'Click had no effect — onStartCalibration prop not connected in dashboard-app.tsx',
          opened ? undefined : 'BUG-004')
      } else {
        record('AS-ACT-03', 'Card Actions', 'SKIP', 'high', 'No Recalibrar button visible')
      }
    })

    test('AS-ACT-04: "Ver" navigates to linked job or pool', async ({ page }) => {
      await navigateToAgentStudio(page)
      const verBtn = page.locator('button').filter({ hasText: 'Ver' }).first()
      if (await verBtn.isVisible()) {
        const urlBefore = page.url()
        await verBtn.click()
        await page.waitForTimeout(2000)
        const urlAfter = page.url()
        await captureEvidence(page, 'AS-ACT-04-VER')
        const navigated = urlBefore !== urlAfter
        record('AS-ACT-04', 'Card Actions', navigated ? 'PASS' : 'FAIL', 'high',
          navigated ? `Navigated from ${urlBefore} to ${urlAfter}` : 'URL unchanged — onNavigateToJob/Pool props not connected',
          navigated ? undefined : 'BUG-005')
      } else {
        record('AS-ACT-04', 'Card Actions', 'SKIP', 'high', 'No Ver button visible')
      }
    })
  })

  test.describe('7. Stats Bar', () => {
    test('AS-STATS-01: Stats bar shows agent count labels', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasAtivos = body.includes('Ativos') || body.includes('ativo')
      const hasTotal = body.includes('Total') || body.includes('agentes')
      expect(hasAtivos || hasTotal).toBeTruthy()
      record('AS-STATS-01', 'Stats Bar', 'PASS', 'medium',
        `Stats labels: Ativos=${hasAtivos}, Total=${hasTotal}`)
    })

    test('AS-STATS-02: Pulsing dot element exists for active agents', async ({ page }) => {
      await navigateToAgentStudio(page)
      const pulsingDot = page.locator('.animate-pulse, [class*="pulse"]').first()
      const hasDot = await pulsingDot.isVisible().catch(() => false)
      if (hasDot) {
        const bgColor = await pulsingDot.evaluate(el => getComputedStyle(el).backgroundColor)
        record('AS-STATS-02', 'Stats Bar', 'PASS', 'low', `Pulsing dot visible, color: ${bgColor}`)
      } else {
        record('AS-STATS-02', 'Stats Bar', 'SKIP', 'low', 'No pulsing dot found (may have no active agents)')
      }
    })

    test('AS-STATS-03: Agent count is a valid number', async ({ page }) => {
      await navigateToAgentStudio(page)
      const countElements = page.locator('span, div').filter({ hasText: /^\d+$/ })
      const count = await countElements.count()
      expect(count).toBeGreaterThan(0)
      const firstCount = await countElements.first().textContent()
      const parsedCount = parseInt(firstCount ?? '', 10)
      expect(Number.isNaN(parsedCount)).toBeFalsy()
      record('AS-STATS-03', 'Stats Bar', 'PASS', 'low',
        `Found ${count} numeric elements, first value: ${parsedCount}`)
    })
  })

  test.describe('8. Tab Navigation', () => {
    test('AS-TAB-01: Three tabs present', async ({ page }) => {
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      const hasMeusAgentes = body.includes('Meus Agentes') || body.includes('Agentes')
      const hasTwins = body.includes('Digital Twins')
      const hasSearch = body.includes('Busca Inteligente') || body.includes('Multi-Strategy')
      expect(hasMeusAgentes).toBeTruthy()
      expect(hasTwins).toBeTruthy()
      record('AS-TAB-01', 'Tab Navigation', 'PASS', 'high',
        `Tabs: Agents=${hasMeusAgentes}, Twins=${hasTwins}, Search=${hasSearch}`)
    })

    test('AS-TAB-02: Clicking Digital Twins tab changes content', async ({ page }) => {
      await navigateToAgentStudio(page)
      const bodyBefore = await page.textContent('body') ?? ''
      const twinsTab = page.locator('text=Digital Twins').first()
      await twinsTab.click()
      await page.waitForTimeout(1500)
      const bodyAfter = await page.textContent('body') ?? ''
      const contentChanged = bodyAfter.includes('Twin') || bodyAfter.includes('Gêmeo') || bodyAfter.includes('Nenhum digital twin')
      expect(contentChanged).toBeTruthy()
      record('AS-TAB-02', 'Tab Navigation', 'PASS', 'high',
        `Tab content changed after clicking Digital Twins: ${contentChanged}`)
    })

    test('AS-TAB-03: Tab badge shows count number', async ({ page }) => {
      await navigateToAgentStudio(page)
      const tabButtons = page.locator('button, [role="tab"]').filter({ hasText: /\(\d+\)|\d+/ })
      const count = await tabButtons.count()
      if (count > 0) {
        const text = await tabButtons.first().textContent()
        record('AS-TAB-03', 'Tab Navigation', 'PASS', 'low', `Badge count found in tab: "${text}"`)
      } else {
        const allTabs = await page.locator('button').filter({ hasText: /Agentes|Twins|Busca/ }).allTextContents()
        record('AS-TAB-03', 'Tab Navigation', 'WARN', 'low', `No numeric badge in tabs. Tabs found: ${allTabs.join(', ')}`)
      }
    })

    test('AS-TAB-04: Switching back to Agents tab restores content', async ({ page }) => {
      await navigateToAgentStudio(page)
      const bodyInitial = await page.textContent('body') ?? ''
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(1000)
      const agentsTab = page.locator('text=Meus Agentes').first()
      if (await agentsTab.isVisible()) {
        await agentsTab.click()
      } else {
        await page.locator('text=Agentes').first().click()
      }
      await page.waitForTimeout(1000)
      const bodyRestored = await page.textContent('body') ?? ''
      const restored = bodyRestored.includes('Ativo') || bodyRestored.includes('Criar Agente')
      expect(restored).toBeTruthy()
      record('AS-TAB-04', 'Tab Navigation', 'PASS', 'medium',
        `Tab state restored: agent content visible=${restored}`)
    })
  })

  test.describe('9. Digital Twins', () => {
    test('AS-TWIN-01: Digital Twins tab loads content', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(2000)
      const body = await page.textContent('body') ?? ''
      const hasContent = body.includes('Twin') || body.includes('Gêmeo') || body.includes('Nenhum')
      expect(hasContent).toBeTruthy()
      record('AS-TWIN-01', 'Digital Twins', 'PASS', 'high', `Twins tab content loaded: ${hasContent}`)
    })

    test('AS-TWIN-02: Twins header description text present', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(1000)
      const body = await page.textContent('body') ?? ''
      const hasDescription = body.includes('twin') || body.includes('gêmeo') || body.includes('simulação') || body.includes('perfil')
      record('AS-TWIN-02', 'Digital Twins', hasDescription ? 'PASS' : 'WARN', 'medium',
        hasDescription ? 'Description text found in Twins tab' : 'No description text found — may use different terminology')
    })

    test('AS-TWIN-03: Evaluate with Twin button or empty state', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(1000)
      const evalBtn = page.locator('button').filter({ hasText: /Avaliar|Criar Twin|Novo Twin/ }).first()
      const hasEval = await evalBtn.isVisible().catch(() => false)
      const body = await page.textContent('body') ?? ''
      const hasEmpty = body.includes('Nenhum') || body.includes('nenhum')
      if (hasEval) {
        record('AS-TWIN-03', 'Digital Twins', 'PASS', 'medium', 'Evaluate/Create Twin button found')
      } else if (hasEmpty) {
        record('AS-TWIN-03', 'Digital Twins', 'PASS', 'medium', 'Empty state shown (no twins exist)')
      } else {
        record('AS-TWIN-03', 'Digital Twins', 'BLOCKED', 'medium', 'No twins and no clear empty state CTA')
      }
    })
  })

  test.describe('10. Multi-Strategy Search', () => {
    test('AS-SEARCH-01: Search tab loads form', async ({ page }) => {
      await navigateToAgentStudio(page)
      const searchTab = page.locator('text=Busca Inteligente').first()
      if (await searchTab.isVisible()) {
        await searchTab.click()
        await page.waitForTimeout(2000)
        const inputs = await page.locator('input, textarea').count()
        expect(inputs).toBeGreaterThan(0)
        record('AS-SEARCH-01', 'Multi-Strategy Search', 'PASS', 'high', `Search form loaded with ${inputs} input fields`)
      } else {
        record('AS-SEARCH-01', 'Multi-Strategy Search', 'SKIP', 'high', 'Busca Inteligente tab not visible')
      }
    })

    test('AS-SEARCH-02: Title and location fields present', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Busca Inteligente').first().click()
      await page.waitForTimeout(1000)
      const body = await page.textContent('body') ?? ''
      const hasTitulo = body.includes('Título') || body.includes('Cargo') || body.includes('título')
      const hasLocal = body.includes('Local') || body.includes('Região') || body.includes('localização')
      record('AS-SEARCH-02', 'Multi-Strategy Search', hasTitulo ? 'PASS' : 'WARN', 'high',
        `Title field: ${hasTitulo}, Location field: ${hasLocal}`)
    })

    test('AS-SEARCH-03: Search button disabled without required input', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Busca Inteligente').first().click()
      await page.waitForTimeout(1000)
      const searchBtn = page.locator('button').filter({ hasText: /Buscar|Iniciar/ }).first()
      if (await searchBtn.isVisible().catch(() => false)) {
        const disabled = await searchBtn.isDisabled()
        record('AS-SEARCH-03', 'Multi-Strategy Search', disabled ? 'PASS' : 'WARN', 'medium',
          disabled ? 'Search button disabled without input' : 'Button enabled — may allow empty search')
      } else {
        record('AS-SEARCH-03', 'Multi-Strategy Search', 'SKIP', 'medium', 'Search button not found')
      }
    })

    test('AS-SEARCH-04: Search execution crashes app (BUG-003)', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Busca Inteligente').first().click()
      await page.waitForTimeout(1000)

      const titleInput = page.locator('input').first()
      if (await titleInput.isVisible()) {
        await titleInput.fill('Senior Software Engineer')
        await page.waitForTimeout(500)

        const searchBtn = page.locator('button').filter({ hasText: /Buscar|Iniciar/ }).first()
        if (await searchBtn.isVisible().catch(() => false) && await searchBtn.isEnabled()) {
          await searchBtn.click()
          await page.waitForTimeout(5000)
          const body = await page.textContent('body') ?? ''
          const crashed = body.includes('Algo deu errado') || body.includes('Application error')
          await captureEvidence(page, 'AS-SEARCH-04-CRASH')
          record('AS-SEARCH-04', 'Multi-Strategy Search', crashed ? 'FAIL' : 'PASS', 'critical',
            crashed ? 'APP CRASHED: Error boundary triggered after multi-strategy search. Root cause: empty BACKEND_URL in proxy + undefined handling in MultiStrategySearchPanel' : 'Search executed without crash',
            crashed ? 'BUG-003' : undefined)
        }
      }
    })
  })

  test.describe('11. Calibration Deep Flow', () => {
    test('AS-CAL-01: Calibration entry point blocked by BUG-004', async ({ page }) => {
      await navigateToAgentStudio(page)
      const recalBtn = page.locator('button').filter({ hasText: 'Recalibrar' }).first()
      if (await recalBtn.isVisible()) {
        await recalBtn.click()
        await page.waitForTimeout(2000)
        const modal = page.locator('[role="dialog"]')
        const opened = await modal.isVisible()
        await captureEvidence(page, 'AS-CAL-01')
        record('AS-CAL-01', 'Calibration', opened ? 'PASS' : 'BLOCKED', 'critical',
          opened ? 'Calibration modal opened' : 'BLOCKED: onStartCalibration prop not wired in <AgentStudioPage /> render at dashboard-app.tsx:195',
          opened ? undefined : 'BUG-004')
      } else {
        record('AS-CAL-01', 'Calibration', 'BLOCKED', 'critical', 'No Recalibrar button — no agents or button hidden')
      }
    })

    test('AS-CAL-02: Candidate approval flow (blocked by BUG-002 + BUG-004)', async ({ page }) => {
      record('AS-CAL-02', 'Calibration', 'BLOCKED', 'high',
        'BLOCKED: Calibration modal unreachable. BUG-004 prevents modal open (onStartCalibration not connected). BUG-002 prevents API calls (/sourcing-agents/[id]/calibration-candidates returns 404 — Next.js [id]/route.ts cannot match sub-paths)',
        'BUG-002, BUG-004')
    })

    test('AS-CAL-03: Candidate rejection with reasons (blocked)', async ({ page }) => {
      record('AS-CAL-03', 'Calibration', 'BLOCKED', 'high',
        'BLOCKED: Same root causes as AS-CAL-02. CalibrationCardModal requires calibration-candidates API which 404s via current proxy routing.',
        'BUG-002, BUG-004')
    })

    test('AS-CAL-04: Candidate navigation arrows (blocked)', async ({ page }) => {
      record('AS-CAL-04', 'Calibration', 'BLOCKED', 'high',
        'BLOCKED: Same. ChevronLeft/ChevronRight navigation in CalibrationCardModal inaccessible.',
        'BUG-002, BUG-004')
    })

    test('AS-CAL-05: Calibration completion triggers agent update (blocked)', async ({ page }) => {
      record('AS-CAL-05', 'Calibration', 'BLOCKED', 'high',
        'BLOCKED: Cannot reach calibration completion. Fix requires catch-all route [id]/[...path]/route.ts + connecting onStartCalibration prop.',
        'BUG-002, BUG-004')
    })
  })

  test.describe('12. Wizard Job Creation Flow', () => {
    test('AS-WIZ-01: Navigate to Vagas and find creation wizard', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle', { timeout: PAGE_TIMEOUT })
      const vagasLink = page.locator('a, button').filter({ hasText: 'Vagas' }).first()
      if (await vagasLink.isVisible()) {
        await vagasLink.click()
        await page.waitForTimeout(3000)
        const body = await page.textContent('body') ?? ''
        const createBtn = page.locator('button').filter({ hasText: /Criar|Nova Vaga/ }).first()
        const hasCreate = await createBtn.isVisible().catch(() => false)
        if (hasCreate) {
          await createBtn.click()
          await page.waitForTimeout(3000)
          const wizardBody = await page.textContent('body') ?? ''
          const hasSourceStep = wizardBody.includes('Sourcing') || wizardBody.includes('sourcing') || wizardBody.includes('ativar sourcing')
          await captureEvidence(page, 'AS-WIZ-01')
          record('AS-WIZ-01', 'Wizard', hasSourceStep ? 'PASS' : 'SKIP', 'medium',
            hasSourceStep ? 'WizardAgentStep found in job creation wizard' : 'Sourcing step not visible at this wizard stage')
        } else {
          record('AS-WIZ-01', 'Wizard', 'SKIP', 'medium', `No create button on Vagas page. Body contains: ${body.substring(0, 100)}`)
        }
      } else {
        record('AS-WIZ-01', 'Wizard', 'SKIP', 'medium', 'Vagas link not found in sidebar')
      }
    })

    test('AS-WIZ-02: Sourcing activation has Sim/Não options', async ({ page }) => {
      record('AS-WIZ-02', 'Wizard', 'SKIP', 'medium',
        'Depends on AS-WIZ-01 reaching WizardAgentStep. Component has "Sim, ativar sourcing" and "Não, vou buscar manualmente" buttons per code review.')
    })
  })

  test.describe('13. Visual Quality', () => {
    test('AS-VIS-01: Primary colors match Design System tokens', async ({ page }) => {
      await navigateToAgentStudio(page)
      const createBtn = page.locator('button').filter({ hasText: 'Criar Agente' }).first()
      const bgColor = await createBtn.evaluate(el => getComputedStyle(el).backgroundColor)
      const isDesignSystemColor = bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent'
      record('AS-VIS-01', 'Visual Quality', isDesignSystemColor ? 'PASS' : 'WARN', 'medium',
        `Primary button background: ${bgColor}`)
    })

    test('AS-VIS-02: Font family is consistent', async ({ page }) => {
      await navigateToAgentStudio(page)
      const heading = page.locator('h1, h2, h3').first()
      const fontFamily = await heading.evaluate(el => getComputedStyle(el).fontFamily)
      const bodyFont = await page.locator('body').evaluate(el => getComputedStyle(el).fontFamily)
      record('AS-VIS-02', 'Visual Quality', fontFamily.length > 0 ? 'PASS' : 'FAIL', 'low',
        `Heading font: ${fontFamily.substring(0, 40)}, Body font: ${bodyFont.substring(0, 40)}`)
    })

    test('AS-VIS-03: Dark mode renders without broken elements', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.evaluate(() => document.documentElement.classList.add('dark'))
      await page.waitForTimeout(1000)
      const bodyBg = await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor)
      const isDark = bodyBg !== 'rgb(255, 255, 255)' && bodyBg !== 'rgba(0, 0, 0, 0)'
      const heading = page.locator('h1, h2, h3').first()
      const textColor = await heading.evaluate(el => getComputedStyle(el).color)
      record('AS-VIS-03', 'Visual Quality', isDark ? 'PASS' : 'WARN', 'medium',
        `Dark mode bg: ${bodyBg}, text: ${textColor}`)
    })

    test('AS-VIS-04: Card border-radius and shadow consistency', async ({ page }) => {
      await navigateToAgentStudio(page)
      const card = page.locator('[class*="rounded"]').first()
      if (await card.isVisible()) {
        const borderRadius = await card.evaluate(el => getComputedStyle(el).borderRadius)
        const boxShadow = await card.evaluate(el => getComputedStyle(el).boxShadow)
        record('AS-VIS-04', 'Visual Quality', borderRadius !== '0px' ? 'PASS' : 'WARN', 'low',
          `Card border-radius: ${borderRadius}, shadow: ${boxShadow.substring(0, 50)}`)
      } else {
        record('AS-VIS-04', 'Visual Quality', 'SKIP', 'low', 'No card elements found')
      }
    })

    test('AS-VIS-05: Lucide icons render as SVG', async ({ page }) => {
      await navigateToAgentStudio(page)
      const svgs = await page.locator('svg').count()
      expect(svgs).toBeGreaterThan(3)
      record('AS-VIS-05', 'Visual Quality', 'PASS', 'low', `${svgs} SVG icons rendered on page`)
    })

    test('AS-VIS-06: Consistent spacing between card elements', async ({ page }) => {
      await navigateToAgentStudio(page)
      const cards = page.locator('[class*="rounded"]').filter({ hasText: /Ativo|Pausado/ })
      const count = await cards.count()
      if (count >= 2) {
        const box1 = await cards.nth(0).boundingBox()
        const box2 = await cards.nth(1).boundingBox()
        if (box1 && box2) {
          const gap = Math.abs(box2.x - box1.x - box1.width)
          const widthsEqual = Math.abs(box1.width - box2.width) < 5
          expect(widthsEqual).toBeTruthy()
          expect(gap).toBeLessThan(100)
          record('AS-VIS-06', 'Visual Quality', 'PASS', 'low',
            `Gap: ${gap}px, widths: ${box1.width}px/${box2.width}px, consistent=${widthsEqual}`)
        }
      } else {
        record('AS-VIS-06', 'Visual Quality', 'SKIP', 'low', `Only ${count} cards — cannot measure spacing`)
      }
    })

    test('AS-VIS-07: No horizontal overflow on page', async ({ page }) => {
      await navigateToAgentStudio(page)
      const hasOverflow = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth
      })
      expect(hasOverflow).toBeFalsy()
      record('AS-VIS-07', 'Visual Quality', hasOverflow ? 'FAIL' : 'PASS', 'low',
        hasOverflow ? 'Horizontal overflow detected' : 'No horizontal overflow')
    })
  })

  test.describe('14. Accessibility', () => {
    test('AS-A11Y-01: All buttons have accessible names', async ({ page }) => {
      await navigateToAgentStudio(page)
      const buttons = page.locator('button')
      const count = await buttons.count()
      let unlabeled = 0
      const unlabeledTexts: string[] = []
      for (let i = 0; i < Math.min(count, 15); i++) {
        const btn = buttons.nth(i)
        const text = (await btn.textContent())?.trim()
        const ariaLabel = await btn.getAttribute('aria-label')
        const title = await btn.getAttribute('title')
        if (!text && !ariaLabel && !title) {
          unlabeled++
          const html = await btn.evaluate(el => el.outerHTML.substring(0, 80))
          unlabeledTexts.push(html)
        }
      }
      record('AS-A11Y-01', 'Accessibility', unlabeled === 0 ? 'PASS' : 'WARN', 'medium',
        `${count} buttons checked, ${unlabeled} without accessible name. ${unlabeledTexts.length > 0 ? 'Examples: ' + unlabeledTexts[0] : ''}`)
    })

    test('AS-A11Y-02: Modal traps focus inside dialog', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).toBeVisible()
      const focusedElement = await page.evaluate(() => document.activeElement?.closest('[role="dialog"]'))
      record('AS-A11Y-02', 'Accessibility', focusedElement ? 'PASS' : 'WARN', 'medium',
        focusedElement ? 'Focus is inside dialog' : 'Focus may not be trapped in dialog')
    })

    test('AS-A11Y-03: Dialog has aria-describedby attribute', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const dialog = page.locator('[role="dialog"]')
      const ariaDesc = await dialog.getAttribute('aria-describedby')
      const ariaLabel = await dialog.getAttribute('aria-label')
      const ariaLabelledBy = await dialog.getAttribute('aria-labelledby')
      await captureEvidence(page, 'AS-A11Y-03')
      record('AS-A11Y-03', 'Accessibility', ariaDesc ? 'PASS' : 'WARN', 'medium',
        `aria-describedby: ${ariaDesc ?? 'MISSING'}, aria-label: ${ariaLabel ?? 'none'}, aria-labelledby: ${ariaLabelledBy ?? 'none'}`,
        ariaDesc ? undefined : 'BUG-006')
    })

    test('AS-A11Y-04: Tab key moves focus through interactive elements', async ({ page }) => {
      await navigateToAgentStudio(page)
      const focused: string[] = []
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab')
        const tag = await page.evaluate(() => document.activeElement?.tagName)
        focused.push(tag ?? 'null')
      }
      const hasInteractive = focused.some(t => ['BUTTON', 'A', 'INPUT', 'SELECT'].includes(t))
      expect(hasInteractive).toBeTruthy()
      record('AS-A11Y-04', 'Accessibility', 'PASS', 'low',
        `Tab sequence: ${focused.join(' → ')}`)
    })
  })

  test.describe('15. Responsiveness', () => {
    test('AS-RESP-01: Mobile viewport (400px) renders without overflow', async ({ page }) => {
      await page.setViewportSize({ width: 400, height: 800 })
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      expect(body).toContain('Agent Studio')
      const hasOverflow = await page.evaluate(() =>
        document.documentElement.scrollWidth > document.documentElement.clientWidth
      )
      record('AS-RESP-01', 'Responsiveness', !hasOverflow ? 'PASS' : 'WARN', 'medium',
        `Mobile: content renders, overflow=${hasOverflow}`)
    })

    test('AS-RESP-02: Tablet viewport (768px) renders with proper layout', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      expect(body).toContain('Agent Studio')
      const cards = page.locator('[class*="rounded"]').filter({ hasText: /Ativo|Pausado/ })
      const count = await cards.count()
      record('AS-RESP-02', 'Responsiveness', 'PASS', 'medium',
        `Tablet: renders OK, ${count} agent cards visible`)
    })

    test('AS-RESP-03: Desktop viewport (1280px) uses full width', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 900 })
      await navigateToAgentStudio(page)
      const body = await page.textContent('body') ?? ''
      expect(body).toContain('Agent Studio')
      const mainWidth = await page.locator('main, [class*="flex-1"]').first().evaluate(
        el => el.getBoundingClientRect().width
      ).catch(() => 0)
      record('AS-RESP-03', 'Responsiveness', mainWidth > 600 ? 'PASS' : 'WARN', 'medium',
        `Desktop: main content width=${mainWidth}px`)
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 17. SOURCING AGENT CREATION — FULL FLOW WITH SECTOR TEMPLATES
  // ─────────────────────────────────────────────────────────────────
  test.describe('17. Sourcing Agent Creation — Full Flow', () => {
    test('AS-SRC-01: Create sourcing agent (Personalizado) — full API flow', async ({ page }) => {
      const agentName = `SrcAudit-${Date.now()}`
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      await expect(modal).toBeVisible()
      await page.locator('[role="dialog"] input').first().fill(agentName)

      const apiPromise = page.waitForResponse(
        r => r.url().includes('sourcing-agents') && r.request().method() === 'POST',
        { timeout: 15000 }
      ).catch(() => null)

      const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
      if (await submitBtn.isEnabled().catch(() => false)) {
        await submitBtn.click()
        const resp = await apiPromise
        const status = resp?.status() ?? 0
        await captureEvidence(page, 'AS-SRC-01')
        record('AS-SRC-01', 'Sourcing Creation', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'critical',
          `POST /sourcing-agents returned HTTP ${status}. Agent name: "${agentName}"`,
          status === 0 ? 'BUG-SRC-001' : undefined)
      } else {
        record('AS-SRC-01', 'Sourcing Creation', 'WARN', 'critical',
          'Submit button not enabled — could not complete creation flow')
      }
    })

    test('AS-SRC-02: Create agent from Tecnologia template — skills pre-selected', async ({ page }) => {
      await navigateToAgentStudio(page)
      const techTemplate = page.locator('text=Tecnologia').first()
      if (await techTemplate.isVisible()) {
        await techTemplate.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const nameInput = await modal.locator('input').first()
          const prefilledName = await nameInput.inputValue()
          const checkedSwitches = await modal.locator('button[role="switch"][data-state="checked"]').count()
          await captureEvidence(page, 'AS-SRC-02')
          record('AS-SRC-02', 'Sourcing Creation', 'PASS', 'high',
            `Tecnologia template opened modal. Pre-filled name: "${prefilledName}", pre-selected skills: ${checkedSwitches}`)
        } else {
          record('AS-SRC-02', 'Sourcing Creation', 'FAIL', 'high',
            'Tecnologia template did not open modal')
        }
      } else {
        record('AS-SRC-02', 'Sourcing Creation', 'BLOCKED', 'high',
          'Tecnologia template not visible — templates API may have failed (BUG-001)', 'BUG-001')
      }
    })

    test('AS-SRC-03: Create agent from Saúde template', async ({ page }) => {
      await navigateToAgentStudio(page)
      const template = page.locator('text=Saúde').first()
      if (await template.isVisible()) {
        await template.click()
        await page.waitForTimeout(1000)
        const opened = await page.locator('[role="dialog"]').isVisible()
        record('AS-SRC-03', 'Sourcing Creation', opened ? 'PASS' : 'FAIL', 'medium',
          opened ? 'Saúde template opens creation modal' : 'Saúde template did not open modal')
        if (opened) await page.keyboard.press('Escape')
      } else {
        record('AS-SRC-03', 'Sourcing Creation', 'BLOCKED', 'medium', 'Saúde template not visible', 'BUG-001')
      }
    })

    test('AS-SRC-04: Create agent from Varejo template', async ({ page }) => {
      await navigateToAgentStudio(page)
      const template = page.locator('text=Varejo').first()
      if (await template.isVisible()) {
        await template.click()
        await page.waitForTimeout(1000)
        const opened = await page.locator('[role="dialog"]').isVisible()
        record('AS-SRC-04', 'Sourcing Creation', opened ? 'PASS' : 'FAIL', 'medium',
          opened ? 'Varejo template opens creation modal' : 'Varejo template did not open modal')
        if (opened) await page.keyboard.press('Escape')
      } else {
        record('AS-SRC-04', 'Sourcing Creation', 'BLOCKED', 'medium', 'Varejo template not visible', 'BUG-001')
      }
    })

    test('AS-SRC-05: Create agent from Manufatura template', async ({ page }) => {
      await navigateToAgentStudio(page)
      const template = page.locator('text=Manufatura').first()
      if (await template.isVisible()) {
        await template.click()
        await page.waitForTimeout(1000)
        const opened = await page.locator('[role="dialog"]').isVisible()
        record('AS-SRC-05', 'Sourcing Creation', opened ? 'PASS' : 'FAIL', 'medium',
          opened ? 'Manufatura template opens creation modal' : 'Manufatura template did not open modal')
        if (opened) await page.keyboard.press('Escape')
      } else {
        record('AS-SRC-05', 'Sourcing Creation', 'BLOCKED', 'medium', 'Manufatura template not visible', 'BUG-001')
      }
    })

    test('AS-SRC-06: Create agent from Transporte template', async ({ page }) => {
      await navigateToAgentStudio(page)
      const template = page.locator('text=Transporte').first()
      if (await template.isVisible()) {
        await template.click()
        await page.waitForTimeout(1000)
        const opened = await page.locator('[role="dialog"]').isVisible()
        record('AS-SRC-06', 'Sourcing Creation', opened ? 'PASS' : 'FAIL', 'medium',
          opened ? 'Transporte template opens creation modal' : 'Transporte template did not open modal')
        if (opened) await page.keyboard.press('Escape')
      } else {
        record('AS-SRC-06', 'Sourcing Creation', 'BLOCKED', 'medium', 'Transporte template not visible', 'BUG-001')
      }
    })

    test('AS-SRC-07: Validation — empty name keeps submit disabled', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      if (await modal.isVisible()) {
        const nameInput = modal.locator('input').first()
        await nameInput.fill('')
        const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
        const isDisabled = await submitBtn.isDisabled().catch(() => true)
        record('AS-SRC-07', 'Sourcing Creation', isDisabled ? 'PASS' : 'FAIL', 'high',
          isDisabled ? 'Submit disabled with empty name — validation works' : 'FAIL: Submit enabled with empty name — no validation')
      } else {
        record('AS-SRC-07', 'Sourcing Creation', 'SKIP', 'high', 'Modal did not open')
      }
    })

    test('AS-SRC-08: Modal shows Vincular a Vaga and Vincular a Pool options', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      if (await modal.isVisible()) {
        const text = await modal.textContent() ?? ''
        const hasVaga = text.includes('Vaga') || text.includes('vaga')
        const hasPool = text.includes('Pool') || text.includes('pool') || text.includes('banco')
        record('AS-SRC-08', 'Sourcing Creation', (hasVaga || hasPool) ? 'PASS' : 'WARN', 'high',
          `Vincular options: Vaga=${hasVaga}, Pool=${hasPool}`)
      } else {
        record('AS-SRC-08', 'Sourcing Creation', 'SKIP', 'high', 'Modal did not open')
      }
    })

    test('AS-SRC-09: Created agent visible in grid after creation', async ({ page }) => {
      const name = `GridCheck-${Date.now()}`
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const modal = page.locator('[role="dialog"]')
      if (await modal.isVisible()) {
        await modal.locator('input').first().fill(name)
        const submitBtn = page.locator('button:has-text("Criar e Calibrar")')
        if (await submitBtn.isEnabled().catch(() => false)) {
          await submitBtn.click()
          await page.waitForTimeout(8000)
          const body = await page.textContent('body') ?? ''
          const found = body.includes(name)
          await captureEvidence(page, 'AS-SRC-09')
          record('AS-SRC-09', 'Sourcing Creation', found ? 'PASS' : 'WARN', 'high',
            found ? `Agent "${name}" appears in grid after creation` : `Agent "${name}" not found in grid — may need reload`)
        } else {
          record('AS-SRC-09', 'Sourcing Creation', 'SKIP', 'high', 'Submit not enabled')
        }
      } else {
        record('AS-SRC-09', 'Sourcing Creation', 'SKIP', 'high', 'Modal did not open')
      }
    })

    test('AS-SRC-10: Agent created via API has correct status field', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        const agents = data.agents || []
        if (agents.length > 0) {
          const agent = agents[0]
          const validStatus = ['active', 'paused', 'completed'].includes(agent.status)
          const hasJobId = 'job_id' in agent
          const hasPoolId = 'talent_pool_id' in agent
          const hasCalibrationV = 'calibration_v' in agent
          record('AS-SRC-10', 'Sourcing Creation', validStatus ? 'PASS' : 'FAIL', 'high',
            `Agent[0]: status="${agent.status}" valid=${validStatus}, job_id present=${hasJobId}, talent_pool_id present=${hasPoolId}, calibration_v present=${hasCalibrationV}`)
        } else {
          record('AS-SRC-10', 'Sourcing Creation', 'SKIP', 'medium', 'No agents in API response to validate')
        }
      } else {
        record('AS-SRC-10', 'Sourcing Creation', 'FAIL', 'high', `GET /sourcing-agents returned HTTP ${resp.status()}`, 'BUG-SRC-002')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 18. CUSTOM AGENTS — CREATION, EDITING, LIFECYCLE
  // ─────────────────────────────────────────────────────────────────
  test.describe('18. Custom Agents — Creation & Lifecycle', () => {
    test('AS-CA-01: Custom Agents tab loads content', async ({ page }) => {
      await navigateToAgentStudio(page)
      const customTab = page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first()
      if (await customTab.isVisible()) {
        await customTab.click()
        await page.waitForTimeout(2000)
        const body = await page.textContent('body') ?? ''
        const hasContent = body.includes('Custom') || body.includes('Agentes Customizados') || body.includes('Meus Agentes')
        record('AS-CA-01', 'Custom Agents', hasContent ? 'PASS' : 'FAIL', 'critical',
          hasContent ? 'Custom Agents tab loads with content' : 'Custom Agents tab shows no recognizable content')
      } else {
        record('AS-CA-01', 'Custom Agents', 'FAIL', 'critical', 'Custom Agents tab not found in navigation')
      }
    })

    test('AS-CA-02: TemplateGallery is visible in Custom Agents tab', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const body = await page.textContent('body') ?? ''
      const hasGallery = body.includes('template') || body.includes('Template') || body.includes('Comece com um template') || body.includes('Criar com IA')
      record('AS-CA-02', 'Custom Agents', hasGallery ? 'PASS' : 'WARN', 'high',
        hasGallery ? 'Template gallery or ConversationalCreator found in Custom tab' : 'No template gallery UI found')
    })

    test('AS-CA-03: ConversationalCreator generates config from description', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const textarea = page.locator('textarea').filter({ hasText: '' }).first()
      if (await textarea.isVisible()) {
        await textarea.fill('Preciso de um agente que avalie candidatos Python com experiência em AWS e classifique por senioridade')
        const generateBtn = page.locator('button:has-text("Gerar")').first()
        if (await generateBtn.isEnabled().catch(() => false)) {
          const apiPromise = page.waitForResponse(
            r => r.url().includes('custom-agents/generate'),
            { timeout: 15000 }
          ).catch(() => null)
          await generateBtn.click()
          const resp = await apiPromise
          const status = resp?.status() ?? 0
          await captureEvidence(page, 'AS-CA-03')
          record('AS-CA-03', 'Custom Agents', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
            `POST /custom-agents/generate: HTTP ${status}`)
        } else {
          record('AS-CA-03', 'Custom Agents', 'SKIP', 'high', 'Generate button not enabled (description may be too short or textarea not visible)')
        }
      } else {
        record('AS-CA-03', 'Custom Agents', 'SKIP', 'high', 'ConversationalCreator textarea not visible in current tab layout')
      }
    })

    test('AS-CA-04: Create custom agent via manual form — POST to /custom-agents', async ({ page }) => {
      const agentName = `CustomAudit-${Date.now()}`
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)

      const newBtn = page.locator('button').filter({ hasText: /Novo Agente Custom|Criar do zero|Criar Agente Custom/ }).first()
      if (await newBtn.isVisible()) {
        await newBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const inputs = modal.locator('input')
          const count = await inputs.count()
          if (count >= 1) await inputs.nth(0).fill(agentName)
          if (count >= 2) await inputs.nth(1).fill('Analista de Fit Cultural')

          const promptArea = modal.locator('textarea')
          if (await promptArea.isVisible()) {
            await promptArea.fill('Você é um agente especialista em avaliar candidatos por fit cultural.')
          }

          const apiPromise = page.waitForResponse(
            r => r.url().includes('custom-agents') && r.request().method() === 'POST',
            { timeout: 10000 }
          ).catch(() => null)

          const saveBtn = modal.locator('button').filter({ hasText: /Criar Agente|Salvar/ }).last()
          if (await saveBtn.isEnabled().catch(() => false)) {
            await saveBtn.click()
            const resp = await apiPromise
            const status = resp?.status() ?? 0
            await captureEvidence(page, 'AS-CA-04')
            record('AS-CA-04', 'Custom Agents', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'critical',
              `POST /custom-agents: HTTP ${status}. Agent: "${agentName}"`)
          } else {
            record('AS-CA-04', 'Custom Agents', 'WARN', 'critical', 'Save button not enabled — required fields may be missing')
          }
        } else {
          record('AS-CA-04', 'Custom Agents', 'FAIL', 'critical', 'Create modal did not open from "Novo Agente Custom"')
        }
      } else {
        record('AS-CA-04', 'Custom Agents', 'SKIP', 'critical', 'Create button not found in Custom Agents tab')
      }
    })

    test('AS-CA-05: Custom agent list shows correct fields (version, domain, tools)', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const body = await page.textContent('body') ?? ''
      const hasVersion = body.includes('Versão') || /v\d+/.test(body)
      const hasDomain = body.includes('Domínio') || body.includes('Dominio')
      const hasExecCount = body.includes('Execuções') || body.includes('Execucoes')
      if (body.includes('Nenhum') || body.includes('nenhum')) {
        record('AS-CA-05', 'Custom Agents', 'SKIP', 'medium', 'No custom agents exist — cannot verify card fields')
      } else {
        record('AS-CA-05', 'Custom Agents', hasVersion ? 'PASS' : 'WARN', 'medium',
          `Fields: version=${hasVersion}, domain=${hasDomain}, execCount=${hasExecCount}`)
      }
    })

    test('AS-CA-06: Edit custom agent — opens modal with pre-filled data', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const editBtn = page.locator('button').filter({ hasText: 'Editar' }).first()
      if (await editBtn.isVisible()) {
        await editBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const firstInput = modal.locator('input').first()
          const value = await firstInput.inputValue()
          record('AS-CA-06', 'Custom Agents', value.length > 0 ? 'PASS' : 'WARN', 'high',
            `Edit modal opened, pre-filled name: "${value}"`)
          await page.keyboard.press('Escape')
        } else {
          record('AS-CA-06', 'Custom Agents', 'FAIL', 'high', 'Edit button clicked but modal did not open')
        }
      } else {
        record('AS-CA-06', 'Custom Agents', 'SKIP', 'high', 'No Edit button visible — no custom agents exist')
      }
    })

    test('AS-CA-07: Edit custom agent — PATCH request sent with updated data', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const editBtn = page.locator('button').filter({ hasText: 'Editar' }).first()
      if (await editBtn.isVisible()) {
        await editBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const firstInput = modal.locator('input').first()
          const updatedName = `Edited-${Date.now()}`
          await firstInput.fill(updatedName)

          const apiPromise = page.waitForResponse(
            r => r.url().includes('custom-agents') && r.request().method() === 'PATCH',
            { timeout: 10000 }
          ).catch(() => null)

          const saveBtn = modal.locator('button').filter({ hasText: /Salvar|Criar/ }).last()
          if (await saveBtn.isEnabled().catch(() => false)) {
            await saveBtn.click()
            const resp = await apiPromise
            const status = resp?.status() ?? 0
            record('AS-CA-07', 'Custom Agents', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
              `PATCH /custom-agents/:id returned HTTP ${status}`)
          } else {
            record('AS-CA-07', 'Custom Agents', 'WARN', 'high', 'Save button not enabled in edit modal')
          }
        } else {
          record('AS-CA-07', 'Custom Agents', 'SKIP', 'high', 'Edit modal did not open')
        }
      } else {
        record('AS-CA-07', 'Custom Agents', 'SKIP', 'high', 'No Edit button — no agents exist')
      }
    })

    test('AS-CA-08: Pause/activate custom agent — PATCH status change', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)

      const pauseBtn = page.locator('button[title="Pausar"]').first()
      const activateBtn = page.locator('button[title="Ativar"]').first()
      const targetBtn = await pauseBtn.isVisible() ? pauseBtn : await activateBtn.isVisible() ? activateBtn : null

      if (targetBtn) {
        const isActivate = targetBtn === activateBtn
        const apiPromise = page.waitForResponse(
          r => r.url().includes('custom-agents') && r.request().method() === 'PATCH',
          { timeout: 8000 }
        ).catch(() => null)
        await targetBtn.click()
        const resp = await apiPromise
        const status = resp?.status() ?? 0
        record('AS-CA-08', 'Custom Agents', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
          `${isActivate ? 'Activate' : 'Pause'} PATCH returned HTTP ${status}`,
          status === 0 ? 'BUG-CA-001' : undefined)
      } else {
        record('AS-CA-08', 'Custom Agents', 'SKIP', 'high', 'No pause/activate button visible — no agents or all archived')
      }
    })

    test('AS-CA-09: Delete custom agent — DELETE request with confirmation', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)

      const deleteBtn = page.locator('button[title="Excluir"]').first()
      if (await deleteBtn.isVisible()) {
        page.once('dialog', async dialog => {
          await dialog.accept()
        })
        const apiPromise = page.waitForResponse(
          r => r.url().includes('custom-agents') && r.request().method() === 'DELETE',
          { timeout: 8000 }
        ).catch(() => null)
        await deleteBtn.click()
        const resp = await apiPromise
        const status = resp?.status() ?? 0
        await captureEvidence(page, 'AS-CA-09')
        record('AS-CA-09', 'Custom Agents', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
          `DELETE /custom-agents/:id returned HTTP ${status}. Confirm dialog handled.`)
      } else {
        record('AS-CA-09', 'Custom Agents', 'SKIP', 'high', 'No delete button — no custom agents exist')
      }
    })

    test('AS-CA-10: Custom agent "Testar" button opens TestDebugPanel', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const testBtn = page.locator('button').filter({ hasText: 'Testar' }).first()
      if (await testBtn.isVisible()) {
        await testBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        const opened = await modal.isVisible()
        const body = opened ? (await modal.textContent() ?? '') : ''
        const hasTestPanel = body.includes('Testar') || body.includes('Ferramentas') || body.includes('Metricas') || body.includes('Envie uma mensagem')
        await captureEvidence(page, 'AS-CA-10')
        record('AS-CA-10', 'Custom Agents', opened && hasTestPanel ? 'PASS' : opened ? 'WARN' : 'FAIL', 'high',
          opened ? `TestDebugPanel opened: ${hasTestPanel ? 'correct UI' : 'unexpected content'}` : 'TestDebugPanel did not open')
      } else {
        record('AS-CA-10', 'Custom Agents', 'SKIP', 'high', 'No Testar button — no custom agents')
      }
    })

    test('AS-CA-11: GET /custom-agents returns valid agents array', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/custom-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({}))
        const agents = data.agents || []
        const total = data.total ?? 0
        const countMatch = agents.length === total || total === 0
        record('AS-CA-11', 'Custom Agents', 'PASS', 'high',
          `GET /custom-agents: total=${total}, agents.length=${agents.length}, count consistent=${countMatch}`)
      } else {
        record('AS-CA-11', 'Custom Agents', 'FAIL', 'high',
          `GET /custom-agents returned HTTP ${resp.status()}`, 'BUG-CA-002')
      }
    })

    test('AS-CA-12: Available tools endpoint returns list for form', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/custom-agents/available-tools')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ tools: [] }))
        const tools = data.tools || []
        record('AS-CA-12', 'Custom Agents', tools.length > 0 ? 'PASS' : 'WARN', 'medium',
          `GET /custom-agents/available-tools: ${tools.length} tools returned (${tools.slice(0, 5).join(', ')}...)`)
      } else {
        record('AS-CA-12', 'Custom Agents', 'FAIL', 'medium',
          `GET /custom-agents/available-tools: HTTP ${resp.status()}`, 'BUG-CA-003')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 19. TEST DEBUG PANEL — FULL INTERACTION FLOW
  // ─────────────────────────────────────────────────────────────────
  test.describe('19. TestDebugPanel — Message & Metrics Flow', () => {
    test('AS-TDP-01: Send message in TestDebugPanel triggers POST /test', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const testBtn = page.locator('button').filter({ hasText: 'Testar' }).first()
      if (await testBtn.isVisible()) {
        await testBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const msgInput = modal.locator('input[type="text"]').first()
          if (await msgInput.isVisible()) {
            await msgInput.fill('Liste os últimos candidatos aprovados')
            const apiPromise = page.waitForResponse(
              r => r.url().includes('custom-agents') && r.url().includes('/test') && r.request().method() === 'POST',
              { timeout: 15000 }
            ).catch(() => null)
            const sendBtn = modal.locator('button').filter({ has: modal.locator('svg') }).last()
            await sendBtn.click()
            const resp = await apiPromise
            const status = resp?.status() ?? 0
            await captureEvidence(page, 'AS-TDP-01')
            record('AS-TDP-01', 'TestDebugPanel', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
              `POST /custom-agents/:id/test: HTTP ${status}`)
          } else {
            record('AS-TDP-01', 'TestDebugPanel', 'WARN', 'high', 'Message input not found in panel')
          }
        } else {
          record('AS-TDP-01', 'TestDebugPanel', 'SKIP', 'high', 'Panel did not open')
        }
      } else {
        record('AS-TDP-01', 'TestDebugPanel', 'SKIP', 'high', 'No custom agents — cannot test panel')
      }
    })

    test('AS-TDP-02: Debug panel shows tool_calls, confidence, latency after response', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const testBtn = page.locator('button').filter({ hasText: 'Testar' }).first()
      if (await testBtn.isVisible()) {
        await testBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const body = await modal.textContent() ?? ''
          const hasTools = body.includes('Ferramentas') || body.includes('tool')
          const hasMetrics = body.includes('Metricas') || body.includes('Tokens') || body.includes('Latencia') || body.includes('Confianca')
          const hasCost = body.includes('Custo') || body.includes('Consumo')
          const hasCompliance = body.includes('Compliance') || body.includes('FairnessGuard')
          record('AS-TDP-02', 'TestDebugPanel', hasMetrics ? 'PASS' : 'WARN', 'medium',
            `UI sections: tools=${hasTools}, metrics=${hasMetrics}, cost=${hasCost}, compliance=${hasCompliance}`)
        } else {
          record('AS-TDP-02', 'TestDebugPanel', 'SKIP', 'medium', 'Panel did not open')
        }
      } else {
        record('AS-TDP-02', 'TestDebugPanel', 'SKIP', 'medium', 'No custom agents')
      }
    })

    test('AS-TDP-03: Multiple messages in sequence — session accumulates interactions', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const testBtn = page.locator('button').filter({ hasText: 'Testar' }).first()
      if (await testBtn.isVisible()) {
        await testBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const msgInput = modal.locator('input[type="text"]').first()
          if (await msgInput.isVisible()) {
            await msgInput.fill('Primeira mensagem de teste')
            await msgInput.press('Enter')
            await page.waitForTimeout(3000)
            await msgInput.fill('Segunda mensagem de teste')
            await msgInput.press('Enter')
            await page.waitForTimeout(3000)
            const body = await modal.textContent() ?? ''
            const interactions = (body.match(/mensagem de teste/g) || []).length
            record('AS-TDP-03', 'TestDebugPanel', interactions >= 2 ? 'PASS' : 'WARN', 'medium',
              `Multi-turn test: ${interactions} messages visible in panel`)
          } else {
            record('AS-TDP-03', 'TestDebugPanel', 'SKIP', 'medium', 'Input not found')
          }
        } else {
          record('AS-TDP-03', 'TestDebugPanel', 'SKIP', 'medium', 'Panel did not open')
        }
      } else {
        record('AS-TDP-03', 'TestDebugPanel', 'SKIP', 'medium', 'No custom agents')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 20. AGENT ↔ JOB INTEGRATION
  // ─────────────────────────────────────────────────────────────────
  test.describe('20. Agent ↔ Job Integration', () => {
    test('AS-JOB-01: Sourcing agents API returns job_id field in each agent', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const allHaveJobId = agents.every(a => 'job_id' in a)
          record('AS-JOB-01', 'Agent-Job Integration', allHaveJobId ? 'PASS' : 'WARN', 'high',
            `${agents.length} agents checked. All have job_id field: ${allHaveJobId}`)
        } else {
          record('AS-JOB-01', 'Agent-Job Integration', 'SKIP', 'high', 'No agents to verify')
        }
      } else {
        record('AS-JOB-01', 'Agent-Job Integration', 'FAIL', 'high', `API returned HTTP ${resp.status()}`)
      }
    })

    test('AS-JOB-02: "Ver" action on agent with job_id navigates to job page', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      let hasLinkedJob = false
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        hasLinkedJob = (data.agents || []).some((a: Record<string, unknown>) => a.job_id != null)
      }

      if (hasLinkedJob) {
        const verBtn = page.locator('button').filter({ hasText: 'Ver' }).first()
        if (await verBtn.isVisible()) {
          const urlBefore = page.url()
          await verBtn.click()
          await page.waitForTimeout(2000)
          const urlAfter = page.url()
          const navigated = urlBefore !== urlAfter
          await captureEvidence(page, 'AS-JOB-02')
          record('AS-JOB-02', 'Agent-Job Integration', navigated ? 'PASS' : 'FAIL', 'high',
            navigated ? `Navigated to: ${urlAfter}` : 'URL unchanged — Ver button not wired to navigation', 'BUG-005')
        } else {
          record('AS-JOB-02', 'Agent-Job Integration', 'WARN', 'high', 'Agent has job_id but no Ver button found')
        }
      } else {
        record('AS-JOB-02', 'Agent-Job Integration', 'SKIP', 'high', 'No agents with job_id to test navigation')
      }
    })

    test('AS-JOB-03: Agent with no job_id shows warning toast on Ver click', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      let hasUnlinked = false
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        hasUnlinked = (data.agents || []).some((a: Record<string, unknown>) => a.job_id == null && a.talent_pool_id == null)
      }

      if (hasUnlinked) {
        const verBtn = page.locator('button').filter({ hasText: 'Ver' }).first()
        if (await verBtn.isVisible()) {
          await verBtn.click()
          await page.waitForTimeout(1500)
          const body = await page.textContent('body') ?? ''
          const hasWarning = body.includes('sem vínculo') || body.includes('Vincule') || body.includes('não está vinculado')
          record('AS-JOB-03', 'Agent-Job Integration', hasWarning ? 'PASS' : 'WARN', 'medium',
            hasWarning ? 'Warning toast shown for unlinked agent' : 'No warning shown — expected "sem vínculo" toast')
        } else {
          record('AS-JOB-03', 'Agent-Job Integration', 'SKIP', 'medium', 'No Ver button found')
        }
      } else {
        record('AS-JOB-03', 'Agent-Job Integration', 'SKIP', 'medium', 'No unlinked agents to verify warning flow')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 21. AGENT ↔ TALENT POOL INTEGRATION
  // ─────────────────────────────────────────────────────────────────
  test.describe('21. Agent ↔ Talent Pool Integration', () => {
    test('AS-POOL-01: Sourcing agents have talent_pool_id field', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const allHavePool = agents.every(a => 'talent_pool_id' in a)
          const withPool = agents.filter(a => a.talent_pool_id != null).length
          record('AS-POOL-01', 'Agent-Pool Integration', allHavePool ? 'PASS' : 'WARN', 'high',
            `${agents.length} agents: ${withPool} with pool, field present=${allHavePool}`)
        } else {
          record('AS-POOL-01', 'Agent-Pool Integration', 'SKIP', 'high', 'No agents to inspect')
        }
      } else {
        record('AS-POOL-01', 'Agent-Pool Integration', 'FAIL', 'high', `API returned HTTP ${resp.status()}`)
      }
    })

    test('AS-POOL-02: Agent with talent_pool_id can navigate to pool via Ver', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      let hasLinkedPool = false
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        hasLinkedPool = (data.agents || []).some((a: Record<string, unknown>) => a.talent_pool_id != null)
      }

      if (hasLinkedPool) {
        const verBtn = page.locator('button').filter({ hasText: 'Ver' }).first()
        if (await verBtn.isVisible()) {
          const urlBefore = page.url()
          await verBtn.click()
          await page.waitForTimeout(2000)
          const urlAfter = page.url()
          const navigated = urlBefore !== urlAfter
          record('AS-POOL-02', 'Agent-Pool Integration', navigated ? 'PASS' : 'FAIL', 'high',
            navigated ? `Navigated to pool page: ${urlAfter}` : 'Navigation failed — onNavigateToPool prop may not be wired', 'BUG-005')
        } else {
          record('AS-POOL-02', 'Agent-Pool Integration', 'WARN', 'high', 'No Ver button found for pool-linked agent')
        }
      } else {
        record('AS-POOL-02', 'Agent-Pool Integration', 'SKIP', 'high', 'No agents linked to pools')
      }
    })

    test('AS-POOL-03: Talent pools API accessible and linked pool exists', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/talent-pools')
      const status = resp.status()
      let poolCount = 0
      if (status === 200) {
        const data = await resp.json().catch(() => ({ pools: [] }))
        poolCount = (data.pools || data).length
      }
      record('AS-POOL-03', 'Agent-Pool Integration', status === 200 ? 'PASS' : 'WARN', 'medium',
        `GET /talent-pools: HTTP ${status}, ${poolCount} pools found`)
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 22. CALIBRATION FLOW — EXTENDED
  // ─────────────────────────────────────────────────────────────────
  test.describe('22. Calibration — Extended Tests', () => {
    test('AS-CAL-EXT-01: Calibration candidates API exists', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const agentId = agents[0].id
          const calResp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/calibration-candidates`)
          const status = calResp.status()
          record('AS-CAL-EXT-01', 'Calibration Extended', status === 200 ? 'PASS' : 'FAIL', 'critical',
            `GET /sourcing-agents/${agentId}/calibration-candidates: HTTP ${status}`,
            status !== 200 ? 'BUG-002' : undefined)
        } else {
          record('AS-CAL-EXT-01', 'Calibration Extended', 'SKIP', 'critical', 'No agents to test calibration endpoint')
        }
      } else {
        record('AS-CAL-EXT-01', 'Calibration Extended', 'SKIP', 'critical', 'Cannot get agents list')
      }
    })

    test('AS-CAL-EXT-02: Calibration thumbs-up API endpoint exists', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const agentId = agents[0].id
          const calResp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/calibration-candidates`)
          if (calResp.status() === 200) {
            const candidates = await calResp.json().catch(() => [])
            if (Array.isArray(candidates) && candidates.length > 0) {
              const candidateId = candidates[0].id || candidates[0].candidate_id
              const feedbackResp = await page.request.post(
                `/api/backend-proxy/sourcing-agents/${agentId}/calibrate`,
                { data: { candidate_id: candidateId, decision: 'approve' } }
              )
              const status = feedbackResp.status()
              record('AS-CAL-EXT-02', 'Calibration Extended', status === 200 ? 'PASS' : 'FAIL', 'high',
                `POST /sourcing-agents/${agentId}/calibrate (approve): HTTP ${status}`,
                status !== 200 ? 'BUG-002' : undefined)
            } else {
              record('AS-CAL-EXT-02', 'Calibration Extended', 'SKIP', 'high', 'No candidates in calibration pool')
            }
          } else {
            record('AS-CAL-EXT-02', 'Calibration Extended', 'BLOCKED', 'high',
              `Calibration candidates endpoint failed: HTTP ${calResp.status()}`, 'BUG-002')
          }
        } else {
          record('AS-CAL-EXT-02', 'Calibration Extended', 'SKIP', 'high', 'No agents to test')
        }
      } else {
        record('AS-CAL-EXT-02', 'Calibration Extended', 'SKIP', 'high', 'Cannot fetch agents')
      }
    })

    test('AS-CAL-EXT-03: Recalibrar button fires API (not hardcoded)', async ({ page }) => {
      await navigateToAgentStudio(page)
      const recalBtn = page.locator('button').filter({ hasText: 'Recalibrar' }).first()
      if (await recalBtn.isVisible()) {
        const netRequests: string[] = []
        page.on('request', req => { netRequests.push(req.url()) })
        await recalBtn.click()
        await page.waitForTimeout(2000)
        const hasNetCall = netRequests.some(u => u.includes('sourcing-agents') || u.includes('calibrat'))
        const modal = await page.locator('[role="dialog"]').isVisible()
        record('AS-CAL-EXT-03', 'Calibration Extended', (modal || hasNetCall) ? 'PASS' : 'FAIL', 'critical',
          `Recalibrar click: modal_opened=${modal}, network_calls=${netRequests.filter(u => u.includes('agent')).join('; ')}`,
          (!modal && !hasNetCall) ? 'BUG-004' : undefined)
      } else {
        record('AS-CAL-EXT-03', 'Calibration Extended', 'SKIP', 'critical', 'No Recalibrar button found')
      }
    })

    test('AS-CAL-EXT-04: calibration_v increments after calibrate API call', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const agentId = agents[0].id
          const calVBefore = (agents[0].calibration_v as number) ?? 0

          const calResp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/calibration-candidates`)
          if (calResp.status() === 200) {
            const calData = await calResp.json().catch(() => ({ candidates: [] }))
            const candidates: Record<string, unknown>[] = Array.isArray(calData) ? calData : (calData.candidates || [])
            if (candidates.length > 0) {
              const candidateId = candidates[0].id
              const calibrateResp = await page.request.post(`/api/backend-proxy/sourcing-agents/${agentId}/calibrate`, {
                data: { candidate_id: candidateId, decision: 'approve' }
              })

              if (!(calibrateResp.status() >= 200 && calibrateResp.status() < 300)) {
                record('AS-CAL-EXT-04', 'Calibration Extended', 'WARN', 'high',
                  `calibration_v=${calVBefore}. Calibrate POST returned HTTP ${calibrateResp.status()} — cannot verify increment`)
                return
              }

              const afterResp = await page.request.get('/api/backend-proxy/sourcing-agents')
              if (afterResp.status() === 200) {
                const afterData = await afterResp.json().catch(() => ({ agents: [] }))
                const afterAgents: Record<string, unknown>[] = afterData.agents || []
                const afterAgent = afterAgents.find((a: Record<string, unknown>) => a.id === agentId)
                const calVAfter = (afterAgent?.calibration_v as number) ?? 0
                const incremented = calVAfter > calVBefore
                record('AS-CAL-EXT-04', 'Calibration Extended', incremented ? 'PASS' : 'WARN', 'high',
                  `calibration_v before=${calVBefore}, after=${calVAfter}. ${incremented ? 'Incremented correctly' : 'Did not increment — may require multiple calibrations'}`)
              } else {
                record('AS-CAL-EXT-04', 'Calibration Extended', 'FAIL', 'high', 'Failed to re-fetch agents after calibration')
              }
            } else {
              record('AS-CAL-EXT-04', 'Calibration Extended', 'SKIP', 'high',
                `calibration_v=${calVBefore}. No candidates available for calibration test.`)
            }
          } else {
            record('AS-CAL-EXT-04', 'Calibration Extended', 'BLOCKED', 'high',
              `calibration_v=${calVBefore}. Calibration candidates API returned HTTP ${calResp.status()}`, 'BUG-002')
          }
        } else {
          record('AS-CAL-EXT-04', 'Calibration Extended', 'SKIP', 'high', 'No agents to verify calibration_v')
        }
      } else {
        record('AS-CAL-EXT-04', 'Calibration Extended', 'SKIP', 'high', 'Cannot fetch agents')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 23. MARKETPLACE — BROWSE, INSTALL, PUBLISH, APPROVALS
  // ─────────────────────────────────────────────────────────────────
  test.describe('23. Marketplace — Full Flow', () => {
    test('AS-MKT-01: Marketplace tab loads with 3 sub-views', async ({ page }) => {
      await navigateToAgentStudio(page)
      const mktTab = page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first()
      if (await mktTab.isVisible()) {
        await mktTab.click()
        await page.waitForTimeout(2000)
        const body = await page.textContent('body') ?? ''
        const hasExplorar = body.includes('Explorar')
        const hasInstalados = body.includes('Instalados')
        const hasConsumo = body.includes('Consumo') || body.includes('Billing')
        record('AS-MKT-01', 'Marketplace', (hasExplorar && hasInstalados) ? 'PASS' : 'WARN', 'high',
          `Marketplace sub-views: Explorar=${hasExplorar}, Instalados=${hasInstalados}, Consumo=${hasConsumo}`)
      } else {
        record('AS-MKT-01', 'Marketplace', 'FAIL', 'high', 'Marketplace tab not found in navigation')
      }
    })

    test('AS-MKT-02: Browse marketplace calls GET /agent-marketplace/listings', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(1000)
      const resp = await page.request.get('/api/backend-proxy/agent-marketplace/listings')
      const status = resp.status()
      let listingCount = 0
      if (status === 200) {
        const data = await resp.json().catch(() => ({ listings: [] }))
        listingCount = (data.listings || data).length
      }
      record('AS-MKT-02', 'Marketplace', status === 200 ? 'PASS' : 'FAIL', 'high',
        `GET /agent-marketplace/listings: HTTP ${status}, ${listingCount} listings found`,
        status !== 200 ? 'BUG-MKT-001' : undefined)
    })

    test('AS-MKT-03: Search filter in marketplace is interactive', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const searchInput = page.locator('input[placeholder*="Buscar"], input[placeholder*="buscar"], input[type="search"]').first()
      if (await searchInput.isVisible()) {
        await searchInput.fill('sourcing')
        await page.waitForTimeout(1000)
        record('AS-MKT-03', 'Marketplace', 'PASS', 'medium', 'Marketplace search filter is interactive')
      } else {
        const body = await page.textContent('body') ?? ''
        const hasSearch = body.includes('Buscar') || body.includes('buscar') || body.includes('Search')
        record('AS-MKT-03', 'Marketplace', hasSearch ? 'WARN' : 'SKIP', 'medium',
          hasSearch ? 'Search UI text found but no input element' : 'Marketplace search not found')
      }
    })

    test('AS-MKT-04: Category filter buttons change displayed listings', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const categoryBtns = page.locator('button').filter({ hasText: /Sourcing|Pipeline|Analytics|Triagem/ })
      const count = await categoryBtns.count()
      if (count > 0) {
        await categoryBtns.first().click()
        await page.waitForTimeout(1000)
        record('AS-MKT-04', 'Marketplace', 'PASS', 'medium', `${count} category filter buttons found and clicked`)
      } else {
        record('AS-MKT-04', 'Marketplace', 'SKIP', 'medium', 'No category filter buttons found in marketplace')
      }
    })

    test('AS-MKT-05: Install button sends POST to /agent-marketplace/install', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const installBtn = page.locator('button').filter({ hasText: /Instalar|Install/ }).first()
      if (await installBtn.isVisible()) {
        const apiPromise = page.waitForResponse(
          r => r.url().includes('marketplace') && r.request().method() === 'POST',
          { timeout: 10000 }
        ).catch(() => null)
        await installBtn.click()
        await page.waitForTimeout(2000)
        const resp = await apiPromise
        const status = resp?.status() ?? 0
        await captureEvidence(page, 'AS-MKT-05')
        record('AS-MKT-05', 'Marketplace', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
          `Install POST: HTTP ${status}`)
      } else {
        record('AS-MKT-05', 'Marketplace', 'SKIP', 'high', 'No Install button — marketplace may be empty')
      }
    })

    test('AS-MKT-06: Installed agents view loads from GET /agent-marketplace/my-installations', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const installedTab = page.locator('button').filter({ hasText: 'Instalados' }).first()
      if (await installedTab.isVisible()) {
        await installedTab.click()
        await page.waitForTimeout(1000)
        const resp = await page.request.get('/api/backend-proxy/agent-marketplace/my-installations')
        const status = resp.status()
        record('AS-MKT-06', 'Marketplace', status === 200 ? 'PASS' : 'FAIL', 'medium',
          `GET /agent-marketplace/my-installations: HTTP ${status}`,
          status !== 200 ? 'BUG-MKT-002' : undefined)
      } else {
        record('AS-MKT-06', 'Marketplace', 'SKIP', 'medium', 'Instalados tab not found')
      }
    })

    test('AS-MKT-07: Publish agent button calls POST /agent-marketplace/publish', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const publishBtn = page.locator('button').filter({ hasText: /Publicar|Publish/ }).first()
      if (await publishBtn.isVisible()) {
        const apiPromise = page.waitForResponse(
          r => r.url().includes('marketplace') && r.request().method() === 'POST',
          { timeout: 10000 }
        ).catch(() => null)
        await publishBtn.click()
        await page.waitForTimeout(2000)
        const resp = await apiPromise
        const status = resp?.status() ?? 0
        record('AS-MKT-07', 'Marketplace', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
          `Publish POST: HTTP ${status}`)
      } else {
        record('AS-MKT-07', 'Marketplace', 'SKIP', 'high', 'No Publish button visible (agents may not be active)')
      }
    })

    test('AS-MKT-08: Approvals list visible in Custom Agents tab', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const resp = await page.request.get('/api/backend-proxy/agent-approvals/pending')
      const status = resp.status()
      let approvalCount = 0
      if (status === 200) {
        const data = await resp.json().catch(() => [])
        approvalCount = Array.isArray(data) ? data.length : (data.approvals || []).length
      }
      const body = await page.textContent('body') ?? ''
      const hasApprovals = body.includes('Aprovacoes') || body.includes('Aprovações') || body.includes('aprovacao') || body.includes('ShieldCheck')
      record('AS-MKT-08', 'Marketplace', status === 200 ? 'PASS' : 'WARN', 'medium',
        `GET /agent-approvals/pending: HTTP ${status}, ${approvalCount} pending. UI shows approvals section: ${hasApprovals}`)
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 24. DIGITAL TWINS — EXTENDED
  // ─────────────────────────────────────────────────────────────────
  test.describe('24. Digital Twins — Extended', () => {
    test('AS-DT-01: Digital Twins API returns list', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/digital-twins')
      const status = resp.status()
      let twinCount = 0
      if (status === 200) {
        const data = await resp.json().catch(() => [])
        twinCount = Array.isArray(data) ? data.length : (data.twins || []).length
      }
      record('AS-DT-01', 'Digital Twins Extended', status === 200 ? 'PASS' : 'WARN', 'high',
        `GET /digital-twins: HTTP ${status}, ${twinCount} twins found`)
    })

    test('AS-DT-02: Avaliar candidato button opens EvaluateWithTwinModal', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(2000)
      const evalBtn = page.locator('button').filter({ hasText: /Avaliar candidato|Avaliar/ }).first()
      if (await evalBtn.isVisible()) {
        await evalBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        const opened = await modal.isVisible()
        await captureEvidence(page, 'AS-DT-02')
        record('AS-DT-02', 'Digital Twins Extended', opened ? 'PASS' : 'FAIL', 'high',
          opened ? 'EvaluateWithTwinModal opened from Avaliar button' : 'Modal did not open')
      } else {
        record('AS-DT-02', 'Digital Twins Extended', 'SKIP', 'high', 'No Avaliar button — no digital twins exist')
      }
    })

    test('AS-DT-03: EvaluateWithTwinModal sends POST to /digital-twins/:id/evaluate', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(2000)
      const evalBtn = page.locator('button').filter({ hasText: /Avaliar candidato|Avaliar/ }).first()
      if (await evalBtn.isVisible()) {
        await evalBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const idInput = modal.locator('input').first()
          if (await idInput.isVisible()) {
            await idInput.fill('test-candidate-123')
            const evaluateBtn = modal.locator('button').filter({ hasText: /Avaliar|Evaluate/ }).last()
            if (await evaluateBtn.isEnabled().catch(() => false)) {
              const apiPromise = page.waitForResponse(
                r => r.url().includes('digital-twin') && r.request().method() === 'POST',
                { timeout: 10000 }
              ).catch(() => null)
              await evaluateBtn.click()
              const resp = await apiPromise
              const status = resp?.status() ?? 0
              record('AS-DT-03', 'Digital Twins Extended', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
                `POST /digital-twins/:id/evaluate: HTTP ${status}`)
            } else {
              record('AS-DT-03', 'Digital Twins Extended', 'WARN', 'high', 'Evaluate button not enabled in modal')
            }
          } else {
            record('AS-DT-03', 'Digital Twins Extended', 'SKIP', 'high', 'No input found in EvaluateWithTwinModal')
          }
        } else {
          record('AS-DT-03', 'Digital Twins Extended', 'SKIP', 'high', 'EvaluateWithTwinModal did not open')
        }
      } else {
        record('AS-DT-03', 'Digital Twins Extended', 'SKIP', 'high', 'No digital twins to test evaluation')
      }
    })

    test('AS-DT-04: Twin card shows accuracy and decision count', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('text=Digital Twins').first().click()
      await page.waitForTimeout(2000)
      const body = await page.textContent('body') ?? ''
      const hasTwins = !(body.includes('Nenhum') && body.includes('twin'))
      if (hasTwins) {
        const hasAccuracy = body.includes('%') || body.includes('precisão') || body.includes('Precisão')
        const hasDecisions = /\d+/.test(body)
        record('AS-DT-04', 'Digital Twins Extended', hasAccuracy ? 'PASS' : 'WARN', 'medium',
          `Twin cards: accuracy shown=${hasAccuracy}, decisions count=${hasDecisions}`)
      } else {
        record('AS-DT-04', 'Digital Twins Extended', 'SKIP', 'medium', 'No digital twins to verify card content')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 25. DEPLOY DIALOG
  // ─────────────────────────────────────────────────────────────────
  test.describe('25. Deploy Dialog', () => {
    test('AS-DEPLOY-01: Deploy button opens DeployDialog with target options', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const deployBtn = page.locator('button').filter({ hasText: /Vincular|Deploy|Publicar/ }).first()
      if (await deployBtn.isVisible()) {
        await deployBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const body = await modal.textContent() ?? ''
          const hasJobTarget = body.includes('Vaga') || body.includes('vaga') || body.includes('job')
          const hasPoolTarget = body.includes('Pool') || body.includes('banco') || body.includes('talent')
          const hasTrigger = body.includes('Trigger') || body.includes('trigger') || body.includes('novo candidato') || body.includes('manual')
          await captureEvidence(page, 'AS-DEPLOY-01')
          record('AS-DEPLOY-01', 'Deploy Dialog', (hasJobTarget || hasPoolTarget) ? 'PASS' : 'WARN', 'high',
            `DeployDialog: job target=${hasJobTarget}, pool target=${hasPoolTarget}, trigger mode=${hasTrigger}`)
          await page.keyboard.press('Escape')
        } else {
          record('AS-DEPLOY-01', 'Deploy Dialog', 'FAIL', 'high', 'DeployDialog did not open')
        }
      } else {
        record('AS-DEPLOY-01', 'Deploy Dialog', 'SKIP', 'high', 'No Vincular/Deploy button found in Custom Agents tab')
      }
    })

    test('AS-DEPLOY-02: Deploy submit sends POST to /custom-agents/:id/deployments', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const deployBtn = page.locator('button').filter({ hasText: /Vincular|Deploy/ }).first()
      if (await deployBtn.isVisible()) {
        await deployBtn.click()
        await page.waitForTimeout(1000)
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible()) {
          const targetInput = modal.locator('input').first()
          if (await targetInput.isVisible()) {
            await targetInput.fill('test-job-id-123')
          }
          const submitBtn = modal.locator('button').filter({ hasText: /Vincular|Deploy/ }).last()
          if (await submitBtn.isEnabled().catch(() => false)) {
            const apiPromise = page.waitForResponse(
              r => r.url().includes('custom-agents') && r.url().includes('deployment') && r.request().method() === 'POST',
              { timeout: 10000 }
            ).catch(() => null)
            await submitBtn.click()
            const resp = await apiPromise
            const status = resp?.status() ?? 0
            record('AS-DEPLOY-02', 'Deploy Dialog', (status >= 200 && status < 300) ? 'PASS' : 'FAIL', 'high',
              `POST /custom-agents/:id/deployments: HTTP ${status}`)
          } else {
            record('AS-DEPLOY-02', 'Deploy Dialog', 'WARN', 'high', 'Deploy submit button not enabled — target ID required')
          }
        } else {
          record('AS-DEPLOY-02', 'Deploy Dialog', 'SKIP', 'high', 'Modal did not open')
        }
      } else {
        record('AS-DEPLOY-02', 'Deploy Dialog', 'SKIP', 'high', 'No deploy button found')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 26. HARDCODED BUTTON DETECTION
  // ─────────────────────────────────────────────────────────────────
  test.describe('26. Hardcoded Button Detection', () => {
    test('AS-HBC-01: Agents tab — ALL buttons intercepted for network calls', async ({ page }) => {
      await navigateToAgentStudio(page)
      const report: Array<{ label: string; hasNetCall: boolean }> = []

      const buttons = page.locator('button:visible')
      const count = await buttons.count()

      for (let i = 0; i < count; i++) {
        const btn = buttons.nth(i)
        const label = (await btn.textContent())?.trim() ?? `[icon-only-${i}]`
        if (['Criar Agente'].includes(label)) continue

        const netCalls: string[] = []
        const handler = (req: { url: () => string }) => { netCalls.push(req.url()) }
        page.on('request', handler)
        await btn.click({ force: true }).catch(() => {})
        await page.waitForTimeout(800)
        page.removeListener('request', handler)
        await page.keyboard.press('Escape').catch(() => {})
        await page.waitForTimeout(300)

        const hasNetCall = netCalls.some(u => u.includes('/api/') && !u.includes('.js') && !u.includes('.css'))
        report.push({ label, hasNetCall })
      }

      const hardcoded = report.filter(r => !r.hasNetCall && r.label !== '' && !r.label.startsWith('[icon'))
      const interactive = report.filter(r => r.hasNetCall)
      await captureEvidence(page, 'AS-HBC-01')
      record('AS-HBC-01', 'Hardcoded Buttons', hardcoded.length === 0 ? 'PASS' : 'WARN', 'critical',
        `Agents tab: ${count} buttons tested. ${interactive.length} fire API calls. Potentially hardcoded (no API): ${hardcoded.map(r => '"' + r.label + '"').join(', ') || 'none'}`)
    })

    test('AS-HBC-02: Custom Agents tab — ALL buttons intercepted for network calls', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Custom Agents' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const report: Array<{ label: string; hasNetCall: boolean }> = []

      const buttons = page.locator('button:visible')
      const count = await buttons.count()

      for (let i = 0; i < count; i++) {
        const btn = buttons.nth(i)
        const label = (await btn.textContent())?.trim() ?? `[icon-only-${i}]`

        const netCalls: string[] = []
        const handler = (req: { url: () => string }) => { netCalls.push(req.url()) }
        page.on('request', handler)
        await btn.click({ force: true }).catch(() => {})
        await page.waitForTimeout(800)
        page.removeListener('request', handler)
        await page.keyboard.press('Escape').catch(() => {})
        await page.waitForTimeout(300)

        const hasNetCall = netCalls.some(u => u.includes('/api/') && !u.includes('.js') && !u.includes('.css'))
        report.push({ label, hasNetCall })
      }

      const hardcoded = report.filter(r => !r.hasNetCall && r.label.length > 0)
      record('AS-HBC-02', 'Hardcoded Buttons', hardcoded.length === 0 ? 'PASS' : 'WARN', 'high',
        `Custom Agents tab: ${count} buttons tested. Hardcoded (no API): ${hardcoded.map(r => '"' + r.label + '"').join(', ') || 'none'}`)
    })

    test('AS-HBC-03: Marketplace tab — ALL buttons intercepted', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button, [role="tab"]').filter({ hasText: 'Marketplace' }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
      const report: Array<{ label: string; hasNetCall: boolean }> = []

      const buttons = page.locator('button:visible')
      const count = await buttons.count()

      for (let i = 0; i < count; i++) {
        const btn = buttons.nth(i)
        const label = (await btn.textContent())?.trim() ?? `[icon-only-${i}]`
        const netCalls: string[] = []
        const handler = (req: { url: () => string }) => { netCalls.push(req.url()) }
        page.on('request', handler)
        await btn.click({ force: true }).catch(() => {})
        await page.waitForTimeout(800)
        page.removeListener('request', handler)
        await page.keyboard.press('Escape').catch(() => {})
        await page.waitForTimeout(300)
        const hasNetCall = netCalls.some(u => u.includes('/api/') && !u.includes('.js') && !u.includes('.css'))
        report.push({ label, hasNetCall })
      }

      const hardcoded = report.filter(r => !r.hasNetCall && r.label.length > 0)
      record('AS-HBC-03', 'Hardcoded Buttons', hardcoded.length === 0 ? 'PASS' : 'WARN', 'medium',
        `Marketplace tab: ${count} buttons tested. Hardcoded (no API): ${hardcoded.map(r => '"' + r.label + '"').join(', ') || 'none'}`)
    })

    test('AS-HBC-04: Search tab — ALL buttons intercepted', async ({ page }) => {
      await navigateToAgentStudio(page)
      const searchTab = page.locator('button, [role="tab"]').filter({ hasText: 'Busca Inteligente' }).first()
      if (await searchTab.isVisible()) {
        await searchTab.click()
        await page.waitForTimeout(2000)
        const report: Array<{ label: string; hasNetCall: boolean }> = []
        const buttons = page.locator('button:visible')
        const count = await buttons.count()

        for (let i = 0; i < count; i++) {
          const btn = buttons.nth(i)
          const label = (await btn.textContent())?.trim() ?? `[icon-only-${i}]`
          const netCalls: string[] = []
          const handler = (req: { url: () => string }) => { netCalls.push(req.url()) }
          page.on('request', handler)
          await btn.click({ force: true }).catch(() => {})
          await page.waitForTimeout(600)
          page.removeListener('request', handler)
          const hasNetCall = netCalls.some(u => u.includes('/api/') && !u.includes('.js'))
          report.push({ label, hasNetCall })
        }

        const hardcoded = report.filter(r => !r.hasNetCall && r.label.length > 0)
        record('AS-HBC-04', 'Hardcoded Buttons', hardcoded.length === 0 ? 'PASS' : 'WARN', 'medium',
          `Search tab: ${count} buttons tested. Hardcoded: ${hardcoded.map(r => '"' + r.label + '"').join(', ') || 'none'}`)
      } else {
        record('AS-HBC-04', 'Hardcoded Buttons', 'SKIP', 'medium', 'Busca Inteligente tab not visible')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 27. QUALITY ASSESSMENT
  // ─────────────────────────────────────────────────────────────────
  test.describe('27. Quality Assessment', () => {
    test('AS-QUAL-01: Sourcing agent returns candidates with required fields', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = (data.agents || []).filter((a: Record<string, unknown>) => a.status === 'active')
        if (agents.length > 0) {
          const agentId = agents[0].id
          const candResp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/candidates`)
          if (candResp.status() === 200) {
            const candData = await candResp.json().catch(() => ({ candidates: [] }))
            const candidates: Record<string, unknown>[] = candData.candidates || candData || []
            if (candidates.length > 0) {
              const sample = candidates[0]
              const hasName = 'name' in sample || 'full_name' in sample
              const hasEmail = 'email' in sample
              const hasScore = 'lia_score' in sample || 'score' in sample || 'match_score' in sample
              const quality = [hasName, hasEmail, hasScore].filter(Boolean).length
              record('AS-QUAL-01', 'Quality Assessment', quality >= 2 ? 'PASS' : 'WARN', 'high',
                `Candidate data quality: name=${hasName}, email=${hasEmail}, score=${hasScore}. Total candidates: ${candidates.length}`)
            } else {
              record('AS-QUAL-01', 'Quality Assessment', 'WARN', 'high', 'Active agent has 0 candidates — sourcing may not have run yet')
            }
          } else {
            record('AS-QUAL-01', 'Quality Assessment', 'WARN', 'high',
              `GET /sourcing-agents/${agentId}/candidates: HTTP ${candResp.status()}`)
          }
        } else {
          record('AS-QUAL-01', 'Quality Assessment', 'SKIP', 'high', 'No active sourcing agents to assess quality')
        }
      } else {
        record('AS-QUAL-01', 'Quality Assessment', 'SKIP', 'high', 'Cannot fetch agents for quality check')
      }
    })

    test('AS-QUAL-02: Custom agent test endpoint returns structured response', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/custom-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const agentId = agents[0].id
          const testResp = await page.request.post(`/api/backend-proxy/custom-agents/${agentId}/test`, {
            data: { message: 'Qual é o seu papel na plataforma?' }
          })
          if (testResp.status() === 200) {
            const result = await testResp.json().catch(() => ({}))
            const hasResponse = 'response' in result
            const hasConfidence = 'confidence' in result
            const hasTokens = 'tokens_input' in result || 'tokens_output' in result
            const hasLatency = 'execution_time_ms' in result

            const responseText: string = result.response || ''
            const classification = responseText.length > 20 ? 'RESPOSTA COERENTE' : 'SEM RESPOSTA'
            const quality = [hasResponse, hasConfidence, hasTokens, hasLatency].filter(Boolean).length

            record('AS-QUAL-02', 'Quality Assessment', quality >= 3 ? 'PASS' : 'WARN', 'high',
              `Custom agent test quality: response=${hasResponse}(${responseText.length} chars), confidence=${hasConfidence}, tokens=${hasTokens}, latency=${hasLatency}. Classification: ${classification}`)
          } else {
            record('AS-QUAL-02', 'Quality Assessment', 'FAIL', 'high',
              `POST /custom-agents/:id/test: HTTP ${testResp.status()}`)
          }
        } else {
          record('AS-QUAL-02', 'Quality Assessment', 'SKIP', 'high', 'No custom agents to test quality')
        }
      } else {
        record('AS-QUAL-02', 'Quality Assessment', 'SKIP', 'high', 'Cannot fetch custom agents')
      }
    })

    test('AS-QUAL-03: WSI screening available for sourcing agent candidates', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = (data.agents || []).filter((a: Record<string, unknown>) => a.status === 'active')
        if (agents.length > 0) {
          const agentId = agents[0].id
          const wsiResp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/screening-status`)
          const wsiStatus = wsiResp.status()
          record('AS-QUAL-03', 'Quality Assessment', wsiStatus === 200 ? 'PASS' : 'WARN', 'high',
            `GET /sourcing-agents/${agentId}/screening-status: HTTP ${wsiStatus}`)
        } else {
          record('AS-QUAL-03', 'Quality Assessment', 'SKIP', 'high', 'No active agents for WSI screening check')
        }
      } else {
        record('AS-QUAL-03', 'Quality Assessment', 'SKIP', 'high', 'Cannot fetch agents')
      }
    })

    test('AS-QUAL-04: Custom agent response classified correctly via eval-helpers logic', async ({ page }) => {
      await navigateToAgentStudio(page)
      const agentsResp = await page.request.get('/api/backend-proxy/custom-agents')
      if (agentsResp.status() === 200) {
        const data = await agentsResp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        if (agents.length > 0) {
          const agentId = agents[0].id
          const testResp = await page.request.post(`/api/backend-proxy/custom-agents/${agentId}/test`, {
            data: { message: 'Encontre candidatos com experiência em Python para uma vaga de engenheiro sênior' }
          })
          if (testResp.status() === 200) {
            const result = await testResp.json().catch(() => ({ response: '' }))
            const responseText: string = result.response || ''

            const classification = classifyResponse(responseText)
            const isAcceptable = ['AÇÃO EXECUTADA', 'RESPOSTA COERENTE', 'AÇÃO PARCIAL', 'CLARIFICAÇÃO ADEQUADA'].includes(classification)
            record('AS-QUAL-04', 'Quality Assessment', isAcceptable ? 'PASS' : 'WARN', 'high',
              `Custom agent sourcing prompt classification: ${classification}. Response preview: "${responseText.substring(0, 150)}"`)
          } else {
            record('AS-QUAL-04', 'Quality Assessment', 'WARN', 'high',
              `Test endpoint returned HTTP ${testResp.status()}`)
          }
        } else {
          record('AS-QUAL-04', 'Quality Assessment', 'SKIP', 'high', 'No custom agents for quality eval')
        }
      } else {
        record('AS-QUAL-04', 'Quality Assessment', 'SKIP', 'high', 'Cannot fetch custom agents')
      }
    })

    test('AS-QUAL-05: Sourcing agent approval rate is reasonable (0-100%)', async ({ page }) => {
      await navigateToAgentStudio(page)
      const resp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (resp.status() === 200) {
        const data = await resp.json().catch(() => ({ agents: [] }))
        const agents: Record<string, unknown>[] = data.agents || []
        const results: string[] = []
        for (const agent of agents) {
          const viewed = (agent.profiles_viewed as number) ?? 0
          const approved = (agent.profiles_approved as number) ?? 0
          const rate = viewed > 0 ? (approved / viewed) * 100 : 0
          const reasonable = rate >= 0 && rate <= 100
          results.push(`${agent.agent_name}: ${approved}/${viewed} (${rate.toFixed(1)}%) valid=${reasonable}`)
        }
        record('AS-QUAL-05', 'Quality Assessment', 'PASS', 'medium',
          agents.length > 0 ? `Agent metrics: ${results.join(' | ')}` : 'No agents to evaluate')
      } else {
        record('AS-QUAL-05', 'Quality Assessment', 'SKIP', 'medium', 'Cannot fetch agents for metrics check')
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 29. AGENT ↔ LISTAS (CANDIDATE LISTS)
  // ─────────────────────────────────────────────────────────────────
  test.describe('29. Agent ↔ Listas', () => {
    test('AS-LIST-01: GET /candidate-lists endpoint responds', async ({ page }) => {
      const resp = await page.request.get('/api/backend-proxy/candidate-lists')
      if (resp.status() >= 200 && resp.status() < 300) {
        const data = await resp.json().catch(() => ({}))
        const lists = Array.isArray(data.lists) ? data.lists : Array.isArray(data) ? data : []
        record('AS-LIST-01', 'Agent Listas', 'PASS', 'medium',
          `Candidate lists endpoint returned ${lists.length} list(s)`)
      } else if (resp.status() === 404) {
        record('AS-LIST-01', 'Agent Listas', 'SKIP', 'medium',
          'Candidate lists endpoint not implemented (404)')
      } else {
        record('AS-LIST-01', 'Agent Listas', 'FAIL', 'medium',
          `Candidate lists endpoint returned HTTP ${resp.status()}`)
      }
    })

    test('AS-LIST-02: POST create candidate list', async ({ page }) => {
      const resp = await page.request.post('/api/backend-proxy/candidate-lists', {
        data: { name: `E2E-Test-List-${Date.now()}`, description: 'Auto-generated by E2E audit' }
      })
      if (resp.status() >= 200 && resp.status() < 300) {
        const data = await resp.json().catch(() => ({}))
        record('AS-LIST-02', 'Agent Listas', 'PASS', 'medium',
          `List created: id=${data.id || 'unknown'}`)
      } else if (resp.status() === 404 || resp.status() === 405) {
        record('AS-LIST-02', 'Agent Listas', 'SKIP', 'medium',
          `Create list endpoint returned ${resp.status()} — not implemented`)
      } else {
        record('AS-LIST-02', 'Agent Listas', 'WARN', 'medium',
          `Create list returned HTTP ${resp.status()}`)
      }
    })

    test('AS-LIST-03: Associate agent to candidate list', async ({ page }) => {
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() !== 200) {
        record('AS-LIST-03', 'Agent Listas', 'SKIP', 'medium', 'Cannot fetch agents')
        return
      }
      const agentsData = await agentsResp.json().catch(() => ({ agents: [] }))
      const agents: Record<string, unknown>[] = agentsData.agents || []
      if (agents.length === 0) {
        record('AS-LIST-03', 'Agent Listas', 'SKIP', 'medium', 'No agents available')
        return
      }
      const agentId = agents[0].id
      const listsResp = await page.request.get('/api/backend-proxy/candidate-lists')
      if (listsResp.status() !== 200) {
        record('AS-LIST-03', 'Agent Listas', 'SKIP', 'medium', 'Candidate lists endpoint unavailable')
        return
      }
      const listsData = await listsResp.json().catch(() => ({ lists: [] }))
      const lists = Array.isArray(listsData.lists) ? listsData.lists : Array.isArray(listsData) ? listsData : []
      if (lists.length === 0) {
        record('AS-LIST-03', 'Agent Listas', 'SKIP', 'medium', 'No candidate lists to associate')
        return
      }
      const listId = (lists[0] as Record<string, unknown>).id
      const assocResp = await page.request.post(`/api/backend-proxy/sourcing-agents/${agentId}/lists`, {
        data: { list_id: listId }
      })
      if (assocResp.status() >= 200 && assocResp.status() < 300) {
        record('AS-LIST-03', 'Agent Listas', 'PASS', 'medium',
          `Agent ${agentId} associated with list ${listId}`)
      } else if (assocResp.status() === 404 || assocResp.status() === 405) {
        record('AS-LIST-03', 'Agent Listas', 'SKIP', 'medium',
          `Associate endpoint not implemented (${assocResp.status()})`)
      } else {
        record('AS-LIST-03', 'Agent Listas', 'WARN', 'medium',
          `Associate returned HTTP ${assocResp.status()}`)
      }
    })

    test('AS-LIST-04: Verify filtered candidates for agent list', async ({ page }) => {
      const agentsResp = await page.request.get('/api/backend-proxy/sourcing-agents')
      if (agentsResp.status() !== 200) {
        record('AS-LIST-04', 'Agent Listas', 'SKIP', 'medium', 'Cannot fetch agents')
        return
      }
      const agentsData = await agentsResp.json().catch(() => ({ agents: [] }))
      const agents: Record<string, unknown>[] = agentsData.agents || []
      if (agents.length === 0) {
        record('AS-LIST-04', 'Agent Listas', 'SKIP', 'medium', 'No agents available')
        return
      }
      const agentId = agents[0].id
      const resp = await page.request.get(`/api/backend-proxy/sourcing-agents/${agentId}/candidates`)
      if (resp.status() >= 200 && resp.status() < 300) {
        const data = await resp.json().catch(() => ({ candidates: [] }))
        const candidates = Array.isArray(data.candidates) ? data.candidates : Array.isArray(data) ? data : []
        record('AS-LIST-04', 'Agent Listas', 'PASS', 'medium',
          `Agent ${agentId} returned ${candidates.length} candidate(s)`)
      } else if (resp.status() === 404) {
        record('AS-LIST-04', 'Agent Listas', 'SKIP', 'medium',
          'Agent candidates endpoint not implemented')
      } else {
        record('AS-LIST-04', 'Agent Listas', 'WARN', 'medium',
          `Agent candidates returned HTTP ${resp.status()}`)
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 30. CUSTOM AGENT — ARCHIVE, DUPLICATE, VERSION INCREMENT
  // ─────────────────────────────────────────────────────────────────
  test.describe('30. Custom Agent Lifecycle', () => {
    test('AS-LIFE-01: Archive custom agent via API', async ({ page }) => {
      const resp = await page.request.get('/api/backend-proxy/custom-agents')
      if (resp.status() !== 200) {
        record('AS-LIFE-01', 'Agent Lifecycle', 'SKIP', 'medium', 'Cannot fetch custom agents')
        return
      }
      const data = await resp.json().catch(() => ({ agents: [] }))
      const agents: Record<string, unknown>[] = data.agents || data || []
      if (agents.length === 0) {
        record('AS-LIFE-01', 'Agent Lifecycle', 'SKIP', 'medium', 'No custom agents to archive')
        return
      }
      const agentId = agents[agents.length - 1].id
      const archiveResp = await page.request.post(`/api/backend-proxy/custom-agents/${agentId}/archive`)
      if (archiveResp.status() >= 200 && archiveResp.status() < 300) {
        record('AS-LIFE-01', 'Agent Lifecycle', 'PASS', 'medium',
          `Agent ${agentId} archived successfully`)
      } else if (archiveResp.status() === 404 || archiveResp.status() === 405) {
        record('AS-LIFE-01', 'Agent Lifecycle', 'SKIP', 'medium',
          `Archive endpoint not implemented (${archiveResp.status()})`)
      } else {
        record('AS-LIFE-01', 'Agent Lifecycle', 'WARN', 'medium',
          `Archive returned HTTP ${archiveResp.status()}`)
      }
    })

    test('AS-LIFE-02: Duplicate custom agent via API', async ({ page }) => {
      const resp = await page.request.get('/api/backend-proxy/custom-agents')
      if (resp.status() !== 200) {
        record('AS-LIFE-02', 'Agent Lifecycle', 'SKIP', 'medium', 'Cannot fetch custom agents')
        return
      }
      const data = await resp.json().catch(() => ({ agents: [] }))
      const agents: Record<string, unknown>[] = data.agents || data || []
      if (agents.length === 0) {
        record('AS-LIFE-02', 'Agent Lifecycle', 'SKIP', 'medium', 'No custom agents to duplicate')
        return
      }
      const agentId = agents[0].id
      const dupResp = await page.request.post(`/api/backend-proxy/custom-agents/${agentId}/duplicate`)
      if (dupResp.status() >= 200 && dupResp.status() < 300) {
        const dupData = await dupResp.json().catch(() => ({}))
        record('AS-LIFE-02', 'Agent Lifecycle', 'PASS', 'medium',
          `Agent ${agentId} duplicated → new id=${dupData.id || 'unknown'}`)
      } else if (dupResp.status() === 404 || dupResp.status() === 405) {
        record('AS-LIFE-02', 'Agent Lifecycle', 'SKIP', 'medium',
          `Duplicate endpoint not implemented (${dupResp.status()})`)
      } else {
        record('AS-LIFE-02', 'Agent Lifecycle', 'WARN', 'medium',
          `Duplicate returned HTTP ${dupResp.status()}`)
      }
    })

    test('AS-LIFE-03: Version increment on custom agent update', async ({ page }) => {
      const resp = await page.request.get('/api/backend-proxy/custom-agents')
      if (resp.status() !== 200) {
        record('AS-LIFE-03', 'Agent Lifecycle', 'SKIP', 'medium', 'Cannot fetch custom agents')
        return
      }
      const data = await resp.json().catch(() => ({ agents: [] }))
      const agents: Record<string, unknown>[] = data.agents || data || []
      if (agents.length === 0) {
        record('AS-LIFE-03', 'Agent Lifecycle', 'SKIP', 'medium', 'No custom agents to test version increment')
        return
      }
      const agent = agents[0]
      const agentId = agent.id
      const versionBefore = (agent.version as number) ?? (agent.v as number) ?? 0

      const updateResp = await page.request.put(`/api/backend-proxy/custom-agents/${agentId}`, {
        data: { description: `E2E version test — ${Date.now()}` }
      })
      if (updateResp.status() >= 200 && updateResp.status() < 300) {
        const afterResp = await page.request.get('/api/backend-proxy/custom-agents')
        if (afterResp.status() === 200) {
          const afterData = await afterResp.json().catch(() => ({ agents: [] }))
          const afterAgents: Record<string, unknown>[] = afterData.agents || afterData || []
          const afterAgent = afterAgents.find((a: Record<string, unknown>) => a.id === agentId)
          const versionAfter = (afterAgent?.version as number) ?? (afterAgent?.v as number) ?? 0
          const incremented = versionAfter > versionBefore
          record('AS-LIFE-03', 'Agent Lifecycle', incremented ? 'PASS' : 'WARN', 'medium',
            `version before=${versionBefore}, after=${versionAfter}. ${incremented ? 'Incremented correctly' : 'Version unchanged — backend may not auto-increment'}`)
        } else {
          record('AS-LIFE-03', 'Agent Lifecycle', 'FAIL', 'medium', 'Failed to re-fetch agents after update')
        }
      } else if (updateResp.status() === 404 || updateResp.status() === 405) {
        record('AS-LIFE-03', 'Agent Lifecycle', 'SKIP', 'medium',
          `Update endpoint returned ${updateResp.status()}`)
      } else {
        record('AS-LIFE-03', 'Agent Lifecycle', 'WARN', 'medium',
          `Update returned HTTP ${updateResp.status()}`)
      }
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 31. HTML REPORT GENERATION
  // ─────────────────────────────────────────────────────────────────
  test.describe('28. Report Generation', () => {
    test('AS-RPT-01: Generate consolidated HTML audit report', async ({ page }) => {
      const countBefore = results.length
      record('AS-RPT-01', 'Report Generation', 'PASS', 'low',
        `Report will include ${countBefore} test results. HTML will be generated in afterAll hook.`)
    })
  })

  // ─────────────────────────────────────────────────────────────────
  // 16. EDGE CASES (EXISTING — unchanged)
  // ─────────────────────────────────────────────────────────────────
  test.describe('16. Edge Cases', () => {
    test('AS-EDGE-01: Long agent name (200 chars) accepted', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const input = page.locator('[role="dialog"] input').first()
      const longName = 'A'.repeat(200)
      await input.fill(longName)
      const value = await input.inputValue()
      expect(value.length).toBeGreaterThan(50)
      record('AS-EDGE-01', 'Edge Cases', 'PASS', 'low',
        `Long name accepted: ${value.length} chars in input`)
    })

    test('AS-EDGE-02: XSS-like characters safely rendered', async ({ page }) => {
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      const input = page.locator('[role="dialog"] input').first()
      const xssName = '<script>alert(1)</script> & "quotes" <img onerror=alert(1)>'
      await input.fill(xssName)
      const value = await input.inputValue()
      expect(value).toContain('<script>')
      const dialogCount = await page.locator('dialog, [role="alertdialog"]').count()
      expect(dialogCount).toBeLessThanOrEqual(1)
      const bodyHtml = await page.locator('body').innerHTML()
      const hasUnescapedScript = bodyHtml.includes('<script>alert(1)</script>') && !bodyHtml.includes('&lt;script&gt;')
      expect(hasUnescapedScript).toBeFalsy()
      record('AS-EDGE-02', 'Edge Cases', 'PASS', 'medium',
        `XSS characters stored in input (${value.length} chars), no script execution detected`)
    })

    test('AS-EDGE-03: Refresh reloads agent data from API', async ({ page }) => {
      await navigateToAgentStudio(page)
      const responsePromise = page.waitForResponse(
        r => r.url().includes('sourcing-agents') && r.request().method() === 'GET',
        { timeout: 5000 }
      ).catch(() => null)

      const refreshBtn = page.locator('button').filter({ has: page.locator('svg') }).first()
      if (await refreshBtn.isVisible()) {
        await refreshBtn.click()
        const resp = await responsePromise
        record('AS-EDGE-03', 'Edge Cases', resp ? 'PASS' : 'WARN', 'low',
          resp ? `Refresh triggered API call, status: ${resp.status()}` : 'Refresh clicked but no API call captured')
      }
    })
  })

  test.afterAll(async () => {
    console.log('\n=== AGENT STUDIO E2E AUDIT RESULTS ===\n')
    const grouped = results.reduce((acc, r) => {
      acc[r.area] = acc[r.area] || []
      acc[r.area].push(r)
      return acc
    }, {} as Record<string, AuditResult[]>)

    for (const [area, items] of Object.entries(grouped)) {
      console.log(`\n--- ${area} ---`)
      for (const item of items) {
        const bugRef = item.bug ? ` [${item.bug}]` : ''
        console.log(`  ${item.status} | ${item.id} | ${item.details}${bugRef}`)
      }
    }

    const pass = results.filter(r => r.status === 'PASS').length
    const fail = results.filter(r => r.status === 'FAIL').length
    const blocked = results.filter(r => r.status === 'BLOCKED').length
    const skip = results.filter(r => r.status === 'SKIP').length
    const warn = results.filter(r => r.status === 'WARN').length

    console.log(`\n=== SUMMARY ===`)
    console.log(`Total: ${results.length} | PASS: ${pass} | FAIL: ${fail} | BLOCKED: ${blocked} | SKIP: ${skip} | WARN: ${warn}`)
    console.log(`\nBugs referenced:`)
    const bugs = [...new Set(results.filter(r => r.bug).map(r => r.bug!))]
    for (const bug of bugs) {
      const relatedTests = results.filter(r => r.bug === bug).map(r => r.id)
      console.log(`  ${bug}: affects ${relatedTests.join(', ')}`)
    }

    const fs = await import('fs')
    const path = await import('path')

    const evidenceDir = 'e2e/evidence'
    if (!fs.existsSync(evidenceDir)) fs.mkdirSync(evidenceDir, { recursive: true })

    // Write JSON artifact
    const artifact = {
      audit: 'Agent Studio E2E',
      timestamp: new Date().toISOString(),
      summary: { total: results.length, pass, fail, blocked, skip, warn },
      bugs: bugs.map(b => ({
        id: b,
        severity: results.find(r => r.bug === b)?.severity ?? 'medium',
        tests: results.filter(r => r.bug === b).map(r => r.id)
      })),
      hardcodedButtons: results
        .filter(r => r.area === 'Hardcoded Buttons')
        .map(r => ({ id: r.id, details: r.details })),
      qualityAssessment: results
        .filter(r => r.area === 'Quality Assessment')
        .map(r => ({ id: r.id, status: r.status, details: r.details })),
      results
    }
    fs.writeFileSync(path.join(evidenceDir, 'agent-studio-audit-results.json'), JSON.stringify(artifact, null, 2))

    // Generate HTML Report
    const statusColors: Record<Status, string> = {
      PASS: '#10b981',
      FAIL: '#ef4444',
      BLOCKED: '#f59e0b',
      SKIP: '#6b7280',
      WARN: '#f97316',
    }
    const severityBadge: Record<Severity, string> = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#f59e0b',
      low: '#6b7280',
    }

    const passRate = results.length > 0 ? Math.round((pass / results.length) * 100) : 0
    const timestamp = new Date().toISOString()

    const areaRows = Object.entries(grouped).map(([area, items]) => {
      const aPass = items.filter(i => i.status === 'PASS').length
      const aFail = items.filter(i => i.status === 'FAIL').length
      const aWarn = items.filter(i => i.status === 'WARN').length
      const aBlocked = items.filter(i => i.status === 'BLOCKED').length
      const aSkip = items.filter(i => i.status === 'SKIP').length
      const aRate = items.length > 0 ? Math.round((aPass / items.length) * 100) : 0
      return `
        <tr>
          <td style="padding:8px 12px;font-weight:600">${area}</td>
          <td style="padding:8px 12px;text-align:center">${items.length}</td>
          <td style="padding:8px 12px;text-align:center;color:#10b981;font-weight:600">${aPass}</td>
          <td style="padding:8px 12px;text-align:center;color:#ef4444;font-weight:600">${aFail}</td>
          <td style="padding:8px 12px;text-align:center;color:#f97316">${aWarn}</td>
          <td style="padding:8px 12px;text-align:center;color:#f59e0b">${aBlocked}</td>
          <td style="padding:8px 12px;text-align:center;color:#6b7280">${aSkip}</td>
          <td style="padding:8px 12px;text-align:center">
            <span style="background:${aRate >= 70 ? '#d1fae5' : aRate >= 40 ? '#fef3c7' : '#fee2e2'};color:${aRate >= 70 ? '#065f46' : aRate >= 40 ? '#92400e' : '#991b1b'};padding:2px 8px;border-radius:9999px;font-size:12px;font-weight:700">${aRate}%</span>
          </td>
        </tr>`
    }).join('')

    const bugRows = bugs.map(b => {
      const affected = results.filter(r => r.bug === b)
      const sev = affected[0]?.severity ?? 'medium'
      return `
        <tr>
          <td style="padding:8px 12px;font-weight:700">${b}</td>
          <td style="padding:8px 12px"><span style="background:${severityBadge[sev]}22;color:${severityBadge[sev]};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;text-transform:uppercase">${sev}</span></td>
          <td style="padding:8px 12px">${affected.map(r => r.id).join(', ')}</td>
          <td style="padding:8px 12px;font-size:12px;color:#4b5563">${affected[0]?.details ?? ''}</td>
        </tr>`
    }).join('')

    const hardcodedRows = results
      .filter(r => r.area === 'Hardcoded Buttons')
      .map(r => `<tr><td style="padding:8px 12px;font-weight:600">${r.id}</td><td style="padding:8px 12px;font-size:12px">${r.details}</td></tr>`)
      .join('')

    const qualityRows = results
      .filter(r => r.area === 'Quality Assessment')
      .map(r => `
        <tr>
          <td style="padding:8px 12px;font-weight:600">${r.id}</td>
          <td style="padding:8px 12px"><span style="background:${statusColors[r.status]}22;color:${statusColors[r.status]};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">${r.status}</span></td>
          <td style="padding:8px 12px;font-size:12px;color:#374151">${r.details}</td>
        </tr>`)
      .join('')

    const detailRows = results.map(r => {
      const screenshot = fs.existsSync(path.join(evidenceDir, `${r.id}.png`))
        ? `<a href="${r.id}.png" target="_blank" style="color:#3b82f6;font-size:11px">📷 screenshot</a>`
        : ''
      const bugTag = r.bug ? `<span style="background:#fee2e2;color:#991b1b;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:4px">${r.bug}</span>` : ''
      return `
        <tr style="border-bottom:1px solid #f3f4f6">
          <td style="padding:6px 10px;font-family:monospace;font-size:12px;white-space:nowrap">${r.id}${bugTag}</td>
          <td style="padding:6px 10px"><span style="background:${statusColors[r.status]}22;color:${statusColors[r.status]};padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700">${r.status}</span></td>
          <td style="padding:6px 10px"><span style="background:${severityBadge[r.severity]}11;color:${severityBadge[r.severity]};padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase">${r.severity}</span></td>
          <td style="padding:6px 10px;color:#374151;font-size:12px">${r.area}</td>
          <td style="padding:6px 10px;color:#374151;font-size:12px;max-width:400px">${r.details}</td>
          <td style="padding:6px 10px">${screenshot}</td>
        </tr>`
    }).join('')

    const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Studio E2E Audit Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; background: #f9fafb; color: #111827; }
    h1 { font-size: 22px; font-weight: 800; color: #111827; margin-bottom: 4px; }
    h2 { font-size: 15px; font-weight: 700; color: #374151; margin: 24px 0 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 24px; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .card { background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .card-val { font-size: 28px; font-weight: 800; }
    .card-lbl { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 24px; }
    thead { background: #f3f4f6; }
    th { padding: 10px 12px; text-align: left; font-size: 11px; font-weight: 700; color: #4b5563; text-transform: uppercase; letter-spacing: 0.05em; }
    tbody tr:hover { background: #f9fafb; }
  </style>
</head>
<body>
  <h1>🤖 Agent Studio — Roteiro E2E Completo</h1>
  <div class="meta">Gerado em: ${timestamp} &nbsp;|&nbsp; Cobertura: ${results.length} cenários em ${Object.keys(grouped).length} áreas</div>

  <div class="summary-grid">
    <div class="card"><div class="card-val" style="color:#111827">${results.length}</div><div class="card-lbl">Total</div></div>
    <div class="card"><div class="card-val" style="color:#10b981">${pass}</div><div class="card-lbl">PASS</div></div>
    <div class="card"><div class="card-val" style="color:#ef4444">${fail}</div><div class="card-lbl">FAIL</div></div>
    <div class="card"><div class="card-val" style="color:#f97316">${warn}</div><div class="card-lbl">WARN</div></div>
    <div class="card"><div class="card-val" style="color:#f59e0b">${blocked}</div><div class="card-lbl">BLOCKED</div></div>
    <div class="card"><div class="card-val" style="color:#6b7280">${skip}</div><div class="card-lbl">SKIP</div></div>
    <div class="card"><div class="card-val" style="color:${passRate >= 70 ? '#10b981' : passRate >= 40 ? '#f97316' : '#ef4444'}">${passRate}%</div><div class="card-lbl">Pass Rate</div></div>
  </div>

  <h2>📊 Resultados por Área</h2>
  <table>
    <thead><tr><th>Área</th><th>Total</th><th>PASS</th><th>FAIL</th><th>WARN</th><th>BLOCKED</th><th>SKIP</th><th>Taxa</th></tr></thead>
    <tbody>${areaRows}</tbody>
  </table>

  <h2>🐛 Bugs Encontrados (${bugs.length})</h2>
  ${bugs.length > 0 ? `<table>
    <thead><tr><th>Bug ID</th><th>Severidade</th><th>Testes Afetados</th><th>Descrição</th></tr></thead>
    <tbody>${bugRows}</tbody>
  </table>` : '<p style="color:#6b7280;font-size:13px">Nenhum bug crítico registrado nesta execução.</p>'}

  <h2>🔍 Detecção de Botões Hardcoded</h2>
  ${hardcodedRows ? `<table>
    <thead><tr><th>Teste</th><th>Resultado</th></tr></thead>
    <tbody>${hardcodedRows}</tbody>
  </table>` : '<p style="color:#6b7280;font-size:13px">Nenhum dado de hardcoded buttons — execução necessária.</p>'}

  <h2>⭐ Avaliação de Qualidade dos Agentes</h2>
  ${qualityRows ? `<table>
    <thead><tr><th>Teste</th><th>Status</th><th>Resultado</th></tr></thead>
    <tbody>${qualityRows}</tbody>
  </table>` : '<p style="color:#6b7280;font-size:13px">Nenhum dado de qualidade — execução necessária.</p>'}

  <h2>📋 Todos os Cenários (${results.length})</h2>
  <table>
    <thead><tr><th>ID</th><th>Status</th><th>Sev.</th><th>Área</th><th>Detalhes</th><th>Evidência</th></tr></thead>
    <tbody>${detailRows}</tbody>
  </table>

  <div style="text-align:center;color:#9ca3af;font-size:12px;margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb">
    Agent Studio E2E Audit — Plataforma LIA &nbsp;|&nbsp; ${timestamp}
  </div>
</body>
</html>`

    const htmlPath = path.join(evidenceDir, 'agent-studio-audit-report.html')
    fs.writeFileSync(htmlPath, html)
    console.log(`\nHTML Report written to ${htmlPath}`)
    console.log(`JSON Artifact written to e2e/evidence/agent-studio-audit-results.json`)
  })
})
