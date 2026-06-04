export interface KanbanAssistantRequest {
  command: string
  command_type?: string
  job_context: {
    title: string
    department?: string
    level?: string
    requirements?: string[]
    skills?: string[]
    location?: string
    salary?: string
    workModel?: string
    deadline?: string
  }
  candidates: Array<{
    id: string
    name: string
    role?: string
    currentCompany?: string
    location?: string
    score?: number | null
    fitScore?: number
    skills?: string[]
    experience?: string
    stage?: string
    warnings?: number
    email?: string
    phone?: string
    bigFive?: Record<string, number>
  }>
  selected_candidate_ids?: string[]
}

export interface KanbanAssistantResponse {
  success: boolean
  response_type: string
  content: string
  structured_data?: Record<string, unknown>
  suggested_actions: string[]
  follow_up_prompts: string[]
  ui_action?: string | null
  ui_action_params?: Record<string, unknown> | null
}

export async function callKanbanAssistant(
  request: KanbanAssistantRequest
): Promise<KanbanAssistantResponse> {
  const response = await fetch(`/api/backend-proxy/lia/kanban-assistant`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Kanban Assistant request failed: ${errorText}`)
  }

  return response.json()
}

export async function getKanbanCommandTypes(): Promise<{
  command_types: Array<{
    type: string
    description: string
    keywords: string[]
    example: string
  }>
}> {
  const response = await fetch(`/api/backend-proxy/lia/kanban-assistant/command-types`)

  if (!response.ok) {
    throw new Error("Failed to fetch command types")
  }

  return response.json()
}


export interface OrchestratedJobChatRequest {
  message: string
  job_context: {
    id?: string
    title: string
    department?: string
    level?: string
    requirements?: string[]
    skills?: string[]
    location?: string
    salary?: string
    workModel?: string
    deadline?: string
  }
  candidates: Array<{
    id: string
    name: string
    role?: string
    currentCompany?: string
    location?: string
    score?: number | null
    wsiScore?: number | null
    wsiTechnical?: number | null
    wsiBehavioral?: number | null
    fitScore?: number
    skills?: string[]
    experience?: string
    stage?: string
    subStatus?: string
    daysInStage?: number
    warnings?: number
    email?: string
    phone?: string
    bigFive?: Record<string, number>
    hasCV?: boolean
  }>
  selected_candidate_ids?: string[]
  conversation_id?: string
  company_id?: string
}

// Interface for Jobs Management page context (multiple jobs overview)
export interface OrchestratedJobsManagementRequest {
  message: string
  jobs_context: {
    total: number
    active: number
    paused: number
    completed: number
    urgent: number
    withoutCandidates: number
    totalCandidates: number
    currentFilter?: string
  }
  selected_jobs?: Array<{
    id: number
    title: string
    department: string
    status: string
  }>
  top_jobs?: Array<{
    id: number
    title: string
    department: string
    status: string
    priority: string
    candidatesTotal: number
    candidatesInterview: number
    hired: number
    daysOpen: number
  }>
  conversation_history?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
  action?: string
  conversation_id?: string
  company_id?: string
}

export interface OrchestratedJobsManagementResponse {
  success: boolean
  content: string
  agent_used: string
  intent_detected: string
  confidence: number
  suggested_prompts: string[]
  ui_action?: 'start_job_wizard' | 'filter_jobs' | 'compare_jobs' | null
  ui_action_params?: {
    initial_message?: string
    filter?: string
    job_ids?: number[]
    [key: string]: unknown
  }
  action_executed?: boolean
  action_result?: {
    job_id?: number
    job_title?: string
    status?: string
    previous_status?: string
    new_job_id?: number
    simulated?: boolean
    action?: string
    [key: string]: unknown
  }
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  conversation_id?: string
}

export interface OrchestratedJobChatResponse {
  success: boolean
  content: string
  agent_used: string
  agents_consulted: string[]
  intent_detected: string
  confidence: number
  structured_data?: {
    funnel_metrics?: Record<string, unknown>
    top_candidates?: Array<Record<string, unknown>>
  }
  suggested_prompts: string[]
  actions: Array<{
    type: string
    action: string
    label: string
    candidate_ids?: string[]
  }>
  ui_action?: 'start_job_wizard' | 'move_candidate' | null
  ui_action_params?: {
    initial_message?: string
    [key: string]: unknown
  }
  conversation_id?: string
  action_executed?: boolean
  action_result?: {
    candidate_id?: string
    candidate_name?: string
    from_stage?: string
    to_stage?: string
    subject?: string
    datetime?: string
    moved_at?: string
    sent_at?: string
    scheduled_at?: string
    simulated?: boolean
    action?: string
    [key: string]: unknown
  }
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
}

export async function callOrchestratedJobChat(
  request: OrchestratedJobChatRequest
): Promise<OrchestratedJobChatResponse> {
  const response = await fetch(`/api/backend-proxy/orchestrator/job-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Orchestrated job chat request failed: ${errorText}`)
  }

  return response.json()
}

// Function for Jobs Management page (multiple jobs overview context)
export async function callOrchestratedJobsManagement(
  request: OrchestratedJobsManagementRequest
): Promise<OrchestratedJobsManagementResponse> {
  const response = await fetch(`/api/backend-proxy/orchestrator/jobs-management`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Jobs management chat request failed: ${errorText}`)
  }

  return response.json()
}

export async function getJobChatIntents(): Promise<{
  intents: Array<{
    id: string
    description: string
    keywords: string[]
    agent: string
  }>
}> {
  const response = await fetch(`/api/backend-proxy/orchestrator/job-chat/intents`)

  if (!response.ok) {
    throw new Error("Failed to fetch job chat intents")
  }

  return response.json()
}


export interface OrchestratedTalentChatRequest {
  message: string
  candidates: Array<{
    id: string
    name: string
    current_title?: string
    current_company?: string
    location?: string
    skills?: string[]
    experience_years?: number
    lia_score?: number | null
    wsi_score?: number | null
    source?: string
    work_model?: string
    is_remote?: boolean
    willing_to_relocate?: boolean
    salary_expectation_clt?: number
    salary_expectation_pj?: number
    languages?: Record<string, string>
    seniority_level?: string
    gender?: string
    status?: string
    is_active?: boolean
    technical_skills?: string[]
    soft_skills?: string[]
  }>
  selected_candidate_ids?: string[]
  search_context?: {
    query?: string
    mode?: string
    total_results?: number
    local_results?: number
    global_results?: number
    active_filters?: Record<string, unknown>
  }
  target_job?: {
    id?: string
    title?: string
    department?: string
    level?: string
    skills?: string[]
  }
  conversation_id?: string
  company_id?: string
}

export interface OrchestratedTalentChatResponse {
  success: boolean
  content: string
  agent_used: string
  agents_consulted: string[]
  intent_detected: string
  confidence: number
  structured_data?: Record<string, unknown>
  suggested_prompts: string[]
  actions: Array<{
    type: string
    action: string
    label: string
    candidate_ids?: string[]
  }>
  ui_action?: 'start_job_wizard' | 'switch_search_mode' | 'open_communication_modal' | 'open_schedule_modal' | 'open_screening_modal' | 'trigger_export' | 'open_add_to_list_modal' | null
  ui_action_params?: {
    initial_message?: string
    mode?: string
    [key: string]: unknown
  }
  conversation_id?: string
  action_executed?: boolean
  action_result?: {
    candidate_id?: string
    candidate_name?: string
    from_stage?: string
    to_stage?: string
    subject?: string
    datetime?: string
    moved_at?: string
    sent_at?: string
    scheduled_at?: string
    simulated?: boolean
    action?: string
    [key: string]: unknown
  }
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
}

export async function callOrchestratedTalentChat(
  request: OrchestratedTalentChatRequest
): Promise<OrchestratedTalentChatResponse> {
  const response = await fetch(`/api/backend-proxy/orchestrator/talent-chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Orchestrated talent chat request failed: ${errorText}`)
  }

  return response.json()
}

export async function getTalentChatIntents(): Promise<{
  intents: Array<{
    id: string
    description: string
    keywords: string[]
    agent?: string
    ui_action?: string
  }>
  context: string
}> {
  const response = await fetch(`/api/backend-proxy/orchestrator/talent-chat/intents`)

  if (!response.ok) {
    throw new Error("Failed to fetch talent chat intents")
  }

  return response.json()
}


