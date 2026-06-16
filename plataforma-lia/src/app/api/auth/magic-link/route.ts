/**
 * Next.js API proxy for magic link verification.
 *
 * Phase 2 (2026-06-10): routes to FastAPI when FASTAPI_MAGIC_LINK_PRIMARY=true
 * on the backend, falls back to Rails when flag is off.
 *
 * GET /api/auth/magic-link?token=X&uid=Y
 *   -> FastAPI GET /api/v1/auth/magic-link/verify?token=X&uid=Y (Phase 2)
 *   -> Rails  GET /v1/auth/magic-link/verify?token=X&uid=Y     (fallback)
 */

import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || "http://localhost:3000"
const FASTAPI_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const COOKIE_SECURE = process.env.NODE_ENV === "production"

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token") || ""
  const uid = request.nextUrl.searchParams.get("uid") || ""

  if (!token || !uid) {
    return NextResponse.json({ error: "Token and uid required" }, { status: 400 })
  }

  // ── Phase 2b: try FastAPI first ─────────────────────────────────────────
  try {
    const fastapiResp = await fetch(
      `${FASTAPI_URL}/api/v1/auth/magic-link/verify?token=${encodeURIComponent(token)}&uid=${encodeURIComponent(uid)}`,
      { headers: { "Content-Type": "application/json" } },
    )

    if (fastapiResp.ok) {
      const data = await fastapiResp.json()
      if (data.access_token) {
        const target = data.first_login
          ? new URL(`/onboarding`, request.url)
          : new URL("/", request.url)
        const response = NextResponse.redirect(target)
        response.cookies.set("lia_access_token", data.access_token, {
          httpOnly: true,
          secure: COOKIE_SECURE,
          sameSite: "lax",
          maxAge: data.expires_in ?? 86400,
          path: "/",
        })
        return response
      }
    }

    // 404 from FastAPI = user not in FastAPI DB yet → fall through to Rails
    // 401 from FastAPI = invalid/expired token → don't retry Rails (same token)
    if (fastapiResp.status === 401) {
      return NextResponse.redirect(
        new URL(`/login?error=${encodeURIComponent("Link invalido ou expirado")}`, request.url),
      )
    }
    // 503 or 404 → fall through to Rails
  } catch {
    // FastAPI unreachable → fall through to Rails
  }

  // ── Rails fallback ───────────────────────────────────────────────────────
  const resp = await fetch(
    `${RAILS_URL}/v1/auth/magic-link/verify?token=${encodeURIComponent(token)}&uid=${encodeURIComponent(uid)}`,
    { headers: { "Content-Type": "application/json" } },
  )

  const data = await resp.json()

  if (resp.ok && data.token) {
    const response = data.first_login
      ? NextResponse.redirect(new URL(`/onboarding?session=${data.onboarding_session_id}`, request.url))
      : NextResponse.redirect(new URL("/", request.url))

    response.cookies.set("lia_access_token", data.token, {
      httpOnly: true,
      secure: COOKIE_SECURE,
      sameSite: "lax",
      maxAge: 86400,
      path: "/",
    })

    return response
  }

  return NextResponse.redirect(
    new URL(`/login?error=${encodeURIComponent(data.error || "Link invalido")}`, request.url),
  )
}
