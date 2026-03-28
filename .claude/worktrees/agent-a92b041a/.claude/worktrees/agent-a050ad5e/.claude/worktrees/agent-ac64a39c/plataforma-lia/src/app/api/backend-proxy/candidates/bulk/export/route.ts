import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao exportar candidatos', details: errorData },
        { status: response.status }
      )
    }

    const contentType = response.headers.get('content-type')
    
    if (contentType?.includes('text/csv') || contentType?.includes('application/vnd.openxmlformats')) {
      const blob = await response.blob()
      const headers = new Headers()
      headers.set('Content-Type', contentType)
      headers.set('Content-Disposition', response.headers.get('Content-Disposition') || 'attachment; filename=candidates.csv')
      return new NextResponse(blob, { headers })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Bulk export proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
