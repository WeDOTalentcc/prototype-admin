const { chromium } = require('playwright');
const code = process.argv[2];
if (!code || code.length !== 6) { console.log('Usage: node login-fast.js <6-digit-code>'); process.exit(1); }

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true })).newPage();
  const D = 'plataforma-lia/docs/screenshots';

  // Login flow - as fast as possible
  console.log('Login...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'domcontentloaded' });
  await page.waitForSelector('input[type="text"]', { timeout: 10000 });
  await page.fill('input[type="text"]', 'paulo.moraes@wedotalent.cc');
  await page.click('button:has-text("Continuar")');
  await page.waitForSelector('input[type="password"]', { timeout: 10000 });
  await page.fill('input[type="password"]', 'Rodesia94');
  await page.click('button:has-text("Entrar")');
  
  // Wait for 2FA screen
  await page.waitForSelector('.code-input', { timeout: 15000 });
  await page.waitForTimeout(1000);
  console.log('2FA screen ready, entering code:', code);

  // Approach: use fill() on each input which Playwright implements 
  // by clearing, focusing, and dispatching all needed events
  const inputs = await page.$$('.code-input');
  console.log('Inputs found:', inputs.length);
  
  // Method 1: Playwright fill on each
  for (let i = 0; i < 6; i++) {
    await inputs[i].fill(code[i]);
    await page.waitForTimeout(100);
  }
  
  let vals = await page.$$eval('.code-input', els => els.map(e => e.value));
  console.log('After fill:', vals);
  
  // Check if fill worked
  const allFilled = vals.every((v, i) => v === code[i]);
  
  if (!allFilled) {
    console.log('Fill did not stick. Trying evaluate + Vue trigger...');
    // Method 2: Direct Vue instance manipulation
    await page.evaluate((c) => {
      const inputs = document.querySelectorAll('.code-input');
      inputs.forEach((input, i) => {
        // Try to find Vue instance
        const vueKey = Object.keys(input).find(k => k.startsWith('__vue'));
        if (vueKey) {
          console.log('Found Vue instance on input');
        }
        
        // Set value via property descriptor
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, c[i]);
        
        // Fire all possible events
        ['input', 'change'].forEach(evtName => {
          input.dispatchEvent(new Event(evtName, { bubbles: true, cancelable: true }));
        });
        ['keydown', 'keypress', 'keyup'].forEach(evtName => {
          input.dispatchEvent(new KeyboardEvent(evtName, { 
            key: c[i], code: 'Digit' + c[i], keyCode: 48 + parseInt(c[i]),
            which: 48 + parseInt(c[i]), bubbles: true 
          }));
        });
      });
      
      // Also try to find the parent Vue component and set the code array
      const container = document.querySelector('.mfa-container, .code-input-group');
      if (container) {
        const vueKey = Object.keys(container).find(k => k.startsWith('__vue'));
        if (vueKey) {
          const vueInstance = container[vueKey];
          console.log('Vue instance found on container');
        }
      }
    }, code);
    
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('After Vue trigger:', vals);
  }
  
  // Method 3: If still not working, try focus+type approach with delays
  const allFilled2 = vals.every((v, i) => v === code[i]);
  if (!allFilled2) {
    console.log('Trying focus+pressSequentially...');
    for (let i = 0; i < 6; i++) {
      await inputs[i].click({ force: true });
      await page.waitForTimeout(100);
      await inputs[i].pressSequentially(code[i], { delay: 50 });
      await page.waitForTimeout(150);
    }
    vals = await page.$$eval('.code-input', els => els.map(e => e.value));
    console.log('After pressSequentially:', vals);
  }

  await page.screenshot({ path: `${D}/vue-2fa-attempt.png` });
  
  // Check button state
  const btnEl = await page.$('button:has-text("Verificar")');
  if (btnEl) {
    const disabled = await btnEl.evaluate(el => el.disabled);
    console.log('Verify disabled?', disabled);
    
    if (!disabled) {
      await btnEl.click();
      console.log('✓ Verify clicked!');
    } else {
      // Force click anyway
      await btnEl.evaluate(el => {
        el.disabled = false;
        el.click();
      });
      console.log('✓ Verify force-enabled and clicked');
    }
    
    await page.waitForTimeout(10000);
    await page.screenshot({ path: `${D}/vue-10-after-2fa.png` });
    console.log('URL:', page.url());
  }
  
  // If logged in, capture everything
  const url = page.url();
  if (url !== 'https://app.wedotalent.cc/' && !url.endsWith('/login')) {
    console.log('✓✓✓ LOGGED IN!');
    await captureAll(page, D);
  } else {
    const text = await page.evaluate(() => document.body.innerText.substring(0, 200));
    console.log('Body:', text);
    console.log('✗ Not logged in');
  }
  
  await browser.close();
})();

async function captureAll(page, D) {
  // Candidates list
  console.log('\n=== CANDIDATES ===');
  await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${D}/vue-11-candidates.png` });
  await page.screenshot({ path: `${D}/vue-11-candidates-full.png`, fullPage: true });
  console.log('URL:', page.url());
  
  const rows = await page.$$('table tbody tr');
  console.log('Rows:', rows.length);
  
  if (rows.length > 0) {
    await rows[0].click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${D}/vue-12-preview.png` });
    console.log('✓ Preview opened');
    
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
}
