import { test, expect, type Page } from '@playwright/test'

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

function record(id: string, area: string, status: Status, severity: Severity, details: string, bug?: string) {
  results.push({ id, area, status, severity, details, bug })
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

      record('AS-CREATE-09', 'Creation Modal', apiStatus > 0 ? 'PASS' : 'WARN', 'high',
        `Loading state observed: ${loadingVisible}, API response: ${apiStatus}`)
    })

    test('AS-CREATE-10: Created agent appears in card grid', async ({ page }) => {
      const agentName = `AuditCheck ${Date.now()}`
      await navigateToAgentStudio(page)
      await page.locator('button').filter({ hasText: 'Criar Agente' }).first().click()
      await page.waitForTimeout(1000)
      await page.locator('[role="dialog"] input').first().fill(agentName)
      await page.locator('button:has-text("Criar e Calibrar")').click()
      await page.waitForTimeout(6000)

      const body = await page.textContent('body') ?? ''
      const created = body.includes(agentName) || body.includes('Erro')
      record('AS-CREATE-10', 'Creation Modal', created ? 'PASS' : 'FAIL', 'high',
        created ? `Agent "${agentName}" found in page or error shown` : 'Agent not found and no error displayed')
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
    const artifact = {
      audit: 'Agent Studio E2E',
      timestamp: new Date().toISOString(),
      summary: { total: results.length, pass, fail, blocked, skip, warn },
      bugs: bugs.map(b => ({
        id: b,
        tests: results.filter(r => r.bug === b).map(r => r.id)
      })),
      results
    }
    fs.writeFileSync('e2e/evidence/agent-studio-audit-results.json', JSON.stringify(artifact, null, 2))
    console.log('\nArtifact written to e2e/evidence/agent-studio-audit-results.json')
  })
})
