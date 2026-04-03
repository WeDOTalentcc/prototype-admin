const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
    storageState: undefined
  });
  const page = await context.newPage();
  
  console.log('Step 1: Opening WeDOTalent...');
  await page.goto('https://app.wedotalent.cc', { timeout: 30000, waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  console.log('Step 2: Email...');
  await page.click('input[type="text"]');
  await page.keyboard.type('paulo.moraes@wedotalent.cc', { delay: 20 });
  await page.click('button:has-text("Continuar")');
  await page.waitForTimeout(3000);
  
  console.log('Step 3: Password...');
  await page.click('input[type="password"]');
  await page.keyboard.type('Rodesia94', { delay: 20 });
  await page.click('button:has-text("Entrar")');
  await page.waitForTimeout(5000);
  
  console.log('Step 4: 2FA screen reached');
  await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-2fa-ready.png' });
  
  // Analyze the OTP component structure
  const otpAnalysis = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    const result = [];
    inputs.forEach((input, i) => {
      result.push({
        index: i,
        type: input.type,
        maxLength: input.maxLength,
        className: input.className.substring(0, 80),
        id: input.id,
        name: input.name,
        autocomplete: input.autocomplete,
        parentClass: input.parentElement?.className?.substring(0, 80),
        grandparentClass: input.parentElement?.parentElement?.className?.substring(0, 80),
        visible: input.offsetParent !== null,
        value: input.value,
        tagName: input.tagName
      });
    });
    return result;
  });
  console.log('OTP inputs analysis:', JSON.stringify(otpAnalysis, null, 2));
  
  // Save browser state for step 2
  const cookies = await context.cookies();
  const storageState = await context.storageState();
  const fs = require('fs');
  fs.writeFileSync('/tmp/wedotalent-session.json', JSON.stringify(storageState));
  console.log('Session saved to /tmp/wedotalent-session.json');
  console.log('Cookies:', cookies.length);
  
  // Try OTP via keyboard only approach
  console.log('\nNow waiting for code input...');
  console.log('The 2FA screen is live. Ready for code.');
  
  // Keep browser open - save context
  // Actually, we can't persist the browser. Let's try the code right here.
  // The user should paste the code as argument
  const code = process.argv[2];
  if (code && code.length === 6) {
    console.log('\nEntering code:', code);
    
    // Focus first OTP input
    const firstInput = await page.$('input[maxlength="1"]');
    if (firstInput) {
      await firstInput.click();
      await page.waitForTimeout(300);
      
      // Type each digit - the OTP component should auto-advance focus
      for (const digit of code) {
        await page.keyboard.type(digit, { delay: 100 });
        await page.waitForTimeout(200);
      }
      
      await page.waitForTimeout(500);
      await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-2fa-typed.png' });
      
      // Check values
      const values = await page.$$eval('input[maxlength="1"]', els => els.map(e => e.value));
      console.log('Input values:', values);
      
      // Check button
      const btnDisabled = await page.$eval('button:has-text("Verificar")', el => el.disabled);
      console.log('Verify disabled?', btnDisabled);
      
      if (!btnDisabled) {
        await page.click('button:has-text("Verificar")');
        console.log('✓ Verify clicked!');
        await page.waitForTimeout(10000);
        await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-10-after-2fa.png' });
        console.log('URL:', page.url());
        
        if (page.url() !== 'https://app.wedotalent.cc/') {
          console.log('✓✓✓ LOGGED IN!');
          
          // Navigate to candidates
          await page.goto('https://app.wedotalent.cc/user/candidates', { timeout: 30000, waitUntil: 'networkidle' });
          await page.waitForTimeout(5000);
          await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-11-candidates.png' });
          console.log('Candidates URL:', page.url());
          
          // Full page screenshot
          await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-11-candidates-full.png', fullPage: true });
          
          // Click first row
          const firstRow = await page.$('table tbody tr');
          if (firstRow) {
            await firstRow.click();
            await page.waitForTimeout(5000);
            await page.screenshot({ path: 'plataforma-lia/docs/screenshots/vue-12-preview.png' });
            console.log('✓ Preview opened');
            
            // Scroll
            for (let i = 1; i <= 4; i++) {
              await page.evaluate(s => {
                const drawers = document.querySelectorAll('.v-navigation-drawer, [class*="drawer"], [class*="detail"]');
                for (const d of drawers) {
                  if (d.scrollHeight > d.clientHeight + 50) {
                    d.scrollTop = (d.scrollHeight * s) / 5;
                    return;
                  }
                }
                window.scrollTo(0, s * 250);
              }, i);
              await page.waitForTimeout(1500);
              await page.screenshot({ path: `plataforma-lia/docs/screenshots/vue-12-scroll${i}.png` });
            }
            
            // Tabs
            const tabs = await page.$$eval('[role="tab"], .v-tab', els => 
              els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 30)
            );
            console.log('Tabs:', tabs);
            
            for (const t of tabs) {
              try {
                await page.click(`[role="tab"]:has-text("${t}"), .v-tab:has-text("${t}")`);
                await page.waitForTimeout(3000);
                const name = t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '-');
                await page.screenshot({ path: `plataforma-lia/docs/screenshots/vue-tab-${name}.png` });
                console.log(`✓ Tab "${t}"`);
                
                // Scroll tab content
                await page.evaluate(() => {
                  const drawers = document.querySelectorAll('.v-navigation-drawer, [class*="drawer"]');
                  for (const d of drawers) { if (d.scrollHeight > d.clientHeight) { d.scrollTop = d.scrollHeight / 2; return; }}
                });
                await page.waitForTimeout(1500);
                await page.screenshot({ path: `plataforma-lia/docs/screenshots/vue-tab-${name}-scroll.png` });
              } catch(e) {
                console.log(`✗ Tab "${t}" failed`);
              }
            }
          }
        }
      } else {
        console.log('✗ Button still disabled after typing');
      }
    }
  } else {
    console.log('No code provided as argument');
  }
  
  await browser.close();
  console.log('\n=== Done ===');
})();
