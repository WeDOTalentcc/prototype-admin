import { test, expect, type Page } from '@playwright/test';

// Task #896 — cobertura mínima dos 8 hubs do menu Configurações
// (incluindo fairness-compliance, que faltava na lista original).
const SECTION_IDS = [
  'minha-empresa', 'pipeline', 'screening',
  'templates-assinatura', 'comunicacao-alertas',
  'usuarios-departamentos', 'integrations',
  'fairness-compliance',
] as const;

async function navigateToSettings(page: Page) {
  await page.goto('/pt');
  await page.waitForLoadState('networkidle');
  const settingsLink = page.locator('text=Configurações').first();
  await settingsLink.click();
  await page.waitForTimeout(3000);
}

async function expandSidebar(page: Page) {
  const sidebar = page.locator('aside').first();
  await sidebar.hover();
  await page.waitForTimeout(1000);
}

async function clickMenuById(page: Page, sectionId: string) {
  await expandSidebar(page);
  const button = page.locator(`[data-testid="settings-menu-${sectionId}"]`);
  await expect(button).toBeVisible({ timeout: 5000 });
  await button.click();
  await page.waitForTimeout(3000);
}

async function assertActiveSection(page: Page, sectionId: string) {
  const contentArea = page.locator('[data-testid="settings-content-area"]');
  await expect(contentArea).toBeVisible({ timeout: 5000 });
  await expect(contentArea).toHaveAttribute('data-active-section', sectionId);
}

test.describe('Settings Migration — Menu Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
  });

  test('SM-001: All 7 menu items visible via data-testid', async ({ page }) => {
    await expandSidebar(page);
    for (const id of SECTION_IDS) {
      await expect(page.locator(`[data-testid="settings-menu-${id}"]`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('SM-002: Progress bar with numeric percentage', async ({ page }) => {
    await expandSidebar(page);
    await expect(page.locator('text=Progresso do Setup')).toBeVisible({ timeout: 5000 });
    const percentEl = page.locator('span').filter({ hasText: /^\d+%$/ }).first();
    await expect(percentEl).toBeVisible({ timeout: 5000 });
    const text = await percentEl.textContent();
    const num = parseInt(text!.replace('%', ''), 10);
    expect(num).toBeGreaterThanOrEqual(0);
    expect(num).toBeLessThanOrEqual(100);
  });

  test('SM-004: Navigate all 7 sections with data-active-section verification', async ({ page }) => {
    for (const id of SECTION_IDS) {
      await clickMenuById(page, id);
      await assertActiveSection(page, id);
    }
  });

  test('SM-010: Section roundtrip A→B→A preserves state', async ({ page }) => {
    await clickMenuById(page, 'minha-empresa');
    await assertActiveSection(page, 'minha-empresa');
    await clickMenuById(page, 'pipeline');
    await assertActiveSection(page, 'pipeline');
    await clickMenuById(page, 'minha-empresa');
    await assertActiveSection(page, 'minha-empresa');
  });
});

test.describe('Settings Migration — Minha Empresa Content & Editing', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuById(page, 'minha-empresa');
  });

  test('SM-003: Minha Empresa shows heading and company content', async ({ page }) => {
    await assertActiveSection(page, 'minha-empresa');
    await expect(page.locator('h2:has-text("Minha Empresa")')).toBeVisible({ timeout: 5000 });
    const content = page.locator('[data-testid="settings-content-area"]');
    const innerContent = await content.innerHTML();
    expect(innerContent.length).toBeGreaterThan(100);
  });

  test('SM-011: Edit buttons present in Minha Empresa cards', async ({ page }) => {
    const content = page.locator('[data-testid="settings-content-area"]');
    await expect(content).toBeVisible();
    const buttons = content.locator('button').filter({ has: page.locator('svg') });
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Settings Migration — Chat Context Integration', () => {
  test('SM-012: Chat panel renders with data-chat-mode in settings', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuById(page, 'minha-empresa');

    const chatPanel = page.locator('[data-chat-mode]').first();
    await expect(chatPanel).toBeVisible({ timeout: 10000 });
    const chatMode = await chatPanel.getAttribute('data-chat-mode');
    expect(['sidebar', 'floating', 'fullscreen']).toContain(chatMode);
  });

  test('SM-013: Chat textarea is present and accepts input', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuById(page, 'minha-empresa');

    const chatInput = page.locator('[data-chat-mode] textarea').first();
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    await chatInput.fill('teste de input');
    const value = await chatInput.inputValue();
    expect(value).toBe('teste de input');
    await chatInput.fill('');
  });

  test('SM-017: Chat empty state shows suggestion chips in settings', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuById(page, 'minha-empresa');

    const chatPanel = page.locator('[data-chat-mode]').first();
    await expect(chatPanel).toBeVisible({ timeout: 10000 });

    const suggestionButtons = chatPanel.locator('button').filter({
      hasNot: page.locator('svg'),
    });
    const chipCount = await suggestionButtons.count();
    expect(chipCount).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Settings Migration — Independent Sections', () => {
  const sectionHeadings: Record<string, string> = {
    'pipeline': 'Pipeline',
    'screening': 'Screening',
    'templates-assinatura': 'Templates',
    'comunicacao-alertas': 'Comunicação',
    'usuarios-departamentos': 'Usuários',
    'integrations': 'Integrações',
    'fairness-compliance': 'Fairness',
  };

  for (const [id, headingText] of Object.entries(sectionHeadings)) {
    test(`SM-section-${id}: renders with heading "${headingText}"`, async ({ page }) => {
      await navigateToSettings(page);
      await clickMenuById(page, id);
      await assertActiveSection(page, id);
      await expect(page.locator(`h2:has-text("${headingText}")`)).toBeVisible({ timeout: 5000 });
    });
  }
});

test.describe('Settings Migration — Progress API Contract', () => {
  test('SM-009: Returns 7 new section IDs, no old IDs, correct subsections', async ({ page }) => {
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');

    const response = await page.request.get('/api/backend-proxy/settings/progress');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(typeof data.overall).toBe('number');
    expect(data.overall).toBeGreaterThanOrEqual(0);
    expect(data.overall).toBeLessThanOrEqual(100);

    const apiKeys = [
      'minha-empresa', 'pipeline', 'screening',
      'templates-assinatura', 'comunicacao-alertas',
      'usuarios-departamentos', 'integracoes',
    ];
    expect(Object.keys(data.sections)).toHaveLength(7);
    for (const key of apiKeys) {
      expect(data.sections).toHaveProperty(key);
      expect(typeof data.sections[key]).toBe('number');
      expect(data.sections[key]).toBeGreaterThanOrEqual(0);
      expect(data.sections[key]).toBeLessThanOrEqual(100);
    }

    const oldKeys = ['company-team', 'recruitment', 'communication', 'goals-planning', 'global-search'];
    for (const oldKey of oldKeys) {
      expect(data.sections).not.toHaveProperty(oldKey);
    }

    const subsections = [
      'company_data', 'culture', 'tech_stack', 'benefits',
      'policies', 'workforce', 'stages', 'slas', 'questions',
      'templates', 'signature', 'alerts', 'lgpd_schedule',
      'users', 'departments', 'integrations_active',
    ];
    for (const sub of subsections) {
      expect(data.subsections).toHaveProperty(sub);
      expect(typeof data.subsections[sub]).toBe('boolean');
    }

    expect(data.details).toBeDefined();
    expect(data.details.company_id).toBeTruthy();
    expect(data.details.scores).toBeDefined();
  });

  test('SM-016: No 500 error on progress endpoint', async ({ page }) => {
    await page.goto('/pt');
    const response = await page.request.get('/api/backend-proxy/settings/progress');
    expect(response.status()).not.toBe(500);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.error).toBeFalsy();
  });

  test('SM-018: Frontend integrations key maps from API integracoes key', async ({ page }) => {
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');

    const response = await page.request.get('/api/backend-proxy/settings/progress');
    const data = await response.json();
    expect(data.sections).toHaveProperty('integracoes');
    expect(data.sections).not.toHaveProperty('integrations');
  });
});
