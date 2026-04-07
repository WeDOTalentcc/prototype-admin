import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const period = searchParams.get("period") || "90d"

    const cookieHeader = req.headers.get("cookie") || ""
    const authHeader = req.headers.get("authorization") || ""

    const response = await fetch(
      `${BACKEND_URL}/api/v1/work-model-analytics?period=${encodeURIComponent(period)}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...(cookieHeader ? { Cookie: cookieHeader } : {}),
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: "Backend error", status: response.status },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    console.error("[work-model-analytics proxy]", message)
    return NextResponse.json({ error: "proxy_error" }, { status: 502 })
  }
}
