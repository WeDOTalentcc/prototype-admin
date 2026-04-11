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
  testDir: '.',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../reports/html', open: 'never' }],
    ['./eval-reporter.ts'],
  ],
  timeout: 75_000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'on',
    video: 'retain-on-failure',
    viewport: { width: 1920, height: 1080 },
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium } } : {}),
  },

  projects: [
    {
      name: 'eval-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
      },
    },
  ],

  ...(process.env.PLAYWRIGHT_BASE_URL ? {} : {
    webServer: {
      command: 'npm run dev',
      url: 'http://localhost:5000',
      reuseExistingServer: true,
      timeout: 120_000,
    },
  }),
});
