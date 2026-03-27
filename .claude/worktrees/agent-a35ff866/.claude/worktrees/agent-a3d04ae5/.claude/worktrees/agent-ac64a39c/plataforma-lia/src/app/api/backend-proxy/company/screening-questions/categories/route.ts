import { NextRequest, NextResponse } from 'next/server'
import { getWorkOSSession } from '@/lib/workos-session'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

async function getAuthHeaders(request: NextRequest) {
  const session = await getWorkOSSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`
  }
  return headers
}

export async function GET(request: NextRequest) {
  try {
    const headers = await getAuthHeaders(request)
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/screening-questions/categories`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`)
      return NextResponse.json({
        categories: {
          availability: 'Disponibilidade',
          salary: 'Pretensão Salarial',
          work_model: 'Modelo de Trabalho',
          logistics: 'Logística',
          legal: 'Documentação/Legal',
          experience: 'Experiência',
          language: 'Idiomas',
          custom: 'Personalizada'
        },
        types: {
          text: 'Texto livre',
          yes_no: 'Sim/Não',
          single_choice: 'Escolha única',
          multiple_choice: 'Múltipla escolha',
          scale: 'Escala (1-10)'
        }
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Categories proxy error:', error)
    return NextResponse.json({
      categories: {
        availability: 'Disponibilidade',
        salary: 'Pretensão Salarial',
        work_model: 'Modelo de Trabalho',
        logistics: 'Logística',
        legal: 'Documentação/Legal',
        experience: 'Experiência',
        language: 'Idiomas',
        custom: 'Personalizada'
      },
      types: {
        text: 'Texto livre',
        yes_no: 'Sim/Não',
        single_choice: 'Escolha única',
        multiple_choice: 'Múltipla escolha',
        scale: 'Escala (1-10)'
      }
    })
  }
}
