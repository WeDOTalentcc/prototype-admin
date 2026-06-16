export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/v1/company/departments/import/template`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/csv',
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao baixar template' },
        { status: response.status }
      )
    }

    const blob = await response.blob()
    const headers = new Headers()
    headers.set('Content-Type', 'text/csv')
    headers.set('Content-Disposition', 'attachment; filename=template_departamentos.csv')

    return new NextResponse(blob, {
      status: 200,
      headers,
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
