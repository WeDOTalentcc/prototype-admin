import { BACKEND_URL } from './base'
import type {
  TranscriptionResponse,
  VoiceChatResponse,
  VoiceStatusResponse,
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
