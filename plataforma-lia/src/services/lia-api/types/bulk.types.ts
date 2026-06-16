export interface BulkOperationError {
  id: string
  error_message: string    // was: error (aligned to BE bulk_actions.py:98)
}

export interface BulkOperationResult {
  total: number
  successful: number       // was: success: boolean (aligned to BE bulk_actions.py:104)
  failed: number
  errors: BulkOperationError[]
  processed_ids: string[]  // was: processed: number (aligned to BE bulk_actions.py:108)
  message?: string
}

export interface BulkUpdateStatusRequest {
  candidate_ids: string[]
  new_status: string
}

export interface BulkAssignJobRequest {
  candidate_ids: string[]
  job_vacancy_id: string   // was: job_id (aligned to BE BulkAssignJobRequest)
  notes?: string
}

export interface BulkSendEmailRequest {
  candidate_ids: string[]
  template_id: string
  custom_data?: Record<string, unknown>
}

export interface BulkStartScreeningRequest {
  candidate_ids: string[]
  job_vacancy_id: string   // ADDED - required by BE for saturation guard
  screening_type?: string
  override_saturation?: boolean
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
