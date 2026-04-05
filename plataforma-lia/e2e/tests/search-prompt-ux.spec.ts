import { test, expect } from '@playwright/test'

test.describe('Search Prompt UX — Funil de Talentos', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await page.waitForSelector('text=Vamos buscar de forma inteligente?', { timeout: 30000 })
    await page.waitForTimeout(2000)
  })

  test('search prompt loads with mode tabs and criteria tags', async ({ page }) => {
    await expect(page.locator('text=Linguagem Natural')).toBeVisible()
    await expect(page.locator('text=Similar')).toBeVisible()
    await expect(page.locator('text=Boolean')).toBeVisible()

    const textarea = page.locator('textarea')
    await expect(textarea).toBeVisible()
  })

  test('typing in search input shows criteria tags', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')
    await page.waitForTimeout(3000)

    await expect(page.locator('text=Cargo')).toBeVisible()
    await expect(page.locator('text=Localização')).toBeVisible()
  })

  test('autocomplete dropdown renders as separate section, not overlapping tags', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      const acBox = await autocomplete.boundingBox()
      expect(acBox).toBeTruthy()

      const tagsContainer = page.locator('text=Localização').first()
      const isTagsVisible = await tagsContainer.isVisible().catch(() => false)
      expect(isTagsVisible).toBe(false)

      const closeBtn = autocomplete.locator('button[title="Fechar lista"]')
      if (await closeBtn.isVisible()) {
        await closeBtn.click()
        await page.waitForTimeout(1000)

        await expect(page.locator('text=Cargo')).toBeVisible()
      }
    }
  })

  test('autocomplete closes and tags reappear with quality bar', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior')
    await page.waitForTimeout(4000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)

    if (isAutocompleteVisible) {
      const closeBtn = autocomplete.locator('button[title="Fechar lista"]')
      await closeBtn.click()
      await page.waitForTimeout(1000)
    }

    await expect(page.locator('text=Cargo')).toBeVisible()
    await expect(page.locator('text=Qualidade da busca')).toBeVisible()
  })

  test('assistente de busca button is visible in tags area', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Engenheiro de dados')
    await page.waitForTimeout(3000)

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')
    const isAutocompleteVisible = await autocomplete.isVisible().catch(() => false)
    if (isAutocompleteVisible) {
      const closeBtn = autocomplete.locator('button[title="Fechar lista"]')
      if (await closeBtn.isVisible()) {
        await closeBtn.click()
        await page.waitForTimeout(1000)
      }
    }

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
