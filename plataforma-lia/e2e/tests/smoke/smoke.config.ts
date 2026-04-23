import { defineConfig, devices } from '@playwright/test';
import { execSync } from 'child_process';
import * as path from 'path';

function getSystemChromiumPath(): string | undefined {
  try {
    return execSync('which chromium', { encoding: 'utf-8' }).trim();
  } catch {
    return undefined;
  }
}

const systemChromium = process.env.PLAYWRIGHT_CHROMIUM_PATH || getSystemChromiumPath();
const REPORT_DIR = path.join(process.cwd(), 'playwright-report', 'diagnostic');

export default defineConfig({
  testDir: '.',
  testMatch: /smoke\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 1,
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(REPORT_DIR, 'smoke-results.json') }],
  ],
  timeout: 60_000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1366, height: 900 },
    ignoreHTTPSErrors: true,
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium } } : {}),
  },

  projects: [
    { name: 'smoke', use: { ...devices['Desktop Chrome'] } },
  ],
});
