import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File | null
    
    if (!file) {
      return NextResponse.json(
        { error: 'Arquivo CV é obrigatório' },
        { status: 400 }
      )
    }
    
    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') || '20'
    const searchPearch = searchParams.get('search_pearch') !== 'false'
    const pearchType = searchParams.get('pearch_type') || 'fast'
    
    const backendFormData = new FormData()
    backendFormData.append('file', file)
    
    const backendUrl = `${BACKEND_URL}/api/v1/search/from-cv?limit=${limit}&search_pearch=${searchPearch}&pearch_type=${pearchType}`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      body: backendFormData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar candidatos pelo CV', details: errorData },
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
