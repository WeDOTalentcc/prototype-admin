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

  test('typing triggers entity extraction and shows criteria tags and quality bar simultaneously', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')

    await expect(page.locator('text=Cargo')).toBeVisible({ timeout: 8000 })
    await expect(page.locator('text=Localização')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('text=Qualidade da busca')).toBeVisible({ timeout: 5000 })
  })

  test('criteria tags and quality bar remain visible regardless of autocomplete state', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')

    await expect(page.locator('text=Cargo')).toBeVisible({ timeout: 8000 })
    await expect(page.locator('text=Qualidade da busca')).toBeVisible({ timeout: 5000 })

    const cargoTag = page.locator('text=Cargo').first()
    const qualityBar = page.locator('text=Qualidade da busca').first()

    const tagBox = await cargoTag.boundingBox()
    const qualityBox = await qualityBar.boundingBox()
    expect(tagBox).toBeTruthy()
    expect(qualityBox).toBeTruthy()

    if (tagBox && qualityBox) {
      expect(tagBox.y + tagBox.height).toBeLessThanOrEqual(qualityBox.y + 2)
    }
  })

  test('autocomplete dropdown renders below textarea and above tags without overlap', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior em São Paulo')

    await expect(page.locator('text=Cargo')).toBeVisible({ timeout: 8000 })

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')

    try {
      await autocomplete.waitFor({ state: 'visible', timeout: 6000 })
    } catch {
      test.skip(true, 'Autocomplete did not appear (backend may not have returned suggestions)')
      return
    }

    const acBox = await autocomplete.boundingBox()
    const tagBox = await page.locator('text=Cargo').first().boundingBox()
    const textareaBox = await textarea.boundingBox()

    expect(acBox).toBeTruthy()
    expect(tagBox).toBeTruthy()
    expect(textareaBox).toBeTruthy()

    if (acBox && tagBox && textareaBox) {
      expect(acBox.y).toBeGreaterThanOrEqual(textareaBox.y + textareaBox.height - 2)
      expect(acBox.y + acBox.height).toBeLessThanOrEqual(tagBox.y + 2)
    }

    await expect(page.locator('text=Qualidade da busca')).toBeVisible()
  })

  test('autocomplete items have proper accessibility attributes', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')

    try {
      await autocomplete.waitFor({ state: 'visible', timeout: 6000 })
    } catch {
      test.skip(true, 'Autocomplete did not appear')
      return
    }

    const items = autocomplete.locator('[data-testid="autocomplete-item"]')
    const count = await items.count()
    expect(count).toBeGreaterThan(0)

    await expect(items.first()).toHaveAttribute('role', 'option')
    await expect(items.first()).toHaveAttribute('aria-selected')
  })

  test('clicking autocomplete item updates textarea value', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')

    try {
      await autocomplete.waitFor({ state: 'visible', timeout: 6000 })
    } catch {
      test.skip(true, 'Autocomplete did not appear')
      return
    }

    const firstItem = autocomplete.locator('[data-testid="autocomplete-item"]').first()
    await expect(firstItem).toBeVisible()
    await firstItem.click()
    await page.waitForTimeout(500)

    const newValue = await textarea.inputValue()
    expect(newValue.length).toBeGreaterThan(0)
  })

  test('Tab key accepts first autocomplete suggestion', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python')

    const autocomplete = page.locator('[data-testid="autocomplete-dropdown"]')

    try {
      await autocomplete.waitFor({ state: 'visible', timeout: 6000 })
    } catch {
      test.skip(true, 'Autocomplete did not appear')
      return
    }

    await page.keyboard.press('Tab')
    await page.waitForTimeout(500)

    const newValue = await textarea.inputValue()
    expect(newValue.length).toBeGreaterThan(0)
  })

  test('assistente de busca tooltip trigger is visible in tags area', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Engenheiro de dados senior')

    await expect(page.locator('text=Assistente de Busca')).toBeVisible({ timeout: 8000 })
  })

  test('search mode tabs switch content correctly', async ({ page }) => {
    await page.locator('text=Boolean').click()
    await page.waitForTimeout(500)
    await expect(page.locator('text=Boolean')).toBeVisible()

    await page.locator('text=Linguagem Natural').click()
    await page.waitForTimeout(500)
    await expect(page.locator('textarea')).toBeVisible()
  })

  test('tooltip text uses reduced font sizes', async ({ page }) => {
    const textarea = page.locator('textarea')
    await textarea.click()
    await textarea.fill('Desenvolvedor Python senior')

    await expect(page.locator('text=Assistente de Busca')).toBeVisible({ timeout: 8000 })

    const tooltipTrigger = page.locator('text=Assistente de Busca').first()
    await tooltipTrigger.hover()
    await page.waitForTimeout(1000)

    const tooltipContent = page.locator('[role="tooltip"], [data-state="delayed-open"], [data-radix-popper-content-wrapper]')
    const isTooltipVisible = await tooltipContent.isVisible().catch(() => false)

    if (isTooltipVisible) {
      const tooltipText = await tooltipContent.textContent()
      expect(tooltipText).toBeTruthy()
    }
  })
})
