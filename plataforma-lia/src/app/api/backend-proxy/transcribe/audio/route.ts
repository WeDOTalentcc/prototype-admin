export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"
const MAX_AUDIO_SIZE = 25 * 1024 * 1024

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const audio = formData.get("audio") as Blob

    if (!audio || !(audio instanceof Blob)) {
      return NextResponse.json(
        { error: "No audio provided" },
        { status: 400 }
      )
    }

    if (audio.size > MAX_AUDIO_SIZE) {
      return NextResponse.json(
        { error: "Audio file too large (max 25MB)" },
        { status: 413 }
      )
    }

    const backendFormData = new FormData()
    backendFormData.append("audio", audio)

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/voice/transcribe`, {
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
