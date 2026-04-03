import asyncio, os, sys, json
from playwright.async_api import async_playwright

CODE = sys.argv[1] if len(sys.argv) > 1 else ""
SSDIR = "plataforma-lia/docs/screenshots/session3"
os.makedirs(SSDIR, exist_ok=True)
CHROMIUM = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"

async def main():
    if not CODE or len(CODE) != 6:
        print("Usage: python3 wedo-login-v2.py <6-digit-code>")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROMIUM, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await browser.new_context(viewport={"width":1440,"height":900})
        page = await ctx.new_page()

        print("[1] Login...", flush=True)
        await page.goto("https://app.wedotalent.cc/", wait_until="networkidle", timeout=30000)
        await page.locator('input[type="text"]').first.fill("paulo.moraes@wedotalent.cc")
        await page.locator('button:has-text("Continuar")').first.click()
        await page.wait_for_timeout(3000)

        pw = page.locator('input[type="password"]').first
        await pw.wait_for(timeout=5000)
        await pw.fill("Rodesia94")
        await page.locator('button:has-text("Entrar"), button[type="submit"]').first.click()
        await page.wait_for_timeout(5000)

        if "microsoftonline" in page.url:
            await page.locator("input#i0118").first.fill("Rodesia94")
            await page.locator("input#idSIButton9").first.click()
            await page.wait_for_timeout(5000)

        print(f"[URL] {page.url}", flush=True)

        result = await page.evaluate("""(code) => {
            const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null && i.maxLength === 1);
            if (inputs.length < 6) return {ok: false, msg: 'Not enough inputs: ' + inputs.length};
            
            for (let i = 0; i < 6; i++) {
                const inp = inputs[i];
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(inp, code[i]);
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
                inp.dispatchEvent(new KeyboardEvent('keydown', {key: code[i], code: 'Digit' + code[i], bubbles: true}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {key: code[i], code: 'Digit' + code[i], bubbles: true}));
            }
            
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
            return {ok: true, btnText: btn?.textContent, btnDisabled: btn?.disabled, inputValues: inputs.slice(0,6).map(i => i.value)};
        }""", CODE)
        print(f"[FILL] {result}", flush=True)

        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{SSDIR}/S3-v2-filled.png")

        btn_state = await page.evaluate("""() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
            return {disabled: btn?.disabled, text: btn?.textContent};
        }""")
        print(f"[BTN] {btn_state}", flush=True)

        if btn_state.get("disabled"):
            print("[TRY] Using Vue reactivity trigger...", flush=True)
            await page.evaluate("""(code) => {
                const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null && i.maxLength === 1);
                for (let i = 0; i < 6; i++) {
                    const inp = inputs[i];
                    inp.focus();
                    inp.value = code[i];
                    inp.dispatchEvent(new Event('input', {bubbles: true, cancelable: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true, cancelable: true}));
                    
                    // Try triggering Vue's v-model
                    const ev = new InputEvent('input', {bubbles: true, cancelable: true, data: code[i], inputType: 'insertText'});
                    inp.dispatchEvent(ev);
                }
            }""", CODE)
            await page.wait_for_timeout(500)

            btn_state2 = await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
                return {disabled: btn?.disabled};
            }""")
            print(f"[BTN2] {btn_state2}", flush=True)

        if btn_state.get("disabled", True):
            print("[TRY] Clipboard paste approach...", flush=True)
            for i in range(6):
                inp = page.locator("input:visible").nth(i)
                await inp.click()
                await page.wait_for_timeout(100)
                await inp.fill(CODE[i])
                await page.wait_for_timeout(100)

            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{SSDIR}/S3-v2-fill-method.png")

            btn_state3 = await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
                return {disabled: btn?.disabled};
            }""")
            print(f"[BTN3] {btn_state3}", flush=True)

        if btn_state.get("disabled", True):
            print("[TRY] Type method...", flush=True)
            for i in range(6):
                inp = page.locator("input:visible").nth(i)
                await inp.click()
                await inp.press_sequentially(CODE[i], delay=50)
                await page.wait_for_timeout(100)

            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{SSDIR}/S3-v2-type-method.png")

            btn_state4 = await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
                const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null && i.maxLength === 1);
                return {disabled: btn?.disabled, values: inputs.map(i => i.value)};
            }""")
            print(f"[BTN4] {btn_state4}", flush=True)

        final_btn = await page.evaluate("""() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
            return {disabled: btn?.disabled};
        }""")

        if not final_btn.get("disabled"):
            print("[CLICK] Verificar Código!", flush=True)
            await page.locator('button:has-text("Verificar")').first.click()
            await page.wait_for_timeout(8000)
            print(f"[URL] {page.url}", flush=True)
            await page.screenshot(path=f"{SSDIR}/S3-v2-result.png")
            body = await page.evaluate("document.body.innerText.substring(0,600)")
            print(f"[BODY] {body[:300]}", flush=True)
            if "Verificação" not in body and "inválido" not in body:
                print("[SUCCESS]", flush=True)
                await ctx.storage_state(path="wedotalent-logged-in.json")
                await page.goto("https://app.wedotalent.cc/candidatos", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                await page.screenshot(path=f"{SSDIR}/S3-v2-candidatos.png")
        else:
            print("[FAILED] Could not enable button with any method", flush=True)
            await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Verificar'));
                if (btn) btn.disabled = false;
            }""")
            await page.locator('button:has-text("Verificar")').first.click(force=True)
            await page.wait_for_timeout(8000)
            await page.screenshot(path=f"{SSDIR}/S3-v2-force-result.png")
            print(f"[URL] {page.url}", flush=True)

        await browser.close()
        print("[DONE]", flush=True)

asyncio.run(main())
