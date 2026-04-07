export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getWorkOSSession } from '@/lib/workos-session'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

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
