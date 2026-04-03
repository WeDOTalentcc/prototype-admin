const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true })).newPage();
  const D = 'plataforma-lia/docs/screenshots';

  // Step 1: Login with email + password
  console.log('[1/3] Opening WeDOTalent...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'domcontentloaded' });
  await page.waitForSelector('input[type="text"]', { timeout: 10000 });
  await page.fill('input[type="text"]', 'paulo.moraes@wedotalent.cc');
  await page.click('button:has-text("Continuar")');
  
  console.log('[2/3] Entering password...');
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  await page.fill('input[type="password"]', 'Rodesia94');
  await page.click('button:has-text("Entrar")');
  
  console.log('[3/3] Waiting for 2FA screen...');
  await page.waitForSelector('.code-input', { timeout: 15000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${D}/vue-2fa-waiting.png` });
  console.log('=== 2FA SCREEN READY ===');
  console.log('Waiting for code file at /tmp/2fa-code.txt ...');
  
  // Poll for code file
  let code = null;
  for (let attempt = 0; attempt < 300; attempt++) { // 5 minutes max
    if (fs.existsSync('/tmp/2fa-code.txt')) {
      code = fs.readFileSync('/tmp/2fa-code.txt', 'utf8').trim();
      if (code.length === 6) {
        fs.unlinkSync('/tmp/2fa-code.txt');
        break;
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }
  
  if (!code || code.length !== 6) {
    console.log('Timeout waiting for code');
    await browser.close();
    return;
  }
  
  console.log('Got code:', code);
  console.log('Entering code...');
  
  // Enter code using fill() on each input
  const inputs = await page.$$('.code-input');
  for (let i = 0; i < 6; i++) {
    await inputs[i].fill(code[i]);
    await page.waitForTimeout(100);
  }
  
  let vals = await page.$$eval('.code-input', els => els.map(e => e.value));
  console.log('Values after fill:', vals);
  
  // If fill didn't work, try pressSequentially
  if (vals.some(v => v === '')) {
    console.log('Fill did not work, trying pressSequentially...');
    for (let i = 0; i < 6; i++) {
      await inputs[i].click();
      await inputs[i].evaluate(el => { el.value = ''; });
      await inputs[i].pressSequentially(code[i], { delay: 50 });
      await page.waitForTimeout(200);
    }
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('Values after pressSequentially:', vals);
  }
  
  await page.screenshot({ path: `${D}/vue-2fa-filled-check.png` });
  
  // Click verify
  const btn = await page.$('button:has-text("Verificar")');
  const disabled = await btn.evaluate(el => el.disabled);
  console.log('Verify disabled?', disabled);
  
  if (!disabled) {
    await btn.click();
  } else {
    // Force enable and click
    await btn.evaluate(el => { el.disabled = false; el.click(); });
  }
  
  console.log('Verify clicked, waiting...');
  await page.waitForTimeout(10000);
  await page.screenshot({ path: `${D}/vue-10-after-2fa.png` });
  console.log('URL:', page.url());
  
  const url = page.url();
  if (url === 'https://app.wedotalent.cc/' || url.endsWith('/login')) {
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 200));
    console.log('Not logged in:', bodyText);
    await browser.close();
    return;
  }
  
  console.log('=== LOGGED IN! Capturing... ===');
  
  // Candidates list
  await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${D}/vue-11-candidates.png` });
  await page.screenshot({ path: `${D}/vue-11-candidates-full.png`, fullPage: true });
  console.log('Candidates page captured');
  
  // Click first row
  const rows = await page.$$('table tbody tr');
  console.log('Rows:', rows.length);
  
  if (rows.length > 0) {
    await rows[0].click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${D}/vue-12-preview.png` });
    
    for (let i = 1; i <= 4; i++) {
      await page.evaluate(s => {
        for (const d of document.querySelectorAll('.v-navigation-drawer, [class*="drawer"]')) {
          if (d.scrollHeight > d.clientHeight + 50) { d.scrollTop = (d.scrollHeight * s) / 5; return; }
        }
        window.scrollTo(0, s * 250);
      }, i);
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `${D}/vue-12-scroll${i}.png` });
    }
    
    const tabs = await page.$$eval('[role="tab"], .v-tab', els => 
      els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 30)
    );
    console.log('Tabs:', tabs);
    
    for (const t of tabs) {
      try {
        await page.click(`[role="tab"]:has-text("${t}"), .v-tab:has-text("${t}")`);
        await page.waitForTimeout(3000);
        const n = t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '-');
        await page.screenshot({ path: `${D}/vue-tab-${n}.png` });
        console.log(`✓ Tab "${t}"`);
        
        await page.evaluate(() => {
          for (const d of document.querySelectorAll('.v-navigation-drawer, [class*="drawer"]')) {
            if (d.scrollHeight > d.clientHeight) { d.scrollTop = d.scrollHeight / 2; return; }
          }
        });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: `${D}/vue-tab-${n}-scroll.png` });
      } catch(e) { console.log(`✗ Tab "${t}"`); }
    }
  }
  
  await browser.close();
  console.log('=== DONE ===');
})();
