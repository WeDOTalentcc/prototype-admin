import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.LIA_BACKEND_URL || 'http://0.0.0.0:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/lia/conversational`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { 
          response: "Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
          understood_intent: "fallback",
          can_help: true
        },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { 
        response: "Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
        understood_intent: "fallback",
        can_help: true
      },
      { status: 200 }
    )
  }
}
