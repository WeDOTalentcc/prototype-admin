import { NextRequest } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { verifyAndDecodeSession } from "@/lib/session-crypto"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  const url = new URL(request.url)
  const limit = url.searchParams.get("limit") ?? "3"
  const authHeaders = getAuthHeaders(request)

  // Resolve user_id from workos session cookie to enable per-user history.
  // Optional: backend falls back to company archetypes when absent.
  let userId: string | null = null
  const workosSession = request.cookies.get("workos_session")
  if (workosSession?.value) {
    const session = verifyAndDecodeSession(workosSession.value)
    if (session?.workosProfile?.id) userId = session.workosProfile.id
  }

  const backendUrl = new URL(
    `${BACKEND_URL}/api/v1/search/autocomplete/recent`
  )
  backendUrl.searchParams.set("limit", limit)
  if (userId) backendUrl.searchParams.set("x_user_id", userId)

  try {
    const res = await fetch(backendUrl.toString(), {
      headers: authHeaders,
      cache: "no-store",
    })
    const data = await res.json()
    return Response.json(data, { status: res.status })
  } catch {
    return Response.json({ suggestions: [] }, { status: 200 })
  }
}
