import { NextRequest, NextResponse } from "next/server"
import { getAuthHeadersForForm } from "@/lib/api/auth-headers"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(request: NextRequest) {
  try {
    const headers = getAuthHeadersForForm(request)

    // Forward multipart form directly — do NOT call request.json(), preserve FormData boundary
    const formData = await request.formData()

    const response = await fetch(`${BACKEND_URL}/api/v1/company/benefits/upload-extract`, {
      method: "POST",
      headers,
      body: formData,
    })

    const contentType = response.headers.get("content-type") || ""
    if (contentType.includes("application/json")) {
      const data = await response.json()
      // T-1171: unwrap envelope canonico {ok, data, meta} do FastAPI
      const unwrapped = data && typeof data === "object" && "ok" in data && "data" in data ? (data as Record<string, unknown>).data : data
      return NextResponse.json(unwrapped, { status: response.status })
    }
    const text = await response.text()
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": contentType || "text/plain" },
    })
  } catch (error) {
    console.error("[upload-extract] proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}
