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

async def take_screenshot(page, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    await page.screenshot(path=filepath, full_page=False)
    print(f"[SCREENSHOT] {name}.png")

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "ms-login"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROMIUM_PATH,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            storage_state="wedotalent-auth-state.json"
        )
        page = await context.new_page()

        if mode == "ms-login":
            print("[1] Loading saved state, going to WeDOTalent...")
            await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            current_url = page.url
            print(f"[URL] {current_url}")
            await take_screenshot(page, "S3-ms-01-current")

            if "microsoftonline" in current_url:
                print("[2] On MS login, filling password...")
                pw_input = page.locator('input#i0118, input[name="passwd"]').first
                await pw_input.fill(CREDS["password"])
                await take_screenshot(page, "S3-ms-02-pw-filled")

                sign_in = page.locator('input#idSIButton9, button:has-text("Sign in")').first
                await sign_in.click()
                await page.wait_for_timeout(5000)
                print(f"[URL after MS sign-in] {page.url}")
                await take_screenshot(page, "S3-ms-03-after-signin")

                stay_signed = page.locator('input#idSIButton9, button:has-text("Yes"), input#idBtn_Back').first
                try:
                    is_visible = await stay_signed.is_visible()
                    if is_visible:
                        text = await page.evaluate("document.body.innerText.substring(0, 500)")
                        print(f"[PAGE TEXT] {text[:300]}")
                        if "Stay signed in" in text or "Permanecer" in text:
                            yes_btn = page.locator('input#idSIButton9').first
                            await yes_btn.click()
                            await page.wait_for_timeout(5000)
                        elif "Approve" in text or "authenticator" in text.lower():
                            print("[MFA] Microsoft Authenticator required!")
                except:
                    pass

                print(f"[URL final] {page.url}")
                await take_screenshot(page, "S3-ms-04-final")

                page_text = await page.evaluate("document.body.innerText.substring(0, 1000)")
                print(f"[PAGE TEXT] {page_text[:500]}")

                all_inputs = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, placeholder: i.placeholder, id: i.id, visible: i.offsetParent !== null}))
                """)
                print(f"[INPUTS] {all_inputs}")

            elif "wedotalent" in current_url:
                print("[OK] Already on WeDOTalent!")
                email_input = page.locator('input').first
                try:
                    has_input = await email_input.is_visible()
                    if has_input:
                        print("[INFO] Login page again, need to re-login")
                        await email_input.fill(CREDS["email"])
                        btn = page.locator('button:has-text("Continuar")').first
                        await btn.click()
                        await page.wait_for_timeout(3000)

                        pw_input = page.locator('input[type="password"]').first
                        try:
                            has_pw = await pw_input.is_visible()
                            if has_pw:
                                await pw_input.fill(CREDS["password"])
                                submit = page.locator('button[type="submit"], button:has-text("Entrar")').first
                                await submit.click()
                                await page.wait_for_timeout(5000)
                                print(f"[URL after re-login] {page.url}")
                                await take_screenshot(page, "S3-ms-05-relogin")

                                if "microsoftonline" in page.url:
                                    pw2 = page.locator('input#i0118, input[name="passwd"]').first
                                    await pw2.fill(CREDS["password"])
                                    signin2 = page.locator('input#idSIButton9').first
                                    await signin2.click()
                                    await page.wait_for_timeout(5000)
                                    print(f"[URL after MS] {page.url}")
                                    await take_screenshot(page, "S3-ms-06-after-ms")
                        except:
                            pass
                except:
                    pass
            else:
                print(f"[UNKNOWN] On unexpected page: {current_url}")

            await context.storage_state(path="wedotalent-auth-state.json")
            print("[STATE SAVED]")

        elif mode == "2fa":
            code = sys.argv[2] if len(sys.argv) > 2 else ""
            if not code:
                print("Usage: python3 capture-wedo-ms-login.py 2fa <CODE>")
                await browser.close()
                return

            await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-2fa-01")

            code_input = page.locator('input:visible').first
            await code_input.fill(code)
            submit = page.locator('button:visible').first
            await submit.click()
            await page.wait_for_timeout(6000)
            print(f"[URL after 2FA] {page.url}")
            await take_screenshot(page, "S3-2fa-02-after")

            await context.storage_state(path="wedotalent-auth-state.json")
            print("[STATE SAVED]")

        elif mode == "capture":
            await page.goto("https://app.wedotalent.cc/candidatos", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-cap-01-candidatos")

            nav = await page.evaluate("""
                () => Array.from(document.querySelectorAll('nav a, .v-list-item, .sidebar a')).map(a => ({href: a.href || '', text: (a.innerText || '').trim().substring(0,50)})).filter(a => a.text)
            """)
            print(f"[NAV] {nav}")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
