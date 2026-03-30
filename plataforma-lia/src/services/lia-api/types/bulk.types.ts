export interface BulkOperationResult {
  success: boolean
  processed: number
  failed: number
  errors: Array<{
    id: string
    error: string
  }>
  results?: Array<{
    id: string
    status: string
    success: boolean
    error?: string
  }>
}

export interface BulkUpdateStatusRequest {
  candidate_ids: string[]
  new_status: string
}

export interface BulkAssignJobRequest {
  candidate_ids: string[]
  job_id: string
}

export interface BulkSendEmailRequest {
  candidate_ids: string[]
  template_id: string
  custom_data?: Record<string, unknown>
}

export interface BulkStartScreeningRequest {
  candidate_ids: string[]
  screening_type?: string
}

export interface BulkExportRequest {
  candidate_ids: string[]
  format: 'csv' | 'xlsx'
  fields?: string[]
}

export interface BulkDeleteRequest {
  candidate_ids: string[]
  hard_delete?: boolean
}

// =============================================
// NOTIFICATION TYPES
// =============================================
