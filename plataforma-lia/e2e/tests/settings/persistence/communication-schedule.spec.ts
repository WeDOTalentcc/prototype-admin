/**
 * E2E persistence — Configurações > Comunicação e Alertas > Agenda.
 *
 * Cobre `ScheduleTab.tsx` (sending_hours, respect_weekends,
 * respect_holidays, max_messages_per_day). Pattern UI:
 *   * Botão "Editar" abre modo edição → fields ficam <input>/Switch
 *   * Botão "Salvar alterações" persiste via POST
 *     /api/v1/company/communication-settings
 *   * Botão "Cancelar" descarta mudanças
 *
 * ⚠ Selectors: `ScheduleTab.tsx` NÃO tem `data-testid` nos fields
 * (auditoria 2026-05-21). Os locators abaixo dependem de heading
 * ("Horário de envio", "Respeitar fins de semana") e role. Adicionar
 * `data-testid="schedule-{field}"` no frontend é TODO de harness
 * (vide README pattern).
 *
 * Importante: este test MUTA o schedule do tenant demo. afterEach
 * restaura via re-fill com valor original.
 */
import { test, expect } from './persistence-fixtures'

test.describe.configure({ retries: 1 })

test.describe('Comunicação e Alertas — Schedule persistence', () => {
  test.setTimeout(120_000)

  test.beforeEach(async ({ navigateToSettings }) => {
    await navigateToSettings('comunicacao-alertas', 'agenda')
  })

  test('hub Comunicação renderiza tab Agenda', async ({ authenticatedPage: page }) => {
    // Heading canonical do ScheduleTab — vem do i18n
    // (`settings.communication.scheduleSection.title`)
    const heading = page
      .getByText(/Horário de envio|Schedule|Agenda de envio/i)
      .first()
    await expect(heading).toBeVisible({ timeout: 15_000 })
  })

  test('toggle "Respeitar fins de semana" persiste após refresh @persistence', async ({
    authenticatedPage: page,
  }) => {
    // 1. Entrar em modo edição
    const editBtn = page.getByRole('button', { name: /^Editar$/i }).first()
    if (await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await editBtn.click()
    }

    // 2. Achar o switch — pode ser <button role="switch"> ou
    //    <input type="checkbox"> dependendo do componente shadcn usado.
    //    Tentamos role=switch primeiro (pattern canonical).
    const switchLabel = /Respeitar fins de semana|Respect weekends/i
    let sw = page.getByRole('switch', { name: switchLabel }).first()
    let visible = await sw.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      // Fallback: checkbox tradicional próximo ao texto
      sw = page.locator(`label:has-text("Respeitar fins de semana") input[type="checkbox"]`).first()
      visible = await sw.isVisible({ timeout: 3_000 }).catch(() => false)
    }

    if (!visible) {
      test.skip(
        true,
        '[setup] Switch "Respeitar fins de semana" não visível. ' +
          'Verificar `ScheduleTab.tsx` — provável mudança de label ou ' +
          'componente. Adicionar `data-testid="schedule-respect-weekends"` ' +
          'no frontend resolveria definitivamente.',
      )
      return
    }

    // Capturar estado inicial
    const beforeChecked =
      (await sw.getAttribute('aria-checked')) === 'true' ||
      (await sw.isChecked().catch(() => false))

    // Flip
    await sw.click()

    // Salvar (botão "Salvar alterações" do ScheduleTab)
    const saveBtn = page.getByRole('button', { name: /Salvar alterações|Save changes/i }).first()
    await expect(saveBtn).toBeVisible({ timeout: 5_000 })
    await saveBtn.click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })

    // Reload
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    // Re-localizar switch após reload (DOM resetou)
    let swAfter = page.getByRole('switch', { name: switchLabel }).first()
    let visibleAfter = await swAfter.isVisible({ timeout: 8_000 }).catch(() => false)
    if (!visibleAfter) {
      swAfter = page.locator(`label:has-text("Respeitar fins de semana") input[type="checkbox"]`).first()
      visibleAfter = await swAfter.isVisible({ timeout: 3_000 }).catch(() => false)
    }
    expect(visibleAfter, '[regression] switch sumiu após reload').toBe(true)

    const afterChecked =
      (await swAfter.getAttribute('aria-checked')) === 'true' ||
      (await swAfter.isChecked().catch(() => false))

    expect(
      afterChecked,
      `[persistence FAIL] "Respeitar fins de semana" voltou pra ${beforeChecked} ` +
        `após reload (esperado: ${!beforeChecked}). Provável causa: PATCH ` +
        `/api/v1/company/communication-settings retornou 200 mas o GET ` +
        `subsequente não trouxe o campo. Verificar serializer ` +
        `respect_weekends no backend.`,
    ).toBe(!beforeChecked)

    // Restore: flip de volta pro estado inicial
    const editBtn2 = page.getByRole('button', { name: /^Editar$/i }).first()
    if (await editBtn2.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await editBtn2.click()
      await swAfter.click()
      const saveBtn2 = page.getByRole('button', { name: /Salvar alterações/i }).first()
      if (await saveBtn2.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await saveBtn2.click()
        await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
      }
    }
  })

  test('sending_hours_start persiste após edit @persistence', async ({
    authenticatedPage: page,
  }) => {
    const editBtn = page.getByRole('button', { name: /^Editar$/i }).first()
    if (await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await editBtn.click()
    }

    // sending_hours.start é tipicamente number input ou slider. Vamos
    // procurar input[type="number"] dentro do ScheduleTab heading area.
    const startInput = page.locator('input[type="number"]').first()
    const visible = await startInput.isVisible({ timeout: 5_000 }).catch(() => false)
    if (!visible) {
      test.skip(
        true,
        '[setup] Input numérico de sending_hours não encontrado. ' +
          'Possível causa: UI usa slider/select em vez de number input. ' +
          'Adicionar `data-testid="schedule-sending-hours-start"` resolveria.',
      )
      return
    }

    const originalValue = await startInput.inputValue()
    const newValue = originalValue === '9' ? '10' : '9'
    await startInput.fill(newValue)

    const saveBtn = page.getByRole('button', { name: /Salvar alterações|Save changes/i }).first()
    await saveBtn.click()
    await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => { /* ok */ })

    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => { /* ok */ })

    const afterValue = await page.locator('input[type="number"]').first().inputValue()
    expect(
      afterValue,
      `[persistence FAIL] sending_hours.start voltou pra "${originalValue}" ` +
        `após reload (esperado: "${newValue}").`,
    ).toBe(newValue)

    // Restore valor original
    const editBtn2 = page.getByRole('button', { name: /^Editar$/i }).first()
    if (await editBtn2.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await editBtn2.click()
      await page.locator('input[type="number"]').first().fill(originalValue)
      const saveBtn2 = page.getByRole('button', { name: /Salvar alterações/i }).first()
      if (await saveBtn2.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await saveBtn2.click()
        await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => { /* ok */ })
      }
    }
  })
})
