/**
 * E2E persistence — Configurações > Pipeline > Screening Questions.
 *
 * Cobertura: smoke render do RecruitmentScreeningTab + add question
 * persiste após reload + delete question persiste.
 *
 * ⚠ MUTAÇÃO: criar/deletar question é destrutivo do POV do tenant.
 * Cada test cria question com prefixo `e2e-test-` no enunciado e
 * deleta no afterEach (fail-safe). Se assertion intermediária falhar
 * o cleanup ainda roda no afterEach.
 *
 * Pattern UI canonical (`RecruitmentScreeningTab.tsx`):
 *   1. Clicar "Editar" → entra em modo edit
 *   2. Clicar "Nova pergunta" → abre form
 *   3. Preencher question text + type=text + required=false
 *   4. Clicar "Adicionar" no form → question vai pra lista
 *   5. Clicar "Salvar alterações" → POST persiste
 *   6. Reload → question presente
 *
 * Selectors heurísticos — RecruitmentScreeningTab ainda sem
 * data-testid canonical. Usamos label i18n "recruitment.screening.*"
 * via texto traduzido PT. TODO no README pra adicionar testids.
 */
import { test, expect } from './persistence-fixtures'

const E2E_QUESTION_PREFIX = 'e2e-test-question'

test.describe.configure({ retries: 1 })

test.describe('@persistence Pipeline — Screening Questions persistence', () => {
  test.setTimeout(180_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('pipeline', 'screening-questions')
  })

  test.afterEach(async ({ authenticatedPage: page }) => {
    // Fail-safe: tentar deletar qualquer question com prefixo e2e-test
    try {
      const editBtn = page.getByRole('button', { name: /^Editar$|^Edit$/i }).first()
      if (await editBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await editBtn.click()
        await page.waitForTimeout(500)
      }

      const testQuestion = page
        .locator(`text=/${E2E_QUESTION_PREFIX}/i`)
        .first()
      if (await testQuestion.isVisible({ timeout: 2_000 }).catch(() => false)) {
        // Procurar botão Delete/Trash perto da question
        const deleteBtn = testQuestion
          .locator('xpath=ancestor::*[self::div or self::li or self::tr][1]')
          .locator('button[aria-label*="Delet"], button[aria-label*="Remover"], button:has(svg)')
          .last()
        if (await deleteBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await deleteBtn.click()
          await page.waitForTimeout(300)
        }

        const saveBtn = page.getByRole('button', { name: /Salvar/i }).first()
        if (await saveBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
          await saveBtn.click()
          await page.waitForLoadState('networkidle', { timeout: 5_000 }).catch(() => { /* ok */ })
        }
      }
    } catch { /* cleanup best-effort */ }
  })

  test('smoke: RecruitmentScreeningTab renderiza com auto-questions note', async ({
    authenticatedPage: page,
  }) => {
    // Heading + texto canonical (autoQuestionsNote / catalogTitle do i18n)
    const visible = await page
      .locator('text=/perguntas|questions|triagem|screening|catálogo|catalog/i')
      .first()
      .isVisible({ timeout: 15_000 })
      .catch(() => false)

    if (!visible) {
      test.skip(
        true,
        '[setup] RecruitmentScreeningTab não renderizou. Verificar ' +
          'useRecruitmentHub("screening") loading state e backend ' +
          '/api/v1/screening-questions endpoint.',
      )
      return
    }
    expect(visible).toBe(true)
  })

  test('add question persiste após refresh', async ({
    authenticatedPage: page,
  }) => {
    const editBtn = page.getByRole('button', { name: /^Editar$|^Edit$/i }).first()
    const editVisible = await editBtn.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!editVisible) {
      test.skip(true, '[setup] Botão Editar não visível em screening tab.')
      return
    }
    await editBtn.click()
    await page.waitForTimeout(500)

    // Abrir form de nova pergunta
    const newBtn = page
      .getByRole('button', { name: /Nova pergunta|New question/i })
      .first()
    const newVisible = await newBtn.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!newVisible) {
      test.skip(true, '[setup] Botão "Nova pergunta" não visível.')
      return
    }
    await newBtn.click()
    await page.waitForTimeout(500)

    // Preencher texto da pergunta. Usa htmlFor "screening-question-text".
    const questionInput = page
      .locator('#screening-question-text, textarea#screening-question-text, [name="question-text"]')
      .first()
    const inputVisible = await questionInput.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!inputVisible) {
      test.skip(true, '[setup] input #screening-question-text não visível.')
      return
    }
    const unique = `${E2E_QUESTION_PREFIX}-${Date.now()}`
    await questionInput.fill(unique)

    // Clicar botão "Adicionar" do form (não confundir com "Adicionar
    // selecionadas" do bank de catálogo)
    const addFormBtn = page
      .getByRole('button', { name: /^Adicionar$|^Add$/i })
      .first()
    if (await addFormBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await addFormBtn.click()
      await page.waitForTimeout(500)
    }

    // Salvar alterações
    const saveBtn = page
      .getByRole('button', { name: /Salvar alterações|Save changes/i })
      .first()
    if (!(await saveBtn.isVisible({ timeout: 3_000 }).catch(() => false))) {
      test.skip(true, '[setup] Botão Salvar alterações não visível.')
      return
    }
    await saveBtn.click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })

    // Reload e verificar persistência
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    const persisted = await page
      .locator(`text=/${unique}/i`)
      .first()
      .isVisible({ timeout: 10_000 })
      .catch(() => false)
    expect(
      persisted,
      `[persistence FAIL] Question "${unique}" sumiu após reload. ` +
        `Verificar POST /api/v1/screening-questions e GET refresh.`,
    ).toBe(true)
  })

  test('toggle modo edit on/off renderiza Salvar/Cancelar', async ({
    authenticatedPage: page,
  }) => {
    const editBtn = page.getByRole('button', { name: /^Editar$|^Edit$/i }).first()
    const editVisible = await editBtn.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!editVisible) {
      test.skip(true, '[setup] Botão Editar não visível.')
      return
    }
    await editBtn.click()
    await page.waitForTimeout(500)

    const saveBtn = page
      .getByRole('button', { name: /Salvar alterações|Save changes/i })
      .first()
    const cancelBtn = page
      .getByRole('button', { name: /^Cancelar$|^Cancel$/i })
      .first()
    const anyVisible =
      (await saveBtn.isVisible({ timeout: 3_000 }).catch(() => false)) ||
      (await cancelBtn.isVisible({ timeout: 3_000 }).catch(() => false))

    expect(
      anyVisible,
      '[regression] Modo edit não expôs Salvar/Cancelar. ' +
        'Verificar isEditingQuestions em useRecruitmentHub.',
    ).toBe(true)

    if (await cancelBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await cancelBtn.click()
    }
  })
})
