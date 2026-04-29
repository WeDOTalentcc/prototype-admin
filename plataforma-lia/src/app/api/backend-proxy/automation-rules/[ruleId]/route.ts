export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function buildHeaders(request: NextRequest): HeadersInit {
  const base = getAuthHeaders(request) as Record<string, string>
  const companyId = request.headers.get("X-Company-ID")
  if (companyId) base["X-Company-ID"] = companyId
  return base
}

function backendUrl(companyId: string, ruleId: string) {
  return `${BACKEND_URL}/api/v1/automation-rules/company/${encodeURIComponent(companyId)}/${encodeURIComponent(ruleId)}`
}

function company(request: NextRequest): string {
  return request.headers.get("X-Company-ID") || "platform"
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ruleId: string }> },
) {
  const { ruleId } = await params
  const r = await fetch(backendUrl(company(request), ruleId), {
    headers: buildHeaders(request),
  })
  const data = await r.json().catch(() => ({}))
  return NextResponse.json(data, { status: r.status })
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ ruleId: string }> },
) {
  const { ruleId } = await params
  const body = await request.text()
  const r = await fetch(backendUrl(company(request), ruleId), {
    method: "PUT",
    headers: buildHeaders(request),
    body,
  })
  const data = await r.json().catch(() => ({}))
  return NextResponse.json(data, { status: r.status })
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ ruleId: string }> },
) {
  const { ruleId } = await params
  const r = await fetch(backendUrl(company(request), ruleId), {
    method: "DELETE",
    headers: buildHeaders(request),
  })
  const data = await r.json().catch(() => ({}))
  return NextResponse.json(data, { status: r.status })
}
