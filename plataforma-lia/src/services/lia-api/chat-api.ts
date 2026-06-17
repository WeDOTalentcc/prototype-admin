import { BACKEND_URL, getAuthHeaders, getAuthHeadersForFormData } from './base'
import type {
  ChatMessage,
  ChatResponse,
  Conversation,
  OrchestratorProcessRequest,
  OrchestratorProcessResponse,
  InterpretMessageRequest,
  InterpretMessageResponse,
  ConversationalRequest,
  ConversationalResponse,
  ActiveDraftInfo,
} from './types'

export async function sendMessage(data: ChatMessage): Promise<ChatResponse> {
  const hasFiles = (data.attachments && data.attachments.length > 0) || data.audio

  if (hasFiles) {
    const formData = new FormData()
    formData.append('content', data.content)
    if (data.user_id) formData.append('user_id', data.user_id)
    if (data.conversation_id) formData.append('conversation_id', data.conversation_id)

    if (data.attachments) {
      data.attachments.forEach((file) => {
        formData.append(`attachments`, file, file.name)
      })
    }

    if (data.audio) {
      formData.append('audio', data.audio, 'recording.webm')
    }

    const response = await fetch(`${BACKEND_URL}/chat/with-attachments`, {
      method: 'POST',
      headers: getAuthHeadersForFormData(),
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to send message with attachments')
    }

    return response.json()
  }

  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      content: data.content,
      user_id: data.user_id,
      conversation_id: data.conversation_id
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to send message')
  }

  return response.json()
}

export async function getConversations(userId: string): Promise<Conversation[]> {
  const response = await fetch(`${BACKEND_URL}/chat/?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`)
  }

  return response.json()
}

export async function getConversationHistory(conversationId: string): Promise<Record<string, unknown>[]> {
  const response = await fetch(`${BACKEND_URL}/chat/?conversation_id=${conversationId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch conversation history: ${response.statusText}`)
  }

  const data = await response.json()
  return data.messages || []
}

export async function orchestratorProcess(request: OrchestratorProcessRequest): Promise<OrchestratorProcessResponse> {
  const response = await fetch(`${BACKEND_URL}/orchestrator/process`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    return {
      success: false,
      error: error.detail || 'Orchestrator process failed',
    }
  }

  return response.json()
}

export async function interpretMessage(request: InterpretMessageRequest): Promise<InterpretMessageResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/job-wizard/interpret`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      return {
        action: 'other',
        confidence: 0.5,
        should_advance: false,
        clarification_needed: false,
        lia_response: 'Não consegui interpretar a mensagem. Pode reformular?'
      }
    }

    return await response.json()
  } catch {
    return {
      action: 'other',
      confidence: 0.5,
      should_advance: false,
      clarification_needed: false,
      lia_response: 'Estou com dificuldade de conexão. Pode tentar novamente em alguns segundos?'
    }
  }
}

export async function getConversationalResponse(request: ConversationalRequest): Promise<ConversationalResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/conversational`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      return {
        response: "Estou com dificuldade de conexão no momento. Pode tentar novamente em alguns segundos?",
        understood_intent: "fallback",
        can_help: true
      }
    }

    return await response.json()
  } catch {
    return {
      response: "Estou com dificuldade de conexão no momento. Pode tentar novamente em alguns segundos?",
      understood_intent: "fallback",
      can_help: true
    }
  }
}

export async function getActiveDraft(): Promise<ActiveDraftInfo | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/active-draft`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      return null
    }

    const data = await response.json()
    if (data.success && data.job_draft) {
      return data.job_draft as ActiveDraftInfo
    }
    return null
  } catch {
    return null
  }
}
