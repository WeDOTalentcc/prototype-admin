export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

async function forward(
  request: NextRequest,
  candidateId: string,
  method: 'GET' | 'DELETE'
) {
  const companyId = await resolveCompanyId(request)
  if (!companyId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  const url = `${BACKEND_URL}/api/v1/experience-highlights/${candidateId}?company_id=${encodeURIComponent(companyId)}`
  const response = await fetch(url, { method, headers: getAuthHeaders(request) })
  const text = await response.text()
  if (!response.ok) {
    return new NextResponse(text || JSON.stringify({ error: 'Upstream error' }), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    })
  }
  return new NextResponse(text, {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ candidateId: string }> }
) {
  const { candidateId } = await params
  return forward(request, candidateId, 'GET')
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ candidateId: string }> }
) {
  const { candidateId } = await params
  return forward(request, candidateId, 'DELETE')
}
