import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || ""

function authHeaders(req: NextRequest): HeadersInit {
  return {
    Authorization: req.headers.get("Authorization") || "",
    "Content-Type": "application/json",
  }
}

function railsUnavailable() {
  return NextResponse.json(
    { error: "Backend not configured", service: "rh/candidates" },
    { status: 503 },
  )
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!RAILS_URL) return railsUnavailable()
  const { id } = await params
  const body = await req.text()
  try {
    const res = await fetch(`${RAILS_URL}/v1/users/candidates/${id}`, {
      method: "PUT",
      headers: authHeaders(req),
      body,
      cache: "no-store",
    })
    const text = await res.text()
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json({ error: "Upstream error" }, { status: 502 })
  }
}
