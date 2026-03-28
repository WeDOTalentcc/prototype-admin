import { getAuthHeaders } from './base'
import type {
  BulkUpdateStatusRequest,
  BulkAssignJobRequest,
  BulkSendEmailRequest,
  BulkStartScreeningRequest,
  BulkExportRequest,
  BulkDeleteRequest,
  BulkOperationResult,
} from './types'

export async function bulkUpdateStatus(request: BulkUpdateStatusRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/update-status', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao atualizar status')
  }
  return response.json()
}

export async function bulkAssignJob(request: BulkAssignJobRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/assign-job', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao atribuir candidatos à vaga')
  }
  return response.json()
}

export async function bulkSendEmail(request: BulkSendEmailRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/send-email', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao enviar emails')
  }
  return response.json()
}

export async function bulkStartScreening(request: BulkStartScreeningRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/start-screening', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao iniciar triagem')
  }
  return response.json()
}

export async function bulkExport(request: BulkExportRequest): Promise<Blob | BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/export', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao exportar candidatos')
  }
  const contentType = response.headers.get('content-type')
  if (contentType?.includes('text/csv') || contentType?.includes('application/vnd.openxmlformats')) {
    return response.blob()
  }
  return response.json()
}

export async function bulkDelete(request: BulkDeleteRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/delete', {
    method: 'DELETE',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao excluir candidatos')
  }
  return response.json()
}
