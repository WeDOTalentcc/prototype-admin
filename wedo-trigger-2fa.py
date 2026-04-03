import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {
    "email": "paulo.moraes@wedotalent.cc",
    "password": "Rodesia94"
}

CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

async def take_screenshot(page, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    await page.screenshot(path=filepath, full_page=False)
    print(f"[SCREENSHOT] {name}.png")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROMIUM_PATH,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("[1] Going to WeDOTalent...")
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)

        print("[2] Filling email...")
        email_input = page.locator('input[placeholder*="email" i], input[type="text"]').first
        await email_input.fill(CREDS["email"])

        print("[3] Clicking Continuar...")
        btn = page.locator('button:has-text("Continuar")').first
        await btn.click()
        await page.wait_for_timeout(3000)

        print("[4] Filling password...")
        pw_input = page.locator('input[type="password"]').first
        await pw_input.wait_for(timeout=5000)
        await pw_input.fill(CREDS["password"])

        print("[5] Clicking Entrar...")
        login_btn = page.locator('button:has-text("Entrar"), button[type="submit"]').first
        await login_btn.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            print("[6] Microsoft SSO - filling password...")
            ms_pw = page.locator('input#i0118, input[name="passwd"]').first
            await ms_pw.wait_for(timeout=5000)
            await ms_pw.fill(CREDS["password"])
            ms_signin = page.locator('input#idSIButton9').first
            await ms_signin.click()
            await page.wait_for_timeout(5000)

            try:
                stay = page.locator('input#idSIButton9')
                if await stay.is_visible():
                    text = await page.evaluate("document.body.innerText")
                    if "Stay signed in" in text:
                        await stay.click()
                        await page.wait_for_timeout(5000)
            except:
                pass

        print(f"[URL] {page.url}")
        await take_screenshot(page, "S3-trigger-2fa")

        page_text = await page.evaluate("document.body.innerText.substring(0, 500)")
        print(f"[PAGE] {page_text[:300]}")

        if "Verificação" in page_text or "código" in page_text.lower():
            print("\n=============================================")
            print("2FA CODE SENT! Check email NOW.")
            print("Then run: python3 wedo-fill-2fa-fast.py <CODE>")
            print("=============================================\n")

        await context.storage_state(path="wedotalent-2fa-pending.json")
        print("[STATE SAVED] wedotalent-2fa-pending.json")
        await browser.close()

asyncio.run(main())
