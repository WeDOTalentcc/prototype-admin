/**
 * Place at: src/app/api/backend-proxy/recruitment-campaigns/[id]/advance-stage/route.ts
 */
import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await fetch(`${RAILS_URL}/v1/users/recruitment_campaigns/${params.id}/advance_stage`, {
    method: "POST", headers: getAuthHeaders(req),
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
