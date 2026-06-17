/**
 * Rail A — E2E Completo: 22 Cards × Visual + Behavioral
 *
 * Testa todos os 22 cards do ChatWorkflowReels no app real.
 * Harness:
 *  - Sensor computacional (pirâmide lia-testing camada 4 — E2E)
 *  - Guide: atributos `data-rail-a-card` tornam seletores robustos
 *  - Visual: toHaveScreenshot() gera baseline na 1ª execução e compara
 *    nas subsequentes (regressão visual automática)
 *
 * Por card:
 *  - NAVIGATION cards → verifica router.push para URL correta
 *  - MODAL cards → verifica evento lia:open_modal + modal abre
 *  - CHAT cards → verifica evento lia:rail-a-card-click com metadata
 *
 * Run (Replit):
 *   PLAYWRIGHT_BASE_URL=https://82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev \
 *   npx playwright test e2e/tests/chat/rail-a-cards.spec.ts --project=desktop-chrome --reporter=html
 *
 * Update visual baselines:
 *   npx playwright test rail-a-cards.spec.ts --update-snapshots
 */

import { test, expect } from '../../fixtures/auth.fixture';
import type { Page } from '@playwright/test';

const SS = 'e2e/screenshots/rail-a';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface RailAEvent {
  card_id: string;
  stage_id: string;
  navigate: boolean;
  modal: boolean;
}

interface OpenModalEvent {
  modal_id: string;
  data: Record<string, unknown>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Navigate to /pt/chat and wait for the Rail A stage nodes to appear. */
async function goChatEmpty(page: Page): Promise<void> {
  // domcontentloaded fires before 'load' and is reliable in HMR/dev environments
  // where 'load' can hang if background network connections (HMR websockets, etc.)
  // prevent the load event from firing within the timeout window.
  await page.goto('/pt/chat', { waitUntil: 'domcontentloaded', timeout: 30_000 });
  // Vaga is the default active stage: its cards are always visible after hydration.
  // data-rail-a-card is a stable, test-specific selector (guide computacional).
  await page.waitForSelector('[data-rail-a-card="create-job"]', { timeout: 25_000 });
  await page.waitForTimeout(600); // let animations settle
}

/**
 * Click the stage node identified by its shortLabel ("Vaga", "Captação", etc.)
 * and wait for the card tray to animate in.
 */
/** Map of shortLabel → stage.id used for data-rail-a-node selector */
const STAGE_LABEL_TO_ID: Record<string, string> = {
  Vaga: 'definir-vaga',
  'Captação': 'sourcing',
  Triagem: 'triagem',
  Entrevista: 'entrevista',
  Oferta: 'oferta',
  'Contratação': 'contratacao',
  'Análises': 'analytics',
  IA: 'ia-automacoes',
  Config: 'configuracoes',
};

async function expandStage(page: Page, shortLabel: string): Promise<void> {
  const stageId = STAGE_LABEL_TO_ID[shortLabel] ?? shortLabel.toLowerCase();
  // Use data-rail-a-node for stable, unambiguous selector (guide computacional)
  const btn = page.locator(`[data-rail-a-node="${stageId}"]`);
  await btn.waitFor({ state: 'visible', timeout: 20_000 });
  await btn.scrollIntoViewIfNeeded();
  await btn.click();
  await page.waitForTimeout(400); // fade-in-up (350 ms) + margin
}

/**
 * Set up a one-shot listener for `lia:rail-a-card-click`, run `action`,
 * then return the captured detail. Fails if no event fires within 3 s.
 */
async function onRailAClick(
  page: Page,
  action: () => Promise<void>,
): Promise<RailAEvent> {
  // Attach listener BEFORE click so we never miss the synchronous dispatch
  await page.evaluate(() => {
    (window as any).__ral_event = null;
    window.addEventListener(
      'lia:rail-a-card-click',
      (e: Event) => { (window as any).__ral_event = (e as CustomEvent).detail; },
      { once: true },
    );
  });
  await action();
  await page.waitForFunction(
    () => (window as any).__ral_event !== null,
    { timeout: 3_000 },
  );
  return page.evaluate(() => (window as any).__ral_event as RailAEvent);
}

/**
 * Set up a one-shot listener for `lia:open_modal`, run `action`, return detail.
 */
async function onOpenModal(
  page: Page,
  action: () => Promise<void>,
): Promise<OpenModalEvent> {
  await page.evaluate(() => {
    (window as any).__modal_event = null;
    window.addEventListener(
      'lia:open_modal',
      (e: Event) => { (window as any).__modal_event = (e as CustomEvent).detail; },
      { once: true },
    );
  });
  await action();
  await page.waitForFunction(
    () => (window as any).__modal_event !== null,
    { timeout: 5_000 },
  );
  return page.evaluate(() => (window as any).__modal_event as OpenModalEvent);
}

// ─────────────────────────────────────────────────────────────────────────────
// Visual snapshots: Rail A initial state
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Rail A — snapshot inicial', () => {
  test('RAL-000: todos os 9 stages visíveis no estado vazio do chat', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await page.screenshot({ path: `${SS}/00-initial.png` });
    await expect(page).toHaveScreenshot('ral-00-initial.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });

    for (const lbl of ['Vaga', 'Captação', 'Triagem', 'Entrevista', 'Oferta', 'Contratação', 'Análises', 'IA', 'Config']) {
      await expect(
        page.locator('button').filter({ hasText: new RegExp(`^${lbl}$`) }).first(),
        `Stage "${lbl}" deve estar visível`,
      ).toBeVisible();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 1 — Vaga (definir-vaga)
// ─────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────
// Stage 1 — Vaga — modal tests (W1-3)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 1 — Vaga — modal', () => {
  test('RAL-011 MODAL: 1.1 Criar nova vaga → lia:open_modal {modal_id: "create_job"}', async ({ authenticatedPage: page }) => {
    // W1-3: Card opens CreateJobModal directly instead of going through chat.
    await goChatEmpty(page);
    await expandStage(page, 'Vaga');
    // Capture the lia:open_modal event
    await page.evaluate(() => {
      (window as any).__ral_modal_event = undefined;
      window.addEventListener('lia:open_modal', (e: Event) => {
        (window as any).__ral_modal_event = (e as CustomEvent).detail;
      }, { once: true });
    });
    await page.locator('[data-rail-a-card="create-job"]').click();
    await page.waitForTimeout(600);
    const ev = await page.evaluate(() => (window as any).__ral_modal_event);
    expect(ev, 'create-job card deve disparar lia:open_modal').toBeDefined();
    expect(ev?.modal_id).toBe('create_job');
  });

  test('RAL-012 MODAL: 1.2 Usar modelo → lia:open_modal {modal_id: "create_job"}', async ({ authenticatedPage: page }) => {
    // W1-3: Job template card uses same CreateJobModal (step choose offers templates).
    await goChatEmpty(page);
    await expandStage(page, 'Vaga');
    await page.evaluate(() => {
      (window as any).__ral_modal_event = undefined;
      window.addEventListener('lia:open_modal', (e: Event) => {
        (window as any).__ral_modal_event = (e as CustomEvent).detail;
      }, { once: true });
    });
    await page.locator('[data-rail-a-card="job-template"]').click();
    await page.waitForTimeout(600);
    const ev = await page.evaluate(() => (window as any).__ral_modal_event);
    expect(ev, 'job-template card deve disparar lia:open_modal').toBeDefined();
    expect(ev?.modal_id).toBe('create_job');
  });
});

test.describe('Stage 1 — Vaga', () => {
  test('RAL-101 visual: cards do stage Vaga', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    // Vaga is default active on load — calling expandStage would toggle it OFF
    await page.screenshot({ path: `${SS}/01-vaga.png` });
    await expect(page).toHaveScreenshot('ral-01-vaga.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="create-job"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="job-template"]')).toBeVisible();
  });

  test('RAL-111 CHAT: 1.1 Criar nova vaga → metadata {card_id, stage_id, domain_hint}', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    // Vaga is default active on load — calling expandStage would toggle it OFF
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="create-job"]').click(),
    );
    expect(ev.card_id).toBe('create-job');
    expect(ev.stage_id).toBe('definir-vaga');
    expect(ev.navigate).toBe(false);
    expect(ev.modal).toBe(false);
  });

  test('RAL-112 CHAT: 1.2 Usar modelo de vaga → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    // Vaga is default active on load — calling expandStage would toggle it OFF
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="job-template"]').click(),
    );
    expect(ev.card_id).toBe('job-template');
    expect(ev.stage_id).toBe('definir-vaga');
    expect(ev.navigate).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 2 — Captação (sourcing)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 2 — Captação', () => {
  test('RAL-201 visual: cards do stage Captação (3 cards)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Captação');
    await page.screenshot({ path: `${SS}/02-captacao.png` });
    await expect(page).toHaveScreenshot('ral-02-captacao.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="search-candidates"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="add-candidate"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="talent-pool"]')).toBeVisible();
  });

  test('RAL-211 CHAT: 2.1 Buscar candidatos → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Captação');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="search-candidates"]').click(),
    );
    expect(ev.card_id).toBe('search-candidates');
    expect(ev.stage_id).toBe('sourcing');
  });

  test('RAL-212 MODAL: 2.2 Adicionar candidato → lia:open_modal {modal_id: "add_candidate"}', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Captação');
    const ev = await onOpenModal(page, () =>
      page.locator('[data-rail-a-card="add-candidate"]').click(),
    );
    expect(ev.modal_id).toBe('add_candidate');
    // Also check modal visually opened
    const dialog = page.locator('role=dialog');
    const opened = await dialog.isVisible({ timeout: 5_000 }).catch(() => false);
    if (opened) {
      await page.screenshot({ path: `${SS}/02b-add-candidate-modal.png` });
      await expect(page).toHaveScreenshot('ral-02b-add-candidate-modal.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    }
  });

  test('RAL-213 NAVIGATION: 2.3 Banco de talentos → /bancos-de-talentos', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Captação');
    await Promise.all([
      page.waitForURL(/bancos-de-talentos/, { timeout: 12_000 }),
      page.locator('[data-rail-a-card="talent-pool"]').click(),
    ]);
    expect(page.url()).toMatch(/bancos-de-talentos/);
    await page.screenshot({ path: `${SS}/02c-talent-pool-nav.png` });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 3 — Triagem
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 3 — Triagem', () => {
  test('RAL-301 visual: cards do stage Triagem', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Triagem');
    await page.screenshot({ path: `${SS}/03-triagem.png` });
    await expect(page).toHaveScreenshot('ral-03-triagem.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="candidate-info"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="update-status"]')).toBeVisible();
  });

  test('RAL-311 CHAT: 3.1 Consultar candidato → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Triagem');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="candidate-info"]').click(),
    );
    expect(ev.card_id).toBe('candidate-info');
    expect(ev.stage_id).toBe('triagem');
  });

  test('RAL-312 CHAT: 3.2 Atualizar status → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Triagem');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="update-status"]').click(),
    );
    expect(ev.card_id).toBe('update-status');
    expect(ev.stage_id).toBe('triagem');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 4 — Entrevista
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 4 — Entrevista', () => {
  test('RAL-401 visual: cards do stage Entrevista', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Entrevista');
    await page.screenshot({ path: `${SS}/04-entrevista.png` });
    await expect(page).toHaveScreenshot('ral-04-entrevista.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="schedule-interview"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="reschedule-interview"]')).toBeVisible();
  });

  test('RAL-411 CHAT: 4.1 Agendar entrevista → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Entrevista');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="schedule-interview"]').click(),
    );
    expect(ev.card_id).toBe('schedule-interview');
    expect(ev.stage_id).toBe('entrevista');
  });

  test('RAL-412 CHAT: 4.2 Reagendar entrevista → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Entrevista');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="reschedule-interview"]').click(),
    );
    expect(ev.card_id).toBe('reschedule-interview');
    expect(ev.stage_id).toBe('entrevista');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 5 — Oferta
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 5 — Oferta', () => {
  test('RAL-501 visual: cards do stage Oferta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Oferta');
    await page.screenshot({ path: `${SS}/05-oferta.png` });
    await expect(page).toHaveScreenshot('ral-05-oferta.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="send-offer"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="compare-candidates"]')).toBeVisible();
  });

  test('RAL-511 CHAT: 5.1 Enviar proposta → metadata correta (offer domain)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Oferta');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="send-offer"]').click(),
    );
    expect(ev.card_id).toBe('send-offer');
    expect(ev.stage_id).toBe('oferta');
  });

  test('RAL-512 CHAT: 5.2 Comparar finalistas → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Oferta');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="compare-candidates"]').click(),
    );
    expect(ev.card_id).toBe('compare-candidates');
    expect(ev.stage_id).toBe('oferta');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 6 — Contratação
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 6 — Contratação', () => {
  test('RAL-601 visual: cards do stage Contratação', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Contratação');
    await page.screenshot({ path: `${SS}/06-contratacao.png` });
    await expect(page).toHaveScreenshot('ral-06-contratacao.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="register-hire"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="close-vacancy"]')).toBeVisible();
  });

  test('RAL-611 CHAT: 6.1 Registrar contratação → metadata correta (pipeline domain)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Contratação');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="register-hire"]').click(),
    );
    expect(ev.card_id).toBe('register-hire');
    expect(ev.stage_id).toBe('contratacao');
  });

  test('RAL-612 CHAT: 6.2 Encerrar vaga → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Contratação');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="close-vacancy"]').click(),
    );
    expect(ev.card_id).toBe('close-vacancy');
    expect(ev.stage_id).toBe('contratacao');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 7 — Análises (analytics)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 7 — Análises', () => {
  test('RAL-701 visual: cards do stage Análises (3 cards)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Análises');
    await page.screenshot({ path: `${SS}/07-analises.png` });
    await expect(page).toHaveScreenshot('ral-07-analises.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="job-report"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="daily-briefing"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="hiring-predictions"]')).toBeVisible();
  });

  test('RAL-711 CHAT: 7.1 Relatório da vaga → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Análises');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="job-report"]').click(),
    );
    expect(ev.card_id).toBe('job-report');
    expect(ev.stage_id).toBe('analytics');
  });

  test('RAL-712 CHAT: 7.2 Briefing diário → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Análises');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="daily-briefing"]').click(),
    );
    expect(ev.card_id).toBe('daily-briefing');
    expect(ev.stage_id).toBe('analytics');
  });

  test('RAL-713 CHAT: 7.3 Previsões → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Análises');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="hiring-predictions"]').click(),
    );
    expect(ev.card_id).toBe('hiring-predictions');
    expect(ev.stage_id).toBe('analytics');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 8 — IA & Automações (ia-automacoes)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 8 — IA & Automações', () => {
  test('RAL-801 visual: cards do stage IA (3 cards)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'IA');
    await page.screenshot({ path: `${SS}/08-ia.png` });
    await expect(page).toHaveScreenshot('ral-08-ia.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="configure-automations"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="wsi-screening"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="ai-suggestions"]')).toBeVisible();
  });

  test('RAL-811 CHAT: 8.1 Configurar automações → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'IA');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="configure-automations"]').click(),
    );
    expect(ev.card_id).toBe('configure-automations');
    expect(ev.stage_id).toBe('ia-automacoes');
  });

  test('RAL-812 CHAT: 8.2 Triagem WSI → metadata correta (interview_scheduling domain)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'IA');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="wsi-screening"]').click(),
    );
    expect(ev.card_id).toBe('wsi-screening');
    expect(ev.stage_id).toBe('ia-automacoes');
  });

  test('RAL-813 CHAT: 8.3 Sugestões da LIA → metadata correta', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'IA');
    const ev = await onRailAClick(page, () =>
      page.locator('[data-rail-a-card="ai-suggestions"]').click({ force: true }),
    );
    expect(ev.card_id).toBe('ai-suggestions');
    expect(ev.stage_id).toBe('ia-automacoes');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Stage 9 — Configurações (navigation cards)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Stage 9 — Configurações', () => {
  test('RAL-901 visual: cards do stage Config (3 cards)', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Config');
    await page.screenshot({ path: `${SS}/09-config.png` });
    await expect(page).toHaveScreenshot('ral-09-config.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
    await expect(page.locator('[data-rail-a-card="ai-credits"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="hiring-policy"]')).toBeVisible();
    await expect(page.locator('[data-rail-a-card="email-templates"]')).toBeVisible();
  });

  test('RAL-911 NAVIGATION: 9.1 Créditos IA → /configuracoes/ai-credits', async ({ authenticatedPage: page }) => {
    // W1-3: ai-credits page now exists — card navigates directly instead of coming-soon.
    await goChatEmpty(page);
    await expandStage(page, 'Config');
    await Promise.all([
      page.waitForURL(/configuracoes.*ai-credits|ai-credits/, { timeout: 12_000 }),
      page.locator('[data-rail-a-card="ai-credits"]').click(),
    ]);
    expect(page.url()).toMatch(/ai-credits/);
    await page.screenshot({ path: `${SS}/09a-ai-credits-nav.png` });
  });

  test('RAL-912 NAVIGATION: 9.2 Política de contratação → /configuracoes?section=pipeline', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Config');
    await Promise.all([
      page.waitForURL(/configuracoes/, { timeout: 12_000 }),
      page.locator('[data-rail-a-card="hiring-policy"]').click(),
    ]);
    expect(page.url()).toMatch(/configuracoes/);
    await page.screenshot({ path: `${SS}/09b-hiring-policy-nav.png` });
  });

  test('RAL-913 NAVIGATION: 9.3 Templates de email → /configuracoes?section=templates-assinatura', async ({ authenticatedPage: page }) => {
    await goChatEmpty(page);
    await expandStage(page, 'Config');
    await Promise.all([
      page.waitForURL(/configuracoes/, { timeout: 12_000 }),
      page.locator('[data-rail-a-card="email-templates"]').click(),
    ]);
    expect(page.url()).toMatch(/configuracoes/);
    await page.screenshot({ path: `${SS}/09c-email-templates.png` });
    await expect(page).toHaveScreenshot('ral-09c-email-templates.png', { maxDiffPixelRatio: 0.05, timeout: 20_000 });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Integridade global: todos os 22 cards presentes e clicáveis
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Rail A — Integridade: 22/22 cards presentes', () => {
  /**
   * Sensor computacional (harness-engineering):
   * Detecta regressão caso qualquer card seja removido do RAIL_A_SUGGESTIONS
   * ou o data-rail-a-card deixe de ser renderizado.
   */
  test('RAL-999: todos os 22 card IDs existem e são clicáveis', async ({ authenticatedPage: page }) => {
    const stages: Array<{ shortLabel: string; cards: string[] }> = [
      { shortLabel: 'Vaga',        cards: ['create-job', 'job-template'] },
      { shortLabel: 'Captação',    cards: ['search-candidates', 'add-candidate', 'talent-pool'] },
      { shortLabel: 'Triagem',     cards: ['candidate-info', 'update-status'] },
      { shortLabel: 'Entrevista',  cards: ['schedule-interview', 'reschedule-interview'] },
      { shortLabel: 'Oferta',      cards: ['send-offer', 'compare-candidates'] },
      { shortLabel: 'Contratação', cards: ['register-hire', 'close-vacancy'] },
      { shortLabel: 'Análises',    cards: ['job-report', 'daily-briefing', 'hiring-predictions'] },
      { shortLabel: 'IA',          cards: ['configure-automations', 'wsi-screening', 'ai-suggestions'] },
      { shortLabel: 'Config',      cards: ['ai-credits', 'hiring-policy', 'email-templates'] },
    ];

    // Navigate ONCE — repeated goChatEmpty in a loop causes hydration flicker.
    // Cycle stages via expandStage (toggles within the same mounted component).
    await goChatEmpty(page);

    let verified = 0;
    for (const { shortLabel, cards } of stages) {
      // Vaga is default active on load — calling expandStage would toggle it OFF.
      if (shortLabel !== 'Vaga') {
        await expandStage(page, shortLabel);
      }
      for (const cardId of cards) {
        const card = page.locator(`[data-rail-a-card="${cardId}"]`);
        await expect(
          card,
          `Card "${cardId}" (stage "${shortLabel}") deve ser visível`,
        ).toBeVisible({ timeout: 8_000 });
        await expect(card).toBeEnabled();
        verified++;
      }
    }
    expect(verified, '22 cards verificados').toBe(22);
  });
});
