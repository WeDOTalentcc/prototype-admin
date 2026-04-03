const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: '/home/runner/workspace/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'
  });
  const context = await browser.newContext({ 
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true 
  });
  const page = await context.newPage();
  
  const baseUrl = 'http://localhost:5000';
  const outDir = 'plataforma-lia/docs/screenshots';
  
  console.log('=== REPLIT APP — Candidate Preview Audit ===');
  
  console.log('1. Navigating to home page...');
  try {
    await page.goto(baseUrl, { timeout: 60000, waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${outDir}/replit-01-homepage.png`, fullPage: false });
    console.log('   ✓ Homepage captured');
    console.log('   URL:', page.url());
    
    const title = await page.title();
    console.log('   Title:', title);
    
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log('   Body preview:', bodyText.substring(0, 200));
  } catch (e) {
    console.log('   ✗ Homepage failed:', e.message.substring(0, 200));
  }
  
  console.log('\n2. Navigating to funil-de-talentos...');
  try {
    await page.goto(`${baseUrl}/funil-de-talentos`, { timeout: 60000, waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${outDir}/replit-02-funil.png`, fullPage: false });
    console.log('   ✓ Funil captured');
    
    const allText = await page.evaluate(() => document.body.innerText.substring(0, 1000));
    console.log('   Content:', allText.substring(0, 300));
    
    // Find candidate rows
    const rows = await page.$$('table tbody tr, [data-testid*="candidate"], [class*="TableRow"], tr');
    console.log('   Table rows found:', rows.length);
    
    if (rows.length > 1) {
      await rows[1].click();
      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${outDir}/replit-03-candidate-opened.png`, fullPage: false });
      console.log('   ✓ Candidate opened');
    }
  } catch (e) {
    console.log('   ✗ Funil failed:', e.message.substring(0, 200));
  }

  // Try to find and click tabs
  console.log('\n3. Looking for tabs...');
  try {
    const tabTexts = ['Perfil Completo', 'Atividades', 'Arquivos', 'Pareceres'];
    for (const tabText of tabTexts) {
      const tab = await page.$(`text="${tabText}"`);
      if (tab) {
        await tab.click();
        await page.waitForTimeout(3000);
        const safeName = tabText.toLowerCase().replace(/\s+/g, '-');
        await page.screenshot({ path: `${outDir}/replit-tab-${safeName}.png`, fullPage: false });
        console.log(`   ✓ Tab "${tabText}" captured`);
        
        // scroll down to see more content
        await page.evaluate(() => {
          const scrollable = document.querySelector('[class*="overflow-y-auto"], [class*="scroll"], main');
          if (scrollable) scrollable.scrollTop = 500;
        });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: `${outDir}/replit-tab-${safeName}-scrolled.png`, fullPage: false });
        console.log(`   ✓ Tab "${tabText}" scrolled captured`);
      } else {
        console.log(`   ✗ Tab "${tabText}" not found`);
      }
    }
  } catch (e) {
    console.log('   ✗ Tab navigation failed:', e.message.substring(0, 200));
  }

  // Print page structure
  console.log('\n4. Page structure:');
  try {
    const buttons = await page.$$eval('button', els => els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 40));
    console.log('   Buttons:', buttons.slice(0, 20).join(' | '));
    
    const links = await page.$$eval('a', els => els.map(e => `${e.textContent.trim().substring(0, 30)} → ${e.href}`).filter(t => !t.startsWith(' →')));
    console.log('   Links:', links.slice(0, 10).join(' | '));
  } catch (e) {
    console.log('   ✗ Structure analysis failed');
  }
  
  await browser.close();
  console.log('\n=== Done ===');
})();
