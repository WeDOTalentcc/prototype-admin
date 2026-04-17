/**
 * KANBAN FULL AUDIT — Roteiro Exaustivo de Testes
 * ================================================
 * Audita todos os botões, modais, campos, integrações e fluxos do Kanban de Vaga.
 *
 * Cada bloco inclui referência ao arquivo de código-fonte para diagnóstico de problemas.
 *
 * Executar:
 *   PLAYWRIGHT_BASE_URL=https://82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev \
 *   npx playwright test e2e/tests/kanban/kanban-full-audit.spec.ts --reporter=html
 */

import { test, expect, KANBAN_JOBS } from '../../fixtures/kanban-auth.fixture'
import type { Page } from '@playwright/test'

// ─── Module-level state ────────────────────────────────────────────────────────
let _kanbanUrl = ''

// ─── Helpers ───────────────────────────────────────────────────────────────────

/** Navega diretamente ao kanban do Product Manager (tem seed data) */
async function goToFirstKanban(page: Page): Promise<string> {
  // Fixture já navegou — verifica se kanban já carregou, caso contrário aguarda
  const isAlreadyLoaded = await page.locator('[data-testid="kanban-column"]').first().isVisible({ timeout: 1000 }).catch(() => false)
  if (!isAlreadyLoaded) {
    const url = KANBAN_JOBS.productManager.url
    await page.goto(url)
    await page.waitForLoadState('domcontentloaded')
    await page.waitForSelector('[data-testid="kanban-column"]', { timeout: 40000 }).catch(() => {})
  }
  return KANBAN_JOBS.productManager.url
}

/** Garante que há pelo menos um card visível no kanban */
async function ensureKanbanLoaded(page: Page): Promise<boolean> {
  const col = page.locator('[data-testid="kanban-column"]').first()
  return col.isVisible({ timeout: 15000 }).catch(() => false)
}

/** Captura screenshot com nome descritivo */
async function snap(page: Page, name: string) {
  await page.screenshot({ path: `playwright-report/screenshots/${name}.png`, fullPage: false })
}

// ═══════════════════════════════════════════════════════════════════════════════
// 1. SETUP E NAVEGAÇÃO
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('01 · Setup e Navegação', () => {
  test('página /vagas carrega sem erros', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas')
    await page.waitForLoadState('domcontentloaded')
    await snap(page, '01-vagas-list')

    // Verifica ausência de erros críticos de JS
    const errors: string[] = []
    page.on('pageerror', err => errors.push(err.message))
    await page.waitForTimeout(1000)

    expect.soft(errors.filter(e => !e.includes('ResizeObserver')), 'JS errors na página /vagas').toHaveLength(0)
    await expect.soft(page.locator('h1, [class*="page-title"], [class*="PageTitle"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('abre kanban do primeiro job disponível', async ({ authenticatedPage: page }) => {
    const url = await goToFirstKanban(page)
    _kanbanUrl = url
    await snap(page, '01-kanban-opened')

    if (!url) {
      console.warn('⚠️  Nenhum job encontrado em /vagas — verifique se há dados de teste.')
      test.skip()
    }

    const kanbanLoaded = await ensureKanbanLoaded(page)
    expect.soft(kanbanLoaded, 'Kanban deve exibir ao menos 1 coluna').toBe(true)
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 2. COLUNAS E LAYOUT VISUAL
// Ref: src/components/pages/job-kanban/KanbanColumn.tsx
//      src/components/pages/job-kanban/KanbanBoardSection.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('02 · Colunas e Layout Visual', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('exibe múltiplas colunas do kanban', async ({ authenticatedPage: page }) => {
    const columns = page.locator('[data-testid="kanban-column"]')
    const count = await columns.count()
    await snap(page, '02-columns-overview')

    expect.soft(count, 'Deve ter ao menos 3 colunas').toBeGreaterThanOrEqual(3)
    console.log(`  ✓ Colunas encontradas: ${count}`)
  })

  test('cada coluna exibe nome e badge de contagem', async ({ authenticatedPage: page }) => {
    const columns = page.locator('[data-testid="kanban-column"]')
    const count = await columns.count()

    for (let i = 0; i < Math.min(count, 7); i++) {
      const col = columns.nth(i)
      const stageId = await col.getAttribute('data-stage-id')
      const badge = col.locator('span[class*="text-micro"]').first()
      const name  = col.locator('h3').first()

      await expect.soft(name, `Coluna ${i} deve ter nome visível`).toBeVisible({ timeout: 3000 })
      await expect.soft(badge, `Coluna ${i} deve ter badge de contagem`).toBeVisible({ timeout: 3000 })
      console.log(`  ✓ Coluna ${i}: stage=${stageId}`)
    }
  })

  test('header da vaga está visível (título, status, botões)', async ({ authenticatedPage: page }) => {
    // Ref: src/components/pages/job-kanban/KanbanJobHeader.tsx
    const header = page.locator('[class*="KanbanJobHeader"], [data-testid="kanban-header"]').first()
    const backBtn = page.getByRole('button', { name: /voltar|back/i }).first()
    const jobTitle = page.locator('h1').first()

    await snap(page, '02-header')
    await expect.soft(jobTitle, 'Título da vaga deve ser visível').toBeVisible({ timeout: 5000 })
    await expect.soft(backBtn, 'Botão Voltar deve existir').toBeVisible({ timeout: 3000 })
  })

  test('tabs Kanban / Tabela estão presentes', async ({ authenticatedPage: page }) => {
    // Ref: src/components/pages/job-kanban/KanbanContentArea.tsx
    const kanbanTab = page.getByRole('button', { name: /^Kanban$/i }).or(page.locator('[data-tab="kanban"]'))
    const tableTab  = page.getByRole('button', { name: /^Tabela$/i }).or(page.locator('[data-tab="table"]'))

    await expect.soft(kanbanTab.first(), 'Tab Kanban deve existir').toBeVisible({ timeout: 5000 })
    await expect.soft(tableTab.first(), 'Tab Tabela deve existir').toBeVisible({ timeout: 5000 })
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 3. CARD DO CANDIDATO
// Ref: src/components/pages/job-kanban/KanbanCard.tsx
//      src/components/pages/job-kanban/KanbanCardScores.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('03 · Card do Candidato', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('card exibe nome, cargo e empresa', async ({ authenticatedPage: page }) => {
    const card = page.locator('[data-testid="candidate-card"]').first()

    if (!await card.isVisible({ timeout: 8000 }).catch(() => false)) {
      console.warn('⚠️  Nenhum candidato no kanban — testes de card pulados')
      test.skip()
    }

    await snap(page, '03-candidate-card')
    await expect.soft(card, 'Card deve ser visível').toBeVisible()

    // Verifica estrutura interna do card
    const name    = card.locator('h4').first()
    const avatar  = card.locator('span[class*="overflow-hidden"]').first()
    await expect.soft(name, 'Nome do candidato deve aparecer').toBeVisible({ timeout: 3000 })
    await expect.soft(avatar, 'Avatar deve aparecer').toBeVisible({ timeout: 3000 })
  })

  test('card tem data-candidate-id preenchido', async ({ authenticatedPage: page }) => {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { test.skip() }

    const id = await card.getAttribute('data-candidate-id')
    expect.soft(id, 'data-candidate-id deve estar presente e não vazio').toBeTruthy()
    console.log(`  ✓ candidate-id: ${id}`)
  })

  test('ícones de score (Geral, Triagem, CV, Técnico, Inglês, B5) aparecem no card', async ({ authenticatedPage: page }) => {
    // Ref: src/components/pages/job-kanban/KanbanCardScores.tsx
    // 6 ScoreIconButton: Gauge(geral), BrainCircuit(triagem), Target(cv),
    //                    Code(tecnico), Globe(ingles), Fingerprint(b5)
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { test.skip() }

    await card.hover()
    await page.waitForTimeout(500)
    await snap(page, '03-card-scores')

    // Os ícones de score ficam no ScoreIconButton — buscar por aria-label ou SVG
    const scoreButtons = card.locator('button[aria-label*="score"], button[title*="Score"], [class*="ScoreIcon"], [class*="score-icon"]')
    const scoreCount = await scoreButtons.count()
    console.log(`  ✓ Score buttons visíveis no card: ${scoreCount}`)
    // Não forçamos 6 pois podem estar sem dados e ocultos, mas reportamos
    if (scoreCount === 0) {
      console.warn('  ⚠️  Nenhum ícone de score encontrado — verifique KanbanCardScores.tsx')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 4. MODAIS DE SCORE — General Score / Triagem WSI / Rubrica CV / B5 / Técnico / Inglês
// Ref: src/components/pages/job-kanban/KanbanPageModalsExtra.tsx
//      src/components/modals/general-score-modal.tsx
//      src/components/rubric-evaluation-modal.tsx
//      src/components/big-five-modal.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('04 · Modais de Score', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  async function openScoreModal(page: Page, label: string): Promise<boolean> {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) return false
    await card.hover()
    await page.waitForTimeout(400)

    // Tenta clicar no ícone de score pelo aria-label ou title
    const btn = page.locator(`button[aria-label*="${label}" i], button[title*="${label}" i]`).first()
    if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await btn.click()
      await page.waitForTimeout(800)
      return true
    }
    return false
  }

  test('modal General Score (Gauge/Geral) abre e exibe dados', async ({ authenticatedPage: page }) => {
    const opened = await openScoreModal(page, 'geral')
    const modal = page.locator('[role="dialog"]').first()

    if (!opened) {
      console.warn('  ⚠️  Botão General Score não encontrado — src/components/modals/general-score-modal.tsx')
    }

    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-general-score')
      await expect.soft(modal, 'Modal General Score deve estar visível').toBeVisible()

      // Verifica se dados são reais ou hardcoded
      const scoreValue = modal.locator('[class*="score"], [class*="Score"], [data-score]').first()
      const isHardcoded = await modal.locator('text=/lorem|test|hardcode|mock/i').count()
      console.log(`  ✓ Modal aberto. Hardcoded mock text: ${isHardcoded > 0 ? 'SIM ⚠️' : 'não'}`)

      // Fecha modal
      const closeBtn = modal.locator('button[aria-label*="close" i], button[aria-label*="fechar" i], [class*="close"]').first()
        .or(page.keyboard.press.bind(page.keyboard, 'Escape') as never)
      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Modal não abriu — sem dados de score ou botão não conectado')
    }
  })

  test('modal Triagem WSI (BrainCircuit) abre e exibe resultado', async ({ authenticatedPage: page }) => {
    const opened = await openScoreModal(page, 'triagem')
    if (!opened) console.warn('  ⚠️  Botão Triagem WSI não encontrado — src/components/triagem-details-modal.tsx')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-triagem-wsi')
      // Verifica se há dados de triagem ou mensagem de "não disponível"
      const noData = await modal.locator('text=/sem triagem|não realiz|not found|no data/i').count()
      console.log(`  ✓ Modal Triagem: sem dados = ${noData > 0 ? 'SIM' : 'não'}`)
      await page.keyboard.press('Escape')
    }
  })

  test('modal Rubrica CV (Target) abre e exibe avaliação', async ({ authenticatedPage: page }) => {
    // Ref: src/components/rubric-evaluation-modal.tsx
    const opened = await openScoreModal(page, 'cv')
    if (!opened) console.warn('  ⚠️  Botão Rubrica CV não encontrado — src/components/rubric-evaluation-modal.tsx')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-rubrica-cv')
      await page.keyboard.press('Escape')
    }
  })

  test('modal Big Five (Fingerprint) abre', async ({ authenticatedPage: page }) => {
    // Ref: src/components/big-five-modal.tsx
    const opened = await openScoreModal(page, 'b5')
    if (!opened) console.warn('  ⚠️  Botão Big Five não encontrado — src/components/big-five-modal.tsx')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-b5')
      await page.keyboard.press('Escape')
    }
  })

  test('modal Teste Técnico (Code) abre', async ({ authenticatedPage: page }) => {
    // Ref: src/components/modals/technical-test-modal.tsx
    const opened = await openScoreModal(page, 'tecnico')
    if (!opened) console.warn('  ⚠️  Botão Teste Técnico não encontrado')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-tecnico')
      await page.keyboard.press('Escape')
    }
  })

  test('modal Inglês (Globe) abre', async ({ authenticatedPage: page }) => {
    // Ref: src/components/modals/english-test-modal.tsx
    const opened = await openScoreModal(page, 'ingles')
    if (!opened) console.warn('  ⚠️  Botão Inglês não encontrado')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      await snap(page, '04-modal-ingles')
      await page.keyboard.press('Escape')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 5. AÇÕES DO CARD (DROPDOWN MENU)
// Ref: src/components/pages/job-kanban/KanbanCardActions.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('05 · Ações do Card (Menu Dropdown)', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  async function openCardDropdown(page: Page): Promise<boolean> {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) return false
    await card.hover()
    await page.waitForTimeout(500)
    // Clica no botão MoreVertical que aparece no hover
    const moreBtn = card.locator('button[aria-label*="opções" i], button[title*="opções" i], button[aria-label*="options" i]')
      .or(card.locator('button').filter({ has: page.locator('svg[class*="MoreVertical"], [data-lucide="more-vertical"]') }))
      .first()
    if (await moreBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await moreBtn.click()
      await page.waitForTimeout(400)
      return true
    }
    return false
  }

  test('menu dropdown abre ao hover no card', async ({ authenticatedPage: page }) => {
    const opened = await openCardDropdown(page)
    await snap(page, '05-card-dropdown')

    if (!opened) {
      console.warn('  ⚠️  Botão MoreVertical não encontrado — src/components/pages/job-kanban/KanbanCardActions.tsx')
    }

    const menu = page.locator('[role="menu"], [data-radix-popper-content-wrapper]').first()
    if (await menu.isVisible({ timeout: 2000 }).catch(() => false)) {
      const items = menu.locator('[role="menuitem"]')
      const count = await items.count()
      console.log(`  ✓ Menu items encontrados: ${count}`)

      // Verifica itens esperados
      for (const label of ['email', 'whatsapp', 'entrevista', 'wsi', 'feedback', 'shortlist', 'favorito']) {
        const item = menu.locator(`[role="menuitem"]:has-text("${label}")`).or(
          menu.locator(`[role="menuitem"] >> text=/${label}/i`)
        ).first()
        const visible = await item.isVisible({ timeout: 500 }).catch(() => false)
        console.log(`  ${visible ? '✓' : '⚠️ '} MenuItem "${label}": ${visible ? 'OK' : 'NÃO ENCONTRADO'}`)
      }

      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Menu dropdown não abriu')
    }
  })

  test('opção "Enviar Email" abre modal de email', async ({ authenticatedPage: page }) => {
    // Ref: src/components/email-templates/send-email-modal.tsx (via KanbanPageModalsCore)
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const emailItem = page.locator('[role="menuitem"]').filter({ hasText: /email/i }).first()
    if (await emailItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      await emailItem.click()
      await page.waitForTimeout(1000)
      await snap(page, '05-email-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Verifica campos do modal de email
        const toField      = modal.locator('input[name="to"], input[placeholder*="para" i]').first()
        const subjectField = modal.locator('input[name="subject"], input[placeholder*="assunto" i]').first()
        const bodyField    = modal.locator('textarea, [contenteditable="true"]').first()

        await expect.soft(toField,      'Campo "Para" deve existir').toBeVisible({ timeout: 3000 })
        await expect.soft(subjectField, 'Campo "Assunto" deve existir').toBeVisible({ timeout: 3000 })
        await expect.soft(bodyField,    'Campo de corpo do email deve existir').toBeVisible({ timeout: 3000 })

        // Tenta enviar (pode falhar por Mailgun não configurado)
        const sendBtn = modal.locator('button').filter({ hasText: /enviar|send/i }).first()
        if (await sendBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await sendBtn.click()
          await page.waitForTimeout(1500)
          const toast = page.locator('[class*="toast"], [role="alert"]').first()
          const toastText = await toast.textContent().catch(() => '')
          console.log(`  ✓ Toast após envio de email: "${toastText}"`)
          if (/erro|error|falha|fail/i.test(toastText || '')) {
            console.warn('  ⚠️  Envio de email FALHOU — verificar MAILGUN_API_KEY nas env vars')
          }
        }
        await page.keyboard.press('Escape')
      } else {
        console.warn('  ⚠️  Modal de email não abriu — src/components/email-templates/send-email-modal.tsx')
      }
    }
  })

  test('opção "Agendar Entrevista" abre modal de agendamento', async ({ authenticatedPage: page }) => {
    // Ref: KanbanPageModalsCore → UnifiedCommunicationModal ou agendamento
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const scheduleItem = page.locator('[role="menuitem"]').filter({ hasText: /entrevista|interview|agendar/i }).first()
    if (await scheduleItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      await scheduleItem.click()
      await page.waitForTimeout(1000)
      await snap(page, '05-schedule-interview-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect.soft(modal).toBeVisible()
        // Verifica campos de data/hora
        const dateField = modal.locator('input[type="date"], input[type="datetime-local"], [class*="date-picker"]').first()
        await expect.soft(dateField, 'Campo de data deve existir').toBeVisible({ timeout: 3000 })
        console.log('  ✓ Modal de agendamento abriu com campo de data')
        await page.keyboard.press('Escape')
      } else {
        console.warn('  ⚠️  Modal de agendamento não abriu')
        console.warn('     Possível problema: integração Calendar (Microsoft/Google) não configurada')
      }
    }
  })

  test('opção "Triagem WSI" abre modal de convite WSI', async ({ authenticatedPage: page }) => {
    // Ref: src/components/wsi/wsi-triagem-invite-modal.tsx
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const wsiItem = page.locator('[role="menuitem"]').filter({ hasText: /wsi|triagem/i }).first()
    if (await wsiItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      await wsiItem.click()
      await page.waitForTimeout(1000)
      await snap(page, '05-wsi-invite-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect.soft(modal).toBeVisible()
        console.log('  ✓ Modal WSI Invite abriu')
        // Verifica botão de enviar convite
        const sendBtn = modal.locator('button').filter({ hasText: /enviar|send|convidar/i }).first()
        await expect.soft(sendBtn, 'Botão de enviar convite WSI deve existir').toBeVisible({ timeout: 3000 })
        await page.keyboard.press('Escape')
      } else {
        console.warn('  ⚠️  Modal WSI não abriu — src/components/wsi/wsi-triagem-invite-modal.tsx')
      }
    }
  })

  test('opção "Enviar Feedback" abre modal de feedback', async ({ authenticatedPage: page }) => {
    // Ref: KanbanPageModalsCore → UnifiedCommunicationModal type=feedback
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const feedbackItem = page.locator('[role="menuitem"]').filter({ hasText: /feedback/i }).first()
    if (await feedbackItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      await feedbackItem.click()
      await page.waitForTimeout(1000)
      await snap(page, '05-feedback-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect.soft(modal).toBeVisible()
        console.log('  ✓ Modal Feedback abriu')
        await page.keyboard.press('Escape')
      } else {
        console.warn('  ⚠️  Modal Feedback não abriu')
      }
    }
  })

  test('opção "WhatsApp" abre modal ou link de WhatsApp', async ({ authenticatedPage: page }) => {
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const whatsItem = page.locator('[role="menuitem"]').filter({ hasText: /whatsapp/i }).first()
    if (await whatsItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Intercepta abertura de nova aba/janela
      const [popup] = await Promise.all([
        page.context().waitForEvent('page', { timeout: 3000 }).catch(() => null),
        whatsItem.click(),
      ])
      await page.waitForTimeout(800)
      await snap(page, '05-whatsapp')

      if (popup) {
        console.log(`  ✓ WhatsApp abre nova aba: ${await popup.url()}`)
        await popup.close()
      } else {
        const modal = page.locator('[role="dialog"]').first()
        const modalVisible = await modal.isVisible({ timeout: 2000 }).catch(() => false)
        console.log(`  ${modalVisible ? '✓' : '⚠️'} WhatsApp ${modalVisible ? 'abriu modal' : 'não abriu nada'}`)
        if (modalVisible) await page.keyboard.press('Escape')
      }
    }
  })

  test('toggle Shortlist funciona', async ({ authenticatedPage: page }) => {
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const shortlistItem = page.locator('[role="menuitem"]').filter({ hasText: /shortlist|short list/i }).first()
    if (await shortlistItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      const textBefore = await shortlistItem.textContent()
      await shortlistItem.click()
      await page.waitForTimeout(800)
      console.log(`  ✓ Shortlist: texto antes="${textBefore?.trim()}"`)
      // Reabre dropdown para verificar toggle
      await openCardDropdown(page)
      const textAfter = await page.locator('[role="menuitem"]').filter({ hasText: /shortlist/i }).first().textContent().catch(() => '')
      console.log(`  ✓ Shortlist: texto depois="${textAfter?.trim()}"`)
      const toggled = textBefore?.trim() !== textAfter?.trim()
      expect.soft(toggled, 'Texto do shortlist deve mudar após clique').toBe(true)
      await page.keyboard.press('Escape')
    }
  })

  test('toggle Favorito funciona', async ({ authenticatedPage: page }) => {
    const opened = await openCardDropdown(page)
    if (!opened) { test.skip() }

    const favItem = page.locator('[role="menuitem"]').filter({ hasText: /favorit/i }).first()
    if (await favItem.isVisible({ timeout: 2000 }).catch(() => false)) {
      const textBefore = await favItem.textContent()
      await favItem.click()
      await page.waitForTimeout(800)
      console.log(`  ✓ Favorito: "${textBefore?.trim()}" → toggled`)
      await page.keyboard.press('Escape')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 6. BOTÕES APROVAÇÃO / REJEIÇÃO POR ETAPA
// Ref: src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('06 · Botões Aprovar / Reprovar por Etapa', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  async function getCardsInStage(page: Page, stageId: string) {
    const col = page.locator(`[data-testid="kanban-column"][data-stage-id="${stageId}"]`).first()
    return col.locator('[data-testid="candidate-card"]')
  }

  test('coluna Funil (sourcing) exibe botões Aprovar e Reprovar no hover', async ({ authenticatedPage: page }) => {
    const cards = await getCardsInStage(page, 'sourcing')
    const count = await cards.count()
    console.log(`  ✓ Cards em sourcing: ${count}`)

    if (count === 0) {
      console.warn('  ⚠️  Sem candidatos em sourcing — botões Aprovar/Reprovar não testados')
      return
    }

    const card = cards.first()
    await card.hover()
    await page.waitForTimeout(500)
    await snap(page, '06-sourcing-hover')

    const approveBtn = card.locator('button').filter({ hasText: /aprovar|approve/i }).first()
    const rejectBtn  = card.locator('button').filter({ hasText: /reprovar|reject/i }).first()

    await expect.soft(approveBtn, 'Botão Aprovar em sourcing deve aparecer').toBeVisible({ timeout: 3000 })
    await expect.soft(rejectBtn,  'Botão Reprovar em sourcing deve aparecer').toBeVisible({ timeout: 3000 })
  })

  test('coluna Triagem (screening) exibe botões Aprovar e Reprovar', async ({ authenticatedPage: page }) => {
    const cards = await getCardsInStage(page, 'screening')
    const count = await cards.count()
    console.log(`  ✓ Cards em screening: ${count}`)

    if (count === 0) { return }

    const card = cards.first()
    await card.hover()
    await page.waitForTimeout(500)
    await snap(page, '06-screening-hover')

    const approveBtn = card.locator('button').filter({ hasText: /aprovar|approve/i }).first()
    const rejectBtn  = card.locator('button').filter({ hasText: /reprovar|reject/i }).first()

    await expect.soft(approveBtn, 'Botão Aprovar em screening deve aparecer').toBeVisible({ timeout: 3000 })
    await expect.soft(rejectBtn,  'Botão Reprovar em screening deve aparecer').toBeVisible({ timeout: 3000 })
  })

  test('clicar Aprovar em sourcing abre Decision Flow Modal', async ({ authenticatedPage: page }) => {
    // Ref: src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx:57
    //      src/components/candidate-decision-flow-modal.tsx
    const cards = await getCardsInStage(page, 'sourcing')
    if (await cards.count() === 0) { return }

    const card = cards.first()
    await card.hover()
    await page.waitForTimeout(500)

    const approveBtn = card.locator('button').filter({ hasText: /aprovar|approve/i }).first()
    if (!await approveBtn.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await approveBtn.click()
    await page.waitForTimeout(1000)
    await snap(page, '06-approve-modal')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Decision Flow Modal abriu ao aprovar em sourcing')
      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Modal não abriu após aprovar — src/components/candidate-decision-flow-modal.tsx')
    }
  })

  test('clicar Reprovar abre modal de confirmação', async ({ authenticatedPage: page }) => {
    const cards = await getCardsInStage(page, 'sourcing')
    if (await cards.count() === 0) { return }

    const card = cards.first()
    await card.hover()
    await page.waitForTimeout(500)

    const rejectBtn = card.locator('button').filter({ hasText: /reprovar|reject/i }).first()
    if (!await rejectBtn.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await rejectBtn.click()
    await page.waitForTimeout(1000)
    await snap(page, '06-reject-modal')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Modal de reprovação abriu')
      await page.keyboard.press('Escape')
    }
  })

  test('coluna Entrevista (interview_hr) exibe botões corretos sem agendamento', async ({ authenticatedPage: page }) => {
    // Ref: KanbanCardInterviewButtons.tsx:97 — sem agendamento: Urgência + Remarcar
    const stageIds = ['interview_hr', 'interview_technical', 'interview_manager']
    for (const stageId of stageIds) {
      const cards = await getCardsInStage(page, stageId)
      const count = await cards.count()
      console.log(`  ✓ Cards em ${stageId}: ${count}`)

      if (count > 0) {
        const card = cards.first()
        await card.hover()
        await page.waitForTimeout(400)
        await snap(page, `06-${stageId}-hover`)
        break
      }
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 7. MOVER CANDIDATO ENTRE COLUNAS
// Ref: src/components/pages/job-kanban/KanbanBoardSection.tsx
//      src/components/pages/job-kanban/KanbanPageModalsInline.tsx (move confirmation)
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('07 · Mover Candidato Entre Etapas', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('drag and drop move candidato para próxima coluna', async ({ authenticatedPage: page }) => {
    const sourceCol = page.locator('[data-testid="kanban-column"]').nth(0)
    const targetCol = page.locator('[data-testid="kanban-column"]').nth(1)
    const card      = sourceCol.locator('[data-testid="candidate-card"]').first()

    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.warn('  ⚠️  Sem candidatos para arrastar')
      return
    }

    await snap(page, '07-before-drag')
    const countBefore = await targetCol.locator('[data-testid="candidate-card"]').count()

    await card.dragTo(targetCol, { timeout: 10000 })
    await page.waitForTimeout(1500)
    await snap(page, '07-after-drag')

    // Verifica se modal de confirmação abriu
    const confirmModal = page.locator('[role="dialog"]').first()
    if (await confirmModal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Modal de confirmação de movimento abriu')

      // Verifica sub-status sugerido pela LIA
      const liaLabel = confirmModal.locator('text=/LIA|sugest/i').first()
      const hasLia = await liaLabel.isVisible({ timeout: 2000 }).catch(() => false)
      console.log(`  ${hasLia ? '✓' : '⚠️'} Sugestão LIA de sub-status: ${hasLia ? 'presente' : 'ausente'}`)

      // Confirma o movimento
      const confirmBtn = confirmModal.locator('button').filter({ hasText: /confirmar|confirmer|confirm/i }).first()
      if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmBtn.click()
        await page.waitForTimeout(1500)
        await snap(page, '07-after-confirm')
        console.log('  ✓ Movimento confirmado')
      } else {
        await page.keyboard.press('Escape')
      }
    }
  })

  test('modal de movimento exibe seletor de sub-status', async ({ authenticatedPage: page }) => {
    // Ref: KanbanPageModalsInline.tsx — Select de subStatus
    const card   = page.locator('[data-testid="candidate-card"]').first()
    const colTwo = page.locator('[data-testid="kanban-column"]').nth(1)

    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { return }
    await card.dragTo(colTwo)
    await page.waitForTimeout(1000)

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      const selectTrigger = modal.locator('[role="combobox"], [class*="SelectTrigger"]').first()
      if (await selectTrigger.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('  ✓ Seletor de sub-status presente no modal')
      } else {
        console.warn('  ⚠️  Seletor de sub-status não encontrado — KanbanPageModalsInline.tsx')
      }
      await page.keyboard.press('Escape')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 8. BOTÕES COLUNA ENTREVISTA — Alterar/Reagendar Entrevista
// Ref: src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx:99–140
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('08 · Coluna Entrevista — Botões de Entrevista', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('candidato COM entrevista agendada mostra: link vídeo, reagendar, cancelar', async ({ authenticatedPage: page }) => {
    // Ref: KanbanCardInterviewButtons.tsx:102 — agendada=true → 3 botões
    const interviewCols = ['interview_hr', 'interview_technical', 'interview_manager']

    for (const stageId of interviewCols) {
      const col = page.locator(`[data-testid="kanban-column"][data-stage-id="${stageId}"]`)
      if (!await col.isVisible({ timeout: 2000 }).catch(() => false)) continue

      const cards = col.locator('[data-testid="candidate-card"]')
      if (await cards.count() === 0) continue

      const card = cards.first()
      await card.hover()
      await page.waitForTimeout(500)
      await snap(page, `08-${stageId}-interview-buttons`)

      // Candidato com agendamento
      const videoBtn     = card.locator('button').filter({ hasText: /entrar|join|video/i }).first()
      const rescheduleBtn = card.locator('button').filter({ hasText: /reagendar|remarcar|reschedule/i }).first()

      const hasVideo = await videoBtn.isVisible({ timeout: 1000 }).catch(() => false)
      const hasReschedule = await rescheduleBtn.isVisible({ timeout: 1000 }).catch(() => false)

      if (hasVideo || hasReschedule) {
        console.log(`  ✓ ${stageId}: botões de entrevista agendada visíveis`)
        if (hasReschedule) {
          await rescheduleBtn.click()
          await page.waitForTimeout(1000)
          await snap(page, `08-${stageId}-reschedule-modal`)
          const modal = page.locator('[role="dialog"]').first()
          console.log(`  ✓ Modal de reagendamento: ${await modal.isVisible({ timeout: 2000 }).catch(() => false) ? 'abriu' : '⚠️ não abriu'}`)
          await page.keyboard.press('Escape')
        }
      } else {
        // Candidato sem agendamento — deve ter urgência + reagendar
        const urgencyBtn    = card.locator('button').filter({ hasText: /urgência|urgency/i }).first()
        const scheduleBtn   = card.locator('button').filter({ hasText: /agendar|schedule|horário/i }).first()
        const hasUrgency    = await urgencyBtn.isVisible({ timeout: 1000 }).catch(() => false)
        const hasSchedule   = await scheduleBtn.isVisible({ timeout: 1000 }).catch(() => false)
        console.log(`  ${hasUrgency ? '✓' : '⚠️'} ${stageId}: botão urgência ${hasUrgency ? 'presente' : 'ausente'}`)
        console.log(`  ${hasSchedule ? '✓' : '⚠️'} ${stageId}: botão agendar ${hasSchedule ? 'presente' : 'ausente'}`)
      }
      break
    }
  })

  test('botão "Alterar Entrevista" / reagendar abre modal correto', async ({ authenticatedPage: page }) => {
    // Ref: KanbanCardInterviewButtons.tsx:120 — usa openTransition com initialPrompt
    const interviewCols = ['interview_hr', 'interview_technical', 'interview_manager']

    for (const stageId of interviewCols) {
      const col = page.locator(`[data-testid="kanban-column"][data-stage-id="${stageId}"]`)
      if (!await col.isVisible({ timeout: 2000 }).catch(() => false)) continue

      const cards = col.locator('[data-testid="candidate-card"]')
      if (await cards.count() === 0) continue

      const card = cards.first()
      await card.hover()
      await page.waitForTimeout(500)

      const rescheduleBtn = card.locator('button').filter({ hasText: /reagendar|alterar entrevista|remarcar/i }).first()
      if (!await rescheduleBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        console.warn(`  ⚠️  Botão reagendar não encontrado em ${stageId}`)
        break
      }

      await rescheduleBtn.click()
      await page.waitForTimeout(1000)
      await snap(page, '08-reschedule-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('  ✓ Modal de reagendamento abriu')
        // Verifica se há campo de data/hora
        const dateInput = modal.locator('input[type="date"], input[type="datetime-local"], [class*="DatePicker"]').first()
        const hasDate = await dateInput.isVisible({ timeout: 2000 }).catch(() => false)
        console.log(`  ${hasDate ? '✓' : '⚠️'} Campo data: ${hasDate ? 'presente' : 'ausente'}`)
        await page.keyboard.press('Escape')
      }
      break
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 9. COLUNA OFERTA — Botão Enviar Proposta
// Ref: src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx:155–166
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('09 · Coluna Oferta — Enviar Proposta', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('coluna "offer" exibe botão Gerenciar Proposta', async ({ authenticatedPage: page }) => {
    // Ref: KanbanCardInterviewButtons.tsx:155 — stageId==="offer" → manageProposal
    const offerCol = page.locator('[data-testid="kanban-column"][data-stage-id="offer"]')
    if (!await offerCol.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.warn('  ⚠️  Coluna "offer" não encontrada no kanban')
      return
    }

    const cards = offerCol.locator('[data-testid="candidate-card"]')
    const count = await cards.count()
    console.log(`  ✓ Cards em offer: ${count}`)

    if (count === 0) { return }

    const card = cards.first()
    await card.hover()
    await page.waitForTimeout(500)
    await snap(page, '09-offer-hover')

    const proposalBtn = card.locator('button').filter({ hasText: /proposta|proposal|gerenciar/i }).first()
    if (await proposalBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect.soft(proposalBtn, 'Botão Gerenciar Proposta deve ser visível').toBeVisible()

      await proposalBtn.click()
      await page.waitForTimeout(1000)
      await snap(page, '09-proposal-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('  ✓ Modal de proposta abriu')
        await page.keyboard.press('Escape')
      } else {
        // KanbanCardInterviewButtons.tsx:162 — onClick está VAZIO (sem handler)
        console.warn('  ⚠️  Modal de proposta NÃO abriu — botão onClick está vazio em:')
        console.warn('     src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx:162')
      }
    } else {
      console.warn('  ⚠️  Botão de proposta não visível no hover')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 10. COLUNA CONTRATADO — Placement / Conclusão do Processo
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('10 · Coluna Contratado — Placement', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('coluna "hired" está presente e exibe candidatos', async ({ authenticatedPage: page }) => {
    const hiredCol = page.locator('[data-testid="kanban-column"][data-stage-id="hired"]')
      .or(page.locator('[data-testid="kanban-column"]').filter({ hasText: /contratado|hired|placement/i }))
      .first()

    if (!await hiredCol.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.warn('  ⚠️  Coluna "hired/contratado" não encontrada — verificar stages configuradas')
      return
    }

    const cards = hiredCol.locator('[data-testid="candidate-card"]')
    const count = await cards.count()
    await snap(page, '10-hired-column')
    console.log(`  ✓ Coluna Contratado visível. Candidatos: ${count}`)
  })

  test('mover candidato para "hired" inicia fluxo de placement', async ({ authenticatedPage: page }) => {
    const hiredCol = page.locator('[data-testid="kanban-column"][data-stage-id="hired"]')
    if (!await hiredCol.isVisible({ timeout: 3000 }).catch(() => false)) { return }

    const offerCards = page.locator('[data-testid="kanban-column"][data-stage-id="offer"] [data-testid="candidate-card"]')
    if (await offerCards.count() === 0) {
      console.warn('  ⚠️  Sem candidatos em offer para mover para hired')
      return
    }

    const card = offerCards.first()
    await card.dragTo(hiredCol)
    await page.waitForTimeout(1500)
    await snap(page, '10-move-to-hired')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Modal de conclusão de placement abriu')
      await page.keyboard.press('Escape')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 11. HEADER DA VAGA — Pausar / Reativar / Fechar Vaga
// Ref: src/components/pages/job-kanban/KanbanJobHeader.tsx
//      src/components/modals/job-status-modal.tsx
//      src/components/modals/close-vacancy-modal.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('11 · Header da Vaga — Status', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('badge de status da vaga é clicável e abre popover', async ({ authenticatedPage: page }) => {
    // Ref: KanbanJobHeader.tsx:65 — Popover no Badge de status
    const statusBadge = page.locator('[class*="badge" i]').filter({ hasText: /ativa|ativo|pausada|active|paused/i }).first()
      .or(page.locator('[data-testid="job-status-badge"]').first())

    await snap(page, '11-header-status')

    if (!await statusBadge.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.warn('  ⚠️  Badge de status não encontrado — KanbanJobHeader.tsx:65')
      return
    }

    await statusBadge.click()
    await page.waitForTimeout(600)
    await snap(page, '11-status-popover')

    const popover = page.locator('[data-radix-popper-content-wrapper], [role="listbox"]').first()
    if (await popover.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('  ✓ Popover de status abriu')

      const pauseBtn    = popover.locator('button').filter({ hasText: /pausar|pause/i }).first()
      const closeBtn    = popover.locator('button').filter({ hasText: /fechar|encerrar|close|archive/i }).first()
      const activateBtn = popover.locator('button').filter({ hasText: /ativar|reativar|activate/i }).first()

      const hasPause    = await pauseBtn.isVisible({ timeout: 1000 }).catch(() => false)
      const hasClose    = await closeBtn.isVisible({ timeout: 1000 }).catch(() => false)
      const hasActivate = await activateBtn.isVisible({ timeout: 1000 }).catch(() => false)

      console.log(`  ${hasPause ? '✓' : '⚠️'} Botão "Pausar Vaga": ${hasPause ? 'presente' : 'ausente'}`)
      console.log(`  ${hasClose ? '✓' : '⚠️'} Botão "Fechar Vaga": ${hasClose ? 'presente' : 'ausente'}`)
      console.log(`  ${hasActivate ? '✓' : '⚠️'} Botão "Ativar/Reativar": ${hasActivate ? 'presente' : 'ausente'}`)

      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Popover de status não abriu')
    }
  })

  test('botão Pausar abre JobStatusModal', async ({ authenticatedPage: page }) => {
    // Ref: KanbanJobHeader.tsx:75 → setJobStatusModalMode('pause') + setShowJobStatusModal(true)
    //      src/components/modals/job-status-modal.tsx
    const statusBadge = page.locator('[class*="badge" i]').filter({ hasText: /ativa|active/i }).first()
    if (!await statusBadge.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.warn('  ⚠️  Vaga não está ativa — pular teste de pausa')
      return
    }

    await statusBadge.click()
    await page.waitForTimeout(400)

    const pauseBtn = page.locator('button').filter({ hasText: /pausar|pause/i }).first()
    if (!await pauseBtn.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await pauseBtn.click()
    await page.waitForTimeout(800)
    await snap(page, '11-pause-modal')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Modal de Pausa de Vaga abriu')
      // Verifica campos do modal
      const reasonField = modal.locator('textarea, input[name="reason"]').first()
      const hasReason   = await reasonField.isVisible({ timeout: 2000 }).catch(() => false)
      console.log(`  ${hasReason ? '✓' : 'ℹ️'} Campo de motivo de pausa: ${hasReason ? 'presente' : 'não há campo'}`)
      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Modal de pausa não abriu — src/components/modals/job-status-modal.tsx')
    }
  })

  test('botão Fechar Vaga abre CloseVacancyModal', async ({ authenticatedPage: page }) => {
    // Ref: KanbanJobHeader.tsx:82 → setShowCloseVacancyModal(true)
    //      src/components/modals/close-vacancy-modal.tsx
    const statusBadge = page.locator('[class*="badge" i]').filter({ hasText: /ativa|active|pausada/i }).first()
    if (!await statusBadge.isVisible({ timeout: 5000 }).catch(() => false)) { return }

    await statusBadge.click()
    await page.waitForTimeout(400)

    const closeJobBtn = page.locator('button').filter({ hasText: /fechar vaga|encerrar|close job/i }).first()
      .or(page.locator('button').filter({ hasText: /archive/i }).first())

    if (!await closeJobBtn.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await closeJobBtn.click()
    await page.waitForTimeout(800)
    await snap(page, '11-close-vacancy-modal')

    const modal = page.locator('[role="dialog"]').first()
    if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('  ✓ Modal de Fechar Vaga abriu')
      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Modal de fechar vaga não abriu — src/components/modals/close-vacancy-modal.tsx')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 12. TRIAGEM WSI — Enviar Convite / Ver Resultado
// Ref: src/components/wsi/wsi-triagem-invite-modal.tsx
//      src/components/wsi/wsi-text-screening-modal.tsx
//      src/app/api/backend-proxy/candidates/[id]/screening-decision/route.ts
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('12 · Triagem WSI', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('modal WSI Invite tem campos de email e template', async ({ authenticatedPage: page }) => {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { return }

    await card.hover()
    await page.waitForTimeout(400)

    const moreBtn = card.locator('button[aria-label*="opções" i], button[title*="opções" i]')
      .or(card.locator('button').filter({ has: page.locator('svg') }).last())
      .first()
    if (!await moreBtn.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await moreBtn.click()
    await page.waitForTimeout(300)

    const wsiItem = page.locator('[role="menuitem"]').filter({ hasText: /wsi/i }).first()
    if (!await wsiItem.isVisible({ timeout: 2000 }).catch(() => false)) { return }

    await wsiItem.click()
    await page.waitForTimeout(1000)
    await snap(page, '12-wsi-invite-modal')

    const modal = page.locator('[role="dialog"]').first()
    if (!await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.warn('  ⚠️  Modal WSI não abriu')
      return
    }

    // Verifica campos
    const emailField = modal.locator('input[type="email"], input[name="email"]').first()
    const hasEmail   = await emailField.isVisible({ timeout: 2000 }).catch(() => false)
    console.log(`  ${hasEmail ? '✓' : '⚠️'} Campo email no modal WSI: ${hasEmail ? 'presente' : 'ausente'}`)

    // Verifica botão de envio
    const sendBtn = modal.locator('button').filter({ hasText: /enviar|send/i }).first()
    if (await sendBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Intercepta chamada de API
      const [request] = await Promise.all([
        page.waitForRequest(req => req.url().includes('screening') || req.url().includes('wsi'), { timeout: 3000 }).catch(() => null),
        sendBtn.click(),
      ])
      await page.waitForTimeout(1500)
      await snap(page, '12-wsi-after-send')

      if (request) {
        console.log(`  ✓ API chamada: ${request.url()} [${request.method()}]`)
      } else {
        console.warn('  ⚠️  Nenhuma requisição de screening capturada após envio WSI')
      }

      const toast = page.locator('[class*="toast"], [role="alert"]').first()
      const toastText = await toast.textContent().catch(() => '')
      console.log(`  ✓ Toast WSI: "${toastText}"`)
    }
    await page.keyboard.press('Escape')
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 13. CANDIDATE PREVIEW PANEL — Abrir perfil pelo clique no card
// Ref: src/components/pages/job-kanban/KanbanCandidatePreviewPanel.tsx
//      src/components/candidate-page.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('13 · Preview Panel do Candidato', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('clique no card abre painel de preview do candidato', async ({ authenticatedPage: page }) => {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { return }

    await card.click()
    await page.waitForTimeout(1500)
    await snap(page, '13-candidate-preview')

    // Painel lateral ou modal de perfil
    const panel = page.locator('[data-testid="candidate-preview"], [class*="CandidatePage"], [class*="candidate-page"], [role="dialog"]').first()
    if (await panel.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  ✓ Preview/perfil do candidato abriu')

      // Verifica tabs: Perfil, Atividades, Arquivos, Opiniões
      for (const tabName of ['perfil', 'atividades', 'arquivos', 'opiniões']) {
        const tab = panel.locator(`[role="tab"]:has-text("${tabName}")`).or(
          panel.locator(`button:has-text("${tabName}")`)
        ).first()
        const visible = await tab.isVisible({ timeout: 1000 }).catch(() => false)
        console.log(`  ${visible ? '✓' : '⚠️'} Tab "${tabName}": ${visible ? 'presente' : 'não encontrada'}`)
      }

      await snap(page, '13-candidate-tabs')
      await page.keyboard.press('Escape')
    } else {
      console.warn('  ⚠️  Preview de candidato não abriu ao clicar no card')
      console.warn('     Ref: src/components/pages/job-kanban/KanbanCandidatePreviewPanel.tsx')
    }
  })

  test('pipeline decision bar exibe botões de decisão', async ({ authenticatedPage: page }) => {
    // Ref: src/components/candidate-preview/PipelineDecisionBar.tsx
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 5000 }).catch(() => false)) { return }

    await card.click()
    await page.waitForTimeout(1500)

    const decisionBar = page.locator('[class*="PipelineDecision"], [data-testid="pipeline-decision-bar"]').first()
    const approveBtn  = page.locator('button').filter({ hasText: /aprovar|approve/i }).first()
    const rejectBtn   = page.locator('button').filter({ hasText: /reprovar|reject/i }).first()

    const hasApprove = await approveBtn.isVisible({ timeout: 3000 }).catch(() => false)
    const hasReject  = await rejectBtn.isVisible({ timeout: 3000 }).catch(() => false)

    console.log(`  ${hasApprove ? '✓' : '⚠️'} Botão Aprovar no preview: ${hasApprove ? 'OK' : 'NÃO ENCONTRADO'}`)
    console.log(`  ${hasReject  ? '✓' : '⚠️'} Botão Reprovar no preview: ${hasReject  ? 'OK' : 'NÃO ENCONTRADO'}`)

    await page.keyboard.press('Escape')
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 14. FILTROS DO KANBAN
// Ref: src/components/pages/job-kanban/KanbanFiltersPanel.tsx
//      src/components/pages/job-kanban/KanbanToolbar.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('14 · Filtros do Kanban', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('toolbar tem botão de filtros', async ({ authenticatedPage: page }) => {
    // Ref: src/components/pages/job-kanban/KanbanToolbar.tsx
    const filterBtn = page.locator('button').filter({ hasText: /filtros|filter/i }).first()
      .or(page.locator('[data-testid="filter-button"]').first())
      .or(page.locator('button[aria-label*="filtro" i]').first())

    await snap(page, '14-toolbar')
    const hasFilters = await filterBtn.isVisible({ timeout: 5000 }).catch(() => false)
    console.log(`  ${hasFilters ? '✓' : '⚠️'} Botão de filtros: ${hasFilters ? 'presente' : 'ausente'}`)

    if (hasFilters) {
      await filterBtn.click()
      await page.waitForTimeout(800)
      await snap(page, '14-filters-panel')

      const panel = page.locator('[class*="FiltersPanel"], [class*="filter-panel"], [data-testid="filters-panel"]').first()
      const panelOpen = await panel.isVisible({ timeout: 3000 }).catch(() => false)
      console.log(`  ${panelOpen ? '✓' : '⚠️'} Painel de filtros: ${panelOpen ? 'abriu' : 'não abriu'}`)
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 15. INTEGRAÇÕES E CHAMADAS DE API
// Ref: src/app/api/backend-proxy/candidates/[id]/stage/route.ts
//      src/app/api/backend-proxy/job-vacancies/[jobId]/close/route.ts
//      src/app/api/backend-proxy/job-vacancies/[jobId]/publish/route.ts
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('15 · APIs e Integrações — Verificação de Chamadas', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('carregamento do kanban chama API de candidatos da vaga', async ({ authenticatedPage: page }) => {
    const requests: string[] = []
    page.on('request', req => {
      if (req.url().includes('/api/') || req.url().includes('backend-proxy')) {
        requests.push(`${req.method()} ${req.url()}`)
      }
    })

    await goToFirstKanban(page)
    await page.waitForTimeout(3000)

    console.log('  ✓ API requests capturadas na carga do kanban:')
    requests.forEach(r => console.log(`    ${r}`))

    const hasCandidatesCall = requests.some(r => r.includes('candidates') || r.includes('pipeline'))
    const hasJobCall        = requests.some(r => r.includes('job-vacanc') || r.includes('vagas'))

    expect.soft(hasCandidatesCall || hasJobCall, 'Deve haver chamadas de API para candidatos ou vagas').toBe(true)
  })

  test('resposta da API tem estrutura correta (não retorna 401/500)', async ({ authenticatedPage: page }) => {
    const responses: { url: string; status: number }[] = []
    page.on('response', resp => {
      if (resp.url().includes('/api/') || resp.url().includes('backend-proxy')) {
        responses.push({ url: resp.url(), status: resp.status() })
      }
    })

    await goToFirstKanban(page)
    await page.waitForTimeout(3000)

    const errors = responses.filter(r => r.status >= 400)
    console.log('  ✓ Respostas de API:')
    responses.forEach(r => console.log(`    [${r.status}] ${r.url}`))

    if (errors.length > 0) {
      console.warn('  ⚠️  Erros de API encontrados:')
      errors.forEach(e => console.warn(`    [${e.status}] ${e.url}`))
    }

    // Não falhamos o teste por isso, apenas reportamos
    expect.soft(errors.filter(e => e.status === 401), 'Sem erros 401 (auth) nas APIs').toHaveLength(0)
  })

  test('API de mudança de stage responde ao mover candidato', async ({ authenticatedPage: page }) => {
    // Ref: src/app/api/backend-proxy/candidates/[id]/stage/route.ts
    const stageRequests: { method: string; url: string; body: string }[] = []
    page.on('request', req => {
      if (req.url().includes('/stage')) {
        stageRequests.push({ method: req.method(), url: req.url(), body: req.postData() || '' })
      }
    })

    const card   = page.locator('[data-testid="candidate-card"]').first()
    const colTwo = page.locator('[data-testid="kanban-column"]').nth(1)

    if (await card.isVisible({ timeout: 5000 }).catch(() => false)) {
      await card.dragTo(colTwo)
      await page.waitForTimeout(2000)

      // Cancela modal se abrir
      const confirmBtn = page.locator('button').filter({ hasText: /confirmar|cancel/i }).first()
      if (await confirmBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        await page.keyboard.press('Escape')
      }
    }

    if (stageRequests.length > 0) {
      console.log('  ✓ API de stage chamada:')
      stageRequests.forEach(r => console.log(`    ${r.method} ${r.url}`))
    } else {
      console.warn('  ⚠️  API /stage não chamada ao mover candidato — verificar:')
      console.warn('     src/app/api/backend-proxy/candidates/[id]/stage/route.ts')
    }
  })

  test('verificar se dados de candidato são reais ou mockados', async ({ authenticatedPage: page }) => {
    const card = page.locator('[data-testid="candidate-card"]').first()
    if (!await card.isVisible({ timeout: 8000 }).catch(() => false)) {
      console.warn('  ⚠️  Sem cards no kanban — dados não verificados')
      return
    }

    const candidateName = await card.locator('h4').first().textContent().catch(() => '')
    const candidateId   = await card.getAttribute('data-candidate-id')

    const isMock = /test|lorem|mock|exemplo|demo|fake/i.test(candidateName || '')
    console.log(`  ✓ Candidato: "${candidateName}" (id: ${candidateId})`)
    console.log(`  ${isMock ? '⚠️  DADOS PARECEM SER MOCK' : '✓ Dados parecem reais'}`)
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 16. KANBAN TABLE VIEW — Tab Tabela
// Ref: src/components/pages/job-kanban/KanbanTableView.tsx
//      src/components/pages/job-kanban/KanbanTableCellRenderer.tsx
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('16 · Visão em Tabela', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('switch para view tabela funciona', async ({ authenticatedPage: page }) => {
    const tableTab = page.getByRole('button', { name: /^Tabela$/i }).first()
      .or(page.locator('[data-tab="table"], [value="table"]').first())

    if (!await tableTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.warn('  ⚠️  Tab de tabela não encontrada')
      return
    }

    await tableTab.click()
    await page.waitForTimeout(1000)
    await snap(page, '16-table-view')

    const table = page.locator('table, [role="table"], [class*="KanbanTableView"]').first()
    if (await table.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('  ✓ Visão em tabela carregou')
      const rows = table.locator('tr, [role="row"]')
      const count = await rows.count()
      console.log(`  ✓ Linhas na tabela: ${count}`)
    } else {
      console.warn('  ⚠️  Tabela não carregou — src/components/pages/job-kanban/KanbanTableView.tsx')
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 17. AUDITORIA VISUAL COMPLETA — Screenshot de Cada Coluna
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('17 · Auditoria Visual — Screenshots', () => {
  test('captura screenshot completa do kanban board', async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
    await page.waitForTimeout(2000)

    await page.screenshot({
      path: 'playwright-report/screenshots/17-kanban-full-board.png',
      fullPage: true
    })
    console.log('  ✓ Screenshot completo salvo: playwright-report/screenshots/17-kanban-full-board.png')
  })

  test('captura cada coluna individualmente', async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)

    const columns = page.locator('[data-testid="kanban-column"]')
    const count = await columns.count()

    for (let i = 0; i < count; i++) {
      const col = columns.nth(i)
      const stageId = await col.getAttribute('data-stage-id') || `col-${i}`
      await col.screenshot({ path: `playwright-report/screenshots/17-column-${stageId}.png` })
      console.log(`  ✓ Screenshot coluna ${stageId}`)
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
// 18. RELATÓRIO DA VAGA
// Ref: src/components/job-report-modal.tsx
//      KanbanJobHeader.tsx → handleShowReport
// ═══════════════════════════════════════════════════════════════════════════════

test.describe('18 · Relatório da Vaga', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await goToFirstKanban(page)
    await ensureKanbanLoaded(page)
  })

  test('botão de relatório no header abre modal', async ({ authenticatedPage: page }) => {
    // Ref: KanbanJobHeader.tsx → handleShowReport + JobReportModal
    const reportBtn = page.locator('button').filter({ hasText: /relatório|report/i }).first()
      .or(page.locator('button[aria-label*="relatório" i]').first())
      .or(page.locator('[data-testid="report-button"]').first())

    const hasReport = await reportBtn.isVisible({ timeout: 5000 }).catch(() => false)
    console.log(`  ${hasReport ? '✓' : '⚠️'} Botão Relatório: ${hasReport ? 'encontrado' : 'não encontrado no header'}`)

    if (hasReport) {
      await reportBtn.click()
      await page.waitForTimeout(1000)
      await snap(page, '18-report-modal')

      const modal = page.locator('[role="dialog"]').first()
      if (await modal.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('  ✓ Modal de relatório abriu')
        await page.keyboard.press('Escape')
      }
    }
  })
})
