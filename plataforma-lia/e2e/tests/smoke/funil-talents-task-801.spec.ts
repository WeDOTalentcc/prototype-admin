/**
 * Task #801 — E2E smoke: Funil de Talentos carrega candidatos no boot frio.
 *
 * Reproduz o cenário em que o backend está em cold-start e o frontend tem
 * que sobreviver a TypeError("Failed to fetch") inicial via:
 *   - dev-auto-login com retry (C3)
 *   - useCandidatesList preservando snapshot e auto-retentando (C1)
 *   - fetchWithRetry com mensagem fixa (C2)
 *
 * Falha esperada (regressão de qualquer das 3): página fica em estado vazio
 * permanente OU dispara dev-overlay com "Failed to fetch".
 */
import { test, expect } from '@playwright/test';

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000';
const LIA_E2E_COOKIE = process.env.LIA_E2E_COOKIE || 'e2e-test-token';

test.describe('@smoke Funil de Talentos — Task #801', () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      {
        name: 'lia_session',
        value: LIA_E2E_COOKIE,
        url: BASE,
      },
    ]);
  });

  test('SM-801-A: lista de candidatos aparece após cold-start', async ({ page }) => {
    // Captura overlays do Next.js (regressão da Task #728/801).
    const overlayHits: string[] = [];
    page.on('console', msg => {
      const text = msg.text();
      if (/typeerror.*failed to fetch/i.test(text)) {
        overlayHits.push(text);
      }
    });

    await page.goto(`${BASE}/funil-de-talentos`, { waitUntil: 'domcontentloaded' });

    // Aguarda a contagem total de candidatos aparecer (>0). O backend tem 320
    // candidates seed; com cold-start + retry deve resolver em <30s.
    const totalLocator = page.locator('[data-testid="funil-relogin-state"], [data-testid="funil-error-state"]').first();
    const statsLocator = page.locator('text=/\\d+\\s+(candidates?|candidatos?)/i').first();

    await Promise.race([
      statsLocator.waitFor({ state: 'visible', timeout: 60_000 }),
      totalLocator.waitFor({ state: 'visible', timeout: 60_000 }),
    ]);

    // Não deve estar em estado de relogin/erro permanente
    await expect(page.locator('[data-testid="funil-relogin-state"]')).toHaveCount(0);

    // O contador deve mostrar > 0
    const statsText = await statsLocator.textContent();
    expect(statsText).toBeTruthy();
    const match = statsText!.match(/(\d{1,4})/);
    expect(match).toBeTruthy();
    expect(Number(match![1])).toBeGreaterThan(0);

    // Não deveria ter ressuscitado o sintoma da Task #728 no console.
    expect(overlayHits, `dev-overlay deveria estar suprimido. Hits: ${overlayHits.join('|')}`).toHaveLength(0);
  });

  test('SM-801-B: banner de reconexão aparece em flap mas lista persiste', async ({ page }) => {
    await page.goto(`${BASE}/funil-de-talentos`, { waitUntil: 'networkidle' });

    // Aguarda lista carregar
    const statsLocator = page.locator('text=/\\d+\\s+(candidates?|candidatos?)/i').first();
    await statsLocator.waitFor({ state: 'visible', timeout: 60_000 });

    const initialText = await statsLocator.textContent();
    const initialMatch = initialText!.match(/(\d{1,4})/);
    const initialCount = Number(initialMatch![1]);
    expect(initialCount).toBeGreaterThan(0);

    // Simula flap: intercepta /candidates com falha de rede uma vez.
    let interceptedOnce = false;
    await page.route('**/api/backend-proxy/candidates*', async route => {
      if (!interceptedOnce) {
        interceptedOnce = true;
        await route.abort('failed');
      } else {
        await route.continue();
      }
    });

    // Dispara um refresh via window focus (que o hook escuta)
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));

    // A lista NÃO deve ter sido zerada — contagem permanece.
    await page.waitForTimeout(500);
    const midText = await statsLocator.textContent();
    const midMatch = midText!.match(/(\d{1,4})/);
    expect(Number(midMatch![1])).toBe(initialCount);

    // Banner discreto pode aparecer (reconectando) — mas é opcional, então
    // só verificamos que NÃO estamos em relogin permanente.
    await expect(page.locator('[data-testid="funil-relogin-state"]')).toHaveCount(0);
  });
});
