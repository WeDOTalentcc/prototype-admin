import asyncio
import os
import json
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {"email": "paulo.moraes@wedotalent.cc", "password": "Rodesia94"}
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900})
        page = await context.new_page()

        cdp = await page.context.new_cdp_session(page)

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

        await ss(page, "S3-step1-2fa-page")
        text = await page.evaluate("document.body.innerText.substring(0,300)")
        print(f"[PAGE] {text[:200]}")

        cookies = await context.cookies()
        state = await context.storage_state()
        with open("wedotalent-2fa-cookies.json", "w") as f:
            json.dump({"cookies": cookies, "state": state, "url": page.url}, f)

        print("[SAVED] Cookies and state saved")
        print("2FA code sent to email. Now run step2 with the code.")

        await browser.close()

asyncio.run(main())
