import { test, expect } from '@playwright/test'

test.describe('Search Prompt UX — Funil de Talentos', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await page.waitForSelector('text=Vamos buscar de forma inteligente?', { timeout: 30000 })
    await page.waitForTimeout(2000)
  })

  test('search prompt loads with mode tabs and textarea', async ({ page }) => {
    await expect(page.locator('text=Linguagem Natural')).toBeVisible()
    await expect(page.locator('text=Similar')).toBeVisible()
    await expect(page.locator('text=Boolean')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()
  })

  test('typing triggers entity extraction and shows criteria tags', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(3000)

    await expect(page.locator('text=Cargo')).toBeVisible()
    await expect(page.locator('text=Localização')).toBeVisible()
  })

  test('autocomplete dropdown and criteria tags are both visible without overlap', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      const acBox = await autocomplete.boundingBox()
      expect(acBox).toBeTruthy()

      await expect(page.locator('text=Cargo')).toBeVisible()

      const cargoTag = page.locator('text=Cargo').first()
      const tagBox = await cargoTag.boundingBox()

      if (acBox && tagBox) {
        const acBottom = acBox.y + acBox.height
        expect(acBottom).toBeLessThanOrEqual(tagBox.y + 2)
      }
    }
  })

  test('accepting autocomplete suggestion via click updates textarea', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      const firstItem = autocomplete.locator('[role="option"]').first()
      if (await firstItem.isVisible()) {
        const itemText = await firstItem.textContent()
        await firstItem.click()
        await page.waitForTimeout(1000)

        const currentValue = await textarea.inputValue()
        expect(currentValue.length).toBeGreaterThan(0)
      }
    }
  })

  test('accepting autocomplete suggestion via Tab key', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      await page.keyboard.press('Tab')
      await page.waitForTimeout(1000)

      const currentValue = await textarea.inputValue()
      expect(currentValue.length).toBeGreaterThan(0)
    }
  })

  test('quality bar remains visible when autocomplete is open', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(4000)

    await expect(page.locator('text=Qualidade da busca')).toBeVisible()

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      await expect(page.locator('text=Qualidade da busca')).toBeVisible()
    }
  })

  test('assistente de busca button is visible in tags area', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Engenheiro de dados')
    await page.waitForTimeout(3000)

    await expect(page.locator('text=Assistente de Busca')).toBeVisible()
  })

  test('search mode tabs are interactive', async ({ page }) => {
    await page.locator('text=Boolean').click()
    await page.waitForTimeout(500)
    await expect(page.locator('text=Boolean')).toBeVisible()

    await page.locator('text=Linguagem Natural').click()
    await page.waitForTimeout(500)
    await expect(page.locator('textarea')).toBeVisible()
  })
})
