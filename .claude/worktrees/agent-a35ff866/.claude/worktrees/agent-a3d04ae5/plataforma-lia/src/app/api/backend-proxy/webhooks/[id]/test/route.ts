import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'demo_company',
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
    const backendUrl = `${BACKEND_URL}/api/v1/webhooks/${id}/test`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`)
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao testar webhook', details: errorData, success: false },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ ...data, success: true })
  } catch (error) {
    console.error('Webhook test proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend', success: false },
      { status: 500 }
    )
  }
}
