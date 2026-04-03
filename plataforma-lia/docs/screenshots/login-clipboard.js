const { chromium } = require('playwright');

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
  const fs = require('fs');

  // Login
  console.log('[1] Login...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'domcontentloaded' });
  await page.waitForSelector('input[type="text"]', { timeout: 10000 });
  await page.fill('input[type="text"]', 'paulo.moraes@wedotalent.cc');
  await page.click('button:has-text("Continuar")');
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  await page.fill('input[type="password"]', 'Rodesia94');
  await page.click('button:has-text("Entrar")');
  
  // Wait for 2FA
  console.log('[2] Waiting for 2FA...');
  await page.waitForSelector('.code-input', { timeout: 15000 });
  await page.waitForTimeout(1000);
  console.log('=== 2FA READY - WAITING FOR CODE ===');
  
  // Write signal file so we know we're ready
  fs.writeFileSync('/tmp/2fa-ready.txt', 'ready');
  
  // Poll for code
  let code = null;
  for (let i = 0; i < 120; i++) { // 2 min max
    if (fs.existsSync('/tmp/2fa-code.txt')) {
      code = fs.readFileSync('/tmp/2fa-code.txt', 'utf8').trim();
      if (code.length === 6) {
        fs.unlinkSync('/tmp/2fa-code.txt');
        break;
      }
    }
    await new Promise(r => setTimeout(r, 1000));
    if (i % 10 === 0) console.log(`  waiting... ${i}s`);
  }
  
  if (!code) {
    console.log('Timeout');
    await browser.close();
    return;
  }
  
  console.log('[3] Got code:', code, '- entering via clipboard paste...');
  
  // Click first input to focus
  const firstInput = (await page.$$('.code-input'))[0];
  await firstInput.click();
  await page.waitForTimeout(300);
  
  // Method: Set clipboard and paste
  await page.evaluate(async (c) => {
    await navigator.clipboard.writeText(c);
  }, code).catch(() => {});
  
  // Also set via execCommand approach
  await firstInput.click();
  await page.evaluate((c) => {
    const input = document.querySelector('.code-input');
    input.focus();
    
    // Create and dispatch paste event with data
    const dt = new DataTransfer();
    dt.setData('text/plain', c);
    const pasteEvent = new ClipboardEvent('paste', {
      clipboardData: dt,
      bubbles: true,
      cancelable: true
    });
    input.dispatchEvent(pasteEvent);
  }, code);
  
  await page.waitForTimeout(500);
  
  // Check if paste worked
  let vals = await page.$$eval('.code-input', els => els.map(e => e.value));
  console.log('After paste:', vals);
  
  if (vals.some(v => v === '')) {
    // Try Ctrl+V approach
    console.log('Paste event did not work. Trying Ctrl+V...');
    await page.evaluate(async (c) => {
      try { await navigator.clipboard.writeText(c); } catch(e) {}
    }, code);
    
    await firstInput.click();
    await page.keyboard.down('Control');
    await page.keyboard.press('v');
    await page.keyboard.up('Control');
    await page.waitForTimeout(500);
    
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('After Ctrl+V:', vals);
  }
  
  if (vals.some(v => v === '')) {
    // Nuclear option: directly manipulate the Vue component's data
    console.log('Trying Vue data manipulation...');
    await page.evaluate((c) => {
      const container = document.querySelector('.code-input-group') || document.querySelector('.mfa-container');
      
      // Walk up to find Vue component instance
      let el = container || document.querySelector('.code-input');
      while (el) {
        const vueKey = Object.keys(el).find(k => k.startsWith('__vue_app') || k.startsWith('__vue'));
        if (vueKey) {
          console.log('Found Vue key:', vueKey);
          break;
        }
        el = el.parentElement;
      }
      
      // Set each input value and fire events
      const inputs = document.querySelectorAll('.code-input');
      const digits = c.split('');
      
      inputs.forEach((input, i) => {
        // Use Object.defineProperty trick to bypass Vue reactivity guard
        const proto = Object.getPrototypeOf(input);
        const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
        descriptor.set.call(input, digits[i]);
        
        // Fire multiple event types to trigger any listener
        ['beforeinput', 'input', 'change', 'keydown', 'keyup', 'keypress'].forEach(type => {
          if (type.startsWith('key')) {
            input.dispatchEvent(new KeyboardEvent(type, { key: digits[i], bubbles: true }));
          } else if (type === 'beforeinput') {
            input.dispatchEvent(new InputEvent(type, { data: digits[i], inputType: 'insertText', bubbles: true }));
          } else {
            input.dispatchEvent(new Event(type, { bubbles: true }));
          }
        });
      });
    }, code);
    
    await page.waitForTimeout(500);
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('After Vue manipulation:', vals);
  }
  
  await page.screenshot({ path: `${D}/vue-2fa-final.png` });
  
  // Try to click verify regardless
  const btn = await page.$('button:has-text("Verificar")');
  if (btn) {
    const disabled = await btn.evaluate(el => el.disabled);
    console.log('Verify disabled?', disabled);
    
    if (disabled) {
      // Force enable
      await btn.evaluate(el => { el.disabled = false; });
      await page.waitForTimeout(100);
    }
    
    await btn.click({ force: true });
    console.log('Verify clicked');
    await page.waitForTimeout(10000);
  }
  
  await page.screenshot({ path: `${D}/vue-10-result.png` });
  console.log('Final URL:', page.url());
  
  const finalUrl = page.url();
  if (finalUrl !== 'https://app.wedotalent.cc/' && !finalUrl.endsWith('/login')) {
    console.log('=== LOGGED IN! ===');
    
    // Capture candidates
    await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${D}/vue-11-candidates.png` });
    await page.screenshot({ path: `${D}/vue-11-candidates-full.png`, fullPage: true });
    console.log('Candidates captured, URL:', page.url());
    
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
