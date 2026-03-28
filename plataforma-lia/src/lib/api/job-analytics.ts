export interface CommandTemplate {
  id: string;
  name: string;
  description: string;
  required_context: string[];
}

export interface AnalyticsResponse {
  command: string;
  agent_used: string;
  response: string;
  data: Record<string, unknown>;
  charts: Array<{type: string; title: string; data: Record<string, unknown>}>;
  suggestions: string[];
  metadata: {execution_time_ms: number};
  success?: boolean;
  error?: string;
}

export interface QuickInsights {
  total_candidates: number;
  days_open: number;
  candidates_by_stage: Record<string, number>;
  new_this_week: number;
  funnel_conversion: number;
  quality_score: number;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function getAvailableCommands(): Promise<CommandTemplate[]> {
  const res = await fetch('/api/backend-proxy/job-analytics?action=commands');
  const data = await handleResponse<{commands: CommandTemplate[]}>(res);
  return data.commands;
}

export async function executeCommand(commandId: string, context: Record<string, unknown>): Promise<AnalyticsResponse> {
  const res = await fetch('/api/backend-proxy/job-analytics?action=execute', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({command_id: commandId, context})
  });
  return handleResponse<AnalyticsResponse>(res);
}

export async function naturalQuery(query: string, context: Record<string, unknown>): Promise<AnalyticsResponse> {
  const res = await fetch('/api/backend-proxy/job-analytics?action=natural-query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query, context})
  });
  return handleResponse<AnalyticsResponse>(res);
}

export async function getQuickInsights(jobId: string): Promise<QuickInsights> {
  const res = await fetch(`/api/backend-proxy/job-analytics?action=quick-insights&job_id=${encodeURIComponent(jobId)}`);
  return handleResponse<QuickInsights>(res);
}

export async function compareJobs(jobIds: string[]): Promise<AnalyticsResponse> {
  const res = await fetch('/api/backend-proxy/job-analytics?action=compare', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({job_ids: jobIds})
  });
  return handleResponse<AnalyticsResponse>(res);
}

export async function getSuggestions(jobId: string): Promise<{suggestions: Array<{action: string; reason: string; priority: string}>}> {
  const res = await fetch(`/api/backend-proxy/job-analytics?action=suggestions&job_id=${encodeURIComponent(jobId)}`);
  return handleResponse<{suggestions: Array<{action: string; reason: string; priority: string}>}>(res);
}
