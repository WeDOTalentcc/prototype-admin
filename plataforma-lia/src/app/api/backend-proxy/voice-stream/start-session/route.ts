import { NextRequest, NextResponse } from "next/server"
import { proxyFetchWithRetry } from "@/lib/api/proxy-fetch-with-retry"

export async function POST(req: NextRequest) {
  try {
    const response = await proxyFetchWithRetry(req, "/api/v1/voice-stream/start-session", {
      method: "POST",
      body: await req.text(),
    })
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json(
      { success: false, error: "Proxy error" },
      { status: 502 },
    )
  }
}
