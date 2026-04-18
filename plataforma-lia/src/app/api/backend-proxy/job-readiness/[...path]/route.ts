/**
 * Catch-all proxy for /api/backend-proxy/job-readiness/* (Task #429).
 *
 * Forwards every method (GET/POST/PUT/PATCH/DELETE) to the LIA backend at
 * /api/v1/job-readiness/*, using the standard `getAuthHeaders` helper so the
 * Authorization bearer is resolved exactly like the rest of the proxy layer
 * (header → `lia_access_token` cookie → `workos_session` cookie → optional
 * dev-mode fallback).
 */
export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

type Ctx = { params: Promise<{ path: string[] }> }

async function forward(
  request: NextRequest,
  ctx: Ctx,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
) {
  try {
    const { path } = await ctx.params
    const tail = (path || []).map(encodeURIComponent).join("/")
    const { searchParams } = new URL(request.url)
    const qs = searchParams.toString()
    const url = `${BACKEND_URL}/api/v1/job-readiness/${tail}${qs ? `?${qs}` : ""}`

    const headers = getAuthHeaders(request) as Record<string, string>

    const init: RequestInit = { method, headers }
    if (method !== "GET" && method !== "DELETE") {
      const raw = await request.text()
      if (raw) init.body = raw
    }

    const upstream = await fetch(url, { ...init, signal: AbortSignal.timeout(30000) })
    const text = await upstream.text()
    if (!upstream.ok) {
      const ct = upstream.headers.get("content-type") || ""
      if (!text) return new NextResponse(null, { status: upstream.status })
      if (ct.includes("application/json")) {
        return new NextResponse(text, {
          status: upstream.status,
          headers: { "Content-Type": "application/json" },
        })
      }
      return new NextResponse(text, {
        status: upstream.status,
        headers: { "Content-Type": ct || "text/plain" },
      })
    }
    if (!text) return new NextResponse(null, { status: upstream.status })
    try {
      return NextResponse.json(JSON.parse(text), { status: upstream.status })
    } catch {
      return new NextResponse(text, {
        status: upstream.status,
        headers: { "content-type": upstream.headers.get("content-type") || "text/plain" },
      })
    }
  } catch (err) {
    console.error("[job-readiness proxy] error", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

export const GET = (req: NextRequest, ctx: Ctx) => forward(req, ctx, "GET")
export const POST = (req: NextRequest, ctx: Ctx) => forward(req, ctx, "POST")
export const PUT = (req: NextRequest, ctx: Ctx) => forward(req, ctx, "PUT")
export const PATCH = (req: NextRequest, ctx: Ctx) => forward(req, ctx, "PATCH")
export const DELETE = (req: NextRequest, ctx: Ctx) => forward(req, ctx, "DELETE")
