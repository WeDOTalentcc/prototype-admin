export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'
const DEV_FALLBACK_COMPANY = 'dev_company'

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

export async function GET(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/progress`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar progresso', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
