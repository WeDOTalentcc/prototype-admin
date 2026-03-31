export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const thread_id = searchParams.get('thread_id')
    const additional_query = searchParams.get('additional_query')
    const limit = searchParams.get('limit')
    
    if (!thread_id || !additional_query) {
      return NextResponse.json(
        { error: 'thread_id e additional_query são obrigatórios' },
        { status: 400 }
      )
    }
    
    let backendUrl = `${BACKEND_URL}/api/v1/search/candidates/refine?thread_id=${encodeURIComponent(thread_id)}&additional_query=${encodeURIComponent(additional_query)}`
    if (limit) {
      backendUrl += `&limit=${limit}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao refinar busca', details: errorData },
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
