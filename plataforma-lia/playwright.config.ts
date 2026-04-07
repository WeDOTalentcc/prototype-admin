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
  timeout: 45000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ||
      (process.env.REPLIT_DEV_DOMAIN
        ? `https://${process.env.REPLIT_DEV_DOMAIN}`
        : 'http://localhost:5000'),
    trace: 'on-first-retry',
    screenshot: 'on',
    video: 'retain-on-failure',
    viewport: { width: 1920, height: 1080 },
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium } } : {}),
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

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
