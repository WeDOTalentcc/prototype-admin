export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(request: NextRequest): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" }
  const a = request.headers.get("Authorization")
  if (a) h["Authorization"] = a
  return h
}

/** GET list canonical (master + custom da company) */
export async function GET(request: NextRequest) {
  const url = new URL(request.url)
  const qs = url.search ? url.search : ""
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/pipeline-stage-templates${qs}`,
      { method: "GET", headers: getAuthHeaders(request) },
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed" },
      { status: 500 },
    )
  }
}

/** POST create custom canonical */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/pipeline-stage-templates`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      },
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed" },
      { status: 500 },
    )
  }
}
