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
    return filepath

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "login"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROMIUM_PATH,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        if mode == "login":
            context = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await context.new_page()

            print("[1] Navigating to app.wedotalent.cc ...")
            await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-01-login-page")

            print("[2] Filling email...")
            email_input = page.locator('input').first
            await email_input.fill(CREDS["email"])
            await take_screenshot(page, "S3-02-email-filled")

            print("[3] Clicking Continuar...")
            btn = page.locator('button:has-text("Continuar")').first
            await btn.click()
            await page.wait_for_timeout(3000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-03-after-email")

            all_inputs = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, placeholder: i.placeholder, id: i.id, visible: i.offsetParent !== null}))
            """)
            print(f"[INPUTS] {all_inputs}")

            password_input = page.locator('input[type="password"]').first
            try:
                has_pw = await password_input.is_visible()
            except:
                has_pw = False

            if has_pw:
                print("[4] Filling password...")
                await password_input.fill(CREDS["password"])
                await take_screenshot(page, "S3-04-password-filled")

                submit = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Continuar"), button:has-text("Login")').first
                await submit.click()
                await page.wait_for_timeout(5000)
                print(f"[URL after login] {page.url}")
                await take_screenshot(page, "S3-05-after-login")

                all_inputs2 = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, placeholder: i.placeholder, id: i.id}))
                """)
                print(f"[INPUTS after login] {all_inputs2}")
            else:
                print("[INFO] No password field visible")
                page_text = await page.evaluate("document.body.innerText.substring(0, 1000)")
                print(f"[TEXT] {page_text[:500]}")

            await context.storage_state(path="wedotalent-auth-state.json")
            print("[STATE SAVED]")
            print("\n========================================")
            print("If 2FA required, run: python3 capture-wedo-s3.py 2fa <CODE>")
            print("========================================")

        elif mode == "2fa":
            code = sys.argv[2] if len(sys.argv) > 2 else ""
            if not code:
                print("Usage: python3 capture-wedo-s3.py 2fa <CODE>")
                await browser.close()
                return

            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                storage_state="wedotalent-auth-state.json"
            )
            page = await context.new_page()
            await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-2fa-01-before")

            all_inputs = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, placeholder: i.placeholder, id: i.id, visible: i.offsetParent !== null}))
            """)
            print(f"[INPUTS] {all_inputs}")

            code_input = page.locator('input:visible').first
            try:
                await code_input.fill(code)
                await take_screenshot(page, "S3-2fa-02-filled")

                submit = page.locator('button[type="submit"], button:has-text("Verificar"), button:has-text("Confirmar"), button:has-text("Entrar"), button:has-text("Continuar")').first
                await submit.click()
                await page.wait_for_timeout(6000)
                print(f"[URL after 2FA] {page.url}")
                await take_screenshot(page, "S3-2fa-03-after")
            except Exception as e:
                print(f"[ERROR] {e}")

            await context.storage_state(path="wedotalent-auth-state.json")
            print("[STATE SAVED]")

        elif mode == "capture":
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                storage_state="wedotalent-auth-state.json"
            )
            page = await context.new_page()

            pages_to_capture = [
                ("https://app.wedotalent.cc/candidatos", "S3-cap-01-candidatos"),
                ("https://app.wedotalent.cc/vagas", "S3-cap-02-vagas"),
                ("https://app.wedotalent.cc/dashboard", "S3-cap-03-dashboard"),
                ("https://app.wedotalent.cc/configuracoes", "S3-cap-04-config"),
                ("https://app.wedotalent.cc/relatorios", "S3-cap-05-relatorios"),
                ("https://app.wedotalent.cc/automacoes", "S3-cap-06-automacoes"),
            ]

            for url, name in pages_to_capture:
                try:
                    print(f"[CAPTURE] {url}")
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                    await page.wait_for_timeout(2000)
                    print(f"  [URL] {page.url}")
                    await take_screenshot(page, name)
                except Exception as e:
                    print(f"  [ERROR] {e}")

            nav_links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a, [role="link"], [role="menuitem"]')).map(a => ({href: a.href || '', text: (a.innerText || '').trim().substring(0,50)})).filter(a => a.text.length > 0)
            """)
            print(f"\n[NAV LINKS] {nav_links}")

            await context.storage_state(path="wedotalent-auth-state.json")

        elif mode == "preview":
            candidate_id = sys.argv[2] if len(sys.argv) > 2 else ""
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                storage_state="wedotalent-auth-state.json"
            )
            page = await context.new_page()

            await page.goto("https://app.wedotalent.cc/candidatos", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"[URL] {page.url}")
            await take_screenshot(page, "S3-prev-01-list")

            rows = await page.evaluate("""
                () => Array.from(document.querySelectorAll('tr, [role="row"], .candidate-row, .v-data-table__tr')).map((r, i) => ({
                    index: i, text: (r.innerText || '').trim().substring(0, 100)
                })).slice(0, 20)
            """)
            print(f"[ROWS] {rows}")

            if rows and len(rows) > 1:
                print("[CLICK] Clicking first candidate row...")
                row = page.locator('tr, [role="row"], .v-data-table__tr').nth(1)
                await row.click()
                await page.wait_for_timeout(3000)
                await take_screenshot(page, "S3-prev-02-preview-open")

                tabs = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('[role="tab"], .v-tab, .v-btn--variant-text')).map(t => ({text: (t.innerText || '').trim()}))
                """)
                print(f"[TABS] {tabs}")

            await context.storage_state(path="wedotalent-auth-state.json")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
