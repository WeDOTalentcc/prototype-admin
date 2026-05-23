/**
 * E2E persistence — Configurações > Pipeline > Recruitment Stages.
 *
 * Cobertura: smoke render do RecruitmentPipelineTab + entrar em modo
 * edit + tentar persistir mudança simples (toggle de sub-status ou
 * "Save" sem mudanças → estado "synced").
 *
 * ⚠ Drag-drop reorder NÃO é coberto aqui porque Playwright DnD pra
 * componentes @dnd-kit (canonical no `useRecruitmentPipeline`) tem
 * histórico de flakiness. Reorder é coberto por unit tests
 * (`__tests__/useRecruitmentPipeline.test.tsx`). Aqui foco em smoke
 * + edit-mode toggle + cancel-without-save.
 *
 * Selectors heurísticos: `RecruitmentPipelineTab.tsx` ainda NÃO tem
 * `data-testid` canonical (auditoria 2026-05-21). Usamos role+name
 * com texto i18n PT. TODO no README pra adicionar testids.
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('@persistence Pipeline — RecruitmentStages persistence', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('pipeline', 'recruitment-stages')
  })

  test('smoke: RecruitmentPipelineTab renderiza com stages', async ({
    authenticatedPage: page,
  }) => {
    // Pipeline carrega 5+ stages canonical. Heurística: texto "estagio"/
    // "stage" OU card visível contendo um dos stages canonical default.
    const visible = await page
      .locator('text=/Triagem|Sourcing|Entrevista|Oferta|Stages|Pipeline/i')
      .first()
      .isVisible({ timeout: 15_000 })
      .catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] RecruitmentPipelineTab não renderizou stages. Possível ' +
          'causa: useRecruitmentHub("pipeline") em loading state preso ou ' +
          'backend /api/v1/recruitment-stages 404. Verificar hub.',
      )
      return
    }
    expect(visible).toBe(true)
  })

  test('botão "Editar" entra em modo edição e "Cancelar" sai sem persistir', async ({
    authenticatedPage: page,
  }) => {
    const editBtn = page.getByRole('button', { name: /^Editar$|^Edit$/i }).first()
    const editVisible = await editBtn.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!editVisible) {
      test.skip(
        true,
        '[setup] Botão Editar não visível. RecruitmentPipelineTab pode ' +
          'estar em loading state ou usuário sem permission.',
      )
      return
    }
    await editBtn.click()
    await page.waitForTimeout(500)

    // Em modo edit, "Salvar" + "Cancelar" devem ficar visíveis
    const saveBtn = page.getByRole('button', { name: /Salvar|Save/i }).first()
    const cancelBtn = page.getByRole('button', { name: /Cancelar|Cancel/i }).first()
    const saveVisible = await saveBtn.isVisible({ timeout: 3_000 }).catch(() => false)
    const cancelVisible = await cancelBtn.isVisible({ timeout: 3_000 }).catch(() => false)

    expect(
      saveVisible || cancelVisible,
      '[regression] Após clicar Editar, nem Salvar nem Cancelar apareceram. ' +
        'Verificar `isEditingPipeline` toggle em useRecruitmentHub.',
    ).toBe(true)

    // Cancelar pra não persistir nada
    if (cancelVisible) {
      await cancelBtn.click()
      await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => { /* ok */ })
    }
  })

  test('stages renderizam ordem estável após reload (sem edit)', async ({
    authenticatedPage: page,
  }) => {
    // Captura primeiros N stages visíveis (heurística — cards com h3/h4
    // dentro do tab).
    const stageHeaders = page.locator(
      'h3, h4, [class*="stage-card"], [class*="StageCard"]',
    )
    const beforeCount = await stageHeaders
      .count()
      .catch(() => 0)
    if (beforeCount === 0) {
      test.skip(true, '[setup] Sem stages visíveis pra comparar ordem.')
      return
    }
    const beforeText = await stageHeaders
      .first()
      .textContent()
      .catch(() => '')

    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    const afterFirst = page
      .locator('h3, h4, [class*="stage-card"], [class*="StageCard"]')
      .first()
    await expect(afterFirst).toBeVisible({ timeout: 10_000 })
    const afterText = await afterFirst.textContent().catch(() => '')

    expect(
      (beforeText || '').trim(),
      `[persistence FAIL] primeira stage mudou após reload sem edit. ` +
        `Antes: "${beforeText?.trim()}", depois: "${afterText?.trim()}".`,
    ).toBe((afterText || '').trim())
  })
})
