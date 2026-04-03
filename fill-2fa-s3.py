import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

CODE = sys.argv[1] if len(sys.argv) > 1 else "244976"

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
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            storage_state="wedotalent-auth-state.json"
        )
        page = await context.new_page()

        print("[1] Loading WeDOTalent...")
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        print(f"[URL] {page.url}")
        await take_screenshot(page, "S3-2fa-01-page")

        page_text = await page.evaluate("document.body.innerText.substring(0, 500)")
        print(f"[TEXT] {page_text[:300]}")

        all_inputs = await page.evaluate("""
            () => Array.from(document.querySelectorAll('input')).map(i => ({
                type: i.type, name: i.name, placeholder: i.placeholder, 
                id: i.id, visible: i.offsetParent !== null, maxLength: i.maxLength
            }))
        """)
        print(f"[INPUTS] {all_inputs}")

        visible_inputs = [i for i in all_inputs if i.get('visible')]
        print(f"[VISIBLE INPUTS] {len(visible_inputs)}")

        if len(visible_inputs) >= 6:
            print(f"[2] Filling 6-digit code: {CODE}")
            for i, digit in enumerate(CODE):
                input_el = page.locator('input:visible').nth(i)
                await input_el.fill(digit)
                await page.wait_for_timeout(100)
            
            await take_screenshot(page, "S3-2fa-02-code-filled")

            print("[3] Clicking Verificar Código...")
            verify_btn = page.locator('button:has-text("Verificar"), button:has-text("Verificar Código")').first
            await verify_btn.click()
            await page.wait_for_timeout(8000)
            print(f"[URL after verify] {page.url}")
            await take_screenshot(page, "S3-2fa-03-after-verify")

            page_text2 = await page.evaluate("document.body.innerText.substring(0, 1000)")
            print(f"[TEXT after verify] {page_text2[:400]}")

        elif len(visible_inputs) == 1:
            print(f"[2] Single input field, filling code: {CODE}")
            input_el = page.locator('input:visible').first
            await input_el.fill(CODE)
            await take_screenshot(page, "S3-2fa-02-code-filled")

            verify_btn = page.locator('button:has-text("Verificar"), button:has-text("Continuar"), button[type="submit"]').first
            await verify_btn.click()
            await page.wait_for_timeout(8000)
            print(f"[URL after verify] {page.url}")
            await take_screenshot(page, "S3-2fa-03-after-verify")
        else:
            print(f"[WARN] Unexpected number of visible inputs: {len(visible_inputs)}")
            if "Verificação" not in page_text and "candidat" in page_text.lower():
                print("[INFO] Might already be logged in!")

        await context.storage_state(path="wedotalent-auth-state.json")
        print("[STATE SAVED]")

        await browser.close()
        print("[DONE]")

asyncio.run(main())
