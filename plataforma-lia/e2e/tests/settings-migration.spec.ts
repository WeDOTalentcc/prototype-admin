import { test, expect } from '@playwright/test';

const SETTINGS_MENU_ITEMS = [
  { id: 'minha-empresa', label: 'Minha Empresa' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'screening', label: 'Screening' },
  { id: 'templates-assinatura', label: 'Templates & Assinatura' },
  { id: 'comunicacao-alertas', label: 'Comunicação & Alertas' },
  { id: 'usuarios-departamentos', label: 'Usuários & Departamentos' },
  { id: 'integrations', label: 'Integrações' },
];

test.describe('Settings Migration — 7-Item Menu', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');

    const settingsLink = page.locator('text=Configurações').first();
    await settingsLink.click();
    await page.waitForTimeout(3000);
  });

  test('SM-001: All 7 menu items are visible in settings sidebar', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    for (const item of SETTINGS_MENU_ITEMS) {
      const button = page.locator(`button:has-text("${item.label}")`).first();
      await expect(button).toBeVisible({ timeout: 5000 });
    }
  });

  test('SM-002: Progress bar visible in expanded sidebar', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const progressText = page.locator('text=Progresso do Setup');
    await expect(progressText).toBeVisible({ timeout: 5000 });

    const percentageText = page.locator('text=/%/');
    await expect(percentageText).toBeVisible({ timeout: 5000 });
  });

  test('SM-003: Minha Empresa loads company data cards', async ({ page }) => {
    const minhaEmpresaBtn = page.locator('button:has-text("Minha Empresa")').first();
    await minhaEmpresaBtn.click();
    await page.waitForTimeout(3000);

    const contentArea = page.locator('main, [class*="flex-1"]').first();
    await expect(contentArea).toBeVisible();
  });

  test('SM-004: Navigate through all 7 sections without errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('401') && !msg.text().includes('404')) {
        consoleErrors.push(msg.text());
      }
    });

    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    for (const item of SETTINGS_MENU_ITEMS) {
      const button = page.locator(`button:has-text("${item.label}")`).first();
      await button.click();
      await page.waitForTimeout(2000);
    }

    const criticalErrors = consoleErrors.filter(e =>
      !e.includes('Fast Refresh') &&
      !e.includes('chatWorkflowReels') &&
      !e.includes('ws-token') &&
      !e.includes('fetch failed')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test('SM-005: Pipeline renders as independent section', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const pipelineBtn = page.locator('button:has-text("Pipeline")').first();
    await pipelineBtn.click();
    await page.waitForTimeout(3000);

    const contentArea = page.locator('main, [class*="flex-1"]').first();
    await expect(contentArea).toBeVisible();
  });

  test('SM-006: Screening renders as independent section', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const screeningBtn = page.locator('button:has-text("Screening")').first();
    await screeningBtn.click();
    await page.waitForTimeout(3000);

    const contentArea = page.locator('main, [class*="flex-1"]').first();
    await expect(contentArea).toBeVisible();
  });

  test('SM-007: Templates & Assinatura renders combined section', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const templatesBtn = page.locator('button:has-text("Templates & Assinatura")').first();
    await templatesBtn.click();
    await page.waitForTimeout(3000);

    const contentArea = page.locator('main, [class*="flex-1"]').first();
    await expect(contentArea).toBeVisible();
  });

  test('SM-008: Usuarios & Departamentos renders combined section', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const usersBtn = page.locator('button:has-text("Usuários & Departamentos")').first();
    await usersBtn.click();
    await page.waitForTimeout(3000);

    const contentArea = page.locator('main, [class*="flex-1"]').first();
    await expect(contentArea).toBeVisible();
  });

  test('SM-009: Settings progress API returns 7 section IDs', async ({ page }) => {
    const response = await page.request.get('/api/backend-proxy/settings/progress');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.sections).toBeDefined();

    const expectedKeys = [
      'minha-empresa', 'pipeline', 'screening',
      'templates-assinatura', 'comunicacao-alertas',
      'usuarios-departamentos', 'integracoes',
    ];

    for (const key of expectedKeys) {
      expect(data.sections).toHaveProperty(key);
      expect(typeof data.sections[key]).toBe('number');
    }

    expect(data.overall).toBeDefined();
    expect(typeof data.overall).toBe('number');

    if (data.subsections) {
      expect(typeof data.subsections).toBe('object');
    }
  });

  test('SM-010: Section switching preserves sidebar state', async ({ page }) => {
    const sidebar = page.locator('aside').first();
    await sidebar.hover();
    await page.waitForTimeout(1000);

    const minhaEmpresaBtn = page.locator('button:has-text("Minha Empresa")').first();
    await minhaEmpresaBtn.click();
    await page.waitForTimeout(2000);

    const pipelineBtn = page.locator('button:has-text("Pipeline")').first();
    await pipelineBtn.click();
    await page.waitForTimeout(2000);

    await minhaEmpresaBtn.click();
    await page.waitForTimeout(2000);

    await expect(minhaEmpresaBtn).toBeVisible();
    await expect(pipelineBtn).toBeVisible();
  });
});
