export interface AgentMemoryState {
  session_id: string;
  domain: string;
  current_stage: string | null;
  collected_fields: Record<string, unknown>;
  iteration_count: number;
  agent_notes: string | null;
  pending_actions: Record<string, unknown>[];
  accepted_suggestions: Record<string, unknown>[];
  rejected_suggestions: Record<string, unknown>[];
  parecer_data: Record<string, unknown>;
  last_intent: string | null;
  last_confidence: number | null;
  updated_at: string | null;
}

export interface AgentMemorySummary {
  session_id: string;
  domain: string;
  current_stage: string | null;
  fields_count: number;
  completion_percentage: number;
  last_updated: string | null;
}

function getDefaultMemory(sessionId: string, domain: string): AgentMemoryState {
  return {
    session_id: sessionId,
    domain,
    current_stage: null,
    collected_fields: {},
    iteration_count: 0,
    agent_notes: null,
    pending_actions: [],
    accepted_suggestions: [],
    rejected_suggestions: [],
    parecer_data: {},
    last_intent: null,
    last_confidence: null,
    updated_at: null,
  };
}

function getDefaultSummary(sessionId: string, domain: string): AgentMemorySummary {
  return {
    session_id: sessionId,
    domain,
    current_stage: null,
    fields_count: 0,
    completion_percentage: 0,
    last_updated: null,
  };
}

export const agentMemoryService = {
  async getMemory(sessionId: string, domain: string = 'wizard'): Promise<AgentMemoryState> {
    const res = await fetch(`/api/backend-proxy/agent-memory/${sessionId}?domain=${domain}`);
    if (!res.ok) return getDefaultMemory(sessionId, domain);
    return res.json();
  },

  async getMemorySummary(sessionId: string, domain: string = 'wizard'): Promise<AgentMemorySummary> {
    const res = await fetch(`/api/backend-proxy/agent-memory/${sessionId}/summary?domain=${domain}`);
    if (!res.ok) return getDefaultSummary(sessionId, domain);
    return res.json();
  },

  async resetMemory(sessionId: string, domain: string = 'wizard'): Promise<boolean> {
    const res = await fetch(`/api/backend-proxy/agent-memory/${sessionId}?domain=${domain}`, { method: 'DELETE' });
    return res.ok;
  },

  async getActiveSessions(domain?: string, limit: number = 10): Promise<AgentMemorySummary[]> {
    const params = new URLSearchParams();
    if (domain) params.set('domain', domain);
    params.set('limit', String(limit));
    const res = await fetch(`/api/backend-proxy/agent-memory/active-sessions?${params}`);
    if (!res.ok) return [];
    return res.json();
  },
};
