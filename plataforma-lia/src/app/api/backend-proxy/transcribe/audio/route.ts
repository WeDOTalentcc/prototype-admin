import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const audio = formData.get("audio") as Blob

    if (!audio) {
      return NextResponse.json(
        { error: "No audio provided" },
        { status: 400 }
      )
    }

    const backendFormData = new FormData()
    backendFormData.append("audio", audio)

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/transcribe/audio`, {
        method: "POST",
        body: backendFormData,
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }

    } catch (backendError) {
    }

    return NextResponse.json({
      text: "",
      error: "Transcrição temporariamente indisponível. Por favor, digite sua mensagem.",
    })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to transcribe audio" },
      { status: 500 }
    )
  }
}
