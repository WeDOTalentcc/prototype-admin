/**
 * Smoke test suite — @smoke layer for the unified diagnostic battery.
 *
 * Validates the fastest paths through the product to confirm core flows
 * are alive after a code change or deployment:
 *
 *   SM-01  Recruiter auth — cookie-based JWT, expected to land on dashboard
 *   SM-02  Auth persists across page navigations (not redirected to login)
 *   SM-03  Open unified chat and receive a non-empty response
 *   SM-04  Kanban (pipeline) page loads without error
 *   SM-05  Jobs list page loads without error
 *   SM-06  WSI page loads without error
 *   SM-07  Admin role auth — lands on admin panel (requires E2E_ADMIN_TOKEN)
 *   SM-08  Candidate role auth — lands on candidate portal (requires E2E_CANDIDATE_TOKEN)
 *
 * Role coverage:
 *   SM-01–SM-06 run under the seed recruiter identity (LIA_E2E_COOKIE).
 *   SM-07 runs with E2E_ADMIN_TOKEN — SKIPPED with an explicit message if the
 *         env var is not set. When set, the cookie is injected and the test
 *         asserts the user lands on an admin-specific route.
 *   SM-08 runs with E2E_CANDIDATE_TOKEN — same semantics as SM-07.
 *
 *   To enable all 3 roles set E2E_ADMIN_TOKEN and E2E_CANDIDATE_TOKEN in
 *   Replit Secrets. Generate them via:
 *     python lia-agent-system/eval/eval_runner.py --print-token --role admin
 *     python lia-agent-system/eval/eval_runner.py --print-token --role candidate
 *
 * Auth cookie:
 *   LIA_E2E_COOKIE defaults to 'e2e-test-token' — the standard Playwright
 *   test cookie accepted by the Next.js middleware in local dev mode.
 *   For real-backend runs set LIA_E2E_COOKIE to a valid recruiter JWT.
 *
 * Wall time target: < 2 minutes.
 */
import { test, expect, type Page } from '@playwright/test';

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000';

const E2E_COOKIE = process.env.LIA_E2E_COOKIE || 'e2e-test-token';
const ADMIN_TOKEN = process.env.E2E_ADMIN_TOKEN || '';
const CANDIDATE_TOKEN = process.env.E2E_CANDIDATE_TOKEN || '';
// Set by orchestrator --require-all-roles flag. When true, SM-07/SM-08
// run even without tokens (they will fail, making 3-role coverage a hard gate).
const REQUIRE_ALL_ROLES = process.env.REQUIRE_ALL_ROLES === '1';

const CHAT_INPUT =
  'textarea[aria-label="Mensagem para a LIA"], ' +
  'textarea[aria-label="Digite sua mensagem para a LIA"], ' +
  'textarea[placeholder*="LIA"]';
const CHAT_SEND = 'button[aria-label="Enviar mensagem"]';

async function injectAuthCookie(page: Page, cookieValue: string) {
  let domain = 'localhost';
  try { domain = new URL(BASE).hostname; } catch { /* keep default */ }
  await page.context().addCookies([
    { name: 'lia_access_token', value: cookieValue, domain, path: '/' },
    { name: 'lia_auth_method',  value: 'jwt',        domain, path: '/' },
  ]);
}

async function openChatInput(page: Page): Promise<void> {
  const input = page.locator(CHAT_INPUT).first();
  if (!(await input.isVisible().catch(() => false))) {
    await page
      .getByRole('button', { name: /Conversar|Chat LIA|abrir chat|mensagem/i })
      .first()
      .click()
      .catch(() => {});
    await input.waitFor({ state: 'visible', timeout: 15_000 });
  }
}

test.describe('Smoke suite @smoke', () => {
  test.describe.configure({ mode: 'serial' });

  // ── Recruiter flows (SM-01–SM-06) ───────────────────────────────────────────

  test.describe('Recruiter role', () => {
    test.beforeEach(async ({ page }) => {
      await injectAuthCookie(page, E2E_COOKIE);
    });

    test('SM-01 — Recruiter auth: cookie accepted, lands on dashboard @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/dashboard`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      expect(
        !url.includes('/login') && !url.includes('/signin'),
        `SM-01: auth cookie not accepted — redirected to ${url}`
      ).toBe(true);
      expect(
        url.includes('/pt/') || url.includes('/dashboard') || url.includes('/home'),
        `SM-01: unexpected redirect to ${url}`
      ).toBe(true);
    });

    test('SM-02 — Auth persists across page navigations @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/jobs`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      const url = page.url();
      expect(
        !url.includes('/login') && !url.includes('/signin'),
        `SM-02: session dropped on navigation — redirected to ${url}`
      ).toBe(true);
    });

    test('SM-03 — Unified chat: send one message, receive non-empty response @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/chat`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      await openChatInput(page);

      const input = page.locator(CHAT_INPUT).first();
      await input.fill('Olá LIA.');

      const responseP = page.waitForResponse(
        (res) =>
          (res.url().includes('/api/v1/chat') ||
            res.url().includes('/chat/message') ||
            res.url().includes('/backend-proxy/chat')) &&
          res.request().method() === 'POST',
        { timeout: 60_000 }
      );

      await page
        .locator(CHAT_SEND)
        .first()
        .click()
        .catch(() => page.keyboard.press('Enter'));

      const response = await responseP;
      expect(
        response.status(),
        `SM-03: LIA chat endpoint returned HTTP ${response.status()}`
      ).toBeLessThan(500);

      const body = await response.json().catch(() => ({})) as Record<string, unknown>;
      const content =
        (body.response as string) ||
        (body.content as string) ||
        ((body.message as Record<string, unknown>)?.content as string) ||
        '';
      expect(
        content.length,
        `SM-03: LIA replied with empty content. Full body: ${JSON.stringify(body).slice(0, 300)}`
      ).toBeGreaterThan(0);
    });

    test('SM-04 — Kanban (pipeline) page loads @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/pipeline`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      const hasKanban =
        url.includes('/pipeline') ||
        url.includes('/kanban') ||
        (await page.getByText(/pipeline|kanban|triagem|entrevista/i).count()) > 0;
      expect(hasKanban, `SM-04: Kanban page not found. URL: ${url}`).toBe(true);
    });

    test('SM-05 — Jobs list page loads @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/jobs`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      const hasJobs =
        url.includes('/jobs') ||
        url.includes('/vagas') ||
        (await page.getByText(/vagas|jobs|V0037/i).count()) > 0;
      expect(hasJobs, `SM-05: Jobs page not found. URL: ${url}`).toBe(true);
    });

    test('SM-06 — WSI page loads @smoke', async ({ page }) => {
      await page.goto(`${BASE}/pt/wsi`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      const hasWSI =
        url.includes('/wsi') ||
        url.includes('/screening') ||
        (await page.getByText(/WSI|triagem inteligente|screening/i).count()) > 0;
      expect(hasWSI, `SM-06: WSI page not found. URL: ${url}`).toBe(true);
    });
  });

  // ── Admin role (SM-07) ───────────────────────────────────────────────────────

  test.describe('Admin role', () => {
    test('SM-07 — Admin auth: admin cookie accepted, lands on admin panel @smoke', async ({ page }) => {
      test.skip(
        !REQUIRE_ALL_ROLES && !ADMIN_TOKEN,
        'SM-07 SKIPPED — E2E_ADMIN_TOKEN is not set.\n' +
        '  → Generate with: python lia-agent-system/eval/eval_runner.py --print-token --role admin\n' +
        '  → Set as E2E_ADMIN_TOKEN in Replit Secrets to enable this check.\n' +
        '  → For release-grade runs: npm run diagnostic -- --require-all-roles'
      );
      await injectAuthCookie(page, ADMIN_TOKEN);
      await page.goto(`${BASE}/pt/admin`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      expect(
        !url.includes('/login') && !url.includes('/signin'),
        `SM-07: admin cookie not accepted — redirected to ${url}`
      ).toBe(true);
      const hasAdmin =
        url.includes('/admin') ||
        url.includes('/dashboard') ||
        (await page.getByText(/admin|gestão|configurações/i).count()) > 0;
      expect(hasAdmin, `SM-07: Admin panel not found after auth. URL: ${url}`).toBe(true);
    });
  });

  // ── Candidate role (SM-08) ──────────────────────────────────────────────────

  test.describe('Candidate role', () => {
    test('SM-08 — Candidate auth: candidate cookie accepted, lands on candidate portal @smoke', async ({ page }) => {
      test.skip(
        !REQUIRE_ALL_ROLES && !CANDIDATE_TOKEN,
        'SM-08 SKIPPED — E2E_CANDIDATE_TOKEN is not set.\n' +
        '  → Generate with: python lia-agent-system/eval/eval_runner.py --print-token --role candidate\n' +
        '  → Set as E2E_CANDIDATE_TOKEN in Replit Secrets to enable this check.\n' +
        '  → For release-grade runs: npm run diagnostic -- --require-all-roles'
      );
      await injectAuthCookie(page, CANDIDATE_TOKEN);
      await page.goto(`${BASE}/pt/candidate`, { waitUntil: 'domcontentloaded', timeout: 20_000 });
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      const url = page.url();
      expect(
        !url.includes('/login') && !url.includes('/signin'),
        `SM-08: candidate cookie not accepted — redirected to ${url}`
      ).toBe(true);
      const hasCandidate =
        url.includes('/candidate') ||
        url.includes('/candidato') ||
        url.includes('/portal') ||
        (await page.getByText(/candidato|candidate|meu perfil/i).count()) > 0;
      expect(hasCandidate, `SM-08: Candidate portal not found after auth. URL: ${url}`).toBe(true);
    });
  });
});
