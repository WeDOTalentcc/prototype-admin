/**
 * E2E persistence — Configurações > Minha Empresa (campos core).
 *
 * Gap original (Paulo 2026-05-21): "verificar persistência de cada
 * campo de cada sessão e subssessão" — auditamos código, NÃO
 * testamos round-trip via browser. Este spec preenche o gap para
 * o subset crítico do hub Minha Empresa.
 *
 * Estratégia:
 *   1. Login canonical via `auth.fixture` (POST /api/v1/auth/login)
 *   2. Navega via menu canonical `[data-testid="settings-menu-…"]`
 *   3. Pra cada campo: abre Edit → injeta valor único (timestamp) →
 *      Save → reload → assert valor preservado (BD + GET round-trip)
 *
 * TODO canonical (frontend): `MinhaEmpresaCard.tsx:144` (input
 * edit-in-place) NÃO tem `data-field="<canonical_key>"`. Os locators
 * abaixo dependem do texto do bloco (`pending-section-basic` etc.)
 * + heurística de "primeiro input visível no card". Quando o
 * frontend padronizar `data-field`, refatorar pra usar selector
 * estável.
 */
import { test, expect } from './persistence-fixtures'
import { assertInputPersistsAfterRefresh, waitForSaveSuccess } from './test-utils'

test.describe.configure({ retries: 1 })

test.describe('Minha Empresa — persistência campos core', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('minha-empresa')
  })

  /**
   * Smoke gate: hub abre e mostra o painel de progresso canonical.
   * Sem isso, nenhum dos tests abaixo faz sentido.
   */
  test('hub renderiza com painel de progresso', async ({ authenticatedPage: page }) => {
    await expect(page.locator('[data-testid="profile-progress-panel"]')).toBeVisible({
      timeout: 15_000,
    })
    await expect(page.locator('h2:has-text("Minha Empresa")')).toBeVisible({ timeout: 10_000 })
  })

  /**
   * Persistence: campo "nome da empresa" (bloco basic).
   *
   * Assume que o bloco `basic` está em modo card editável. Se a
   * empresa-demo do CI já está 100% preenchida, esse test pula
   * (skipif via `pending-section-basic` invisible).
   */
  test('campo do bloco basic persiste após refresh @persistence', async ({
    authenticatedPage: page,
  }, testInfo) => {
    // O hub mostra cards `pending-section-{basic,mission,values,…}`
    // quando há campos faltando. Se basic já está completo, abrir o
    // card pelo título.
    const basicCard = page.locator('[data-testid="pending-section-basic"]').first()
    const hasPending = await basicCard.isVisible({ timeout: 5_000 }).catch(() => false)

    if (!hasPending) {
      test.skip(
        true,
        'Bloco "basic" já está 100% preenchido na empresa-demo. ' +
          'Rodar `python -m scripts.seeds.demo_company --reset basic` ' +
          'pra restaurar pendências e re-rodar.',
      )
      return
    }

    // Procura input editável dentro do card basic. Heurística enquanto
    // não há `data-field` canonical: primeiro `<input type="text">`
    // dentro do card que NÃO esteja desabilitado.
    const editBtn = basicCard.locator('button:has-text("Editar"), [aria-label*="Editar"]').first()
    if (await editBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await editBtn.click()
    }
    const input = basicCard.locator('input[type="text"]:not([disabled])').first()
    const saveBtn = basicCard.locator('button:has(svg.lucide-check), [data-testid="save-btn"]').first()

    const testValue = `E2E-${Date.now()}`
    await assertInputPersistsAfterRefresh(page, input, saveBtn, testValue)

    await page.screenshot({
      path: testInfo.outputPath('minha-empresa-after-reload.png'),
      fullPage: true,
    })

    // Após reload, valor deve aparecer no card (modo leitura)
    const reopenedCard = page.locator('[data-testid="pending-section-basic"]').first()
    // Pode ter sumido se preencheu o último field pendente — tentar
    // alternativa de busca por texto no card-mãe ou via API GET
    const found =
      (await reopenedCard.isVisible({ timeout: 3_000 }).catch(() => false))
        ? await reopenedCard.locator(`text=${testValue}`).first().isVisible({ timeout: 5_000 }).catch(() => false)
        : await page.locator(`text=${testValue}`).first().isVisible({ timeout: 5_000 }).catch(() => false)

    expect(
      found,
      `[persistence FAIL] valor "${testValue}" não foi encontrado após reload. ` +
        `Provável causa: PATCH /api/v1/company/profile retornou 200 mas o GET ` +
        `subsequente NÃO trouxe o campo (round-trip quebrado). Comparar com ` +
        `sentinel test_company_profile_roundtrip_t1017.py.`,
    ).toBe(true)
  })

  /**
   * Persistence sentinel: campo missão (bloco mission).
   * Mesmo pattern do basic — separado pra isolar falha por bloco.
   */
  test('campo do bloco mission persiste após refresh @persistence', async ({
    authenticatedPage: page,
  }) => {
    const missionCard = page.locator('[data-testid="pending-section-mission"]').first()
    const hasPending = await missionCard.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!hasPending) {
      test.skip(true, 'Bloco "mission" já completo — re-seed demo pra restaurar pendência.')
      return
    }

    const editBtn = missionCard.locator('button:has-text("Editar"), [aria-label*="Editar"]').first()
    if (await editBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await editBtn.click()
    }
    const input = missionCard.locator('input[type="text"]:not([disabled])').first()
    const saveBtn = missionCard.locator('button:has(svg.lucide-check), [data-testid="save-btn"]').first()

    const testValue = `Missão E2E ${Date.now()}`
    await assertInputPersistsAfterRefresh(page, input, saveBtn, testValue)

    const found = await page.locator(`text=${testValue}`).first().isVisible({ timeout: 5_000 }).catch(() => false)
    expect(found, `[persistence FAIL] missão "${testValue}" não preservada após reload`).toBe(true)
  })
})
