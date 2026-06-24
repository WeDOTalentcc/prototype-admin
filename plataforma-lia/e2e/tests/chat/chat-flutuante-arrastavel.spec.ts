/**
 * Test Suite: Chat Flutuante Arrastável (Task #1291 / verificação #1292)
 *
 * Confirma, em um navegador real, que a janela flutuante da LIA criada na
 * Task #1291 funciona ponta-a-ponta — montando a árvore real do UnifiedChat
 * (auth store, websocket e contextos), e não o harness isolado do unit test
 * (`UnifiedChatFloating.test.tsx`).
 *
 * Contrato sob teste (espelha o "Done looks like" da Task #1292):
 *  - arrastar o header REAL move a janela e ela permanece dentro do viewport;
 *  - o botão "voltar ao canto" (data-testid="floating-reset-button") re-doca
 *    a janela no canto inferior direito;
 *  - clicar num controle do header (ex.: nova conversa) durante um "quase
 *    clique" NÃO move a janela (o guard closest("button") segura o drag);
 *  - uma navegação soft preserva a posição arrastada; um reload completo
 *    volta a janela para o canto.
 */

import { test, expect } from '../../fixtures/auth.fixture';
import type { Page } from '@playwright/test';

const HANDLE = '[data-testid="floating-drag-handle"]';
const RESET = '[data-testid="floating-reset-button"]';
const CONTAINER = '[data-render-mode="overlay"][data-chat-mode="floating"]';

/**
 * Garante que a janela flutuante esteja montada: força o modo "floating" no
 * localStorage ANTES de qualquer script de página, navega para uma rota de
 * dashboard (não-"Conversar", que auto-abre o chat) e espera o handle real.
 *
 * O modo é gravado no MESMO formato canônico (envelope com TTL) que
 * `setPersisted`/`getPersisted` usam — todos os readers (dashboard-app,
 * UnifiedChatConditional, DashboardChatPanel, UnifiedChat) leem via
 * `getPersisted`, então o modo "floating" sobrevive a soft-nav e reload.
 */
async function openFloatingWindow(page: Page): Promise<void> {
  await page.addInitScript(() => {
    try {
      const wrapper = {
        value: 'floating',
        expiresAt: Date.now() + 90 * 24 * 60 * 60 * 1000,
      };
      localStorage.setItem('lia-chat-mode', JSON.stringify(wrapper));
    } catch {
      /* ignore */
    }
  });
  await page.goto('/jobs', { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await page.locator(HANDLE).first().waitFor({ state: 'visible', timeout: 30_000 });
}

/** Retorna o bounding box do container flutuante (top-left + dimensões). */
async function containerRect(page: Page) {
  const box = await page.locator(CONTAINER).first().boundingBox();
  if (!box) throw new Error('floating container has no bounding box');
  return box;
}

/**
 * Arrasta o header por (dx, dy). Pega num ponto "vazio" do header (centro
 * horizontal, fora dos grupos de botões alinhados às bordas via
 * justify-between) para não acionar o guard closest("button").
 */
async function dragBy(page: Page, dx: number, dy: number): Promise<void> {
  const handle = page.locator(HANDLE).first();
  const box = await handle.boundingBox();
  if (!box) throw new Error('drag handle has no bounding box');
  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + dx, startY + dy, { steps: 12 });
  await page.mouse.up();
}

test.describe('Chat Flutuante Arrastável (UnifiedChat real)', () => {
  test('TC-DRAG-001: arrastar o header move a janela e a mantém no viewport', async ({
    authenticatedPage: page,
  }) => {
    await openFloatingWindow(page);

    const before = await containerRect(page);
    await dragBy(page, -260, -180);

    const after = await containerRect(page);
    // A janela realmente se moveu (não é mais a posição ancorada).
    expect(
      Math.abs(after.x - before.x) + Math.abs(after.y - before.y),
      'janela deve ter se movido após o arrasto',
    ).toBeGreaterThan(40);

    // E continua inteiramente dentro do viewport.
    const vp = page.viewportSize()!;
    expect(after.x, 'left >= 0').toBeGreaterThanOrEqual(-1);
    expect(after.y, 'top >= 0').toBeGreaterThanOrEqual(-1);
    expect(after.x + after.width, 'right <= viewport').toBeLessThanOrEqual(vp.width + 1);
    expect(after.y + after.height, 'bottom <= viewport').toBeLessThanOrEqual(vp.height + 1);

    // O botão "voltar ao canto" só aparece depois que a janela foi arrastada.
    await expect(page.locator(RESET).first()).toBeVisible();

    await page.screenshot({ path: 'e2e/screenshots/chat-flutuante-arrastada.png' });
  });

  test('TC-DRAG-002: "voltar ao canto" re-doca no canto inferior direito', async ({
    authenticatedPage: page,
  }) => {
    await openFloatingWindow(page);

    const docked = await containerRect(page);
    await dragBy(page, -300, -200);
    const dragged = await containerRect(page);
    expect(Math.abs(dragged.x - docked.x) + Math.abs(dragged.y - docked.y)).toBeGreaterThan(40);

    await page.locator(RESET).first().click();
    // O botão de reset some quando a janela volta ao canto (posição === null).
    await expect(page.locator(RESET).first()).toBeHidden();

    const redocked = await containerRect(page);
    // Volta para (aprox.) a mesma posição ancorada original (bottom-4 right-4).
    expect(Math.abs(redocked.x - docked.x), 'mesma x do canto').toBeLessThanOrEqual(2);
    expect(Math.abs(redocked.y - docked.y), 'mesma y do canto').toBeLessThanOrEqual(2);

    const vp = page.viewportSize()!;
    // Ancorada no canto inferior direito.
    expect(vp.width - (redocked.x + redocked.width)).toBeLessThanOrEqual(40);
    expect(vp.height - (redocked.y + redocked.height)).toBeLessThanOrEqual(40);
  });

  test('TC-DRAG-003: clicar num controle do header não move a janela', async ({
    authenticatedPage: page,
  }) => {
    await openFloatingWindow(page);

    const before = await containerRect(page);

    // Pressiona sobre o botão "nova conversa", movimenta poucos pixels (quase
    // clique) e solta. O guard closest("button") deve impedir o drag.
    const newChat = page
      .locator(CONTAINER)
      .locator('button[aria-label="Nova conversa"]')
      .first();
    const btnBox = await newChat.boundingBox();
    if (!btnBox) throw new Error('botão "Nova conversa" não encontrado no header');
    const cx = btnBox.x + btnBox.width / 2;
    const cy = btnBox.y + btnBox.height / 2;
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    await page.mouse.move(cx + 3, cy + 3, { steps: 3 });
    await page.mouse.up();

    const after = await containerRect(page);
    expect(Math.abs(after.x - before.x), 'x inalterado').toBeLessThanOrEqual(2);
    expect(Math.abs(after.y - before.y), 'y inalterado').toBeLessThanOrEqual(2);
    // Nunca mostrou o botão de reset (nunca virou posição custom).
    await expect(page.locator(RESET).first()).toBeHidden();
  });

  test('TC-DRAG-004: soft-nav preserva a posição; reload completo reseta', async ({
    authenticatedPage: page,
  }) => {
    await openFloatingWindow(page);

    const docked = await containerRect(page);
    await dragBy(page, -280, -200);
    const dragged = await containerRect(page);
    expect(Math.abs(dragged.x - docked.x) + Math.abs(dragged.y - docked.y)).toBeGreaterThan(40);

    // --- Navegação soft (client-side, sem reload): clica um item da sidebar.
    // O provider do chat vive acima do router, então o componente NÃO remonta
    // e a posição arrastada (estado efêmero em memória) deve sobreviver.
    //
    // O modo "floating" persiste sozinho: leitura e escrita usam o MESMO
    // formato canônico (`getPersisted`/`setPersisted`), então o effect de troca
    // de página em dashboard-app lê "floating" e a janela flutuante permanece
    // montada — sem precisar reafirmar o modo no localStorage antes do clique.
    await page.getByRole('button', { name: 'Decidir', exact: true }).first().click();
    await page.waitForURL(/\/tasks(\b|\/|$)/, { timeout: 15_000 });
    await page.locator(HANDLE).first().waitFor({ state: 'visible', timeout: 15_000 });

    const afterSoftNav = await containerRect(page);
    expect(Math.abs(afterSoftNav.x - dragged.x), 'x preservado no soft-nav').toBeLessThanOrEqual(4);
    expect(Math.abs(afterSoftNav.y - dragged.y), 'y preservado no soft-nav').toBeLessThanOrEqual(4);
    await expect(page.locator(RESET).first()).toBeVisible();

    // --- Reload completo: remonta tudo, posição volta ao canto (efêmera).
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 30_000 });
    await page.locator(HANDLE).first().waitFor({ state: 'visible', timeout: 30_000 });

    const afterReload = await containerRect(page);
    expect(Math.abs(afterReload.x - docked.x), 'x volta ao canto após reload').toBeLessThanOrEqual(2);
    expect(Math.abs(afterReload.y - docked.y), 'y volta ao canto após reload').toBeLessThanOrEqual(2);
    await expect(page.locator(RESET).first()).toBeHidden();
  });
});
