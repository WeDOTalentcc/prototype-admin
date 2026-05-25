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

// PATCH /api/backend-proxy/talent-pools/:id/agents/:assignmentId
// Atualiza assignment (status, schedule, overrides) — Sprint 7B-1.
export async function PATCH(
  req: NextRequest,
  { params: pRaw }: { params: Promise<{ id: string; assignmentId: string }> },
) {
  const { id, assignmentId } = await pRaw
  const body = await req.text()
  const res = await fetch(
    `${FASTAPI_URL}/api/v1/talent-pools/${id}/agents/${assignmentId}`,
    {
      method: "PATCH",
      headers: getAuthHeaders(req),
      body,
    },
  )
  const data = await res.text()
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}

// DELETE /api/backend-proxy/talent-pools/:id/agents/:assignmentId
// Unassign agent do pool — Sprint 7B-1.
export async function DELETE(
  req: NextRequest,
  { params: pRaw }: { params: Promise<{ id: string; assignmentId: string }> },
) {
  const { id, assignmentId } = await pRaw
  const res = await fetch(
    `${FASTAPI_URL}/api/v1/talent-pools/${id}/agents/${assignmentId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(req),
    },
  )
  // DELETE devolve 204 sem body — preservar comportamento canonical
  const data = res.status === 204 ? "" : await res.text()
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
