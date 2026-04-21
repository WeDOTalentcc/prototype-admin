/**
 * Task #717 — Regression coverage for the onboarding entry flow.
 *
 * Why this spec exists
 * --------------------
 * Task #712 fixed the bug where the "Setup Intro" modal swallowed the
 * "Configurar agora" click and dropped the user back into an empty
 * dashboard. The fix relies on two pieces working together:
 *
 *   1. SetupProgressBanner (the persistent CTA shown while
 *      setup_progress < 80%) MUST point at /[locale]/onboarding and
 *      MUST honour the 24h dismiss flag.
 *   2. /[locale]/onboarding MUST render the OnboardingChatPage with the
 *      OnboardingActionOrchestrator + UnifiedChat bridge once the user
 *      and context endpoints respond.
 *
 * Without an end-to-end check covering BOTH steps, a refactor of either
 * the banner href, the OnboardingController state machine, or the
 * onboarding route's data loading could silently reintroduce the
 * "modal engole o clique" regression.
 *
 * The tests here are auth-free: we stub the few backend endpoints used
 * by the route + banner so we exercise the frontend bridge in
 * isolation, the same approach already used by `onboarding-712.spec.ts`.
 */
import { test, expect } from '@playwright/test';

const PROGRESS_URL = '**/api/backend-proxy/settings/progress/**';
const USERS_ME_URL = '**/api/backend-proxy/users/me';
const ONB_CONTEXT_URL = '**/api/backend-proxy/onboarding/**';

const BANNER_DISMISS_KEY = 'lia.setup-banner.dismissed-at';

async function stubBackend(
  page: import('@playwright/test').Page,
  opts: { progressOverall: number },
) {
  await page.route(PROGRESS_URL, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        overall: opts.progressOverall,
        sections: {},
      }),
    }),
  );
  await page.route(USERS_ME_URL, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 7, user_id: 7, email: 'e2e@wedo.cc' }),
    }),
  );
  await page.route(ONB_CONTEXT_URL, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ whatsapp_messages: [], onboarding_data: {} }),
    }),
  );
}

test.describe('@onboarding-717 SetupProgressBanner thresholds + dismiss', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((key) => {
      try { localStorage.removeItem(key); } catch {}
    }, BANNER_DISMISS_KEY);
  });

  test('T01 banner shows progress + Continuar CTA when overall < 80%', async ({ page }) => {
    await stubBackend(page, { progressOverall: 35 });
    await page.goto('/pt');

    const banner = page.getByTestId('setup-progress-banner');
    await expect(banner).toBeVisible({ timeout: 15_000 });
    await expect(banner).toContainText('35%');

    const cta = banner.getByRole('link', { name: /Continuar/i });
    await expect(cta).toHaveAttribute('href', '/onboarding');
  });

  test('T02 banner is hidden when overall >= 80%', async ({ page }) => {
    let progressHit = false;
    await page.route(PROGRESS_URL, (route) => {
      progressHit = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ overall: 92, sections: {} }),
      });
    });
    await page.route(USERS_ME_URL, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 7, user_id: 7, email: 'e2e@wedo.cc' }),
      }),
    );
    await page.route(ONB_CONTEXT_URL, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ whatsapp_messages: [], onboarding_data: {} }),
      }),
    );

    await page.goto('/pt');
    // Wait until the banner has actually fetched its progress signal —
    // only then can we trust that "not visible" means "hidden by 92%>=80%"
    // and not just "still mounting".
    await expect.poll(() => progressHit, { timeout: 15_000 }).toBe(true);
    await expect(page.getByTestId('setup-progress-banner')).toHaveCount(0);
  });

  test('T03 dismiss persists for 24h then expires', async ({ page, context }) => {
    await stubBackend(page, { progressOverall: 40 });

    // First visit: dismiss the banner.
    await page.goto('/pt');
    const banner = page.getByTestId('setup-progress-banner');
    await expect(banner).toBeVisible({ timeout: 15_000 });
    await banner.getByRole('button', { name: /Dispensar/i }).click();
    await expect(banner).toHaveCount(0);

    // Reload within 24h window — banner must stay hidden. Wait for the
    // progress fetch so we know the banner has had a chance to evaluate.
    const reload1 = page.waitForResponse((r) =>
      r.url().includes('/api/backend-proxy/settings/progress'),
    );
    await page.reload();
    await reload1;
    await expect(page.getByTestId('setup-progress-banner')).toHaveCount(0);

    // Now backdate the dismiss flag past the 24h window in this origin's
    // localStorage and reload — banner must reappear.
    await page.evaluate((key) => {
      const past = Date.now() - 25 * 60 * 60 * 1000;
      localStorage.setItem(key, String(past));
    }, BANNER_DISMISS_KEY);
    await page.reload();
    await expect(page.getByTestId('setup-progress-banner')).toBeVisible({
      timeout: 15_000,
    });
  });
});

test.describe('@onboarding-717 Banner CTA → /onboarding chat bridge', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((key) => {
      try { localStorage.removeItem(key); } catch {}
      try { sessionStorage.removeItem('lia-onboarding-checked'); } catch {}
    }, BANNER_DISMISS_KEY);
  });

  test('T04 clicking Continuar navigates to /onboarding and chat loads context', async ({ page }) => {
    await stubBackend(page, { progressOverall: 25 });

    // Spy: did the route fetch the user-scoped context after we landed?
    let contextHit = false;
    await page.route('**/api/backend-proxy/onboarding/7/context', (route) => {
      contextHit = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ whatsapp_messages: [], onboarding_data: {} }),
      });
    });

    await page.goto('/pt');
    const banner = page.getByTestId('setup-progress-banner');
    await expect(banner).toBeVisible({ timeout: 15_000 });

    await Promise.all([
      page.waitForURL(/\/(pt\/)?onboarding(\?|$)/, { timeout: 15_000 }),
      banner.getByRole('link', { name: /Continuar/i }).click(),
    ]);

    // The OnboardingChatPage mounts the orchestrator after userId resolves
    // and the context fetch returns. Both must happen for the chat bridge
    // to work — that's the regression we're guarding.
    await expect(page.getByTestId('onboarding-orchestrator')).toBeVisible({
      timeout: 15_000,
    });
    expect(contextHit).toBe(true);
  });

  test('T05 /onboarding shows a loading state until users/me resolves', async ({ page }) => {
    await stubBackend(page, { progressOverall: 25 });

    // Hold /users/me open so we can assert the loading state, then release.
    let release: (() => void) | undefined;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    await page.route(USERS_ME_URL, async (route) => {
      await gate;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 7, user_id: 7, email: 'e2e@wedo.cc' }),
      });
    });

    await page.goto('/pt/onboarding');
    await expect(page.getByText(/Carregando seu onboarding/i)).toBeVisible({
      timeout: 15_000,
    });

    release?.();

    await expect(page.getByTestId('onboarding-orchestrator')).toBeVisible({
      timeout: 15_000,
    });
  });
});
