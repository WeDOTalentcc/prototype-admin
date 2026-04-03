import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"
CODE = sys.argv[1] if len(sys.argv) > 1 else ""

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}")

async def main():
    if not CODE:
        print("Usage: python3 wedo-login-step2.py <CODE>")
        return

    with open("wedotalent-2fa-cookies.json") as f:
        saved = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900}, storage_state=saved["state"])
        page = await context.new_page()

        print("[1] Loading WeDOTalent with saved cookies...")
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        print(f"[URL] {page.url}")

        text = await page.evaluate("document.body.innerText.substring(0,500)")
        visible = await page.evaluate("""
            () => Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null).map(i => ({type:i.type,maxLength:i.maxLength,placeholder:i.placeholder}))
        """)
        print(f"[TEXT] {text[:200]}")
        print(f"[INPUTS] {visible}")

        if len(visible) >= 6 and all(v.get('maxLength') == 1 for v in visible[:6]):
            print(f"[2] 2FA page! Typing code: {CODE}")
            first = page.locator('input:visible').first
            await first.click()
            await page.wait_for_timeout(200)
            for digit in CODE:
                await page.keyboard.press(digit)
                await page.wait_for_timeout(150)

            await page.wait_for_timeout(500)
            await ss(page, "S3-step2-code-typed")

            btn = page.locator('button:has-text("Verificar")')
            is_enabled = await btn.first.is_enabled()
            print(f"[BTN enabled] {is_enabled}")

            if is_enabled:
                await btn.first.click()
                await page.wait_for_timeout(8000)
                print(f"[URL after 2FA] {page.url}")
                await ss(page, "S3-step2-success")
                final = await page.evaluate("document.body.innerText.substring(0,500)")
                print(f"[RESULT] {final[:300]}")
                await context.storage_state(path="wedotalent-logged-in.json")
                print("[LOGGED IN STATE SAVED]")
            else:
                print("[ERROR] Button disabled, trying force click via JS...")
                await page.evaluate("document.querySelector('button').removeAttribute('disabled')")
                await page.wait_for_timeout(500)
                try:
                    await btn.first.click(force=True)
                    await page.wait_for_timeout(8000)
                    print(f"[URL] {page.url}")
                    await ss(page, "S3-step2-force")
                except Exception as e:
                    print(f"[ERROR] {e}")
                    await ss(page, "S3-step2-error")
        elif len(visible) == 1:
            print("[SINGLE INPUT] Filling code...")
            await page.locator('input:visible').first.fill(CODE)
            await page.locator('button:has-text("Verificar"), button:has-text("Continuar")').first.click()
            await page.wait_for_timeout(8000)
            await ss(page, "S3-step2-success")
            await context.storage_state(path="wedotalent-logged-in.json")
        else:
            print(f"[UNEXPECTED] {len(visible)} inputs, not a 2FA page")
            if "email" in str(visible) or "Digite seu email" in text:
                print("[INFO] Back to login page - session expired")
            await ss(page, "S3-step2-unexpected")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
