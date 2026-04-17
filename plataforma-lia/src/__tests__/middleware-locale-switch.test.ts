/**
 * Locks in the PT/EN locale switching behavior fixed by task #380.
 *
 * Verifies that:
 *  - Visiting `/` honors an existing NEXT_LOCALE cookie (en stays en, pt stays pt).
 *  - Visiting `/` with no cookie falls back to the default locale (pt).
 *  - The intl routing is configured so it never silently overwrites the
 *    user-chosen locale (`localeDetection: false`, `localePrefix: 'always'`).
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { NextRequest, NextResponse } from "next/server"

// Mock heavy / environment-coupled deps that the middleware module imports
// at load time. Keep these BEFORE the dynamic import of `../middleware`.
vi.mock("@/lib/auth/dev-auto-login", () => ({
  getDevToken: vi.fn(async () => null),
  isDevAutoLoginEnabled: () => false,
}))

vi.mock("@/lib/session-crypto", () => ({
  verifyAndDecodeSession: () => null,
}))

// next-intl/middleware imports `next/server` via a path that vitest's resolver
// chokes on in node env. We don't need its real behavior for these assertions
// — we just need an identity passthrough so the outer middleware can run.
vi.mock("next-intl/middleware", () => ({
  default: () => () => NextResponse.next(),
}))

// `@/i18n/routing` pulls in next-intl/navigation which transitively imports
// `next/navigation` via a path the vitest resolver can't follow in node env.
// The middleware only consumes `routing` to build the (mocked) intl middleware,
// so a minimal stub is sufficient here.
vi.mock("@/i18n/routing", () => ({
  routing: {
    locales: ["pt", "en"],
    defaultLocale: "pt",
    localePrefix: "always",
    localeDetection: false,
  },
}))

function makeRequest(url: string, cookies: Record<string, string> = {}) {
  const req = new NextRequest(new URL(url), {})
  for (const [name, value] of Object.entries(cookies)) {
    req.cookies.set(name, value)
  }
  return req
}

describe("middleware: PT/EN locale switching at `/` (task #380)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("redirects `/` to `/en/` when NEXT_LOCALE=en cookie is set", async () => {
    const { middleware } = await import("../middleware")
    const res = await middleware(
      makeRequest("http://localhost:5000/", { NEXT_LOCALE: "en" }),
    )
    expect(res.status).toBeGreaterThanOrEqual(300)
    expect(res.status).toBeLessThan(400)
    const location = res.headers.get("location") ?? ""
    expect(location).toMatch(/\/en\/?$/)
    expect(location).not.toMatch(/\/pt/)
  })

  it("redirects `/` to `/pt/` when NEXT_LOCALE=pt cookie is set", async () => {
    const { middleware } = await import("../middleware")
    const res = await middleware(
      makeRequest("http://localhost:5000/", { NEXT_LOCALE: "pt" }),
    )
    expect(res.status).toBeGreaterThanOrEqual(300)
    expect(res.status).toBeLessThan(400)
    expect(res.headers.get("location") ?? "").toMatch(/\/pt\/?$/)
  })

  it("redirects `/` to `/pt/` (default) when no NEXT_LOCALE cookie is present", async () => {
    const { middleware } = await import("../middleware")
    const res = await middleware(makeRequest("http://localhost:5000/"))
    expect(res.status).toBeGreaterThanOrEqual(300)
    expect(res.status).toBeLessThan(400)
    expect(res.headers.get("location") ?? "").toMatch(/\/pt\/?$/)
  })

  it("ignores invalid NEXT_LOCALE values and uses the default", async () => {
    const { middleware } = await import("../middleware")
    const res = await middleware(
      makeRequest("http://localhost:5000/", { NEXT_LOCALE: "xx" }),
    )
    expect(res.headers.get("location") ?? "").toMatch(/\/pt\/?$/)
  })
})

describe("i18n routing: never silently overrides the user's locale", () => {
  it("disables locale auto-detection so the cookie/path locale is authoritative", async () => {
    // Read the routing source directly: importing it pulls next-intl/navigation
    // which the vitest node resolver can't load. A static check is enough to
    // guard against a regression where someone re-enables localeDetection.
    const fs = await import("node:fs")
    const path = await import("node:path")
    const src = fs.readFileSync(
      path.resolve(__dirname, "../i18n/routing.ts"),
      "utf-8",
    )
    expect(src).toMatch(/localeDetection:\s*false/)
    expect(src).toMatch(/localePrefix:\s*['"]always['"]/)
  })

  it("middleware does not set/override NEXT_LOCALE on locale-prefixed public paths", async () => {
    const { middleware } = await import("../middleware")
    // /pt/login is a public path — middleware delegates to intlMiddleware and
    // must not write a Set-Cookie that overrides the user's choice.
    const res = await middleware(
      makeRequest("http://localhost:5000/pt/login", { NEXT_LOCALE: "en" }),
    )
    const setCookie = res.headers.get("set-cookie") ?? ""
    expect(setCookie).not.toMatch(/NEXT_LOCALE=/)
  })
})
