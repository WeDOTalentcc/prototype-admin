import { BACKEND_URL } from './base'
import type {
  TranscriptionResponse,
  VoiceChatResponse,
  VoiceStatusResponse,
  VoiceStreamMessage,
  VoiceStreamSessionResponse,
  ImageAnalysisResponse,
  DocumentAnalysisResponse,
  ResumeAnalysisResponse,
  MultimodalStatusResponse,
} from './types'

export async function transcribeAudio(
  audioBlob: Blob,
  language?: string
): Promise<TranscriptionResponse> {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    if (language) formData.append('language', language)

    const response = await fetch(`${BACKEND_URL}/lia/voice/transcribe`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      return { text: '', confidence: 0, duration: 0 }
    }
    return response.json()
  } catch {
    return { text: '', confidence: 0, duration: 0 }
  }
}

export async function synthesizeSpeech(
  text: string,
  voice?: string
): Promise<Blob> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/voice/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice })
    })
    if (!response.ok) {
      return new Blob()
    }
    return response.blob()
  } catch {
    return new Blob()
  }
}

export async function voiceChat(
  audioBlob: Blob,
  sessionId?: string
): Promise<VoiceChatResponse> {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    if (sessionId) formData.append('session_id', sessionId)

    const response = await fetch(`${BACKEND_URL}/lia/voice/chat`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      return {
        transcription: '',
        response_text: 'Desculpe, não consegui processar o áudio.',
        response_audio_base64: '',
        session_id: sessionId || ''
      }
    }
    return response.json()
  } catch {
    return {
      transcription: '',
      response_text: 'Desculpe, ocorreu um erro ao processar o áudio.',
      response_audio_base64: '',
      session_id: sessionId || ''
    }
  }
}

export async function getVoiceStatus(): Promise<VoiceStatusResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/voice/status`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { transcription_available: false, synthesis_available: false }
    }
    return response.json()
  } catch {
    return { transcription_available: false, synthesis_available: false }
  }
}

export async function startVoiceStreamSession(
  candidateId: string,
  candidateName: string,
  jobTitle: string,
  companyId: string,
  jobId?: string,
  language?: string,
): Promise<VoiceStreamSessionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/voice-stream/start-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_id: companyId,
        language: language || 'pt-BR',
        system_prompt: `Candidate: ${candidateName}, Position: ${jobTitle}`,
      }),
    })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        session_id: '',
        status: 'error',
        voice_provider: '',
        error: errorData.detail || 'Failed to start voice session',
      }
    }
    return response.json()
  } catch {
    return {
      success: false,
      session_id: '',
      status: 'error',
      voice_provider: '',
      error: 'Network error starting voice session',
    }
  }
}

export type VoiceStreamEventHandler = (event: VoiceStreamMessage) => void

export function createVoiceStreamConnection(
  sessionId: string,
  wsToken: string,
  onEvent: VoiceStreamEventHandler,
  onClose?: () => void,
  onError?: (error: string) => void,
): {
  sendAudio: (audioData: ArrayBuffer) => void
  sendText: (text: string) => void
  close: () => void
  isConnected: () => boolean
} {
  const wsBase = process.env.NEXT_PUBLIC_WS_URL
    || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
  const wsUrl = `${wsBase}/api/v1/voice-stream/live?session_id=${sessionId}&ws_token=${encodeURIComponent(wsToken)}`

  let ws: WebSocket | null = null
  let connected = false

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected = true
      onEvent({ type: 'status', status: 'connecting', session_id: sessionId })
    }

    ws.onmessage = (event) => {
      try {
        const msg: VoiceStreamMessage = JSON.parse(event.data)
        onEvent(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      connected = false
      onClose?.()
    }

    ws.onerror = () => {
      connected = false
      onError?.('WebSocket connection error')
    }
  } catch (err) {
    onError?.('Failed to create WebSocket connection')
  }

  return {
    sendAudio: (audioData: ArrayBuffer) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return
      const base64 = arrayBufferToBase64(audioData)
      ws.send(JSON.stringify({ type: 'audio', data: base64 }))
    },
    sendText: (text: string) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return
      ws.send(JSON.stringify({ type: 'text', data: text }))
    },
    close: () => {
      if (!ws) return
      try {
        ws.send(JSON.stringify({ type: 'end' }))
      } catch {
        // ignore
      }
      ws.close()
      ws = null
      connected = false
    },
    isConnected: () => connected,
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

export async function analyzeImage(
  file: File,
  analysisType?: string,
  prompt?: string
): Promise<ImageAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (analysisType) formData.append('analysis_type', analysisType)
    if (prompt) formData.append('prompt', prompt)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-image`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      return { analysis: '', confidence: 0 }
    }
    return response.json()
  } catch {
    return { analysis: '', confidence: 0 }
  }
}

export async function analyzeDocument(
  file: File,
  documentType?: string
): Promise<DocumentAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (documentType) formData.append('document_type', documentType)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-document`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      return { text_content: '', structure: {}, formatting_quality: 0 }
    }
    return response.json()
  } catch {
    return { text_content: '', structure: {}, formatting_quality: 0 }
  }
}

export async function analyzeResume(file: File): Promise<ResumeAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-resume`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      return {
        candidate_name: '',
        contact_info: {},
        layout_score: 0,
        improvement_suggestions: []
      }
    }
    return response.json()
  } catch {
    return {
      candidate_name: '',
      contact_info: {},
      layout_score: 0,
      improvement_suggestions: []
    }
  }
}

export async function getMultimodalStatus(): Promise<MultimodalStatusResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/multimodal/status`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { image_analysis: false, video_analysis: false, document_analysis: false }
    }
    return response.json()
  } catch {
    return { image_analysis: false, video_analysis: false, document_analysis: false }
  }
}
