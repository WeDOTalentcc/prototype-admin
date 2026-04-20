import { defineConfig, devices } from "@playwright/test";
import * as path from "path";

const REPORT_DIR = path.join(process.cwd(), "playwright-report", "diagnostic");

export default defineConfig({
  testDir: ".",
  testMatch: /agentic-eval\.spec\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    ["json", { outputFile: path.join(REPORT_DIR, "agentic-results.json") }],
  ],
  timeout: 300_000,

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5000",
    trace: "off",
    screenshot: "off",
    video: "off",
    viewport: { width: 1366, height: 900 },
    ignoreHTTPSErrors: true,
    launchOptions: {
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--no-first-run",
      ],
    },
  },

  projects: [
    { name: "agentic-eval", use: { ...devices["Desktop Chrome"] } },
  ],
});
