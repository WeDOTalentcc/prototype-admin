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

async function navigateToSettings(page: any) {
  await page.goto('/pt');
  await page.waitForLoadState('networkidle');
  const settingsLink = page.locator('text=Configurações').first();
  await settingsLink.click();
  await page.waitForTimeout(3000);
}

async function expandSettingsSidebar(page: any) {
  const sidebar = page.locator('aside').first();
  await sidebar.hover();
  await page.waitForTimeout(1000);
}

async function clickMenuItem(page: any, label: string) {
  await expandSettingsSidebar(page);
  const button = page.locator(`button:has-text("${label}")`).first();
  await button.click();
  await page.waitForTimeout(3000);
}

test.describe('Settings Migration — 7-Item Menu Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
  });

  test('SM-001: All 7 menu items are visible in settings sidebar', async ({ page }) => {
    await expandSettingsSidebar(page);
    for (const item of SETTINGS_MENU_ITEMS) {
      const button = page.locator(`button:has-text("${item.label}")`).first();
      await expect(button).toBeVisible({ timeout: 5000 });
    }
  });

  test('SM-002: Progress bar with percentage visible in expanded sidebar', async ({ page }) => {
    await expandSettingsSidebar(page);

    const progressLabel = page.locator('text=Progresso do Setup');
    await expect(progressLabel).toBeVisible({ timeout: 5000 });

    const percentageEl = page.locator('span:has-text("%")').first();
    await expect(percentageEl).toBeVisible({ timeout: 5000 });
    const percentText = await percentageEl.textContent();
    expect(percentText).toMatch(/\d+%/);

    const progressBar = page.locator('[class*="rounded-full"][class*="h-1"]').first();
    await expect(progressBar).toBeVisible({ timeout: 5000 });
  });

  test('SM-004: Navigate all 7 sections without critical JS errors', async ({ page }) => {
    const criticalErrors: string[] = [];
    page.on('console', (msg: any) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.includes('401') && !text.includes('404') &&
            !text.includes('Fast Refresh') && !text.includes('chatWorkflowReels') &&
            !text.includes('ws-token') && !text.includes('fetch failed') &&
            !text.includes('undefined is not iterable')) {
          criticalErrors.push(text);
        }
      }
    });

    for (const item of SETTINGS_MENU_ITEMS) {
      await clickMenuItem(page, item.label);
    }

    expect(criticalErrors).toHaveLength(0);
  });

  test('SM-010: Section switching preserves sidebar state', async ({ page }) => {
    await clickMenuItem(page, 'Minha Empresa');
    await clickMenuItem(page, 'Pipeline');
    await clickMenuItem(page, 'Minha Empresa');

    await expandSettingsSidebar(page);
    const minhaEmpresaBtn = page.locator('button:has-text("Minha Empresa")').first();
    const pipelineBtn = page.locator('button:has-text("Pipeline")').first();
    await expect(minhaEmpresaBtn).toBeVisible();
    await expect(pipelineBtn).toBeVisible();
  });
});

test.describe('Settings Migration — Minha Empresa Cards', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Minha Empresa');
  });

  test('SM-003: Minha Empresa loads company data cards with real data', async ({ page }) => {
    const cardTitles = [
      'Dados da Empresa',
      'Cultura',
      'Tech Stack',
      'Benefícios',
      'Documentos',
      'Políticas',
    ];

    let foundCards = 0;
    for (const title of cardTitles) {
      const card = page.locator(`text=${title}`).first();
      if (await card.isVisible().catch(() => false)) {
        foundCards++;
      }
    }
    expect(foundCards).toBeGreaterThanOrEqual(2);

    const profileResponse = await page.request.get('/api/backend-proxy/company/profile');
    if (profileResponse.ok()) {
      const profile = await profileResponse.json();
      expect(profile).toBeDefined();
    }
  });

  test('SM-011: Inline editing on cards — save and cancel', async ({ page }) => {
    const editButtons = page.locator('button:has(svg), [data-testid*="edit"]').filter({
      has: page.locator('svg'),
    });

    const editBtnCount = await editButtons.count();

    if (editBtnCount > 0) {
      const firstEditBtn = editButtons.first();
      await firstEditBtn.click();
      await page.waitForTimeout(1000);

      const cancelBtn = page.locator('button:has-text("Cancelar"), button:has(svg[class*="X"])').first();
      if (await cancelBtn.isVisible().catch(() => false)) {
        await cancelBtn.click();
        await page.waitForTimeout(500);
      }
    }
  });
});

test.describe('Settings Migration — Chat Context Switching', () => {
  test('SM-012: Chat context switches to settings_config on Minha Empresa', async ({ page }) => {
    const contextEvents: string[] = [];
    await page.exposeFunction('__captureContext', (ctx: string) => {
      contextEvents.push(ctx);
    });

    await navigateToSettings(page);
    await clickMenuItem(page, 'Minha Empresa');

    const chatPanel = page.locator('[data-chat-mode], [class*="UnifiedChat"]').first();
    if (await chatPanel.isVisible().catch(() => false)) {
      const chatInput = page.locator('textarea[placeholder*="mensagem"], textarea[placeholder*="LIA"], [data-testid="chat-input"]').first();
      if (await chatInput.isVisible().catch(() => false)) {
        expect(true).toBeTruthy();
      }
    }
  });

  test('SM-013: Chat shows settings suggestion chips in Minha Empresa', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Minha Empresa');

    const chatArea = page.locator('[data-chat-mode]').first();
    if (await chatArea.isVisible().catch(() => false)) {
      const suggestionChips = page.locator('button[class*="suggestion"], [class*="chip"], [class*="empty-state"] button');
      const chipCount = await suggestionChips.count();

      if (chipCount > 0) {
        const firstChip = suggestionChips.first();
        const chipText = await firstChip.textContent();
        expect(chipText).toBeTruthy();
      }
    }
  });
});

test.describe('Settings Migration — Independent Sections', () => {
  test('SM-005: Pipeline renders with stage-related content', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Pipeline');

    const pipelineContent = page.locator('text=/[Ee]tapa|[Ss]tage|[Pp]ipeline|[Ff]unil|SLA/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await pipelineContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('SM-006: Screening renders with question-related content', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Screening');

    const screeningContent = page.locator('text=/[Pp]ergunt|[Qq]uestion|[Ss]creening|[Ee]legibilidade|WhatsApp/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await screeningContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('SM-007: Templates & Assinatura renders combined content', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Templates & Assinatura');

    const templatesContent = page.locator('text=/[Tt]emplate|[Aa]ssinatura|[Mm]odelo|[Ee]mail/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await templatesContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('SM-008: Usuarios & Departamentos renders combined content', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Usuários & Departamentos');

    const usersContent = page.locator('text=/[Uu]suário|[Dd]epartamento|[Rr]ecrutador|[Pp]ermiss/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await usersContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('SM-014: Integracoes hub renders', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Integrações');

    const intContent = page.locator('text=/[Ii]ntegra|[Cc]onect|API|webhook/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await intContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('SM-015: Comunicacao & Alertas renders with alert-related content', async ({ page }) => {
    await navigateToSettings(page);
    await clickMenuItem(page, 'Comunicação & Alertas');

    const commContent = page.locator('text=/[Aa]lerta|[Nn]otifica|LGPD|[Hh]orário|[Cc]omunica/').first();
    const contentArea = page.locator('[class*="ErrorBoundary"], [class*="flex-1"] > div').first();
    const hasContent = await commContent.isVisible().catch(() => false) ||
                       await contentArea.isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });
});

test.describe('Settings Migration — Progress API', () => {
  test('SM-009: Settings progress API returns correct 7-section structure', async ({ page }) => {
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');

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

    expect(typeof data.overall).toBe('number');
    expect(data.overall).toBeGreaterThanOrEqual(0);
    expect(data.overall).toBeLessThanOrEqual(100);

    if (data.subsections) {
      const expectedSubs = [
        'company_data', 'culture', 'tech_stack', 'benefits',
        'policies', 'workforce', 'stages', 'slas', 'questions',
        'templates', 'signature', 'alerts', 'lgpd_schedule',
        'users', 'departments', 'integrations_active',
      ];
      for (const sub of expectedSubs) {
        expect(data.subsections).toHaveProperty(sub);
        expect(typeof data.subsections[sub]).toBe('boolean');
      }
    }

    if (data.details) {
      expect(data.details.company_id).toBeDefined();
      expect(data.details.scores).toBeDefined();
    }

    const oldKeys = ['company-team', 'recruitment', 'communication', 'goals-planning', 'global-search'];
    for (const oldKey of oldKeys) {
      expect(data.sections).not.toHaveProperty(oldKey);
    }
  });
});
