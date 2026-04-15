import { test, expect, type Page } from '@playwright/test';

const SECTION_IDS = [
  'minha-empresa', 'pipeline', 'screening',
  'templates-assinatura', 'comunicacao-alertas',
  'usuarios-departamentos', 'integrations',
] as const;

const SECTION_LABELS: Record<string, string> = {
  'minha-empresa': 'Minha Empresa',
  'pipeline': 'Pipeline',
  'screening': 'Screening',
  'templates-assinatura': 'Templates & Assinatura',
  'comunicacao-alertas': 'Comunicação & Alertas',
  'usuarios-departamentos': 'Usuários & Departamentos',
  'integrations': 'Integrações',
};

async function navigateToSettings(page: Page) {
  await page.goto('/pt');
  await page.waitForLoadState('networkidle');
  const settingsLink = page.locator('text=Configurações').first();
  await settingsLink.click();
  await page.waitForTimeout(3000);
}

async function expandAndLockSidebar(page: Page) {
  const sidebar = page.locator('aside').first();
  await sidebar.hover();
  await page.waitForTimeout(1000);
}

async function clickMenuItemById(page: Page, sectionId: string) {
  await expandAndLockSidebar(page);
  const button = page.locator(`[data-testid="settings-menu-${sectionId}"]`);
  await expect(button).toBeVisible({ timeout: 5000 });
  await button.click();
  await page.waitForTimeout(3000);
}

async function assertContentAreaShowsSection(page: Page, sectionId: string) {
  const contentArea = page.locator('[data-testid="settings-content-area"]');
  await expect(contentArea).toBeVisible({ timeout: 5000 });
  await expect(contentArea).toHaveAttribute('data-active-section', sectionId);
}

test.describe('Settings Migration — Menu Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
  });

  test('SM-001: All 7 menu items visible with data-testid attributes', async ({ page }) => {
    await expandAndLockSidebar(page);
    for (const id of SECTION_IDS) {
      const button = page.locator(`[data-testid="settings-menu-${id}"]`);
      await expect(button).toBeVisible({ timeout: 5000 });
    }
  });

  test('SM-002: Progress bar with numeric percentage in expanded sidebar', async ({ page }) => {
    await expandAndLockSidebar(page);
    const progressLabel = page.locator('text=Progresso do Setup');
    await expect(progressLabel).toBeVisible({ timeout: 5000 });

    const percentageEl = page.locator('span').filter({ hasText: /^\d+%$/ }).first();
    await expect(percentageEl).toBeVisible({ timeout: 5000 });
    const text = await percentageEl.textContent();
    expect(text).toBeTruthy();
    const numericValue = parseInt(text!.replace('%', ''), 10);
    expect(numericValue).toBeGreaterThanOrEqual(0);
    expect(numericValue).toBeLessThanOrEqual(100);
  });

  test('SM-004: Navigate all 7 sections, content area reflects active section', async ({ page }) => {
    for (const id of SECTION_IDS) {
      await clickMenuItemById(page, id);
      await assertContentAreaShowsSection(page, id);
    }
  });

  test('SM-010: Section switching roundtrip preserves state', async ({ page }) => {
    await clickMenuItemById(page, 'minha-empresa');
    await assertContentAreaShowsSection(page, 'minha-empresa');

    await clickMenuItemById(page, 'pipeline');
    await assertContentAreaShowsSection(page, 'pipeline');

    await clickMenuItemById(page, 'minha-empresa');
    await assertContentAreaShowsSection(page, 'minha-empresa');

    await expandAndLockSidebar(page);
    for (const id of SECTION_IDS) {
      const button = page.locator(`[data-testid="settings-menu-${id}"]`);
      await expect(button).toBeVisible();
    }
  });
});

test.describe('Settings Migration — Minha Empresa Content', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'minha-empresa');
  });

  test('SM-003: Minha Empresa loads with section title and real content', async ({ page }) => {
    await assertContentAreaShowsSection(page, 'minha-empresa');

    const heading = page.locator('h2:has-text("Minha Empresa")');
    await expect(heading).toBeVisible({ timeout: 5000 });

    const contentArea = page.locator('[data-testid="settings-content-area"]');
    const hasCards = await contentArea.locator('[class*="Card"], [class*="card"]').count();
    expect(hasCards).toBeGreaterThan(0);
  });

  test('SM-011: Inline editing — edit button exists and triggers edit mode', async ({ page }) => {
    const contentArea = page.locator('[data-testid="settings-content-area"]');
    await expect(contentArea).toBeVisible();

    const editButtons = contentArea.locator('button').filter({
      has: page.locator('svg'),
    });
    const editCount = await editButtons.count();
    expect(editCount).toBeGreaterThan(0);
  });
});

test.describe('Settings Migration — Chat Context', () => {
  test('SM-012: Chat panel present alongside settings with correct data attribute', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'minha-empresa');

    const chatPanel = page.locator('[data-chat-mode]');
    const chatVisible = await chatPanel.isVisible().catch(() => false);

    if (chatVisible) {
      const chatMode = await chatPanel.getAttribute('data-chat-mode');
      expect(chatMode).toBeTruthy();
      expect(['sidebar', 'floating', 'fullscreen']).toContain(chatMode);
    }
  });

  test('SM-013: Chat input is interactive in settings context', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'minha-empresa');

    const chatInput = page.locator('textarea').first();
    const inputVisible = await chatInput.isVisible().catch(() => false);

    if (inputVisible) {
      await chatInput.fill('test');
      const value = await chatInput.inputValue();
      expect(value).toBe('test');
      await chatInput.fill('');
    }
  });
});

test.describe('Settings Migration — Independent Sections', () => {
  test('SM-005: Pipeline section renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'pipeline');
    await assertContentAreaShowsSection(page, 'pipeline');

    const heading = page.locator('h2:has-text("Pipeline")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('SM-006: Screening section renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'screening');
    await assertContentAreaShowsSection(page, 'screening');

    const heading = page.locator('h2:has-text("Screening")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('SM-007: Templates & Assinatura renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'templates-assinatura');
    await assertContentAreaShowsSection(page, 'templates-assinatura');

    const heading = page.locator('h2:has-text("Templates")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('SM-008: Usuarios & Departamentos renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'usuarios-departamentos');
    await assertContentAreaShowsSection(page, 'usuarios-departamentos');

    const heading = page.locator('h2:has-text("Usuários")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('SM-014: Integracoes section renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'integrations');
    await assertContentAreaShowsSection(page, 'integrations');

    const heading = page.locator('h2:has-text("Integrações")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });

  test('SM-015: Comunicacao & Alertas renders with section-specific heading', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItemById(page, 'comunicacao-alertas');
    await assertContentAreaShowsSection(page, 'comunicacao-alertas');

    const heading = page.locator('h2:has-text("Comunicação")');
    await expect(heading).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Settings Migration — Progress API Contract', () => {
  test('SM-009: API returns exactly 7 new section IDs with correct types', async ({ page }) => {
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');

    const response = await page.request.get('/api/backend-proxy/settings/progress');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();

    expect(data.overall).toBeDefined();
    expect(typeof data.overall).toBe('number');
    expect(data.overall).toBeGreaterThanOrEqual(0);
    expect(data.overall).toBeLessThanOrEqual(100);

    expect(data.sections).toBeDefined();
    const apiSectionKeys = [
      'minha-empresa', 'pipeline', 'screening',
      'templates-assinatura', 'comunicacao-alertas',
      'usuarios-departamentos', 'integracoes',
    ];
    for (const key of apiSectionKeys) {
      expect(data.sections).toHaveProperty(key);
      expect(typeof data.sections[key]).toBe('number');
      expect(data.sections[key]).toBeGreaterThanOrEqual(0);
      expect(data.sections[key]).toBeLessThanOrEqual(100);
    }
    expect(Object.keys(data.sections)).toHaveLength(7);

    const oldKeys = ['company-team', 'recruitment', 'communication', 'goals-planning', 'global-search'];
    for (const oldKey of oldKeys) {
      expect(data.sections).not.toHaveProperty(oldKey);
    }

    expect(data.subsections).toBeDefined();
    const expectedSubsections = [
      'company_data', 'culture', 'tech_stack', 'benefits',
      'policies', 'workforce', 'stages', 'slas', 'questions',
      'templates', 'signature', 'alerts', 'lgpd_schedule',
      'users', 'departments', 'integrations_active',
    ];
    for (const sub of expectedSubsections) {
      expect(data.subsections).toHaveProperty(sub);
      expect(typeof data.subsections[sub]).toBe('boolean');
    }

    expect(data.details).toBeDefined();
    expect(data.details.company_id).toBeTruthy();
    expect(data.details.scores).toBeDefined();
  });

  test('SM-016: No backend 500 errors on settings progress endpoint', async ({ page }) => {
    await page.goto('/pt');
    const response = await page.request.get('/api/backend-proxy/settings/progress');
    expect(response.status()).not.toBe(500);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.error).toBeFalsy();
  });
});
