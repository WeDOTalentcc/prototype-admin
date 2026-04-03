import asyncio
import os
import sys
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDS = {"email": "paulo.moraes@wedotalent.cc", "password": "Rodesia94"}
CHROMIUM_PATH = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

CODE = sys.argv[1] if len(sys.argv) > 1 else ""

async def ss(page, name):
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=False)
    print(f"[SS] {name}", flush=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM_PATH, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":1440,"height":900})
        page = await context.new_page()

        print("[1] Login...", flush=True)
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
        await page.locator('input[placeholder*="email" i], input[type="text"]').first.fill(CREDS["email"])
        await page.locator('button:has-text("Continuar")').first.click()
        await page.wait_for_timeout(3000)
        pw = page.locator('input[type="password"]').first
        await pw.wait_for(timeout=5000)
        await pw.fill(CREDS["password"])
        await page.locator('button:has-text("Entrar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            await page.locator('input#i0118').first.fill(CREDS["password"])
            await page.locator('input#idSIButton9').first.click()
            await page.wait_for_timeout(5000)

        print(f"[URL] {page.url}", flush=True)
        await ss(page, "S3-final-2fa")

        if not CODE:
            print("[NO CODE] Provide code as argv[1]", flush=True)
            await browser.close()
            return

        print(f"[2] Typing 2FA: {CODE}", flush=True)

        inputs = page.locator('input:visible')
        input_count = await inputs.count()
        print(f"[INPUTS] {input_count} visible", flush=True)

        if input_count >= 6:
            await inputs.first.click()
            await page.wait_for_timeout(200)
            for digit in CODE:
                await page.keyboard.press(digit)
                await page.wait_for_timeout(150)
        else:
            await inputs.first.fill(CODE)

        await page.wait_for_timeout(1000)
        await ss(page, "S3-final-typed")

        btn = page.locator('button:has-text("Verificar")')
        enabled = await btn.first.is_enabled()
        print(f"[BTN] enabled={enabled}", flush=True)

        if enabled:
            await btn.first.click()
        else:
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1000)
            enabled = await btn.first.is_enabled()
            if enabled:
                await btn.first.click()
            else:
                await btn.first.click(force=True)

        await page.wait_for_timeout(8000)
        print(f"[URL] {page.url}", flush=True)
        await ss(page, "S3-final-result")

        body = await page.evaluate("document.body.innerText.substring(0,800)")
        print(f"[BODY] {body[:400]}", flush=True)

        if "Verificação" not in body:
            print("[LOGIN OK]", flush=True)
            await context.storage_state(path="wedotalent-logged-in.json")

            await page.goto("https://app.wedotalent.cc/candidatos", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            await ss(page, "S3-final-candidatos")

            rows = page.locator('tr, [role="row"], .candidate-row, .v-data-table__tr')
            cnt = await rows.count()
            print(f"[ROWS] {cnt}", flush=True)
            if cnt > 1:
                await rows.nth(1).click()
                await page.wait_for_timeout(5000)
                await ss(page, "S3-final-preview")

        await browser.close()
        print("[DONE]", flush=True)

asyncio.run(main())
