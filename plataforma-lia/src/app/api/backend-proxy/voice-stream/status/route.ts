import { NextRequest, NextResponse } from "next/server"
import { proxyFetchWithRetry } from "@/lib/api/proxy-fetch-with-retry"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const companyId = searchParams.get("company_id") || ""
    const response = await proxyFetchWithRetry(
      req,
      `/api/v1/voice-stream/status?company_id=${encodeURIComponent(companyId)}`,
    )
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json(
      { streaming_available: false, error: "Proxy error" },
      { status: 502 },
    )
  }
}
