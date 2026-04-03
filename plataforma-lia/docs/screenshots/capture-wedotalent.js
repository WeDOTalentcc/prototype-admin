const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const context = await browser.newContext({ 
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true 
  });
  const page = await context.newPage();
  const outDir = 'plataforma-lia/docs/screenshots';
  
  console.log('=== WEDOTALENT PRODUCTION — Login ===');
  
  // Step 1: Open login page
  console.log('1. Opening WeDOTalent...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  console.log('   URL:', page.url());
  
  // Step 2: Fill email
  console.log('2. Filling email...');
  const emailInput = await page.$('input[type="text"], input[type="email"]');
  await emailInput.fill('paulo.moraes@wedotalent.cc');
  await page.waitForTimeout(500);
  
  // Step 3: Click "Continuar"
  console.log('3. Clicking Continuar...');
  const continueBtn = await page.$('button:has-text("Continuar"), button:has-text("Continue")');
  if (continueBtn) {
    await continueBtn.click();
  } else {
    await page.keyboard.press('Enter');
  }
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${outDir}/vue-02-password-step.png`, fullPage: false });
  console.log('   URL:', page.url());
  
  // Get page state
  const inputs2 = await page.$$eval('input', els => els.map(e => ({
    type: e.type, name: e.name || e.id, placeholder: e.placeholder, visible: e.offsetParent !== null
  })));
  console.log('   Inputs:', JSON.stringify(inputs2));
  
  const bodyText2 = await page.evaluate(() => document.body.innerText.substring(0, 300));
  console.log('   Body:', bodyText2.substring(0, 200));
  
  // Step 4: Fill password
  console.log('4. Filling password...');
  const passField = await page.$('input[type="password"]');
  if (passField) {
    await passField.fill('Rodesia94');
    console.log('   ✓ Password filled');
    
    // Click login/Entrar button
    const loginBtn = await page.$('button:has-text("Entrar"), button:has-text("Login"), button[type="submit"]');
    if (loginBtn) {
      await loginBtn.click();
      console.log('   ✓ Login clicked');
    } else {
      await page.keyboard.press('Enter');
      console.log('   ✓ Enter pressed');
    }
    
    await page.waitForTimeout(8000);
    await page.screenshot({ path: `${outDir}/vue-03-after-login.png`, fullPage: false });
    console.log('   URL after login:', page.url());
    
    const afterText = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log('   Body:', afterText.substring(0, 300));
  } else {
    console.log('   ✗ No password field — checking for 2FA or other state');
    const allInputs = await page.$$eval('input:visible, input', els => els.map(e => ({
      type: e.type, name: e.name, id: e.id, placeholder: e.placeholder
    })));
    console.log('   All inputs:', JSON.stringify(allInputs));
  }
  
  // Step 5: Check if logged in
  console.log('\n5. Checking login state...');
  const currentUrl = page.url();
  console.log('   Current URL:', currentUrl);
  
  if (currentUrl.includes('candidates') || currentUrl.includes('user') || currentUrl.includes('dashboard')) {
    console.log('   ✓ Logged in!');
    
    // Navigate to candidates
    console.log('6. Going to candidates...');
    await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${outDir}/vue-04-candidates-list.png`, fullPage: false });
    console.log('   URL:', page.url());
    
    // Click first candidate
    const rows = await page.$$('tr.v-data-table__tr, tr[class*="row"], .candidate-row, table tbody tr');
    console.log('   Rows found:', rows.length);
    
    if (rows.length > 0) {
      await rows[0].click();
      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${outDir}/vue-05-candidate-preview.png`, fullPage: false });
      console.log('   ✓ Candidate preview opened');
      
      // Capture all tabs
      const tabTexts = ['Atividades', 'Arquivos', 'Curriculo'];
      for (const tabText of tabTexts) {
        const tab = await page.$(`[role="tab"]:has-text("${tabText}"), .v-tab:has-text("${tabText}"), button:has-text("${tabText}")`);
        if (tab) {
          await tab.click();
          await page.waitForTimeout(3000);
          const safeName = tabText.toLowerCase().replace(/\s+/g, '-');
          await page.screenshot({ path: `${outDir}/vue-tab-${safeName}.png`, fullPage: false });
          console.log(`   ✓ Tab "${tabText}" captured`);
        } else {
          console.log(`   ✗ Tab "${tabText}" not found`);
        }
      }
    }
  } else {
    console.log('   ✗ Not logged in — may need 2FA');
    // Check for 2FA
    const codeInput = await page.$('input[maxlength="6"], input[placeholder*="código"], input[placeholder*="code"]');
    if (codeInput) {
      console.log('   ⚠ 2FA code required');
    }
  }
  
  await browser.close();
  console.log('\n=== Done ===');
})();
