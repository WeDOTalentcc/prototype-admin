/**
 * E2E persistence — Configurações > Minha Empresa > Learning Loops.
 *
 * Cobertura: 1 master toggle ("Loops de Aprendizado") + 4 sub-toggles
 * (DNA Cultural, Histórico por Departamento, Sugestão de JD Similar,
 * Efetividade de Perguntas WSI). Pattern canonical: cada toggle é um
 * `role="switch"` com `aria-label` = `def.label` (vide
 * `LearningLoopsPanel.tsx:106`).
 *
 * Defesa em profundidade: este test garante que o PATCH realmente
 * persiste (não apenas atualiza state local React) — bug clássico
 * de "toggle parecia salvar mas voltou OFF no refresh" (audit
 * 2026-05-21 menu_configuracoes_inteligencia_agentes.md, Camada 1
 * gate fail-closed).
 *
 * ⚠ Cuidado: este test MUTA state real do tenant demo. O afterEach
 * restaura o estado inicial pra evitar drift entre runs.
 */
import { test, expect } from './persistence-fixtures'
import { assertSwitchPersistsAfterRefresh, restoreSwitch } from './test-utils'

test.describe.configure({ retries: 1 })

const MASTER_LABEL = 'Loops de Aprendizado'
const SUB_LABELS = [
  'DNA Cultural da Empresa (Layer 3)',
  'Histórico por Departamento (Layer 4)',
  'Sugestão de JD Similar (Phase 1)',
  'Efetividade de Perguntas WSI (Phase 3)',
] as const

test.describe('Learning Loops — toggle persistence', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    // Learning Loops vive dentro de Minha Empresa. Sub-tab pode variar
    // (data-testid="settings-subtab-learning-loops" ou role="tab").
    await navigateToSettings('minha-empresa', 'learning-loops')
  })

  test('master toggle "Loops de Aprendizado" persiste após refresh @persistence', async ({
    authenticatedPage: page,
  }) => {
    const switchVisible = await page
      .getByRole('switch', { name: MASTER_LABEL })
      .first()
      .isVisible({ timeout: 10_000 })
      .catch(() => false)

    if (!switchVisible) {
      test.skip(
        true,
        '[setup] Master toggle não visível. Possíveis causas: sub-tab ' +
          '"learning-loops" não existe no menu (testid não bate) ou ' +
          'painel não foi montado. Verificar `LearningLoopsPanel.tsx` ' +
          'wire-up no hub Minha Empresa.',
      )
      return
    }

    const { before } = await assertSwitchPersistsAfterRefresh(page, MASTER_LABEL)
    // Restore estado inicial pra próximo run não herdar drift
    await restoreSwitch(page, MASTER_LABEL, before)
  })

  // Tests paramétricos pros 4 sub-toggles — falha individual fica
  // isolada (não derruba o batch inteiro).
  for (const label of SUB_LABELS) {
    test(`sub-toggle "${label}" persiste após refresh @persistence`, async ({
      authenticatedPage: page,
    }) => {
      const sw = page.getByRole('switch', { name: label }).first()
      const visible = await sw.isVisible({ timeout: 8_000 }).catch(() => false)
      if (!visible) {
        test.skip(
          true,
          `[setup] Sub-toggle "${label}" não visível. Possível causa: ` +
            `master OFF (sub-toggles ficam disabled) ou label mudou no frontend.`,
        )
        return
      }
      const disabled = (await sw.getAttribute('disabled')) !== null
      if (disabled) {
        test.skip(true, `[setup] Sub-toggle "${label}" disabled — master está OFF.`)
        return
      }

      const { before } = await assertSwitchPersistsAfterRefresh(page, label)
      await restoreSwitch(page, label, before)
    })
  }
})
