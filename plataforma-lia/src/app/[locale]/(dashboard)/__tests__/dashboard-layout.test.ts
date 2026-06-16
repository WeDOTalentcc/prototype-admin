/**
 * Sensor: (dashboard) route group has the canonical layout shell.
 *
 * Post-mortem 2026-04-29 wizard-domain-hint-leak audit:
 *   The `(dashboard)/layout.tsx` was missing in the App Router setup.
 *   Result: subpages like /pt/configuracoes rendered without the global
 *   Sidebar (because only /[locale]/page.tsx instantiated DashboardApp,
 *   and that page is only the root `/`). Users got "stuck" in Settings
 *   with no way back to Chat / Agent Studio / etc.
 *
 *   Fix: created `(dashboard)/layout.tsx` + `DashboardLayoutClient.tsx`
 *   that wraps every subpage with `<DashboardApp>{children}</DashboardApp>`.
 *   This sensor prevents regression: if either file is deleted or stops
 *   rendering DashboardApp, the test fails immediately.
 *
 * Guards:
 *   1. `(dashboard)/layout.tsx` exists.
 *   2. `(dashboard)/DashboardLayoutClient.tsx` exists.
 *   3. layout.tsx imports and uses DashboardLayoutClient.
 *   4. DashboardLayoutClient.tsx imports and renders DashboardApp.
 *   5. DashboardLayoutClient.tsx maps pathname → initialPage for sidebar
 *      highlighting (or has a sane default).
 *
 * Fix se falhar:
 *   Restaurar os dois arquivos a partir desta doc + commits que
 *   referenciam o post-mortem. NÃO renderizar DashboardApp em pages
 *   individuais (perde o single-source-of-truth shell).
 *
 * Skill canônica: harness-engineering [sensor computacional] +
 *                 canonical-fix (single shell source).
 */
import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const REPO_ROOT = (() => {
  let dir = __dirname
  while (dir !== "/") {
    if (existsSync(join(dir, "package.json"))) {
      try {
        const pkg = JSON.parse(readFileSync(join(dir, "package.json"), "utf-8"))
        if (pkg.name) return dir
      } catch {
        // ignore
      }
    }
    dir = join(dir, "..")
  }
  throw new Error("Could not locate repo root from " + __dirname)
})()

const DASHBOARD_DIR = join(REPO_ROOT, "src/app/[locale]/(dashboard)")
const LAYOUT_PATH = join(DASHBOARD_DIR, "layout.tsx")
const CLIENT_PATH = join(DASHBOARD_DIR, "DashboardLayoutClient.tsx")

describe("Sensor: (dashboard) layout shell (post-mortem 2026-04-29)", () => {
  test("Guard 1: (dashboard)/layout.tsx exists", () => {
    expect(existsSync(LAYOUT_PATH)).toBe(true)
  })

  test("Guard 2: (dashboard)/DashboardLayoutClient.tsx exists", () => {
    expect(existsSync(CLIENT_PATH)).toBe(true)
  })

  test("Guard 3: layout.tsx renders DashboardLayoutClient", () => {
    const src = readFileSync(LAYOUT_PATH, "utf-8")
    expect(src).toMatch(/import\s+.*DashboardLayoutClient/i)
    expect(src).toMatch(/<DashboardLayoutClient[\s>]/)
  })

  test("Guard 4: DashboardLayoutClient imports and renders DashboardApp", () => {
    const src = readFileSync(CLIENT_PATH, "utf-8")
    expect(src).toMatch(/import\s+.*DashboardApp.*from.*dashboard-app/)
    expect(src).toMatch(/<DashboardApp[\s>]/)
  })

  test("Guard 5: client maps pathname → initialPage (sidebar highlight)", () => {
    const src = readFileSync(CLIENT_PATH, "utf-8")
    // Either a route map or usePathname-driven initialPage selection.
    expect(src).toMatch(/usePathname/)
    expect(src).toMatch(/initialPage/)
  })
})
