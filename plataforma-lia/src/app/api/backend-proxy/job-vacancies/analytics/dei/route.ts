import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  const auth = request.headers.get("Authorization") || ""
  const { searchParams } = new URL(request.url)
  const period = searchParams.get("period") ?? "90d"
  try {
    const resp = await fetch(
      `${BACKEND_URL}/api/v1/job-vacancies/analytics/dei-insights?period=${encodeURIComponent(period)}`,
      { headers: { Authorization: auth, "Content-Type": "application/json" } }
    )
    const data = await resp.json()
    return NextResponse.json(data, { status: resp.status })
  } catch (err) {
    console.error("[dei-insights proxy]", err)
    return NextResponse.json({ error: "upstream_error" }, { status: 502 })
  }
}
