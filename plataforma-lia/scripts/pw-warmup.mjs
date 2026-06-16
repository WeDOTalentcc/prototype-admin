#!/usr/bin/env node
// Task #1173 — warmup de bundles via headless Chromium real.
//
// Por que isto existe:
//   O warmup por curl (em run-pw-cenario.sh) só busca o HTML de /pt e /pt/chat.
//   Isso força o Turbopack a compilar a ROTA do servidor, mas NÃO os dezenas de
//   chunks JS client-side que o Chromium headless pede em seguida (componentes
//   com dynamic import, locale routing, o chat lazy-loaded). Na primeira
//   navegação real do teste, esses chunks ainda não estão compilados: o
//   `next dev --turbopack` responde 502/"Failed to fetch" enquanto compila, e o
//   `page.goto('/pt')` estoura o timeout de 90s — mesmo com o curl tendo passado
//   em <1s logo antes.
//
//   Este script dirige um Chromium headless (mesmos args da playwright.config.ts)
//   pelas rotas-alvo ANTES do teste, esperando o textbox do chat aparecer. Isso
//   força a compilação de TODOS os chunks que o browser real vai pedir, deixando
//   o cache do Turbopack quente. O teste subsequente reusa os bundles compilados.
//
// Best-effort: loga claramente e sai 0 mesmo em falha parcial — o teste tem sua
// própria malha de retry (goToChatHome em 01-helpers.ts). O objetivo é eliminar
// o cold-compile, não bloquear o run se um path warmup falhar.
//
// Uso: node scripts/pw-warmup.mjs [baseUrl]
//   baseUrl default: $PLAYWRIGHT_BASE_URL || http://localhost:5000

import { chromium } from '@playwright/test'
import { execSync } from 'node:child_process'

const baseUrl = (
  process.argv[2] ||
  process.env.PLAYWRIGHT_BASE_URL ||
  'http://localhost:5000'
).replace(/\/$/, '')

const PATHS = ['/pt', '/pt/chat']
const MAX_ATTEMPTS = 3
const NAV_TIMEOUT_MS = 120_000

function resolveChromium() {
  if (process.env.PLAYWRIGHT_CHROMIUM_PATH) return process.env.PLAYWRIGHT_CHROMIUM_PATH
  try {
    return execSync('which chromium', { encoding: 'utf-8' }).trim() || undefined
  } catch {
    return undefined
  }
}

async function warmPath(browser, path) {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
    })
    const page = await context.newPage()
    const t0 = Date.now()
    try {
      await page.goto(`${baseUrl}${path}`, {
        waitUntil: 'domcontentloaded',
        timeout: NAV_TIMEOUT_MS,
      })
      // Espera o chat carregar de fato (compila os chunks lazy do UnifiedChat).
      await page
        .getByRole('textbox', { name: /mensagem|message/i })
        .first()
        .waitFor({ state: 'visible', timeout: 30_000 })
        .catch(() => {/* textbox pode não existir em todas as rotas — ok */})
      await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => {})
      const dt = ((Date.now() - t0) / 1000).toFixed(1)
      console.log(`[pw-warmup]   GET ${path} -> OK (browser) em ${dt}s (tentativa ${attempt})`)
      await context.close()
      return true
    } catch (err) {
      const dt = ((Date.now() - t0) / 1000).toFixed(1)
      console.log(
        `[pw-warmup]   GET ${path} -> FALHOU em ${dt}s (tentativa ${attempt}/${MAX_ATTEMPTS}): ${err?.message?.split('\n')[0] ?? err}`
      )
      await context.close().catch(() => {})
      if (attempt < MAX_ATTEMPTS) await new Promise((r) => setTimeout(r, 2000))
    }
  }
  return false
}

async function main() {
  const executablePath = resolveChromium()
  console.log(`[pw-warmup] baseUrl=${baseUrl} chromium=${executablePath ?? '(bundled)'}`)
  const browser = await chromium.launch({
    ...(executablePath ? { executablePath } : {}),
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-first-run',
    ],
  })
  try {
    for (const path of PATHS) {
      await warmPath(browser, path)
    }
  } finally {
    await browser.close().catch(() => {})
  }
  console.log('[pw-warmup] done')
}

main().catch((err) => {
  console.log(`[pw-warmup] erro inesperado (continuando): ${err?.message ?? err}`)
  process.exit(0)
})
