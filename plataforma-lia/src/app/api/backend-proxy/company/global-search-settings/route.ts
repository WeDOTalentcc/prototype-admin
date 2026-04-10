export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

async function resolveCompanyId(request: NextRequest): Promise<string | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/me`, { headers: getAuthHeaders(request) })
    if (res.ok) {
      const user = await res.json()
      if (user.company_id) return user.company_id
    }
  } catch {}
  return null
}

export async function GET(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: "Não foi possível resolver company_id" }, { status: 401 })
    }
    const res = await fetch(`${BACKEND_URL}/api/v1/company/global-search-settings?company_id=${companyId}`, {
      headers: getAuthHeaders(request),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return NextResponse.json({ error: "Backend error", details: err }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json({ error: "Erro ao conectar com o backend" }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: "Não foi possível resolver company_id" }, { status: 401 })
    }
    const body = await request.json()
    const res = await fetch(`${BACKEND_URL}/api/v1/company/global-search-settings?company_id=${companyId}`, {
      method: "PUT",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return NextResponse.json({ error: "Backend error", details: err }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json({ error: "Erro ao conectar com o backend" }, { status: 500 })
  }
}
