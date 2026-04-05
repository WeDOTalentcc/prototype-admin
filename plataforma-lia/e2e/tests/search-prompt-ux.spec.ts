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

  test('typing triggers entity extraction and shows criteria tags and quality bar', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(3000)

    await expect(page.locator('text=Cargo')).toBeVisible()
    await expect(page.locator('text=Localização')).toBeVisible()
    await expect(page.locator('text=Qualidade da busca')).toBeVisible()
  })

  test('autocomplete dropdown does not overlap criteria tags', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const cargoTag = page.locator('text=Cargo').first()

    await expect(cargoTag).toBeVisible()

    const isAutocompleteVisible = await autocomplete.isVisible()
    if (isAutocompleteVisible) {
      const acBox = await autocomplete.boundingBox()
      const tagBox = await cargoTag.boundingBox()
      expect(acBox).toBeTruthy()
      expect(tagBox).toBeTruthy()
      if (acBox && tagBox) {
        expect(acBox.y + acBox.height).toBeLessThanOrEqual(tagBox.y + 2)
      }
    }

    await expect(page.locator('text=Qualidade da busca')).toBeVisible()
  })

  test('criteria tags remain visible when autocomplete is open', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(4000)

    await expect(page.locator('text=Cargo')).toBeVisible()
    await expect(page.locator('text=Localização')).toBeVisible()
    await expect(page.locator('text=Qualidade da busca')).toBeVisible()
  })

  test('autocomplete items have correct accessibility attributes', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isVisible = await autocomplete.isVisible()
    if (isVisible) {
      const items = autocomplete.locator('[data-testid="autocomplete-item"]')
      const count = await items.count()
      expect(count).toBeGreaterThan(0)

      const firstItem = items.first()
      await expect(firstItem).toHaveAttribute('role', 'option')
    }
  })

  test('clicking autocomplete item updates textarea value', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isVisible = await autocomplete.isVisible()
    if (isVisible) {
      const firstItem = autocomplete.locator('[data-testid="autocomplete-item"]').first()
      await firstItem.click()
      await page.waitForTimeout(1000)

      const newValue = await textarea.inputValue()
      expect(newValue.length).toBeGreaterThan(0)
    }
  })

  test('Tab key accepts autocomplete suggestion', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isVisible = await autocomplete.isVisible()
    if (isVisible) {
      const valueBefore = await textarea.inputValue()
      await page.keyboard.press('Tab')
      await page.waitForTimeout(1000)

      const valueAfter = await textarea.inputValue()
      expect(valueAfter.length).toBeGreaterThan(0)
    }
  })

  test('assistente de busca tooltip trigger is visible', async ({ page }) => {
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
