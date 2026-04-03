import { chromium } from 'playwright';

const SCREENSHOTS_DIR = '/home/runner/workspace/.agents/outputs/screenshots';

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/home/runner/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true
  });
  
  const page = await context.newPage();
  
  console.log('[1/6] Abrindo login...');
  await page.goto('https://app.wedotalent.cc/login', { waitUntil: 'networkidle', timeout: 30000 });
  await page.screenshot({ path: `${SCREENSHOTS_DIR}/vue-01-login-page.jpg`, type: 'jpeg', quality: 85 });
  console.log('Screenshot: vue-01-login-page.jpg');
  
  console.log('[2/6] Preenchendo credenciais...');
  
  const emailSelectors = ['input[type="email"]', 'input[name="email"]', '#email', 'input[placeholder*="email" i]', 'input[placeholder*="Email" i]'];
  let emailFilled = false;
  for (const sel of emailSelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        await el.fill('paulo.moraes@wedotalent.cc');
        emailFilled = true;
        console.log(`  Email preenchido via: ${sel}`);
        break;
      }
    } catch(e) {}
  }
  if (!emailFilled) {
    const inputs = await page.$$('input');
    console.log(`  Inputs encontrados: ${inputs.length}`);
    for (let i = 0; i < inputs.length; i++) {
      const type = await inputs[i].getAttribute('type');
      const name = await inputs[i].getAttribute('name');
      const placeholder = await inputs[i].getAttribute('placeholder');
      console.log(`  Input ${i}: type=${type} name=${name} placeholder=${placeholder}`);
    }
    if (inputs.length > 0) {
      await inputs[0].fill('paulo.moraes@wedotalent.cc');
      console.log('  Email preenchido no primeiro input');
    }
  }

  const pwdSelectors = ['input[type="password"]', 'input[name="password"]', '#password'];
  for (const sel of pwdSelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        await el.fill('Rodesia94');
        console.log(`  Senha preenchida via: ${sel}`);
        break;
      }
    } catch(e) {}
  }

  await page.screenshot({ path: `${SCREENSHOTS_DIR}/vue-02-login-filled.jpg`, type: 'jpeg', quality: 85 });
  console.log('Screenshot: vue-02-login-filled.jpg');

  console.log('[3/6] Clicando login...');
  const btnSelectors = ['button[type="submit"]', 'button:has-text("Entrar")', 'button:has-text("Login")', 'button:has-text("Sign in")', '.v-btn:has-text("Entrar")'];
  for (const sel of btnSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn) {
        await btn.click();
        console.log(`  Botão clicado via: ${sel}`);
        break;
      }
    } catch(e) {}
  }

  console.log('[4/6] Aguardando resposta (pode pedir 2FA)...');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${SCREENSHOTS_DIR}/vue-03-after-login.jpg`, type: 'jpeg', quality: 85 });
  console.log('Screenshot: vue-03-after-login.jpg');

  const currentUrl = page.url();
  console.log(`  URL atual: ${currentUrl}`);
  
  const pageText = await page.textContent('body');
  if (pageText.includes('código') || pageText.includes('code') || pageText.includes('2FA') || pageText.includes('verificação') || pageText.includes('verification')) {
    console.log('\n⚠️  2FA DETECTADO — preciso do código para continuar.');
    console.log('  Envie o código 2FA para prosseguir.');
  } else if (currentUrl.includes('dashboard') || currentUrl.includes('candidates') || currentUrl.includes('search')) {
    console.log('\n✅ Login bem-sucedido! Redirecionado para:', currentUrl);
  } else {
    console.log('\n📋 Estado pós-login — verificar screenshot vue-03-after-login.jpg');
  }

  const cookies = await context.cookies();
  const fs = await import('fs');
  fs.writeFileSync('/tmp/wedotalent-cookies.json', JSON.stringify(cookies, null, 2));
  console.log(`  ${cookies.length} cookies salvos em /tmp/wedotalent-cookies.json`);

  await context.storageState({ path: '/tmp/wedotalent-storage.json' });
  console.log('  Storage state salvo para reusar sessão');

  await browser.close();
  console.log('\nBrowser fechado. Verificar screenshots na pasta.');
}

main().catch(e => {
  console.error('ERRO:', e.message);
  process.exit(1);
});
