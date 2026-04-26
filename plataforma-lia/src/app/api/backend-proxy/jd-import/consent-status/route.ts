/**
 * Task #838 — JD upload consent preflight (M-01 bypass).
 *
 * Read-only proxy para `GET /api/v1/import/jd-upload/consent-status`. O hook
 * `useSmartFileUpload` usa essa resposta para suprimir o diálogo de
 * consentimento quando o backend (audit_logs) já contém um `consent_granted`
 * para a empresa do usuário — concretizando "bypass para domínios já
 * consentidos" do done criteria.
 */
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  let headers: HeadersInit
  try {
    headers = getAuthHeaders(request, true)
  } catch {
    return NextResponse.json(
      { has_consent: false, error: "Authentication required" },
      { status: 401 },
    )
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/import/jd-upload/consent-status`,
      { method: "GET", headers },
    )

    if (!response.ok) {
      // Fail-open conservador para preflight: cliente assume "sem consent"
      // e mostra o diálogo. NUNCA assumir consent quando o backend falha.
      return NextResponse.json(
        { has_consent: false },
        { status: response.status },
      )
    }

    const data = await response.json()
    const hasConsent = data && typeof data.has_consent === "boolean"
      ? data.has_consent
      : false
    return NextResponse.json({ has_consent: hasConsent })
  } catch {
    return NextResponse.json({ has_consent: false }, { status: 500 })
  }
}
