export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'admin_company',
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const limit = searchParams.get('limit') || '50'
    
    let backendUrl = `${BACKEND_URL}/api/v1/billing/my-invoices?limit=${limit}`
    if (status) {
      backendUrl += `&status=${status}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar faturas', details: errorData },
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
