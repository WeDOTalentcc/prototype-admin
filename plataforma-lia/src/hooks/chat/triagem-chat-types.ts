// Shared types and utilities for the triagem chat hook family.
// All domain types (TriagemMessage, TriagemSession, etc.) come from
// @/components/triagem/types and are re-exported here for convenience.

export type {
  TriagemMessageType,
  TriagemSession,
  TriagemConfig,
  TriagemMessage,
  TriagemError,
  TriagemPageState,
  WSIProgress,
  TriagemCompletionSummary,
  SendMessagePayload,
  UseTriagemChatReturn,
} from "@/components/triagem/types"

import type {
  TriagemMessage,
  TriagemSession,
  TriagemError,
  WSIProgress,
} from "@/components/triagem/types"

export const API_BASE = "/api/backend-proxy/triagem"
export const DEBOUNCE_MS = 300
export const TIMEOUT_MS = 30000
export const MAX_RETRIES = 2

import { fetchWithRetry as canonicalFetchWithRetry } from "@/services/lia-api/base"

// Thin wrapper around the canonical fetchWithRetry (services/lia-api/base).
// The legacy local helper retried indiscriminately on any network error and
// never honored `Retry-After`; the canonical helper retries only on
// 5xx/429/network and respects `Retry-After`. We preserve the longer
// per-attempt timeout (TIMEOUT_MS) historically used by the triagem chat,
// because LLM responses can take longer than the 20s default.
export function fetchWithRetry(url: string, options: RequestInit = {}): Promise<Response> {
  return canonicalFetchWithRetry(url, options, { timeoutMs: TIMEOUT_MS })
}

export function base64ToAudioUrl(base64Data: string): string {
  const binaryStr = atob(base64Data)
  const bytes = new Uint8Array(binaryStr.length)
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: "audio/mp3" })
  return URL.createObjectURL(blob)
}

export function mapBackendMessage(raw: Record<string, unknown>): TriagemMessage {
  let audioUrl: string | null = (raw.audio_url as string) ?? (raw.audioUrl as string) ?? null
  if (!audioUrl && raw.audio_base64) {
    try {
      audioUrl = base64ToAudioUrl(raw.audio_base64 as string)
    } catch {
      /* ignore decode errors */
    }
  }
  return {
    id: String(raw.id ?? ""),
    sessionId: String(raw.session_id ?? raw.sessionId ?? ""),
    role: (raw.sender as string) === "lia" || (raw.sender as string) === "candidate"
      ? (raw.sender as "lia" | "candidate")
      : (raw.role as "lia" | "candidate") ?? "lia",
    type: ((raw.message_type as string) ?? (raw.type as string) ?? "text") as TriagemMessage["type"],
    content: String(raw.content ?? ""),
    options: (raw.options as TriagemMessage["options"]) ?? null,
    selectedOption: (raw.selected_option as string) ?? (raw.selectedOption as string) ?? null,
    likertValue: (raw.likert_value as number) ?? (raw.likertValue as number) ?? null,
    likertLabels: (raw.likert_labels as string[]) ?? (raw.likertLabels as string[]) ?? null,
    timestamp: String(raw.created_at ?? raw.timestamp ?? new Date().toISOString()),
    blockIndex: (raw.wsi_block as number) ?? (raw.blockIndex as number) ?? null,
    blockName: (raw.block_name as string) ?? (raw.blockName as string) ?? null,
    audioUrl,
  }
}

export function mapBackendProgress(raw: Record<string, unknown>): WSIProgress {
  return {
    currentBlock: (raw.current_block as number) ?? (raw.currentBlock as number) ?? 0,
    totalBlocks: (raw.total_blocks as number) ?? (raw.totalBlocks as number) ?? 7,
    currentBlockName: String(raw.block_name ?? raw.currentBlockName ?? ""),
    questionsAnswered: (raw.questions_answered as number) ?? (raw.questionsAnswered as number) ?? 0,
    totalQuestions: (raw.total_questions as number) ?? (raw.totalQuestions as number) ?? 0,
    estimatedMinutesRemaining: (raw.estimated_minutes_remaining as number) ?? (raw.estimatedMinutesRemaining as number) ?? 0,
  }
}

export function mapBackendSession(raw: Record<string, unknown>): TriagemSession {
  const progress = raw.progress
    ? mapBackendProgress(raw.progress as Record<string, unknown>)
    : {
        currentBlock: (raw.current_block as number) ?? 0,
        totalBlocks: (raw.total_blocks as number) ?? 7,
        currentBlockName: "",
        questionsAnswered: 0,
        totalQuestions: 0,
        estimatedMinutesRemaining: 0,
      }
  return {
    id: String(raw.id ?? ""),
    token: String(raw.token ?? ""),
    status: (raw.status as TriagemSession["status"]) ?? "invited",
    candidateId: String(raw.candidate_id ?? raw.candidateId ?? ""),
    candidateName: String(raw.candidate_name ?? raw.candidateName ?? ""),
    jobId: String(raw.job_id ?? raw.jobId ?? ""),
    jobTitle: String(raw.job_title ?? raw.jobTitle ?? ""),
    companyName: String(raw.company_name ?? raw.companyName ?? ""),
    companyLogoUrl: (raw.company_logo_url as string) ?? (raw.companyLogoUrl as string) ?? null,
    progress,
    createdAt: String(raw.created_at ?? raw.createdAt ?? ""),
    expiresAt: String(raw.expires_at ?? raw.expiresAt ?? ""),
    startedAt: (raw.started_at as string) ?? (raw.startedAt as string) ?? null,
    completedAt: (raw.completed_at as string) ?? (raw.completedAt as string) ?? null,
    wsiFinalScore: (raw.wsi_final_score as number) ?? (raw.wsiFinalScore as number) ?? null,
    recommendation: (raw.recommendation as TriagemSession["recommendation"]) ?? null,
  }
}

function extractErrorMessage(body: Record<string, unknown>): string | undefined {
  return (body.detail as string) || (body.message as string) || undefined
}

export function mapErrorResponse(status: number, body: Record<string, unknown>): TriagemError {
  const raw = extractErrorMessage(body)
  const isGeneric = !raw || raw === "Not Found" || raw === "Internal Server Error"
  const msg = isGeneric ? undefined : raw
  if (status === 404) {
    return { code: "TOKEN_INVALID", message: msg || "Token inv\u00e1lido ou n\u00e3o encontrado. Verifique o link recebido." }
  }
  if (status === 410) {
    return { code: "TOKEN_EXPIRED", message: msg || "Este link expirou. Solicite um novo convite ao recrutador." }
  }
  if (status === 409) {
    return { code: "SESSION_COMPLETED", message: msg || "Esta triagem j\u00e1 foi conclu\u00edda." }
  }
  if (status === 429) {
    return { code: "RATE_LIMITED", message: msg || "Muitas requisi\u00e7\u00f5es. Tente novamente em instantes." }
  }
  return { code: "SERVER_ERROR", message: msg || "Erro interno. Tente novamente." }
}
