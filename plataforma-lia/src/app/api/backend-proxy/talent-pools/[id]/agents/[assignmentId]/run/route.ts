import { NextRequest, NextResponse } from "next/server"

const FASTAPI_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  const cookie = req.headers.get("cookie")
  if (cookie) headers["Cookie"] = cookie
  return headers
}

// POST /api/backend-proxy/talent-pools/:id/agents/:assignmentId/run
// Dispatch on-demand do assignment (Sprint 7B-1).
// Backend retorna 202 Accepted com { status: "queued", ... } — full impl Celery em 7C.
export async function POST(
  req: NextRequest,
  { params: pRaw }: { params: Promise<{ id: string; assignmentId: string }> },
) {
  const { id, assignmentId } = await pRaw
  // Body opcional — passar adiante mesmo que vazio pra preservar contrato futuro
  const body = await req.text()
  const res = await fetch(
    `${FASTAPI_URL}/api/v1/talent-pools/${id}/agents/${assignmentId}/run`,
    {
      method: "POST",
      headers: getAuthHeaders(req),
      body: body || undefined,
    },
  )
  const data = await res.text()
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
