import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import type { NextRequest } from "next/server"
import { getAuthHeaders, getAuthHeadersForForm } from "./auth-headers"

vi.mock("@/lib/session-crypto", () => ({
  verifyAndDecodeSession: vi.fn(() => null),
}))

type FakeCookies = { get: (name: string) => { value: string } | undefined }

function makeRequest(opts: {
  authHeader?: string
  cookies?: Record<string, string>
}): NextRequest {
  const headers = new Headers()
  if (opts.authHeader) headers.set("Authorization", opts.authHeader)
  const cookies: FakeCookies = {
    get: (name: string) =>
      opts.cookies && opts.cookies[name]
        ? { value: opts.cookies[name] }
        : undefined,
  }
  return { headers, cookies } as unknown as NextRequest
}

const ORIGINAL_ENV = { ...process.env }

describe("getAuthHeaders — dev fallback injection (task #293)", () => {
  beforeEach(() => {
    process.env = { ...ORIGINAL_ENV }
    delete process.env.LIA_DEV_MODE
    delete process.env.LIA_DEV_API_KEY
    delete process.env.APP_ENV
  })

  afterEach(() => {
    process.env = ORIGINAL_ENV
  })

  it("forwards Bearer from Authorization header when present", () => {
    const req = makeRequest({ authHeader: "Bearer real-token" })
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["Authorization"]).toBe("Bearer real-token")
    expect(headers["X-Dev-Api-Key"]).toBeUndefined()
  })

  it("no bearer + LIA_DEV_MODE=true + LIA_DEV_API_KEY → injects X-Dev-Api-Key", () => {
    process.env.LIA_DEV_MODE = "true"
    process.env.LIA_DEV_API_KEY = "dev-secret"
    const req = makeRequest({})
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["Authorization"]).toBeUndefined()
    expect(headers["X-Dev-Api-Key"]).toBe("dev-secret")
  })

  it("no bearer + LIA_DEV_MODE unset → no dev header (even with key)", () => {
    process.env.APP_ENV = "production"
    process.env.NODE_ENV = "production"
    process.env.LIA_DEV_API_KEY = "dev-secret"
    delete process.env.LIA_DEV_MODE
    const req = makeRequest({})
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["Authorization"]).toBeUndefined()
    expect(headers["X-Dev-Api-Key"]).toBeUndefined()
  })

  it("no bearer + NODE_ENV=development but LIA_DEV_MODE unset → no dev header", () => {
    process.env.NODE_ENV = "development"
    process.env.APP_ENV = "development"
    process.env.LIA_DEV_API_KEY = "dev-secret"
    delete process.env.LIA_DEV_MODE
    const req = makeRequest({})
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["X-Dev-Api-Key"]).toBeUndefined()
  })

  it("no bearer + dev-mode but no LIA_DEV_API_KEY → no dev header", () => {
    process.env.LIA_DEV_MODE = "true"
    const req = makeRequest({})
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["X-Dev-Api-Key"]).toBeUndefined()
  })

  it("Bearer present + dev-mode → Bearer wins, no dev header", () => {
    process.env.LIA_DEV_MODE = "true"
    process.env.LIA_DEV_API_KEY = "dev-secret"
    const req = makeRequest({ authHeader: "Bearer real" })
    const headers = getAuthHeaders(req) as Record<string, string>
    expect(headers["Authorization"]).toBe("Bearer real")
    expect(headers["X-Dev-Api-Key"]).toBeUndefined()
  })

  it("getAuthHeadersForForm applies same dev-fallback rules", () => {
    process.env.LIA_DEV_MODE = "true"
    process.env.LIA_DEV_API_KEY = "dev-secret"
    const req = makeRequest({})
    const headers = getAuthHeadersForForm(req) as Record<string, string>
    expect(headers["X-Dev-Api-Key"]).toBe("dev-secret")
    expect(headers["Content-Type"]).toBeUndefined()
  })
})
