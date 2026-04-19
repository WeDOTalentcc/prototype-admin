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
  testMatch: /agentic-eval\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  timeout: 240_000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    viewport: { width: 1366, height: 900 },
    ignoreHTTPSErrors: true,
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium } } : {}),
  },

  projects: [
    { name: 'agentic-eval', use: { ...devices['Desktop Chrome'] } },
  ],
});
