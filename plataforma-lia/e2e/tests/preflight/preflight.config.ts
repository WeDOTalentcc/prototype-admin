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
  testMatch: /preflight\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(REPORT_DIR, 'preflight-results.json') }],
  ],
  timeout: 30_000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5000',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    ignoreHTTPSErrors: true,
    ...(systemChromium ? { launchOptions: { executablePath: systemChromium } } : {}),
  },

  projects: [
    { name: 'preflight', use: { ...devices['Desktop Chrome'] } },
  ],
});
