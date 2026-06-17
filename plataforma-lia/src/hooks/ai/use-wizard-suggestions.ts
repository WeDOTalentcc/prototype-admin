import { useState, useCallback } from 'react';
import type {
  FieldSuggestionResponse,
  AllSuggestionsResponse,
  AllSuggestionsRequest,
  SimilarJob,
  DataCoverage,
  SourcePriority,
  WizardSuggestionContext
} from '@/types/wizard-suggestions';

const API_BASE = '/api/v1/wizard';

export function useWizardSuggestions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSuggestion = useCallback(async (
    field: string,
    context: WizardSuggestionContext
  ): Promise<FieldSuggestionResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (context.job_title) params.append('job_title', context.job_title);
      if (context.department) params.append('department', context.department);
      if (context.seniority) params.append('seniority', context.seniority);
      if (context.location) params.append('location', context.location);
      if (context.work_model) params.append('work_model', context.work_model);
      
      const response = await fetch(
        `${API_BASE}/suggestion/${field}?${params.toString()}`
      );
      
      if (!response.ok) {
        throw new Error(`Falha ao buscar sugestão: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getAllSuggestions = useCallback(async (
    request: AllSuggestionsRequest
  ): Promise<AllSuggestionsResponse | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/suggestions/all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`Falha ao buscar sugestões: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getSimilarJobs = useCallback(async (
    job_title?: string,
    department?: string,
    limit: number = 5
  ): Promise<SimilarJob[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (job_title) params.append('job_title', job_title);
      if (department) params.append('department', department);
      params.append('limit', limit.toString());
      
      const response = await fetch(
        `${API_BASE}/similar-jobs?${params.toString()}`
      );
      
      if (!response.ok) {
        throw new Error(`Falha ao buscar vagas similares: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const getDataCoverage = useCallback(async (): Promise<DataCoverage | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/data-coverage`);
      
      if (!response.ok) {
        throw new Error(`Falha ao buscar cobertura: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getSourcesPriority = useCallback(async (): Promise<SourcePriority[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/sources-priority`);
      
      if (!response.ok) {
        throw new Error(`Falha ao buscar prioridades: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.sources || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getSuggestion,
    getAllSuggestions,
    getSimilarJobs,
    getDataCoverage,
    getSourcesPriority
  };
}

export function useAutoFillWizard() {
  const { getAllSuggestions, loading, error } = useWizardSuggestions();
  const [autoFilledFields, setAutoFilledFields] = useState<Set<string>>(new Set());

  const autoFillFields = useCallback(async (
    context: WizardSuggestionContext,
    currentData: Record<string, unknown>,
    minConfidence: number = 0.7
  ): Promise<Record<string, unknown>> => {
    const suggestions = await getAllSuggestions(context);
    
    if (!suggestions) return currentData;
    
    const updates: Record<string, unknown> = {};
    const newAutoFilled = new Set<string>();
    
    Object.entries(suggestions.suggestions).forEach(([field, suggestion]) => {
      if (!suggestion.best_suggestion) return;
      
      const isFieldEmpty = !currentData[field] || 
        (Array.isArray(currentData[field]) && currentData[field].length === 0);
      
      if (isFieldEmpty && suggestion.best_suggestion.confidence >= minConfidence) {
        updates[field] = suggestion.best_suggestion.value;
        newAutoFilled.add(field);
      }
    });
    
    setAutoFilledFields(prev => new Set([...prev, ...newAutoFilled]));
    
    return { ...currentData, ...updates };
  }, [getAllSuggestions]);

  const clearAutoFilled = useCallback((field?: string) => {
    if (field) {
      setAutoFilledFields(prev => {
        const next = new Set(prev);
        next.delete(field);
        return next;
      });
    } else {
      setAutoFilledFields(new Set());
    }
  }, []);

  const isAutoFilled = useCallback((field: string): boolean => {
    return autoFilledFields.has(field);
  }, [autoFilledFields]);

  return {
    loading,
    error,
    autoFillFields,
    autoFilledFields,
    clearAutoFilled,
    isAutoFilled
  };
}
