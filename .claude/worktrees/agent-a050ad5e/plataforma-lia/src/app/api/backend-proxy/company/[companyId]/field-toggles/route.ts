import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { companyId: string } }
) {
  try {
    const { companyId } = params
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/${companyId}/field-toggles`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`)
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao buscar field toggles', 
        details: errorData,
        status: response.status 
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Field toggles GET proxy error:', error)
    return NextResponse.json({ 
      error: 'Erro ao conectar com o backend',
      status: 500 
    }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { companyId: string } }
) {
  try {
    const { companyId } = params
    const body = await request.json()
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/${companyId}/field-toggles`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`)
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao atualizar field toggles', 
        details: errorData,
        status: response.status 
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Field toggles PUT proxy error:', error)
    return NextResponse.json({ 
      error: 'Erro ao conectar com o backend',
      status: 500 
    }, { status: 500 })
  }
}
