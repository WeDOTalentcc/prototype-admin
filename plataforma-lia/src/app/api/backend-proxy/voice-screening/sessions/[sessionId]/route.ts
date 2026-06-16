import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {}
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// GET /api/backend-proxy/voice-screening/sessions/:sessionId
export async function GET(req: NextRequest, { params: pRaw }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await pRaw;
  const res = await fetch(`${BACKEND_URL}/api/v1/voice-screening/sessions/${sessionId}`, {
    headers: { ...getAuthHeaders(req), "Content-Type": "application/json" },
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

// POST handles both /audio and /text sub-paths
export async function POST(req: NextRequest, { params: pRaw }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await pRaw;
  const url = new URL(req.url)
  const subPath = url.pathname.split(`/${sessionId}/`)[1] || "text"

  if (subPath === "audio") {
    // Forward multipart form data as-is
    const formData = await req.formData()
    const res = await fetch(`${BACKEND_URL}/api/v1/voice-screening/sessions/${sessionId}/audio`, {
      method: "POST",
      headers: getAuthHeaders(req),
      body: formData,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  }

  // Text submission
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/voice-screening/sessions/${sessionId}/text`, {
    method: "POST",
    headers: { ...getAuthHeaders(req), "Content-Type": "application/json" },
    body,
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
