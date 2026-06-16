import { defineConfig, devices } from '@playwright/test';
import { execSync } from 'child_process';

function getSystemChromiumPath(): string | undefined {
  try {
    return execSync('which chromium', { encoding: 'utf-8' }).trim();
  } catch {
    return undefined;
  }
}

const systemChromium = process.env.PLAYWRIGHT_CHROMIUM_PATH || getSystemChromiumPath();

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  timeout: 120000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'on',
    video: 'retain-on-failure',
    viewport: { width: 1920, height: 1080 },
    // Extra args for Replit's constrained environment:
    // - disable-dev-shm-usage: prevents /dev/shm OOM crashes
    // - no-sandbox: required for Replit (no setuid sandbox)
    // - disable-gpu: reduces memory pressure
    launchOptions: {
      ...(systemChromium ? { executablePath: systemChromium } : {}),
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
      ],
    },
  },

  projects: [
    {
      name: 'desktop-chrome',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        viewport: { width: 390, height: 844 },
      },
    },
  ],

  ...(process.env.PLAYWRIGHT_BASE_URL ? {} : {
    webServer: {
      command: 'npm run dev',
      url: 'http://localhost:5000',
      // Task #1079 — opt-out explícito (PW_REUSE_SERVER=0) em vez da
      // heurística antiga `!process.env.CI`. Replit setta CI=true, então
      // `!CI` virava `false` e cada cenário tentava spawnar seu próprio
      // webServer na 5000 → EADDRINUSE colidindo com o `dev-server` do
      // workflow já em pé. Default agora é REUSAR; só se ofusca quando
      // o operador explicitamente quer um webServer fresco.
      reuseExistingServer: process.env.PW_REUSE_SERVER !== '0',
      timeout: 120000,
    },
  }),
});
