import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// GET /api/backend-proxy/digital-twins/:id
export async function GET(req: NextRequest, { params: pRaw }: { params: Promise<{ id: string }> }) {
  const { id } = await pRaw;
  const res = await fetch(`${BACKEND_URL}/api/v1/digital-twins/${id}`, { headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

// POST handles sub-paths: /evaluate, /index-audio, /index-decision
export async function POST(req: NextRequest, { params: pRaw }: { params: Promise<{ id: string }> }) {
  const { id } = await pRaw;
  const url = new URL(req.url)
  const subPath = url.pathname.split(`/${id}/`)[1] || "evaluate"
  const railsPath = subPath.replace(/-/g, "_") // index-audio → index_audio

  const contentType = req.headers.get("content-type") || ""

  if (contentType.includes("multipart")) {
    // Audio upload
    const formData = await req.formData()
    const res = await fetch(`${BACKEND_URL}/api/v1/digital-twins/${id}/${railsPath}`, {
      method: "POST",
      headers: { Authorization: req.headers.get("authorization") || "" },
      body: formData,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  }

  // JSON body
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/digital-twins/${id}/${railsPath}`, {
    method: "POST", headers: getAuthHeaders(req), body,
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
