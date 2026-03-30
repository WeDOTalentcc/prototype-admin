export interface ChatMessage {
  conversation_id?: string
  content: string
  user_id?: string
  attachments?: File[]
  audio?: Blob
}

export interface ChatResponse {
  message: {
    id: string
    conversation_id: string
    role: string
    content: string
    message_metadata: Record<string, unknown>
    created_at: string
  }
  conversation: {
    id: string
    user_id: string
    user_role: string
    title?: string
    intent?: string
    workflow_type?: string
    workflow_step: number
    workflow_data?: Record<string, unknown>
    status: string
    created_at: string
    updated_at: string
  }
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface OrchestratorProcessRequest {
  user_id: string
  message: string
  conversation_id?: string
  context_type?: 'general' | 'wizard' | 'pipeline' | string  // Context type for routing
  context_id?: string  // ID related to context (e.g., job_id)
  conversation_context?: {
    conversation_id: string
    context_type: string
    context_id?: string
    summary?: string
    recent_messages: Array<{ role: string; content: string; intent?: string }>
  }  // Previous conversation context for memory
}

export interface OrchestratorProcessResponse {
  success: boolean
  conversation_id?: string
  intent?: string
  agent?: string
  confidence?: number
  result?: Record<string, unknown>
  message?: string
  error?: string
  suggested_tool_call?: {
    tool_name: string
    parameters?: Record<string, unknown>
    requires_confirmation?: boolean
    confirmation_message?: string
  }
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}

// =============================================
// CANDIDATE LIST TYPES
// =============================================

export type InterpretMessageAction = 
  | 'advance_stage'
  | 'go_back'
  | 'confirm'
  | 'reject'
  | 'update_field'
  | 'ask_question'
  | 'provide_data'
  | 'help'
  | 'other'

export interface InterpretMessageRequest {
  message: string
  current_stage: string
  context?: Record<string, unknown>
}

export interface InterpretMessageResponse {
  action: InterpretMessageAction
  confidence: number
  extracted_entities?: Record<string, unknown>
  lia_response?: string
  should_advance: boolean
  target_stage?: string
  clarification_needed: boolean
  clarification_question?: string
  reasoning?: string
}

export interface ConversationalRequest {
  message: string
  context?: string
  mode?: string
}

export interface ConversationalResponse {
  response: string
  understood_intent: string
  suggested_action?: string
  can_help: boolean
}

export type WizardOrchestratorAction = 
  | 'respond' 
  | 'advance_stage' 
  | 'update_fields' 
  | 'request_clarification' 
  | 'provide_suggestion' 
  | 'validate_data'

export interface WizardOrchestratorRequest {
  message: string
  current_stage: string
  collected_data: Record<string, unknown>
  conversation_history?: Array<{ role: string; content: string }>
  company_id?: string
  conversation_id?: string
  user_id?: string
}

export interface WizardOrchestratorResponse {
  success: boolean
  lia_message: string
  detected_criteria: Record<string, unknown>
  next_stage?: string
  auto_transition: boolean
  tool_results: Array<Record<string, unknown>>
  confidence: number
  reasoning_steps: string[]
  intent?: string
  error?: string
  awaiting_confirmation?: boolean
  job_vacancy_id?: string
  job_published?: boolean
  action?: WizardOrchestratorAction
  response?: string
  updated_fields?: Record<string, unknown>
  target_stage?: string
  reasoning?: string
  suggestions?: Array<{ field: string; value: Record<string, unknown>; reason: string }>
  validation_errors?: string[]
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}
