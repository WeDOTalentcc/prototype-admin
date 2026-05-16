"use client";

/**
 * Task #1128 — thin typed client for the two canonical wizard-session REST
 * endpoints. The frontend used to keep wizard state in
 * `localStorage["lia-wizard-state-*"]` and treat it as the source of truth;
 * we now ask the backend on mount/switch and tell the backend to clear on
 * "Nova conversa" / "Cancelar wizard". The Next.js proxy at
 * `/api/backend-proxy/lia/...` forwards to `/api/v1/lia/job-wizard/session/...`.
 *
 * Fail-loud philosophy: every non-2xx is surfaced to the caller (incl.
 * 404 — the canonical backend always returns 200 with `was_active=false`
 * for inactive sessions, so a 404 means deploy mismatch or tenant
 * mismatch and must NOT be silently swallowed). The chat UI logs to
 * Sentry and toasts the recruiter — never swallow silently, that's
 * exactly what got us into the "wizard refuses to die" loop the task
 * is fixing.
 */

export interface WizardSessionState {
  session_id: string;
  thread_id: string;
  active: boolean;
  current_stage: string | null;
  completeness: number;
  requires_approval: boolean;
  stage_data: Record<string, unknown>;
  degraded_stages: Record<string, string | true>;
  conversation_message_count: number;
}

export interface WizardSessionResetResult {
  success: boolean;
  session_id: string;
  thread_id: string;
  was_active: boolean;
}

function backendUrl(sessionId: string): string {
  return `/api/backend-proxy/lia/job-wizard/session/${encodeURIComponent(sessionId)}`;
}

export async function fetchWizardSessionState(
  sessionId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<WizardSessionState | null> {
  if (!sessionId) return null;
  const res = await fetchImpl(backendUrl(sessionId), {
    method: "GET",
    credentials: "include",
  });
  // CRITICAL (Task #1128 code review): fail-loud em todos os não-2xx,
  // inclusive 404. O backend canônico devolve 200 com `active=false`
  // para sessões sem snapshot (S4 do sentinela); um 404 só pode
  // significar deploy parcial ou tenant mismatch e o caller PRECISA
  // ver o erro para toast + reset defensivo.
  if (!res.ok) {
    throw new Error(`GET wizard session failed: ${res.status}`);
  }
  return (await res.json()) as WizardSessionState;
}

export async function resetWizardSession(
  sessionId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<WizardSessionResetResult> {
  if (!sessionId) {
    return {
      success: true,
      session_id: "",
      thread_id: "",
      was_active: false,
    };
  }
  const res = await fetchImpl(backendUrl(sessionId), {
    method: "DELETE",
    credentials: "include",
  });
  // CRITICAL (Task #1128 code review): fail-loud em TODOS os status
  // não-2xx, inclusive 404. O backend canônico responde 200 com
  // `was_active=false` quando a sessão já está inativa (idempotência —
  // S3 do sentinela de backend). Um 404 aqui só pode significar deploy
  // parcial (endpoint não montado) ou tenant mismatch (recrutador
  // tentando deletar sessão de outro tenant). Em qualquer caso o caller
  // PRECISA ver o erro — sem isso o frontend resetaria a UI achando que
  // cancelou enquanto o servidor segue com o wizard aberto, exatamente
  // o bug que esta task fecha.
  if (!res.ok) {
    throw new Error(`DELETE wizard session failed: ${res.status}`);
  }
  return (await res.json()) as WizardSessionResetResult;
}

/**
 * Task #1128 — purge every legacy `lia-wizard-state-*` localStorage key
 * left behind by the abolished client-side persistence layer. Called once
 * on chat mount so a recruiter who installed the app before the rollout
 * doesn't keep resurrecting a stale wizard on every reload. Safe to call
 * repeatedly — the second pass is a no-op.
 */
export const LEGACY_WIZARD_STORAGE_PREFIX = "lia-wizard-state";

export function purgeLegacyWizardStorage(): number {
  if (typeof window === "undefined") return 0;
  let removed = 0;
  try {
    const keys: string[] = [];
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i);
      if (k && k.startsWith(LEGACY_WIZARD_STORAGE_PREFIX)) keys.push(k);
    }
    for (const k of keys) {
      window.localStorage.removeItem(k);
      removed += 1;
    }
  } catch {
    /* ignore quota / privacy-mode errors */
  }
  return removed;
}
