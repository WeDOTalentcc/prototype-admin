/**
 * Place at: src/app/api/backend-proxy/sourcing-agents/[id]/route.ts
 * Handles: GET agent, feedback, calibration-candidates, timeline, pause, resume
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const url = new URL(req.url)
  // Route to sub-endpoints based on path segments
  const pathAfterPrev = url.pathname.split(`/${params.id}/`)[1]

  let apiPath = `/api/v1/sourcing-agents/${params.id}`
  if (pathAfterPrev) {
    apiPath += `/${pathAfterPrev}${url.search}`
  }

  const res = await fetch(`${BACKEND_URL}${apiPath}`, { headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const url = new URL(req.url)
  const pathAfterId = url.pathname.split(`/${params.id}/`)[1] || ""
  const apiPath = `/api/v1/sourcing-agents/${params.id}/${pathAfterId}`

  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}${apiPath}`, { method: "POST", headers: getAuthHeaders(req), body })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const url = new URL(req.url)
  const pathAfterId = url.pathname.split(`/${params.id}/`)[1] || ""
  const apiPath = `/api/v1/sourcing-agents/${params.id}/${pathAfterId}`

  const res = await fetch(`${BACKEND_URL}${apiPath}`, { method: "PATCH", headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
