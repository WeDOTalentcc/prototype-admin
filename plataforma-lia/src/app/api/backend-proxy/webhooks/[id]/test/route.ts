export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'
const DEV_FALLBACK_COMPANY = 'dev_company'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})

async function resolveCompanyId(request: NextRequest): Promise<string | null> {
  const cookieStore = await cookies()
  const session = cookieStore.get('workos_session')
  if (session) {
    const data = verifyAndDecodeSession(session.value)
    if (data) return data.workosProfile.organizationId || data.workosProfile.id
  }
  const fromQuery = new URL(request.url).searchParams.get('company_id')
  if (fromQuery) return fromQuery
  if (IS_DEVELOPMENT) return DEV_FALLBACK_COMPANY
  return null
}

async function getAuthHeaders(request: NextRequest): Promise<Record<string, string> | null> {
  const companyId = await resolveCompanyId(request)
  if (!companyId) return null
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': companyId,
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const headers = await getAuthHeaders(request)
    if (!headers) {
      return NextResponse.json(
        { error: 'Unauthorized', success: false },
        { status: 401 }
      )
    }

    const backendUrl = `${BACKEND_URL}/api/v1/webhooks/${id}/test`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao testar webhook', details: errorData, success: false },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ ...data, success: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend', success: false },
      { status: 500 }
    )
  }
}
