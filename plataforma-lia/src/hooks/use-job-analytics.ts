import { useState, useCallback } from 'react';
import * as jobAnalyticsApi from '@/lib/api/job-analytics';

export function useJobAnalytics() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<jobAnalyticsApi.AnalyticsResponse | null>(null);
  
  const executeCommand = useCallback(async (commandId: string, context: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobAnalyticsApi.executeCommand(commandId, context);
      if (data.success === false && data.error) {
        setError(data.error);
      }
      setResult(data);
      return data;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao executar análise';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);
  
  const analyzeNatural = useCallback(async (query: string, context: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobAnalyticsApi.naturalQuery(query, context);
      if (data.success === false && data.error) {
        setError(data.error);
      }
      setResult(data);
      return data;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao processar pergunta';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const getQuickInsights = useCallback(async (jobId: string) => {
    setLoading(true);
    setError(null);
    try {
      return await jobAnalyticsApi.getQuickInsights(jobId);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao buscar insights';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const compareJobs = useCallback(async (jobIds: string[]) => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobAnalyticsApi.compareJobs(jobIds);
      if (data.success === false && data.error) {
        setError(data.error);
      }
      setResult(data);
      return data;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao comparar vagas';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const getSuggestions = useCallback(async (jobId: string) => {
    setLoading(true);
    setError(null);
    try {
      return await jobAnalyticsApi.getSuggestions(jobId);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao buscar sugestões';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const getAvailableCommands = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      return await jobAnalyticsApi.getAvailableCommands();
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Erro ao buscar comandos disponíveis';
      setError(errorMessage);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);
  
  return {
    loading,
    error,
    result,
    executeCommand,
    analyzeNatural,
    getQuickInsights,
    compareJobs,
    getSuggestions,
    getAvailableCommands
  };
}
