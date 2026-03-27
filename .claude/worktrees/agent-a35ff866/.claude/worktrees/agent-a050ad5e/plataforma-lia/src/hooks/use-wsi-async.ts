/**
 * useWSIAsync — E3 (WSI Assíncrono)
 * Hook para candidato responder WSI via link de email.
 */
"use client";
import { useState, useCallback } from "react";

interface WSIQuestion {
  id: string;
  text: string;
  type: "text" | "choice";
  options?: string[];
}

interface WSISessionState {
  token: string;
  status: "pending" | "in_progress" | "completed" | "expired";
  currentQuestion: WSIQuestion | null;
  progress: number;
  totalQuestions: number;
}

interface UseWSIAsyncReturn {
  session: WSISessionState | null;
  isLoading: boolean;
  error: string | null;
  isComplete: boolean;
  loadSession: (token: string) => Promise<void>;
  submitAnswer: (answer: string) => Promise<void>;
  completeSession: () => Promise<void>;
}

export function useWSIAsync(token: string): UseWSIAsyncReturn {
  const [session, setSession] = useState<WSISessionState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const loadSession = useCallback(async (tkn: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/backend-proxy/wsi-async/${tkn}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSession({
        token: tkn,
        status: data.status,
        currentQuestion: data.current_question || null,
        progress: data.progress || 0,
        totalQuestions: data.total_questions || 0,
      });
      if (data.status === "completed") setIsComplete(true);
    } catch (err) {
      setError("Não foi possível carregar a sessão. Tente novamente.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const submitAnswer = useCallback(async (answer: string) => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/backend-proxy/wsi-async/${token}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.is_complete) {
        setIsComplete(true);
        setSession(prev => prev ? { ...prev, status: "completed" } : prev);
      } else if (data.next_question) {
        setSession(prev => prev ? {
          ...prev,
          currentQuestion: data.next_question,
          progress: prev.progress + 1,
        } : prev);
      }
    } catch (err) {
      setError("Erro ao enviar resposta. Tente novamente.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  const completeSession = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      await fetch(`/api/backend-proxy/wsi-async/${token}/complete`);
      setIsComplete(true);
    } catch (err) {
      // fail-open
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  return { session, isLoading, error, isComplete, loadSession, submitAnswer, completeSession };
}
