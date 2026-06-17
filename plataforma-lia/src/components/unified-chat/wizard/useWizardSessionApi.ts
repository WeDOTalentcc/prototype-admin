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
 *
 * Task #1177 — the GET path on mount adds a short retry loop for
 * transient "backend not reachable yet" errors (503 retryable + raw
 * fetch failures during cold start). After the budget is exhausted we
 * throw `WizardBackendUnavailableError` so the caller can show a
 * neutral "Conectando ao servidor…" toast instead of the alarming
 * "Não consegui carregar o estado do wizard" + dev overlay. Real
 * upstream errors (500/404/4xx) continue to fail on the first try.
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

/**
 * Task #1177 — thrown by `fetchWizardSessionState` when the backend stays
 * unreachable across every retry attempt (cold start, rolling restart,
 * upstream 502/503/504). The hydration `useEffect` in `UnifiedChat`
 * branches on this type to show a neutral toast and suppress the
 * `console.error` that would otherwise trigger the Next.js dev overlay.
 */
export class WizardBackendUnavailableError extends Error {
  readonly attempts: number;
  readonly lastStatus: number | null;
  readonly code: string | null;
  constructor(opts: { attempts: number; lastStatus: number | null; code: string | null }) {
    super(
      `Wizard backend unavailable after ${opts.attempts} attempt(s) (status=${opts.lastStatus ?? 'n/a'}, code=${opts.code ?? 'n/a'})`,
    );
    this.name = 'WizardBackendUnavailableError';
    this.attempts = opts.attempts;
    this.lastStatus = opts.lastStatus;
    this.code = opts.code;
  }
}

// Task #1177 — short exponential backoff. 300 + 800 + 2000 ≈ 3.1s of
// total wait across 3 retries (4 attempts), which is the typical cold
// start budget for the FastAPI worker on Replit and well under the
// recruiter patience window.
const RETRY_DELAYS_MS = [300, 800, 2000] as const;

function backendUrl(sessionId: string): string {
  return `/api/backend-proxy/lia/job-wizard/session/${encodeURIComponent(sessionId)}`;
}

function isRetryableStatus(status: number): boolean {
  // 503 is what our own proxy emits for ECONNREFUSED/timeout (Task
  // #1177). 502/504 cover the equivalents when there's a real LB
  // upstream in front of FastAPI. 500 is NOT retryable — that's a
  // genuine endpoint exception and the caller should fail loud.
  return status === 502 || status === 503 || status === 504;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchWizardSessionState(
  sessionId: string,
  fetchImpl: typeof fetch = fetch,
): Promise<WizardSessionState | null> {
  if (!sessionId) return null;
  const totalAttempts = RETRY_DELAYS_MS.length + 1;
  let lastStatus: number | null = null;
  let lastCode: string | null = null;

  for (let attempt = 0; attempt < totalAttempts; attempt++) {
    let res: Response;
    try {
      res = await fetchImpl(backendUrl(sessionId), {
        method: 'GET',
        credentials: 'include',
      });
    } catch (networkErr) {
      // The proxy normally catches connection failures and returns 503,
      // but `fetch()` itself can still reject (e.g. the proxy is being
      // recompiled mid-request). Treat as retryable.
      lastStatus = null;
      lastCode = networkErr instanceof Error ? networkErr.name : 'NETWORK';
      if (attempt < totalAttempts - 1) {
        await sleep(RETRY_DELAYS_MS[attempt]);
        continue;
      }
      throw new WizardBackendUnavailableError({
        attempts: totalAttempts,
        lastStatus,
        code: lastCode,
      });
    }

    if (res.ok) {
      return (await res.json()) as WizardSessionState;
    }

    lastStatus = res.status;
    if (isRetryableStatus(res.status)) {
      // Try to pull the `code` field the proxy sets so the eventual
      // error message is informative without leaking sensitive details.
      try {
        const body = await res.clone().json();
        if (body && typeof body === 'object' && typeof body.code === 'string') {
          lastCode = body.code;
        }
      } catch {
        /* ignore — body parse is best-effort */
      }
      if (attempt < totalAttempts - 1) {
        await sleep(RETRY_DELAYS_MS[attempt]);
        continue;
      }
      throw new WizardBackendUnavailableError({
        attempts: totalAttempts,
        lastStatus,
        code: lastCode,
      });
    }

    // CRITICAL (Task #1128 code review): fail-loud em todos os não-2xx
    // não-retryáveis, inclusive 404. O backend canônico devolve 200 com
    // `active=false` para sessões sem snapshot (S4 do sentinela); um 404
    // só pode significar deploy parcial ou tenant mismatch e o caller
    // PRECISA ver o erro para toast + reset defensivo.
    throw new Error(`GET wizard session failed: ${res.status}`);
  }

  // Defensive — loop above always either returns or throws, but TS
  // wants an exhaustive return.
  throw new WizardBackendUnavailableError({
    attempts: totalAttempts,
    lastStatus,
    code: lastCode,
  });
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
  //
  // Task #1177 explicitamente mantém o DELETE sem retry: "Nova conversa"
  // é ação disparada pelo recrutador, faz sentido falhar alto na 1ª
  // tentativa em vez de mascarar problemas com backoff silencioso.
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
// PR-12 / F-4.6 — also purge the old `lia-wizard-store` (Zustand persist key)
// left behind by the deleted src/stores/wizard-store.ts. Single key, not prefix.
export const LEGACY_WIZARD_STORE_KEY = "lia-wizard-store";

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
    // PR-12 — purge legacy Zustand persist key (different prefix)
    if (window.localStorage.getItem(LEGACY_WIZARD_STORE_KEY) !== null) {
      window.localStorage.removeItem(LEGACY_WIZARD_STORE_KEY);
      removed += 1;
    }
  } catch {
    /* ignore quota / privacy-mode errors */
  }
  return removed;
}
