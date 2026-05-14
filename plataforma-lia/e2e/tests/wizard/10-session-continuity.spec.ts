/**
 * E2E sentinel — Task #1080 wizard-session-continuity-canonical-refactor.
 *
 * Reproduz o bug do pw-cenario-D2: page.reload() mid-wizard fazia o FE
 * perder o thread_id custom (priority 1 do legado derive_thread_id) e o
 * Redis marker (`lia:wizard:active:*`) eventualmente expirava — turno
 * seguinte caía em rota não-wizard, o checkpointer LangGraph não era
 * restaurado, e a LIA "esquecia" o contexto da vaga.
 *
 * Modelo canônico Task #1080: thread_id é função pura de
 * (company_id, session_id) → page.reload() preserva session_id (cookie)
 * → derive_thread_id retorna o MESMO valor → checkpointer LangGraph é
 * restaurado → LIA mantém contexto.
 *
 * Estratégia do teste: mensagem com termo identificador único,
 * page.reload(), follow-up curto, valida que a LIA referencia o que foi
 * dito antes do reload. Loop curto (3 reloads) — evidência empírica
 * suficiente; o invariante real é coberto por unit + integration tests
 * (ver tests/integration/agents/test_wizard_session_continuity_t1080.py).
 */
import { test, expect } from '@playwright/test'
import { authenticateAsRecruiter } from '../../fixtures/auth.fixture'
import {
  openJobWizard,
  sendWizardMessage,
} from '../../fixtures/wizard-conversation.fixture'

const RELOAD_ITERATIONS = 3
const UNIQUE_TITLE = `Engenheiro de Plataforma Sênior ${Date.now()}`

test.describe('Wizard — continuidade de sessão após page.reload()', () => {
  test('LIA preserva o título da vaga através de múltiplos reloads', async ({ page }) => {
    test.setTimeout(180_000)

    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    // Turno 1 — estabelece o contexto com um identificador único.
    await sendWizardMessage(page, `Quero criar uma vaga de ${UNIQUE_TITLE}.`)

    // Captura snapshot do chat antes do primeiro reload (sanity).
    const chatLog = page.locator('[data-testid="lia-chat"], .lia-chat').first()
    await expect(chatLog).toBeVisible()

    for (let i = 1; i <= RELOAD_ITERATIONS; i++) {
      // page.reload() é o disparador canônico do bug pw-cenario-D2:
      // FE perde qualquer thread_id custom em memória; canônico Task #1080
      // re-deriva o mesmo thread_id de (company_id, session_id).
      await page.reload({ waitUntil: 'networkidle' })

      // Aguarda o chat ficar pronto novamente.
      const chatReady = page.locator(
        '[data-testid="lia-chat"], .lia-chat, [data-testid="chat-input"]',
      ).first()
      await chatReady.waitFor({ state: 'visible', timeout: 20_000 })

      // Pergunta curta que SÓ pode ser respondida com contexto preservado.
      await sendWizardMessage(
        page,
        'Qual era o cargo dessa vaga mesmo? Me lembra com a frase exata.',
      )

      // Tolerância: o título completo pode ter sido normalizado pela LIA;
      // exige pelo menos a parte "Engenheiro de Plataforma" como evidência
      // de que a session foi de fato restaurada do checkpointer.
      const evidence = page.locator(
        ':text-matches("Engenheiro de Plataforma", "i")',
      ).last()
      await expect(
        evidence,
        `Reload ${i}/${RELOAD_ITERATIONS}: a LIA deveria lembrar o cargo ` +
          `(${UNIQUE_TITLE}) — Task #1080 single-source-of-truth quebrado.`,
      ).toBeVisible({ timeout: 30_000 })
    }
  })

  test('LIA não pergunta o nome da empresa após reload (anti-regressão B1/B4)', async ({ page }) => {
    test.setTimeout(120_000)

    await authenticateAsRecruiter(page)
    await openJobWizard(page)

    await sendWizardMessage(page, 'Quero criar uma vaga de Analista de Dados Pleno.')
    await page.reload({ waitUntil: 'networkidle' })

    const chatReady = page.locator(
      '[data-testid="lia-chat"], .lia-chat, [data-testid="chat-input"]',
    ).first()
    await chatReady.waitFor({ state: 'visible', timeout: 20_000 })

    await sendWizardMessage(page, 'Qual a faixa salarial sugerida?')

    // Anti-pattern: a LIA não pode pedir nome / ID da empresa, ela já tem
    // via JWT (tenant_context_snippet — vide replit.md → "Tenant Context").
    const askedForCompany = page.locator(
      ':text-matches("(?:qual.*empresa|nome.*empresa|id.*empresa|company.?id)", "i")',
    )
    await expect(
      askedForCompany,
      'Anti-pattern Task #1080: a LIA NÃO pode perguntar o nome/ID da ' +
        'empresa após reload — o tenant vem do JWT, não do chat.',
    ).toHaveCount(0, { timeout: 15_000 })
  })
})
