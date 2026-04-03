import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"
CODE = sys.argv[1] if len(sys.argv) > 1 else ""
CREDS = {"email": "paulo.moraes@wedotalent.cc", "password": "Rodesia94"}

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900})
        page = await context.new_page()

        print("[1] Full login flow...")
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
        email_input = page.locator('input[placeholder*="email" i], input[type="text"]').first
        await email_input.fill(CREDS["email"])
        await page.locator('button:has-text("Continuar")').first.click()
        await page.wait_for_timeout(3000)

        pw = page.locator('input[type="password"]').first
        await pw.wait_for(timeout=5000)
        await pw.fill(CREDS["password"])
        await page.locator('button:has-text("Entrar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            print("[MS SSO]...")
            ms_pw = page.locator('input#i0118').first
            await ms_pw.fill(CREDS["password"])
            await page.locator('input#idSIButton9').first.click()
            await page.wait_for_timeout(5000)
            try:
                if await page.locator('input#idSIButton9').is_visible():
                    await page.locator('input#idSIButton9').click()
                    await page.wait_for_timeout(5000)
            except: pass

        print(f"[URL] {page.url}")
        await ss(page, "S3-2fa-ready")

        visible = await page.evaluate("""
            () => Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null).map(i => ({type:i.type,maxLength:i.maxLength,placeholder:i.placeholder}))
        """)
        print(f"[INPUTS] {visible}")

        if len(visible) >= 6 and CODE:
            print(f"[2] Filling 2FA: {CODE}")
            for i, d in enumerate(CODE[:6]):
                inp = page.locator('input:visible').nth(i)
                await inp.click()
                await page.wait_for_timeout(50)
                await inp.press_sequentially(d)
                await page.wait_for_timeout(100)

            await ss(page, "S3-2fa-filled")
            await page.wait_for_timeout(1000)

            btn = page.locator('button:has-text("Verificar Código"), button:has-text("Verificar")')
            is_enabled = await btn.first.is_enabled()
            print(f"[BTN enabled] {is_enabled}")

            if not is_enabled:
                print("[WAIT] Button disabled, waiting...")
                await page.wait_for_timeout(2000)
                is_enabled = await btn.first.is_enabled()
                print(f"[BTN enabled after wait] {is_enabled}")

            if is_enabled:
                await btn.first.click()
                await page.wait_for_timeout(8000)
                print(f"[URL after 2FA] {page.url}")
                await ss(page, "S3-2fa-success")
                text = await page.evaluate("document.body.innerText.substring(0,500)")
                print(f"[PAGE] {text[:300]}")
                await context.storage_state(path="wedotalent-logged-in.json")
                print("[LOGGED IN STATE SAVED]")
            else:
                print("[ERROR] Button still disabled")
                await ss(page, "S3-2fa-btn-disabled")
        elif CODE:
            print(f"[SINGLE] Filling code: {CODE}")
            inp = page.locator('input:visible').first
            await inp.fill(CODE)
            await page.locator('button:has-text("Verificar")').first.click()
            await page.wait_for_timeout(8000)
            await ss(page, "S3-2fa-success")
            await context.storage_state(path="wedotalent-logged-in.json")
        else:
            print("[NO CODE] Provide code as argument")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
