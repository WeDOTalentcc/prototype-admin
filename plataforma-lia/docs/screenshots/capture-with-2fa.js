const { chromium } = require('playwright');

const CODE_2FA = process.argv[2];
if (!CODE_2FA || CODE_2FA.length !== 6) {
  console.log('Usage: node capture-with-2fa.js <6-digit-code>');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true 
  });
  const page = await context.newPage();
  const outDir = 'plataforma-lia/docs/screenshots';
  
  console.log('=== WEDOTALENT PRODUCTION — Full Capture ===\n');
  
  // === LOGIN ===
  console.log('--- LOGIN ---');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  const emailInput = await page.$('input[type="text"], input[type="email"]');
  await emailInput.click();
  await page.keyboard.type('paulo.moraes@wedotalent.cc', { delay: 30 });
  await page.waitForTimeout(500);
  
  const continueBtn = await page.$('button:has-text("Continuar")');
  await continueBtn.click();
  await page.waitForTimeout(3000);
  
  const passField = await page.$('input[type="password"]');
  await passField.click();
  await page.keyboard.type('Rodesia94', { delay: 30 });
  await page.waitForTimeout(500);
  
  const loginBtn = await page.$('button:has-text("Entrar")');
  await loginBtn.click();
  await page.waitForTimeout(5000);
  
  console.log('Entering 2FA code:', CODE_2FA);
  await page.screenshot({ path: `${outDir}/vue-2fa-before.png`, fullPage: false });
  
  // Get all OTP inputs
  const codeInputs = await page.$$('input[maxlength="1"]');
  console.log('   Found', codeInputs.length, 'code inputs');
  
  if (codeInputs.length >= 6) {
    // Use dispatchEvent to set values natively and trigger Vue reactivity
    for (let i = 0; i < 6; i++) {
      await codeInputs[i].click();
      await page.waitForTimeout(100);
      
      // Set value via native input setter to trigger Vue/Vuetify reactivity
      await codeInputs[i].evaluate((el, digit) => {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(el, digit);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new KeyboardEvent('keydown', { key: digit, code: 'Digit' + digit, bubbles: true }));
        el.dispatchEvent(new KeyboardEvent('keyup', { key: digit, code: 'Digit' + digit, bubbles: true }));
      }, CODE_2FA[i]);
      
      await page.waitForTimeout(150);
    }
    console.log('   ✓ 2FA code filled via native events');
  }
  
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/vue-2fa-filled.png`, fullPage: false });
  
  // Check verify button
  const verifyBtn = await page.$('button:has-text("Verificar")');
  if (verifyBtn) {
    const isDisabled = await verifyBtn.evaluate(el => el.disabled);
    console.log('   Verify button disabled?', isDisabled);
    
    if (isDisabled) {
      // Try alternative: clear all and use keyboard.type approach
      console.log('   Trying keyboard approach...');
      await codeInputs[0].click();
      await page.waitForTimeout(200);
      // Select all and delete
      for (let i = 0; i < 6; i++) {
        await codeInputs[i].evaluate(el => { el.value = ''; });
      }
      await codeInputs[0].click();
      await page.waitForTimeout(200);
      
      // Type each digit one by one with proper focus
      for (let i = 0; i < 6; i++) {
        await codeInputs[i].focus();
        await page.waitForTimeout(50);
        await codeInputs[i].type(CODE_2FA[i], { delay: 50 });
        await page.waitForTimeout(150);
      }
      
      await page.waitForTimeout(500);
      const isStillDisabled = await verifyBtn.evaluate(el => el.disabled);
      console.log('   After keyboard approach, disabled?', isStillDisabled);
      
      if (isStillDisabled) {
        // Last resort: paste approach
        console.log('   Trying paste approach...');
        await codeInputs[0].click();
        await page.evaluate((code) => {
          const inputs = document.querySelectorAll('input[maxlength="1"]');
          inputs.forEach((input, i) => {
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(input, code[i]);
            input.dispatchEvent(new Event('input', { bubbles: true }));
          });
          // Also try triggering paste event on first input
          const dt = new DataTransfer();
          dt.setData('text/plain', code);
          inputs[0].dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true }));
        }, CODE_2FA);
        
        await page.waitForTimeout(1000);
        const finalDisabled = await verifyBtn.evaluate(el => el.disabled);
        console.log('   After paste approach, disabled?', finalDisabled);
      }
    }
    
    // Try clicking regardless
    try {
      await verifyBtn.click({ timeout: 3000, force: true });
      console.log('   ✓ Verify clicked');
    } catch (e) {
      await verifyBtn.evaluate(el => el.click());
      console.log('   ✓ Verify force-clicked');
    }
  }
  
  await page.waitForTimeout(10000);
  await page.screenshot({ path: `${outDir}/vue-10-after-2fa.png`, fullPage: false });
  console.log('   URL after 2FA:', page.url());
  
  const bodyAfter = await page.evaluate(() => document.body.innerText.substring(0, 500));
  console.log('   Body:', bodyAfter.substring(0, 300));
  
  // === CANDIDATES ===
  console.log('\n--- CANDIDATES ---');
  await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${outDir}/vue-11-candidates-list.png`, fullPage: false });
  console.log('   URL:', page.url());
  
  if (page.url() === 'https://app.wedotalent.cc/' || page.url().includes('login')) {
    console.log('   ✗ Not logged in');
    await browser.close();
    return;
  }
  
  console.log('   ✓ Logged in! Capturing candidates page...');
  
  // Full page
  await page.screenshot({ path: `${outDir}/vue-11-candidates-full.png`, fullPage: true });
  
  // Get table rows
  const rows = await page.$$('table tbody tr');
  console.log('   Table rows:', rows.length);
  
  if (rows.length > 0) {
    console.log('\n--- CANDIDATE PREVIEW ---');
    await rows[0].click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${outDir}/vue-12-candidate-preview.png`, fullPage: false });
    console.log('   ✓ Preview opened, URL:', page.url());
    
    // Scroll preview
    for (let scroll = 1; scroll <= 3; scroll++) {
      await page.evaluate((s) => {
        const panels = document.querySelectorAll('.v-navigation-drawer, [class*="drawer"], [class*="preview"], [class*="sidebar"]');
        for (const p of panels) {
          if (p.scrollHeight > p.clientHeight) {
            p.scrollTop = (p.scrollHeight * s) / 4;
            return;
          }
        }
        window.scrollTo(0, s * 300);
      }, scroll);
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `${outDir}/vue-12-scroll${scroll}.png`, fullPage: false });
      console.log(`   ✓ Scroll ${scroll}/3`);
    }
    
    // Find and capture all tabs
    const allTabs = await page.$$eval('[role="tab"], .v-tab', els => 
      els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 30)
    );
    console.log('   Tabs:', JSON.stringify(allTabs));
    
    for (const tabText of allTabs) {
      try {
        const tab = await page.$(`[role="tab"]:has-text("${tabText}"), .v-tab:has-text("${tabText}")`);
        if (tab) {
          await tab.click();
          await page.waitForTimeout(3000);
          const safeName = tabText.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-');
          await page.screenshot({ path: `${outDir}/vue-tab-${safeName}.png`, fullPage: false });
          console.log(`   ✓ Tab "${tabText}"`);
        }
      } catch (e) {
        console.log(`   ✗ Tab "${tabText}" error`);
      }
    }
  }
  
  await browser.close();
  console.log('\n=== Done ===');
})();
