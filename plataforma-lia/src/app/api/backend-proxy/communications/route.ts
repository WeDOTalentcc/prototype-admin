export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = request.headers.get('X-Company-ID') || searchParams.get('company_id') || 'admin_company'
    const candidateId = searchParams.get('candidate_id')
    const vacancyId = searchParams.get('vacancy_id')
    const communicationType = searchParams.get('communication_type')
    const channel = searchParams.get('channel')
    const status = searchParams.get('status')
    const limit = searchParams.get('limit') || '50'
    const offset = searchParams.get('offset') || '0'
    
    const backendUrl = new URL(`${BACKEND_URL}/api/v1/communications`)
    backendUrl.searchParams.set('company_id', companyId)
    backendUrl.searchParams.set('limit', limit)
    backendUrl.searchParams.set('offset', offset)
    
    if (candidateId) backendUrl.searchParams.set('candidate_id', candidateId)
    if (vacancyId) backendUrl.searchParams.set('vacancy_id', vacancyId)
    if (communicationType) backendUrl.searchParams.set('communication_type', communicationType)
    if (channel) backendUrl.searchParams.set('channel', channel)
    if (status) backendUrl.searchParams.set('status', status)
    
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        ...getAuthHeaders(request),
        'X-Company-ID': companyId,
      },
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        { 
          success: false,
          error: data.detail || 'Erro ao buscar comunicações',
          details: data 
        },
        { status: response.status }
      )
    }

    return NextResponse.json({
      success: true,
      ...data
    })
  } catch (error) {
    return NextResponse.json(
      { 
        success: false,
        error: 'Erro ao conectar com o backend',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}
