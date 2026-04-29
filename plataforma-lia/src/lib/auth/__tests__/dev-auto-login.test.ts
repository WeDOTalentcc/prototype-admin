/**
 * Sensor: dev-auto-login is OFF by default; opt-in via LIA_DEV_AUTO_LOGIN=true.
 *
 * Audit context (2026-04-29 wizard-domain-hint-leak post-mortem):
 *   Previous default was "ON whenever NODE_ENV !== 'production'", which masked
 *   identity propagation bugs (company_id, JWT). After the audit, default is
 *   inverted: the dev auto-login only activates when explicitly opted-in via
 *   `LIA_DEV_AUTO_LOGIN=true`, regardless of NODE_ENV. Production stays
 *   permanently disabled (defense in depth).
 *
 * Guards:
 *   1. Without LIA_DEV_AUTO_LOGIN, isDevAutoLoginEnabled() returns false
 *      (default OFF — forces real login flow).
 *   2. With LIA_DEV_AUTO_LOGIN=true and NODE_ENV=development (or any non-prod),
 *      returns true (opt-in for offline / CI / load-test scenarios).
 *   3. With LIA_DEV_AUTO_LOGIN=true and NODE_ENV=production, returns false
 *      (production guard — never auto-login in real environments even if
 *      env var is set by mistake).
 *   4. Random truthy strings ("1", "yes", "True") do NOT enable — only the
 *      exact string "true" does (avoids accidental activation).
 *
 * Fix se falhar:
 *   Verificar `src/lib/auth/dev-auto-login.ts` — DEV_AUTO_LOGIN_ENABLED deve
 *   ser definida como `process.env.LIA_DEV_AUTO_LOGIN === 'true' &&
 *   process.env.NODE_ENV !== 'production'`. Se algum outro valor habilitar
 *   o atalho, é regressão de segurança / identidade.
 *
 * Skill canônica: harness-engineering [sensor computacional].
 */
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"

const ENV_KEYS = ["LIA_DEV_AUTO_LOGIN", "NODE_ENV"] as const

function snapshotEnv(): Record<string, string | undefined> {
  return Object.fromEntries(ENV_KEYS.map((k) => [k, process.env[k]]))
}

function restoreEnv(snapshot: Record<string, string | undefined>): void {
  for (const k of ENV_KEYS) {
    if (snapshot[k] === undefined) delete process.env[k]
    else process.env[k] = snapshot[k]
  }
}

describe("dev-auto-login — opt-in semantics (post-mortem 2026-04-29)", () => {
  let envSnapshot: Record<string, string | undefined>

  beforeEach(() => {
    envSnapshot = snapshotEnv()
    vi.resetModules()
  })

  afterEach(() => {
    restoreEnv(envSnapshot)
    vi.resetModules()
  })

  test("Guard 1: default is OFF (no LIA_DEV_AUTO_LOGIN env var)", async () => {
    delete process.env.LIA_DEV_AUTO_LOGIN
    process.env.NODE_ENV = "development"
    const mod = await import("../dev-auto-login")
    expect(mod.isDevAutoLoginEnabled()).toBe(false)
  })

  test("Guard 2: opt-in via LIA_DEV_AUTO_LOGIN='true' in non-production", async () => {
    process.env.LIA_DEV_AUTO_LOGIN = "true"
    process.env.NODE_ENV = "development"
    const mod = await import("../dev-auto-login")
    expect(mod.isDevAutoLoginEnabled()).toBe(true)
  })

  test("Guard 3: production never enables, even with LIA_DEV_AUTO_LOGIN='true'", async () => {
    process.env.LIA_DEV_AUTO_LOGIN = "true"
    process.env.NODE_ENV = "production"
    const mod = await import("../dev-auto-login")
    expect(mod.isDevAutoLoginEnabled()).toBe(false)
  })

  test("Guard 4: only exact 'true' enables — '1', 'yes', 'True' do not", async () => {
    process.env.NODE_ENV = "development"
    for (const truthy of ["1", "yes", "True", "TRUE", "on", "y"]) {
      vi.resetModules()
      process.env.LIA_DEV_AUTO_LOGIN = truthy
      const mod = await import("../dev-auto-login")
      expect(
        mod.isDevAutoLoginEnabled(),
        `LIA_DEV_AUTO_LOGIN='${truthy}' must NOT enable (only exact 'true' does)`,
      ).toBe(false)
    }
  })

  test("Guard 5: empty string and 'false' do not enable", async () => {
    process.env.NODE_ENV = "development"
    for (const falsy of ["", "false", "FALSE", "0", "no"]) {
      vi.resetModules()
      process.env.LIA_DEV_AUTO_LOGIN = falsy
      const mod = await import("../dev-auto-login")
      expect(mod.isDevAutoLoginEnabled()).toBe(false)
    }
  })
})
