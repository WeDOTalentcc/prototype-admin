/**
 * Pre-flight checks for the LIA unified diagnostic battery.
 *
 * Validates that all prerequisites are met before the main diagnostic
 * stages run. Failure here aborts the battery with a clear, actionable
 * message. All tests are tagged @preflight.
 *
 * Checks:
 *   PF-01  Backend is up and healthy (/health)
 *   PF-02  Demo tenant exists (company_id 00000000-0000-4000-a000-000000000001)
 *   PF-03  Seed recruiter JWT accepted by /api/v1/users/me
 *   PF-04  Seed vaga V0037 exists in the demo tenant
 *   PF-05  At least one LLM provider key is present in environment
 *   PF-06  Frontend returns HTTP 200
 *
 * Required environment variables:
 *   LIA_TEST_TOKEN        Seed recruiter JWT (required for PF-02, PF-03, PF-04)
 *   PLAYWRIGHT_BASE_URL   Frontend base URL (default: http://localhost:5000)
 *   LIA_BACKEND_URL       Backend base URL  (default: http://localhost:8001)
 *   ANTHROPIC_API_KEY     LLM provider key (PF-05 also accepts OPENAI_API_KEY)
 */
import { test, expect } from '@playwright/test';
import * as http from 'http';
import * as https from 'https';

const BACKEND_URL = process.env.LIA_BACKEND_URL || 'http://localhost:8001';
const DEMO_COMPANY_ID = '00000000-0000-4000-a000-000000000001';

function requireToken(checkId: string): string {
  const token = process.env.LIA_TEST_TOKEN;
  if (!token) {
    throw new Error(
      `[PREFLIGHT FAIL] ${checkId} requires LIA_TEST_TOKEN env var.\n` +
      `  → Set LIA_TEST_TOKEN to a valid JWT for the seed recruiter.\n` +
      `  → The token must carry company_id=${DEMO_COMPANY_ID}.\n` +
      `  → Generate one with: python lia-agent-system/eval/eval_runner.py --print-token`
    );
  }
  return token;
}

function httpGet(url: string, token?: string): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const lib = parsed.protocol === 'https:' ? https : http;
    const opts = {
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: 'GET',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      timeout: 10_000,
    };
    const req = lib.request(opts, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => resolve({ status: res.statusCode ?? 0, body }));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('TIMEOUT')); });
    req.end();
  });
}

test.describe('Pre-flight checks @preflight', () => {
  test.describe.configure({ mode: 'serial' });

  test('PF-01 — Backend is up @preflight', async () => {
    let result: { status: number; body: string };
    try {
      result = await httpGet(`${BACKEND_URL}/health`);
    } catch (err) {
      throw new Error(
        `[PREFLIGHT FAIL] Backend unreachable at ${BACKEND_URL}/health: ${(err as Error).message}\n` +
        `  → Start the lia-backend workflow first.\n` +
        `  → Or set LIA_BACKEND_URL env var to the correct URL.`
      );
    }
    expect(
      result.status,
      `[PREFLIGHT FAIL] Backend returned HTTP ${result.status}. Expected 200.\n` +
      `  → Check lia-backend workflow logs for startup errors.`
    ).toBe(200);
  });

  test('PF-02 — Demo tenant seeded @preflight', async () => {
    const token = requireToken('PF-02');
    let result: { status: number; body: string };
    try {
      result = await httpGet(`${BACKEND_URL}/api/v1/companies/${DEMO_COMPANY_ID}`, token);
    } catch (err) {
      throw new Error(
        `[PREFLIGHT FAIL] Could not reach companies endpoint: ${(err as Error).message}`
      );
    }
    if (result.status === 404) {
      throw new Error(
        `[PREFLIGHT FAIL] Demo tenant ${DEMO_COMPANY_ID} not found in database.\n` +
        `  → Run: python lia-agent-system/app/db/seed.py --tenant demo\n` +
        `  → Or: python lia-agent-system/app/db/seed.py --all`
      );
    }
    expect(
      result.status,
      `[PREFLIGHT FAIL] companies endpoint returned ${result.status}. Body: ${result.body.slice(0, 200)}`
    ).toBeLessThan(500);
  });

  test('PF-03 — Seed recruiter JWT accepted @preflight', async () => {
    const token = requireToken('PF-03');
    let result: { status: number; body: string };
    try {
      result = await httpGet(`${BACKEND_URL}/api/v1/users/me`, token);
    } catch (err) {
      throw new Error(`[PREFLIGHT FAIL] Could not reach users/me: ${(err as Error).message}`);
    }
    if (result.status === 401 || result.status === 403) {
      throw new Error(
        `[PREFLIGHT FAIL] Seed recruiter token rejected (HTTP ${result.status}).\n` +
        `  → The server's SECRET_KEY may have rotated. Regenerate LIA_TEST_TOKEN:\n` +
        `  → python lia-agent-system/eval/eval_runner.py --print-token\n` +
        `  → Set it in Replit Secrets as LIA_TEST_TOKEN.`
      );
    }
    expect(
      result.status,
      `[PREFLIGHT FAIL] users/me returned ${result.status}. Body: ${result.body.slice(0, 200)}`
    ).toBeLessThan(500);
  });

  test('PF-04 — Seed vaga V0037 exists @preflight', async () => {
    const token = requireToken('PF-04');
    let result: { status: number; body: string };
    try {
      result = await httpGet(
        `${BACKEND_URL}/api/v1/jobs?limit=100&company_id=${DEMO_COMPANY_ID}`,
        token
      );
    } catch (err) {
      throw new Error(`[PREFLIGHT FAIL] Could not reach jobs endpoint: ${(err as Error).message}`);
    }
    if (result.status !== 200) {
      throw new Error(
        `[PREFLIGHT FAIL] Jobs list returned HTTP ${result.status}.\n  Body: ${result.body.slice(0, 200)}`
      );
    }
    let hasV0037 = false;
    try {
      const parsed = JSON.parse(result.body);
      const jobs = Array.isArray(parsed) ? parsed : (parsed.items || parsed.data || []);
      hasV0037 = jobs.some(
        (j: { code?: string; external_id?: string; title?: string }) =>
          j.code === 'V0037' || j.external_id === 'V0037' || j.title?.includes('V0037')
      );
    } catch {
      hasV0037 = result.body.includes('V0037');
    }
    if (!hasV0037) {
      throw new Error(
        `[PREFLIGHT FAIL] Seed vaga V0037 not found for tenant ${DEMO_COMPANY_ID}.\n` +
        `  → Run: python lia-agent-system/app/db/seed.py --jobs\n` +
        `  → The YAML scenarios reference V0037 as the canonical test job.`
      );
    }
  });

  test('PF-05 — LLM provider key is valid and responds @preflight', async () => {
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    const openaiKey = process.env.OPENAI_API_KEY;

    if (!anthropicKey && !openaiKey) {
      throw new Error(
        `[PREFLIGHT FAIL] No LLM API key found in environment.\n` +
        `  → Set ANTHROPIC_API_KEY (preferred) or OPENAI_API_KEY in Replit Secrets.\n` +
        `  → The user-simulator and judge both require a live LLM provider.`
      );
    }

    // Attempt a lightweight provider health check (list-models endpoint,
    // which does not consume credits). Try Anthropic first.
    if (anthropicKey) {
      let res: { status: number; body: string };
      try {
        res = await new Promise((resolve, reject) => {
          const httpsLib = require('https') as typeof import('https');
          const req = httpsLib.request({
            hostname: 'api.anthropic.com',
            path: '/v1/models',
            method: 'GET',
            headers: {
              'x-api-key': anthropicKey,
              'anthropic-version': '2023-06-01',
            },
            timeout: 15_000,
          }, (r) => {
            let body = '';
            r.on('data', (c: Buffer) => (body += c));
            r.on('end', () => resolve({ status: r.statusCode ?? 0, body }));
          });
          req.on('error', reject);
          req.on('timeout', () => { req.destroy(); reject(new Error('TIMEOUT')); });
          req.end();
        });
      } catch (err) {
        throw new Error(
          `[PREFLIGHT FAIL] ANTHROPIC_API_KEY set but Anthropic API unreachable: ${(err as Error).message}\n` +
          `  → Check network connectivity and key validity.`
        );
      }
      if (res.status === 401) {
        throw new Error(
          `[PREFLIGHT FAIL] ANTHROPIC_API_KEY is invalid (HTTP 401 from api.anthropic.com).\n` +
          `  → Verify the key value in Replit Secrets.\n` +
          `  → Key must start with "sk-ant-".`
        );
      }
      if (res.status >= 500) {
        console.warn(`  ⚠ Anthropic API returned HTTP ${res.status} — may be a transient error.`);
      }
      expect(
        res.status,
        `[PREFLIGHT FAIL] Anthropic API returned unexpected HTTP ${res.status}. Body: ${res.body.slice(0, 200)}`
      ).toBeLessThan(500);
      console.log(`  ✓ ANTHROPIC_API_KEY accepted (HTTP ${res.status})`);
      return;
    }

    // Fallback: validate OpenAI key
    if (openaiKey) {
      let res: { status: number; body: string };
      try {
        res = await new Promise((resolve, reject) => {
          const https = require('https') as typeof import('https');
          const req = https.request({
            hostname: 'api.openai.com',
            path: '/v1/models',
            method: 'GET',
            headers: { Authorization: `Bearer ${openaiKey}` },
            timeout: 15_000,
          }, (r) => {
            let body = '';
            r.on('data', (c: Buffer) => (body += c));
            r.on('end', () => resolve({ status: r.statusCode ?? 0, body }));
          });
          req.on('error', reject);
          req.on('timeout', () => { req.destroy(); reject(new Error('TIMEOUT')); });
          req.end();
        });
      } catch (err) {
        throw new Error(
          `[PREFLIGHT FAIL] OPENAI_API_KEY set but OpenAI API unreachable: ${(err as Error).message}\n` +
          `  → Check network connectivity and key validity.`
        );
      }
      if (res.status === 401) {
        throw new Error(
          `[PREFLIGHT FAIL] OPENAI_API_KEY is invalid (HTTP 401 from api.openai.com).\n` +
          `  → Verify the key value in Replit Secrets.\n` +
          `  → Key must start with "sk-".`
        );
      }
      expect(
        res.status,
        `[PREFLIGHT FAIL] OpenAI API returned unexpected HTTP ${res.status}. Body: ${res.body.slice(0, 200)}`
      ).toBeLessThan(500);
      console.log(`  ✓ OPENAI_API_KEY accepted (HTTP ${res.status})`);
    }
  });

  test('PF-06 — Frontend is up @preflight', async ({ page }) => {
    const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000';
    let response: { status: () => number } | undefined;
    try {
      response = await page.goto(baseURL, { waitUntil: 'domcontentloaded', timeout: 20_000 }) ?? undefined;
    } catch (err) {
      throw new Error(
        `[PREFLIGHT FAIL] Frontend unreachable at ${baseURL}: ${(err as Error).message}\n` +
        `  → Start the dev-server workflow.\n` +
        `  → Or set PLAYWRIGHT_BASE_URL env var to the correct URL.`
      );
    }
    const status = response?.status() ?? 0;
    expect(
      status,
      `[PREFLIGHT FAIL] Frontend returned HTTP ${status}. Expected 2xx.\n` +
      `  → Check dev-server workflow logs for startup errors.`
    ).toBeLessThan(400);
  });
});
