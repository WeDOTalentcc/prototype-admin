const { chromium } = require('playwright');
const code = process.argv[2];
if (!code || code.length !== 6) { console.log('Usage: node login-direct.js <6-digit-code>'); process.exit(1); }

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const ctx = await browser.newContext({ 
    viewport: { width: 1440, height: 900 }, 
    ignoreHTTPSErrors: true,
    permissions: ['clipboard-read', 'clipboard-write']
  });
  const page = await ctx.newPage();
  const D = 'plataforma-lia/docs/screenshots';

  console.log('[1] Login - email...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'domcontentloaded' });
  await page.waitForSelector('input[type="text"]', { timeout: 10000 });
  await page.fill('input[type="text"]', 'paulo.moraes@wedotalent.cc');
  await page.click('button:has-text("Continuar")');
  
  console.log('[2] Password...');
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  await page.fill('input[type="password"]', 'Rodesia94');
  await page.click('button:has-text("Entrar")');
  
  console.log('[3] 2FA...');
  await page.waitForSelector('.code-input', { timeout: 15000 });
  await page.waitForTimeout(500);
  
  // Check for error messages already
  const errorText = await page.evaluate(() => {
    const el = document.querySelector('.error-text, .v-alert, [class*="error"]');
    return el ? el.textContent.trim() : '';
  });
  if (errorText) console.log('   Error on page:', errorText);
  
  console.log('   Entering code:', code);
  
  // The key insight: use page.fill() which does focus + clear + type internally
  const inputs = await page.$$('.code-input');
  console.log('   Inputs:', inputs.length);
  
  // Try 1: Use Playwright's fill
  for (let i = 0; i < Math.min(6, inputs.length); i++) {
    try {
      await inputs[i].fill(code[i]);
    } catch(e) {
      console.log('   fill failed on', i, e.message.substring(0, 50));
    }
    await page.waitForTimeout(50);
  }
  
  let vals = await page.$$eval('.code-input', els => els.map(e => e.value));
  console.log('   After fill():', vals);
  
  // Try 2: If fill didn't work, try evaluate with InputEvent
  if (vals.join('') !== code) {
    console.log('   Trying InputEvent approach...');
    await page.evaluate((c) => {
      document.querySelectorAll('.code-input').forEach((inp, i) => {
        inp.focus();
        inp.value = '';
        
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(inp, c[i]);
        
        inp.dispatchEvent(new InputEvent('input', { 
          data: c[i], inputType: 'insertText', bubbles: true, cancelable: true 
        }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }, code);
    
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('   After InputEvent:', vals);
  }
  
  // Try 3: Focus first and use keyboard
  if (vals.join('') !== code) {
    console.log('   Trying keyboard approach with clear...');
    for (let i = 0; i < inputs.length; i++) {
      await inputs[i].click();
      await page.waitForTimeout(50);
      await page.keyboard.press('Backspace');
      await page.keyboard.press('Delete');
      await page.waitForTimeout(50);
      await page.keyboard.insertText(code[i]);
      await page.waitForTimeout(100);
    }
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('   After keyboard insert:', vals);
  }
  
  await page.screenshot({ path: `${D}/vue-2fa-final.png` });
  
  // Check verify button
  const btn = await page.$('button:has-text("Verificar")');
  if (btn) {
    let disabled = await btn.evaluate(el => el.disabled);
    console.log('   Verify disabled?', disabled);
    
    if (disabled) {
      await btn.evaluate(el => { el.disabled = false; });
      disabled = false;
    }
    
    await btn.click({ force: true });
    console.log('   ✓ Verify clicked');
  }
  
  await page.waitForTimeout(10000);
  await page.screenshot({ path: `${D}/vue-10-result.png` });
  const finalUrl = page.url();
  console.log('   Final URL:', finalUrl);
  
  if (finalUrl !== 'https://app.wedotalent.cc/' && !finalUrl.includes('login')) {
    console.log('=== LOGGED IN! Capturing... ===');
    
    await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${D}/vue-11-candidates.png` });
    await page.screenshot({ path: `${D}/vue-11-candidates-full.png`, fullPage: true });
    console.log('Candidates URL:', page.url());
    
    const rows = await page.$$('table tbody tr');
    console.log('Rows:', rows.length);
    
    if (rows.length > 0) {
      await rows[0].click();
      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${D}/vue-12-preview.png` });
      console.log('✓ Preview');
      
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
        } catch(e) { console.log(`✗ Tab "${t}"`); }
      }
    }
  } else {
    const body = await page.evaluate(() => document.body.innerText.substring(0, 300));
    console.log('Not logged in:', body.substring(0, 200));
  }
  
  await browser.close();
  console.log('=== DONE ===');
})();
