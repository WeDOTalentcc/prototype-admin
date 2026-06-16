/**
 * Next.js API proxy for magic link verification.
 *
 * Apply to: plataforma-lia/src/app/api/auth/magic-link/route.ts
 *
 * GET /api/auth/magic-link?token=X&uid=Y → Rails GET /v1/auth/magic-link/verify?token=X&uid=Y
 */

import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || "http://localhost:3000"

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token") || ""
  const uid = request.nextUrl.searchParams.get("uid") || ""

  if (!token || !uid) {
    return NextResponse.json({ error: "Token and uid required" }, { status: 400 })
  }

  const resp = await fetch(
    `${RAILS_URL}/v1/auth/magic-link/verify?token=${encodeURIComponent(token)}&uid=${encodeURIComponent(uid)}`,
    {
      headers: { "Content-Type": "application/json" },
    }
  )

  const data = await resp.json()

  if (resp.ok && data.token) {
    // Set auth cookie and redirect to onboarding or dashboard
    const response = data.first_login
      ? NextResponse.redirect(new URL(`/onboarding?session=${data.onboarding_session_id}`, request.url))
      : NextResponse.redirect(new URL("/", request.url))

    // Set JWT cookie
    response.cookies.set("auth_token", data.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 86400, // 24h
      path: "/",
    })

    return response
  }

  // Error: redirect to login with message
  return NextResponse.redirect(
    new URL(`/login?error=${encodeURIComponent(data.error || "Link invalido")}`, request.url)
  )
}
