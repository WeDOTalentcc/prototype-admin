/**
 * Next.js API proxy route for onboarding endpoints.
 *
 * Apply to: plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts
 *
 * Routes:
 *   POST /api/backend-proxy/onboarding/invite → Rails POST /v1/users/invite
 *   GET  /api/backend-proxy/onboarding/status → Rails GET /v1/onboarding/status
 *   PATCH /api/backend-proxy/onboarding/progress → Rails PATCH /v1/onboarding/progress
 *   POST /api/backend-proxy/onboarding/consent → Rails POST /v1/onboarding/consent
 *   GET  /api/backend-proxy/onboarding/:userId/context → FastAPI GET /api/v1/onboarding/:userId/context
 */

import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || "http://localhost:3000"
const FASTAPI_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path?.join("/") || ""
  const headers = buildHeaders(request)

  // FastAPI routes: context, state (have user_id in path)
  if (path.match(/^\d+\/(context|state)$/)) {
    const resp = await fetch(`${FASTAPI_URL}/api/v1/onboarding/${path}`, { headers })
    return NextResponse.json(await resp.json(), { status: resp.status })
  }

  // Rails routes: status, settings (use auth token, no user_id in path)
  const railsPath = mapToRailsPath(path)
  const url = `${RAILS_URL}${railsPath}${request.nextUrl.search}`
  const resp = await fetch(url, { headers })
  return NextResponse.json(await resp.json(), { status: resp.status })
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path?.join("/") || ""
  const headers = buildHeaders(request)
  const body = await request.text()

  // FastAPI routes: user_id/event
  if (path.match(/^\d+\/event$/)) {
    const resp = await fetch(`${FASTAPI_URL}/api/v1/onboarding/${path}`, {
      method: "POST",
      headers,
      body,
    })
    return NextResponse.json(await resp.json(), { status: resp.status })
  }

  // Rails routes
  const railsPath = mapToRailsPath(path)
  const resp = await fetch(`${RAILS_URL}${railsPath}`, {
    method: "POST",
    headers,
    body,
  })
  return NextResponse.json(await resp.json(), { status: resp.status })
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path?.join("/") || ""
  const headers = buildHeaders(request)
  const body = await request.text()

  const railsPath = mapToRailsPath(path)
  const resp = await fetch(`${RAILS_URL}${railsPath}`, {
    method: "PATCH",
    headers,
    body,
  })
  return NextResponse.json(await resp.json(), { status: resp.status })
}

function buildHeaders(request: NextRequest): HeadersInit {
  const auth = request.headers.get("Authorization") || ""
  return {
    Authorization: auth,
    "Content-Type": "application/json",
  }
}

function mapToRailsPath(path: string): string {
  if (path === "invite") return "/v1/users/invite"
  if (path === "status") return "/v1/onboarding/status"
  if (path === "progress") return "/v1/onboarding/progress"
  if (path === "consent") return "/v1/onboarding/consent"
  if (path === "settings") return "/v1/onboarding/settings"
  return `/v1/onboarding/${path}`
}
