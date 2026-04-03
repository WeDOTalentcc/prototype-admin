import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {"email": "paulo.moraes@wedotalent.cc", "password": "Rodesia94"}
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"
CODE_FILE = "/tmp/wedo-2fa-code.txt"
SIGNAL_FILE = "/tmp/wedo-2fa-ready.txt"

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}")

async def main():
    if os.path.exists(CODE_FILE):
        os.remove(CODE_FILE)
    if os.path.exists(SIGNAL_FILE):
        os.remove(SIGNAL_FILE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900})
        page = await context.new_page()

        print("[1] Going to WeDOTalent...")
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)

        print("[2] Filling email...")
        await page.locator('input[placeholder*="email" i], input[type="text"]').first.fill(CREDS["email"])
        await page.locator('button:has-text("Continuar")').first.click()
        await page.wait_for_timeout(3000)

        print("[3] Filling password...")
        pw = page.locator('input[type="password"]').first
        await pw.wait_for(timeout=5000)
        await pw.fill(CREDS["password"])
        await page.locator('button:has-text("Entrar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            print("[MS SSO]...")
            await page.locator('input#i0118').first.fill(CREDS["password"])
            await page.locator('input#idSIButton9').first.click()
            await page.wait_for_timeout(5000)

        await ss(page, "S3-wait-2fa-ready")
        print("[4] 2FA page ready!")

        with open(SIGNAL_FILE, "w") as f:
            f.write("READY")
        print(f"[SIGNAL] Written to {SIGNAL_FILE}")
        print(f"[WAITING] Write 6-digit code to {CODE_FILE}")

        code = ""
        for i in range(120):
            if os.path.exists(CODE_FILE):
                with open(CODE_FILE) as f:
                    code = f.read().strip()
                if len(code) == 6 and code.isdigit():
                    print(f"[CODE RECEIVED] {code}")
                    break
            await asyncio.sleep(1)

        if not code:
            print("[TIMEOUT] No code received in 120s")
            await browser.close()
            return

        print(f"[5] Typing code: {code}")
        first_input = page.locator('input:visible').first
        await first_input.click()
        await page.wait_for_timeout(300)

        for digit in code:
            await page.keyboard.press(digit)
            await page.wait_for_timeout(200)

        await page.wait_for_timeout(1000)
        await ss(page, "S3-wait-code-typed")

        btn = page.locator('button:has-text("Verificar")')
        try:
            is_enabled = await btn.first.is_enabled()
            print(f"[BTN enabled] {is_enabled}")

            if not is_enabled:
                await page.wait_for_timeout(2000)
                is_enabled = await btn.first.is_enabled()

            if is_enabled:
                await btn.first.click()
            else:
                print("[FORCE] Clicking with force...")
                await btn.first.click(force=True)
        except Exception as e:
            print(f"[BTN ERROR] {e}")
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(8000)
        print(f"[URL after 2FA] {page.url}")
        await ss(page, "S3-wait-after-2fa")

        final = await page.evaluate("document.body.innerText.substring(0,800)")
        print(f"[PAGE] {final[:400]}")

        if "/candidatos" in page.url or "dashboard" in page.url or "Candidat" in final or "Funil" in final:
            print("[SUCCESS] LOGGED IN!")
            await context.storage_state(path="wedotalent-logged-in.json")

            pages = [
                ("https://app.wedotalent.cc/candidatos", "S3-cap-candidatos"),
                ("https://app.wedotalent.cc/candidatos", "S3-cap-candidatos-list"),
            ]
            for url, name in pages:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                await ss(page, name)

            nav = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a, [role="listitem"], .v-list-item');
                    return Array.from(links).map(a => ({href: a.href||'', text: (a.innerText||'').trim().substring(0,60)})).filter(a => a.text).slice(0,30);
                }
            """)
            print(f"[NAV] {nav}")

            rows = page.locator('tr, .v-data-table__tr, [role="row"]')
            count = await rows.count()
            print(f"[ROWS] {count} rows found")
            if count > 1:
                await rows.nth(1).click()
                await page.wait_for_timeout(4000)
                await ss(page, "S3-cap-preview-open")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
