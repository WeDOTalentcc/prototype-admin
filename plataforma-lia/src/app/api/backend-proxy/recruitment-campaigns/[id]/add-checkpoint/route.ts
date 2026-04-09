/**
 * Place at: src/app/api/backend-proxy/recruitment-campaigns/[id]/add-checkpoint/route.ts
 */
import { NextRequest, NextResponse } from "next/server"

const FASTAPI_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.text()
  const res = await fetch(`${FASTAPI_URL}/api/v1/recruitment_campaigns/${params.id}/add_checkpoint`, {
    method: "POST", headers: getAuthHeaders(req), body,
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
