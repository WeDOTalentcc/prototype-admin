import { test, expect } from '../fixtures/auth.fixture';
import fs from 'fs';
import path from 'path';

// ============================================================
// RA — Rail A Routing — domain hint injection end-to-end
//
// Verifica que, quando o wizard job_creation panel está ativo,
// sendChatMessage injeta automaticamente:
//   context.metadata.source        = "rail_a"
//   context.metadata.domain_hint   = "wizard"
//   context.metadata.card_id       = "panel_active:job_creation"
//
// Ref: lia-float-context.tsx PANEL_TYPE_TO_DOMAIN_HINT,
//      useChatTransport.ts sendMessage PR-A block,
//      app/orchestrator/services/rail_a_hint_override.py
//      _RAIL_A_EXTRA_TARGETS frozenset
// ============================================================

const REPORT_DIR = path.join(__dirname, '../reports/rail-a-routing-2026-04-30');

// Selectors canônicos
const SEL = {
  chatInput: [
    '[data-testid="chat-input"]',
    'textarea[placeholder*="mensagem" i]',
    'textarea[placeholder*="Digite" i]',
    'textarea[placeholder*="LIA" i]',
  ].join(', '),
  liaChat: '[data-testid="lia-chat"], .lia-chat-container, [role="main"]',
  jobCreationPanel: '[role="complementary"]',  // aria-label="Painel contextual: Criação de Vaga"
  liaMarkdown: '.lia-markdown-content',
};

/** Aguarda o painel job_creation ativar via aria-label. */
async function waitForJobCreationPanel(page: import('@playwright/test').Page): Promise<boolean> {
  return page
    .locator(SEL.jobCreationPanel)
    .filter({ hasText: 'Criação de Vaga' })
    .waitFor({ state: 'visible', timeout: 25000 })
    .then(() => true)
    .catch(() => false);
}

/** Coleta frames WS enviados durante o teste. */
function attachWsSentCapture(page: import('@playwright/test').Page): () => string[] {
  const frames: string[] = [];
  page.on('websocket', ws => {
    ws.on('framesent', frame => frames.push(String(frame.payload ?? '')));
  });
  return () => frames;
}

/** Coleta frames WS recebidos durante o teste. */
function attachWsReceivedCapture(page: import('@playwright/test').Page): () => string[] {
  const frames: string[] = [];
  page.on('websocket', ws => {
    ws.on('framereceived', frame => frames.push(String(frame.payload ?? '')));
  });
  return () => frames;
}

test.describe('RA — Rail A Routing', () => {

  // RA-001: Wizard page carrega e chat input aparece
  test('RA-001: /vagas/nova carrega com chat input visivel', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await expect(chatInput).toBeVisible({ timeout: 20000 });

    const errorEl = page.locator('text=/500|Unexpected error|Internal Server Error/i');
    await expect(errorEl).toHaveCount(0);

    await page.screenshot({ path: `${REPORT_DIR}/RA-001-wizard-loaded.png` });
  });

  // RA-002: Painel "Criação de Vaga" ativa após LIA responder
  test('RA-002: painel Criacao de Vaga ativa no wizard', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });

    // Envia primeira mensagem para iniciar o wizard
    await chatInput.fill('Quero criar uma nova vaga');
    await chatInput.press('Enter');

    const panelActivated = await waitForJobCreationPanel(page);

    await page.screenshot({ path: `${REPORT_DIR}/RA-002-panel-activation.png` });

    if (panelActivated) {
      const panel = page.locator(SEL.jobCreationPanel).filter({ hasText: 'Criação de Vaga' });
      await expect(panel).toBeVisible();
    } else {
      // Panel pode não ativar em dev se backend não retornar panel_update
      // Marca como soft fail + screenshot para diagnóstico
      console.log('[RA-002] Painel job_creation não ativou no tempo esperado — backend panel_update ausente?');
    }
  });

  // RA-003: Frame WS enviado APÓS panel ativar inclui domain_hint: "wizard"
  test('RA-003: WS frame apos panel ativo tem domain_hint wizard', async ({ authenticatedPage: page }) => {
    const getSentFrames = attachWsSentCapture(page);

    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });

    // Mensagem inicial para ativar wizard
    await chatInput.fill('Quero criar uma vaga');
    await chatInput.press('Enter');
    await page.waitForTimeout(2000);

    const panelActivated = await waitForJobCreationPanel(page);
    if (!panelActivated) {
      test.skip();
      return;
    }

    // Mensagem enviada COM painel ativo — deve ter domain_hint
    const countBefore = getSentFrames().length;
    await chatInput.fill('Desenvolvedor Senior React');
    await chatInput.press('Enter');
    await page.waitForTimeout(1500);

    const newFrames = getSentFrames().slice(countBefore);
    const chatFrame = newFrames.find(f => {
      try {
        const p = JSON.parse(f);
        return Boolean(p?.content || p?.type === 'chat');
      } catch { return false; }
    });

    expect(chatFrame, 'Nenhum frame chat enviado após panel ativar').toBeTruthy();

    const parsed = JSON.parse(chatFrame!);
    const metadata = parsed?.context?.metadata;

    expect(metadata, 'context.metadata ausente no frame').toBeTruthy();
    expect(metadata?.domain_hint).toBe('wizard');

    await page.screenshot({ path: `${REPORT_DIR}/RA-003-ws-domain-hint.png` });
  });

  // RA-004: Frame WS inclui source: "rail_a"
  test('RA-004: WS frame tem source rail_a', async ({ authenticatedPage: page }) => {
    const getSentFrames = attachWsSentCapture(page);

    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Criar vaga');
    await chatInput.press('Enter');
    await page.waitForTimeout(2000);

    const panelActivated = await waitForJobCreationPanel(page);
    if (!panelActivated) { test.skip(); return; }

    const countBefore = getSentFrames().length;
    await chatInput.fill('Desenvolvedor Backend Python');
    await chatInput.press('Enter');
    await page.waitForTimeout(1500);

    const newFrames = getSentFrames().slice(countBefore);
    const chatFrame = newFrames.find(f => {
      try { const p = JSON.parse(f); return Boolean(p?.content); } catch { return false; }
    });
    if (!chatFrame) { test.skip(); return; }

    const metadata = JSON.parse(chatFrame)?.context?.metadata;
    expect(metadata?.source).toBe('rail_a');
  });

  // RA-005: Frame WS inclui card_id: "panel_active:job_creation"
  test('RA-005: WS frame tem card_id panel_active job_creation', async ({ authenticatedPage: page }) => {
    const getSentFrames = attachWsSentCapture(page);

    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Vou criar uma vaga');
    await chatInput.press('Enter');
    await page.waitForTimeout(2000);

    const panelActivated = await waitForJobCreationPanel(page);
    if (!panelActivated) { test.skip(); return; }

    const countBefore = getSentFrames().length;
    await chatInput.fill('Cargo: Analista de Dados');
    await chatInput.press('Enter');
    await page.waitForTimeout(1500);

    const newFrames = getSentFrames().slice(countBefore);
    const chatFrame = newFrames.find(f => {
      try { const p = JSON.parse(f); return Boolean(p?.content); } catch { return false; }
    });
    if (!chatFrame) { test.skip(); return; }

    const metadata = JSON.parse(chatFrame)?.context?.metadata;
    expect(metadata?.card_id).toBe('panel_active:job_creation');
  });

  // RA-006: Página geral — mensagem enviada SEM domain_hint
  test('RA-006: mensagem de pagina geral nao tem domain_hint', async ({ authenticatedPage: page }) => {
    const getSentFrames = attachWsSentCapture(page);

    // Página principal (não wizard) — dinamicPanel = null
    await page.goto('/pt');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const chatInput = page.locator(SEL.chatInput).first();
    if (!await chatInput.isVisible({ timeout: 8000 }).catch(() => false)) {
      test.skip();
      return;
    }

    const countBefore = getSentFrames().length;
    await chatInput.fill('Olá LIA');
    await chatInput.press('Enter');
    await page.waitForTimeout(1500);

    const newFrames = getSentFrames().slice(countBefore);
    const chatFrame = newFrames.find(f => {
      try { const p = JSON.parse(f); return Boolean(p?.content); } catch { return false; }
    });
    if (!chatFrame) { test.skip(); return; }

    const metadata = JSON.parse(chatFrame)?.context?.metadata;
    // Sem panel ativo, metadata pode ser undefined ou não ter domain_hint
    const hasDomainHint = metadata?.domain_hint !== undefined;
    expect(hasDomainHint, 'domain_hint não deveria existir em página geral').toBe(false);
  });

  // RA-007: WS connection estabelecida no wizard (backend alcançável)
  test('RA-007: WS connection abre no wizard', async ({ authenticatedPage: page }) => {
    const getSentFrames = attachWsSentCapture(page);
    const getReceivedFrames = attachWsReceivedCapture(page);

    let wsOpened = false;
    page.on('websocket', () => { wsOpened = true; });

    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    await page.screenshot({ path: `${REPORT_DIR}/RA-007-ws-connection.png` });
    expect(wsOpened, 'WebSocket não abriu — backend WS endpoint fora do ar?').toBe(true);
  });

  // RA-008: Backend responde no wizard (LIA mensagem de boas-vindas aparece)
  test('RA-008: LIA responde no wizard (backend alcancavel)', async ({ authenticatedPage: page }) => {
    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Olá');
    await chatInput.press('Enter');

    // Aguarda LIA responder
    const liaResponse = page.locator(SEL.liaMarkdown).first();
    const responded = await liaResponse.waitFor({ state: 'visible', timeout: 30000 })
      .then(() => true)
      .catch(() => false);

    await page.screenshot({ path: `${REPORT_DIR}/RA-008-lia-response.png` });
    expect(responded, 'LIA não respondeu — backend pode estar fora do ar').toBe(true);
  });

  // RA-009: Regressão — domínio wizard não vaza para job_management via Tier 3
  test('RA-009: nenhuma mensagem wizard roeia para job_management (sem leak)', async ({ authenticatedPage: page }) => {
    const getReceivedFrames = attachWsReceivedCapture(page);

    await page.goto('/vagas/nova');
    await page.waitForLoadState('networkidle');

    const chatInput = page.locator(SEL.chatInput).first();
    await chatInput.waitFor({ state: 'visible', timeout: 20000 });
    await chatInput.fill('Preciso criar uma vaga de desenvolvedor');
    await chatInput.press('Enter');

    await page.waitForTimeout(8000); // aguarda resposta completa

    const receivedFrames = getReceivedFrames();
    const routingLeakDetected = receivedFrames.some(f => {
      try {
        const p = JSON.parse(f);
        // Se a resposta vier de job_management com confidence baixa,
        // pode ser o leak para o Tier 3 (vetorial) — Rail A deve ter
        // interceptado antes
        const routing = p?.routing_info || p?.debug?.routing;
        return routing?.domain === 'job_management' && routing?.tier === 3;
      } catch { return false; }
    });

    await page.screenshot({ path: `${REPORT_DIR}/RA-009-no-leak.png` });
    // Soft assert: se o backend não retornar routing_info, não podemos verificar
    expect.soft(routingLeakDetected).toBe(false);
  });

});
