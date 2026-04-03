import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {"email": "paulo.moraes@wedotalent.cc", "password": "Rodesia94"}
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"
CODE_FILE = "/tmp/wedo-2fa-code.txt"

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}", flush=True)

async def main():
    if os.path.exists(CODE_FILE):
        os.remove(CODE_FILE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900})
        page = await context.new_page()

        print("[1] Going to WeDOTalent...", flush=True)
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)

        print("[2] Filling email...", flush=True)
        await page.locator('input[placeholder*="email" i], input[type="text"]').first.fill(CREDS["email"])
        await page.locator('button:has-text("Continuar")').first.click()
        await page.wait_for_timeout(3000)

        print("[3] Filling password...", flush=True)
        pw = page.locator('input[type="password"]').first
        await pw.wait_for(timeout=5000)
        await pw.fill(CREDS["password"])
        await page.locator('button:has-text("Entrar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            print("[MS SSO]...", flush=True)
            await page.locator('input#i0118').first.fill(CREDS["password"])
            await page.locator('input#idSIButton9').first.click()
            await page.wait_for_timeout(5000)

        await ss(page, "S3-single-2fa-ready")
        print(f"[URL] {page.url}", flush=True)
        print("=== 2FA CODE SENT TO EMAIL ===", flush=True)
        print(f"=== Write code to {CODE_FILE} ===", flush=True)

        code = ""
        for i in range(150):
            if os.path.exists(CODE_FILE):
                with open(CODE_FILE) as f:
                    code = f.read().strip()
                if len(code) == 6 and code.isdigit():
                    print(f"[CODE] {code}", flush=True)
                    break
                code = ""
            if i % 10 == 0:
                print(f"[POLL] Waiting for code... ({i}s)", flush=True)
            await asyncio.sleep(1)

        if not code:
            print("[TIMEOUT]", flush=True)
            await browser.close()
            return

        print(f"[4] Typing code: {code}", flush=True)
        first_input = page.locator('input:visible').first
        await first_input.click()
        await page.wait_for_timeout(300)
        for digit in code:
            await page.keyboard.press(digit)
            await page.wait_for_timeout(200)

        await page.wait_for_timeout(1000)
        await ss(page, "S3-single-code-typed")

        btn = page.locator('button:has-text("Verificar")')
        is_enabled = await btn.first.is_enabled()
        print(f"[BTN enabled] {is_enabled}", flush=True)

        if is_enabled:
            await btn.first.click()
        else:
            print("[FORCE click]", flush=True)
            await btn.first.click(force=True)

        await page.wait_for_timeout(8000)
        print(f"[URL after 2FA] {page.url}", flush=True)
        await ss(page, "S3-single-after-2fa")

        final = await page.evaluate("document.body.innerText.substring(0,800)")
        print(f"[PAGE] {final[:400]}", flush=True)

        if "Verificação" not in final and page.url != "https://app.wedotalent.cc/":
            print("[SUCCESS] LOGGED IN!", flush=True)
            await context.storage_state(path="wedotalent-logged-in.json")

            nav_items = await page.evaluate("""
                () => {
                    const els = document.querySelectorAll('a[href], .v-list-item, nav a');
                    return Array.from(els).map(a => ({href: a.href||'', text: (a.innerText||'').trim().substring(0,50)})).filter(a => a.text).slice(0,30);
                }
            """)
            print(f"[NAV] {nav_items}", flush=True)

            await page.goto("https://app.wedotalent.cc/candidatos", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            await ss(page, "S3-cap-candidatos-list")

            rows = page.locator('tr, .v-data-table__tr, [role="row"], .candidate-row')
            count = await rows.count()
            print(f"[ROWS] {count}", flush=True)

            if count > 1:
                await rows.nth(1).click()
                await page.wait_for_timeout(5000)
                await ss(page, "S3-cap-preview-panel")
                print(f"[URL] {page.url}", flush=True)

        await browser.close()
        print("[DONE]", flush=True)

asyncio.run(main())
