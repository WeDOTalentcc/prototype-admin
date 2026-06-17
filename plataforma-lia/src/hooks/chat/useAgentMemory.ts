import { useState, useEffect, useCallback, useRef } from 'react';
import {
  agentMemoryService,
  AgentMemorySummary,
  AgentMemoryState,
} from '@/services/agentMemoryService';

const POLL_INTERVAL_MS = 30_000;

interface UseAgentMemoryParams {
  sessionId: string;
  domain?: string;
  enabled?: boolean;
}

interface UseAgentMemoryReturn {
  memory: AgentMemorySummary | null;
  fullMemory: AgentMemoryState | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
  loadFull: () => Promise<void>;
  reset: () => Promise<void>;
}

export function useAgentMemory({
  sessionId,
  domain = 'wizard',
  enabled = true,
}: UseAgentMemoryParams): UseAgentMemoryReturn {
  const [memory, setMemory] = useState<AgentMemorySummary | null>(null);
  const [fullMemory, setFullMemory] = useState<AgentMemoryState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const mountedRef = useRef(true);

  const fetchSummary = useCallback(async () => {
    if (!sessionId || !enabled) return;
    try {
      setIsLoading(true);
      const data = await agentMemoryService.getMemorySummary(sessionId, domain);
      if (mountedRef.current) {
        setMemory(data && data.fields_count > 0 ? data : null);
      }
    } catch {
      // silent
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [sessionId, domain, enabled]);

  const refresh = useCallback(async () => {
    await fetchSummary();
  }, [fetchSummary]);

  const loadFull = useCallback(async () => {
    if (!sessionId) return;
    try {
      setIsLoading(true);
      const data = await agentMemoryService.getMemory(sessionId, domain);
      if (mountedRef.current) setFullMemory(data);
    } catch {
      // silent
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [sessionId, domain]);

  const reset = useCallback(async () => {
    if (!sessionId) return;
    try {
      await agentMemoryService.resetMemory(sessionId, domain);
      if (mountedRef.current) {
        setMemory(null);
        setFullMemory(null);
      }
    } catch (error) {
      console.error("[useAgentMemory] Error:", error)
      // silent
    }
  }, [sessionId, domain]);

  useEffect(() => {
    mountedRef.current = true;
    fetchSummary();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchSummary]);

  useEffect(() => {
    if (!enabled || !sessionId) return;
    const id = setInterval(fetchSummary, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [enabled, sessionId, fetchSummary]);

  return { memory, fullMemory, isLoading, refresh, loadFull, reset };
}
