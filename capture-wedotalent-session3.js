const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = path.join(__dirname, 'plataforma-lia/docs/screenshots/session3');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const CREDS = {
  email: 'paulo.moraes@wedotalent.cc',
  password: 'Rodesia94'
};

let page, browser, context;

async function screenshot(name) {
  const filepath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage: false });
  console.log(`[SCREENSHOT] ${name}.png`);
  return filepath;
}

async function login() {
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  page = await context.newPage();

  console.log('[1] Navigating to login...');
  await page.goto('https://app.wedotalent.cc/login', { waitUntil: 'networkidle', timeout: 30000 });
  await screenshot('S3-01-login-page');

  console.log('[2] Filling email...');
  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first();
  await emailInput.waitFor({ timeout: 10000 });
  await emailInput.fill(CREDS.email);
  await screenshot('S3-02-email-filled');

  console.log('[3] Clicking next/submit...');
  const nextBtn = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Continuar"), button:has-text("Next")').first();
  await nextBtn.click();
  await page.waitForTimeout(2000);
  await screenshot('S3-03-after-email');

  const passwordInput = page.locator('input[type="password"]').first();
  const hasPassword = await passwordInput.isVisible().catch(() => false);
  if (hasPassword) {
    console.log('[4] Filling password...');
    await passwordInput.fill(CREDS.password);
    await screenshot('S3-04-password-filled');

    const loginBtn = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Login")').first();
    await loginBtn.click();
    await page.waitForTimeout(3000);
    await screenshot('S3-05-after-password');
  }

  console.log('[5] Waiting for 2FA or redirect...');
  await screenshot('S3-06-2fa-or-dashboard');

  const has2FA = await page.locator('input[name="code"], input[placeholder*="codigo" i], input[placeholder*="code" i], input[type="number"]').first().isVisible().catch(() => false);
  if (has2FA) {
    console.log('\n========================================');
    console.log('2FA REQUIRED! Check email and provide code.');
    console.log('Run: node fill-2fa.js <CODE>');
    console.log('========================================\n');

    await context.storageState({ path: 'wedotalent-auth-state.json' });
    console.log('[STATE SAVED] wedotalent-auth-state.json');
  } else {
    console.log('[OK] No 2FA detected, checking if logged in...');
    await page.waitForTimeout(2000);
    await screenshot('S3-07-logged-in');
  }

  return { browser, context, page };
}

login().catch(e => {
  console.error('[ERROR]', e.message);
  if (browser) browser.close();
});
