import { BACKEND_URL } from './base'
import type {
  BackgroundJob,
  ProactiveAction,
  CreateJobResponse,
  ExecuteJobResponse,
  ActionResponse,
} from './types'

export async function createBackgroundJob(
  jobType: string,
  name: string,
  config: Record<string, unknown>,
  schedule?: string
): Promise<CreateJobResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_type: jobType,
        name,
        config,
        schedule
      })
    })
    if (!response.ok) {
      return { job_id: '', status: 'error' }
    }
    return response.json()
  } catch {
    return { job_id: '', status: 'error' }
  }
}

export async function listBackgroundJobs(
  status?: string,
  limit?: number
): Promise<BackgroundJob[]> {
  try {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (limit) params.set('limit', String(limit))
    const queryString = params.toString() ? `?${params.toString()}` : ''

    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs${queryString}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return []
    }
    return response.json()
  } catch {
    return []
  }
}

export async function executeJob(jobId: string): Promise<ExecuteJobResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs/${jobId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { status: 'error', result: {} }
    }
    return response.json()
  } catch {
    return { status: 'error', result: {} }
  }
}

export async function getProactiveActions(
  status?: string,
  limit?: number
): Promise<ProactiveAction[]> {
  try {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (limit) params.set('limit', String(limit))
    const queryString = params.toString() ? `?${params.toString()}` : ''

    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions${queryString}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return []
    }
    return response.json()
  } catch {
    return []
  }
}

export async function acceptProactiveAction(actionId: string): Promise<ActionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions/${actionId}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { status: 'error' }
    }
    return response.json()
  } catch {
    return { status: 'error' }
  }
}

export async function rejectProactiveAction(actionId: string): Promise<ActionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions/${actionId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      return { status: 'error' }
    }
    return response.json()
  } catch {
    return { status: 'error' }
  }
}
