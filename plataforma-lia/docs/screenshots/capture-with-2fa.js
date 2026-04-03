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
  
  // Email
  const emailInput = await page.$('input[type="text"], input[type="email"]');
  await emailInput.fill('paulo.moraes@wedotalent.cc');
  await page.waitForTimeout(500);
  
  // Continuar
  const continueBtn = await page.$('button:has-text("Continuar")');
  await continueBtn.click();
  await page.waitForTimeout(3000);
  
  // Password
  const passField = await page.$('input[type="password"]');
  await passField.fill('Rodesia94');
  const loginBtn = await page.$('button:has-text("Entrar")');
  await loginBtn.click();
  await page.waitForTimeout(5000);
  
  // 2FA Code
  console.log('Entering 2FA code:', CODE_2FA);
  const codeInputs = await page.$$('input[maxlength="1"]');
  if (codeInputs.length >= 6) {
    for (let i = 0; i < 6; i++) {
      await codeInputs[i].fill(CODE_2FA[i]);
      await page.waitForTimeout(100);
    }
    console.log('   ✓ 2FA code filled');
  } else {
    const singleInput = await page.$('input[maxlength="6"]');
    if (singleInput) {
      await singleInput.fill(CODE_2FA);
      console.log('   ✓ 2FA code filled (single input)');
    } else {
      console.log('   ✗ No 2FA inputs found, count:', codeInputs.length);
    }
  }
  
  // Verificar Código
  const verifyBtn = await page.$('button:has-text("Verificar"), button:has-text("Confirmar")');
  if (verifyBtn) {
    await verifyBtn.click();
    console.log('   ✓ Verify clicked');
  } else {
    await page.keyboard.press('Enter');
  }
  
  await page.waitForTimeout(8000);
  await page.screenshot({ path: `${outDir}/vue-10-after-2fa.png`, fullPage: false });
  console.log('   URL after 2FA:', page.url());
  
  // Check if logged in
  const url = page.url();
  if (!url.includes('wedotalent.cc') || url === 'https://app.wedotalent.cc/') {
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 300));
    console.log('   Body:', bodyText.substring(0, 200));
    console.log('   ✗ May not be logged in. Stopping.');
    await browser.close();
    return;
  }
  
  console.log('   ✓ Logged in!\n');
  
  // === CANDIDATES LIST ===
  console.log('--- CANDIDATES ---');
  await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${outDir}/vue-11-candidates-list.png`, fullPage: false });
  console.log('   URL:', page.url());
  
  // Count candidates
  const candidateCount = await page.evaluate(() => {
    const rows = document.querySelectorAll('tr, .candidate-row, [class*="candidate"]');
    return rows.length;
  });
  console.log('   Candidate elements:', candidateCount);
  
  // Get page structure
  const pageStructure = await page.evaluate(() => {
    const els = document.querySelectorAll('.v-card, .v-data-table, table, [role="table"]');
    return Array.from(els).map(e => ({ tag: e.tagName, class: e.className.substring(0, 100) }));
  });
  console.log('   Structure:', JSON.stringify(pageStructure).substring(0, 300));
  
  // Click first candidate to open preview
  console.log('\n--- CANDIDATE PREVIEW ---');
  const firstRow = await page.$('table tbody tr, .v-data-table tbody tr, tr.v-data-table__tr');
  if (firstRow) {
    await firstRow.click();
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${outDir}/vue-12-candidate-preview.png`, fullPage: false });
    console.log('   ✓ Candidate preview opened');
    console.log('   URL:', page.url());
    
    // Scroll down to see more
    await page.evaluate(() => {
      const drawer = document.querySelector('.v-navigation-drawer, [class*="drawer"], [class*="preview"], [class*="sidebar"]');
      if (drawer) drawer.scrollTop = drawer.scrollHeight / 3;
      else window.scrollTo(0, 300);
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${outDir}/vue-12b-candidate-scroll1.png`, fullPage: false });
    
    await page.evaluate(() => {
      const drawer = document.querySelector('.v-navigation-drawer, [class*="drawer"], [class*="preview"], [class*="sidebar"]');
      if (drawer) drawer.scrollTop = drawer.scrollHeight * 2 / 3;
      else window.scrollTo(0, 600);
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${outDir}/vue-12c-candidate-scroll2.png`, fullPage: false });
    
    // Click tabs
    const tabs = ['Atividades', 'Arquivos', 'Currículo', 'Curriculo'];
    for (const tab of tabs) {
      const tabEl = await page.$(`[role="tab"]:has-text("${tab}"), .v-tab:has-text("${tab}"), button:has-text("${tab}")`);
      if (tabEl) {
        await tabEl.click();
        await page.waitForTimeout(3000);
        const safeName = tab.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '-');
        await page.screenshot({ path: `${outDir}/vue-13-tab-${safeName}.png`, fullPage: false });
        console.log(`   ✓ Tab "${tab}" captured`);
      }
    }
    
    // Look for tabs we might have missed
    const allTabs = await page.$$eval('[role="tab"], .v-tab, .v-btn--variant-text', els => 
      els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 30)
    );
    console.log('   Available tabs:', allTabs);
    
  } else {
    console.log('   ✗ No candidate rows found');
    
    // Try clicking any clickable element
    const links = await page.$$eval('a, [role="link"], .clickable', els => 
      els.map(e => ({ text: e.textContent.trim().substring(0, 50), href: e.href })).slice(0, 10)
    );
    console.log('   Links found:', JSON.stringify(links).substring(0, 500));
  }
  
  // Full page screenshot
  await page.screenshot({ path: `${outDir}/vue-14-full-page.png`, fullPage: true });
  
  await browser.close();
  console.log('\n=== Done ===');
})();
