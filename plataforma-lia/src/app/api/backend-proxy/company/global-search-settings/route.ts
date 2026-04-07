export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession } from '@/lib/session-crypto'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
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
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/global-search-settings?company_id=${companyId}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar configurações de busca global', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/global-search-settings?company_id=${companyId}`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar configurações de busca global', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
