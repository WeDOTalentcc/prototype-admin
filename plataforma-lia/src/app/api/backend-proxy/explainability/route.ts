export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')
    const sessionId = searchParams.get('sessionId')
    const companyId = searchParams.get('companyId')

    let backendUrl = ''

    switch (action) {
      case 'timeline':
        if (!sessionId) {
          return NextResponse.json({ error: 'sessionId é obrigatório' }, { status: 400 })
        }
        backendUrl = `${BACKEND_URL}/api/v1/explainability/timeline/${sessionId}`
        break
      case 'summary':
        if (!sessionId) {
          return NextResponse.json({ error: 'sessionId é obrigatório' }, { status: 400 })
        }
        backendUrl = `${BACKEND_URL}/api/v1/explainability/session/${sessionId}/summary`
        break
      case 'recent':
        if (!companyId) {
          return NextResponse.json({ error: 'companyId é obrigatório' }, { status: 400 })
        }
        backendUrl = `${BACKEND_URL}/api/v1/explainability/company/${companyId}/recent`
        break
      case 'stats':
        if (!companyId) {
          return NextResponse.json({ error: 'companyId é obrigatório' }, { status: 400 })
        }
        backendUrl = `${BACKEND_URL}/api/v1/explainability/stats/${companyId}`
        break
      default:
        return NextResponse.json({ error: 'Ação inválida' }, { status: 400 })
    }

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar dados de explicabilidade', details: errorData },
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
