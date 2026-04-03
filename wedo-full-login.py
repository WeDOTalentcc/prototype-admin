import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {
    "email": "paulo.moraes@wedotalent.cc",
    "password": "Rodesia94"
}

CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

CODE = sys.argv[1] if len(sys.argv) > 1 else ""

async def take_screenshot(page, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    await page.screenshot(path=filepath, full_page=False)
    print(f"[SCREENSHOT] {name}.png")

async def main():
    if not CODE:
        print("Usage: python3 wedo-full-login.py <2FA_CODE>")
        print("The code must be fresh - run this immediately after receiving it")
        return

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
        await take_screenshot(page, "S3-full-01-login")

        print("[2] Filling email...")
        email_input = page.locator('input[placeholder*="email" i], input[type="text"]').first
        await email_input.fill(CREDS["email"])

        print("[3] Clicking Continuar...")
        btn = page.locator('button:has-text("Continuar")').first
        await btn.click()
        await page.wait_for_timeout(3000)
        await take_screenshot(page, "S3-full-02-after-email")

        print("[4] Filling password...")
        pw_input = page.locator('input[type="password"]').first
        try:
            await pw_input.wait_for(timeout=5000)
            await pw_input.fill(CREDS["password"])

            print("[5] Clicking Entrar...")
            login_btn = page.locator('button:has-text("Entrar"), button[type="submit"]').first
            await login_btn.click()
            await page.wait_for_timeout(5000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-full-03-after-password")
        except Exception as e:
            print(f"[ERROR password] {e}")
            await take_screenshot(page, "S3-full-03-error")

        if "microsoftonline" in page.url:
            print("[6] Microsoft SSO detected, filling password...")
            ms_pw = page.locator('input#i0118, input[name="passwd"]').first
            await ms_pw.wait_for(timeout=5000)
            await ms_pw.fill(CREDS["password"])
            ms_signin = page.locator('input#idSIButton9').first
            await ms_signin.click()
            await page.wait_for_timeout(5000)
            print(f"[URL after MS] {page.url}")
            await take_screenshot(page, "S3-full-04-after-ms")

            try:
                stay = page.locator('input#idSIButton9')
                if await stay.is_visible():
                    text = await page.evaluate("document.body.innerText")
                    if "Stay signed in" in text:
                        await stay.click()
                        await page.wait_for_timeout(5000)
            except:
                pass

        print(f"[URL now] {page.url}")
        await take_screenshot(page, "S3-full-05-before-2fa")

        page_text = await page.evaluate("document.body.innerText.substring(0, 500)")
        print(f"[PAGE] {page_text[:300]}")

        all_inputs = await page.evaluate("""
            () => Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null).map(i => ({
                type: i.type, name: i.name, placeholder: i.placeholder, id: i.id, maxLength: i.maxLength
            }))
        """)
        print(f"[VISIBLE INPUTS] {all_inputs}")

        if "Verificação" in page_text or "erificação" in page_text or "código" in page_text.lower():
            print(f"[7] 2FA page detected! Filling code: {CODE}")

            if len(all_inputs) >= 6:
                for i, digit in enumerate(CODE[:6]):
                    inp = page.locator('input:visible').nth(i)
                    await inp.click()
                    await inp.fill(digit)
                    await page.wait_for_timeout(150)
            else:
                inp = page.locator('input:visible').first
                await inp.fill(CODE)

            await take_screenshot(page, "S3-full-06-2fa-filled")

            print("[8] Clicking Verificar...")
            verify = page.locator('button:has-text("Verificar")').first
            await verify.click()
            await page.wait_for_timeout(8000)
            print(f"[URL after 2FA] {page.url}")
            await take_screenshot(page, "S3-full-07-after-2fa")

            final_text = await page.evaluate("document.body.innerText.substring(0, 500)")
            print(f"[FINAL PAGE] {final_text[:300]}")

            if "candidat" in final_text.lower() or "dashboard" in page.url or "vaga" in final_text.lower():
                print("[SUCCESS] Logged in!")
                await context.storage_state(path="wedotalent-auth-logged.json")
                print("[STATE SAVED] wedotalent-auth-logged.json")
            else:
                print("[WARN] May not be logged in yet")
                await context.storage_state(path="wedotalent-auth-logged.json")
        else:
            print("[INFO] No 2FA page detected")
            if "candidat" in page_text.lower() or "vaga" in page_text.lower():
                print("[SUCCESS] Already logged in!")
                await context.storage_state(path="wedotalent-auth-logged.json")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
